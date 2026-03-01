# P0: Improve Kotlin inheritance-method dynamic dispatch

Last updated: 2026-03-01

Related TODO:
- `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-KOTLIN` in `docs/ja/todo/index.md`

Background:
- The Kotlin emitter outputs `open class`, but lacks method-level `open/override` and `super` lowering.

Goal:
- Make inheritance-method dynamic dispatch work correctly in Kotlin.

Scope:
- `src/hooks/kotlin/emitter/kotlin_native_emitter.py`

Out of scope:
- Whole-backend optimization for Kotlin

Acceptance criteria:
- Base methods emit `open`, and derived methods emit `override`.
- `super` calls are lowered to valid calls rather than no-op.
- Fixture parity matches.

Verification commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2kotlin_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets kotlin`

Breakdown:
- [ ] Add override-relation analysis and align declaration keywords.
- [ ] Implement `super` lowering.
- [ ] Add fixture regressions.

Decision log:
- 2026-03-01: Fixed introducing `open/override` as the leading task for Kotlin.
