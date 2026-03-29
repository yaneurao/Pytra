<a href="../../../ja/plans/archive/20260308-p4-noncpp-backend-recovery-after-linked-program.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P4: Recover Non-C++ Backends After Linked-Program Introduction

Last updated: 2026-03-08

Related TODO:
- Completed. See `ID: P4-NONCPP-BACKEND-RECOVERY-01` in `docs/en/todo/archive/20260308.md`.

Background:
- After linked-program support was introduced, the main risk was leaving non-C++ backends broken while C++ moved forward.
- The fix was not to redesign all backends at once, but to stabilize a shared compatibility contract and then recover backends by family.

Objective:
- Bring non-C++ backends onto the linked-program-era contract without requiring every target to implement full multi-file writing.
- Stabilize them around `SingleFileProgramWriter`-style compatibility.
- Track progress by failure category and target family rather than by anecdotal status.

Acceptance criteria:
- backend health can be checked by family with one command
- wave-by-wave static-contract, smoke, transpile, and parity regressions are closed
- non-C++ health checks are wired into local CI
- documentation reflects the post-linked-program operational model

## Task Breakdown

- [x] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S1-01] Build a health matrix after linked-program introduction.
- [x] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S1-02] Fix the done condition and recovery order.
- [x] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S2-01] Fill common contract gaps around `backend_registry.py`, `py2x.py`, and `ir2lang.py`.
- [x] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S2-02] Add a non-C++ backend health checker.
- [x] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S3-01] Recover Wave 1 (`rs/cs/js/ts`).
- [x] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S3-02] Refresh the Wave 1 parity baseline.
- [x] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S4-01] Recover Wave 2 (`go/java/kotlin/swift/scala`).
- [x] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S4-02] Refresh the Wave 2 parity baseline.
- [x] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S5-01] Recover Wave 3 (`ruby/lua/php/nim`).
- [x] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S5-02] Refresh the Wave 3 parity baseline.
- [x] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S6-01] Integrate non-C++ health checks into local CI.
- [x] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S6-02] Sync docs and close the plan.

## Recovery Waves

### Wave 1

- `rs`, `cs`, `js`, `ts`
- goal: stabilize the first representative family and separate runtime/backend bugs from infrastructure gaps

### Wave 2

- `go`, `java`, `kotlin`, `swift`, `scala`
- goal: fix path/import/runtime smoke and transpile regressions in the larger compiled-target family

### Wave 3

- `ruby`, `lua`, `php`, `nim`
- goal: fix remaining dynamic-language and scripting-target regressions

## Decision Log

- 2026-03-08 [ID: P4-NONCPP-BACKEND-RECOVERY-01-S2-02]: A canonical health checker was added so non-C++ backend status could be measured by family and stage rather than by ad hoc command sets.
- 2026-03-08 [ID: P4-NONCPP-BACKEND-RECOVERY-01-S3-01]: Rust’s representative post-linked-program regression around return-context rendering was fixed, and Wave 1 reached a stable green contract baseline.
- 2026-03-08 [ID: P4-NONCPP-BACKEND-RECOVERY-01-S4-01]: Wave 2’s main failures were reduced to path-constructor source-origin metadata and `src.*` import path issues, which were then fixed target by target.
- 2026-03-08 [ID: P4-NONCPP-BACKEND-RECOVERY-01-S5-01]: Wave 3 mainly required import-path cleanup for `ruby/php/nim` and stale smoke expectations for `lua`.
- 2026-03-08 [ID: P4-NONCPP-BACKEND-RECOVERY-01-S6-01]: Local CI was updated to run `tools/check/check_noncpp_backend_health.py --family all --skip-parity`.
- 2026-03-08 [ID: P4-NONCPP-BACKEND-RECOVERY-01-S6-02]: Specs and how-to-use docs were synchronized to the new non-C++ backend recovery workflow.
