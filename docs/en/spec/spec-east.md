<a href="../../ja/spec/spec-east.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# EAST Specification (Implementation-Aligned)

This document is the unified source of truth for the EAST specification as aligned with the current implementation in `src/toolchain/compiler/east.py` and `src/toolchain/compiler/east_parts/`.

Integration policy:

- Merge the implementation-aligned EAST2 spec and the stage-responsibility spec for `EAST1/EAST2/EAST3` into this document.
- Retire old documents (`spec-east123.md`, `spec-east123-migration.md`, `spec-east1-build.md`) into `docs/en/spec/archive/`.
- For details of the link stage (`type_id` resolution, manifest, restart from intermediate files), see [spec-linker.md](./spec-linker.md).

## 1. Objective

- EAST (Extended AST) is an intermediate representation that converts Python AST into language-agnostic JSON with semantic annotations.
- Type resolution, cast information, readonly/mutable argument classification, and `main`-guard separation are fixed in the earlier stages.
- Python already has the `ast` module as a syntax-tree representation, but it is not enough to preserve source-level information such as comments for practical transpilation. EAST was introduced as that representation, and its parser is implemented in Python.

## 2. Input / Output

### 2.1 Input

- One UTF-8 Python source file.

### 2.2 Output Format

- Success

```json
{
  "ok": true,
  "east": { "...": "..." }
}
```

- Failure

```json
{
  "ok": false,
  "error": {
    "kind": "inference_failure | unsupported_syntax | semantic_conflict",
    "message": "...",
    "source_span": {
      "lineno": 1,
      "col": 0,
      "end_lineno": 1,
      "end_col": 5
    },
    "hint": "..."
  }
}
```

### 2.3 CLI

- `python src/toolchain/compiler/east.py <input.py> [-o output.json] [--pretty] [--human-output output.cpp]`
- `--pretty`: emit formatted JSON.
- `--human-output`: emit a C++-style human-readable view.
- `python3 src/py2x.py <input.py|east.json> --target cpp [-o output.cpp]`: EAST-based C++ generator.

## 3. Top-Level EAST Structure

The `east` object contains:

- `kind`: always `Module`
- `east_stage`: always `2` (`EAST2`)
- `schema_version`: integer (`1` currently)
- `source_path`: input path
- `source_span`: module span
- `body`: ordinary top-level statements
- `main_guard_body`: body of `if __name__ == "__main__":`
- `renamed_symbols`: rename map
- `meta.import_bindings`: canonical import data (`ImportBinding[]`)
- `meta.qualified_symbol_refs`: resolved references for `from-import` (`QualifiedSymbolRef[]`)
- `meta.import_modules`: binding info for `import module [as alias]` (`alias -> module`)
- `meta.import_symbols`: binding info for `from module import symbol [as alias]` (`alias -> {module,name}`)
- `meta.dispatch_mode`: `native | type_id` (decided when compilation starts and semantically applied in `EAST2 -> EAST3`)

Notes:

- The semantic application point of `meta.dispatch_mode` is exactly one place: `EAST2 -> EAST3`. Backends and hooks must not decide it again.
- The detailed contract is defined canonically by this document and `docs/en/spec/spec-linker.md`.
- After linked-program, `EAST3` still keeps `kind=Module` and `east_stage=3`, and may additionally carry `meta.linked_program_v1`. This is not a new EAST stage; it is materialized as `EAST3 -> linker -> linked EAST3`.

`ImportBinding` contains:

- `module_id`
- `export_name` (empty string for `import M`)
- `local_name`
- `binding_kind` (`module` / `symbol`)
- `runtime_module_id` (optional, the runtime module that owns the imported symbol)
- `runtime_symbol` (optional, the runtime symbol name for the imported symbol)
- `source_file`
- `source_line`

`QualifiedSymbolRef` contains:

- `module_id`
- `symbol`
- `local_name`
- `runtime_module_id` (optional)
- `runtime_symbol` (optional)

## 4. Syntax Normalization

- Extract `if __name__ == "__main__":` into `main_guard_body`.
- Rename the following:
  - duplicate definition names
  - reserved names `main`, `py_main`, `__pytra_main`
- `FunctionDef` and `ClassDef` contain both `name` (after renaming) and `original_name`.
- Normalize `for ... in range(...)` into `ForRange`, preserving `start`, `stop`, `step`, and `range_mode`.
- Lower `range(...)` into a dedicated representation during EAST construction and never pass raw `Call(Name("range"), ...)` into later stages such as `py2x.py --target cpp`.
  - In other words, downstream emitters do not interpret Python built-in `range` themselves; they only process already-normalized EAST nodes.
- Lower `range(...)` in expression position outside `for` into `RangeExpr`, including inside `ListComp`.
- Accept `from __future__ import annotations` as a frontend-only directive and do not emit it into EAST nodes or `meta.import_*`.
- Reject other `__future__` features and `from __future__ import *` as `unsupported_syntax` with fail-closed behavior.

## 5. Common Node Attributes

Expression nodes (`_expr`) contain:

- `kind`, `source_span`, `resolved_type`, `type_expr`, `borrow_kind`, `casts`, `repr`
- `type_expr` is the structured type representation and takes precedence over `resolved_type` when present.
- `resolved_type` is the migration-compat inferred-type string mirror.
- `borrow_kind` is `value | readonly_ref | mutable_ref` (`move` is currently unused).
- Major expressions keep structured child nodes such as `left/right`, `args`, `elements`, and `entries`.

Function nodes contain:

- `arg_types`, `arg_type_exprs`, `return_type`, `return_type_expr`, `arg_usage`, `renamed_symbols`
- `arg_type_exprs` / `return_type_expr` are the structured source of truth behind `arg_types` / `return_type`.
- `decorators` (list of raw decorator strings)
- `meta.runtime_abi_v1` (optional, canonical metadata for `@abi`)
- `meta.template_v1` (optional, canonical metadata for `@template`)

Class nodes may additionally carry:

- `bases`, `decorators`
- `meta.nominal_adt_v1` (optional, canonical metadata for nominal ADT families / variants)

Rules for `FunctionDef.meta.runtime_abi_v1`:

- `schema_version: 1`
- `args: {param_name: mode}`
- `ret: mode`
- Canonical modes are `default`, `value`, and `value_mut`
- Allowed canonical modes for `ret` are only `default` and `value`
- Even if legacy `value_readonly` is accepted at the source surface, metadata must normalize it to `value`
- Raw `decorators` are kept only to preserve Python surface syntax. The canonical input for backends and the linker is `meta.runtime_abi_v1`.
- This function-level metadata must survive linked-program and must not be replaced by `meta.linked_program_v1`

Rules for `FunctionDef.meta.template_v1`:

- `schema_version: 1`
- `params: [template_param_name, ...]`
- `scope: "runtime_helper"`
- `instantiation_mode: "linked_implicit"`
- `params` must preserve declaration order and must not be empty
- Raw `decorators` preserve source syntax only. The canonical input for parser, linker, and backend is `meta.template_v1`
- This function-level metadata must survive linked-program and must not be replaced by `meta.linked_program_v1`
- In v1, `@instantiate(...)` is not materialized, so instantiation data is not carried here
- `TypeVar` annotations alone do not create `meta.template_v1`

Rules for `ClassDef.meta.nominal_adt_v1`:

- `schema_version: 1`
- `role: "family" | "variant"`
- `family_name: str`
- `surface_phase: "declaration_v1"`
- For families:
  - `closed: 1`
  - `variant_name` / `payload_style` must not be present
- For variants:
  - `variant_name: str`
  - `payload_style: "unit" | "dataclass"`
  - metadata must not encode non-family base classes
- Raw `decorators` / `bases` preserve Python surface syntax only; the canonical nominal ADT contract is `meta.nominal_adt_v1`
- In v1, only top-level families and top-level variants are canonical; nested variants and namespace sugar must not be lowered into this metadata
- Constructors stay as ordinary `Call` nodes over the variant class; EAST2 does not introduce a dedicated constructor node for nominal ADTs

### 5.1 C++ Pass-Through Notation via `leading_trivia`

- EAST keeps pass-through directives inside existing `leading_trivia` (`kind: "comment"`) and does not introduce a new node kind.
- Interpreted comment forms:
  - `# Pytra::cpp <C++ line>`
  - `# Pytra::cpp: <C++ line>`
  - `# Pytra::pass <C++ line>`
  - `# Pytra::pass: <C++ line>`
  - `# Pytra::cpp begin` ... `# Pytra::cpp end`
  - `# Pytra::pass begin` ... `# Pytra::pass end`
- Output rules for the C++ emitter:
  - directive comments are emitted as raw C++ lines, not converted into ordinary comments like `// ...`
  - inside `begin/end` blocks, ordinary comments are emitted in order as C++ lines after stripping the leading `#`
  - emit them immediately before the statement that owns the `leading_trivia`, aligned to the statement indentation
  - `blank` trivia still means blank lines
  - if multiple directives exist in the same `leading_trivia`, emit them in source order
- Priority:
  - directive interpretation in `leading_trivia` has the highest priority
  - it is independent from docstring-to-comment rendering (`"""..."""` -> `/* ... */`) and neither overrides the other

### 5.2 nominal ADT / pattern / `match` contract (v1)

- Stage-A declaration surface uses `ClassDef.meta.nominal_adt_v1` as the source of truth, and represents both families and variants with ordinary `ClassDef` nodes.
- When Stage B introduces `match/case`, it uses the following statement and helper nodes.
  - `Match`
    - `subject: _expr`
    - `cases: MatchCase[]`
    - `source_span`
    - `repr` (optional)
  - `MatchCase`
    - `pattern: VariantPattern | PatternBind | PatternWildcard`
    - `guard: null` (v1 does not allow guard patterns)
    - `body: stmt[]`
    - `source_span`
  - `VariantPattern`
    - `family_name: str`
    - `variant_name: str`
    - `subpatterns: (PatternBind | PatternWildcard)[]`
    - `source_span`
  - `PatternBind`
    - `name: str`
    - `source_span`
  - `PatternWildcard`
    - `source_span`
- The v1 pattern surface is limited to variant patterns plus payload binds plus wildcard `_`.
- Literal patterns, nested patterns, guard patterns, and expression-form `match` are outside the v1 node contract.
- Backends that receive `Match` / pattern nodes are expected to implement a dedicated lowering lane and must not degrade them into `object` fallback or raw method-name reinterpretation.
- `Match` may carry `meta.match_analysis_v1` for static checking.
  - `schema_version: 1`
  - `family_name: str`
  - `coverage_kind: "exhaustive" | "wildcard_terminal" | "partial" | "invalid"`
  - `covered_variants: str[]`
  - `uncovered_variants: str[]`
  - `duplicate_case_indexes: int[]`
  - `unreachable_case_indexes: int[]`
  - `match_analysis_v1` is auxiliary metadata that records the coverage summary fixed by validators / lowering; it is not a replacement for parser-surface nodes.
- v1 static checking applies only to closed nominal ADT families.
  - Exhaustiveness means either "enumerate every family variant exactly once" or "end with `PatternWildcard` that captures the remaining variants."
  - Duplicate patterns mean either re-listing the same `variant_name` or adding a second and later `PatternWildcard`.
  - Unreachable branches mean any `MatchCase` that appears after wildcard coverage is closed, or a later `VariantPattern` for a variant that was already covered.

## 6. Type System

### 6.1 Canonical Types

- Integer types: `int8`, `uint8`, `int16`, `uint16`, `int32`, `uint32`, `int64`, `uint64`
- Floating-point types: `float32`, `float64`
- Basic types: `bool`, `str`, `None`
- Composite types: `list[T]`, `set[T]`, `dict[K,V]`, `tuple[T1,...]`
- Extended types: `Path`, `Exception`, class names
- Auxiliary types: `unknown`, `module`, `callable[float64]`

### 6.2 Annotation Normalization

- Normalize `int` to `int64`.
- Normalize `float` to `float64`.
- Normalize `byte` to `uint8` as an annotation alias for one-character / one-byte use.
- Preserve `float32` and `float64` as-is.
- Treat `any` and `object` as synonyms of `Any`.
- For concrete C++ runtime representation of `Any`, `object`, `None`, and boxing/unboxing, see the `Any` / `object` representation policy in [spec-runtime.md](./spec-runtime.md).
- Normalize `bytes` and `bytearray` to `list[uint8]`.
- Normalize `pathlib.Path` to `Path`.
- In the C++ runtime, `str`, `list`, `dict`, `set`, `bytes`, and `bytearray` are implemented as wrappers via composition, not STL inheritance.

### 6.3 `TypeExpr` Schema (Structured Type Representation)

`type_expr` is a backend-neutral structured type representation and must support at least the following kinds.

- `NamedType`
  - `name: str`
  - examples: `int64`, `float64`, `str`, `Path`
- `GenericType`
  - `base: str`
  - `args: TypeExpr[]`
  - examples: `list[T]`, `dict[K,V]`, `tuple[T1,T2]`, `callable[float64]`
- `OptionalType`
  - `inner: TypeExpr`
  - canonical form for `T | None`; do not encode this as `UnionType`
- `UnionType`
  - `options: TypeExpr[]`
  - `union_mode: general | dynamic`
  - `general` represents open general unions; `dynamic` represents unions that contain `Any/object/unknown`
- `DynamicType`
  - `name: Any | object | unknown`
  - represents open-world dynamic carriers
- `NominalAdtType`
  - `name: str`
  - `adt_family: str` (optional, example: `json`)
  - `variant_domain: str` (optional, example: `closed`)
  - represents closed nominal ADTs such as `JsonValue`

Notes:

- `bytes` / `bytearray` may continue to normalize to `list[uint8]`; they do not require an independent kind.
- The exact serialized field style may use either `snake_case` or `camelCase`, but the semantics above are required.
- Nodes that directly carry annotations may add `*_type_expr` fields paired with existing string fields.

### 6.4 Three-Way Union Classification and `resolved_type` Mirror Authority

Mandatory rules:

- Always normalize `T | None` to `OptionalType(inner=T)` and never leave it as `UnionType(options=[T, None])`.
- Treat unions that contain `Any/object/unknown` as `UnionType(union_mode=dynamic)` and never lower them with the same rules as general unions.
- Treat JSON decode-first surfaces such as `JsonValue` / `JsonObj` / `JsonArr` as `NominalAdtType`, not as general unions.
- Demote `resolved_type`, `arg_types`, and `return_type` to mirrors derived from `type_expr`, `arg_type_exprs`, and `return_type_expr`.
- When both `type_expr` and `resolved_type` are present, `type_expr` is always authoritative. Conflicts must fail closed as `semantic_conflict`.
- During migration, legacy nodes may temporarily carry only `resolved_type`, but whenever canonical EAST2/EAST3, validators, or backend contracts are extended, `type_expr` must be the preferred input.

Examples:

- `int | None` -> `OptionalType(NamedType("int64"))`
- `int | bool` -> `UnionType(union_mode="general", options=[NamedType("int64"), NamedType("bool")])`
- `int | Any` -> `UnionType(union_mode="dynamic", options=[NamedType("int64"), DynamicType("Any")])`
- `JsonValue` -> `NominalAdtType(name="JsonValue", adt_family="json", variant_domain="closed")`

### 6.5 `JsonValue` Nominal Closed-ADT Lane

Treat `JsonValue` / `JsonObj` / `JsonArr` as a JSON-specific nominal closed-ADT lane, not as a general union and not as an `object` fallback.

Mandatory rules:

- The type of `json.loads(...)` is `NominalAdtType(name="JsonValue", adt_family="json", variant_domain="closed")`.
- `json.loads_obj(...)` / `json.loads_arr(...)` return `OptionalType(NominalAdtType("JsonObj"))` / `OptionalType(NominalAdtType("JsonArr"))`, respectively.
- `JsonValue.as_*`, `JsonObj.get_*`, and `JsonArr.get_*` are decode / narrowing operations for nominal ADTs, not general-purpose casts.
- Do not expand the `JsonValue` lane into `UnionType(union_mode=general|dynamic)`.

Canonical resolved semantic tags fixed in `EAST2 -> EAST3`:

- `json.loads`
- `json.loads_obj`
- `json.loads_arr`
- `json.value.as_obj`
- `json.value.as_arr`
- `json.value.as_str`
- `json.value.as_int`
- `json.value.as_float`
- `json.value.as_bool`
- `json.obj.get`
- `json.obj.get_obj`
- `json.obj.get_arr`
- `json.obj.get_str`
- `json.obj.get_int`
- `json.obj.get_float`
- `json.obj.get_bool`
- `json.arr.get`
- `json.arr.get_obj`
- `json.arr.get_arr`
- `json.arr.get_str`
- `json.arr.get_int`
- `json.arr.get_float`
- `json.arr.get_bool`

Responsibility boundary:

- Frontend / lowering own the job of normalizing raw `json.loads` / `as_*` / `get_*` surface calls into the semantic tags above or an equivalent dedicated IR category.
- Backends / hooks must not reinterpret JSON decode semantics from raw callee names, attribute names, or receiver type strings.
- Validators must check consistency between `type_expr` and semantic tags on the `JsonValue` nominal lane, and stop any path that tries to emit `JsonValue` as a general union with `semantic_conflict` or `unsupported_syntax`.
- If a target does not yet provide a `JsonValue` nominal carrier or decode-op mapping, it must fail closed instead of silently degrading to `object`, `String`, or `PyAny`.

## 7. Type Inference Rules

- `Name`: resolve from the type environment. If unresolved, fail with `inference_failure`.
- `Constant`:
  - integer literals -> `int64`
  - floating-point literals -> `float64`
  - booleans -> `bool`
  - strings -> `str`
  - `None` -> `None`
- `List/Set/Dict`:
  - non-empty containers infer by unifying element types
  - empty containers usually cause `inference_failure`
  - however, an empty container in `AnnAssign` adopts the annotation type
- `Tuple`: constructs `tuple[...]`
- `BinOp`:
  - infer numeric operators `+ - * % // /`
  - mixed numeric types perform promotion when `float32/float64` is involved and attach `casts`
  - `Path / str` becomes `Path`
  - support `str * int` and `list[T] * int`
  - bit operators `& | ^ << >>` infer as integer types
  - note: the Python/C++ difference of `%` is not absorbed in EAST
  - EAST keeps `%` as an operator and the generator switches output according to `--mod-mode` (`native` / `python`)
- `Subscript`:
  - `list[T][i] -> T`
  - `dict[K,V][k] -> V`
  - `str[i] -> str`
  - slicing `list/str` preserves the same type
  - EAST itself preserves `Subscript` / `Slice`, and semantics such as `str-index-mode` and `str-slice-mode` are applied by the generator
  - the current C++ generator implements `byte` and `native`; `codepoint` is not implemented
- `Call`:
  - known calls include `int`, `float`, `bool`, `str`, `bytes`, `bytearray`, `len`, `range`, `min`, `max`, `round`, `print`, `write_rgb_png`, `save_gif`, `grayscale_palette`, `perf_counter`, `Path`, `Exception`, `RuntimeError`
  - `float(...)`, `round(...)`, `perf_counter()`, and the main `math.*` functions infer to `float64`
  - `bytes(...)` / `bytearray(...)` infer to `list[uint8]`
  - class constructors and methods infer through pre-collected type information
- `ListComp`: only a single generator is supported
- `BoolOp` (`or` / `and`) is kept as `kind: BoolOp` in EAST.
  - During C++ generation, when the expected type is `bool`, emit boolean operators (`&&` / `||`).
  - When the expected type is not `bool`, emit Python-style value-selection semantics:
    - `a or b` -> `truthy(a) ? a : b`
    - `a and b` -> `truthy(a) ? b : a`
  - The value-selection decision and rendering are made in `src/py2x.py`; EAST itself does not lower this into another node kind.

About `range`:

- Even if input AST contains `Call(Name("range"), ...)`, the final EAST must convert it into dedicated nodes such as `ForRange` and `RangeExpr`, and must not leave it as a direct `Call`.
- Any case where `range` remains as-is is treated as an EAST-construction defect and must not be rescued implicitly downstream.

About `lowered_kind: BuiltinCall`:

- EAST attaches `runtime_call` so that downstream implementations can reduce branching.
- Major implemented `runtime_call` examples:
  - `py_print`, `py_len`, `py_to_string`, `static_cast`
  - `py_min`, `py_max`, `perf_counter`
  - `list.append`, `list.extend`, `list.pop`, `list.clear`, `list.reverse`, `list.sort`
  - `set.add`, `set.discard`, `set.remove`, `set.clear`
  - `write_rgb_png`, `save_gif`, `grayscale_palette`
  - `py_isdigit`, `py_isalpha`

Mandatory responsibility boundary for `runtime_module_id` / `runtime_symbol` / `runtime_call`:

- `runtime_module_id`, `runtime_symbol`, `runtime_call`, `resolved_runtime_call`, `resolved_runtime_source`, and `semantic_tag` are treated as canonical information of EAST3.
- Backends and emitters are limited to rendering this resolved information and must not resolve function names or module names again.
- If some necessary information is not represented in EAST3, extend the EAST3 schema first and place the data on the schema side.
- `runtime_module_id` and `runtime_symbol` are target-independent and must not carry target-specific paths such as `runtime/cpp/std/time.gen.h`.
- Target-specific include paths, compile sources, and companions are derived by the backend from `tools/runtime_symbol_index.json`.

Forbidden:

- putting direct symbol-name branches such as `if runtime_call == "perf_counter"` into emitters or frontend signature registries
- embedding runtime-dispatch tables for `py_assert_*`, `json.loads`, `write_rgb_png`, and similar symbols into emitters or frontend registries
- moving call-resolution rules into the backend because "EAST3 does not have enough information"
- embedding target-specific file paths into EAST3

Fixed contract for resolved calls from EAST3 to backend:

- Target nodes:
  - `Call`
  - `Attribute` including property access such as `Path.parent/name/stem`
- Resolved attributes that the backend may read:
  - `runtime_module_id`
  - `runtime_symbol`
  - `semantic_tag`
  - `runtime_call`
  - `resolved_runtime_call`
  - `resolved_runtime_source`
  - `resolved_type`
- Resolution priority:
  1. `runtime_module_id + runtime_symbol`
  2. `runtime_call` (migration compatibility)
  3. `resolved_runtime_call` (when `runtime_call` is empty)
  4. if all of the above are empty and `semantic_tag` is `stdlib.*`, fail closed without implicit fallback
- `resolved_runtime_source` contract:
  - `import_symbol`: resolved through `from ... import ...`
  - `module_attr`: resolved through `module.symbol`
  - returning the string form of `runtime_call` / `resolved_runtime_call` remains allowed only for backward compatibility, but new implementations should prefer `import_symbol` and `module_attr`
- Backend API constraints:
  - emitters must not interpret stdlib/runtime semantics from raw `callee`, `owner`, or `attr` names on `Call` / `Attribute`
  - runtime-call rendering APIs in emitters must accept resolved attributes as input and must not contain re-resolution logic over raw AST nodes
  - type-based selection using `resolved_type` is allowed, but reverse lookup from module names and function names is forbidden

Operational enforcement in CI:

- `python3 tools/check_emitter_runtimecall_guardrails.py`
  - fails on newly added direct runtime/stdlib branches in non-C++ emitters
- `python3 tools/check_emitter_forbidden_runtime_symbols.py`
  - fails on reintroduced runtime implementation symbols in emitters such as `__pytra_write_rgb_png`
- `python3 tools/check_noncpp_east3_contract.py`
  - statically detects responsibility-boundary violations in language-specific smokes and EAST3 contracts

About `.get(...).items()` on `dict[str, Any]`:

- During C++ generation, assume `dict[str, object]` and initialize `Dict` / `List` literal values by recursively converting them through `make_object(...)`.
- When `.get(..., {})` supplies a dictionary default, normalize it to `dict[str, object]`.

## 8. Cast Specification

Emit `casts` on numeric promotion:

```json
{
  "on": "left | right | body | orelse",
  "from": "int64",
  "to": "float32 | float64",
  "reason": "numeric_promotion | ifexp_numeric_promotion"
}
```

## 9. Argument Reassignment Classification (`arg_usage`)

Attach `arg_usage` to each `FunctionDef`.

- Allowed values: `readonly | reassigned`
- `reassigned` is set when:
  - the argument name appears on the left-hand side of assignment or augmented assignment (`Assign`, `AnnAssign`, `AugAssign`)
  - the argument name appears on either side of a `Swap`
  - the argument name is used as the target of `for` or `for range`
  - `except ... as name` uses the same name as the argument
- Assignments inside nested `FunctionDef` or `ClassDef` do not count toward the outer function.
- Everything else is `readonly`.

At the moment, this information is used mainly for backend-side `mut` decisions on arguments.

## 10. Supported Statements

- `FunctionDef`, `ClassDef`, `Return`
- `Assign`, `AnnAssign`, `AugAssign`
- `Expr`, `If`, `For`, `ForRange`, `While`, `Try`, `Raise`
- `Import`, `ImportFrom`, `Pass`, `Break`, `Continue`

Notes:

- `Assign` supports only a single target statement.
- Tuple assignment is supported, for example `x, y = ...` and `a[i], a[j] = ...`.
- For name targets, update the type environment when the RHS tuple type is known.
- `from module import *` (wildcard import) is unsupported.

## 11. Pre-Collection of Class Information

Collect the following before generation:

- class names
- simple inheritance relationships
- method return types
- field types (from class-body `AnnAssign` and `__init__` assignment analysis)

## 12. Error Contract

`EastBuildError` contains `kind`, `message`, `source_span`, and `hint`.

- `inference_failure`
- `unsupported_syntax`
- `semantic_conflict`

`SyntaxError` is converted into the same format.

## 13. Human-Readable View

- `--human-output` emits C++-style pseudo source.
- Its purpose is reviewability; strict compilability as C++ is not guaranteed.
- It visualizes EAST data such as `source_span`, `resolved_type`, `ForRange`, and `renamed_symbols`.

## 14. Known Constraints

- The full Python syntax is not supported; only the Pytra subset is.
- Advanced data-flow analysis such as precise alias analysis or side-effect propagation is not implemented.
- `borrow_kind=move` is currently unused.

## 15. Validation Status

- `test/fixtures` 32/32 can be converted by `src/toolchain/compiler/east.py` (`ok: true`)
- `sample/py` 16/16 can be converted by `src/toolchain/compiler/east.py` (`ok: true`)
- `sample/py` 16/16 can be "convert -> compile -> run" through `src/py2x.py` (`ok`)

<a id="east-stages"></a>
## 16. Current Stage Structure (2026-02-24)

- EAST is handled in three stages: `EAST1 -> EAST2 -> EAST3`.
- In the current implementation, the default route of `py2*.py` is `EAST3`.
- `py2x.py --target cpp` accepts only `--east-stage 3` and errors out on `--east-stage 2`.
- The eight non-C++ converters (`py2rs.py`, `py2cs.py`, `py2js.py`, `py2ts.py`, `py2go.py`, `py2java.py`, `py2kotlin.py`, `py2swift.py`) keep `--east-stage 2` as a migration-compatibility mode with a warning.
- `meta.dispatch_mode` is preserved across all stages, and its semantics are applied only once in `EAST2 -> EAST3`.

### 16.1 Responsibilities per Stage

- `EAST1` (Parsed):
  - IR immediately after parsing
  - keeps source spans and trivia, and must not contain backend-specific nodes
- `EAST2` (Normalized):
  - syntax-normalized IR
  - stabilizes `ForRange` / `RangeExpr`, import normalization, and type-resolution results
- `EAST3` (Core):
  - backend-independent semantics-fixed IR
  - materializes boxing/unboxing, `Obj*` instructions, `type_id` checks, and iteration plans as explicit instructions
  - program-wide decisions such as call graph, SCC, global non-escape, container ownership, and final `type_id` table are delegated to the linker stage

### 16.1.1 Stage Boundary Table (Inputs / Outputs / Forbidden Work / Responsible Files)

| Stage / Boundary | Input | Output | Forbidden Work | Responsible Files |
| --- | --- | --- | --- | --- |
| `EAST1` | `Source` (`.py` / parser backend selection) | `Module` document with `east_stage=1` | `EAST2/EAST3` conversion, dispatch semantics application, target-dependent node generation | `src/toolchain/ir/core.py`, `src/toolchain/ir/east1.py` |
| `EAST2` | `EAST1` document | normalized `Module` document with `east_stage=2` | dispatch semantics application, boxing/type_id instruction materialization, backend syntax decisions | `src/toolchain/ir/east2.py` |
| `EAST3` | `EAST2` document + `meta.dispatch_mode` | core-instruction `Module` document with `east_stage=3` | mapping into target-language syntax, semantic reinterpretation in hooks | `src/toolchain/ir/east2_to_east3_lowering.py`, `src/toolchain/ir/east3.py` |
| `Link` | raw `EAST3` set + `link-input.v1` | linked modules (still `east_stage=3`) + `link-output.v1` | target-language rendering, runtime placement, build-manifest generation | `src/toolchain/link/*` |

Notes:

- `Link` is not a new `east_stage`. Both input and output module bodies remain `east_stage=3`.
- Canonical data added by `Link` lives in `link-output.v1` and linked modules' `meta.linked_program_v1`.

### 16.2 Invariants

1. `east_stage` and node shape must agree.
2. `dispatch_mode` semantics are applied exactly once in `EAST2 -> EAST3`.
3. Backends and hooks must not reinterpret `EAST3` semantics.
4. Whole-program summaries are not finalized in raw `EAST3` alone; the linker materializes them into `link-output.v1` and linked modules.

<a id="east-pipeline"></a>
## 17. Integrated Pipeline Specification

1. `Source -> EAST1`
2. `EAST1 -> EAST2` (Normalize pass)
3. `EAST2 -> EAST3` (Core Lowering pass)
4. `EAST3 (raw modules) -> LinkedProgramLoader / LinkedProgramOptimizer`
5. `linked module (EAST3) -> TargetEmitter` (language mapping)

Notes:

- `--object-dispatch-mode {type_id,native}` is decided when compilation starts, then reflected into `iter_plan` and `Obj*` instructions during `EAST2 -> EAST3`.
- Backends and hooks must not re-decide the mode and swap instructions.
- The linker is responsible only for checking `dispatch_mode` consistency and finalizing whole-program summaries. It must not generate target-language syntax in place of the backend.

### 17.1 linked module `meta` Contract

After linked-program, a module still keeps `kind=Module` and `east_stage=3`, while carrying `meta.linked_program_v1`.

Required keys of `meta.linked_program_v1`:

- `program_id`
- `module_id`
- `entry_modules`
- `type_id_resolved_v1`
- `non_escape_summary`
- `container_ownership_hints_v1`

Responsibility boundary:

- Raw `EAST3` must not contain `meta.linked_program_v1`.
- Linked modules must contain `meta.linked_program_v1`.
- Backends are allowed to read `meta.linked_program_v1` and `link-output.v1`, but must not recompute equivalent data.
- The linker may finalize linked summaries on functions and calls, for example `FunctionDef.meta.escape_summary` and `Call.meta.non_escape_callsite`.
- Parser/EAST-build metadata such as `FunctionDef.meta.runtime_abi_v1` must remain present in linked modules and must not be overwritten by the linker.
- `FunctionDef.meta.template_v1` is also parser/EAST-build metadata and must remain present in linked modules without linker overwrite.

<a id="east-file-mapping"></a>
## 18. Current / Post-Migration Responsibility Map (2026-02-24)

| Stage | Responsibility | Current Implementation (at migration start) | Canonical destination after migration |
| --- | --- | --- | --- |
| EAST1 | generate IR immediately after parsing | `src/toolchain/compiler/east_parts/core.py` (compat shim) | `src/toolchain/ir/core.py` |
| EAST1 | EAST1 entry API | `src/toolchain/compiler/east_parts/east1.py` (through compat wrapper) | `src/toolchain/ir/east1.py` |
| EAST2 | `EAST1 -> EAST2` normalization API | `src/toolchain/compiler/east_parts/east2.py` (compat wrapper + selfhost fallback) | `src/toolchain/ir/east2.py` |
| EAST3 | body of `EAST2 -> EAST3` lowering | `src/toolchain/compiler/east_parts/east2_to_east3_lowering.py` (compat shim) | `src/toolchain/ir/east2_to_east3_lowering.py` |
| EAST3 | EAST3 entry API | `src/toolchain/compiler/east_parts/east3.py` (through compat wrapper) | `src/toolchain/ir/east3.py` |
| Bridge | backend entry (C++) | `src/py2x.py` (`--east-stage 3` only) | `src/py2x.py` (`EAST3` only) |
| CLI compat | publishing old API | `src/toolchain/compiler/transpile_cli.py` (compat shim) | `src/toolchain/frontends/transpile_cli.py` (real implementation) |

<a id="east1-build-boundary"></a>
## 19. Responsibility Boundary of the `EAST1` Build Entry

Objective:

- Separate the entry responsibility of `.py/.json -> EAST1` build and reduce the responsibility of `transpile_cli.py`.

Structure:

- `core.py`: self-hosted parser implementation (low layer; current canonical file is `src/toolchain/ir/core.py`)
- `east1_build.py`: build entry (target file to add)
- `east1.py`: thin helpers for stage contracts
- `py2x.py --target cpp`: `_analyze_import_graph` and `build_module_east_map` must only delegate into `East1BuildHelpers`
- `transpile_cli.py`: real implementation lives in `src/toolchain/frontends/transpile_cli.py`; `src/toolchain/compiler/transpile_cli.py` remains only as a thin compatibility wrapper

Acceptance conditions:

1. `EAST1` build is restricted to attaching `east_stage=1` and must not perform `EAST1 -> EAST2`.
2. Keep the error contract of `load_east_document_compat` (`input_invalid` family).
3. `compiler/transpile_cli.py` must not own the build body and should mostly delegate into `frontends/transpile_cli.py`.
4. Include `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` in the regression path, and when diffs appear, track them by cutting new TODO items.
5. Fix the `EAST1` entry contract and the `py2cpp` delegation route through `test/unit/ir/test_east1_build.py` and `test/unit/backends/cpp/test_py2cpp_east1_build_bridge.py`.
6. The body of import-graph analysis uses `src/toolchain/frontends/east1_build.py` (`_analyze_import_graph_impl`) as the source of truth; `analyze_import_graph` and `build_module_east_map` in `compiler/transpile_cli.py` remain only as thin public compatibility wrappers.

<a id="east-migration-phases"></a>
## 20. Migration Phases (Making EAST3 the Main Route)

1. Phase 0: fix contract tests (`EAST3` required fields, `ForCore` / `iter_plan` requirements, dispatch application point)
2. Phase 1: separate APIs (move responsibilities into `east1.py`, `east2.py`, `east3.py`)
3. Phase 2: make `EAST3` the main route (inventory re-decision logic inside `py2x.py --target cpp`)
4. Phase 3: separate hooks (remove temporary stage mixing)
5. Phase 4: reduce the `EAST2` route into compatibility mode, then retire it in stages

Notes:

- Track progress for each phase in `docs/ja/todo/index.md` and `docs/ja/plans/plan-east123-migration.md`.
- Current Phase 4 operation: every `py2*.py` defaults to `--east-stage 3`. `py2x.py --target cpp` rejects `--east-stage 2`, while the eight non-C++ converters keep the compatibility route and print `warning: --east-stage 2 is compatibility mode; default is 3.`

## 21. Acceptance Criteria for EAST Adoption

- Existing `test/fixtures` must be convertible through EAST.
- On inference failure, return errors that include `kind`, `source_span`, and `hint`.
- Document semantic differences instead of rescuing them implicitly in downstream emitters.
- `--object-dispatch-mode` must be applied only in `EAST2 -> EAST3`.
- Hooks must not add new language-agnostic semantics.

## 22. Minimum Verification Commands

```bash
python3 tools/check_py2cpp_transpile.py
python3 tools/check_noncpp_east3_contract.py
python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented
```

## 23. Future Extensions (Direction)

- `borrow_kind` currently uses `value | readonly_ref | mutable_ref`, and `move` is unused.
- In the future, keep the representation extensible enough to connect to Rust-style borrow annotations such as `&` and `&mut`.
  - Final Rust-specific decisions such as ownership and detailed lifetime handling remain backend responsibilities.

## 24. EAST2 Shared IR Contract (Depythonization Draft)

Objective:

- Treat EAST2 as the first shared IR across multiple frontends, and keep direct dependencies on Python-specific names such as builtin names and `py_*` runtime names outside this boundary.

### 24.1 Node Kinds (Information Preserved in EAST2)

- Syntax nodes:
  - `Module`, `FunctionDef`, `ClassDef`, `If`, `While`, `For`, `ForRange`, `Assign`, `AnnAssign`, `AugAssign`, `Return`, `Expr`, `Import`, `ImportFrom`, `Raise`, `Try`, `Pass`, `Break`, `Continue`, `Match`
- Expression nodes:
  - `Name`, `Constant`, `Attribute`, `Call`, `Subscript`, `Slice`, `Tuple`, `List`, `Dict`, `Set`, `ListComp`, `GeneratorExp`, `IfExp`, `Lambda`, `BinOp`, `BoolOp`, `Compare`, `UnaryOp`, `RangeExpr`
- Auxiliary nodes:
  - before conversion into `ForCore`, keep normalization data for `For` / `ForRange`, such as `iter_mode`, `target_type`, and `range_mode`
  - `MatchCase`, `VariantPattern`, `PatternBind`, `PatternWildcard`

### 24.2 Neutral Contract for Operators, Types, and Metadata

- Operators:
  - `BinOp.op` keeps `Add/Sub/Mult/Div/FloorDiv/Mod/BitAnd/BitOr/BitXor/LShift/RShift` as string enums
  - `Compare.ops` keeps `Eq/NotEq/Lt/LtE/Gt/GtE/In/NotIn/Is/IsNot`
  - `BoolOp.op` keeps `And/Or`
- Types:
  - `type_expr` is the canonical type representation and must not carry backend-specific representations
  - `resolved_type` may remain only as a legacy mirror of logical type names such as `int64`, `float64`, `list[T]`, `dict[K,V]`, `tuple[...]`, `Any`, and `unknown`
  - `OptionalType`, `UnionType(union_mode=dynamic)`, and `NominalAdtType` must remain distinct categories
- Metadata:
  - `meta.dispatch_mode` is kept as the compilation-policy value `native | type_id`, and semantics are applied exactly once in `EAST2 -> EAST3`
  - import normalization data (`import_bindings`, `qualified_symbol_refs`, `import_modules`, `import_symbols`) is kept as frontend resolution results

### 24.3 Forbidden at the EAST2 Boundary

- Do not leak a contract where `builtin_name` is interpreted as Python built-ins such as `len`, `str`, or `range` on the backend side.
- Do not fix the meaning of `runtime_call` through `py_*` strings such as `py_len`, `py_to_string`, or `py_iter_or_raise`.
- Do not treat `py_tid_*` compatibility names as public EAST2 contract; keep them inside compatibility bridges only.

### 24.4 Diagnostic and Fail-Closed Contract

- Unresolvable nodes or types must stop with `ok=false` plus `error.kind` (`inference_failure`, `unsupported_syntax`, `semantic_conflict`).
- Inputs outside the neutral contract, such as invalid `dispatch_mode`, unsupported node shapes, or missing required metadata, must fail closed instead of being rescued implicitly.
- Fail closed with `semantic_conflict` when `type_expr` and its `resolved_type` mirror disagree.
- `meta.nominal_adt_v1`, `Match`, and pattern nodes that fall outside the v1 contract (nested variants, guard patterns, literal patterns, namespace-sugar dependence, and similar cases) must fail closed with `unsupported_syntax` or `semantic_conflict`.
- If `Match.meta.match_analysis_v1` reports `coverage_kind=partial` or `invalid`, the program must stop with `semantic_conflict` before backend emission.
- Compatibility fallbacks are allowed only during staged migration and must be logged together with an explicit `legacy` flag.

### 24.5 Principles for `EAST2 -> EAST3`

- EAST2 keeps only "what the program wants to do" as semantic tags; `EAST3` finalizes those into object-boundary instructions such as `Obj*` and `ForCore.iter_plan`.
- `EAST2 -> EAST3` lowering must inspect `type_expr` and split `optional`, `dynamic union`, and `nominal ADT` into separate lanes; it must not recover semantics by re-splitting `resolved_type` strings.
- `JsonValue` decode / narrowing must be normalized in `EAST2 -> EAST3` into resolved semantic tags (`json.loads`, `json.value.as_*`, `json.obj.get_*`, `json.arr.get_*`) or an equivalent dedicated IR category; backend-side raw method-name interpretation is forbidden.
- Frontend-specific resolution of Python built-ins and standard-library items must be converted into neutral tags by an adapter layer before entering EAST2.
- From `EAST3` onward, backends and hooks are responsible only for target-language mapping and must not reinterpret the EAST2 contract.
