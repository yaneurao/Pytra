# P4: Full Multi-Language Selfhost Completion (Very Low Priority)

Last updated: 2026-02-27

Related TODO:
- `ID: P4-MULTILANG-SH-01` in `docs-ja/todo/index.md`

Background:
- In current multi-language selfhost status, unfinished `stage1/stage2/stage3` remains outside C++.
- `rs` fails stage1; `cs`/`js` fail stage2; `ts` is preview-only; `go/java/swift/kotlin` have no multistage runner defined.
- To eventually establish a full "self-conversion chain works on all languages" state, this is tracked as a very-low-priority long-term backlog.

Goal:
- Gradually satisfy selfhost conditions for `py2<lang>.py` (`cpp/rs/cs/js/ts/go/java/swift/kotlin`) and converge to full multistage monitoring coverage across all languages.

In scope:
- `tools/check_multilang_selfhost_stage1.py` / `tools/check_multilang_selfhost_multistage.py` / `tools/check_multilang_selfhost_suite.py`
- Each language `py2*.py` and corresponding emitter/runtime
- Update path for selfhost verification reports (`docs-ja/plans/p1-multilang-selfhost-*.md`)

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
- 2026-02-27: Per user request, decided to add full multi-language selfhost completion as very-low-priority (`P4`) TODO.

## Breakdown

- [ ] [ID: P4-MULTILANG-SH-01-S1-01] Lock unfinished stage1/stage2/stage3 causes per language and document blocking-chain priority order.
- [ ] [ID: P4-MULTILANG-SH-01-S1-02] Define runner contracts for languages without multistage runners (go/java/swift/kotlin) and finalize implementation policy to resolve `runner_not_defined`.
- [ ] [ID: P4-MULTILANG-SH-01-S2-01] Resolve Rust selfhost stage1 failure (from-import acceptance) and move to stage2.
- [ ] [ID: P4-MULTILANG-SH-01-S2-02] Resolve C# selfhost stage2 compile failure and pass stage3 transpile.
- [ ] [ID: P4-MULTILANG-SH-01-S2-03] Resolve JS selfhost stage2 dependency-transpile failure and pass multistage.
- [ ] [ID: P4-MULTILANG-SH-01-S3-01] Resolve TypeScript preview-only status and move to a selfhost-executable generation mode.
- [ ] [ID: P4-MULTILANG-SH-01-S3-02] Link with Go/Java/Swift/Kotlin native-backend tasks and enable selfhost execution chain.
- [ ] [ID: P4-MULTILANG-SH-01-S4-01] Integrate all-language multistage regressions into CI path to continuously detect failure-category recurrence.
- [ ] [ID: P4-MULTILANG-SH-01-S4-02] Document completion-judgment template (stage-pass and exclusion conditions per language) and lock operation rules.
