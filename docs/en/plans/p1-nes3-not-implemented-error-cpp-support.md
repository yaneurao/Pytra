# P1: stop lowering `NotImplementedError` to an undefined C++ symbol

Last updated: 2026-03-13

Related TODO:
- `docs/ja/todo/index.md` `ID: P1-NES3-NOT-IMPLEMENTED-ERROR-CPP-01`

Background:
- The Pytra-NES3 minimal repro [`materials/refs/from-Pytra-NES3/not_implemented_error.py`](../../../materials/refs/from-Pytra-NES3/not_implemented_error.py) reproduces a C++ compile failure with only `raise NotImplementedError("todo")`.
- As of 2026-03-13, the generated C++ still emits `throw NotImplementedError(...)` directly, and the symbol is not defined on the C++ side.
- `bus_port_pkg/` also leaks the same exception symbol, so this residual is a shared blocker rather than a one-off fixture failure.

Objective:
- Align the C++ lane so Python `NotImplementedError` never lowers to a raw undefined symbol.
- Lock the behavior with regressions so both the minimal repro and shared consumer fixtures stop regressing.

In scope:
- Frontend / lowering / emitter / runtime mapping for `NotImplementedError`
- Compile smoke for `materials/refs/from-Pytra-NES3/not_implemented_error.py`
- Focused regressions, docs, and TODO sync for fixtures that hit the same residual

Out of scope:
- A full Python exception-hierarchy implementation
- Rolling out the same work to other exception classes such as `ValueError`
- Non-C++ backends

Acceptance criteria:
- The generated C++ for `not_implemented_error.py` compiles.
- No remaining lane leaves `NotImplementedError` undefined in shared repros such as `bus_port_pkg`.
- The fixed lane is recorded in regressions, the plan, and TODO.

Validation commands (planned):
- `python3 tools/check_todo_priority.py`
- `bash ./pytra materials/refs/from-Pytra-NES3/not_implemented_error.py --target cpp --output-dir /tmp/pytra_nes3_not_implemented_error`
- `g++ -std=c++20 -O0 -c /tmp/pytra_nes3_not_implemented_error/src/not_implemented_error.cpp -I /tmp/pytra_nes3_not_implemented_error/include -I /workspace/Pytra/src -I /workspace/Pytra/src/runtime/cpp`
- `git diff --check`

## Breakdown

- [ ] [ID: P1-NES3-NOT-IMPLEMENTED-ERROR-CPP-01-S1-01] Lock the current compile failure and desired C++ contract in focused regressions, the plan, and TODO.
- [ ] [ID: P1-NES3-NOT-IMPLEMENTED-ERROR-CPP-01-S2-01] Add the `NotImplementedError` lowering/runtime mapping and stop emitting the raw undefined symbol.
- [ ] [ID: P1-NES3-NOT-IMPLEMENTED-ERROR-CPP-01-S3-01] Sync compile smoke and docs for the minimal repro plus shared impact lanes.

Decision log:
- 2026-03-13: Promoted from the Pytra-NES3 bug report as a standalone P1 task so the shared residual can be tracked independently.
