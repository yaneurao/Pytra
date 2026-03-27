<a href="../../../ja/plans/archive/20260308-p1-all-target-sample-parity-rollout.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Reach Sample Parity Across All Targets

Last updated: 2026-03-08

Related TODO:
- Completed. See `ID: P1-ALLTARGET-SAMPLE-PARITY-01` in `docs/en/todo/archive/20260308.md`.

Background:
- Before this rollout, `cpp/js/ts` were green on sample parity, while many other targets were blocked by `toolchain_missing`.
- The goal was not only to remove backend regressions, but to make sample parity executable end to end for every supported target on the current machine.
- This work was intentionally separated from runtime-layout or backend-architecture changes so infrastructure gaps and backend bugs could be measured independently.

Objective:
- Make sample parity complete without `toolchain_missing` for all parity targets.
- Fix the operational definition of “all-target green.”
- Add a canonical runner so the full parity sweep can be repeated with one command.

Acceptance criteria:
- all parity targets can run sample parity without `toolchain_missing`
- each target reaches `cases=18 pass=18 fail=0`
- the canonical execution route is documented and scriptable

## Task Breakdown

- [x] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S1-01] Inventory toolchain requirements and current `toolchain_missing` status.
- [x] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S1-02] Fix the done condition and the failure categories that are not acceptable.
- [x] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S2-01] Bootstrap compiled-target toolchains (`rs/cs/go/java/kotlin/swift/scala`).
- [x] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S2-02] Bootstrap scripting/mixed target toolchains (`ruby/lua/php/nim`).
- [x] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S3-01] Reconfirm the baseline targets (`cpp/js/ts`).
- [x] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S3-02] Bring compiled targets to green.
- [x] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S3-03] Bring scripting/mixed targets to green.
- [x] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S4-01] Add a canonical all-target parity runner and document the rerun path.
- [x] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S4-02] Record the final result and archive the plan.

## Key Results

- Baseline targets `cpp/js/ts` stayed green.
- Compiled targets `rs/cs/go/java/kotlin/swift/scala` all reached `18/18`.
- Scripting/mixed targets `ruby/lua/php/nim` also reached `18/18`.
- A canonical wrapper, `tools/check_all_target_sample_parity.py`, was introduced to run the target groups in a stable order.

## Decision Log

- 2026-03-08 [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S3-02]: After toolchain bootstrap on the current Debian 12 machine, Rust runtime import compatibility was fixed and the full compiled-target family was confirmed green target by target.
- 2026-03-08 [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S3-03]: `ruby/lua/php/nim` also reached `SUMMARY cases=18 pass=18 fail=0` each, eliminating both `toolchain_missing` and backend/runtime parity gaps on the current machine.
- 2026-03-08 [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S4-01]: `tools/check_all_target_sample_parity.py` was established as the canonical all-target runner, grouping targets into `cpp`, `js_ts`, `compiled`, and `scripting_mixed`.
- 2026-03-08 [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S4-02]: The final recorded state was “14 targets green,” with baseline and grouped runs documented in `spec-tools` and `how-to-use`.
