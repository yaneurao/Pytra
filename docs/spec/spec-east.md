<a href="../../docs-ja/spec/spec-east.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# EAST Specification (Implementation-Aligned)

This document describes the EAST specification aligned with the current implementation in `src/pytra/compiler/east.py`.

## 1. Purpose

- EAST (Extended AST) is an intermediate representation that converts Python AST into language-agnostic JSON with semantic annotations.
- Type resolution, cast information, readonly/mutable argument classification, and `main`-guard separation are fixed in this front-end stage.
- Python's built-in `ast` module alone cannot preserve enough source context for practical transpilation workflows (for example, comment handling), so EAST and its Python parser are introduced.

## 2. Input/Output

### 2.1 Input

- One UTF-8 Python source file.

### 2.2 Output Format

- On success:

```json
{
  "ok": true,
  "east": { "...": "..." }
}
```

- On failure:

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

- `python src/pytra/compiler/east.py <input.py> [-o output.json] [--pretty] [--human-output output.cpp]`
- `--pretty`: outputs formatted JSON.
- `--human-output`: outputs a C++-style human-readable view.
- `python src/py2cpp.py <input.py|east.json> [-o output.cpp]`: EAST-based C++ generator.

## 3. Top-Level EAST Structure

`east` object includes:

- `kind`: always `Module`
- `source_path`: input path
- `source_span`: module span
- `body`: normal top-level statements
- `main_guard_body`: body of `if __name__ == "__main__":`
- `renamed_symbols`: rename map
- `meta.import_bindings`: canonical import bindings (`ImportBinding[]`)
- `meta.qualified_symbol_refs`: resolved `from-import` references (`QualifiedSymbolRef[]`)
- `meta.import_modules`: binding info for `import module [as alias]` (`alias -> module`)
- `meta.import_symbols`: binding info for `from module import symbol [as alias]` (`alias -> {module,name}`)

`ImportBinding` fields:

- `module_id`
- `export_name` (empty string for `import M`)
- `local_name`
- `binding_kind` (`module` / `symbol`)
- `source_file`
- `source_line`

`QualifiedSymbolRef` fields:

- `module_id`
- `symbol`
- `local_name`

## 4. Syntax Normalization

- `if __name__ == "__main__":` is extracted to `main_guard_body`.
- Rename targets:
  - duplicate definition names
  - reserved names: `main`, `py_main`, `__pytra_main`
- `FunctionDef` / `ClassDef` include both `name` (renamed) and `original_name`.
- `for ... in range(...)` is normalized to `ForRange`, preserving `start/stop/step/range_mode`.
- `range(...)` is lowered into dedicated EAST representation during EAST construction; raw `Call(Name("range"), ...)` is never passed to downstream emitters.
  - Therefore downstream emitters (including `py2cpp.py`) do not interpret Python `range` semantics directly; they only process normalized EAST nodes.
- `range(...)` outside `for` loops is lowered to `RangeExpr` (including inside `ListComp`).

## 5. Common Node Attributes

Expression nodes (`_expr`) include:

- `kind`, `source_span`, `resolved_type`, `borrow_kind`, `casts`, `repr`
- `resolved_type` is the inferred type string.
- `borrow_kind` is `value | readonly_ref | mutable_ref` (`move` currently unused).
- Major expressions include structured child nodes (`left/right`, `args`, `elements`, `entries`, etc.).

Function nodes include:

- `arg_types`, `return_type`, `arg_usage`, `renamed_symbols`

### 5.1 C++ Pass-through Notation via `leading_trivia`

- EAST stores pass-through directives in existing `leading_trivia` (`kind: "comment"`) without introducing new node kinds.
- Supported directives:
  - `# Pytra::cpp <C++ line>`
  - `# Pytra::cpp: <C++ line>`
  - `# Pytra::pass <C++ line>`
  - `# Pytra::pass: <C++ line>`
  - `# Pytra::cpp begin` ... `# Pytra::cpp end`
  - `# Pytra::pass begin` ... `# Pytra::pass end`
- Output rules (C++ emitter):
  - Directive comments are emitted as raw C++ lines, not converted into normal comments (`// ...`).
  - Inside `begin/end` blocks, normal comments are emitted in order as C++ lines after removing leading `#`.
  - Output position is immediately before the statement carrying that `leading_trivia`, matching the statement indentation.
  - `blank` trivia remains blank lines.
  - Multiple directives in one `leading_trivia` are concatenated in source order.
- Priority:
  - Directive interpretation in `leading_trivia` has highest priority.
  - Existing docstring-to-comment conversion (`"""...""" -> /* ... */`) is independent and not overridden.

## 6. Type System

### 6.1 Canonical Types

- Integer types: `int8`, `uint8`, `int16`, `uint16`, `int32`, `uint32`, `int64`, `uint64`
- Floating-point types: `float32`, `float64`
- Primitive types: `bool`, `str`, `None`
- Composite types: `list[T]`, `set[T]`, `dict[K,V]`, `tuple[T1,...]`
- Extended types: `Path`, `Exception`, class names
- Helper/meta types: `unknown`, `module`, `callable[float64]`

### 6.2 Annotation Normalization

- `int` normalizes to `int64`.
- `float` normalizes to `float64`.
- `byte` normalizes to `uint8` (annotation alias for one-char/one-byte use).
- `float32` / `float64` are preserved.
- `any` / `object` are treated as equivalent to `Any`.
- For concrete C++ runtime representation (`object`, `None`, boxing/unboxing), see the `Any` / `object` representation policy in [Runtime Specification](./spec-runtime.md).
- `bytes` / `bytearray` normalize to `list[uint8]`.
- `pathlib.Path` normalizes to `Path`.
- C++ runtime `str` / `list` / `dict` / `set` / `bytes` / `bytearray` are implemented as wrappers (composition), not STL inheritance.

## 7. Type Inference Rules

- `Name`: resolved from type environment; unresolved name raises `inference_failure`.
- `Constant`:
  - integer literal -> `int64`
  - floating literal -> `float64`
  - boolean -> `bool`
  - string -> `str`
  - `None`
- `List/Set/Dict`:
  - non-empty: inferred by element type unification
  - empty: usually `inference_failure`
  - exception: annotated empty containers in `AnnAssign` use annotation type
- `Tuple`: becomes `tuple[...]`.
- `BinOp`:
  - numeric operators `+ - * % // /`
  - mixed numerics perform promotion (including `float32/float64`) with `casts`
  - `Path / str` -> `Path`
  - supports `str * int` and `list[T] * int`
  - bit operations `& | ^ << >>` infer integer types
  - note: `%` Python/C++ semantic difference is not absorbed in EAST
  - EAST preserves `%` as operator; generator switches by `--mod-mode` (`native` / `python`)
- `Subscript`:
  - `list[T][i] -> T`
  - `dict[K,V][k] -> V`
  - `str[i] -> str`
  - `list/str` slice keeps same container type
  - EAST keeps `Subscript` / `Slice`; generator applies `str-index-mode` / `str-slice-mode`
  - current C++ generator implements `byte` / `native`; `codepoint` not implemented
- `Call`:
  - known: `int`, `float`, `bool`, `str`, `bytes`, `bytearray`, `len`, `range`, `min`, `max`, `round`, `print`, `write_rgb_png`, `save_gif`, `grayscale_palette`, `perf_counter`, `Path`, `Exception`, `RuntimeError`
  - `float(...)`, `round(...)`, `perf_counter()`, and major `math.*` functions infer `float64`
  - `bytes(...)` / `bytearray(...)` infer `list[uint8]`
  - class constructors/methods infer from pre-collected class type info
- `ListComp`: only single-generator form is supported.
- `BoolOp` (`or` / `and`) is preserved as `kind: BoolOp` in EAST.
  - When expected type is `bool`, C++ emits boolean ops (`&&` / `||`).
  - Otherwise it emits Python-style value-selection form:
    - `a or b` -> `truthy(a) ? a : b`
    - `a and b` -> `truthy(a) ? b : a`
  - Selection logic is handled by `src/py2cpp.py`; EAST does not lower this into new nodes.

About `range`:

- Even if input AST contains `Call(Name("range"), ...)`, final EAST converts it into dedicated nodes (`ForRange` / `RangeExpr`, etc.) and does not keep direct `Call` forms.
- Leaving `range` as raw call in EAST is treated as an EAST construction defect; downstream layers do not perform implicit rescue.

About `lowered_kind: BuiltinCall`:

- EAST attaches `runtime_call` to reduce downstream branching.
- Implemented major `runtime_call` examples:
  - `py_print`, `py_len`, `py_to_string`, `static_cast`
  - `py_min`, `py_max`, `perf_counter`
  - `list.append`, `list.extend`, `list.pop`, `list.clear`, `list.reverse`, `list.sort`
  - `set.add`, `set.discard`, `set.remove`, `set.clear`
  - `write_rgb_png`, `save_gif`, `grayscale_palette`
  - `py_isdigit`, `py_isalpha`

For `.get(...).items()` on `dict[str, Any]`:

- C++ generation assumes `dict[str, object]` and recursively converts `Dict`/`List` literal values via `make_object(...)` at initialization.
- When `.get(..., {})` supplies dict default values, it is normalized and handled as `dict[str, object]`.

## 8. Cast Specification

`casts` are emitted during numeric promotion.

```json
{
  "on": "left | right | body | orelse",
  "from": "int64",
  "to": "float32 | float64",
  "reason": "numeric_promotion | ifexp_numeric_promotion"
}
```

## 9. Argument Reassignment Classification (`arg_usage`)

`FunctionDef` attaches `arg_usage`.

- Values are `readonly | reassigned`.
- `reassigned` when:
  - argument name is assigned/aug-assigned (`Assign` / `AnnAssign` / `AugAssign`)
  - argument name appears in `Swap` left/right targets
  - argument name is a `for` / `for range` loop target
  - `except ... as name` binds to an argument name
- Assignments inside nested `FunctionDef` / `ClassDef` are excluded from outer-function classification.
- all other cases are `readonly`

Currently this metadata is used mainly for backend argument `mut` decisions.

## 10. Supported Statements

- `FunctionDef`, `ClassDef`, `Return`
- `Assign`, `AnnAssign`, `AugAssign`
- `Expr`, `If`, `For`, `ForRange`, `While`, `Try`, `Raise`
- `Import`, `ImportFrom`, `Pass`, `Break`, `Continue`

Notes:
- `Assign` currently supports single-target statement form.
- Tuple assignment is supported (examples: `x, y = ...`, `a[i], a[j] = ...`).
- For name targets, type environment is updated when RHS tuple type is known.
- `from module import *` (wildcard import) is unsupported.

## 11. Pre-collection of Class Info

Before generation, collect:

- class names
- simple inheritance relations
- method return types
- field types (`AnnAssign` in class body / assignment analysis in `__init__`)

## 12. Error Contract

`EastBuildError` has `kind`, `message`, `source_span`, and `hint`.

- `inference_failure`
- `unsupported_syntax`
- `semantic_conflict`

`SyntaxError` is converted into the same schema.

## 13. Human-readable View

- `--human-output` emits C++-style pseudo source.
- Goal is reviewability; strict C++ compilability is not guaranteed.
- It visualizes EAST fields such as `source_span`, `resolved_type`, `ForRange`, and `renamed_symbols`.

## 14. Known Limitations

- Not full Python syntax coverage (Pytra subset).
- Advanced dataflow analysis (strict alias/effect propagation) is not implemented.
- `borrow_kind=move` is currently unused.

## 15. Verification Status

- `test/fixtures`: 32/32 convertible by `src/pytra/compiler/east.py` (`ok: true`)
- `sample/py`: 16/16 convertible by `src/pytra/compiler/east.py` (`ok: true`)
- `sample/py`: 16/16 pass "convert -> compile -> run" via `src/py2cpp.py` (`ok`)

## 16. Phased Rollout Plan (EAST Migration)

- Phase 1: implement EAST generator first and centralize type resolution, rename, and cast materialization in EAST.
- Phase 2: each backend gradually reduces direct AST dependency and migrates to EAST input.
- Phase 3: retire direct-AST paths and operate EAST as the sole intermediate representation.

Notes:
- Progress tracking per phase is maintained in `docs/todo/index.md`.
- Detailed implementation split (emitter/profile/hooks) follows `docs/spec/spec-dev.md`.

## 17. Acceptance Criteria for EAST Adoption

- Existing `test/fixtures` must be convertible through EAST path.
- On inference failure, error must include `kind` / `source_span` / `hint`.
- Spec differences must be documented; downstream emitters must not perform implicit rescue (example: never leave raw `range` calls).
- For common runtime cases (`math`, `pathlib`, etc.), semantic consistency across languages must be preserved.

## 18. Future Extensions (Policy)

- Current `borrow_kind` values in use are `value | readonly_ref | mutable_ref`; `move` remains unused.
- Future Rust-oriented reference annotations (`&` / `&mut` equivalents) can be connected to this representation.
  - Final Rust-specific decisions (ownership/lifetime details) remain backend responsibility.
