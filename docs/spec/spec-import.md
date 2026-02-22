<a href="../../docs-jp/spec/spec-import.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Import Specification

Read `docs/spec/spec-runtime.md` first.

This document defines how syntax like the following is converted in `py2cpp.py`.

```python
from X import Y
```

Core idea: because import source `X` is fixed, generate code that includes `X`'s header.

```cpp
#include "X"
```

Then allow access only to `Y` at the transpiler name-resolution layer (other symbols are not registered in the symbol table).
Even though C++ visibility still allows access due to include behavior, such accesses must be rejected as transpilation-time errors.

Name collisions are another concern when names happen to overlap across already loaded modules. Example:

```python
from X import Y
from Z import *
```

Assume `X` internally has variable `z`, and `from Z import *` also introduces another `z`.
Then a statement like `W = z` becomes ambiguous in generated C++ and can cause compile errors.

A practical direction is to place each module in a namespace during `py2cpp.py` conversion, for example:

```text
namespace folder_path::X {

}
```

This works for C++, but what about languages without namespaces?
Should namespace-like prefixes be attached to symbol names?

## Addendum: Concerns

- In current spec (`docs/spec/spec-dev.md`), `from module import *` is unsupported. This should be explicitly fixed as either a target to implement first or continue as `input_invalid`.
- `#include` alone cannot enforce C++ visibility restrictions, so `from X import Y` constraints must be guaranteed by transpiler name resolution.
- The allowed symbol kinds for `from X import Y` (function/class/constant/variable), and whether `X.Y` access is allowed/forbidden, need explicit specification.
- Priority on collisions between import names and local names (local/arg/import alias/builtin) must be fixed to avoid per-language behavior drift.

## Addendum: Implementation Ideas (Detailed)

### 0. Fix Target Scope First (Freeze Spec First)

- Phase-1 supported forms are strictly limited to:
  - `import M`
  - `import M as A`
  - `from M import S`
  - `from M import S as A`
- In phase 1, keep `from M import *` unsupported as `input_invalid`.
- In phase 1, keep relative import (`from .m import x`) unsupported as `input_invalid`.

### 1. Fix Input Data Structure for Dependency Analysis Phase

- Extract import data from EAST in this structure:

```text
ImportBinding
- module_id: str              # normalized module name (e.g. pytra.std.time, foo.bar)
- export_name: str            # original symbol name for from-import (empty for import M)
- local_name: str             # bound name in current scope (after alias)
- binding_kind: str           # "module" | "symbol"
- source_file: str            # input file path
- source_line: int            # keep when possible
```

- `import M as A` becomes `binding_kind=module, module_id=M, local_name=A`.
- `from M import S as A` becomes `binding_kind=symbol, module_id=M, export_name=S, local_name=A`.
- Add analysis results to `meta.import_modules` / `meta.import_symbols`, but keep `ImportBinding[]` as internal source of truth.

### 2. Centralize Module Resolution Rules in One Place

- Module resolution must always go through `resolve_module_name(raw_name, root_dir)`.
- Fix resolution order as follows:
  - `pytra.*` resolves first as reserved namespace.
  - Otherwise search user modules (`foo/bar.py`, `foo/bar/__init__.py`).
  - If neither resolves, record in `missing_modules`.
  - If `pytra.py` / `pytra/__init__.py` exists under input root, add to `reserved_conflicts` and fail with `input_invalid`.

### 3. Build Module Export Symbol Table (ExportTable)

- For validating `from M import S`, pre-collect export symbols for each module.
- In phase 1, exported symbols are fixed as:
  - top-level `FunctionDef.name`
  - top-level `ClassDef.name`
  - identifiers assigned by top-level `Assign/AnnAssign` to `Name`
- Importing undefined `S` fails with `input_invalid`.
- Error messages must include `module_id`, `symbol`, and `source_file`.

### 4. Specify Name Resolution Algorithm

- Fix reference-resolution priority (higher first):
  - local variables in current scope
  - function arguments
  - class members (via `self.x`)
  - imported symbol aliases (`A` in `from M import S as A`)
  - imported module aliases (`A` in `import M as A`)
  - builtins
- Same-priority same-name collisions fail with `input_invalid`.
  - Example: `from a import x` and `from b import x` in same module should raise collision error.
- After `from M import S`, references like `M.T` are not allowed (`M` is not bound).

### 5. Fix C++ Generation Rules

- Generate includes from `ImportBinding` with deduplication + stable sort.
- Even for `binding_kind=symbol`, always normalize emitted C++ references to `module_namespace::export_name`.
- Example:

```python
from foo.bar import add as plus
x = plus(1, 2)
```

```cpp
#include "foo/bar.h"
auto x = pytra_mod_foo__bar::add(1, 2);
```

- In other words, alias use is allowed in source, but generated code always lowers to fully-qualified names.
- This avoids ambiguous C++ references even when different modules have same symbol names.

### 6. Fix single-file / multi-file Consistency

- Unify namespace decisions through one route: `module_namespace_map[module_id] -> cpp_namespace`.
- Use the same `module_namespace_map` for single-file and multi-file modes.
- In multi-file mode, forward declaration generation must also use only `module_namespace_map` (no separate logic).
- Require that import-resolution results do not change by conversion mode.

### 7. Fix Error Categories and Reporting Format

- Unify all import-related failures under `input_invalid`.
- `detail` lines must include at least:
  - `kind`: `missing_module | missing_symbol | duplicate_binding | reserved_conflict | unsupported_import_form`
  - `file`: input file
  - `import`: original import string (reconstructed string is acceptable)
- Example:
  - `kind=missing_symbol file=app.py import=from foo import bar`

### 8. Minimal Test Matrix (Acceptance Criteria)

- Positive cases:
  - `import M` / `import M as A` / `from M import S` / `from M import S as A`
  - no collision at call site due to full qualification even when same-name symbols exist across modules
- Negative cases:
  - `from M import *` (phase 1: `input_invalid`)
  - `from .m import x` (phase 1: `input_invalid`)
  - non-existing module/symbol
  - duplicate same-name alias
  - dependency resolution result is identical between `--dump-deps` and normal conversion

## Addendum: Policy for Other Target Languages (Detailed)

### A. Fix Responsibilities of Language-agnostic IR

- Complete import semantic interpretation in front-end; backend must not reinterpret it.
- Normalize references passed to backend in this shape:

```text
QualifiedSymbolRef
- module_id: str      # e.g. foo.bar
- symbol: str         # e.g. add
- local_name: str     # e.g. plus (name in source)
```

- `Name("plus")` in expression should be resolved before backend into `QualifiedSymbolRef(module_id="foo.bar", symbol="add")`.
- This limits language differences to emission syntax only.

### B. Mapping Rules by Backend Category

- Category 1: languages with namespace/module path (C++, Rust, C#, etc.)
  - Map `module_id` to language namespace syntax and emit qualified access.
  - Example: `foo.bar.add` / `foo::bar::add` / `foo.bar::add` depending on language.
- Category 2: languages with file split but weak namespaces
  - Mangle symbols into `module_prefix + symbol` to avoid collisions.
  - Example: `foo_bar__add(...)`.
- Category 3: languages with mostly flat global namespace
  - Mangle all public symbols and guarantee uniqueness in generated artifacts.

### C. Common Name-mangling Specification

- Provide shared algorithm for non-namespace languages.
- `mangled = "__pytra__" + encode(module_id) + "__" + encode(symbol)`
- `encode`: convert characters outside `[a-zA-Z0-9_]` into `_xx` (two-digit hex).
- If leading char becomes numeric, prefix with `_`.
- Re-check collisions after mangling; if still colliding, fail with `input_invalid`.

### D. Complete Import-constraint Checks in Front-end

- Validate `from M import S`, duplicates, unresolved names, and unsupported forms before IR reaches backend.
- Backend should only emit already-resolved `QualifiedSymbolRef`.
- This reduces language-specific drift such as "passes in C++ but fails in other targets".

### E. Minimum Contract Tests per Backend

- For code generated from same input, verify consistency of:
  - resolved target module/symbol pairs (`module_id/symbol`)
  - alias resolution results
  - collision detection results (success/failure)
- Test criterion should be identity of resolution results, not syntax-level similarity.

## Addendum: Concrete Per-language Implementation Policy (Aligned with `readme.md` / `docs/plans/pytra-wip.md`)

Supported targets: `C++ / Rust / C# / JavaScript / TypeScript / Go / Java / Swift / Kotlin`.

### 1. C++ (`src/py2cpp.py`)

- Implementation style:
  - Parse imports through EAST and resolve using `module_namespace_map` and `meta.import_symbols`.
  - Do not emit import statements directly into C++; reflect them via `#include` and name-resolution tables.
- Concrete implementation:
  - Generate includes from canonical `ImportBinding` (dedup + stable sort).
  - For `from M import S as A`, never emit `A` directly; normalize to `ns_of(M)::S` at reference sites.
  - Use the same `module_namespace_map` in single-file and multi-file modes; no rule drift.
- Error policy:
  - `from M import *`, relative import, unresolved module, unresolved symbol, and duplicate alias all fail as `input_invalid`.

### 2. Rust (`src/py2rs.py`)

- Implementation style:
  - Native AST conversion. Current `Import/ImportFrom` is skipped at module top.
  - Call resolution is handled at expression level (e.g. `math.sqrt`, `pathlib.Path`, `perf_counter`).
- Concrete implementation:
  - Run import analysis first and build internal table `alias -> canonical symbol`.
  - Examples:
    - `from time import perf_counter as pc`: normalize `pc()` to `perf_counter()` before existing lowering.
    - `from pathlib import Path as P`: normalize `P(...)` to `Path(...)`.
    - `from math import sqrt as s`: lower `s(x)` to `math_sqrt(...)`.
  - Keep runtime integration through `py_runtime`; import only used symbols via `use py_runtime::{...}`.
- Error policy:
  - `from M import *` and relative import should be unified as `TranspileError` (equivalent to top-level `input_invalid`).

### 3. C# (`src/py2cs.py`)

- Implementation style:
  - Convert imports into `using` lines; map expression-level calls to `Pytra.CsModule.py_runtime.*` and `System.Math`.
  - `_using_lines_from_import` and `_map_python_module` are import entry points.
- Concrete implementation:
  - Generate `using` from `ImportBinding`.
  - `import math as m` -> `using m = System;`
  - `from pathlib import Path as P` should not map directly to `using P = System.IO.Path;`; instead align with Pytra runtime path for `pathlib.Path` equivalence.
  - Keep existing `typing_aliases` route and register from-import names into type-resolution tables.
  - Keep `py_module`/`pylib` compatibility and gradually converge names to `pytra.*`.
- Error policy:
  - Do not expand `from M import *`; fail as unsupported.
  - Same-name alias collision fails immediately as `duplicate_binding`.

### 4. JavaScript (`src/py2js.py` + `src/common/js_ts_native_transpiler.py`)

- Implementation style:
  - Native AST conversion, runtime modules loaded by `require(...)`.
  - Import resolution handled by `_transpile_import`.
- Concrete implementation:
  - Generate `const ... = require(...)` or destructuring assignments from `ImportBinding`.
  - `import math as m` -> `const m = require(.../math.js)`
  - `from time import perf_counter as pc` -> `const pc = perfCounter`
  - `from pathlib import Path as P` -> `const P = pathlib.Path`
  - `from pytra.utils.gif import save_gif as sg` -> `const { save_gif: sg } = require(.../gif_helper.js)`
  - Add lazy emission based on reference counts (emit require only for used bindings).
- Error policy:
  - Keep unsupported branch in `_transpile_import` and fail early on unsupported import forms.

### 5. TypeScript (`src/py2ts.py` + `src/common/js_ts_native_transpiler.py`)

- Implementation style:
  - Same conversion logic as JS (only runtime extension differs: `.ts`).
- Concrete implementation:
  - Use same `ImportBinding` resolution as JS.
  - Keep `require`-style output for runtime compatibility (`tsx` execution path).
  - Add minimal type annotations for import aliases when needed to preserve type information (future extension).
- Error policy:
  - Same as JS. Unsupported import fails during conversion.

### 6. Go (`src/py2go.py` + `src/common/go_java_native_transpiler.py`)

- Implementation style:
  - Native AST conversion. Go `import` lines are embedded in runtime templates; Python imports are not emitted in body.
  - Function/method call resolution is handled by `_transpile_call` (`math.*`, `pathlib.Path`, `perf_counter`, `save_gif`, etc.).
- Concrete implementation:
  - Before dropping import statements, collect `ImportBinding` for alias normalization.
  - `from time import perf_counter as pc` resolves `pc()` to `pyPerfCounter()`.
  - `from pathlib import Path as P` resolves `P("x")` to `pyPathNew(...)`.
  - `from math import sqrt as s` resolves `s(x)` to `math.Sqrt(pyToFloat(x))`.
  - Normalize `png/gif` calls to `pyWriteRGBPNG` / `pySaveGIF` / `pyGrayscalePalette`.
- Error policy:
  - Detect duplicate alias and undefined symbol before Go generation; fail with `input_invalid`.

### 7. Java (`src/py2java.py` + `src/common/go_java_native_transpiler.py`)

- Implementation style:
  - Uses same common transpiler as Go. Java runtime is `PyRuntime.java`.
  - Python imports are not expanded into Java import lines directly; lowered to `PyRuntime.*` calls.
- Concrete implementation:
  - As in Go, normalize aliases first using `ImportBinding`.
  - `from time import perf_counter as pc` -> `PyRuntime.pyPerfCounter()`
  - `from pathlib import Path as P` -> `PyRuntime.pyPathNew(...)`
  - `from math import sin as s` -> `PyRuntime.pyMathSin(...)`
  - Route module-attribute calls to explicit `PyRuntime` methods and forbid ambiguous `Object` method calls.
- Error policy:
  - Unresolved methods currently fail as `TranspileError("cannot resolve method call: ...")`; move detection to import-resolution phase and unify message format.

### 8. Swift (`src/py2swift.py` + `src/common/swift_kotlin_node_transpiler.py`)

- Implementation style:
  - Node-backend mode. Convert Python -> JS, then embed JS as Base64 in generated Swift.
  - Import semantics are canonicalized in JS conversion (`JsTsNativeTranspiler`), not Swift layer.
- Concrete implementation:
  - Swift-specific layer does not own import-resolution logic.
  - Resolve `ImportBinding` during JS generation and embed resolved result.
  - Keep Swift runtime responsible only for running embedded JS.
- Error policy:
  - Stop at JS conversion on import error; do not proceed to Swift generation (single error source).

### 9. Kotlin (`src/py2kotlin.py` + `src/common/swift_kotlin_node_transpiler.py`)

- Implementation style:
  - Same Node-backend mode as Swift (embedded JS execution in Kotlin).
  - Canonical import semantics are in JS conversion.
- Concrete implementation:
  - Kotlin side handles class-name generation and entrypoint only; no import resolution there.
  - Embed JS output with already-resolved `ImportBinding` result.
  - Keep Kotlin runtime focused on `PyRuntime.runEmbeddedNode(...)` invocation.
- Error policy:
  - Same as Swift. Stop on JS import error before Kotlin generation.

### 10. Recommended Integration Order Across Languages

- Step 1: complete `ImportBinding` / `QualifiedSymbolRef` in C++ implementation (EAST path).
- Step 2: port the same resolver to JS/TS shared base.
- Step 3: Swift/Kotlin only need follow-up validation because they depend on JS path.
- Step 4: introduce alias normalization first in Go/Java shared base.
- Step 5: add import preprocessing tables to Rust/C# without breaking existing behavior.
