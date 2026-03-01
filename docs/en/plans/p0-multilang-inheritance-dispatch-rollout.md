# P0: Non-C++ Inheritance Method Dynamic Dispatch Improvement

Last updated: 2026-03-01

Related TODO:
- `ID: P0-MULTILANG-INHERIT-DISPATCH-01` in `docs/ja/todo/index.md`

Background:
- The C++ backend preserves dynamic dispatch through base references, assuming `virtual/override` and `super()` lowering.
- In non-C++ backends, even when inheritance representation exists, some languages still have incomplete Python-compatible dynamic dispatch.
- For regression detection, we added `test/fixtures/oop/inheritance_virtual_dispatch_multilang.py` and pinned expected values.

Goal:
- Align inheritance method calls and `super()` semantics to Python compatibility across non-C++ backends (`cs/go/java/js/ts/kotlin/swift/rs/ruby/lua`).

In scope:
- fixture: `test/fixtures/oop/inheritance_virtual_dispatch_multilang.py`
- backends: `src/hooks/{cs,go,java,js,ts,kotlin,swift,rs,ruby,lua}/emitter/*`
- verification: `tools/runtime_parity_check.py` / `test/unit/test_py2*_smoke.py`

Out of scope:
- Redesigning the C++ backend
- Introducing multiple inheritance (Pytra is single inheritance)

Acceptance criteria:
- The added fixture is transpileable on each backend.
- On runnable backends, parity matches `loud-dog / loud-dog`.
- Per-backend design differences are recorded in language-specific plans and traceable via TODO child IDs.

Verification commands:
- `PYTHONPATH=src python3 test/fixtures/oop/inheritance_virtual_dispatch_multilang.py`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets cpp,rs,cs,js,ts,go,java,swift,kotlin,ruby,lua`
- `python3 tools/check_todo_priority.py`

Breakdown:
- [x] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S1-01] Connect the added fixture to backend smoke/parity paths and promote it to a recurrence-detection target.
- [x] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-CS] Complete inheritance dispatch/`super()` support for C# backend.
- [x] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-GO] Complete inheritance dispatch/`super()` support for Go backend.
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-JAVA] Complete inheritance dispatch/`super()` support for Java backend.
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-JS] Complete inheritance dispatch/`super()` support for JS backend.
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-TS] Complete inheritance dispatch/`super()` support for TS backend.
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-KOTLIN] Complete inheritance dispatch/`super()` support for Kotlin backend.
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-SWIFT] Complete inheritance dispatch/`super()` support for Swift backend.
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-RS] Complete inheritance dispatch/`super()` support for Rust backend.
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-RUBY] Complete inheritance dispatch/`super()` support for Ruby backend.
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-LUA] Complete inheritance dispatch/`super()` support for Lua backend.
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S3-01] Aggregate parity/smoke results across all backends and isolate unmet blockers.

Decision log:
- 2026-03-01: Planned P0 improvement for inheritance method dynamic dispatch across non-C++ backends.
- 2026-03-01: Added `inheritance_virtual_dispatch_multilang` to default fixture cases in `tools/runtime_parity_check.py` and connected it to the regression path.
- 2026-03-01: `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_runtime_parity_check_cli.py' -v` passed (7 tests, 0 fail).
- 2026-03-01: Ran `python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets cpp,rs,cs,js,ts,go,java,swift,kotlin,ruby,lua --ignore-unstable-stdout --summary-json out/inherit_dispatch_multilang_summary.json` and pinned a pre-S2 implementation baseline (`run_failed=10`, `toolchain_missing=1`).
- 2026-03-01: Implemented C# (`S2-CS`): added `virtual/override`, `super` lowering, and assertion function mapping. Fixture parity for `--targets cs` passed (1/1).
- 2026-03-01: Implemented Go (`S2-GO`): added class interface introduction + `super` lowering. Fixture parity for `--targets go` passed (1/1).
