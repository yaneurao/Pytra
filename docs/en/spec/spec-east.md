<a href="../../ja/spec/spec-east.md"><img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# EAST Specification (Implementation-Aligned)

This document is the unified source of truth for the EAST specification, aligned with the current implementation in `src/toolchain/misc/east.py` / `src/toolchain/misc/east_parts/`.

Integration policy:
- The current-implementation-aligned EAST2 spec and the stage-responsibility spec for the EAST1/EAST2/EAST3 three-tier structure are merged into this document.
- Legacy documents (`spec-east123.md`, `spec-east123-migration.md`, `spec-east1-build.md`) are retired to `docs/ja/spec/archive/`.
- Details of the linking stage (`type_id` resolution, manifests, intermediate-file resumption) are covered in [spec-linker.md](./spec-linker.md).

## 1. Objective

- EAST (Extended AST) is an intermediate representation that produces language-agnostic, semantics-annotated JSON from a Python AST.
- Type resolution, cast information, argument readonly/mutable classification, and main-guard separation are all finalized in the frontend stage.
- Python has a built-in `ast` module for working with abstract syntax trees, but using it directly makes it impossible to preserve source comments during transpilation. EAST was designed to overcome this limitation, and its parser is implemented in Python.

## 2. Inputs and Outputs

### 2.1 Input

- A single UTF-8 Python source file.

### 2.2 Output Format

- On success

```json
{
  "ok": true,
  "east": { "...": "..." }
}
```

- On failure

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

- `python src/toolchain/misc/east.py <input.py> [-o output.json] [--pretty] [--human-output output.cpp]`
- `--pretty`: emit formatted JSON.
- `--human-output`: emit a C++-style human-readable view.
- `python3 src/pytra-cli.py <input.py|east.json> --target cpp [-o output.cpp]`: EAST-based C++ generator.

## 3. Top-Level EAST Structure

The `east` object contains the following fields.

- `kind`: always `Module`
- `east_stage`: always `2` (`EAST2`)
- `schema_version`: integer (currently `1`)
- `source_path`: path of the input file
- `source_span`: module span
- `body`: ordinary top-level statements
- `main_guard_body`: body of `if __name__ == "__main__":`
- `renamed_symbols`: rename map
- `meta.import_bindings`: canonical import bindings (`ImportBinding[]`)
- `meta.qualified_symbol_refs`: resolved references for `from`-imports (`QualifiedSymbolRef[]`)
- `meta.import_modules`: binding information for `import module [as alias]` (`alias -> module`)
- `meta.import_symbols`: binding information for `from module import symbol [as alias]` (`alias -> {module,name}`)
- `meta.dispatch_mode`: `native | type_id` (determined at compile start and semantically applied during `EAST2 -> EAST3`)

Notes:
- The semantic application point of `meta.dispatch_mode` is solely `EAST2 -> EAST3`; it is not re-evaluated by backends or hooks.
- The authoritative contracts are this document and `docs/ja/spec/spec-linker.md`.
- A post-linking `EAST3` continues to carry `kind=Module` / `east_stage=3` and may additionally hold `meta.linked_program_v1`. This is not a new EAST stage; it is treated as a materialization of `EAST3 -> linker -> linked EAST3`.
- When the linked-program optimizer generates a helper as a synthetic module, it likewise maintains `kind=Module` / `east_stage=3` and stores additional information as `meta.synthetic_helper_v1`. No separate EAST stage is introduced for helpers.

`ImportBinding` contains the following fields.

- `module_id`
- `export_name` (empty string for `import M`)
- `local_name`
- `binding_kind` (`module` / `symbol`)
- `runtime_module_id` (optional — runtime module to which the imported symbol belongs)
- `runtime_symbol` (optional — runtime symbol of the import target)
- `source_file`
- `source_line`

`QualifiedSymbolRef` contains the following fields.

- `module_id`
- `symbol`
- `local_name`
- `runtime_module_id` (optional)
- `runtime_symbol` (optional)

## 4. Syntax Normalization

- `if __name__ == "__main__":` is separated into `main_guard_body`.
- The following are subject to renaming:
  - Duplicate definition names
  - Reserved names `main`, `py_main`, `__pytra_main`
- `FunctionDef` / `ClassDef` carry both `name` (post-rename) and `original_name`.
- `for ... in range(...)` is normalized to `ForRange`, which retains `start/stop/step/range_mode`.
- `range(...)` is lowered to a dedicated representation during EAST construction; raw `Call(Name("range"), ...)` is never passed to downstream stages (e.g., `pytra-cli.py --target cpp`).
  - Downstream emitters therefore have no knowledge of the Python built-in `range` semantics and process only the normalized nodes from EAST.
- `range(...)` appearing in expression position outside `for` (including inside `ListComp`) is lowered to `RangeExpr`.
- `from __future__ import annotations` is accepted as a frontend-only directive and is not emitted into EAST nodes or `meta.import_*`.
- Other `__future__` features and `from __future__ import *` are rejected fail-closed as `unsupported_syntax`.

### 4.1 Python → EAST Node Conversion Table

Emitters process EAST3 nodes according to the following conversion table. Emitters must not re-interpret original Python syntax; they must generate code solely from EAST3 node kinds and fields.

#### Assignment / Unpack

| Python | EAST3 Node | Key Fields |
|---|---|---|
| `x = 1` | `Assign` | `target: Name`, `value` |
| `x: int = 1` | `AnnAssign` | `target: Name`, `annotation`, `value`, `decl_type` |
| `x, y = 1, 2` | `TupleUnpack` | `targets: [Name, ...]`, `value: Tuple` |
| `(x, y) = (1, 2)` | `TupleUnpack` | Same as without parentheses (note: current bug, to be fixed in P0-EAST-TUPLE-UNPACK) |
| `[x, y] = [1, 2]` | `TupleUnpack` | Same as without brackets (note: current bug, same as above) |
| `a, (b, c) = 1, (2, 3)` | `TupleUnpack` | Nested targets |
| `a[0], a[1] = 1, 2` | `TupleUnpack` | Targets may include `Subscript` |
| `x, y = y, x` | `Swap` | `left`, `right` |
| `x += 1` | `AugAssign` | `target`, `op`, `value` |

#### Loops

| Python | EAST3 Node | Key Fields |
|---|---|---|
| `for x in range(n)` | `ForRange` → `ForCore(StaticRangeForPlan)` | `start`, `stop`, `step`, `target_plan` |
| `for x in iterable` | `For` → `ForCore(RuntimeIterForPlan)` | `iter_plan.iter_expr`, `target_plan` |
| `for k, v in d.items()` | `ForCore` | `target_plan.direct_unpack_names: [k, v]`, `tuple_expanded: true` |
| `while cond` | `While` | `test`, `body` |

#### Functions / Closures

| Python | EAST3 Node | Key Fields |
|---|---|---|
| `def f(x: int) -> str` | `FunctionDef` | `arg_types`, `return_type`, `arg_usage` |
| Nested `def` | `ClosureDef` | Above + `captures: [{name, mode, type_expr}]` |
| `lambda x: x + 1` | `Lambda` | `args`, `body` |
| `fn: callable` argument | `arg_type_exprs.fn: GenericType(base="callable", args=[param_type, return_type])` | |

#### Control Flow

| Python | EAST3 Node | Key Fields |
|---|---|---|
| `if __name__ == "__main__":` | `main_guard_body` (separated at top level) | |
| `if / elif / else` | `If` | `test`, `body`, `orelse` |
| `try / except / finally` | `Try` | `body`, `handlers`, `finalbody` |
| `raise X` | `Raise` | `exc` |
| `return x` | `Return` | `value` |
| `pass` / `break` / `continue` | `Pass` / `Break` / `Continue` | |

#### Expressions

| Python | EAST3 Node | Key Fields |
|---|---|---|
| `range(n)` (non-`for` position) | `RangeExpr` | `start`, `stop`, `step` |
| `[x for x in it]` | `ListComp` → expanded into `ForCore` + `__comp_N.append()` | |
| `x if cond else y` | `IfExp` | `test`, `body`, `orelse` |
| `isinstance(x, T)` | `Unbox` node inserted after narrowing | `resolved_type` updated to the concrete type |
| `super().method()` | `Call` | receiver `resolved_type` resolved to the base class (note: fixed in P0-EAST3-INHERIT) |

#### Classes

| Python | EAST3 Node | Key Fields |
|---|---|---|
| `class Foo:` | `ClassDef` | `class_storage_hint`, `field_types`, `base` |
| `class Foo(Bar):` | `ClassDef` | `base: "Bar"` |
| `@dataclass class Foo:` | `ClassDef` | `dataclass: true` |
| `@trait class Foo:` | `ClassDef` + `meta.trait_v1` | |
| `type X = A \| B` | `ClassDef` + `meta.nominal_adt_v1` | `role: "family"` / `"variant"` |
| `match x:` | `Match` | `subject`, `cases: [MatchCase]` |

#### Imports

| Python | EAST3 Node | Key Fields |
|---|---|---|
| `import mod` | `Import` | `meta.import_bindings` |
| `from mod import sym` | `ImportFrom` | `meta.qualified_symbol_refs` |
| `from __future__ import annotations` | Not emitted (frontend-only) | |

#### Container Operations (Resolved Information in EAST3)

Emitters can determine container operation semantics from these EAST3 fields. They must not re-interpret Python method names.

| Python | Resolved Information in EAST3 |
|---|---|
| `d.get("key", 0)` | `semantic_tag: "stdlib.method.get"`, `resolved_type: "int64"`, `yields_dynamic: true` |
| `d.items()` | `resolved_type: "list[tuple[K,V]]"` |
| `d.keys()` / `d.values()` | `resolved_type: "list[K]"` / `"list[V]"` |
| `lst[i]` | Element type in `Subscript.resolved_type` |
| `str(x)` | `semantic_tag: "cast.str"`, `runtime_call: "py_to_string"` |
| `len(x)` | `runtime_call: "py_len"`, resolved via mapping.json |
| `x in container` | `Compare(In)`, determined by the container's `resolved_type` |

## 5. Common Node Attributes

Expression nodes (`_expr`) carry the following fields.

- `kind`, `source_span`, `resolved_type`, `type_expr`, `borrow_kind`, `casts`, `repr`
- `type_expr` is the structured type representation; when present, it takes precedence over `resolved_type`.
- `resolved_type` is a migration-compatible mirror string of the inferred type.
- `borrow_kind` is one of `value | readonly_ref | mutable_ref` (`move` is unused).
- Major expressions carry structured child nodes (`left/right`, `args`, `elements`, `entries`, etc.).

Function nodes (`FunctionDef`, `ClosureDef`) carry the following fields.

- `arg_types`, `arg_type_exprs`, `return_type`, `return_type_expr`, `arg_usage`, `renamed_symbols`
- `arg_type_exprs` / `return_type_expr` are the canonical structured forms of `arg_types` / `return_type`.
- **`return_type` is taken from the source type annotation.** When no annotation is present, the following rules apply:
  - If the body contains no `return <value>` statements → `return_type` is inferred as `None`
  - If the body contains a `return <value>` statement → fail-closed with `inference_failure` (an annotation is required)
  - Inferring the return **type** from `return` statement values is prohibited (body-scanning type inference is disallowed). The above determination is a single bit — "presence or absence of `return <value>`" — not type inference.
- `decorators` (list of raw decorator strings)
- `meta.template_v1` (optional — canonical metadata for `@template`)
- `meta.template_specialization_v1` (optional — specialization metadata materialized by the linked-program)
- `ClosureDef` additionally carries `captures: [{name, mode, type_expr?}, ...]`.
- `ClosureDef.mode` in v1 is `readonly | mutable`. `readonly` represents a capture that does not observe reassignment of an outer binding; `mutable` represents a capture that may observe reassignment of an outer binding.
- In `EAST3`, nested `FunctionDef` nodes are lowered to capture-analyzed `ClosureDef` nodes rather than being passed as-is to the backend.

Assignment statement nodes (`Assign`, `AnnAssign`) may carry the following field.

- `meta.extern_var_v1` (optional — canonical metadata for ambient global extern variables)

### 5.1 `Call.meta.copy_elision_safe_v1`

As a result of whole-program / linked-program analysis, the linker may attach `meta.copy_elision_safe_v1` to specific `Call` nodes.  
The purpose of v1 is to allow the backend to optimize **operations that copy in Python semantics** into an alias / borrow **only when it is legal to do so**.

The only canonically permitted target in v1 is:

- `Call(Name("bytes"), [expr])` where `expr.resolved_type == "bytearray"`

Schema for `copy_elision_safe_v1`:

- `schema_version`
  - Fixed value `1`
- `operation`
  - Fixed value `"bytes_from_bytearray"` in v1
- `source_name`
  - Local binding name of the copy source. In v1, only copy sources that are `Name(id=...)` are eligible; store the `id` as the stable identifier.
- `borrow_kind`
  - Fixed value `"readonly_ref"` in v1
- `analysis_scope`
  - The analysis scope used for the determination. In v1, `"linked_program"`.
- `proof_summary`
  - A short, human-readable description. The backend must not treat this string as authoritative.

Semantics:

- **Only when `copy_elision_safe_v1` is present** may the backend emit `bytes(bytearray)` as a "readonly alias / borrow" rather than a "copy".
- When `copy_elision_safe_v1` is **absent**, the backend must generate a copy as Python would (fail-closed).
- The backend / runtime must not infer or reconstruct this metadata independently. The sole canonical source is `Call.meta.copy_elision_safe_v1` as attached by the linker.

Required preconditions for the linker to attach v1:

1. The source `bytearray` is not mutated after the copy.
2. The resulting `bytes` is used exclusively as readonly.
3. Both conditions above must be verified by def-use / non-escape analysis across the entire `linked_program`.

Out of scope for v1:

- Copy elision for anything other than `bytes()`
- Aliasing based on emitter-independent judgment
- Introducing `borrow_kind=move`
- Speculative annotation at the raw `EAST3` stage

Class nodes may carry the following fields.

- `bases`, `decorators`
- `meta.nominal_adt_v1` (optional — canonical metadata for nominal ADT family / variant)

Rules for `FunctionDef.meta.template_v1`:

- `schema_version: 1`
- `params: [template_param_name, ...]`
- `scope: "runtime_helper"`
- `instantiation_mode: "linked_implicit"`
- `params` preserves declaration order; empty arrays are not allowed
- Raw `decorators` are for preserving the Python surface form; the authoritative source for the parser / linker / backend is `meta.template_v1`
- This function-level metadata is retained after linked-program processing and is not replaced by `meta.linked_program_v1`
- v1 does not materialize `@instantiate(...)`; instantiation information is therefore not stored here
- `template_v1` is "declaration metadata" and is not the place to store specialization seeds or lists of materialized helpers — those are determined by the linked-program optimizer from concrete types at callsites.
- The backend must not re-extract template parameters from raw decorators or surface syntax; it must reference only the `meta.template_v1` remaining in the linked module and the linker-confirmed summary.
- `TypeVar` annotations alone do not create `meta.template_v1`

Rules for `FunctionDef.meta.template_specialization_v1`:

- May only be attached to clones that the linked-program optimizer has materialized as implicit specializations
- Canonical shape: `schema_version: 1`, `origin_symbol: <module_id::name>`, `type_args: [concrete_type, ...]`
- `template_specialization_v1` is not a replacement for `template_v1`; it is supplementary metadata indicating the provenance of a materialized clone
- The backend / ProgramWriter uses this metadata and the linker summary — not raw decorators — when handling specialized helpers

Rules for `Assign` / `AnnAssign`.meta.extern_var_v1:

- `schema_version: 1`
- `symbol: str`
- `same_name: 0 | 1`
- In v1, may only be attached to top-level `name: Any = extern()` / `name: Any = extern("symbol")`
- `extern()` → `symbol == target_name` and `same_name == 1`
- `extern("symbol")` → `symbol == <literal>`; `same_name` is determined by whether it matches the target name
- Must not be attached for `extern(expr)` host fallback / runtime hooks
- The backend does not re-interpret raw `extern(...)` initializers; it uses `meta.extern_var_v1` as the authoritative ambient-global indicator

Rules for `ClassDef`.meta.nominal_adt_v1:

- `schema_version: 1`
- `role: "family" | "variant"`
- `family_name: str`
- `surface_phase: "declaration_v1"`
- For families:
  - `closed: 1`
  - Must not carry `variant_name` / `payload_style`
- For variants:
  - `variant_name: str`
  - `payload_style: "unit" | "dataclass"`
  - Base classes other than the family must not be encoded in this metadata
- Raw `decorators` / `bases` are for preserving the Python surface form; the authoritative source for nominal ADT determination is `meta.nominal_adt_v1`
- In v1, only top-level families and top-level variants are the canonical surface; nested variants and namespace sugar must not be lowered into this metadata
- Constructors do not introduce a dedicated node; a regular `Call` to the variant class is the canonical representation

### 5.1 C++ Pass-Through Notation via `leading_trivia`

- In EAST, pass-through does not introduce new nodes; it is preserved using existing `leading_trivia` entries (`kind: "comment"`).
- Interpreted comment directives:
  - `# Pytra::cpp <C++ line>`
  - `# Pytra::cpp: <C++ line>`
  - `# Pytra::pass <C++ line>`
  - `# Pytra::pass: <C++ line>`
  - `# Pytra::cpp begin` ... `# Pytra::cpp end`
  - `# Pytra::pass begin` ... `# Pytra::pass end`
- Output rules (C++ emitter):
  - Directive comments are not converted to ordinary comments (`// ...`); they are emitted as-is as C++ lines.
- Ordinary comments inside a `begin/end` block are emitted as C++ lines in order, with the leading `#` stripped.
  - Output position is immediately before the statement to which the `leading_trivia` is attached, indented to match the statement.
  - `blank` trivia continues to produce blank lines as before.
  - Multiple directives within the same `leading_trivia` are concatenated in declaration order.
- Priority:
  - Directive interpretation of `leading_trivia` takes highest precedence.
- This is independent of the existing docstring comment conversion (`"""..."""` → `/* ... */`) and the two do not overwrite each other.

### 5.2 Nominal ADT / Pattern / `match` Contract (v1)

- The Stage A declaration surface uses `ClassDef.meta.nominal_adt_v1` as authoritative; families and variants are represented by existing `ClassDef` nodes.
- For the `match/case` introduction in Stage B and later, statement nodes and pattern helper nodes are represented as follows.
  - `Match`
    - `subject: _expr`
    - `cases: MatchCase[]`
    - `source_span`
    - `repr` (optional)
  - `MatchCase`
    - `pattern: VariantPattern | PatternBind | PatternWildcard`
    - `guard: null` (guard patterns are not permitted in v1; always `null`)
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
- The v1 pattern surface is restricted to "variant pattern + payload bind + wildcard `_`".
- Literal patterns, nested patterns, guard patterns, and expression-form `match` are not part of the v1 node contract.
- A backend that receives `Match` / pattern nodes is expected to have a dedicated lowering lane; it must not fall back to `object` fallback or re-interpret raw method names.
- `Match` may carry `meta.match_analysis_v1` for static checking.
  - `schema_version: 1`
  - `family_name: str`
  - `coverage_kind: "exhaustive" | "wildcard_terminal" | "partial" | "invalid"`
  - `covered_variants: str[]`
  - `uncovered_variants: str[]`
  - `duplicate_case_indexes: int[]`
  - `unreachable_case_indexes: int[]`
  - `match_analysis_v1` is not a replacement for the parser surface; it is supplementary metadata holding the coverage summary finalized by the validator / lowering pass.
- v1 static checks apply only to closed nominal ADT families.
  - The exhaustive condition is either "enumerate every variant of the family exactly once" or "a terminal `PatternWildcard` covers all remaining variants".
  - A duplicate pattern means re-listing the same `variant_name`, or a second or subsequent `PatternWildcard`.
  - An unreachable branch is a `MatchCase` that appears after coverage has been closed by a wildcard, or after the same variant has already been covered.

## 6. Type System

### 6.1 Canonical Types

- Integer types: `int8`, `uint8`, `int16`, `uint16`, `int32`, `uint32`, `int64`, `uint64`
- Floating-point types: `float32`, `float64`
- Basic types: `bool`, `str`, `None`
- Composite types: `list[T]`, `set[T]`, `dict[K,V]`, `tuple[T1,...]`
- Extended types: `Path`, `Exception`, class names
- Auxiliary types: `unknown`, `module`, `callable[float64]`

### 6.2 Annotation Normalization

- `int` is normalized to `int64`.
- `float` is normalized to `float64`.
- `byte` is normalized to `uint8` (annotation alias for single-character / single-byte use).
- `float32` / `float64` are retained as-is.
- `any` / `object` are treated as synonymous with `Any`.
- For C++ runtime concrete representations (`object`, `None`, boxing/unboxing), refer to the `Any` / `object` representation policy in the [runtime specification](./spec-runtime.md).
- `bytes` / `bytearray` are normalized to `list[uint8]`.
- `pathlib.Path` is normalized to `Path`.
- The C++ runtime implementations of `str` / `list` / `dict` / `set` / `bytes` / `bytearray` use wrappers (composition) rather than STL inheritance.

### 6.3 `TypeExpr` Schema (Structured Type Representation)

`type_expr` is a backend-agnostic structured type representation. It has at least the following kinds.

- `NamedType`
  - `name: str`
  - Examples: `int64`, `float64`, `str`, `Path`
- `GenericType`
  - `base: str`
  - `args: TypeExpr[]`
  - Examples: `list[T]`, `dict[K,V]`, `tuple[T1,T2]`, `callable[float64]`
- `OptionalType`
  - `inner: TypeExpr`
  - Canonical form of `T | None`. Must not be represented as `UnionType`.
- `UnionType`
  - `options: TypeExpr[]`
  - `union_mode: general | dynamic`
  - `general` represents an open general union; `dynamic` represents a dynamic union containing `Any/object/unknown`.
- `DynamicType`
  - `name: Any | object | unknown`
  - Represents an open-world dynamic carrier.
- `NominalAdtType`
  - `name: str`
  - `adt_family: str` (optional; e.g., `json`)
  - `variant_domain: str` (optional; e.g., `closed`)
  - Represents closed nominal ADTs such as `JsonValue`.

Notes:

- `bytes` / `bytearray` may continue to be normalized to `list[uint8]` as before; an independent kind is not required.
- The exact JSON field names may be uniformly snake_case or camelCase to match the implementation, but the semantics must satisfy the kinds/fields listed above.
- Nodes that directly carry an annotation may have a corresponding `*_type_expr` field alongside the existing string field.

### 6.4 Union Three-Way Classification and `resolved_type` Mirror Precedence

Required rules:

- `T | None` must always be normalized to `OptionalType(inner=T)`; it must not remain as `UnionType(options=[T, None])`.
- A union containing `Any/object/unknown` must be treated as `UnionType(union_mode=dynamic)` and must not be lowered using the same rules as a general union.
- JSON decode-first surfaces such as `JsonValue` / `JsonObj` / `JsonArr` must be treated as `NominalAdtType`, not as a general union.
- `resolved_type`, `arg_types`, and `return_type` are all demoted to mirrors derived from `type_expr`, `arg_type_exprs`, and `return_type_expr`.
- When both `type_expr` and `resolved_type` are present, `type_expr` is always authoritative. Contradictions must be treated as `semantic_conflict` fail-closed.
- During migration, legacy nodes that carry only `resolved_type` are acceptable, but when adding an EAST2 canonical, EAST3 canonical, validator, or backend contract, `type_expr` must be the primary input.

Examples:

- `int | None` → `OptionalType(NamedType("int64"))`
- `int | bool` → `UnionType(union_mode="general", options=[NamedType("int64"), NamedType("bool")])`
- `int | Any` → `UnionType(union_mode="dynamic", options=[NamedType("int64"), DynamicType("Any")])`
- `JsonValue` → `NominalAdtType(name="JsonValue", adt_family="json", variant_domain="closed")`

### 6.5 `JsonValue` Nominal Closed ADT Lane

`JsonValue` / `JsonObj` / `JsonArr` are treated not as a general union or `object` fallback, but as a JSON-specific nominal closed ADT lane.

Required rules:

- The type of `json.loads(...)` is `NominalAdtType(name="JsonValue", adt_family="json", variant_domain="closed")`.
- `json.loads_obj(...)` / `json.loads_arr(...)` return `OptionalType(NominalAdtType("JsonObj"))` / `OptionalType(NominalAdtType("JsonArr"))` respectively.
- `JsonValue.as_*`, `JsonObj.get_*`, `JsonArr.get_*` are treated as decode / narrowing operations specific to nominal ADTs, not as general-purpose casts.
- The `JsonValue` lane must not be expanded into `UnionType(union_mode=general|dynamic)`.

Resolved semantic tags fixed in `EAST2 -> EAST3` (canonical):

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

Responsibility boundaries:

- The frontend / lowering is responsible for normalizing raw `json.loads` / `as_*` / `get_*` surfaces to the semantic tags above or an equivalent dedicated IR category.
- The backend / hook must not re-interpret JSON decode semantics from raw callee names, attribute names, or receiver type strings.
- The validator must verify the consistency of `type_expr` and semantic tags for the `JsonValue` nominal lane, and must stop any path that would emit `JsonValue` as a general union with `semantic_conflict` or `unsupported_syntax`.
- If the target does not yet have a `JsonValue` nominal carrier or decode-op mapping, fail-closed; do not silently degrade to `object` / `String` / `PyAny`.

## 7. Type Inference Rules

- `Name`: resolved from the type environment. Unresolved → `inference_failure`.
- `Constant`:
  - Integer literals → `int64`
  - Floating-point literals → `float64`, booleans → `bool`, strings → `str`, `None` → `None`
- `List/Set/Dict`:
  - Non-empty → inferred by unifying element types
  - Empty → normally `inference_failure`
  - Exception: empty containers with an `AnnAssign` annotation adopt the annotation type
- `Tuple`: constructs `tuple[...]`.
- `BinOp`:
  - Numeric operations `+ - * % // /` are inferred
  - Mixed numeric types apply `float32/float64` type promotion and attach `casts`
  - `Path / str` → `Path`
  - `str * int` and `list[T] * int` are supported
  - Bitwise operations `& | ^ << >>` are inferred as integer types
  - Note: The Python/C++ difference for `%` is not absorbed by EAST.
  - EAST retains `%` as an operator; the generator switches output according to `--mod-mode` (`native` / `python`).
- `Subscript`:
  - `list[T][i]` → `T`
  - `dict[K,V][k]` → `V`
  - `str[i]` → `str`
  - `list` / `str` slices preserve the same type
  - EAST retains `Subscript` / `Slice` as-is; the `str-index-mode` / `str-slice-mode` semantics are applied by the generator.
  - The current C++ generator implements `byte` / `native`; `codepoint` is not yet implemented.

### 7.0.1 `Subscript.meta.subscript_access_v1`

The linked-program optimizer / EAST3 optimizer may attach `meta.subscript_access_v1` to `Subscript` nodes as canonical metadata for the subscript access policy.

Purpose:

- Whether negative indices need normalization
- Whether bounds checking is required
- The authoritative source for the backend to choose between a full-check helper like `py_list_at_ref(...)` and direct indexing

Schema for `subscript_access_v1`:

```json
{
  "schema_version": "subscript_access_v1",
  "negative_index": "normalize | skip",
  "bounds_check": "full | off",
  "reason": "string"
}
```

Rules:

- `negative_index`
  - `normalize`: to preserve Python negative-index semantics, the backend applies normalization such as `-1 → len(values) - 1`.
  - `skip`: the optimizer has determined that negative index normalization is unnecessary on this path. The backend must not recompute negative correction.
- `bounds_check`
  - `full`: requires bounds checking equivalent to Python's. The backend must maintain behavior equivalent to `IndexError`.
  - `off`: the optimizer has determined that bounds checking may be omitted on this path. The backend may use direct / native indexing.
- `reason`
  - An optional string in which the optimizer records the reason for the annotation.
  - Recommended v1 values: `for_range_index`, `non_negative_constant`, `negative_literal`, `mode_default`

Responsibility boundaries:

- When the optimizer has attached `subscript_access_v1`, the backend selects the access helper solely from this metadata.
- The backend / runtime must not re-infer `negative_index` / `bounds_check` from the raw `Subscript.slice` or surrounding loops.
- When `subscript_access_v1` is absent, the backend must fail-closed to the default safe path (e.g., full-check helper).
- Unknown values, missing fields, or corruption in `subscript_access_v1` are treated fail-closed; the backend must not select direct indexing.
- `Call`:
  - Known: `int`, `float`, `bool`, `str`, `bytes`, `bytearray`, `len`, `range`, `min`, `max`, `round`, `print`, `write_rgb_png`, `save_gif`, `grayscale_palette`, `perf_counter`, `Path`, `Exception`, `RuntimeError`
  - `float(...)`, `round(...)`, `perf_counter()`, and primary `math.*` functions → `float64`
  - `bytes(...)` / `bytearray(...)` → `list[uint8]`
  - Class constructors / methods are inferred from pre-collected type information
- `ListComp`: only single-generator list comprehensions are supported
- `BoolOp` (`or` / `and`) is retained in EAST as `kind: BoolOp`.
  - When generating C++, it is emitted as a boolean operation (`&&` / `||`) if the expected type is `bool`.
  - When the expected type is not `bool`, it is emitted as a Python value-selection expression.
    - `a or b` → `truthy(a) ? a : b`
    - `a and b` → `truthy(a) ? b : a`
  - Value-selection determination and emission are handled in `src/pytra-cli.py`; EAST does not lower to additional nodes.
- `IfExp` (ternary operator `body if test else orelse`):
  - Resolve `resolved_type` for both the true branch (`body`) and the false branch (`orelse`).
  - If both sides have the same type `T`, the IfExp type is `T`. It must not be collapsed to `unknown`.
  - If one side is `None`, generate `OptionalType(inner=T)` from the other side's type `T`. Example: `expr if cond else None` → `Optional[T]`.
  - If both sides are different non-`None` types, generate `UnionType`. Example: `a if cond else b` (a: int, b: str) → `int | str`.
  - For mixed numeric types (`int64 if cond else float64`), apply the cast rules (§8) and attach `ifexp_numeric_promotion`.

### 7.1 isinstance Type Narrowing (type narrowing)

The type of a target variable is automatically narrowed based on `isinstance` checks.

Rules:

- The resolver detects `isinstance(x, T)` patterns in condition expressions and updates the `resolved_type` / `type_expr` of `x` to `T` within the relevant scope.
- Narrowing is implemented as a type-environment update in the resolve stage and does not introduce new EAST nodes.
- The emitter only maps the already-narrowed `resolved_type` and has no additional responsibility.

Supported patterns (v1):

**Pattern 1: narrowing inside an if/elif block**

```python
val: JsonVal = json.loads(data)

if isinstance(val, dict):
    # val is type-resolved as dict[str, JsonVal]
    val.get("key")  # OK

elif isinstance(val, list):
    # val is type-resolved as list[JsonVal]
    val[0]  # OK
```

**Pattern 2: early return guard (fallthrough narrowing)**

When the if block of `if not isinstance(x, T):` always exits (`return` / `raise` / `break` / `continue`), `x` is narrowed to `T` in subsequent statements.

```python
def process(val: JsonVal) -> str:
    if not isinstance(val, dict):
        return ""
    # val is dict[str, JsonVal] from here on
    val.get("key")  # OK
```

**Pattern 3: ternary isinstance**

In `y = x if isinstance(x, T) else default`, `x` is resolved as `T` on the true branch.

```python
owner_node = owner if isinstance(owner, dict) else None
# type of owner_node is dict[str, JsonVal] | None
```

**Pattern 4: propagation within a block**

Narrowing naturally propagates into loops and other constructs inside the if block.

```python
if isinstance(items, list):
    for item in items:  # items is already type-resolved as list
        process(item)
```

Safety constraints:

- If `x` is reassigned inside the if block, narrowing is invalidated.
- The following are not supported in v1 (candidates for future extension):
  - Exclusion-type inference in `else` blocks
  - Combining `isinstance` with `and` / `or`
- For unsupported patterns, narrowing is not applied and a manual `cast` is required as before (fail-closed).

Backward compatibility:

- Manual `cast` remains valid and can be used alongside narrowing.
- Narrowing is equivalent to an implicit cast and does not break type safety.

`IsInstance` node's `expected_type_name` field (EAST3):

- The `IsInstance` node in EAST3 directly holds the expected type name (e.g., `"dict"`, `"str"`, `"list"`, `"int32"`, `"Dog"`) in the `expected_type_name: str` field.
- Type ID constants such as `PYTRA_TID_DICT` (the `expected_type_id` field) are deprecated. Emitters must not maintain a reverse-lookup table.
- POD types (`int8` through `float64`) and user-defined class names go into the same field.
- `IsSubclass` / `IsSubtype` continue to use `expected_type_id` (integer type ID expression). That field is exclusive to them and does not appear on `IsInstance`.

On `range`:

- Even if `Call(Name("range"), ...)` appears in the input AST, the final EAST converts it to a dedicated node (e.g., `ForRange` / `RangeExpr`); it is never left as a raw `Call`.
- A case where `range` remains as-is is treated as an EAST construction defect and is not silently rescued downstream.

On `lowered_kind: BuiltinCall`:

- EAST attaches `runtime_call` to reduce branching in downstream implementations.
- Representative `runtime_call` values implemented so far:
  - `py_print`, `py_len`, `py_to_string`, `static_cast`
  - `py_min`, `py_max`, `perf_counter`
  - `list.append`, `list.extend`, `list.pop`, `list.clear`, `list.reverse`, `list.sort`
  - `set.add`, `set.discard`, `set.remove`, `set.clear`
  - `write_rgb_png`, `save_gif`, `grayscale_palette`
  - `py_isdigit`, `py_isalpha`

On `yields_dynamic`:

- For method calls that extract container elements (`dict.get`, `dict.pop`, `dict.setdefault`, `list.pop`), the type in Python semantics (`resolved_type`) is a concrete type (e.g., `int64`), but the runtime implementation for non-template languages (Go, Java, etc.) may return a dynamic type (`any` / `interface{}` / `Object`).
- Such `Call` nodes carry `yields_dynamic: true`.
- It is not attached when `resolved_type` is already a dynamic type (`Any`, `object`, `unknown`, `None`).
- Emitters can use `yields_dynamic: true` to decide whether a type assertion / downcast is needed. They must not make that determination by pattern-matching on generated expression strings.
- The corresponding `semantic_tag` values are `container.dict.get`, `container.dict.pop`, `container.dict.setdefault`, and `container.list.pop`.
- When adding future container extraction methods, attach a `container.*`-prefixed `semantic_tag` and `yields_dynamic` as a pair.

Responsibility boundaries for `runtime_module_id` / `runtime_symbol` / `runtime_call` (required):

- `runtime_module_id`, `runtime_symbol`, `runtime_call`, `resolved_runtime_call`, `resolved_runtime_source`, and `semantic_tag` are treated as authoritative information in EAST3.
- The backend / emitter is limited to rendering this resolved information and must not re-resolve function or module names.
- If information needed by a backend is not represented in EAST3, the EAST3 schema must be extended first and the information placed there.
- `runtime_module_id` / `runtime_symbol` are target-agnostic; they do not hold target-specific paths such as `runtime/cpp/std/time.gen.h`.
- Per-target include paths / compile sources / companions are derived by `tools/runtime_symbol_index.json` and the backend.

Prohibited:

- Placing individual symbol branches such as `if runtime_call == "perf_counter"` in emitters or frontends/sig registries.
- Embedding runtime dispatch tables for `py_assert_*` / `json.loads` / `write_rgb_png` etc. in emitters or frontends/sig registries.
- Bringing call-resolution rules into the backend side on the grounds that "EAST3 is insufficient".
- Embedding target-specific file paths in EAST3.

EAST3 → backend resolved call contract (fixed):

- Target nodes:
  - `Call`
  - `Attribute` (including attribute accesses such as `Path.parent/name/stem`)
- Resolved attributes the backend may reference:
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
  4. When all of the above are empty and `semantic_tag` is `stdlib.*` → fail-closed (implicit fallback is prohibited)
- `resolved_runtime_source` contract:
  - `import_symbol`: resolved via `from ... import ...`
  - `module_attr`: resolved via `module.symbol`
  - (For backward compatibility) implementations that return the `runtime_call` / `resolved_runtime_call` string are acceptable, but new implementations should prefer `import_symbol` / `module_attr`.
- Backend API constraint:
  - Emitters must not interpret stdlib / runtime semantics from the raw `callee/owner/attr` names of `Call/Attribute` nodes.
  - The emitter's runtime-call rendering API must be limited to accepting resolved attributes as input; it must not contain re-resolution logic that depends on raw AST nodes.
  - Using `resolved_type` for type selection is permitted, but reverse-lookup of module names or function names is not.

Operational enforcement (CI):

- `python3 tools/check/check_emitter_runtimecall_guardrails.py`
  - Fails on any increase in direct runtime/stdlib branches in non-C++ emitters.
- `python3 tools/check/check_emitter_forbidden_runtime_symbols.py`
  - Fails on any re-introduction of runtime implementation symbols (e.g., `__pytra_write_rgb_png`) into emitters.
- `python3 tools/check/check_noncpp_east3_contract.py`
  - Statically detects responsibility-boundary comment violations and EAST3 contract deviations in per-language smoke tests.

On `.get(...).items()` for `dict[str, Any]`:

- When generating C++, the assumption is `dict[str, object]`; `Dict` / `List` literal values are recursively converted with `make_object(...)` during initialization.
- When a dictionary default value is supplied with `.get(..., {})`, it is normalized to `dict[str, object]`.

## 8. Cast Specification

`casts` are emitted upon numeric promotion.

```json
{
  "on": "left | right | body | orelse",
  "from": "int64",
  "to": "float32 | float64",
  "reason": "numeric_promotion | ifexp_numeric_promotion"
}
```

## 9. Argument Reassignment Detection (`arg_usage`)

`arg_usage` is attached to each `FunctionDef`.

- Values are `readonly | reassigned`.
- `reassigned` conditions:
  - Assignment / augmented assignment to a parameter name (`Assign` / `AnnAssign` / `AugAssign`)
  - A parameter name appearing as the left-hand or right-hand side of `Swap`
  - A parameter name appearing as the target of `for` / `for range`
  - The `name` in `except ... as name` matching a parameter name
- Assignments inside nested `FunctionDef` / `ClassDef` are not included in the outer function's determination.
- All other cases → `readonly`.

Currently, this information is primarily used by the backend for argument `mut` determination.

## 10. Supported Statements

- `FunctionDef`, `ClassDef`, `Return`
- `Assign`, `AnnAssign`, `AugAssign`
- `Expr`, `If`, `For`, `ForRange`, `While`, `Try`, `Raise`
- `Import`, `ImportFrom`, `Pass`, `Break`, `Continue`

Notes:

- `Assign` covers single-target statements only.
- Tuple assignment is supported (e.g., `x, y = ...`, `a[i], a[j] = ...`).
- For name targets, the type environment is updated when the RHS tuple type is known.
- `from module import *` (wildcard imports) are not supported.

## 11. Pre-Collection of Class Information

Before code generation, the following information is collected.

- Class names
- Simple inheritance relationships
- Method return types
- Field types (from class-body `AnnAssign` / `__init__` assignment analysis)

## 12. Error Contract

`EastBuildError` carries `kind`, `message`, `source_span`, and `hint`.

- `inference_failure`
- `unsupported_syntax`
- `semantic_conflict`

`SyntaxError` is also converted to this format.

## 13. Human-Readable View

- `--human-output` emits a C++-style pseudo-source.
- The purpose is to facilitate review; strict compilability as C++ is not guaranteed.
- EAST fields such as `source_span`, `resolved_type`, `ForRange`, and `renamed_symbols` are preserved and visualized.

## 14. Known Limitations

- Does not cover all Python syntax (Pytra targets a subset).
- Advanced dataflow analysis (precise aliasing / side-effect propagation) is not implemented.
- `borrow_kind=move` is unused.

## 15. Validation Status

- 32/32 `test/fixtures` can be converted by `src/toolchain/misc/east.py` (`ok: true`)
- 16/16 `sample/py` can be converted by `src/toolchain/misc/east.py` (`ok: true`)
- 16/16 `sample/py` can be processed end-to-end by `src/pytra-cli.py` (convert → compile → run, `ok`)

<a id="east-stages"></a>
## 16. Current Stage Structure (2026-02-24)

- EAST is processed in three stages: `EAST1 -> EAST2 -> EAST3`.
- In the current implementation, the default path of `py2*.py` targets `EAST3`.
- `pytra-cli.py --target cpp` accepts only `--east-stage 3`; `--east-stage 2` causes an error and stops.
- The eight non-C++ converters (`py2rs.py`, `py2cs.py`, `py2js.py`, `py2ts.py`, `py2go.py`, `py2java.py`, `py2kotlin.py`, `py2swift.py`) maintain `--east-stage 2` as a migration-compatibility mode (with warnings).
- `meta.dispatch_mode` is retained across all stages; semantic application occurs only once, during `EAST2 -> EAST3`.

### 16.1 Stage Responsibilities

- `EAST1` (Parsed):
  - IR produced immediately after parsing.
  - Preserves source spans / trivia; backend-specific nodes must not be mixed in.
- `EAST2` (Normalized):
  - Syntax-normalized IR.
  - Stabilizes `ForRange` / `RangeExpr`, import normalization, and type resolution results.
- `EAST3` (Core):
  - Backend-agnostic, semantics-finalized IR.
  - boxing/unboxing, `Obj*` instructions, `type_id` determination, and iteration plans are made into explicit instructions.
  - However, program-wide decisions (call graph / SCC / global non-escape / container ownership / final `type_id` table) are delegated to the linker stage.

### 16.1.1 Stage Boundary Table (Input / Output / Prohibitions / Responsible Files)

| Stage/Boundary | Input | Output | Prohibitions | Responsible Files |
| --- | --- | --- | --- | --- |
| `EAST1` | `Source` (`.py` / parser backend specification) | `Module` document with `east_stage=1` | `EAST2/EAST3` conversion, dispatch semantic application, target-dependent node generation | `src/toolchain/compile/core.py`, `src/toolchain/compile/east1.py` |
| `EAST2` | `EAST1` document | Normalized `Module` document with `east_stage=2` | Dispatch semantic application, boxing/type_id instruction generation, backend syntax decisions | `src/toolchain/compile/east2.py` |
| `EAST3` | `EAST2` document + `meta.dispatch_mode` | Core-instructionized `Module` document with `east_stage=3` | Mapping to target language syntax, semantic re-evaluation by hooks | `src/toolchain/compile/east2_to_east3_lowering.py`, `src/toolchain/compile/east3.py` |
| `Link` | Raw `EAST3` group + `link-input.v1` | Linked module group (`east_stage=3` maintained) + `link-output.v1` | Target language rendering, runtime placement, build manifest generation | `src/toolchain/link/*` (to be added) |

Notes:
- `Link` is not a new `east_stage`. Both input and output module bodies maintain `east_stage=3`.
- The canonical data added by `Link` is `link-output.v1` and `meta.linked_program_v1` in linked modules.

### 16.2 Invariants

1. `east_stage` and node shape must be consistent.  
2. Semantic application of `dispatch_mode` occurs exactly once, during `EAST2 -> EAST3`.  
3. The backend / hooks do not re-evaluate `EAST3` semantics.  
4. Whole-program summaries are not finalized in raw `EAST3` alone; the linker materializes them into `link-output.v1` and linked modules.  

<a id="east-pipeline"></a>
## 17. Pipeline Specification (Unified)

1. `Source -> EAST1`  
2. `EAST1 -> EAST2` (Normalize pass)  
3. `EAST2 -> EAST3` (Core Lowering pass)  
4. `EAST3 (raw module) -> LinkedProgramLoader / LinkedProgramOptimizer`  
5. `linked module (EAST3) -> TargetEmitter` (language mapping)  

Notes:
- `--object-dispatch-mode {type_id,native}` is determined at compile start and reflected in `iter_plan` / `Obj*` instructions during `EAST2 -> EAST3`.
- The backend / hooks must not re-evaluate the mode and substitute instructions.
- The linker is responsible only for verifying `dispatch_mode` consistency and finalizing whole-program summaries; it must not generate target language syntax on behalf of the backend.

### 17.1 Linked Module `meta` Contract

A post-linking module maintains `kind=Module` / `east_stage=3` and additionally carries `meta.linked_program_v1`.

A synthetic helper module generated by the linked-program optimizer may additionally carry `meta.synthetic_helper_v1`.

Required keys for `meta.linked_program_v1`:

- `program_id`
- `module_id`
- `entry_modules`
- `type_id_resolved_v1`
- `non_escape_summary`
- `container_ownership_hints_v1`

Responsibility boundaries:

- Raw `EAST3` does not carry `meta.linked_program_v1`.
- Linked modules must carry `meta.linked_program_v1`.
- The backend is permitted to read `meta.linked_program_v1` and `link-output.v1`, but must not recompute equivalent information.
- Per-function / per-call linked summaries (e.g., `FunctionDef.meta.escape_summary`, `Call.meta.non_escape_callsite`) may be finalized by the linker.
- `FunctionDef.meta.template_v1`, as parser/EAST-build-derived metadata, must be retained in linked modules; the linker must not overwrite it.

<a id="east-file-mapping"></a>
## 18. Current / Post-Migration Responsibility Mapping (2026-02-24)

| Stage | Responsibility | Current Implementation (at migration start) | Authoritative Post-Migration |
| --- | --- | --- | --- |
| EAST1 | Post-parser IR generation | `src/toolchain/misc/east_parts/core.py` (compatibility shim) | `src/toolchain/compile/core.py` |
| EAST1 | EAST1 entry-point API | `src/toolchain/misc/east_parts/east1.py` (via compatibility wrapper) | `src/toolchain/compile/east1.py` |
| EAST2 | EAST1 → EAST2 normalization API | `src/toolchain/misc/east_parts/east2.py` (compatibility wrapper + selfhost fallback) | `src/toolchain/compile/east2.py` |
| EAST3 | EAST2 → EAST3 lowering body | `src/toolchain/misc/east_parts/east2_to_east3_lowering.py` (compatibility shim) | `src/toolchain/compile/east2_to_east3_lowering.py` |
| EAST3 | EAST3 entry-point API | `src/toolchain/misc/east_parts/east3.py` (via compatibility wrapper) | `src/toolchain/compile/east3.py` |
| Bridge | Backend entry point (C++) | `src/pytra-cli.py` (`--east-stage 3` only) | `src/pytra-cli.py` (EAST3 only) |
| CLI Compat | Legacy API exposure | `src/toolchain/misc/transpile_cli.py` (compatibility shim) | `src/toolchain/frontends/transpile_cli.py` (implementation) |

<a id="east1-build-boundary"></a>
## 19. `EAST1` Build Entry-Point Responsibility Boundary

Purpose:
- Separate the entry-point responsibility for `.py/.json -> EAST1` builds and reduce the responsibilities of `transpile_cli.py`.

Structure:
- `core.py`: self-hosted parser implementation (low-level; current authoritative source is `src/toolchain/compile/core.py`)
- `east1_build.py`: build entry point (to be added)
- `east1.py`: stage contract helper (thin API)
- `pytra-cli.py --target cpp`: responsible only for delegating `_analyze_import_graph` / `build_module_east_map` to `East1BuildHelpers`
- `transpile_cli.py`: the implementation lives in `src/toolchain/frontends/transpile_cli.py`; `src/toolchain/misc/transpile_cli.py` is a thin compatibility-exposure wrapper.

Acceptance criteria:
1. `EAST1` build is limited to attaching `east_stage=1` and does not perform `EAST1 -> EAST2`.  
2. The error contract of `load_east_document_compat` (`input_invalid` family) is maintained.  
3. `compiler/transpile_cli.py` carries no build implementation logic; it delegates to `frontends/transpile_cli.py`.  
4. `python3 tools/check/check_selfhost_cpp_diff.py --mode allow-not-implemented` is included in the regression pipeline; any diff is extracted to a `todo` and tracked.  
5. `tools/unittest/ir/test_east1_build.py` and `tools/unittest/emit/cpp/test_py2cpp_east1_build_bridge.py` fix the `EAST1` entry-point contract and the `py2cpp` delegation path.  
6. The import graph analysis implementation lives in `src/toolchain/frontends/east1_build.py` (`_analyze_import_graph_impl`); `compiler/transpile_cli.py`'s `analyze_import_graph` / `build_module_east_map` retain only thin compatibility-exposure wrappers.  

<a id="east-migration-phases"></a>
## 20. Migration Phases (EAST3 Main-Path Promotion)

1. Phase 0: Fix contract tests (`EAST3` route required items, `ForCore`/`iter_plan` requirements, dispatch reflection points)
2. Phase 1: API separation (delegate responsibilities to `east1.py` / `east2.py` / `east3.py`)
3. Phase 2: EAST3 main-path promotion (audit re-evaluation logic in `pytra-cli.py --target cpp`)
4. Phase 3: Hook separation (resolve stage-mixed state during migration window)
5. Phase 4: EAST2 path demotion (reduce to compatibility mode → phased removal)

Notes:
- Progress management for each phase is tracked in `docs/ja/todo/index.md` and `docs/ja/plans/plan-east123-migration.md`.
- Current status for Phase 4: all `py2*.py` default to `--east-stage 3`. `pytra-cli.py --target cpp` rejects `--east-stage 2` with an error; the eight non-C++ converters maintain a compatibility path with `warning: --east-stage 2 is compatibility mode; default is 3.`.

## 21. Acceptance Criteria for EAST Adoption

- Existing `test/fixtures` must be convertible via EAST.
- On inference failure, an error containing `kind` / `source_span` / `hint` must be returned.
- Spec differences must be documented; downstream emitters must not silently rescue them.
- `--object-dispatch-mode` must be applied only during `EAST2 -> EAST3`.
- No new language-agnostic semantics must be implemented in hooks.

## 22. Minimum Verification Commands

```bash
python3 tools/check/check_py2cpp_transpile.py
python3 tools/check/check_noncpp_east3_contract.py
python3 tools/check/check_selfhost_cpp_diff.py --mode allow-not-implemented
```

## 23. Future Extensions (Policy)

- `borrow_kind` currently uses `value | readonly_ref | mutable_ref`; `move` is unused.
- The representation is designed to be connectable to reference annotations for Rust (`&` / `&mut` equivalents) in the future.
  - However, Rust-specific final decisions (ownership details, lifetime details) are the backend's responsibility.

## 24. EAST2 Common IR Contract (Depythonization Draft)

Purpose:
- Treat EAST2 as "the first common IR shared across multiple frontends", isolating direct dependencies on Python-specific names (builtin names, `py_*` runtime names) outside the boundary.

### 24.1 Node Categories (Information Retained in EAST2)

- Statement nodes:
  - `Module`, `FunctionDef`, `ClassDef`, `If`, `While`, `For`, `ForRange`, `Assign`, `AnnAssign`, `AugAssign`, `Return`, `Expr`, `Import`, `ImportFrom`, `Raise`, `Try`, `Pass`, `Break`, `Continue`, `Match`
- Expression nodes:
  - `Name`, `Constant`, `Attribute`, `Call`, `Subscript`, `Slice`, `Tuple`, `List`, `Dict`, `Set`, `ListComp`, `GeneratorExp`, `IfExp`, `Lambda`, `BinOp`, `BoolOp`, `Compare`, `UnaryOp`, `RangeExpr`
- Auxiliary nodes:
  - Normalization information for `For` / `ForRange` prior to conversion into `ForCore` (`iter_mode`, `target_type`, `range_mode`)
  - `MatchCase`, `VariantPattern`, `PatternBind`, `PatternWildcard`

### 24.2 Neutral Contract for Operators, Types, and Metadata

- Operators:
  - `BinOp.op` retains `Add/Sub/Mult/Div/FloorDiv/Mod/BitAnd/BitOr/BitXor/LShift/RShift` as string enumerations.
  - `Compare.ops` retains `Eq/NotEq/Lt/LtE/Gt/GtE/In/NotIn/Is/IsNot`.
  - `BoolOp.op` retains `And/Or`.
- Types:
  - `type_expr` is the authoritative type representation; backend-specific representations are not used.
  - `resolved_type` may be retained only as a legacy mirror of logical type names (`int64`, `float64`, `list[T]`, `dict[K,V]`, `tuple[...]`, `Any`, `unknown`).
  - `OptionalType` / `UnionType(union_mode=dynamic)` / `NominalAdtType` are retained as distinct categories.
- Metadata:
  - `meta.dispatch_mode` is retained as the compile-policy value `native | type_id`; semantic application occurs only once, during `EAST2 -> EAST3`.
  - Import normalization information (`import_bindings`, `qualified_symbol_refs`, `import_modules`, `import_symbols`) is retained as frontend resolution results.

### 24.3 Prohibitions (EAST2 Boundary)

- Do not leak contracts that interpret `builtin_name` as Python built-in identifiers (`len`, `str`, `range`, etc.) to the backend side.
- Do not fix `py_*` strings in `runtime_call` as meaningful (`py_len`, `py_to_string`, `py_iter_or_raise`, etc.).
- Do not treat `py_tid_*` compatibility names as public EAST2 contracts (they remain internal to the compatibility bridge).

### 24.4 Diagnostics and Fail-Closed Contract

- Unresolvable nodes / types stop with `ok=false` + `error.kind` (`inference_failure` / `unsupported_syntax` / `semantic_conflict`).
- Inputs outside the neutral contract (invalid `dispatch_mode`, unsupported node shapes, missing required metadata) are not silently rescued; they terminate fail-closed.
- Inputs where `type_expr` and the `resolved_type` mirror are contradictory terminate fail-closed as `semantic_conflict`.
- When `meta.nominal_adt_v1`, `Match`, or pattern nodes have shapes outside the v1 contract (nested variants, guard patterns, literal patterns, namespace-sugar dependencies, etc.), terminate fail-closed as `unsupported_syntax` or `semantic_conflict`.
- When `Match.meta.match_analysis_v1` indicates `coverage_kind=partial` or `invalid`, stop before passing to the backend with `semantic_conflict`.
- Compatibility fallbacks are only permitted during the stage migration window and must be recorded in logs with an explicit `legacy` flag.

### 24.5 Connection Principles for EAST2 → EAST3

- EAST2 carries only "what to do (semantic tags)"; object-boundary instructions (`Obj*`, `ForCore.iter_plan`) are finalized in `EAST3`.
- `EAST2 -> EAST3` lowering looks at `type_expr` to route `optional` / `dynamic union` / `nominal ADT` into separate lanes; it must not determine semantics by re-parsing `resolved_type` strings.
- `JsonValue` decode / narrowing is normalized in `EAST2 -> EAST3` to the resolved semantic tags (`json.loads`, `json.value.as_*`, `json.obj.get_*`, `json.arr.get_*`) or an equivalent dedicated IR category; raw method-name interpretation must not be left to the backend.
- Frontend-specific (Python builtins/stdlib) resolutions are converted to neutral tags in an adapter layer before being passed to EAST2.
- The backend / hooks, operating at EAST3 and beyond, are responsible only for language-specific mapping; they must not re-interpret EAST2 contracts.
