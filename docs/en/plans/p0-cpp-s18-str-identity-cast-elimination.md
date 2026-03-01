# P0: Remove `str -> str` identity conversions in sample/18 (`py_to_string` collapse)

Last updated: 2026-03-01

Related TODO:
- `ID: P0-CPP-S18-STR-IDENTITY-CAST-01` in `docs/ja/todo/index.md`

Background:
- In the parser path of generated C++ for sample/18, `py_to_string(this->expect(...)->text)` remains.
- Since `text` is already `str`, this identity conversion is unnecessary and harms readability and runtime efficiency.

Goal:
- Reduce identity conversions on known-`str` paths in the C++ backend and remove unnecessary wrappers in sample/18.

Scope:
- `src/hooks/cpp/emitter/*` (cast decisions/expression emission)
- `src/pytra/compiler/east_parts/east3_opt_passes/*` (if needed)
- `test/unit/test_east3_cpp_bridge.py`
- `test/unit/test_py2cpp_codegen_issues.py`

Out of scope:
- Unsafe blanket reduction into `object/Any` paths
- Full cast-rule overhaul beyond `str`

Acceptance criteria:
- `py_to_string(...->text)` is not emitted in sample/18.
- Collapse applies only to known-`str` paths; safe conversions for `object/unknown` paths are preserved.
- Regression tests enforce fail-closed behavior and confirm no regression.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

Decision log:
- 2026-03-01: Filed as P0 for additional sample/18 optimization to reduce `str -> str` identity casts.
- 2026-03-01: Confirmed that in sample/18, assignment AST for `let_name/assign_name` uses `Unbox(target=str)`, while the `resolved_type` on the value-side `Attribute` is `unknown`, causing `py_to_string(...)` to remain.
- 2026-03-01: Added `class_method_return_types` and `class_field_types` to the C++ emitter, and strengthened type inference for `Call(Attribute)` (e.g. `self.expect(...)`) and field access from it (`Token.text`).
- 2026-03-01: Added a pass-through guard in `_render_expr_kind_unbox` for source/target identity types, collapsing `py_to_string(this->expect("IDENT")->text)` to `this->expect("IDENT")->text`.
- 2026-03-01: Added sample/18 regression coverage in `test_py2cpp_codegen_issues.py` (elide `py_to_string` for `IDENT.text`), and confirmed non-regression via `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v` (81 tests), `python3 tools/check_py2cpp_transpile.py` (`checked=134 ok=134 fail=0 skipped=6`), and `runtime_parity_check` (sample/18 cpp PASS).

## Breakdown

- [x] [ID: P0-CPP-S18-STR-IDENTITY-CAST-01] Collapse `py_to_string` identity conversions on known-`str` paths.
- [x] [ID: P0-CPP-S18-STR-IDENTITY-CAST-01-S1-01] Inventory current identity-conversion sites for `str` and lock applicability/exclusion conditions.
- [x] [ID: P0-CPP-S18-STR-IDENTITY-CAST-01-S2-01] Add collapse implementation in the emitter (and EAST3 pass if needed), while preserving `object` paths.
- [x] [ID: P0-CPP-S18-STR-IDENTITY-CAST-01-S2-02] Add sample/18 regression coverage to prevent reintroduction of unnecessary `py_to_string` emission.
- [x] [ID: P0-CPP-S18-STR-IDENTITY-CAST-01-S3-01] Confirm non-regression via transpile/unit/sample regeneration.
