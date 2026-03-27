# About the Runtime Specification

<a href="../../ja/spec/spec-runtime.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

### 0. Source of truth and responsibility boundary

The only runtime source of truth (SoT) is the following pure Python module set:

- `src/pytra/built_in/*.py`
- `src/pytra/std/*.py`
- `src/pytra/utils/*.py`

Mandatory rules:

- If logic can be written in the SoT, do not manually reimplement it on the runtime side.
- Backends / emitters must only render module / symbol / signature information that has already been resolved in EAST.
- Do not hardcode conversion tables or special branches for library function names, module names, or type names inside backend / emitter code.
- Do not embed knowledge such as `math`, `json`, `gif`, `png`, `Path`, `assertions`, `re`, or `typing` into the transpiler source code.

### 0.5 Runtime placement classification

Across all languages, runtime placement is unified into the following four responsibility buckets:

- `core`
  - low-level runtime / ABI / object representation / GC / I/O / OS / SDK glue, etc.
  - not a storage location for reimplementing the SoT
- `built_in`
  - runtime responsibilities corresponding to `src/pytra/built_in/*.py`
- `std`
  - runtime responsibilities corresponding to `src/pytra/std/*.py`
- `utils`
  - runtime responsibilities corresponding to `src/pytra/utils/*.py`

Representative placement:

- default / legacy:
  - `src/runtime/<lang>/core/`
  - `src/runtime/<lang>/built_in/`
  - `src/runtime/<lang>/std/`
  - `src/runtime/<lang>/utils/`
- language-independent generated intermediate form (`.east`):
  - `src/runtime/east/{built_in,std,utils}/`
- current C++ runtime (handwritten only):
  - `src/runtime/cpp/{core,built_in,std,compiler}/`

Notes:

- `.east` files are language-independent EAST3 JSON intermediate representations. They are converted into each target language at link time.
- `runtime/<lang>/` contains only handwritten language-specific code. The `native/` / `generated/` hierarchy has been abolished there.
- `built_in/std/utils` are SoT-derived responsibility buckets, and equivalent logic must not be duplicated in `core/`.

### 0.6 Runtime file naming rules

Ownership representation for runtime files:

- `.east` files (`src/runtime/east/`):
  - EAST3 JSON generated from `src/pytra/` Python sources by `pytra compile`
  - converted to each target language at link time
  - manual edits forbidden
- handwritten files (`src/runtime/<lang>/`):
  - target-language-specific runtime code
  - handwritten

### 0.6a Current runtime layout structure

Intermediate representations generated from SoT (Python source) are aggregated under `src/runtime/east/`, and handwritten runtime code specific to each language is placed under `src/runtime/<lang>/`. The old directory split between `generated/` and `native/` has been abolished.

Current layout:

- `src/runtime/east/{built_in,std,utils}/` — `.east` files generated from the SoT. Manual edits forbidden.
- `src/runtime/<lang>/{built_in,std,core,...}/` — handwritten runtime code for each target language.

Handling of `@extern` functions:

- `@extern` functions use the SoT Python body as a reference implementation, while the actual target-language implementation is provided by handwritten runtime code.
- **C++**: the emitter outputs only the declaration of an `@extern` function and connects the implementation via handwritten `.h` includes, because C++-specific features such as templates and overloads are used.
- **Other languages**: the emitter generates delegation code for `@extern` functions toward a `_native` module, for example `time.js` calling `perf_counter()` in `time_native.js`.
- The delegation target file name must use the `_native` suffix (for example `os` -> `os_native`). See `spec-abi.md §3.2.1` for details.

Mandatory rules:

- `.east` files must not be edited manually; regenerate them from the Python source in `src/pytra/`.
- Do not duplicate full SoT-equivalent logic in handwritten runtimes. Restrict them to minimal host-API connection code.
- Backend-internal typed-handle helpers such as `rc<list<T>>` may be placed in `core/`.

### 0.6c `emit_context` — module information during multi-module emit

`emit_all_modules` (`src/toolchain/emit/loader.py`) takes `manifest.json` (formerly `link-output.json`) as input and writes each module into the `emit/` directory (see `spec-folder.md §2.8`). Before each module is emitted, the following information is stored in `meta.emit_context` of the EAST3 doc:

```json
{
  "module_id": "os",
  "root_rel_prefix": "../",
  "is_entry": false
}
```

| Field | Type | Meaning |
|---|---|---|
| `module_id` | str | Module ID (for example `"os"`, `"pytra.std.time"`) |
| `root_rel_prefix` | str | Relative path to the output root (for example depth=0 -> `"./"`, depth=1 -> `"../"`, depth=2 -> `"../../"`) |
| `is_entry` | bool | Whether this is the entry module (contains `main`) |

Mandatory rules:

- Emitters must resolve inter-submodule import paths as `root_rel_prefix + target_module_path`.
- Emitters must not compute module placement on their own. `emit_context` is the source of truth.
- `root_rel_prefix` is calculated automatically by `emit_all_modules` from the dot-depth of `module_id`.

### 0.6b Current layout of the C++ runtime

`src/runtime/cpp/` uses the following structure as the source of truth:

- `src/runtime/cpp/core/` — handwritten low-level runtime (`object.h`, `list.h`, `py_types.h`, etc.)
- `src/runtime/cpp/built_in/` — handwritten built-in function implementations (`io_ops.h`, `scalar_ops.h`, etc.)
- `src/runtime/cpp/std/` — handwritten stdlib implementations (`time.h`, `glob.cpp`, etc.)

Mandatory rules:

- Place handwritten core only under `core/`.
- Place C++ implementations of `@extern` functions under `built_in/` or `std/`.
- Checked-in `runtime/cpp/core/*.h` and `runtime/cpp/pytra/core/*.h` must not be reintroduced.
- Compiler paths, generated runtime, native companions, and backend output must include `runtime/cpp/native/core/...` directly.
- `generated/core` / `generated/built_in` artifacts may be generated only through the canonical `src/pytra-cli.py --emit-runtime-cpp` path; do not add module-specific generators or ad-hoc templates.
- Checked-in `generated/core` / `generated/built_in` artifacts require plain naming plus `source:` / `generated-by:` markers.
- If an export-time SDK surface is needed, generate it from the runtime symbol index / manifest; do not keep compatibility shims in the source tree.

### 0.61 Include / reference rules

- Backends / build scripts / transpiler code must reference required runtime files through the canonical names whose ownership is distinguishable.
- Do not add short unsuffixed aliases just because they are easier for humans to type.
- Include / compile targets must remain uniquely determined by the current ownership scheme of the target.

Additional C++ rules:

- The includes used by generated code must be fixed to the direct ownership headers returned by the runtime symbol index (for example `generated/std/time.h`, `generated/utils/png.h`, `native/core/dict.h`).
- The low-level prelude uses `runtime/cpp/native/core/py_runtime.h` as the source of truth.
- Real-path resolution for `generated/` / `native/` belongs to the runtime symbol index and build graph; emitters must not hardcode it ad hoc.
- `--emit-runtime-cpp` writes only generated artifacts to `src/runtime/cpp/generated/...`. `native/` is a place for companion implementations, not an auto-generation output target.
- `runtime_symbol_index` / build graph must keep C++ `public_headers == compiler_headers` and derive compile sources from those direct ownership headers.
- `check_runtime_cpp_layout.py` must fail if `src/runtime/cpp/{core,pytra}` reappears, and at the same time audit the ownership boundary between `generated` and `native`.
- Do not add new include roots to the C++ runtime. The checked-in surface must be limited to direct ownership paths.

### 0.62 Boundary between `core` and module companions

- The C++ low-level runtime is expressed by `generated/core` and `native/core`; there must be no standalone checked-in `core/` surface.
- Module companion implementations for `std/utils/built_in` belong under `native/` in the C++ module runtime.
- Only module-independent ABI / object / container / I/O / OS glue may be placed under `generated/core` / `native/core`.
- Backend-internal alias-preservation layers such as `rc<list<T>>` helpers may be placed under `native/core`, but must be documented as not being ABI boundaries.
- `native/*.h` must be limited to cases that truly require templates / inline helpers; the source of truth for declarations should generally live under `generated/*.h`.
- `native/core/*.h` may define the source of truth for object / container representations and low-level helpers, but must not reabsorb high-level module runtime.
- `generated/core/*.h|*.cpp` may be introduced only where there are real candidates, and SoT markers are mandatory.

Additional `py_runtime` rules:

- `src/runtime/cpp/native/core/py_runtime.h` is the canonical header for the low-level runtime, not the source of truth for high-level built-in semantics.
- The only things allowed to remain in `src/runtime/cpp/native/core/py_runtime.h` are `PyObj` / `object` / `rc<>` / `type_id` / low-level container primitives / dynamic iteration / process I/O / C++ stdlib and OS glue.
- Helpers expressible in pure Python, such as `str::split` / `splitlines` / `count` / `join` and `zip` / `sorted` / `sum` / `py_min` / `py_max`, must not remain permanently in `native/core/py_runtime.h`; they must be treated as candidates for `generated/built_in` or moving back into the SoT.
- Generic helpers such as `sum/min/max/zip/sorted` use `@template("T", ...)` + linked-program specialization as the primary lane. Do not prolong their life by adding new handwritten template helpers to `native/core/py_runtime.h`.
- Helpers tightly coupled to `object` / `std::any` / template specialization, such as `dict_get_*`, `py_dict_get_default`, `py_ord`, `py_chr`, `py_div`, `py_floordiv`, and `py_mod`, must not be moved prematurely before a `generated/core` lane is properly designed. They may remain in the deferred category.
- `generated/core` is not “the new place to dump low-level helpers.” Do not push in helpers that need direct `native/core` includes or target-specific ownership.
- `check_runtime_cpp_layout.py` must also verify that `native/core/py_runtime.h` has not reintroduced removed transitive includes from `predicates`, `sequence`, or `iter_ops`. `string_ops` is temporarily allowed because of `str` method delegates, but other built-in companions must not be pulled back into the aggregator.

### 0.621 Emission-lane contract for `generated/built_in` and `generated/core`

When slimming `py_runtime`, the destination lane for helpers is fixed as follows:

- `generated/built_in`
  - The SoT lives in `src/pytra/built_in/*.py`.
  - Its role is to materialize checked-in C++ artifacts for built-in semantics that can be expressed in pure Python, such as `str::split` / `splitlines` / `count` / `join`, and object-specialized `zip` / `sorted` / `sum` / `min` / `max`.
  - Generic helpers must not expose the raw `@template` surface directly to the backend. They must be materialized as specialized helper artifacts after linked-program specialization. The backend must not reimplement the specialization collector.
  - Template-only modules may be header-only generated artifacts, and `compile_sources=[]` may be canonical. Do not fabricate empty `.cpp` files for helpers such as `numeric_ops` or `zip_ops`.
  - `.h` files may include stable `native/core/*.h` and, if needed, only the same-module `native/<bucket>/*.h` companion. Do not hang legacy shim paths or unrelated handwritten glue off them.
  - `.cpp` files may include `runtime/cpp/native/core/py_runtime.h` and sibling generated headers, but must not embed C++-specific handwritten glue.
  - If a helper wants to receive mutable containers by value at the boundary, it must use an explicit contract such as `@abi`. Do not expose the backend’s ref-first internal representation as a stable helper ABI.
- `generated/core`
  - The SoT is limited to low-level helpers that can still be written in pure Python; it must not be used as a migration target for ordinary `built_in` / `std` / `utils` module runtime.
  - There must be no checked-in `runtime/cpp/core/*.h`; include surfaces must stay in the ownership lanes of `generated/core` or `native/core`.
  - Helpers that cross ownership of `object` / `rc<>` / container representation / GC / exceptions / process I/O must not be moved into `generated/core` prematurely.
  - `generated/core` is for “low-level helpers that still close as pure helpers,” not a pressure valve for `native/core/py_runtime.h` bloat without lane design.
- Common:
  - The build graph / runtime symbol index derive compile sources from direct ownership headers (`public_headers` / `compiler_headers`); emitters must not synthesize paths ad hoc.
  - The decision to move a helper depends not only on “can it be written in pure Python?” but also on whether it preserves a stable include surface and avoids introducing new ownership / ABI glue.

### 0.622 JSON dynamic boundary and the `JsonValue` common ADT

Note:

- This section defines an approved next-step target design.
- As of 2026-03-08, the current implementation may still keep some `json.loads()` paths returning `object`.
- However, all new implementations, new helpers, and new runtime additions must follow this section as the canonical contract.

In Pytra, which assumes static typing, JSON dynamic behavior must not be spread into general `object` helpers. Dynamic boundaries derived from JSON are confined to the JSON-specific surface `JsonValue` / `JsonObj` / `JsonArr`.

Mandatory rules:

- Do not add user-facing dynamic built-in helpers such as `sum(object)`, `zip(object, object)`, `sorted(object)`, or object-overloaded `dict.keys/items/values` for the sake of JSON.
- Do not apply built-ins / operators / collection helpers directly to `object` values. User code must first decode into a concrete type.
- Do not change the semantics of plain assignment by introducing implicit casts for JSON decoding.
- Do not add handwritten fallback helpers to `native/core/py_runtime.h` because of JSON’s dynamic nature.

Common ADT:

- `JsonValue`
  - `Null`
  - `Bool`
  - `Int`
    - payload type: `int64`
  - `Float`
    - payload type: `float64`
  - `Str`
  - `Obj`
  - `Arr`
- `JsonObj`
  - semantically `dict[str, JsonValue]`
- `JsonArr`
  - semantically `list[JsonValue]`

Source-surface policy:

- The long-term canonical form of `json.loads(...)` is `JsonValue`, not general `object`.
- The public module root remains `pytra.std.json`. Even if `json` gets a JSON-specific nominal surface, it must not be moved to `utils/json.py`.
- The reason is that `json` belongs to the stdlib-compatibility family, not to Pytra-specific utilities. Even with a Pytra-specific decode-first contract, the public namespace remains under `std`.
- User code must extract values through the `JsonValue` / `JsonObj` / `JsonArr` decode API.
- There is no need to introduce a general-purpose `cast` first just for JSON.
- Required narrowing should be concentrated into JSON-module-specific APIs.

v1 decode surface (exact API):

- `JsonValue.as_obj() -> JsonObj | None`
- `JsonValue.as_arr() -> JsonArr | None`
- `JsonValue.as_str() -> str | None`
- `JsonValue.as_int() -> int | None`
- `JsonValue.as_float() -> float | None`
- `JsonValue.as_bool() -> bool | None`
- `JsonObj.get(key: str) -> JsonValue | None`
- `JsonObj.get_obj(key: str) -> JsonObj | None`
- `JsonObj.get_arr(key: str) -> JsonArr | None`
- `JsonObj.get_str(key: str) -> str | None`
- `JsonObj.get_int(key: str) -> int | None`
- `JsonArr.get(index: int) -> JsonValue | None`
- `JsonArr.get_obj(index: int) -> JsonObj | None`
- `JsonArr.get_arr(index: int) -> JsonArr | None`
- `JsonArr.get_str(index: int) -> str | None`
- `JsonArr.get_int(index: int) -> int | None`
- `JsonArr.get_float(index: int) -> float | None`
- `JsonArr.get_bool(index: int) -> bool | None`

Notes:

- `loads`, `loads_obj`, `loads_arr`, `JsonValue.as_*`, `JsonObj.get_*`, and `JsonArr.get_*` are the canonical v1 API names.
- v1 prioritizes decodeability through those helpers without depending on general-purpose `cast` or `match`.
- It is acceptable to add `match`-based narrowing later, but that would only be a convenience for decoding `JsonValue`, not a reason to revive dynamic helpers.
- JSON number classification is fixed as follows:
  - a number without a decimal point or exponent is interpreted as `JsonValue.Int(int64)`
  - a number with a decimal point or exponent is interpreted as `JsonValue.Float(float64)`
  - integers outside the `int64` range are parse errors
  - `NaN` / `Infinity` / `-Infinity` are invalid JSON and must not be accepted

Backend lowering policy:

- `JsonValue` is defined as a common target-independent ADT, and each backend lowers it into a natural tagged union / enum / variant in that language.
- The v1 priority implementation order is `C++ -> Rust -> Swift -> Nim`.
- The canonical concrete carriers for v1 are:
  - C++:
    - `class JsonValue` + `std::variant<::std::monostate, bool, int64, float64, str, rc<JsonObj>, rc<JsonArr>>`
    - `JsonObj` is a nominal wrapper holding `dict<str, JsonValue>`
    - `JsonArr` is a nominal wrapper holding `list<JsonValue>`
  - Rust:
    - `enum JsonValue { Null, Bool(bool), Int(i64), Float(f64), Str(String), Obj(BTreeMap<String, JsonValue>), Arr(Vec<JsonValue>) }`
  - Swift:
    - `indirect enum JsonValue { case null, bool(Bool), int(Int64), float(Double), str(String), obj([String: JsonValue]), arr([JsonValue]) }`
  - Nim:
    - a tagged union using `ref object` + `kind`
    - `obj` uses `Table[string, JsonValue]`, `arr` uses `seq[JsonValue]`
- Implementations may temporarily use `object` or `dict[str, object]` / `list[object]` as internal carriers, but only as backend/runtime internals.
- The user-facing surface must use nominal `JsonValue` types as the source of truth and must not expose a general `object` surface.

Relationship with `py_runtime.h`:

- `sum(object)` / `zip(object, object)` / object-overloaded `dict.keys/items/values` must not become permanent APIs.
- They may remain temporarily only as legacy compatibility debt and must be moved gradually toward compile errors.
- User code that uses `json.loads()` must be able to go through the `JsonValue` decode API rather than dynamic helpers.
- `native/core/py_runtime.h` may keep only the minimum implementation of JSON carriers and low-level bridges, and must not keep user-facing dynamic algorithm helpers.

Examples of mistakes:

- placing the companion implementation of `std/math` under `core/`
- handwriting the body of `utils/png` inside `core/`
- embedding `built_in`-derived logic into `py_runtime`
- indiscriminately escaping even low-level helpers into `generated/built_in` just to avoid `py_runtime` bloat

### 0.63 Special generation scripts are forbidden

- Do not add module-specific runtime generation scripts that bypass `src/pytra-cli.py` / the future unified CLI.
- Modules such as `png.py`, `gif.py`, `json.py`, and `math.py` must always generate their canonical runtime artifacts through the canonical transpiler path.
- Do not add language-specific naming rules or special templates just for runtime generation.

### 0.64 `__all__` is forbidden under `src/pytra`

`__all__` must not be defined in `src/pytra/**/*.py`.

- Prioritize simplicity of the selfhost implementation and transpiler implementation.
- Control of public symbols is expressed by whether top-level definitions exist.
- The same rule applies to SoT modules in `built_in/std/utils`.

### 0.65 Host-only import alias rule (`as __name`)

Imports such as `import ... as __m` or `from ... import ... as __f`, where the alias starts with `__`, are treated as host-only imports.

- Host-only imports are exclusively for Python-runtime support.
- Their main purpose is evaluating the Python fallback body of `@extern` functions.
- The transpiler must not emit host-only imports as EAST `Import` / `ImportFrom`.
- A single underscore alias such as `_name` is not host-only.

### 0.66 Stdlib submodule implementation rules

Stdlib submodules such as `os.path` are treated as independent SoT modules.

Mandatory:

- Split submodules into `src/pytra/std/<name>.py`.
  - For example: `os.path` -> `src/pytra/std/os_path.py`
- The parent module references them through module import.
  - For example: `from pytra.std import os_path as path`
- Calls remain module function calls.
  - For example: `path.join(...)`
- Functions that require native implementations are declared with `@extern` on the SoT side, and their bodies live in the corresponding companion layer on the runtime side.
  - In the C++ module runtime, that means `native/`
- `extern_contract_v1` / `extern_v1` are declaration-only metadata and must not represent the native owner implementation location.
- Ambient-global variable declarations via `extern()` / `extern("symbol")` are separate from runtime-SoT `@extern` and must not be mixed into native owner resolution in the runtime symbol index.

Forbidden:

- storing submodules in `object` variables
- adding special branches in emitters / runtimes that depend on submodule names

### 0.67 Internal representation policy for mutable types

The internal representation used in runtime / backend internals is decided separately from the canonical ABI form by the following principles.

Mandatory rules:

- immutable types may be value-first
  - for example: `bool`, `int`, `float`, `str`
- mutable types are ref-first
  - for example: `list`, `dict`, `set`, `bytearray`, mutable user classes
- in the C++ backend, `rc<>` or equivalent typed handles may be used as the ref-first representation
- however, this is an internal backend representation, not an ABI, and must not be exposed directly at `@extern` or cross-language boundaries

Value lowering is allowed only as an optimization result.

- mutable types must not be treated as value types from the start
- value lowering requires mutation / alias / escape analysis
- interprocedural lowering requires a call graph and SCC fixed-point computation
- any path crossing unknown calls, `Any`, `object`, `@extern`, or external SDK boundaries must fail closed and remain ref-first

Notes:

- Holding immutable types such as `str` by value is not equivalent to holding `list` / `dict` by value.
- For types whose destructive update can be observed after `a = b`, shared references are the source of truth.
- Do not break the order of “start ref-first, then lower only the proven-safe paths to stack/value.”

### 0.68 Responsibility boundary between the runtime symbol index and backends

The module ownership and target artifacts of runtime symbols are governed by `tools/runtime_symbol_index.json`.

Mandatory rules:

- IR holds target-independent `runtime_module_id` and `runtime_symbol`.
- Backends receive `runtime_module_id` / `runtime_symbol` and derive target-specific include paths / compile sources / companions from the index.
- Do not embed target-specific paths such as `runtime/cpp/generated/std/time.h` into IR.
- Do not re-hardcode module ownership mappings such as `py_enumerate -> iter_ops` inside backend/emitter source.
- The only things backends/emitters are allowed to decide are target-specific rendering names, namespaces, and syntax.

Runtime metadata that backends may interpret:

- `runtime_module_id`
- `runtime_symbol`
- declaration-only `extern_contract_v1` / `extern_v1`
- `semantic_tag`
- `runtime_call`
- `resolved_runtime_call`
- `resolved_runtime_source`
- adapter kind / ABI kind / import-binding metadata added by the linker/lowerer

Source-side knowledge that backends must not interpret:

- source import names themselves
  - for example `math`, `pytra.utils`, `pytra.std.math`
- source module-attribute spellings
  - for example `.pi`, `.e`, `.sqrt`
- helper-specific names
  - for example `pyMathPi`, `pyMathE`, `save_gif`, `write_rgb_png`, `grayscale_palette`
- ad-hoc rules for guessing helper argument ABI
  - for example letting an emitter interpret `save_gif` arity / defaults / keywords (`delay_cs`, `loop`) directly

Notes:

- It is acceptable to map `resolved_runtime_call` or `semantic_tag` into target symbols.
- But that mapping must follow metadata decided by the index / lowerer, not string matches against source-side module names or helper names.

Responsibility split:

- IR:
  - `runtime_module_id`
  - `runtime_symbol`
  - minimum dispatch information
- runtime symbol index:
  - public symbols per module
  - target-specific `public_headers`
  - target-specific `compile_sources`
  - `gen/ext` companions
- backend/tooling:
  - dedupe / sort of includes
  - rendering of namespace strings
  - build-graph construction

Policy for non-C++ backends:

- While C++ leads the implementation, other backends are also aligned to the same `runtime_module_id + runtime_symbol + index` contract.
- Non-C++ backends may have target-specific public import/package paths, but that resolution belongs to the index-consumer layer.
- Do not reimplement `resolved_runtime_call` or module/file-path mappings as separate handwritten tables per backend.
- What differs by target is “how to import it” and “how to render its fully qualified name,” not “which module owns the symbol.”
- Target helper names such as `pyMath*`, `scala.math.*`, or `png_helper` may appear in final rendered output, but must not remain in emitter source of truth as branch conditions on source module names or helper ABI.

### 0.7 Operation of the C++ runtime

The canonical placement of the C++ runtime is:

- `src/runtime/cpp/generated/{built_in,std,utils,core}/`
- `src/runtime/cpp/native/{built_in,std,utils,core}/`

Regeneration:

- SoT-derived modules in `built_in/std/utils/core` are generated into `generated/` via `--emit-runtime-cpp`.
- Examples:
  - `python3 src/pytra-cli.py src/pytra/built_in/type_id.py --target cpp --emit-runtime-cpp`
  - `python3 src/pytra-cli.py src/pytra/std/math.py --target cpp --emit-runtime-cpp`
  - `python3 src/pytra-cli.py src/pytra/utils/png.py --target cpp --emit-runtime-cpp`

Minimum verification:

- `python3 tools/check_runtime_cpp_layout.py`
- `python3 tools/check_runtime_std_sot_guard.py`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

Forbidden:

- manual edits under `src/runtime/cpp/generated/**`
- reimplementing SoT-equivalent logic under `src/runtime/cpp/native/core/**` or `src/runtime/cpp/native/{built_in,std,utils}/**`
- reintroducing checked-in `src/runtime/cpp/{core,pytra}/**`
- direct module / symbol name resolution in backends / emitters
- adding module-specific scripts for runtime generation

### 0.71 Applying this to multi-language runtimes

This classification and naming rule is not C++-specific; it expands to all language runtimes.

- The canonical target layout is `src/runtime/<lang>/generated/**` and `src/runtime/<lang>/native/**`.
- The baseline end state for non-C++ runtimes is that `generated = baseline`, with the module set of `cpp/generated/{built_in,std,utils}` as the baseline.
- For baseline modules, `blocked`, `compare_artifact`, `no_runtime_module`, `helper_artifact`, and `native canonical` must not be used as close conditions.
- The blocked/native/helper descriptions kept by `src/toolchain/misc/noncpp_runtime_layout_contract.py` and `src/toolchain/misc/noncpp_runtime_layout_rollout_remaining_contract.py` are legacy inventory, not active end-state policy.
- `pytra-gen/pytra-core` and checked-in `pytra/**` are compatibility-debt inventory, not the final form.

Each language backend must generate SoT-derived code into the canonical generated lane and place only the minimum handwritten companions in the native lane.

### 0.72 Runtime `@extern` ownership metadata

- `extern_contract_v1` / `extern_v1` are declaration-only metadata and must not represent the location of the native owner implementation.
- Ambient-global variable declarations through `extern()` / `extern("symbol")` are a separate category from runtime-SoT `@extern` and must not be mixed into native owner resolution in the runtime symbol index.
