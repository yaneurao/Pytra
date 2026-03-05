# TODO (Open)

> `docs/ja/` is the source of truth. `docs/en/` is its translation.

<a href="../../ja/todo/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

Last updated: 2026-03-04

## Context Operation Rules

- Every task must include an `ID` and a context file (`docs/ja/plans/*.md`).
- To override priority, issue chat instructions in the format of `docs/ja/plans/instruction-template.md`; do not use `todo2.md`.
- The active target is fixed to the highest-priority unfinished ID (smallest `P<number>`, and the first one from the top when priorities are equal); do not move to lower priorities unless there is an explicit override instruction.
- If even one `P0` remains unfinished, do not start `P1` or lower.
- Before starting, check `Background` / `Out of scope` / `Acceptance criteria` in the context file.
- Progress memos and commit messages must include the same `ID` (example: `[ID: P0-XXX-01] ...`).
- Keep progress memos in `docs/ja/todo/index.md` to a one-line summary only; details (decisions and verification logs) must be recorded in the `Decision log` of the context file (`docs/ja/plans/*.md`).
- If one `ID` is too large, you may split it into child tasks in `-S1` / `-S2` format in the context file (keep the parent checkbox open until the parent `ID` is completed).
- If uncommitted changes remain due to interruptions, do not start a different `ID` until you complete the same `ID` or revert the diff.
- When updating `docs/ja/todo/index.md` or `docs/ja/plans/*.md`, run `python3 tools/check_todo_priority.py` and verify that each progress `ID` added in the diff matches the highest-priority unfinished `ID` (or its child `ID`).
- Append in-progress decisions to the context file `Decision log`.
- For temporary output, use existing `out/` (or `/tmp` only when necessary), and do not add new temporary folders under the repository root.

## Notes

- This file keeps unfinished tasks only.
- Completed tasks are moved to history via `docs/ja/todo/archive/index.md`.
- `docs/ja/todo/archive/index.md` stores only the index; history bodies are stored by date in `docs/ja/todo/archive/YYYYMMDD.md`.


## Unfinished Tasks

### P0: Complete all PHP sample parity cases (stdout + artifact CRC32)

Context: [docs/ja/plans/p0-php-sample-parity-complete.md](../plans/p0-php-sample-parity-complete.md)

1. [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01] Complete PHP `sample` parity (stdout + artifact size + CRC32) for all 18 cases.
2. [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S1-01] Re-run parity for all PHP `sample` cases and lock the latest baseline for the single target.
3. [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S1-02] Split and classify artifact diffs for the 8 failing cases (`05,06,08,10,11,12,14,16`).
4. [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-01] Align the PHP GIF runtime with the Python implementation and resolve GIF-related CRC mismatches.
5. [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-02] Re-verify the PHP PNG runtime and fix required diffs.
6. [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-03] Correct image output inputs in PHP lower/emitter (palette/frame/list/bytes paths).
7. [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-04] Verify whether stdout mismatch recurs in `sample/13`; if unresolved, apply a root fix.
8. [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S3-01] Re-run `--targets php --all-samples` and confirm `case_pass=18` / `case_fail=0`.
9. [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S3-02] Add regression tests corresponding to the fixes and lock recurrence prevention.
10. [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S3-03] Record generated logs and decisions in the plan and make TODO completion criteria explicit.

### P1: Reorganize `test/unit` layout and prune unused tests

Context: [docs/ja/plans/p1-test-unit-layout-and-pruning.md](../plans/p1-test-unit-layout-and-pruning.md)

1. [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01] Reorganize `test/unit` into responsibility-based folders and prune unused tests with clear rationale.
2. [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S1-01] Inventory current tests in `test/unit` by responsibility classification (common/backends/ir/tooling/selfhost) and finalize the move map.
3. [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S1-02] Define target directory conventions and finalize naming/placement rules.
4. [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S2-01] Move test files to new directories and bulk-update reference paths in `tools/` and `docs/`.
5. [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S2-02] Update CI/local scripts so `unittest discover` and individual execution flows work under the new structure.
6. [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S3-01] Extract unused-test candidates and write an audit memo that decides `remove/integrate/keep`.
7. [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S3-02] Remove or integrate judged-unused tests and add recurrence checks (new if needed).
8. [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S4-01] Run key unit/transpile/selfhost regressions and confirm non-regression after reorganization and pruning.
9. [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S4-02] Reflect new test placement rules and operations in `docs/ja/spec` (and `docs/en/spec` if needed).
- Progress memo: [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S1-01] Inventoried 71 files in `test/unit` and finalized the move map as `backends/*:29, ir:10, tooling:5, selfhost:3, common:23`. Reorganize according to this classification in `S2-01`.

### P1: Complete Nim sample parity (formal integration of runtime_parity_check)

Context: [docs/ja/plans/p1-nim-sample-parity-complete.md](../plans/p1-nim-sample-parity-complete.md)

1. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01] Formally integrate Nim into parity regression targets and complete stdout + artifact (size + CRC32) match for all 18 `sample` cases.
2. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-01] Add Nim target support (transpile/run/toolchain detection) to `runtime_parity_check`.
3. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-02] Add Nim to `regenerate_samples.py` and lock the regeneration path for `sample/nim`.
4. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-03] Run parity for all Nim `sample` cases and lock failure categories.
5. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-01] Implement Nim runtime PNG writer as Python-compatible binary output.
6. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-02] Implement Nim runtime GIF writer (including `grayscale_palette`).
7. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-03] Align image output paths and runtime contracts in Nim emitter/lower.
8. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-04] Resolve remaining cases (for example `sample/18`) with minimal fixes.
9. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-01] Confirm `case_pass=18` / `case_fail=0` with `--targets nim --all-samples`.
10. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-02] Update regression tests for the Nim parity contract (CLI/smoke/transpile).
11. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-03] Record verification logs and operational steps in the plan and document close conditions explicitly.

### P2: Multi-language runtime parity with C++ (redesign: strict SoT + generation-first)

Context: [docs/en/plans/p2-runtime-parity-with-cpp.md](../plans/p2-runtime-parity-with-cpp.md)

1. [ ] [ID: P2-RUNTIME-PARITY-CPP-02] Redesign multi-language runtime parity under strict SoT, generation-first, and boundary separation rules.
2. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S1-01] Remove old P2 (`P2-RUNTIME-PARITY-CPP-01`) from the unfinished TODO list and replace it with the new P2.
3. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S1-02] Document SoT/pytra-core/pytra-gen boundaries and prohibitions in `docs/ja/spec`.
4. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S1-03] Create a classification table of target modules (`std/utils`) as `must-generate` vs `core-allowed`.
5. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S2-01] Add a static check for `pytra-gen` naming rule violations (passthrough naming).
6. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S2-02] Strengthen marker checks (`source/generated-by`) and placement checks (core/gen mix), then integrate into CI.
7. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S2-03] Audit SoT re-implementation residues inside `pytra-core` and feed the findings into a migration plan to `pytra-gen`.
8. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S3-01] Use Java as the first target and unify runtime API calls to the IR-resolved path (remove emitter hardcoding).
9. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S3-02] Apply the same policy to non-C++ backends (`cs/js/ts/go/rs/swift/kotlin/ruby/lua/scala/php/nim`).
10. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S3-03] Lint emitter prohibitions (runtime/library hardcoded names) and fail-fast in PR/CI.
11. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S4-01] Re-run sample parity for all target languages including artifact size + CRC32 and lock diffs.
12. [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S4-02] Reflect operation procedures (local/CI) in `docs/ja` and `docs/en`.

### P4: Full selfhost completion for all languages (Very very low priority)

Context: [docs/ja/plans/p4-multilang-selfhost-full-rollout.md](../plans/p4-multilang-selfhost-full-rollout.md)

1. [ ] [ID: P4-MULTILANG-SH-01] Gradually establish selfhost for `cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua/scala` and make multistage monitoring pass across all languages.
2. [ ] [ID: P4-MULTILANG-SH-01-S2-03] Resolve JS selfhost stage2 dependency-transpile failure and pass multistage.
3. [ ] [ID: P4-MULTILANG-SH-01-S3-01] Resolve TypeScript preview-only status and move to a selfhost-executable generation mode.
4. [ ] [ID: P4-MULTILANG-SH-01-S3-02] Connect with native backend tasks for Go/Java/Swift/Kotlin and enable the selfhost execution chain.
5. [ ] [ID: P4-MULTILANG-SH-01-S3-03] Add Ruby/Lua/Scala3 to selfhost multistage monitoring targets and resolve undefined runner states.
6. [ ] [ID: P4-MULTILANG-SH-01-S4-01] Integrate all-language multistage regressions into CI paths so recurrence of failure categories is continuously detected.
7. [ ] [ID: P4-MULTILANG-SH-01-S4-02] Document the completion-judgment template (stage pass conditions and exclusion conditions per language) and lock operation rules.
- Completed child tasks (`S1-01` to `S2-02-S3`) and past progress memos have been moved to `docs/ja/todo/archive/20260301.md`.
- Progress memo: [ID: P4-MULTILANG-SH-01-S2-03] Resolved JS emitter selfhost parser constraint violations (`Any`-typed `node.get()/node.items()`) and missing in-function `FunctionDef` support, moving the first failure from `stage1_dependency_transpile_fail` to `self_retranspile_fail (ERR_MODULE_NOT_FOUND: ./pytra/std.js)`.
- Progress memo: [ID: P4-MULTILANG-SH-01-S2-03] Added shim generation/import normalization/export injection/syntax rewrites for JS selfhost preparation and resolved `ERR_MODULE_NOT_FOUND`. The first failure shifted to `SyntaxError: Unexpected token ':'` (from `raw[qpos:]`).
- Progress memo: [ID: P4-MULTILANG-SH-01-S2-03] For JS selfhost, applied stepwise source-side degradation for slice/set checks, ESM shims, redesigned import normalization, compatibility shims for `argparse`/`Path`, `.py -> EAST3(JSON)` input path, and selfhost compatibility for `JsEmitter` profile loader. First failure advanced past `ReferenceError/SyntaxError` group to `TypeError: CodeEmitter._dict_copy_str_object is not a function`.
- Progress memo: [ID: P4-MULTILANG-SH-01-S2-03] Made dict access object-safe in `CodeEmitter.load_type_map` and `js_emitter` initialization, and added `set/list/dict` polyfills plus `CodeEmitter` static alias supplementation in selfhost rewrite. First failure moved from `dict is not defined` to `TypeError: module.get is not a function`.
- Progress memo: [ID: P4-MULTILANG-SH-01-S2-03] Rewrote `.get -> __pytra_dict_get` in selfhost rewrite, and added `parent/name/stem` property compatibility plus idempotent defaults for `mkdir(parents/exist_ok)` in `Path` shim. `js` reached `stage1 pass / stage2 pass`, and first failure moved to `stage3 sample output missing`.
- Progress memo: [ID: P4-MULTILANG-SH-01-S2-03] Added object-safe conversions for `CodeEmitter/JsEmitter` (remove `startswith/strip/find` dependencies, fix `next_tmp` f-string, remove `ord/chr` dependency in ASCII helper) and String polyfills in selfhost rewrite (`strip/lstrip/rstrip/startswith/endswith/find/lower/upper/map`). `js` maintained `stage1/native pass` and `multistage stage2 pass`; first failure advanced to `stage3 sample_transpile_fail (SyntaxError: Invalid or unexpected token)`.
- Progress memo: [ID: P4-MULTILANG-SH-01-S2-03] Replaced `emit` indentation generation (string multiplication) with loops, added non-string guard for `quote_string_literal` `quote`, and changed `_emit_function` `in_class` check from `None`-dependent to empty-string check. `js` maintained `stage1/native pass` and `multistage stage2 pass`; first failure updated to `stage3 sample_transpile_fail (SyntaxError: Unexpected token '{')` (remaining issue: unresolved placeholder/function-header collapse in `py2js_stage2.js`).
