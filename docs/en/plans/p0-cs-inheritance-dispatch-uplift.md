# P0: Improve C# inheritance-method dynamic dispatch

Last updated: 2026-03-01

Related TODO:
- `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-CS` in `docs/ja/todo/index.md`

Background:
- `CSharpEmitter` emits class inheritance, but lacks method `virtual/override` and lowering for `super()` calls.

Goal:
- Make Python-equivalent dynamic dispatch work for method calls via base-type references.

Scope:
- `src/hooks/cs/emitter/cs_emitter.py`
- `test/fixtures/oop/inheritance_virtual_dispatch_multilang.py`

Out of scope:
- Full completion of C# selfhost

Acceptance criteria:
- `virtual` is emitted on base methods, and `override` is emitted on derived overrides.
- `super().method(...)` / `super().__init__(...)` are lowered into valid C# syntax.
- Fixture parity matches.

Verification commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets cs`

Breakdown:
- [x] Pre-analyze base-method override relations and add `virtual/override` to method declarations.
- [x] Lower `super()` calls to `base` calls.
- [x] Add transpile + parity regression for fixtures.

Decision log:
- 2026-03-01: Created a dedicated plan for C# as one of the highest-priority targets.
- 2026-03-01: Added inheritance-method analysis (`class_method_map` / `class_children_map`) to `CSharpEmitter`, so methods with base definitions get `override`, and methods with derived redefinitions get `virtual`.
- 2026-03-01: Added lowering from `super().method(...)` to `base.method(...)`, and from `super().__init__(...)` to constructor initializer `: base(...)`.
- 2026-03-01: Added minimal C# mappings for `py_assert_stdout` / `py_assert_eq` / `py_assert_true` / `py_assert_all`, resolving fixture compile blockers.
- 2026-03-01: `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v` passed (46 tests, 0 fail).
- 2026-03-01: `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets cs --ignore-unstable-stdout` passed (1/1).
