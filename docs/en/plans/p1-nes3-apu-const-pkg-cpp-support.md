# P1: align header ordering and reference lanes for imported classes that use module constants

Last updated: 2026-03-13

Related TODO:
- `docs/ja/todo/index.md` `ID: P1-NES3-APU-CONST-PKG-CPP-01`

Background:
- The Pytra-NES3 repro [`materials/refs/from-Pytra-NES3/apu_const_pkg/`](../../../materials/refs/from-Pytra-NES3/apu_const_pkg) imports a class from `.apu` whose methods reference module constants.
- As of 2026-03-13, the generated `apu.h` emits the inline method bodies before the module-constant declarations such as `LENGTH_TABLE`, `CPU_CLOCK_HZ`, and `PULSE_GAIN`, so the header fails with undeclared-name errors.
- This fixture exposes a declaration-order residual in the shared header contract when imported classes and module constants live together.

Objective:
- Make imported classes that reference module constants compile under the C++ multi-file header contract.
- Lock `apu_const_pkg` as representative compile smoke for this header-ordering lane.

In scope:
- Declaration order for module constants and imported-class header emission
- Multi-file compile smoke for `materials/refs/from-Pytra-NES3/apu_const_pkg/`
- Regression, docs, and TODO sync for the header-order residual

Out of scope:
- A redesign of all module globals
- Non-C++ backends
- Optimizing the APU implementation itself

Acceptance criteria:
- The generated C++ for `apu_const_pkg` compiles.
- `apu.h` declares the needed module constants before any use sites that reference them.
- The representative header contract for imported classes plus module constants is recorded in regressions and the plan.

Validation commands (planned):
- `python3 tools/check_todo_priority.py`
- `bash ./pytra materials/refs/from-Pytra-NES3/apu_const_pkg/user.py --target cpp --output-dir /tmp/pytra_nes3_apu_const_pkg`
- `for f in /tmp/pytra_nes3_apu_const_pkg/src/*.cpp; do g++ -std=c++20 -O0 -c "$f" -I /tmp/pytra_nes3_apu_const_pkg/include -I /workspace/Pytra/src -I /workspace/Pytra/src/runtime/cpp; done`
- `git diff --check`

## Breakdown

- [ ] [ID: P1-NES3-APU-CONST-PKG-CPP-01-S1-01] Lock the current header-side compile failure and declaration-order residual in focused regressions, the plan, and TODO.
- [ ] [ID: P1-NES3-APU-CONST-PKG-CPP-01-S2-01] Fix declaration ordering so module constants referenced by imported classes satisfy the C++ header contract.
- [ ] [ID: P1-NES3-APU-CONST-PKG-CPP-01-S3-01] Sync multi-file compile smoke and docs wording to the current contract.

Decision log:
- 2026-03-13: Opened independently because the Pytra-NES3 repro isolates a header-order residual between imported classes and module constants.
