# P0: TypeScript Inheritance Method Dynamic Dispatch Improvement

Last updated: 2026-03-01

Related TODO:
- `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-TS` in `docs/ja/todo/index.md`

Background:
- The TS backend currently delegates to the JS emitter, so inheritance/`super` quality depends on the JS side.

Goal:
- Satisfy inheritance-dispatch requirements in TS output as well, and reduce preview dependency.

In scope:
- `src/hooks/ts/emitter/ts_emitter.py`
- `src/hooks/js/emitter/js_emitter.py` if needed

Out of scope:
- Full migration to a fully native TS emitter

Acceptance criteria:
- `extends` / `super` paths are active in TS output.
- Fixture parity matches.

Verification commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2ts_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets ts`

Breakdown:
- [ ] Introduce minimal fixes on the JS delegation path to satisfy inheritance-dispatch requirements.
- [ ] Pin TS-output-specific breakages (syntax/types) with regressions.
- [ ] Confirm fixture parity.

Decision log:
- 2026-03-01: Fixed policy to follow JS-side fixes for TS while separating TS-specific issues.
