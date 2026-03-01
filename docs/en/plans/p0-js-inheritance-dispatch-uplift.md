# P0: Improve JavaScript inheritance-method dynamic dispatch

Last updated: 2026-03-01

Related TODO:
- `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-JS` in `docs/ja/todo/index.md`

Background:
- The JS emitter outputs classes, but lacks `extends`/`super` paths and diverges from Python inheritance semantics.

Goal:
- Reorganize JS output around `class Child extends Base` + `super(...)`.

Scope:
- `src/hooks/js/emitter/js_emitter.py`

Out of scope:
- Type-annotation extensions on the TS side

Acceptance criteria:
- Emit `extends` for inherited classes.
- `super().__init__` / `super().method` lowering works.
- Fixture parity matches.

Verification commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2js_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets js`

Breakdown:
- [ ] Introduce `extends` in class declarations.
- [ ] Add lowering for `super` calls.
- [ ] Add fixture regressions.

Decision log:
- 2026-03-01: Prioritized fixes to the core class-representation path in JS.
