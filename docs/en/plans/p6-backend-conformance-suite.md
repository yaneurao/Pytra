# P6 Backend Conformance Suite

Last updated: 2026-03-12

Purpose:
- Build a shared conformance suite that validates the same feature fixtures across multiple backends instead of relying only on backend-local smoke tests.
- Tie parse / EAST / EAST3 lowering / emit / runtime parity to the same feature IDs so backend differences can be tracked consistently.
- Turn parity progress into a feature-level testing system rather than “some backend-specific smoke tests happen to pass.”

Background:
- Backend tests are still mostly target-local smoke suites, so it is hard to see how far a given feature actually works across multiple backends.
- Even if `P5` fixes the feature contract, drift will remain hard to catch early without shared fixtures and a shared harness.
- With C++-first implementation flow, unsupported or degraded behavior in other backends can still hide in the gaps between backend-local tests.
- A conformance basis is needed so a future feature × backend matrix can be driven from test evidence rather than hand-edited status notes.

Out of scope:
- Reaching full runtime parity in every backend immediately.
- Replacing all existing smoke tests at once.
- Redesigning the entire CI system.

Acceptance criteria:
- There is a defined plan for connecting feature fixtures to parse / lowering / emit / runtime parity lanes through a shared harness.
- Representative backend lanes (initially C++ / Rust / C# and similar) are selected.
- A strategy exists for comparing representative `pytra.std.*` runtime behavior across backends.
- There is a defined handoff from conformance results into support-matrix/docs/tooling layers.
- The `docs/en/` mirror matches the Japanese source plan.

## Child tasks

- [ ] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S1-01] Fix the mapping rule between feature IDs and fixture paths, and classify representative syntax / builtin / `pytra.std.*` cases.
- [ ] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S2-01] Design how parse / EAST / EAST3 lowering / emit / runtime parity lanes connect into a shared harness.
- [ ] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S2-02] Define a backend-selectable conformance runner, starting with representative lanes such as C++ / Rust / C#.
- [ ] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S3-01] Fix the runtime parity strategy for representative `pytra.std.*` modules such as `json`, `pathlib`, `enum`, and `argparse`.
- [ ] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S4-01] Define how conformance summaries flow into support matrices, docs, and tooling.

## Decision log

- 2026-03-12: The conformance suite follows the `P5` feature contract, so it is placed at `P6` instead of trying to build a matrix before the contract exists.
- 2026-03-12: Existing smoke tests are not dropped immediately; shared conformance is introduced incrementally through representative lanes.
