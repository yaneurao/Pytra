<a href="../../../ja/plans/archive/20260314-p1-nes3-bus-port-pkg-cpp-support.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: align header/symbol qualification and parameter passing for imported bus types with the C++ multi-file contract

Last updated: 2026-03-14

Related TODO:
- `docs/ja/todo/index.md` `ID: P1-NES3-BUS-PORT-PKG-CPP-01`
- Dependency: `ID: P1-NES3-NOT-IMPLEMENTED-ERROR-CPP-01` (shared `NotImplementedError` residual)

Background:
- The Pytra-NES3 repro [`materials/refs/from-Pytra-NES3/bus_port_pkg/`](../../../materials/refs/from-Pytra-NES3/bus_port_pkg) uses a bus interface/type imported from another module in both headers and implementation files.
- As of 2026-03-13, the generated `cpu.h` uses `pytra_mod_bus_port::BusPort` without making the declaration visible, and `bus.cpp` passes `rc<RAMBus>` into `BusPort&`, which does not compile.
- The fixture also carries the shared `NotImplementedError` residual, but the main target of this task is the cross-module user-type header visibility and parameter-passing contract.

Objective:
- Make imported bus types visible from both headers and implementation files in the C++ multi-file lane.
- Align the base/derived bus passing lane with the representative ownership contract so the `bus_port_pkg` compile blocker is removed.

In scope:
- Header includes, forward declarations, and symbol qualification for imported user types
- Parameter passing and call-site lowering for base/derived bus types
- Multi-file compile smoke for `materials/refs/from-Pytra-NES3/bus_port_pkg/`
- Regression, docs, and TODO sync for the bus-port residual

Out of scope:
- The exception-lowering implementation itself
- A redesign of the overall ownership model
- Non-C++ backends

Acceptance criteria:
- The generated C++ for `bus_port_pkg` compiles.
- Headers such as `cpu.h` declare or include imported bus types before use sites.
- The `RAMBus` to `BusPort` passing lane follows the representative C++ ownership contract.

Validation commands (planned):
- `python3 tools/check_todo_priority.py`
- `bash ./pytra materials/refs/from-Pytra-NES3/bus_port_pkg/bus.py --target cpp --output-dir /tmp/pytra_nes3_bus_port_pkg`
- `for f in /tmp/pytra_nes3_bus_port_pkg/src/*.cpp; do g++ -std=c++20 -O0 -c "$f" -I /tmp/pytra_nes3_bus_port_pkg/include -I /workspace/Pytra/src -I /workspace/Pytra/src/runtime/cpp; done`
- `git diff --check`

## Breakdown

- [x] [ID: P1-NES3-BUS-PORT-PKG-CPP-01-S1-01] Locked the current compile failure and cross-module bus-type residual in focused regressions, the plan, and TODO.
- [x] [ID: P1-NES3-BUS-PORT-PKG-CPP-01-S2-01] Fixed header visibility and symbol qualification for imported bus types to match the C++ multi-file contract.
- [x] [ID: P1-NES3-BUS-PORT-PKG-CPP-01-S2-02] Aligned the base/derived bus passing lane with the representative ownership contract.
- [x] [ID: P1-NES3-BUS-PORT-PKG-CPP-01-S3-01] Synced compile smoke and docs wording to the current contract with the shared-residual dependency recorded.

Decision log:
- 2026-03-13: Opened as a separate P1 with an explicit dependency on the `NotImplementedError` task so the shared exception residual and the cross-module bus-type residual can be tracked independently.
- 2026-03-14: Made the header builder pull `py_runtime.h` for headers with class blocks so imported interface headers that use `PYTRA_DECLARE_CLASS_TYPE` and `PYTRA_TID_OBJECT` pass self-contained compile checks.
- 2026-03-14: Aligned imported user-class doc resolution, base qualification, ref-class parameter normalization to `const rc<Base>&`, handle-passing call-site lowering, and virtual/non-const propagation, then locked the `cpu.h` / `bus.h` / `bus_port.h` header compile plus `bus_port.cpp` / `cpu.cpp` / `bus.cpp` compile coverage in the focused regression.
