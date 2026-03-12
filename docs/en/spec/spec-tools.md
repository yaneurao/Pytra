<a href="../../ja/spec/spec-tools.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# `tools/` Script Index

`tools/` contains helper scripts that automate Pytra development workflows.
They serve three main goals:

- repeat regression checks quickly
- standardize selfhost investigation / comparison / build flows
- update and validate C++ runtime artifacts from the `src/pytra/` source of truth

## 1. Daily-Use Tools

- `tools/run_local_ci.py`
  - Purpose: run the local minimal CI bundle at once (version gate + todo-priority guard + runtime-layer guard + non-C++ emitter runtime-call literal guard + forbidden runtime-symbol guard + non-C++ backend health gate + conditional sample regeneration + transpile regression + unit tests + selfhost build + diff)
- `tools/check_todo_priority.py`
  - Purpose: verify that new progress `ID`s added in diffs to `docs/ja/todo/index.md` / `docs/ja/plans/*.md` match the highest-priority unfinished `ID` (or one of its children), and prevent priority drift
- `tools/check_runtime_cpp_layout.py`
  - Purpose: validate the C++ runtime ownership boundary in one guard: keep `src/runtime/cpp/{built_in,std,utils}` legacy-closed, enforce `generated/native/pytra` ownership, and validate the `core` compatibility surface plus the `generated/core` / `native/core` split
  - Notes: `generated/built_in` / `generated/core` require plain naming plus generated markers, ownership mixing into `native` / `core` fails, and reintroducing removed transitive includes (`predicates` / `sequence` / `iter_ops`) into `native/core/py_runtime.h` also fails
- `tools/check_py2cpp_transpile.py`
  - Purpose: batch-transpile `test/fixtures/` with `py2x.py --target cpp`
- `tools/check_py2rs_transpile.py`
  - Purpose: batch-transpile `test/fixtures/` and `sample/py` with `py2x.py --target rs`
- `tools/check_py2js_transpile.py`
  - Purpose: batch-transpile `test/fixtures/` and `sample/py` with `py2x.py --target js`
- `tools/check_py2cs_transpile.py`
  - Purpose: batch-transpile `test/fixtures/` and `sample/py` with `py2x.py --target cs`
- `tools/check_py2go_transpile.py`
  - Purpose: batch-transpile `test/fixtures/` and `sample/py` with `py2x.py --target go`
- `tools/check_py2java_transpile.py`
  - Purpose: batch-transpile `test/fixtures/` and `sample/py` with `py2x.py --target java`
- `tools/check_py2ts_transpile.py`
  - Purpose: batch-transpile `test/fixtures/` and `sample/py` with `py2x.py --target ts`
- `tools/check_py2swift_transpile.py`
  - Purpose: batch-transpile `test/fixtures/` and `sample/py` with `py2x.py --target swift`
- `tools/check_py2kotlin_transpile.py`
  - Purpose: batch-transpile `test/fixtures/` and `sample/py` with `py2x.py --target kotlin`
- `tools/check_py2scala_transpile.py`
  - Purpose: batch-transpile `test/fixtures/` and `sample/py` with `py2x.py --target scala`
- `tools/check_yanesdk_py2cpp_smoke.py`
  - Purpose: verify that the canonical Yanesdk set (`1 library + 7 games`) still passes `py2x.py --target cpp`
- `tools/check_microgpt_original_py2cpp_regression.py`
  - Purpose: keep the original `materials/refs/microgpt/microgpt-20260222.py` fixed as input and detect the first failure stage (A-F) or success
- `tools/build_multi_cpp.py`
  - Purpose: read `manifest.json` emitted by `py2x.py --target cpp --multi-file` and build all related `*.cpp` files plus runtime
- `tools/gen_makefile_from_manifest.py`
  - Purpose: generate a `Makefile` from `manifest.json`
- `tools/verify_multi_file_outputs.py`
  - Purpose: build/run multi-file outputs from `sample/py` and verify that results match single-file outputs
- `tools/check_transpiler_version_gate.py`
  - Purpose: verify that when transpiler-related files change, the corresponding component in `src/toolchain/compiler/transpiler_versions.json` has a minor-or-greater version bump
- `tools/regenerate_samples.py`
  - Purpose: regenerate each `sample/<lang>` from `sample/py`, skipping regeneration unless the version token in `src/toolchain/compiler/transpiler_versions.json` changed
- `tools/run_regen_on_version_bump.py`
  - Purpose: launch `regenerate_samples.py` only when a minor-or-greater version update is detected in `transpiler_versions.json`
- `tools/sync_todo_history_translation.py`
  - Purpose: treat `docs/ja/todo/archive` as the source of truth and synchronize the date-file skeletons plus index in `docs/en/todo/archive`
- `tools/verify_sample_outputs.py`
  - Purpose: compare C++ execution results (stdout/artifacts) against the golden baseline in `sample/golden/manifest.json`
- `tools/verify_image_runtime_parity.py`
  - Purpose: verify parity between Python SoT and C++ image runtime (PNG/GIF)
- `tools/check_runtime_std_sot_guard.py`
  - Purpose: enforce `src/pytra/std/*.py` / `src/pytra/utils/*.py` as the source of truth, treat `src/runtime/{rs,cs}/generated/**` as the canonical generated lane for `rs/cs`, fail handwritten re-entry into legacy generated lanes for the guarded module set, and verify the C++ `std/utils` ownership split on the `generated/native` lanes
- `tools/check_runtime_core_gen_markers.py`
  - Purpose: require `source/generated-by` markers in the canonical generated lane (`src/runtime/<lang>/generated/**` for `rs/cs`, `pytra-gen/**` for legacy backends) and detect mixed generated markers in handwritten lanes; for C++, also require markers in `src/runtime/cpp/generated/core/**`, forbid them in `src/runtime/cpp/native/core/**`, and catch marker-bearing files if the legacy `src/runtime/cpp/core/**` tree reappears
- `tools/check_runtime_pytra_gen_naming.py`
  - Purpose: validate the canonical generated-lane naming/layout for `std|utils` (`generated/**` for `rs/cs`, `pytra-gen/**` for legacy backends)
- `tools/check_emitter_runtimecall_guardrails.py`
  - Purpose: detect new literal runtime/stdlib dispatch branches in non-C++ emitters
- `tools/check_emitter_forbidden_runtime_symbols.py`
  - Purpose: detect forbidden runtime implementation symbols in `src/backends/*/emitter/*.py`

### 1.1 Stop-Ship Checklist for Emitter Changes (mandatory)

- Applies to commits changing `src/backends/*/emitter/*.py`
- Before commit, run all three:
  - `python3 tools/check_emitter_runtimecall_guardrails.py`
  - `python3 tools/check_emitter_forbidden_runtime_symbols.py`
  - `python3 tools/check_noncpp_east3_contract.py`
- If any of them fails, treat it as Stop-Ship and do not commit/push/request review
- Review checklist:
  - [ ] logs exist for the 3 commands
  - [ ] no new forbidden runtime implementation symbols were added to emitters
  - [ ] runtime/stdlib call resolution uses only the EAST3 canonical fields (`runtime_call` / `resolved_runtime_call` / `resolved_runtime_source`)

## 2. Selfhost Tools

- `tools/build_selfhost.py`
  - Purpose: build `selfhost/py2cpp.out`
- `tools/build_selfhost_stage2.py`
  - Purpose: use `selfhost/py2cpp.out` to re-transpile `selfhost/py2cpp.py` and build `selfhost/py2cpp_stage2.out`
- `tools/prepare_selfhost_source.py`
  - Purpose: expand pieces such as `CodeEmitter` into selfhost-ready sources
- `tools/selfhost_transpile.py`
  - Purpose: temporary bridge for `.py -> EAST JSON -> selfhost`
- `tools/check_selfhost_cpp_diff.py`
  - Purpose: compare generated C++ from the Python version and the selfhost version
- `tools/check_selfhost_direct_compile.py`
  - Purpose: batch-transpile `sample/py` through the selfhost direct `.py` route and detect compile regressions via `g++ -fsyntax-only`
- `tools/check_selfhost_stage2_cpp_diff.py`
  - Purpose: compare generated C++ between the Python version and the stage-2 selfhost binary
- `tools/summarize_selfhost_errors.py`
  - Purpose: aggregate selfhost build-log errors by category
- `tools/selfhost_error_hotspots.py`
  - Purpose: aggregate error hotspots by function
- `tools/selfhost_error_report.py`
  - Purpose: format selfhost analysis results into a report

### 2.1 Selfhost Runaway Guards

To stop long-running cases caused by deep recursion, huge ASTs, or symbol explosions during selfhost investigation, the following guards are staged into `py2x.py --target cpp` / common CLI:

- `--guard-profile {off,default,strict}`
  - default is `default`
  - `off` disables limits
  - `strict` lowers limits for investigation
- `default` baseline:
  - `max-ast-depth=800`
  - `max-parse-nodes=2000000`
  - `max-symbols-per-module=200000`
  - `max-scope-depth=400`
  - `max-import-graph-nodes=5000`
  - `max-import-graph-edges=20000`
  - `max-generated-lines=2000000`
- `strict` baseline:
  - `max-ast-depth=200`
  - `max-parse-nodes=200000`
  - `max-symbols-per-module=20000`
  - `max-scope-depth=120`
  - `max-import-graph-nodes=1000`
  - `max-import-graph-edges=4000`
  - `max-generated-lines=300000`
- per-limit overrides (higher priority than `guard_profile`)
  - `--max-ast-depth`
  - `--max-parse-nodes`
  - `--max-symbols-per-module`
  - `--max-scope-depth`
  - `--max-import-graph-nodes`
  - `--max-import-graph-edges`
  - `--max-generated-lines`

Failure contract:

- exceeding any limit fails fast as `input_invalid(kind=limit_exceeded, stage=<parse|analyze|emit>, limit=<name>, value=<n>)`
- selfhost execution tools such as `tools/build_selfhost.py` may additionally use `--timeout-sec` to cap process runtime

## 3. Cross-Language Verification

- `tools/runtime_parity_check.py`
  - Purpose: run runtime-level parity checks across multiple target languages
  - Notes: unstable time lines such as `elapsed_sec`, `elapsed`, and `time_sec` are ignored by default
  - Notes: artifact comparison requires matching presence + size + CRC32 for files reported via `output:`
  - Notes: before each case, identically named artifacts under `sample/out`, `test/out`, and `out` are deleted to avoid stale-output mixups
  - Notes: on timeout, the whole process group is killed so orphaned children such as `*_swift.out` are not left behind
- `tools/check_all_target_sample_parity.py`
  - Purpose: run canonical parity groups (`cpp`, `js_ts`, `compiled`, `scripting_mixed`) in order and establish full-target sample parity
  - Main options: `--groups`, `--east3-opt-level`, `--cpp-codegen-opt`, `--summary-dir`
- `tools/check_noncpp_backend_health.py`
  - Purpose: aggregate the non-C++ backend health gate after linked-program rollout by family, exposing `primary_failure`, `toolchain_missing`, and broken/green family status in one command
  - Main options: `--family`, `--targets`, `--skip-parity`, `--summary-json`
- `tools/check_scala_parity.py`
  - Purpose: run sample parity plus the positive fixture manifest for Scala3 as one canonical route

### 3.1 Smoke-Test Operation After `py2x` Unification

- Common smoke cases are canonically defined in `test/unit/common/test_py2x_smoke_common.py`
- Language-specific smoke suites keep only language-specific emitter/runtime contracts
- Each language-specific smoke suite must include a responsibility-boundary comment and is statically checked by `tools/check_noncpp_east3_contract.py`
- Canonical `PYTHONPATH` for smoke execution is `src:.:test/unit`
- Recommended regression order:
  - `PYTHONPATH=src:.:test/unit python3 -m unittest discover -s test/unit/common -p 'test_py2x_smoke*.py'`
  - `python3 tools/check_noncpp_east3_contract.py --skip-transpile`
  - `python3 tools/check_py2<lang>_transpile.py`

### 3.2 Non-C++ Backend Health Matrix (Post Linked Program)

- Evaluate recovery in the order `static_contract -> common_smoke -> target_smoke -> transpile -> parity`
- Run `parity` only for targets that passed every earlier gate
- Keep `toolchain_missing` as infra baseline separate from `parity_fail`
- Snapshot as of 2026-03-08:
  - Wave 1: `js/ts` green, `rs/cs` toolchain-missing
  - Wave 2: `go/java/kotlin/swift/scala` toolchain-missing for sample parity
  - Wave 3: `ruby/lua/php/nim` toolchain-missing for sample parity
- Daily family-level health checks use commands such as `python3 tools/check_noncpp_backend_health.py --family wave1`
- `tools/run_local_ci.py` includes `python3 tools/check_noncpp_backend_health.py --family all --skip-parity`

### 3.3 Full-Target Sample Parity Done Condition

- Canonical parity target order:
  - `cpp,rs,cs,js,ruby,lua,php,ts,go,java,swift,kotlin,scala,nim`
- "full-target parity green" means:
  - running `python3 tools/runtime_parity_check.py --targets cpp,rs,cs,js,ruby,lua,php,ts,go,java,swift,kotlin,scala,nim --case-root sample --all-samples --ignore-unstable-stdout --east3-opt-level 2 --cpp-codegen-opt 3`
  - and every target / every one of the 18 sample cases finishes as `ok`
- No exception is made for `toolchain_missing`; all of the following must be zero:
  - `case_missing`
  - `python_failed`
  - `python_artifact_missing`
  - `toolchain_missing`
  - `transpile_failed`
  - `run_failed`
  - `output_mismatch`
  - `artifact_presence_mismatch`
  - `artifact_missing`
  - `artifact_size_mismatch`
  - `artifact_crc32_mismatch`
- Canonical wrapper for daily reruns:
  - `python3 tools/check_all_target_sample_parity.py --summary-dir work/logs/all_target_sample_parity`

### 3.4 Debian 12 Parity Bootstrap Snapshot

- Current-machine snapshot as of 2026-03-08 assumes Debian 12 (`bookworm`) and `root`
- Compiled-target bootstrap:
  - `apt-get update`
  - `apt-get install -y rustc mono-mcs golang-go openjdk-17-jdk kotlin scala nim`
  - `apt-get install -y binutils-gold gcc git libcurl4-openssl-dev libedit-dev libpython3-dev libsqlite3-dev uuid-dev gnupg2`
  - install Swift 6.2.2 for Debian 12 under `/opt`, then symlink `swift` / `swiftc` into `/usr/local/bin`
- Scripting/mixed bootstrap:
  - `apt-get install -y ruby lua5.4 php-cli`
- After bootstrap, `runner_needs` was measured as `OK` for `cpp,rs,cs,js,ruby,lua,php,ts,go,java,swift,kotlin,scala,nim`

## 4. Update Rules

- Whenever a new tool is added under `tools/`, update this document at the same time
- Each tool description must state in one line what it automates
- If destructive changes are made (arguments, deprecation, consolidation), also update the related examples in `docs/ja/tutorial/how-to-use.md`
- Sample regeneration is triggered by minor-or-greater updates in `src/toolchain/compiler/transpiler_versions.json`, not merely by source diffs
- Commits that modify transpiler-related files (`src/py2*.py`, `src/pytra/**`, `src/backends/**`, `src/backends/**/profiles/**`) must pass `tools/check_transpiler_version_gate.py`
- When regeneration happens due to a version bump, use `tools/run_regen_on_version_bump.py --verify-cpp-on-diff` to compile/run only the C++ cases whose generated output changed
- Toolchain-compatibility shims go under `tools/shims/`; do not add special root-level directories such as `.chain`
