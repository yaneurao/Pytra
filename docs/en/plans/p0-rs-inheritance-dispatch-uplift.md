# P0: Rust Inheritance Method Dynamic Dispatch Improvement

Last updated: 2026-03-01

Related TODO:
- `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-RS` in `docs/ja/todo/index.md`

Background:
- The Rust backend is centered on `struct + impl`, and direct support for Python inheritance/`super` is insufficient.

Goal:
- Finalize a Rust lowering strategy (trait/enum/composition) that satisfies inheritance method-call requirements.

In scope:
- `src/hooks/rs/emitter/rs_emitter.py`
- If needed: `src/runtime/rs/pytra/py_runtime.rs`

Out of scope:
- General ownership optimization for the Rust backend

Acceptance criteria:
- A policy for inheritance method dispatch is fixed in an implementable form.
- Expected output matches on the fixture.

Verification commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rs_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets rs`

Breakdown:
- [ ] Narrow inheritance emulation in Rust to one approach.
- [ ] Lower `super`-equivalent calls.
- [ ] Add fixture regression.

Decision log:
- 2026-03-01: Because Rust has multiple design options, we put approach finalization first.
