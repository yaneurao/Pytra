# P0: All-Language Golden-Match Pipeline for Samples

Last updated: 2026-02-25

Related TODO:
- `ID: P0-SAMPLE-GOLDEN-ALL-01` to `P0-SAMPLE-GOLDEN-ALL-01-S8` in `docs/ja/todo/index.md`

Background:
- The 18 `sample/py` cases (`01_` to `18_`) had golden baselines, but validation was historically C++-heavy and incomplete for other targets.
- Because compile/run/golden checks were not uniformly established across languages, regression priorities were easily distorted.
- Final acceptance policy was unified to: no unfinished P0 tasks and all-language/all-case green simultaneously.

In scope:
- All `sample/py` cases (`01_mandelbrot` to `18_mini_language_interpreter`)
- Target languages: `cpp, rs, cs, js, ts, go, java, swift, kotlin`
- Compare sample output (`stdout` + artifacts) against `sample/golden/manifest.json`

Out of scope:
- Adding/removing samples
- Deep runtime refactors (separate tasks)
- README wording polish unrelated to validation diffs

Acceptance criteria:
- For each language, all 18 cases pass `compile -> run -> compare`.
- Comparison uses normalized stdout (`normalize_stdout_for_compare`) plus artifact hash/size equality.
- `tools/runtime_parity_check.py` and `tools/verify_sample_outputs.py` finish with NG=0 for executable targets.
- Remaining issues (if any) are recorded with failure category and retry conditions in this context doc.

## Execution policy

1. Preparation:
   - Fix target list from `sample/py` and `sample/golden/manifest.json`.
   - Normalize common CLI/workdir handling in `tools/runtime_parity_check.py`.
2. C++ as baseline:
   - Reconfirm full C++ 18/18 consistency first.
3. Per-language iterative repair:
   - Run `compile -> run -> compare` case-by-case.
   - Resolve same failure class with consistent rules.
4. Cross-language convergence:
   - Confirm no failed target remains.
   - Reflect results in `docs/ja/todo/index.md` and README notes (JA/EN).

## Subtasks

- `P0-SAMPLE-GOLDEN-ALL-01-S1`: Lock validation scope (18 samples, 9 languages, compare rules).
- `P0-SAMPLE-GOLDEN-ALL-01-S2`: Make runtime parity flow all-language-ready (toolchain requirements, failure taxonomy).
- `P0-SAMPLE-GOLDEN-ALL-01-S3`: Achieve full C++ 18-case compile/run/compare parity.
- `P0-SAMPLE-GOLDEN-ALL-01-S4`: Achieve full Rust 18-case compile/run/compare parity.
- `P0-SAMPLE-GOLDEN-ALL-01-S5`: Achieve full C# 18-case compile/run/compare parity.
- `P0-SAMPLE-GOLDEN-ALL-01-S6`: Achieve full JS/TS 18-case transpile/run/compare parity.
- `P0-SAMPLE-GOLDEN-ALL-01-S7`: Achieve full Go/Java/Swift/Kotlin 18-case transpile/run/compare parity.
- `P0-SAMPLE-GOLDEN-ALL-01-S8`: Reflect all-language aggregated results in `docs/ja/README.md` / `readme.md`.

## Finalized results by stage

- `S1` (2026-02-25): Scope/target/compare rules fixed; reproducible commands documented.
- `S2` (2026-02-25): `runtime_parity_check` gained case resolution + failure-category JSON summary; CLI behavior guarded with unit tests.
- `S3` (2026-02-25): C++ module resolution/runtime tuple boxing/type-id init-order fixes; `cpp` reached `cases=18 pass=18 fail=0`.
- `S4` (2026-02-25): Rust emitter fixes for call/subscript/dict/mutability and media-arg ownership; `rs` reached `cases=18 pass=18 fail=0`.
- `S5` (2026-02-25): C# emitter/runtime corrections and math runtime additions; `cs` reached `cases=18 pass=18 fail=0`.
- `S6` (2026-02-25): JS/TS emitter + runtime shim path alignment; `js,ts` reached `cases=18 pass=18 fail=0`.
- `S7` (2026-02-25): Go/Java/Swift/Kotlin aligned to sidecar-bridge execution path for parity; reached `cases=18 pass=18 fail=0` across those four targets.
- `S8` (2026-02-25): README notes (JA/EN) updated to reflect all-9-language parity completion and operational policy.

## Decision log summary

- 2026-02-25: Added as new P0 with completion defined as all-language/all-case consistency.
- 2026-02-25: Completed staged rollout S1-S8; parity completion state fixed and linked to README updates.
- Detailed command-by-command logs remain in `docs/ja/plans/p0-sample-all-languages-golden-pipeline.md`.
