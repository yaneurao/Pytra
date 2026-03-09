# P4: Canonicalize Backend Registry Metadata and Strengthen Selfhost Parity Gates

Last updated: 2026-03-09

Related TODO:
- `ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01` in `docs/ja/todo/index.md`

Background:
- The host-side `toolchain/compiler/backend_registry.py` and the selfhost/static `toolchain/compiler/backend_registry_static.py` still duplicate a large amount of backend spec, runtime-copy, emitter-wiring, and option-schema logic.
- That duplication was useful during bootstrap, but it now makes backend-surface updates drift-prone because one side can be updated without the other.
- Selfhost verification tools already exist: `build_selfhost.py`, `build_selfhost_stage2.py`, `verify_selfhost_end_to_end.py`, `check_multilang_selfhost_suite.py`, and related scripts. But operationally they still behave more like auxiliary reports than stable gates for compiler-internal changes.
- The current selfhost path also mixes direct routes, host-Python bridges, preview lanes, and known blocks, so it is often unclear which failures are expected and which are true regressions.
- Even if P2/P3 improve typed boundaries and compiler contracts, host-vs-selfhost divergence will reappear unless backend-registry ownership and selfhost parity gates are hardened too.

Goal:
- Establish one source of truth for backend spec, runtime-copy rules, layer option schema, and writer metadata, and reduce drift between host and selfhost/static registries.
- Turn selfhost parity from "useful information" into a practical non-regression gate for compiler-internal work.
- Classify stage1 / stage2 / direct-route / multilang selfhost failures so expected blocks and real regressions are easy to distinguish.

Scope:
- `toolchain/compiler/backend_registry.py`
- `toolchain/compiler/backend_registry_static.py`
- Shared backend spec / runtime-copy / option-schema / writer metadata
- `tools/build_selfhost.py` / `build_selfhost_stage2.py` / `verify_selfhost_end_to_end.py`
- `tools/check_multilang_selfhost_stage1.py` / `check_multilang_selfhost_multistage.py` / `check_multilang_selfhost_suite.py`
- Selfhost parity docs / reports / guards

Out of scope:
- Typed-carrier design itself
- Fully removing the host-Python bridge
- Forcing every backend to succeed at multistage selfhost immediately
- Adding new backend language features
- A full runtime redesign

Dependencies:
- The boundary-ownership policy from `P2-COMPILER-TYPED-BOUNDARY-01` must be fixed
- The validator/diagnostic policy from `P3-COMPILER-CONTRACT-HARDENING-01` should exist at least for representative lanes

## Mandatory Rules

These are requirements, not recommendations.

1. Backend capability, runtime-copy, option-schema, and writer-rule metadata must have exactly one source of truth. Host/static manual duplication is not acceptable as the canonical design.
2. If host and selfhost/static registries behave differently, each difference must be identified as either intentional or drift. Hidden divergence is not allowed.
3. Selfhost parity failures must be categorized explicitly (`known_block`, `not_implemented`, `regression`, etc.). Vague preview text alone is not enough.
4. Representative stage1 / stage2 / direct-route / multilang selfhost gates must be runnable as part of routine compiler-internal regression checks.
5. Unsupported targets and unsupported modes should report the same diagnostic category in registry code and parity reports.
6. Any runtime-copy-list or backend-spec update must update both the shared source of truth and the parity/reporting side.
7. Selfhost parity does not need to mean "every backend passes everything," but it must always distinguish expected blocks from regressions.

Acceptance criteria:
- Backend spec / runtime-copy / option-schema / writer metadata is shared, and hand-written duplication between host/static registries is reduced.
- A drift guard or diff test exists to catch one-sided backend-registry updates.
- The selfhost parity suite reports representative stage1 / stage2 / direct e2e / multilang lanes with stable failure categories.
- For representative compiler changes, it is possible to tell which selfhost failures are known blocks and which are regressions.
- Docs / reports / archive make selfhost readiness and known blocks traceable.

Planned verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 tools/build_selfhost.py`
- `python3 tools/build_selfhost_stage2.py --skip-stage1-build`
- `python3 tools/verify_selfhost_end_to_end.py --skip-build`
- `python3 tools/check_multilang_selfhost_suite.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_*selfhost*.py'`
- `git diff --check`

## Implementation Order

Keep the order fixed: inventory drift sources first, fix the canonical source of truth second, then strengthen the parity gates.

1. Inventory registry drift and parity blind spots
2. Fix canonical backend spec / runtime metadata
3. Share host/static registry ownership
4. Strengthen selfhost parity gates / reports / failure categories
5. Refresh docs / archive / migration notes

## Breakdown

- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-01] Inventory duplicated surfaces across `backend_registry.py` and `backend_registry_static.py` (backend spec, runtime copy, writer rules, option schema, direct-route behavior), then classify each difference as intentional or drift-prone.
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-02] Inventory current gates and blind spots across `build_selfhost`, stage2, direct e2e verification, and multilang selfhost tools, then fix the known-block vs regression classification policy in the decision log.
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-01] Define the canonical source of truth for backend capability, runtime-copy rules, option schema, and writer metadata so both host and static registries can be derived from it.
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-02] Fix the boundaries where intentional differences are allowed (for example host-only lazy imports or selfhost-only direct routes) together with their diagnostic contracts.
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S3-01] Move host/static registries toward shared metadata, a generator, or equivalent adapters and retire avoidable hand-written duplication.
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S3-02] Add a registry-drift guard or diff test so one-sided backend-surface updates fail fast.
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S4-01] Reorganize representative stage1 / stage2 / direct e2e / multilang selfhost parity suites so they report a stable shared summary and failure taxonomy.
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S4-02] Align unsupported / preview / known-block / regression diagnostics between registry code and parity reports so expected failures are explicitly managed.
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S5-01] Refresh docs / plan reports / archive so backend readiness, known blocks, and gate execution flow remain traceable.
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S5-02] Verify that representative internal changes are checked through equivalent contracts on both host and selfhost lanes, then fix reintroduction guards.

## Expected Deliverables

### Deliverables for S1

- An inventory of host/static registry drift candidates
- An inventory of selfhost parity blind spots

### Deliverables for S2

- A design for the backend-registry source of truth
- A contract for intentional differences and their diagnostics

### Deliverables for S3

- Shared metadata / generator / adapters
- A drift guard

### Deliverables for S4

- Unified selfhost parity categories
- Representative gates for stage1 / stage2 / direct-route / multilang lanes

### Deliverables for S5

- Docs/reports that track readiness and known blocks
- Reintroduction guards against host/selfhost divergence

Decision log:
- 2026-03-09: Added this P4 in response to the user request to keep improving the compiler internals after the type/carrier work.
- 2026-03-09: Fixed the scope of this P4 to backend-registry source-of-truth cleanup and selfhost non-regression gates, not new backend language features.
- 2026-03-09: Fixed the policy that host/selfhost differences are not banned outright, but must always be classified as intentional differences or drift and tracked through guards/reports.
