<a href="../../ja/spec/spec-emitter-guide.md"><img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

# Emitter Implementation Guidelines

This document describes the conventions to follow when implementing a new target-language backend (emitter) and when maintaining an existing emitter.

## 0. Authoritative Pipeline

**The authoritative source for emitters is `src/toolchain2/emit/<lang>/`.**

- Use `runtime_parity_check_fast.py` for parity checks.

## 1. Principles

- An emitter uses **only the information in EAST3** to generate code. Hard-coding module names or paths is forbidden.
- Do not hard-code specific module IDs such as `pytra.std.*` / `pytra.utils.*` / `pytra.built_in.*` in an emitter.
- The calling convention for runtime functions (builtin or extern delegate) must be determined from the `runtime_call_adapter_kind` field. Hard-coding such as `runtime_module_id.startswith("pytra.std.")` is forbidden.
- Delegate import-path resolution, `@extern` delegation, and runtime copying to the common functions in `loader.py`.
- Emitter-specific logic must be limited solely to the transformation of EAST3 nodes into target-language syntax.

### 1.1 Prohibited Actions for Emitters

An emitter faithfully renders EAST3. The following are prohibited:

| Prohibited action | Reason | Correct fix |
|---|---|---|
| **Adding casts** | A missing cast in EAST is a resolve bug | Fix resolve |
| **Changing a variable's type** | `resolved_type` in EAST is authoritative | Fix resolve |
| **Changing the loop-variable type of a for-range** | Type information in EAST is authoritative | Fix resolve |
| **Hard-coding name mappings not in mapping.json** | `mapping.json` is authoritative | Add to mapping.json |
| **Re-implementing type inference** | See §12.1 | Fix EAST type inference |
| **Accepting a FunctionDef whose return type is undetermined** | resolve should have determined it from `None` or annotation | Bug in resolve |
| **Specializing the `in` operator per tuple element count** | A tuple is iterable; per-element-count runtime implementations break | Use a generic `contains` for iterables (`slice.contains()`, `[]T.contains()`, etc.) |

An emitter is permitted to:

| Permitted action | Description |
|---|---|
| Render EAST nodes into target-language syntax | The emitter's primary responsibility |
| Map names according to `calls` in `mapping.json` | See §7 |
| Skip cast output according to `implicit_promotions` in `mapping.json` | See §12.4. Omits output only; never adds casts |
| Expand special markers (e.g., `__CAST__`) into language-specific syntax | See §5 |

**When EAST lacks information, fix EAST (resolve/compile/optimize) rather than writing a workaround in the emitter.**

### 1.5 Built-in Casts such as `str()` / `int()` and Avoiding Boxing

`str(x)` is lowered in EAST3 to `semantic_tag: "cast.str"` / `runtime_call: "py_to_string"`. The `call_arg_type` in EAST3 is `Obj` (object expected), but **the emitter must look at the argument's `resolved_type` rather than `call_arg_type`, and call the runtime function with the concrete type.**

```python
# Python
s: str = str(42)
```

```
# EAST3
Call: str(42)
  semantic_tag: "cast.str"
  runtime_call: "py_to_string"
  arg[0].resolved_type: "int64"    ← use this
  arg[0].call_arg_type: "Obj"      ← ignore this
```

```cpp
// Correct C++ — no boxing
str s = py_to_string(int64(42));

// Wrong — unnecessary boxing
str s = py_to_string(object(int64(42)));
```

The runtime for most languages has overloads of `py_to_string` / `str()` for concrete types. There is no need to box via `object`.

This rule applies not only to `str()` but also to built-in casts and functions such as `int()` / `float()` / `bool()` / `len()`. `call_arg_type: Obj` merely represents Python's dynamic dispatch; if the static type is available in `resolved_type`, use it.

### 1.2 Preconditions for EAST3

EAST3 reaching an emitter must satisfy the following. If it does not, it is a bug in an upstream stage, and the emitter must not absorb it.

- The `return_type` of every `FunctionDef` / `ClosureDef` must be determined. `unknown` or an empty string is not acceptable. **For functions without a return-type annotation, resolve determines `None` if the body contains no `return <value>`. If `return <value>` is present but there is no annotation, resolve stops with `inference_failure`.**
- The `resolved_type` of every expression node must be determined (zero `unknown` values).
- `range()` must not remain as a raw `Call` (it has been converted to `ForRange` / `RangeExpr`).

### 1.3 Code-Writing Rules for Emitter Implementations

The emitter's own code (Python files under `src/toolchain2/emit/`) is a selfhost target. Observe the following:

- **Write return-type annotations on functions that return values.** `-> None` may be omitted (the body automatically returns `None` if it contains no `return <value>`). Having `return <value>` without an annotation causes resolve to stop with `inference_failure`.
- **Do not import Python standard modules other than `pytra.std.*`.**
- **Do not use dynamic imports (`try/except ImportError`, `importlib`).**
- **Do not depend on the Python standard `ast` module.**

### 1.4 Quality Requirements for Generated Code

Code generated by an emitter must maintain quality that conforms to the idioms of the target language.

**Exception safety (C++):**

Generated code must be exception-safe. In expressions containing two or more `new` calls, ensure that no leak occurs if the second allocation fails after the first succeeds.

```cpp
// NG: boxed may leak
auto* boxed = new PyBoxedValue<int64>(v);
cb = new ControlBlock{0, tid, boxed};  // bad_alloc → boxed leaks

// OK: retain ownership with make_unique, then release after success
auto boxed = std::make_unique<PyBoxedValue<int64>>(v);
cb = new ControlBlock{0, tid, boxed.get()};
boxed.release();
```

Recovering from `bad_alloc` is not practical, but exception safety is guaranteed as code generated by the transpiler.

**Reserved-word escaping:**

If a user identifier (function name, method name, variable name) collides with a reserved word in the target language, append a trailing `_` to escape it.

```cpp
// Python: def double(x: int) -> int: ...
// C++: double is a type keyword, so rename
int64 double_(int64 x) { ... }
```

Each emitter must maintain a reserved-word table and perform collision detection (Go: `_safe_go_ident`, C++: `_safe_cpp_ident`).

**Generic RC wrapping pattern (C++):**

Use the generic `rc_from_value<T>` rather than per-type dedicated functions (e.g., `rc_list_from_value`) when wrapping non-POD values in RC. The emitter determines only whether a type is POD or non-POD; for non-POD it simply wraps with `rc_from_value(...)`.

```cpp
// NG: separate function per type (requires per-type branching in the emitter)
rc_list_from_value(list<str>{str("a"), str("b")})
rc_dict_from_value(dict<str, int64>{...})

// OK: single generic function (emitter: non-POD → wrap with rc_from_value)
rc_from_value(list<str>{str("a"), str("b")})
rc_from_value(dict<str, int64>{...})
rc_from_value(Foo{...})
```

**Prohibition of redundant output:**

Generated code must maintain quality that a programmer familiar with the target language finds natural. Code output to `sample/` is a showcase for Pytra; redundant constructs diminish that impression.

Each emitter maintainer must visually inspect the generated code in `sample/<lang>/` and eliminate the following NG patterns.

```cpp
// NG: explicit cast on POD type literal
int64 row_sum = int64(0);
float64 x = float64(1.5);
bool flag = bool(true);

// OK: output the literal directly
int64 row_sum = 0;
float64 x = 1.5;
bool flag = true;
```

```cpp
// NG: unnecessary str() wrapper
str name = str("hello");

// OK: output the string literal directly
str name = "hello";
```

```go
// NG: unnecessary type conversion
var count int64 = int64(0)

// OK: output the literal directly
var count int64 = 0
```

```typescript
// NG: unnecessary Number() wrapper
let x: number = Number(0);

// OK: output the literal directly
let x: number = 0;
```

```cpp
// NG: default constructor for zero initialization
int64 r = int64{};
float64 x = float64{};

// OK: initialize with a literal
int64 r = 0;
float64 x = 0.0;
```

```cpp
// NG: redundant parentheses (self-evident from operator precedence)
int64 x = (a) + (b);
int64 y = (a + b) * c;  // + has lower precedence than *, so parentheses are needed → OK

// OK: remove self-evident parentheses
int64 x = a + b;

// OK: keep parentheses that change evaluation order
int64 z = a * (b + c);   // without them the result would be a*b+c
float64 w = a * (b * c); // may change result due to floating-point associativity; may be kept
```

General rules:
- For EAST3 `Call(Name("<pod_type>"), [Constant(value)])` with a single literal argument, output the literal itself rather than a type-constructor call.
- `str(literal)` is output as a string literal.
- `bool(True)` / `bool(False)` are output as `true` / `false`.
- The above applies only when unambiguous under the target language's type inference. In languages that require type annotations, indicate the type via annotation and output the literal bare.
- Use literals (`0`, `0.0`, `false`, `""`) for default-value initialization of POD types; do not use default constructors (`int64{}`, `float64{}`).
- Do not output parentheses that are self-evident from operator precedence. Do keep parentheses that change evaluation order. In particular, parentheses that affect floating-point associativity (e.g., `a * (b * c)` vs `(a * b) * c`) may be retained.
- CommonRenderer holds common logic of "add parentheses if the parent operator's precedence ≥ the child operator's precedence"; each language passes its own precedence table.

### runtime_call_adapter_kind

`runtime_call_adapter_kind` on a Call node indicates the calling convention for the runtime function. EAST3 derives it automatically from the group to which `runtime_module_id` belongs.

| Value | Meaning | Example |
|---|---|---|
| `"builtin"` | Functions provided by `py_runtime` under the `__pytra_` prefix | `py_print`, `py_len` |
| `"extern_delegate"` | `@extern` delegation functions provided by the generated `std/<mod>.<ext>` under bare names | `perf_counter`, `sqrt` |
| `""` (empty) | Unresolved or user-defined functions | user-defined functions |

```python
# Prohibited pattern
if runtime_mod_id.startswith("pytra.std."):  # ← hard-coded
    call_name = bare_name

# Correct pattern
adapter = call_node.get("runtime_call_adapter_kind", "")
if adapter == "extern_delegate":
    call_name = bare_name
elif adapter == "builtin":
    call_name = "__pytra_" + bare_name
```

## 2. Emitter Invocation Structure

### 2.1 CLI Entry Point

The `-emit` / `-build` commands of `pytra-cli2.py` invoke each language's emitter via **subprocess**. They do not import it directly.

```
pytra-cli2.py -build --target cpp input.py
  → parse → resolve → compile → optimize → link → manifest.json
  → subprocess: python3 -m toolchain2.emit.cpp.cli manifest.json -o out/
```

This ensures that `pytra-cli2.py` does not load emitters for languages it does not use (preserving startup speed).

### 2.2 Per-Language cli.py

Each language provides `src/toolchain2/emit/<lang>/cli.py`. Its contents simply pass the emit function to the common runner:

```python
from toolchain2.emit.common.cli_runner import run_emit_cli
from toolchain2.emit.<lang>.emitter import emit_<lang>_module

if __name__ == "__main__":
    import sys
    raise SystemExit(run_emit_cli(emit_<lang>_module, sys.argv[1:]))
```

Reading the manifest, the module loop, and argument parsing are handled by `run_emit_cli` (the common runner). Each language provides only the emit function.

### 2.3 Emit Function Interface

The emitter for each language satisfies the following signature:

```python
def emit_<lang>_module(east_doc: dict[str, JsonVal]) -> str:
    """Generate and return target-language code from an EAST3 document."""
    ...
```

Languages such as C++ that need to branch on `module_kind` read `module_kind` from `meta` inside `east_doc` and branch internally. The cli.py and common runner have no knowledge of `module_kind`.

### 2.4 Invocation from runtime_parity_check_fast.py

`tools/check/runtime_parity_check_fast.py` is under `tools/` (not a selfhost target), so it may import `emit_<lang>_module` directly. However, use the common emit loop (equivalent to `run_emit_cli`) and do not write language-specific logic in the parity check.

### 2.5 Prohibited Actions

- `pytra-cli2.py` importing each language's emitter directly (call cli.py via subprocess instead).
- cli.py independently implementing manifest reading or a module loop (use the common runner).
- The common runner branching on `module_kind` (that is the internal responsibility of each language's emit function).

## 3. Import Path Resolution

### Prohibited Pattern

```python
# NG: hard-coded module names
if module_id == "pytra.utils":
    zig_path = "utils/" + name + ".zig"
elif module_id.startswith("pytra.std."):
    zig_path = "std/" + tail + ".zig"
```

### Correct Pattern

```python
# OK: derive the path mechanically from module_id
def _module_id_to_import_path(module_id: str, ext: str, root_rel_prefix: str) -> str:
    rel = module_id
    if rel.startswith("pytra."):
        rel = rel[len("pytra."):]
    return root_rel_prefix + rel.replace(".", "/") + ext
```

### Languages That Do Not Need Import Statements

In languages such as Swift where all files are compiled together and symbols within the same module can cross-reference each other without `import`, **there is no need to generate import statements in the source.**

However, `build_import_alias_map` is used not only for generating import statements but also for **resolving owner names in module-attr calls** (e.g., `math.sqrt` → `pytra.std.math` → correct namespace/function call). Even languages that do not generate import statements need `build_import_alias_map`.

| Language | Import statement generation | `build_import_alias_map` |
|---|---|---|
| JS/TS | Generate `import { ... } from "..."` | Required (import generation + alias resolution) |
| Go | No import needed (flat layout) | Required (alias resolution) |
| Swift | No import needed (compiled together) | Required (alias resolution) |
| Zig | Generate `@import("...")` | Required (import generation + alias resolution) |
| Others | Generate as appropriate for the language | Required |

### Distinguishing Symbol Import from Module Import

`binding_kind` in `import_bindings` can be `"module"` or `"symbol"`. Distinguish these correctly.

```python
from re import sub       # binding_kind="symbol" — the sub function of the re module
from pytra.utils import png  # binding_kind="symbol" — but png is a submodule
import math               # binding_kind="module" — the entire math module
```

**Generating include/import paths for symbol imports:**

- `from re import sub` → include the `re` module (`std/re.<ext>`)
- `sub` is a function within the module and **is not a submodule**
- Do not expand the symbol name into a path as in `std/re/sub.<ext>`

```
# Correct
from re import sub  → #include "std/re.h"      (C++)
                    → import { sub } from "./std/re.js"  (JS)

# Wrong
from re import sub  → #include "std/re/sub.h"  ← treating sub as a submodule
```

**Identifying submodule imports:**

Whether `png` in `from pytra.utils import png` is a submodule or a symbol is determined by the linker, which checks whether a runtime module exists for `module_id + "." + export_name`. Using `build_import_alias_map` means the emitter does not need to implement this distinction logic.

### Resolving Import Aliases

Aliases such as `from pytra.std import os_path as path` are resolved with `build_import_alias_map`:

```python
from toolchain2.emit.common.code_emitter import build_import_alias_map

alias_map = build_import_alias_map(east_doc.get("meta", {}))
# {"path": "pytra.std.os_path", "math": "pytra.std.math"}

# Resolve owner_name in an Attribute Call:
resolved_module = alias_map.get(owner_name, "")
if resolved_module != "":
    import_path = _module_id_to_import_path(resolved_module, ".zig", root_rel_prefix)
```

## 4. Generating Delegation Code for @extern Functions

Following spec-abi.md §3.2.1, emitters for languages other than C++ generate delegation code to a `_native` module for `@extern` functions.

### Detection

```python
decorators = func_def.get("decorators", [])
if isinstance(decorators, list) and "extern" in decorators:
    # This function is @extern → generate delegation code
```

### Examples of Generated Delegation Code

JS:
```javascript
import * as __native from "./std/time_native.js";
export function perf_counter() { return __native.perf_counter(); }
```

PowerShell:
```powershell
. "$PSScriptRoot/std/time_native.ps1"
function perf_counter { return (__native_perf_counter) }
```

Zig:
```zig
const __native = @import("std/time_native.zig");
pub fn perf_counter() f64 { return __native.perf_counter(); }
```

### Delegating extern() Variables (Ambient Globals)

In addition to `@extern` functions, there are variables (constants) declared with `extern()`:

```python
# math.py
pi: float = extern(math.pi)   # extern() variable declaration
e: float = extern(math.e)
```

In EAST3, `AnnAssign` nodes gain a `meta.extern_var_v1` annotation.

When an emitter sees an `extern()` variable, it generates delegation to the `__native` module just as for `@extern` functions:

```zig
// std/math.zig (generated)
const __native = @import("math_native.zig");
pub const pi: f64 = __native.pi;
pub const e: f64 = __native.e;
```

```javascript
// std/math.js (generated)
import * as __native from "./math_native.js";
export const pi = __native.pi;
export const e = __native.e;
```

The corresponding native file provides target-language standard-library values by hand:

```zig
// std/math_native.zig (hand-written)
const std = @import("std");
pub const pi: f64 = std.math.pi;
pub const e: f64 = std.math.e;
```

```javascript
// std/math_native.js (hand-written)
export const pi = Math.PI;
export const e = Math.E;
```

### Detection

```python
# Recommended: check meta.extern_var_v1 (does not depend on structure)
meta = stmt.get("meta", {})
extern_v1 = meta.get("extern_var_v1")
if isinstance(extern_v1, dict):
    symbol = extern_v1.get("symbol", "")  # name of the target symbol
    # extern() variable → generate delegation to __native
```

Structure of `meta.extern_var_v1`:
```json
{"schema_version": 1, "symbol": "pi", "same_name": 1}
```

- `symbol`: name of the target native symbol
- `same_name`: `1` if the target name and the symbol name match

Note: The value node may be wrapped in `Unbox` by EAST3 lowering, so direct detection via `value.get("kind") == "Call"` is unreliable. Use `meta.extern_var_v1` as the authoritative source.

**Prohibited**: The emitter must not hard-code target-language standard-library constants (e.g., `std.math.pi`, `Math.PI`). Constant values are provided by the native file.

### Native Module Path

Normalize with `canonical_runtime_module_id` and append the `_native` suffix:

```python
from toolchain.frontends.runtime_symbol_index import canonical_runtime_module_id

clean_id = module_id.replace(".east", "")
canonical = canonical_runtime_module_id(clean_id)
# pytra.std.time → std/time_native.<ext>
parts = canonical.split(".")
if len(parts) > 1 and parts[0] == "pytra":
    native_path = "/".join(parts[1:]) + "_native.<ext>"
```

## 5. Unified Naming Convention for Output Files

### Module → File Name Mapping

All languages follow the rules below. Emitters must not use their own naming conventions.

| module_id | Output file name |
|---|---|
| `17_monte_carlo_pi` (entry) | `17_monte_carlo_pi.<ext>` |
| `pytra.std.time` | `std/time.<ext>` |
| `pytra.std.math` | `std/math.<ext>` |
| `pytra.utils.gif` | `utils/gif.<ext>` |
| `pytra.built_in.io_ops` | `built_in/io_ops.<ext>` |

Conversion rule: strip the `pytra.` prefix from `module_id`, replace `.` with `/`, and append the extension. `emit_all_modules` does this automatically, so no emitter implementation is needed.

### Languages Requiring Flat Layout

In languages such as Go where `.go` files in subdirectories are treated as separate packages, all files must be placed flat directly under `emit/`.

In this case:
- Do not use `emit_all_modules`; use a custom loop for flat output.
- Instead of `copy_native_runtime`, copy files from `built_in/` / `std/` directly under `emit/`.
- To avoid filename collisions, prepend the subdirectory name as a prefix (e.g., `std_time.<ext>`, `built_in_py_runtime.<ext>`).

```
# Example of flat layout (Go)
emit/
├── 17_monte_carlo_pi.go
├── std_time.go              # pytra.std.time
├── std_time_native.go       # hand-written native
├── std_math.go              # pytra.std.math
├── std_math_native.go
├── built_in_py_runtime.go   # hand-written built-in
└── utils_gif.go             # pytra.utils.gif
```

Pass `flat=True` to `copy_native_runtime` in `loader.py` for a flat copy. `emit_all_modules` has a similar `flat=True` option.

Applicable languages: Go (add others requiring flat layout as needed).

### Native File Naming

Hand-written runtime files use the `_native` suffix:

| module_id | Generated file | Native file |
|---|---|---|
| `pytra.std.time` | `std/time.<ext>` | `std/time_native.<ext>` |
| `pytra.std.math` | `std/math.<ext>` | `std/math_native.<ext>` |
| `pytra.built_in.io_ops` | `built_in/io_ops.<ext>` | (built_in is integrated into py_runtime) |

### Entry Module Naming

- **Standard**: use the module_id as-is → `17_monte_carlo_pi.<ext>`
- **Scala only (exception)**: merge all modules into a single file

Changing entry file names in any other way is prohibited.

### Java main Separation

Because Java's language specification requires that the class name match the file name, only the `main()` method is separated into `Main.java`. The logic body is output to a file name derived from the module_id.

```
emit/
├── 01_mandelbrot.java    # Logic body (function and class definitions)
├── Main.java             # main() only. Calls into the body class
├── std/time.java
└── ...
```

This ensures:
- Matches `sample/java/01_mandelbrot.java` (no renaming needed)
- Compilable with `javac *.java` and runnable with `java Main`
- No Java-specific renaming logic needed in `regenerate_samples.py` or `pytra-cli2.py`

## 5.1 Unified Naming for @extern Delegation

### Delegation Target Variable Name

Use `__native` in all languages:

```javascript
// JS
import * as __native from "../std/time_native.js";
export function perf_counter() { return __native.perf_counter(); }
```

```zig
// Zig
const __native = @import("../std/time_native.zig");
pub fn perf_counter() f64 { return __native.perf_counter(); }
```

```powershell
# PowerShell
. "$PSScriptRoot/../std/time_native.ps1"
function perf_counter { return (__native_perf_counter) }
```

`__native` is treated as a reserved name and is assumed not to collide with user code. In languages without namespaces such as PowerShell, prefix function names with `__native_`.

### Delegation Function Naming

- The generated function name must **exactly match** the original Python function name.
- The implementation function name in the native file must also match the original Python function name.
- Do not add a `py_` prefix or a `_native` suffix to function names (the `_native` in file names is separate from function names).

```
# Correct
def perf_counter() → export function perf_counter() in std/time.js
                   → function perf_counter() in std/time_native.js

# Wrong
def perf_counter() → function py_perf_counter()      ← prefix forbidden
                   → function perf_counter_native()   ← suffix forbidden
```

### Native File Import Path

Use `emit_context.root_rel_prefix` to reference the **`_native` file of the same module**:

```python
# Referencing std/time_native.<ext> from std/time.<ext>
native_import_path = root_rel_prefix + "std/time_native.<ext>"
# root_rel_prefix = "../" (depth=1)  → "../std/time_native.<ext>"
# root_rel_prefix = "./"  (depth=0)  → "./std/time_native.<ext>"
```

## 6. Runtime Copying and py_runtime Responsibilities

Passing `lang="<lang>"` to `emit_all_modules` causes automatic copying from `src/runtime/<lang>/{built_in,std}/`. An individual `_copy_runtime` is not needed.

Copying does not overwrite already-generated files (because `@extern` delegation code is generated first).

### py_runtime Responsibilities

`built_in/py_runtime.<ext>` provides **only helpers equivalent to Python's built-in functions**:

| May include | Examples |
|---|---|
| print / len / range / int / float / str / bool | Python built-in functions |
| Type conversions (py_to_bool, etc.) | Python implicit conversions |
| Container operations (list append, etc.) | Python methods |
| String operations (split, join, etc.) | str methods |

| Must not include | Reason |
|---|---|
| `write_rgb_png` / `save_gif` / `grayscale_palette` | `pytra.utils.*` module functions; generated by the linker only when needed |
| `perf_counter` / `sqrt` / `sin` | `pytra.std.*` module functions; provided by `_native` files |
| JSON / pathlib / os operations | `pytra.std.*` module functions |

Functions from `pytra.std.*` / `pytra.utils.*` are generated via the emitter from `.east` only when the linker resolves dependencies. Including them in `py_runtime` causes compilation errors (undefined symbol references) even in programs that do not use those functions.

### Prohibition on Hand-Writing Image Runtimes (PNG/GIF)

**Do not hand-implement the encoding body logic for `write_rgb_png` / `save_gif` / `grayscale_palette` (CRC32 / Adler32 / DEFLATE / LZW / chunk construction) in the target language.**

The authoritative source for these is `src/pytra/utils/png.py` / `src/pytra/utils/gif.py`; only the generated code produced by the transpiler (`src/runtime/<lang>/generated/utils/png.*` / `gif.*`) is used.

```
Authoritative:  src/pytra/utils/png.py        ← Python source
Generated:      src/runtime/<lang>/generated/utils/png.<ext>  ← transpile result
Native:         src/runtime/<lang>/native/utils/png_native.<ext>  ← I/O adapter only
```

Prohibited actions:
- Directly implementing `write_rgb_png` / `save_gif` in `py_runtime`
- Using the target language's image libraries (Go's `image/png`, Swift's `CoreGraphics`, etc.) to provide independent implementations
- Hand-porting CRC32 / DEFLATE / LZW tables or algorithms

Permitted language differences:
- I/O adapters (file writing, byte-sequence conversion) may be hand-written in `native/`
- Native implementations of helper functions called by generated code (e.g., `write_bytes`)

If the image runtime does not work, fix it by **correcting the transpile pipeline (EAST → emitter)**. Do not work around it by hand-writing.

**Language backend contributors must not modify the authoritative source files (`src/pytra/utils/*.py`, `src/pytra/std/*.py`).** These files are the basis for generated output in all languages; changes propagate across all languages. If a change is necessary, the planner or infrastructure lead must first confirm the impact on all languages.

### Skipping emit for built_in Modules

The linker includes `pytra.built_in.io_ops` / `pytra.built_in.scalar_ops` etc. in the link-output (for dependency tracking). However, the emitter should **skip emit** for these modules.

Reason: The `@extern` functions in `built_in` modules (`py_print`, `py_ord`, etc.) are provided directly by `py_runtime.<ext>`, so there is no need to generate delegation code to a `_native` file. Native files like `io_ops_native` do not exist.

```python
# Skip built_in modules inside transpile_fn
def _transpile(east_doc: dict) -> str:
    meta = east_doc.get("meta", {})
    emit_ctx = meta.get("emit_context", {}) if isinstance(meta, dict) else {}
    module_id = emit_ctx.get("module_id", "") if isinstance(emit_ctx, dict) else ""
    # built_in modules are provided by py_runtime; no emit needed
    if module_id.startswith("pytra.built_in."):
        return ""  # returning an empty string causes emit_all_modules to skip file generation
    ...
```

`emit_all_modules` does not generate a file when `transpile_fn` returns an empty string.

| module_id | Emit | Reason |
|---|---|---|
| `pytra.built_in.io_ops` | **Skip** | `py_runtime` directly provides `py_print` etc. |
| `pytra.built_in.scalar_ops` | **Skip** | `py_runtime` directly provides `py_ord` etc. |
| `pytra.built_in.sequence` | **Skip** | `py_runtime` directly provides `py_range` etc. |
| `pytra.std.time` | Emit | `@extern` → generate `__native` delegation code |
| `pytra.utils.png` | Emit | Normal function code generation |

## 7. runtime mapping.json

Place a `mapping.json` in each language's runtime to map EAST3 `runtime_call` values to function names in the target language.
The `CodeEmitter` base class reads this file and resolves names via `resolve_runtime_call()`.

- Location: `src/runtime/<lang>/mapping.json`
- Loading: `load_runtime_mapping()` in `toolchain2/emit/common/code_emitter.py`
- Naming convention: `py_<type>_<method>` format (e.g., `py_str_strip`, `py_dict_get`)

**Official specification: [spec-runtime-mapping.md](./spec-runtime-mapping.md)**

### 7.1 Uses of the `calls` Table

The `calls` table is used not only for function calls but also for mapping constants and variables.

| Use | Example (key → value) | Output form |
|---|---|---|
| Function call | `"py_len"` → `"py_len"` | Output as a function name |
| External function | `"math.sqrt"` → `"std::sqrt"` | Replace with the external library function name |
| Constant | `"math.pi"` → `"M_PI"` | Replace with the target-language constant name |
| Special marker | `"static_cast"` → `"__CAST__"` | Expanded by the emitter via dedicated logic |

Constants (e.g., `math.pi` → `M_PI`) are resolved against `AnnAssign` nodes with `extern_var_v1` metadata. Because the emitter outputs the value from the `calls` table as-is, it must be a valid expression in the target language.

### 7.2 Mapping String Literal Constants

When you want to embed a string literal itself rather than a macro constant in the target language (e.g., `env.target` → `"cpp"`), write the value including its quotes:

```json
{
  "calls": {
    "env.target": "\"cpp\""
  }
}
```

Because the emitter outputs the `calls` value as an expression verbatim, `"\"cpp\""` is embedded in C++/Go source as `"cpp"`.

This mechanism allows compile-time constants declared with `runtime_var` to be defined per language solely via mapping.json, without adding individual logic to the emitter.

### 7.3 Required Entries for All Languages

The following entries are mandatory in every `mapping.json`. Do not forget to define them when adding a new emitter.

| Key | Value | Description |
|---|---|---|
| `env.target` | `"\"<lang>\""` | The target language name at runtime. Maps `pytra.std.env.target` |

#### What is `env.target`?

`pytra.std.env.target` is a compile-time constant that returns the target language in which the current code is running. User code accesses it as follows:

```python
import pytra.std.env as env

if env.target == "python":
    # Running directly in Python
    ...
elif env.target == "cpp":
    # Compiled to C++ and running
    ...
```

The emitter looks up `calls["env.target"]` in mapping.json and embeds it as a string literal in the source. No runtime function call is generated.

The declaration is placed in `include/py/pytra/std/env.py` as `runtime_var("pytra.std.env")`. When running directly in Python, mapping.json is not consulted, so the module returns `"python"` as its default value.

#### Definition Examples for Each Language

```json
// src/runtime/cpp/mapping.json
"env.target": "\"cpp\""

// src/runtime/go/mapping.json
"env.target": "\"go\""

// src/runtime/rs/mapping.json
"env.target": "\"rs\""

// src/runtime/ts/mapping.json
"env.target": "\"ts\""
```

Validation: `tools/check/check_mapping_json.py` (verifies that `env.target` is defined in all mapping.json files, etc.)

### 7.4 Type Mapping Table (`types`)

The `types` table in mapping.json maps EAST3 type names to target-language type names. Emitters must not hard-code type names; instead they resolve them from this table.

```json
{
  "types": {
    "int64": "int64_t",
    "float64": "double",
    "bool": "bool",
    "str": "str",
    "Exception": "std::runtime_error",
    "Path": "PyPath"
  }
}
```

- Both POD types (`int64`, `float64`, `bool`, `str`, etc.) and class types (`Exception`, `Path`, etc.) are managed in the same table.
- Type names not found in `types` are output as-is (user-defined classes).
- The `CodeEmitter` base class provides a `resolve_type(east3_type)` method.
- Hard-coding in each language's `types.py` is deprecated; migrate to mapping.json.

Official specification: [spec-runtime-mapping.md](./spec-runtime-mapping.md) §7

## 8. Common Utilities (standalone functions in `code_emitter.py`)

Functions usable even in emitters that do not inherit from `CodeEmitter`:

| Function | Purpose |
|---|---|
| `build_import_alias_map(meta)` | Build an import alias → module_id map |
| `collect_reassigned_params(func_def)` | Detect reassigned parameters (for languages with immutable parameters) |
| `mutable_param_name(name)` | Rename a parameter (`data` → `data_`) |

```python
from toolchain2.emit.common.code_emitter import (
    build_import_alias_map,
    collect_reassigned_params,
    mutable_param_name,
)
```

## 8. Using emit_context

Information that `emit_all_modules` sets in `meta.emit_context` for each module:

```python
emit_ctx = east_doc.get("meta", {}).get("emit_context", {})
module_id = emit_ctx.get("module_id", "")         # Module ID
root_rel_prefix = emit_ctx.get("root_rel_prefix", "./")  # Relative path to the root
is_entry = emit_ctx.get("is_entry", False)         # Whether this is the entry module
```

- `root_rel_prefix` is used to resolve import paths from submodules.
- `is_entry` is used to determine whether to emit the main function (see below).
- `module_id` is used to resolve the native path for `@extern` delegation.

### Handling is_entry and main_guard_body

The link pipeline sets only the one file specified on the CLI to `is_entry=True`. Dependency modules always have `is_entry=False`.

Emitters follow these rules:

- **Modules with `is_entry=True`**: Output `main_guard_body` (the body of `if __name__ == "__main__":`) as the target language's `main` function.
- **Modules with `is_entry=False`**: Do **not** output `main_guard_body` even if it is present in EAST. Treat as a library module.
- In languages such as Java where `main` is separated into a different file, generate `Main.java` only for modules with `is_entry=True` (see §5).
- Emitters must **not** determine `is_entry` on their own. Use `emit_context.is_entry` as the authoritative source.

## 9. EAST3 Nodes That Emitters Must Handle

| Node | Description | Emitter responsibility |
|---|---|---|
| `VarDecl` | Hoisted variable declaration | Generate a typed variable declaration |
| `Swap` | `a, b = b, a` pattern (**left/right are always Name**) | Generate language-specific swap code |
| `discard_result: true` | Suppress return value in main_guard_body | Generate code that discards the return value |
| `unused: true` | Unused variable (Assign / VarDecl / tuple element) | Suppress warning or omit declaration |
| `decorators: ["extern"]` | @extern function | Generate delegation code to `_native` |
| `decorators: ["property"]` | @property method | Convert to getter access |
| `mutates_self: true/false` | Whether a method mutates self | Select mutable/immutable self |
| `ClosureDef` | FunctionDef that has been closure-ified by EAST3 lowering | Generate language-specific closure syntax (§9.2) |
| `With` | Context manager (`with expr as var:`) | Generate language-specific resource-management syntax (§9.3) |

### 9.1 Swap Node Contract

The `left` / `right` of a Swap node are **always Name nodes**. Subscript-based swaps (e.g., `values[i], values[j] = values[j], values[i]`) are expanded by EAST3 lowering into a sequence of Assign statements with a temporary variable, so they never reach the emitter as Swap.

When an emitter receives a Swap node, it only needs to handle a **simple value exchange between two Names**. No Subscript branch is needed.

```python
# Swap node structure (guaranteed)
{"kind": "Swap", "left": {"kind": "Name", "id": "a"}, "right": {"kind": "Name", "id": "b"}}
```

Generated code by language:

| Language | Generated code |
|---|---|
| C++ | `std::swap(a, b);` |
| Go | `a, b = b, a` |
| Rust | `std::mem::swap(&mut a, &mut b);` |
| Swift | `swap(&a, &b)` |
| Others | `tmp := a; a = b; b = tmp` |

Subscript swaps arrive as Assign nodes and are naturally handled by the emitter's normal Assign processing.

### 9.2 ClosureDef Node Contract

`ClosureDef` is a node produced by EAST3 lowering, which closure-ifies a nested FunctionDef. Capture analysis is already complete in EAST3; the emitter must not re-implement capture analysis.

```json
{
  "kind": "ClosureDef",
  "name": "inner",
  "captures": [
    {"name": "x", "mode": "readonly", "type_expr": ...},
    {"name": "y", "mode": "mutable", "type_expr": ...}
  ],
  "args": [...],
  "body": [...],
  "return_type_expr": ...
}
```

- `captures`: list of variables captured from an outer scope.
  - `name`: variable name
  - `mode`: `readonly` (value capture is acceptable) or `mutable` (reference capture required)
  - `type_expr`: type of the captured variable (structured type representation)
- The emitter's responsibility is solely to map `ClosureDef` to the closure syntax of the target language.

Generated code by language:

| Language | Level | Generated code |
|---|---|---|
| C++ | B | `auto inner = [&y, x](args) -> T { ... };` (mutable by reference, readonly by value) |
| Go | B | `inner := func(args) T { ... }` (Go captures everything by implicit reference) |
| Java | B | Lambda or anonymous class (mutable capture worked around with array wrappers etc.) |
| C# | B | `Func<...> inner = (args) => { ... };` |
| Rust | A/B | `let inner = \|args\| -> T { ... };` |
| Swift | A/B | `let inner: (Args) -> T = { args in ... }` |
| Kotlin | A/B | `val inner: (Args) -> T = { args -> ... }` |
| JS | A | `function inner(args) { ... }` or `const inner = (args) => { ... }` |
| TS | A | Same as above (with type annotations) |

Languages at Level A (natively supporting nested functions) may output `ClosureDef` as a normal nested function. In that case the `captures` information may be ignored.

Prohibited:

- Analyzing capture variables in the emitter (EAST3's `captures` is authoritative).
- Changing a capture mode in the emitter.
- Ignoring a `ClosureDef` as unsupported when it arrives (fail closed; stop with an error).

### 9.3 With Node Contract

`With` is a resource-management node corresponding to Python's `with expr as var:`. EAST preserves it as-is without lowering, so the emitter maps it to the appropriate syntax of each language.

```json
{
  "kind": "With",
  "context_expr": { "kind": "Call", "...": "..." },
  "var_name": "f",
  "body": [...]
}
```

- `context_expr`: expression that produces the context manager (e.g., `open(path, "wb")`)
- `var_name`: variable bound by `as` (empty string if omitted)
- `body`: body of the with block

Generated patterns by language:

| Language | Generated pattern |
|---|---|
| C++ | RAII (automatic release at scope exit) or `try`/destructor |
| Go | `f := open(...); defer f.Close(); ...` |
| Rust | `Drop` at scope exit, or explicit `drop()` |
| Java | `try (var f = open(...)) { ... }` (try-with-resources) |
| C# | `using (var f = open(...)) { ... }` |
| Kotlin | `open(...).use { f -> ... }` |
| Swift | `defer { f.close() }` at scope exit |
| JS/TS | `try { const f = open(...); ... } finally { f.close(); }` |

Mapping principles:

- If the language has a resource-management construct (Java try-with-resources, C# using, Go defer, etc.), use it.
- If no resource-management construct is available, use a `try/finally` pattern to guarantee `close()` / release.
- Guarantee that resources are released even if an exception occurs in the body of the `with` block.

Prohibited:

- Expanding `With` into manual `open/close` and losing exception safety.
- Ignoring a `With` node as unsupported when it arrives (fail closed; stop with an error).
- **Rewriting the `with` statement in the authoritative source (`src/pytra/utils/*.py` etc.) to work around transpiler limitations.** The correct fix is for the emitter to handle `With`.

## 10. Container Reference Semantics Requirements

### 10.1 Mandatory Rules

Python's `list` / `dict` / `set` have reference semantics. When a container is passed to a function and destructively operated on (`.append()` / `.pop()` / `[]=` etc.), those changes must be reflected in the caller's container.

Every backend must hold containers in a **reference-type wrapper** (reference-counted, GC reference, pointer, etc.).

```python
def add_item(xs: list[int], v: int) -> None:
    xs.append(v)  # reflected in the caller's xs

items: list[int] = [1, 2, 3]
add_item(items, 4)
print(items)  # [1, 2, 3, 4]
```

### 10.2 Prohibited Patterns

Do not use a language's native value-type container without a wrapper.

| Language | NG (value type) | OK (reference-type wrapper) |
|---|---|---|
| Go | `[]any` | `*PyList` / reference-wrapper struct |
| Swift | `[Any]` | `class PyList` / reference-type wrapper |
| Rust | `Vec<PyAny>` (ownership move) | `Rc<RefCell<Vec<T>>>` / reference wrapper |
| C++ | `list<T>` (value type directly) | `Object<list<T>>` (reference-counted) |

Do not add annotations such as `mutates_params` to EAST3 to work around value-type containers. This leaks a target-specific runtime concern into the language-independent IR and requires IR extensions each time a method is added. Switching to reference-type wrappers solves `append` / `extend` / `pop` / `[]=` / `clear` / `sort` / `reverse` all at once.

### 10.3 Reference Implementations

| Backend | Reference-type wrapper | Location |
|---|---|---|
| C++ | `Object<list<T>>` — reference counting via `ControlBlock` + typed pointer | `src/runtime/cpp/core/object.h` |
| Zig | `Obj` — `*anyopaque` + `*usize` (rc) + `drop_fn` | `src/runtime/zig/built_in/py_runtime.zig` |
| Java/Kotlin/C#/Scala | Language reference-type classes (`ArrayList`, `MutableList`, etc.) already satisfy reference semantics | Each `src/runtime/<lang>/` |

### 10.4 Conditions for Allowing Value-Type Reduction

Value-type reduction is permitted only on local paths where the type is known and non-escape is provable.

- Maintain the reference representation at `container_ref_boundary` (inflow paths to `Any` / `object` / `unknown`).
- Allow shallow-copy materialization only on `typed_non_escape_value_path` (type known + locally non-escape).
- When undecidable, fail closed to the reference representation.

See `spec-cpp-list-reference-semantics.md` §5 and `p3-multilang-container-ref-model-rollout.md` §S1-02 for details.

### 10.5 Implementing Value-Type Reduction via Optimizer Hints

In backends such as Go / Swift / Rust that have introduced reference-type wrappers for containers, all containers are held as reference types by default. However, the EAST3 optimizer (`ContainerValueLocalHintPass`) performs escape analysis and supplies, via the linker as `container_value_locals_v1` hints, the local variables that can safely be held as value types.

The emitter consults `meta.linked_program_v1.container_ownership_hints_v1.container_value_locals_v1` in the linked module, and may use the language's native value-type container rather than a reference wrapper for local variables listed in the hints.

```
# Structure of linked module metadata
meta.linked_program_v1.container_ownership_hints_v1:
  container_value_locals_v1:
    "<module_id>::<function_name>":
      version: "1"
      locals: ["xs", "buf"]    # list of variable names safe to hold as value types
```

Example implementation (Go emitter pseudocode):

```
# No hint (default): use a reference wrapper
xs := NewPyList()       # *PyList (reference type)

# With hint: hold directly as a value type
xs := make([]int64, 0)  # []int64 (value-type slice)
```

Notes:

- Variables not in the hints must **always** be held as reference types (fail closed).
- Hints currently target list only (dict / set are future extensions).

## 10.2 Handling the type_id Table

The virtual module `pytra.built_in.type_id_table` generated by the linker is included in the link-output as a normal EAST3 module.

Emitter responsibilities:

- Use the target language's native type-checking facility (`instanceof`, `holds_alternative`, `match`, etc.) for isinstance (see [spec-adt.md](./spec-adt.md) §3).
- `PYTRA_TYPE_ID` / `pytra_isinstance` / `type_id_table` are deprecated. Do not use them in new emitters.

isinstance subtype rules:

- **`bool` is not a subtype of `int`.** `isinstance(True, int)` is `False` in Pytra. This is a Python incompatibility, but it is adopted to simplify isinstance implementation across all languages (see [spec-python-compat.md](./spec-python-compat.md)).
- `IntEnum` / `IntFlag` derived classes are treated as ordinary class inheritance (`isinstance(Color.RED, IntEnum)` → `True`). However, `isinstance(Color.RED, int)` → `False`.
- All primitive types (`bool`, `int`, `str`, `float`, `list`, `dict`, `set`, `None`) are leaf types and have no subtype relationships with each other.

Prohibited:

- Embedding `PYTRA_TYPE_ID` fields in generated code.
- Generating type_id-based checks such as `pytra_isinstance(x, TID)`. Use native facilities.
- Hard-coding the size or values of the type_id table in runtime headers.

See `spec-type_id.md` §7 for details.

## 11. `yields_dynamic` Contract

For method calls that extract container elements (`dict.get`, `dict.pop`, `dict.setdefault`, `list.pop`), the Python-semantic type (`resolved_type`) is a concrete type (e.g., `int64`), but the runtime implementation in non-template languages (Go, Java, etc.) may return a dynamic type (`any` / `interface{}` / `Object`).

- Such Call nodes are annotated with `yields_dynamic: true` in EAST3.
- It is not applied when `resolved_type` is already a dynamic type (`Any`, `object`, `unknown`).
- The emitter uses `yields_dynamic: true` to determine whether a type assertion / downcast is needed.
- Do not determine this by pattern-matching on the generated target-language expression string.
- The corresponding `semantic_tag` values are `container.dict.get`, `container.dict.pop`, `container.dict.setdefault`, `container.list.pop`.

See "About `yields_dynamic`" in `spec-east.md` §7 for details.

## 12. Usage Rules for EAST3 Type Information

### 12.1 Emitters Do Not Re-implement Type Inference

EAST3's `resolved_type` / `decl_type` / `type_expr` are the authoritative values determined by the type-inference pipeline. If an emitter cannot trust these values, the type inference in EAST3 should be fixed; workarounds must not be added to the emitter.

Prohibited patterns:

```python
# NG: re-determining the return type of math module calls in the emitter
if owner_name in _IMPORT_ALIAS_MAP and _IMPORT_ALIAS_MAP[owner_name].endswith("math"):
    return "double"  # ← use EAST3's resolved_type

# NG: reading ahead from a subsequent Assign to determine the type of a VarDecl in the emitter
for stmt in body[i+1:]:
    if stmt.get("target", {}).get("id") == var_name:
        real_type = stmt.get("decl_type")  # ← use VarDecl.type from EAST3
```

### 12.2 Guarantees for resolved_type / decl_type

The EAST3 pipeline guarantees the following. Emitters may rely on these as preconditions.

| Field | Guarantee |
|---|---|
| `Call.resolved_type` | Stdlib functions (`math.sin` etc.) have a concrete type set. Includes `from pytra.std import math` style imports |
| `cast(T, value)` | `resolved_type` is set to the cast target type name `T`. The emitter generates the target-language cast by looking at `resolved_type` |
| `list[T].pop()` | Element type `T` is set in `resolved_type` (not `object`) |
| Container method return values | `list.append()` / `list.extend()` → `None`; `dict.get()` / `dict.pop()` → value type. Derived from the generic parameter |
| `VarDecl.type` | A concrete type derived from the type inference result of the assignment expression is set even for variables without type annotations. `object` appears only when the type is genuinely dynamic |
| `Assign.decl_type` | For `declare: true` Assigns, the type derived from the `resolved_type` of the value expression is set |
| Tuple destructuring | For `x, y = stack[-1]` where `stack: list[tuple[int, int]]`, `resolved_type` of `x` / `y` resolves to `int64` |
| `FunctionDef.returns` | If `return_type` is set, the same value is also reflected in `returns`. Emitters may reference `returns` in forward declarations etc. |
| `VarDecl.name` | Always a non-empty string. VarDecl nodes with `None` or empty string are never generated |
| `unused` on tuple elements | Elements not referenced in the body (e.g., `root, _ = s.split(".")`) are annotated with `unused: true`. Applied not only to the Assign as a whole but to each individual element in a Tuple target |

Notes:
- The `resolved_type` of the `func` (function name / attribute access expression node) on a Call node is a callable type and may remain `unknown`. Emitters must use **`Call.resolved_type` (the type of the call result)**, not `func.resolved_type`.
- `return_type` is authoritative for the return type of a `FunctionDef`. `returns` is a synchronized copy from `return_type`; when both are set, `return_type` takes priority.

### 12.3 Type Mapping for `Any` / `Obj` / `unknown`

EAST's `Any` / `Obj` / `unknown` map to the dynamic type of each language:

| EAST type | Go | C++ | Rust | Java | C# |
|---|---|---|---|---|---|
| `Any` | `any` | `std::any` or `Object<void>` | `Box<dyn Any>` | `Object` | `object` |
| `Obj` | `any` | `Object<void>` | `Box<dyn Any>` | `Object` | `object` |
| `unknown` | `any` | `auto` | `_` (inferred) | `Object` | `var` |

When `unknown` reaches the emitter:
- The emitter may fall back to the dynamic type above.
- However, frequent `unknown` values are likely a bug in EAST3 type inference. They should be reported as an issue; permanent workarounds must not be added to the emitter.

### 12.4 Type Mapping for Optional / Union

EAST's `type_expr` clearly distinguishes `OptionalType` from `UnionType` (see [spec-east.md](./spec-east.md) §6.4). Emitters must recognize this distinction and choose the appropriate representation in the target language.

#### Three Categories

| EAST `type_expr` | Meaning |
|---|---|
| `OptionalType(inner=T)` | `T \| None` |
| `UnionType(general)` | `T1 \| T2` (no None) |
| `OptionalType(inner=UnionType)` | `T1 \| T2 \| None` |

#### Per-Language Mapping (Specification Target)

Target the per-language conversions defined in [spec-adt.md §3](./spec-adt.md).

| EAST | C++ | Rust | Go | Java | C# | TS |
|---|---|---|---|---|---|---|
| `OptionalType(T)` | `std::optional<T>` | `Option<T>` | `*T` / nil | `T` (nullable) | `T?` | `T \| null` |
| `UnionType(general)` | `std::variant<T1, T2>` | `enum { T1(T1), T2(T2) }` | `any` | `Object` | `object` | `T1 \| T2` |
| `OptionalType(UnionType)` | See below | `Option<enum>` | `any` | `Object` | `object?` | `T1 \| T2 \| null` |

#### Gap from Current Implementations

| Language | Spec target for `UnionType(general)` | Current implementation | Notes |
|---|---|---|---|
| C++ | `std::variant<T1, T2>` | `std::variant<T1, T2>` | Implemented |
| TS | `T1 \| T2` | `T1 \| T2` | Implemented (native union) |
| Rust | `enum { T1(T1), T2(T2) }` | `PyAny` / `Box<dyn Any>` | Type-safe enum not yet implemented |
| Go | `any` | `any` | As specified |
| Java | `Object` | `Object` | As specified |
| C# | `object` | `object` | As specified |

#### C++ Mapping for `OptionalType(inner=UnionType)`

For `T1 | T2 | None` where None is mixed into a union, C++ has two approaches:

- **monostate approach**: `std::variant<T1, T2, std::monostate>` — flat, shorter type. `is None` uses `std::holds_alternative<std::monostate>(x)`.
- **optional+variant approach**: `std::optional<std::variant<T1, T2>>` — corresponds to EAST's type structure. `is None` uses `!x.has_value()`.

The current C++ emitter uses the monostate approach. Both approaches are valid; the choice is left to the emitter.

#### None Value Mapping

| Language | None value |
|---|---|
| C++ | `std::nullopt` or `std::monostate{}` (depends on the emitter's approach) |
| Rust | `None` |
| Go | `nil` |
| TS/JS | `null` |
| Java | `null` |
| C# | `null` |

#### Mandatory Rules

- Do not emit `OptionalType` as `UnionType(options=[T, None])`. EAST normalizes it; the emitter need not re-classify it.
- Do not process `UnionType(union_mode=dynamic)` with the same mapping as a general union. Unions containing `Any` / `object` follow the dynamic-type mapping in §12.3.

### 12.5 Determining Whether to Output Numeric Casts

EAST always inserts explicit cast nodes for mixed numeric-type operations (spec-east2.md §2.5). The emitter uses the `implicit_promotions` table in `mapping.json` to determine whether to output these casts.

- Casts matching `implicit_promotions` → skip output (the target language converts implicitly)
- Casts not matching → output explicit cast code

```python
# CodeEmitter base class method
if self.is_implicit_cast(from_type, to_type):
    return expr  # output without cast
else:
    return cast_expr(to_type, expr)  # output with explicit cast
```

Go / Rust have an empty `implicit_promotions`, so all casts are output. C++ / Java / C# define pairs equivalent to C's integer promotions.

**Emitters must not write their own cast-elimination logic. The `mapping.json` table is authoritative.**

Official specification: [spec-runtime-mapping.md §7](./spec-runtime-mapping.md)

### 12.6 Callable Type Mapping

EAST3's `callable` type (`GenericType(base="callable", args=[arg_types, return_type])`) maps to function types in each language.

| Language | callable mapping | `callable \| None` mapping |
|---|---|---|
| C++ | `std::function<R(P1, P2)>` | `std::optional<std::function<R(P1, P2)>>` |
| Rust | `Box<dyn Fn(P1, P2) -> R>` | `Option<Box<dyn Fn(P1, P2) -> R>>` |
| Go | `func(P1, P2) R` | `func(P1, P2) R` (nil represents None) |
| Java | `Function<P, R>` etc. | `Function<P, R>` (null represents None) |
| TS | `(p1: P1, p2: P2) => R` | `((p1: P1, p2: P2) => R) \| null` |
| Zig | `fn(P1, P2) R` | `?fn(P1, P2) R` |
| Swift | `(P1, P2) -> R` | `((P1, P2) -> R)?` |
| Nim | `proc(p1: P1, p2: P2): R` | `Option[proc(p1: P1, p2: P2): R]` |

#### Notes on `callable | None`

In some languages, function pointers are non-null (`fn != null` is a type error). `callable | None` is normalized in EAST3 as `OptionalType(inner=callable)`, so the emitter must see `OptionalType` and map it to an Optional type (`?fn`, `Option<...>`, etc.).

**Prohibited**: Treating callable as always non-null and reducing `is None` to the constant `false`. When `OptionalType` is present, `is None` checks are valid.

## 13. Conducting Parity Checks

### Initial Setup (After git clone)

Golden files and the runtime east cache are not managed by git. See **[Development Environment Setup](./spec-setup.md)** for the generation procedure immediately after cloning.

### Authoritative Tool

**`tools/check/runtime_parity_check_fast.py` is the authoritative parity check tool for all languages.** All of the following are prohibited:

- Per-language parity check scripts (e.g., `check_cs_fixture_emit.py`)
- Per-language smoke test scripts (e.g., `test_cs_emitter_smoke.py`)
- Per-language fixture emit checkers

All can be replaced by `runtime_parity_check_fast.py --targets <lang>`. Creating custom scripts means results are not accumulated in `.parity-results/` and are not reflected in the progress matrix.

The transpile stage is executed via in-memory calls to the toolchain2 Python API, eliminating process startup and disk I/O.

```bash
# sample parity
PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py \
  --targets <lang> --case-root sample
```

### fixture Parity Check

All test cases in `test/fixture/source/py/` (146+ cases) can also be verified for all languages with the same tool. `ng_*` (negative tests) are automatically skipped. Partial execution by category is possible with `--category`.

```bash
# fixture parity (by category)
PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py \
  --targets <lang> --category oop

# fixture parity (all)
PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py \
  --targets <lang>
```

### stdlib Parity Check

stdlib module tests in `test/stdlib/source/py/` can also be verified with the same tool. There is a separate folder per module.

```bash
# stdlib parity (all)
PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py \
  --targets <lang> --case-root stdlib
```

### All Three Parities Are Required

During emitter development, run parity checks for **all three of fixture, sample, and stdlib**. Use the default optimization level (1). **Do not specify optimization options such as `--opt-level`.**

```bash
# fixture — comprehensive tests of language features
PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py \
  --targets <lang>

# sample — real applications
PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py \
  --targets <lang> --case-root sample

# stdlib — Python standard library compatibility modules
PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py \
  --targets <lang> --case-root stdlib
```

**The Python row in the selfhost matrix becomes PASS only when all of fixture + sample + stdlib PASS.** If any one FAIL is present, FAIL is displayed.

Results are automatically accumulated in `.parity-results/` and reflected in the progress matrix by `tools/gen/gen_backend_progress.py`.

### Sample Benchmark

Sample execution time is automatically measured during the sample run of the parity check and recorded in `elapsed_sec` in `.parity-results/<target>_sample.json`. At the end of the parity check, `tools/gen/gen_sample_benchmark.py` is automatically run and updates the benchmark table in `sample/README-ja.md` / `sample/README.md` (only when more than 10 minutes have elapsed since the last generation).

### Removal of the Skip List

The `_LANG_UNSUPPORTED_FIXTURES` skip mechanism has been removed. All fixtures are run for all languages; if they FAIL, that is recorded as FAIL in `.parity-results/` and reflected in the progress matrix. Problems are not hidden by skipping.

### What Is Verified

`runtime_parity_check.py` automatically performs the following:

1. Runs the case in Python and records stdout and artifacts (`sample/out/*.png`, `*.gif`, `*.txt`)
2. Transpiles → compiles → runs in the target language
3. Normalized comparison of stdout (timing lines such as `elapsed_sec` are excluded)
4. Size + CRC32 comparison of artifacts

### Emit-Only Fixtures (`eo_` Prefix)

Fixtures whose file name starts with `eo_` are **emit-only**. Neither Python execution nor target execution is performed; only successful emit (transpile) is verified.

Use case: items such as `@extern class` that have no implementation and cannot be run even in Python, but for which successful emit must be guaranteed.

```
test/fixture/source/py/oop/eo_extern_opaque_basic.py  ← emit-only
test/fixture/source/py/oop/class_instance.py           ← normal (run parity)
```

### Relationship to Existing Tools

| Tool | Purpose | Authoritative? |
|---|---|---|
| `tools/check/runtime_parity_check.py` | All-language parity check (stdout + artifact) | **Authoritative** |
| `tools/run/run_selfhost_parity.py` | Parity check using selfhost binary | **Authoritative** (selfhost verification) |
| `tools/benchmark_sample_cpp_rs.py` | C++/Rust execution-time benchmark | Separate responsibility (not parity) |
| `tools/gen/regenerate_samples.py` | Regeneration of sample/py → sample/<lang> | Regeneration only (does not run) |

Use `runtime_parity_check.py` for parity verification during emitter development, and `run_selfhost_parity.py` for selfhost verification. Creating custom scripts is prohibited.

### Parity Test Completion Criteria

**"emit succeeded" alone does not mean parity is complete.** The completion criteria require all of the following to pass:

1. **emit**: Target-language source code is generated (no errors)
2. **compile**: Generated code passes compilation (Go: `go build`, C++: `g++`, Rust: `rustc`, etc.)
3. **run**: Compiled binary executes (no crash)
4. **stdout match**: Execution stdout matches the Python execution result (`elapsed_sec` etc. excluded)
5. **artifact match**: Size + CRC32 of generated files (PNG/GIF/TXT) match Python

Even if emit succeeds alone, placeholder code (e.g., `nil /* list comprehension */`) may have been inserted. Always confirm through compile + run + stdout match.

### Selfhost Parity

The ultimate selfhost goal is to "transpile toolchain2 itself to the target language, and use that binary to convert fixture/sample with parity PASS." The verification tool is `tools/run/run_selfhost_parity.py`.

```bash
# fixture parity with C++ selfhost
python3 tools/run/run_selfhost_parity.py \
  --selfhost-lang cpp --emit-target cpp --case-root fixture

# sample parity with Go selfhost
python3 tools/run/run_selfhost_parity.py \
  --selfhost-lang go --emit-target go --case-root sample

# Python selfhost (aggregate existing parity results)
python3 tools/run/run_selfhost_parity.py --selfhost-lang python
```

Selfhost completion criteria require all of the following to pass:

1. **emit**: All toolchain2 `.py` files can be emitted to the target language
2. **build**: Generated code can be compiled and linked
3. **golden**: Emit results match golden (regression test)
4. **fixture parity**: Use the selfhost binary to convert fixtures; stdout + artifact match Python execution results
5. **sample parity**: Same as above (sample)

Golden alone (regression test for emit success) does not constitute selfhost completion. Confirm that the selfhost binary actually produces correct output using `run_selfhost_parity.py`.

## 14. Checklist

Checklist when implementing a new emitter:

- [ ] `emit_<lang>_module()` is defined in `src/toolchain2/emit/<lang>/emitter.py`
- [ ] No hard-coded module names such as `pytra.std.*` in import paths
- [ ] Aliases are resolved using `build_import_alias_map`
- [ ] Relative paths for submodules are generated using `emit_context.root_rel_prefix`
- [ ] `_native` delegation code is generated for `@extern` functions
- [ ] `VarDecl` / `Swap` / `discard_result` / `unused` / `mutates_self` are handled
- [ ] Languages with immutable parameters use `collect_reassigned_params` + `mutable_param_name`
- [ ] No individual `_copy_runtime` (automatic copy with `lang=`)
- [ ] Image runtime (PNG/GIF) is not hand-written (§6; generated code only)
- [ ] Default output directory is `work/tmp/<lang>` (`out/` is prohibited)
- [ ] Containers (list/dict/set) are held in reference-type wrappers (§10)
- [ ] Type assertions are generated for Call nodes with `yields_dynamic: true` (§11)
- [ ] No type-inference workarounds in the emitter (math return-type determination, VarDecl look-ahead, etc.) (§12)
- [ ] fixture verification done with `runtime_parity_check_fast.py --targets <lang>` (§13)
- [ ] sample verification done with `runtime_parity_check_fast.py --targets <lang> --case-root sample` (§13)
- [ ] stdlib verification done with `runtime_parity_check_fast.py --targets <lang> --case-root stdlib` (§13)
- [ ] Zero emitter lint findings confirmed with `check_emitter_hardcode_lint.py --lang <lang>` (§14.1)

### 14.1 Emitter Hardcode Lint

A lint that detects locations in an emitter where module names, runtime function names, class names, etc. are written as string literals without using EAST3 information.

```bash
# Your language only (lightweight, a few seconds)
python3 tools/check/check_emitter_hardcode_lint.py --lang <lang>

# All languages + runtime source scan (heavy, 1-2 minutes)
python3 tools/check/check_emitter_hardcode_lint.py --include-runtime
```

Results are written to `docs/ja/progress-preview/emitter-hardcode-lint.md` (gitignored; disk only).

**Lint is run manually, separate from parity checks.** Parity checks focus on verifying transpile + compile + run; lint is not included. Batch lint execution is also available via `run_local_ci.py`.

10 categories:

| Category | Content |
|---|---|
| module name | Hard-coded module name strings |
| runtime symbol | Hard-coded runtime function names |
| target const | Hard-coded target constants |
| prefix match | Prefix branching on `pytra.std.` etc. |
| class name | Hard-coded class names |
| Python syntax | Python syntax string matching |
| type_id | Hard-coded type_id constants |
| skip pure py | Pure Python modules in mapping.json's skip_modules |
| rt: type_id | type_id remnants in runtime source (only with `--include-runtime`) |
| rt: call_cov | Cross-referencing mapping.json's calls against EAST3 golden |

## 15. Per-Language FAQ

Common questions and answers when implementing a new emitter.

### How should isinstance be implemented?

The emitter uses the target language's native type-checking facility. `PYTRA_TYPE_ID` / `pytra_isinstance` / `type_id_table` are deprecated and must not be used in new emitters (see [spec-adt.md](./spec-adt.md) §3, §6).

| Language | isinstance implementation |
|---|---|
| C++ | `std::holds_alternative<T>(v)` (after variant migration) |
| Rust | `if let Enum::Variant(x) = v` / `match` |
| Go | `switch v := x.(type)` |
| TS/JS | `instanceof` / `typeof` |
| C# | `x is Type t` |
| Java | `x instanceof Type t` |
| Swift | `if case let .variant(x) = v` |

isinstance subtype rules do not change:
- **`bool` is not a subtype of `int`.** `isinstance(True, int)` is `False` in Pytra (see [spec-python-compat.md](./spec-python-compat.md)).
- All primitive types are leaf types and have no subtype relationships with each other.

### How should enum / IntEnum be output?

Output as constant groups (e.g., `public static final long RED = 1;`). Do not map to the target language's enum type (Java `enum`, C# `enum`, Rust `enum`). Reasons:
- `IntEnum` allows arithmetic operations (`Color.RED + 1`); using a language enum type becomes cumbersome.
- In EAST3, an enum is represented as a normal class with constant fields.
- Prioritize getting fixtures to pass quickly.

### How should property / super / trait be output?

Map to the target language's straightforward inheritance / interfaces:
- `@property` → getter method (Java: `getX()` / C#: property)
- `super().__init__()` → parent class constructor call
- `@trait` → interface (Java: `interface` / C#: `interface` / Go: `interface`)
- `@implements` → implements / interface implementation in the constructor

Map EAST3 nodes directly. Emitters must not hold their own inheritance-resolution logic.

### Are containers (list/dict/set) value types or reference types?

Default to reference-type wrappers (see §10). Per-language representations:
- C++: `Object<list<T>>`
- Go: `*PyList[T]`
- Java: `PyList<T>` (reference type by default)
- C#: `PyList<T>` (reference type by default)
- Rust: `Rc<RefCell<Vec<T>>>`
- TS/JS: plain arrays (JS arrays are reference types)

### How should functions with no return-type annotation be handled?

`-> None` may be omitted. If the body contains no `return <value>`, resolve infers `None`. By the time the emitter is reached, `return_type` is always determined (see §1.2).

### When the return value of `dict.get()` or `list.pop()` is Any/object, how should I cast it?

Simply generate a type assertion by looking at the EAST3 `yields_dynamic: true` flag (see §11). The emitter must not self-determine "this call returns Any, so a cast is needed." If `yields_dynamic` is absent, no cast is needed; if present, output a downcast to `resolved_type`.

```java
// yields_dynamic: true, resolved_type: int64 case
// Java: (long) dict.get(key)
// Go: dict.Get(key).(int64)
// TS: dict.get(key) as number
```

### What should be done when `>>` is a signed right-shift in a given language?

Python's `>>` always behaves as an unsigned right shift (Python integers have arbitrary precision, so there is no sign bit issue). However, in JS/TS `>>` is a signed right shift, which causes incorrect behavior in CRC32 calculations etc.

Correct fix: **Convert `>>` to an unsigned right shift in the emitter.** Do not modify the authoritative source (`src/pytra/`).

| Language | Fix |
|---|---|
| JS/TS | Convert EAST3 `RShift` → `>>>`. `>>=` → `>>>=` |
| Java | Convert `>>` → `>>>` (Java also has `>>>`) |
| C++/Go/Rust/C# | `>>` works as-is (integers are fixed-size, usually not a problem; cast to unsigned if needed) |

Example: The TS emitter resolved CRC32 calculation in `src/pytra/utils/png.py` by converting `>>` → `>>>` (2026-03-30).

### Is it permissible to skip compiler type checks or linters?

**Prohibited.** Parity checks verify "does the generated code work correctly"; skipping type checks or linters allows incorrect code to PASS.

- `tsc --noCheck` is prohibited (prevents detection of TS type errors)
- Suppressing warnings with `rustc --allow` is permitted, but suppressing errors is prohibited
- `g++ -fpermissive` is prohibited
- Ignoring errors from `go build` is prohibited

If type checks or compilation produce errors, fix the emitter's output. Skipping checks to gain parity PASS is self-defeating.

### Are dependencies on package managers such as npm / pip / cargo prohibited?

**Prohibited.** Generated code, runtimes, and build tools must not have dependencies on external package managers.

- `npm install` / `npx` prohibited. Use the globally installed `tsc` and `node` on the system.
- `pip install` prohibited. Only the Python standard library and `pytra.std.*` may be used.
- `cargo add` prohibited. Only the Rust standard library.
- If generated code depends on external crates / npm packages / pip packages, the design is wrong.

The same applies to parity checks. `runtime_parity_check_fast.py` uses only system tools such as `tsc` + `node`, `g++`, `go`, `rustc`, etc.

### The generated code in sample looks messy. How much should I care about quality?

`sample/<lang>/` is a showcase for Pytra. Eliminate all NG patterns from §1.4 and aim for a level that a programmer familiar with the target language finds natural. Specifically:
- `int64(0)` → `0` (remove unnecessary POD casts)
- `(a) + (b)` → `a + b` (remove redundant parentheses)
- `int64{}` → `0` (literal rather than default constructor)
