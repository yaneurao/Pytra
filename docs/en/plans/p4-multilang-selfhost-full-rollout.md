# P4: Full Multi-Language Selfhost Completion (Very Low Priority)

Last updated: 2026-03-01

Related TODO:
- `ID: P4-MULTILANG-SH-01` in `docs/ja/todo/index.md`

Background:
- In current multi-language selfhost status, unfinished `stage1/stage2/stage3` remains outside C++.
- `rs` originally failed stage1; `cs`/`js` failed stage2; `ts` is preview-only; `go/java/swift/kotlin` had no multistage runner contract.
- To eventually establish a full "self-conversion chain works on all languages" state, this is tracked as a very-low-priority long-term backlog.

Goal:
- Gradually satisfy selfhost conditions for `py2<lang>.py` (`cpp/rs/cs/js/ts/go/java/swift/kotlin`) and converge to full multistage monitoring coverage across all languages.

In scope:
- `tools/check_multilang_selfhost_stage1.py` / `tools/check_multilang_selfhost_multistage.py` / `tools/check_multilang_selfhost_suite.py`
- Each language `py2*.py` and corresponding emitter/runtime
- Update path for selfhost verification reports (`docs/ja/plans/p1-multilang-selfhost-*.md`)

Out of scope:
- Speed optimization or code-size optimization
- Full backend redesigns not needed for selfhost establishment
- Starting this ahead of existing P0/P1/P3 tasks

Acceptance criteria:
- All languages are `stage1 pass` in `tools/check_multilang_selfhost_suite.py`.
- Multistage reports show `stage2 pass` and `stage3 pass` for all languages (or explicit permanent exclusions).
- Persistent dependence on `runner_not_defined` / `preview_only` / `toolchain_missing` is eliminated.

Verification commands:
- `python3 tools/check_multilang_selfhost_suite.py`
- `python3 tools/check_multilang_selfhost_stage1.py`
- `python3 tools/check_multilang_selfhost_multistage.py`
- `python3 tools/build_selfhost.py`

Decision log:
- 2026-02-27: Per user request, added full multi-language selfhost completion as very-low-priority (`P4`) TODO.
- 2026-02-27: Fixed per-language stage blockers and runner-contract definitions (`S1-01`, `S1-02`).
- 2026-02-27 to 2026-03-01: Completed Rust stage1 unblock and C# stage2/stage3 unblocks through incremental emitter/runtime/selfhost source fixes.
- 2026-03-01: `P4-MULTILANG-SH-01-S2-02` and child tasks through `S2-02-S3` reached done status; remaining work is now JS/TS/GSK chain and CI integration.

## Current Snapshot (S1-01)

Per-language blocker snapshot (2026-02-27 baseline):

| lang | stage1 | stage2 | stage3 | category | first blocker |
| --- | --- | --- | --- | --- | --- |
| rs | fail | skip | skip | `stage1_transpile_fail` | `unsupported from-import clause` |
| cs | pass | fail | skip | `compile_fail` | unresolved `Path` type (`System.IO` mapping gap) |
| js | pass | fail | skip | `stage1_dependency_transpile_fail` | JS emitter object-receiver attribute/method restriction |
| ts | pass | blocked | blocked | `preview_only` | generated transpiler remains preview-only |
| go | pass | skip | skip | `runner_not_defined` | multistage runner undefined |
| java | pass | skip | skip | `runner_not_defined` | multistage runner undefined |
| swift | pass | skip | skip | `runner_not_defined` | multistage runner undefined |
| kotlin | pass | skip | skip | `runner_not_defined` | multistage runner undefined |

Blocking-chain priority:
1. Fix `rs` stage1 failure (otherwise stage2/stage3 cannot be evaluated).
2. Fix `cs` stage2 compile failure (cannot proceed to stage3).
3. Fix `js` stage2 dependency-transpile failure (cannot proceed to stage3).
4. Resolve `ts` preview-only state (stage2/stage3 evaluation is blocked).
5. Define runners for `go/java/swift/kotlin` and remove `runner_not_defined`.

## Runner Contracts (S1-02)

Purpose:
- Replace `runner_not_defined` in `check_multilang_selfhost_multistage.py` with language-specific adapters.

Common API contract:
1. `build_stage1(lang, stage1_src, stage1_runner)`
2. `run_stage2(lang, stage1_runner, src_py, stage2_src)`
3. `build_stage2(lang, stage2_src, stage2_runner)`
4. `run_stage3(lang, stage2_runner, sample_py, stage3_out)`

Language-specific runner contracts:

| lang | build_stage1 / build_stage2 | run_stage2 / run_stage3 | success condition |
| --- | --- | --- | --- |
| go | `go build -o <runner> <stage*.go>` | `<runner> <input.py> -o <out.go>` | `out.go` is generated |
| java | `javac <stage*.java>` | `java -cp <dir> <main_class> <input.py> -o <out.java>` | `out.java` is generated |
| swift | `swiftc <stage*.swift> -o <runner>` | `<runner> <input.py> -o <out.swift>` | `out.swift` is generated |
| kotlin | `kotlinc <stage*.kt> -include-runtime -d <runner.jar>` | `java -jar <runner.jar> <input.py> -o <out.kt>` | `out.kt` is generated |

Failure classification rules:
- build failure: `compile_fail` / `stage2_compile_fail`
- runtime failure: `self_retranspile_fail` / `sample_transpile_fail`
- missing output: include as runtime failure with `output missing` note

## Breakdown

- [x] [ID: P4-MULTILANG-SH-01-S1-01] Lock unfinished stage1/stage2/stage3 causes per language and document blocking-chain priority order.
- [x] [ID: P4-MULTILANG-SH-01-S1-02] Define runner contracts for languages without multistage runners (`go/java/swift/kotlin`) and finalize implementation policy to resolve `runner_not_defined`.
- [x] [ID: P4-MULTILANG-SH-01-S2-01] Resolve Rust selfhost stage1 failure (from-import acceptance) and move to stage2.
- [x] [ID: P4-MULTILANG-SH-01-S2-02] Resolve C# selfhost stage2 compile failure and pass stage3 transpile.
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S1] Fill C# emitter selfhost compatibility gaps (`Path`, `str.endswith|startswith`, constant default args) and move first compile blocker forward.
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2] Finalize import-dependency closure policy for `py2cs.py` selfhost artifacts (single-source generation or module linking) and resolve `sys/argparse/transpile_cli` unresolved path.
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S1] Remove C# selfhost first-error gate (`sys.exit`, docstring expression) and lock first unresolved symbol for import closure.
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2] Implement C# selfhost import-dependency closure (single selfhost source or module linking) and resolve `transpile_to_csharp` unresolved path.
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S1] Implement PoC for single selfhost source (`prepare_selfhost_source_cs.py`) and validate conversion viability.
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2] Resolve PoC blockers (C# object-receiver restrictions) or pivot to module-linking path to establish import closure.
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S1] Resolve parse-time restrictions in single-source PoC and pass C# conversion of `selfhost/py2cs.py`.
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2] Classify compile failures in single selfhost source artifact (`cs_selfhost_full_stage1.cs`) and close emit/runtime compatibility gaps needed for mcs pass.
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S1] Add machine-classification tooling for compile failures and report current error-code/category state.
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S2] Implement fixes for classified categories (template-fragment leakage / broken call shape / shadowed locals) and reduce `CS1525/CS1002`.
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S3] Implement emit policy avoiding `mcs` internal exception (`tuples > 7`) and return stage2 compile to normal validation.
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S4] Reduce first-category counts among normal compile errors (`CS1061/CS0103/CS1503` top groups).
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S5] Add emitter lowering for remaining top groups (`CS0103 set/list/json`, `CS0019 char/string`) and further reduce stage2 failures.
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S6] Resolve remaining major failures (`json` unresolved, `dict.get/items` not lowered, `CodeEmitter` static-reference mismatch) and refresh top error composition.
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7] Reinforce nested helpers/type reductions for remaining top failures (`_add`/`item_expr` undefined, object-driven `CS1503/CS0266`) and further reduce stage2 compile counts.
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S3] Pass C# selfhost stage2/stage3 and move from `compile_fail` to `pass`.
- [ ] [ID: P4-MULTILANG-SH-01-S2-03] Resolve JS selfhost stage2 dependency-transpile failure and pass multistage.
- [ ] [ID: P4-MULTILANG-SH-01-S3-01] Resolve TypeScript preview-only status and move to a selfhost-executable generation mode.
- [ ] [ID: P4-MULTILANG-SH-01-S3-02] Link with Go/Java/Swift/Kotlin native-backend tasks and enable selfhost execution chains.
- [ ] [ID: P4-MULTILANG-SH-01-S4-01] Integrate all-language multistage regressions into CI path to continuously detect failure-category recurrence.
- [ ] [ID: P4-MULTILANG-SH-01-S4-02] Document completion-judgment template (stage-pass and exclusion conditions per language) and lock operation rules.
