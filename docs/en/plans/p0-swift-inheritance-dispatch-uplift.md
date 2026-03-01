# P0: Swift Inheritance Method Dynamic Dispatch Improvement

Last updated: 2026-03-01

Related TODO:
- `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-SWIFT` in `docs/ja/todo/index.md`

Background:
- In the Swift emitter, default `final class` and `super` no-op are blocking factors for inheritance behavior.

Goal:
- Introduce inheritable class declarations and `override`/`super` paths.

In scope:
- `src/hooks/swift/emitter/swift_native_emitter.py`

Out of scope:
- General type optimization for the Swift backend

Acceptance criteria:
- Remove `final` from classes that are inheritance targets, and attach `override` where needed.
- Enable `super.init` / `super.method` lowering.
- Fixture parity matches.

Verification commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2swift_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets swift`

Breakdown:
- [ ] Design inheritance support for class/function declarations (`final/override`).
- [ ] Implement `super` lowering.
- [ ] Add fixture regression.

Decision log:
- 2026-03-01: Created the plan with the premise that Swift default `final` behavior must be revised.
