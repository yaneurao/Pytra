# P0: Improve Java inheritance-method dynamic dispatch

Last updated: 2026-03-01

Related TODO:
- `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-JAVA` in `docs/ja/todo/index.md`

Background:
- Java has the foundation with `extends` and virtual methods, but `super()` lowering and regression lock-in are insufficient.

Goal:
- Stably pass fixture-required `super()` + base-reference call behavior.

Scope:
- `src/hooks/java/emitter/java_native_emitter.py`

Out of scope:
- General Java backend optimization

Acceptance criteria:
- `super().__init__` / `super().method` lowering is consistently effective.
- Fixture parity matches.

Verification commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2java_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets java`

Breakdown:
- [ ] Organize `super` lowering conditions and verify method paths beyond `__init__`.
- [ ] Add regression tests for fixture fragments.
- [ ] Confirm expected-output match in parity.

Decision log:
- 2026-03-01: Fixed policy to strengthen regression lock-in while using existing Java foundations.
