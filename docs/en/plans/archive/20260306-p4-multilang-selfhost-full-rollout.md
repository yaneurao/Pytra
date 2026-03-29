<a href="../../../ja/plans/archive/20260306-p4-multilang-selfhost-full-rollout.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P4: Full Multi-Language Selfhost Completion (Deferred Until ABI Stabilization)

Last updated: 2026-03-06

Related TODO:
- Removed from the open TODO list on 2026-03-06.
- Re-add `ID: P4-MULTILANG-SH-01` only after ABI and runtime-boundary work has stabilized.

Background:
- In current multi-language selfhost status, unfinished `stage1/stage2/stage3` remains outside C++.
- `rs/cs` still have unfinished `stage2`/`stage3` work, `js` still fails stage3, `ts/go/java/swift/kotlin` still have no multistage runner contract, and `ruby/lua/scala/php/nim` remain outside multistage monitoring scope.
- To eventually establish a full "self-conversion chain works on all languages" state, this is tracked as a very-low-priority long-term backlog.

Goal:
- Gradually satisfy selfhost conditions for `py2<lang>.py` (`cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua/scala/php/nim`) and converge to full multistage monitoring coverage across all languages.

In scope:
- `tools/check/check_multilang_selfhost_stage1.py` / `tools/check/check_multilang_selfhost_multistage.py` / `tools/check/check_multilang_selfhost_suite.py`
- Each language `py2*.py` and corresponding emitter/runtime
- Update path for selfhost verification reports (`docs/ja/plans/p1-multilang-selfhost-*.md`)

Out of scope:
- Speed optimization or code-size optimization
- Full backend redesigns not needed for selfhost establishment
- Starting this ahead of existing P0/P1/P3 tasks

Acceptance criteria:
- All languages are `stage1 pass` in `tools/check/check_multilang_selfhost_suite.py`.
- Multistage reports show `stage2 pass` and `stage3 pass` for all languages (or explicit permanent exclusions).
- Persistent dependence on `runner_not_defined` / `preview_only` / `toolchain_missing` is eliminated.

Verification commands:
- `python3 tools/check/check_multilang_selfhost_suite.py`
- `python3 tools/check/check_multilang_selfhost_stage1.py`
- `python3 tools/check/check_multilang_selfhost_multistage.py`
- `python3 tools/build_selfhost.py`

Decision log:
- 2026-02-27: Per user request, added full multi-language selfhost completion as very-low-priority (`P4`) TODO.
- 2026-03-02: Per user request, added `ruby/lua/scala` to selfhost target languages and expanded P4 monitoring scope to `cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua/scala`.
- 2026-03-05: Per user request, added `php/nim` to the selfhost target languages and expanded the P4 monitoring scope to `cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua/scala/php/nim`. At the same time, reconfirmed the policy of achieving selfhost through the common path without increasing language-specific special-case implementations.
- 2026-03-06: Per user instruction, this plan was withdrawn from the open TODO list because there is no point in advancing it before the current ABI / runtime responsibility boundary is stabilized. This is not treated as completed; it will be reevaluated after the ABI specification is established.
- 2026-02-27: Fixed per-language stage blockers and runner-contract definitions (`S1-01`, `S1-02`).
- 2026-02-27 to 2026-03-01: Completed Rust stage1 unblock and C# stage2/stage3 unblocks through incremental emitter/runtime/selfhost source fixes.
- 2026-03-01: `P4-MULTILANG-SH-01-S2-02` and child tasks through `S2-02-S3` reached done status; remaining work is now JS/TS/GSK chain and CI integration.
- 2026-03-02: [ID: `P4-MULTILANG-SH-01-S2-03`] Replaced JS selfhost parser constraint violations in `src/hooks/js/emitter/js_emitter.py` (`node.get()/node.items()` on `Any`) via object-safe helpers and extended unsupported in-function `FunctionDef` emit to local-function output. First `js` failure moved from `stage1_dependency_transpile_fail` to `self_retranspile_fail (ERR_MODULE_NOT_FOUND: ./pytra/std.js)`.
- 2026-03-02: [ID: `P4-MULTILANG-SH-01-S2-03`] Extended JS preparation in `check_multilang_selfhost_stage1.py` / `check_multilang_selfhost_multistage.py` with selfhost shim generation, import-relative-path normalization, named-export injection, and syntax rewrites for `in {..}` / simple f-strings. `ERR_MODULE_NOT_FOUND` was resolved, and the first failure moved to `SyntaxError: Unexpected token ':'` (Python slice syntax from `raw[qpos:]`).
- 2026-03-02: [ID: `P4-MULTILANG-SH-01-S2-03`] Added source-side reductions for `raw[qpos:]` / `txt in {"",...}`, ESM-ized and re-applied JS selfhost shim/runtime, argparse map-tag compatibility, `.py -> EAST3(JSON)` input switching, and staged relaxation of `JsEmitter` profile-loader selfhost dependencies (`EmitterHooks`/`__file__`/`CodeEmitter`). `ReferenceError/SyntaxError` classes were cleared; first failure moved to `TypeError: CodeEmitter._dict_copy_str_object is not a function`.
- 2026-03-02: [ID: `P4-MULTILANG-SH-01-S2-03`] Made `.get` paths in `CodeEmitter.load_type_map` and `profile/operators/syntax` references in `JsEmitter.__init__` object-safe, and added `set/list/dict` polyfills plus `CodeEmitter` static alias completion in selfhost rewrite. Resolved `dict is not defined`; first failure moved to `TypeError: module.get is not a function`.
- 2026-03-02: [ID: `P4-MULTILANG-SH-01-S2-03`] Unified `.get(...)` to `__pytra_dict_get(...)` in selfhost rewrite and resolved descriptor collisions from `Object.prototype.get`. Also added `parent/name/stem` property compatibility and default-idempotent `mkdir` in the `Path` shim. Re-check reached `js stage1 pass / stage2 pass`, and multistage first failure advanced to `sample_transpile_fail: stage3 sample output missing`.
- 2026-03-02: [ID: `P4-MULTILANG-SH-01-S2-03`] Further reinforced CodeEmitter/JsEmitter selfhost compatibility: reduced dynamic-value dependencies for `startswith/strip/find` through helpers, replaced `next_tmp` f-string path (`self` resolution break) with concatenation, removed `ord/chr` dependency from ASCII helpers, and added String polyfills (`strip/lstrip/rstrip/startswith/endswith/find/lower/upper/map`) in stage-checker JS rewrite. Re-passed `python3 tools/check/check_multilang_selfhost_stage1.py --strict-stage1` / `python3 tools/check/check_multilang_selfhost_multistage.py`; `js` kept `stage1/native pass` and `multistage stage2 pass`; first failure updated to `stage3 sample_transpile_fail (SyntaxError: Invalid or unexpected token)`.
- 2026-03-02: [ID: `P4-MULTILANG-SH-01-S2-03`] Traced stage3 failure with minimal repro and confirmed `py2js_stage2.js` header collapse (`0import ...` / `undefined...`). Replaced string-multiplication dependency in `CodeEmitter.emit` with `_indent_padding` loop, added non-string guard for `quote_string_literal` `quote`, and switched `JsEmitter._emit_function` `in_class` check to empty-string sentinel to partially resolve stage2 output corruption. Latest re-check kept `js: stage1/native pass`, `multistage stage2 pass`; first failure updated to `stage3 sample_transpile_fail (SyntaxError: Unexpected token '{')` (stage2 output corruption including unresolved placeholders like `return {value};`).

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

Supplement:
- At the timing of this table, `ruby/lua/scala/php/nim` were outside checker targets and therefore unmeasured (monitoring not connected).

Blocking-chain priority:
1. Fix `rs` stage2 compile failure (cannot proceed to stage3).
2. Fix `cs` stage2 compile failure (cannot proceed to stage3).
3. Fix `js` stage2 dependency-transpile failure (cannot proceed to stage3).
4. Resolve `ts` preview-only state (stage2/stage3 evaluation is blocked).
5. Define runners for `go/java/swift/kotlin` and remove `runner_not_defined`.
6. Add `ruby/lua/scala` to multistage checker targets and resolve unmonitored status.

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
| ruby | no build needed (interpreter run) | `ruby <stage*.rb> <input.py> -o <out.rb>` | `out.rb` is generated |
| lua | no build needed (interpreter run) | `lua <stage*.lua> <input.py> -o <out.lua>` | `out.lua` is generated |
| scala | `scala run <runtime.scala> <stage*.scala> -- --help` (runnability check) | `scala run <runtime.scala> <stage*.scala> -- <input.py> -o <out.scala>` | `out.scala` is generated |
| php | no build needed (interpreter run) | `php <stage*.php> <input.py> -o <out.php>` | `out.php` is generated |
| nim | `nim c -o:<runner> <stage*.nim>` | `<runner> <input.py> -o <out.nim>` | `out.nim` is generated |

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
- [ ] [ID: P4-MULTILANG-SH-01-S3-03] Add Ruby/Lua/Scala3/PHP/Nim to selfhost multistage checker targets and resolve runner-undefined/out-of-scope status.
- [ ] [ID: P4-MULTILANG-SH-01-S3-03-S1] Add `ruby/lua/scala/php/nim` to target-language sets in `check_multilang_selfhost_stage1.py` / `check_multilang_selfhost_multistage.py` / `check_multilang_selfhost_suite.py`, and implement category classification.
- [ ] [ID: P4-MULTILANG-SH-01-S3-03-S2] Add stage2/stage3 runner implementations (build/run/output-missing checks) for Ruby/Lua/Scala3/PHP/Nim.
- [ ] [ID: P4-MULTILANG-SH-01-S3-03-S3] Establish the first multistage baseline for `ruby/lua/scala/php/nim` and lock language-specific blocker chains.
- [ ] [ID: P4-MULTILANG-SH-01-S4-01] Integrate all-language multistage regressions into CI path to continuously detect failure-category recurrence.
- [ ] [ID: P4-MULTILANG-SH-01-S4-02] Document completion-judgment template (stage-pass and exclusion conditions per language) and lock operation rules.
