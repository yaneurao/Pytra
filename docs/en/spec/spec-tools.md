<a href="../../ja/spec/spec-tools.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# `tools/` Script Index

`tools/` is the collection of helper scripts that automates Pytra development operations.
Its goals are the following three:

- make regression checks repeatable in a short cycle
- standardize selfhost investigation, comparison, and build flows
- update and validate C++ runtime generated artifacts from the `src/pytra/` source of truth

## 1. Daily-Use Tools

- `tools/run_local_ci.py`
  - Purpose: run the local minimal CI bundle in one shot (version gate + todo-priority guard + runtime-layer split guard + non-C++ emitter runtime-call literal guard + emitter forbidden runtime implementation symbol guard + non-C++ backend health gate + conditional sample regeneration + transpile regression + unit + selfhost build + diff).
- `tools/check_todo_priority.py`
  - Purpose: verify that progress `ID`s newly added in diffs to `docs/ja/todo/index.md` / `docs/ja/plans/*.md` match the highest unfinished `ID` (or one of its child `ID`s), and prevent priority drift. On the `plans` side, only decision-log lines (`- YYYY-MM-DD: ...`) are judged as progress; structural ID enumerations are excluded.
- `tools/check_jsonvalue_decode_boundaries.py`
  - Purpose: verify that `json.loads_obj(...)` is the canonical entrypoint at JSON artifact boundaries in `pytra-cli.py` / `east2x.py` / `toolchain/compile/east_io.py` / `toolchain/link/*`, and fail fast on any re-entry of raw `json.loads(...)`.
- `tools/check_runtime_cpp_layout.py`
  - Purpose: validate, under one guard, that `src/runtime/cpp/{built_in,std,utils}` stays legacy-closed, that `generated/native/pytra` ownership boundaries are preserved, and that the `core` compatibility surface plus the `generated/core` / `native/core` split stay intact.
  - Notes: `generated/built_in` / `generated/core` require plain naming and generated markers, ownership mixing into `native` / `core` fails, and reintroducing removed transitive includes (`predicates` / `sequence` / `iter_ops`) into `native/core/py_runtime.h` also fails.
- `tools/check_py2x_transpile.py`
  - Purpose: batch-convert `test/fixtures/` and `sample/py` with `pytra-cli.py --target <lang>` and detect failing cases. This is the unified transpile checker across all languages.
  - Main options: `--target <lang>` (`cpp`, `rs`, `js`, `cs`, `go`, `java`, `ts`, `swift`, `kotlin`, `scala`, etc.)
  - Notes: the former per-language scripts (`check_py2cpp_transpile.py` and the other ten variants) were retired and moved to `tools/unregistered/`.
- `tools/check_yanesdk_py2cpp_smoke.py`
  - Purpose: verify that the Yanesdk canonical set (`1 library + 7 games`) still passes `pytra-cli.py --target cpp`.
- `tools/check_microgpt_original_py2cpp_regression.py`
  - Purpose: keep `materials/refs/microgpt/microgpt-20260222.py` as a fixed original input and detect either the failing stage (`A` to `F`) or success.
- `tools/build_multi_cpp.py`
  - Purpose: read the `manifest.json` emitted by `pytra-cli.py --target cpp --multi-file` and build all related `*.cpp` files together with the runtime.
- `tools/gen_makefile_from_manifest.py`
  - Purpose: take `manifest.json` and generate a `Makefile` that includes `all`, `run`, and `clean`.
- `tools/verify_multi_file_outputs.py`
  - Purpose: build and run multi-file outputs from `sample/py`, then verify that the results match single-file outputs.
- `tools/check_transpiler_version_gate.py`
  - Purpose: when transpiler-related files change, verify that the corresponding component (`shared` / per-language) in `src/toolchain/misc/transpiler_versions.json` has a minor-or-greater version bump.
- `tools/regenerate_samples.py`
  - Purpose: regenerate each `sample/<lang>` from `sample/py`, and skip regeneration unless the version token in `src/toolchain/misc/transpiler_versions.json` changed.
  - Main option: `--verify-cpp-on-diff` (compile/run verification with `runtime_parity_check.py --targets cpp` only for cases that produced C++ generation diffs).
- `tools/run_regen_on_version_bump.py`
  - Purpose: launch `regenerate_samples.py` only when a minor-or-greater update in `transpiler_versions.json` is detected, and regenerate only affected languages.
- `tools/sync_todo_history_translation.py`
  - Purpose: treat `docs/ja/todo/archive` as the source of truth, synchronize the date-file skeletons and index in `docs/en/todo/archive`, and detect missed syncs with `--check`.
- `tools/check_east3_golden.py`
  - Purpose: run EAST3 snapshot tests (diff between `test/east3_fixtures/` golden files and EAST3 output). `--check-runtime-east` checks freshness of `.east` files under `src/runtime/east/`, and `--update` regenerates them.
- `tools/verify_image_runtime_parity.py`
  - Purpose: verify parity between the Python source of truth and the C++ image runtime (PNG/GIF).
- `tools/check_runtime_std_sot_guard.py`
  - Purpose: audit the operation that treats `src/pytra/std/*.py` / `src/pytra/utils/*.py` as the source of truth, enforce `src/runtime/{rs,cs}/generated/**` as the canonical generated lane for `rs/cs`, fail handwritten re-entry into the legacy `pytra-gen` lane (currently guarded: `json/assertions/re/typing`), and also verify the full responsibility boundary of C++ `std/utils` (`generated/native` ownership + required manual implementation split).
- `tools/check_runtime_core_gen_markers.py`
  - Purpose: for `rs/cs`, enforce `source/generated-by` markers in the canonical generated lane (`src/runtime/<lang>/generated/**`) while treating legacy `pytra-gen/pytra-core` only as a scan target for not-yet-migrated backends. For C++, also require markers in `src/runtime/cpp/generated/core/**`, forbid them in `src/runtime/cpp/native/core/**`, and audit marker contamination if legacy `src/runtime/cpp/core/**` reappears (based on `tools/runtime_core_gen_markers_allowlist.txt`).
  - Notes: C++ `generated/built_in` / `generated/std` / `generated/utils` are audited under the same marker contract, and increments that break the assumption that `generated/core` is a low-level pure-helper lane are stopped.
- `tools/check_runtime_pytra_gen_naming.py`
  - Purpose: validate `std|utils` placement and pass-through naming in the canonical generated lane (`src/runtime/<lang>/generated/**` for `rs/cs`, `pytra-gen/**` for unmigrated backends), and fail naming/layout violations such as `image_runtime.*` or `runtime/*.php` (based on `tools/runtime_pytra_gen_naming_allowlist.txt`).
- `tools/check_emitter_runtimecall_guardrails.py`
  - Purpose: detect increments in which non-C++ emitters hard-code runtime/stdlib function names in `if/elif` string branches, and fail anything outside the allowlist (`tools/emitter_runtimecall_guardrails_allowlist.txt`).
- `tools/check_emitter_forbidden_runtime_symbols.py`
  - Purpose: detect increments that introduce forbidden runtime implementation symbols (`__pytra_write_rgb_png` / `__pytra_save_gif` / `__pytra_grayscale_palette`) in `src/toolchain/emit/*/emitter/*.py`, and fail anything outside the allowlist (`tools/emitter_forbidden_runtime_symbols_allowlist.txt`).

### 1.1 Stop-Ship Checklist for Emitter Changes (Mandatory)

- Applies to commits that change `src/toolchain/emit/*/emitter/*.py`.
- Before committing, the following three commands must always be run.
  - `python3 tools/check_emitter_runtimecall_guardrails.py`
  - `python3 tools/check_emitter_forbidden_runtime_symbols.py`
  - `python3 tools/check_noncpp_east3_contract.py`
- If any of the three commands returns `FAIL`, treat it as Stop-Ship and do not commit, push, or request review.
- During review, confirm the following checklist items.
  - [ ] There are execution logs for the three commands above.
  - [ ] There are no increments of forbidden runtime implementation symbols in `src/toolchain/emit/*/emitter/*.py`.
  - [ ] Runtime/stdlib call resolution uses only the EAST3 source of truth (`runtime_call` / `resolved_runtime_call` / `resolved_runtime_source`).

### 1.x Golden File Generation

- `tools/generate_golden.py`
  - Purpose: use the current `toolchain/` to generate golden files for each stage (`east1` / `east2` / `east3` / `east3-opt`) under `test/` in one shot. These are the reference data used to verify whether `toolchain2/`'s own implementation matches the golden files.
  - Main options: `--stage={east1,east2,east3,east3-opt}`, `-o OUTPUT_DIR`, `--from=python`, `--sample-dir`
  - Design document: `docs/ja/plans/plan-pipeline-redesign.md` §6.1
  - Note: golden file generation must be centralized in this tool. Agents must not create golden files with ad hoc scripts.

## 2. Selfhost Related

The old selfhost tool set (`build_selfhost.py`, `prepare_selfhost_source.py`, `check_selfhost_*.py`, etc.) has already been moved to `tools/unregistered/`.

In the new pipeline (`toolchain2/`), selfhost is designed to complete within the normal build pipeline (`pytra-cli2 -build --target=cpp`), making dedicated tools unnecessary. See `docs/ja/plans/plan-pipeline-redesign.md` for details.

## 3. Cross-Language Verification

- `tools/runtime_parity_check.py`
  - Purpose: run runtime-level equalization checks across multiple target languages.
  - Notes: unstable time lines such as `elapsed_sec`, `elapsed`, and `time_sec` are excluded from comparison by default.
  - Notes: artifact comparison requires exact matches for presence + size + CRC32 on artifacts reported via `output:`.
  - Notes: before each case runs, artifacts with the same name under `sample/out`, `test/out`, and `out` are deleted to prevent stale-output mixups.
  - Notes: on timeout, the process group is killed as a unit so child processes such as `*_swift.out` are not left orphaned.
- `tools/check_all_target_sample_parity.py`
  - Purpose: run the canonical parity groups (`cpp`, `js_ts`, `compiled`, `scripting_mixed`) in order and establish sample parity across all targets.
  - Main options: `--groups`, `--east3-opt-level`, `--cpp-codegen-opt`, `--summary-dir`
- `tools/check_noncpp_backend_health.py`
  - Purpose: aggregate the post-linked-program non-C++ backend health gate by family, and report `primary_failure`, `toolchain_missing`, and family broken/green status in one command.
  - Main options: `--family`, `--targets`, `--skip-parity`, `--summary-json`
- `tools/check_noncpp_runtime_generated_cpp_baseline_contract.py`
  - Purpose: verify synchronization between the 25-module baseline derived from `cpp/generated/{built_in,std,utils}` and the legacy rollout inventory / active runtime policy wording.
- `tools/export_backend_test_matrix.py`
  - Purpose: run `test/unit/toolchain/emit/**` and shared starred smoke, then regenerate the JA/EN backend test matrix docs.
- `tools/check_scala_parity.py`
  - Purpose: run sample parity and the positive fixture manifest for Scala3 in one fixed path.
  - Main options: `--skip-fixture`, `--fixture-manifest`, `--east3-opt-level`, `--summary-dir`

### 3.1 Smoke Test Operation (After `py2x` Unification)

- The source of truth for common smoke tests (CLI success, `--east-stage 2` rejection, `load_east`, add fixture) is `test/unit/common/test_py2x_smoke_common.py`.
- Language-specific smoke suites (`test/unit/toolchain/emit/<lang>/test_py2*_smoke.py`) keep only language-specific emitter/runtime contracts, and must not reimplement common cases.
- Each language smoke suite must include a responsibility-boundary comment (`Language-specific smoke suite...`), and `tools/check_noncpp_east3_contract.py` verifies it statically.
- The source-of-truth `PYTHONPATH` for smoke execution is `src:.:test/unit`. Some smoke suites load helpers directly under `test/unit`, such as `comment_fidelity.py`, so `test/unit` must not be dropped.
- The recommended regression order is the following three commands.
- `PYTHONPATH=src:.:test/unit python3 -m unittest discover -s test/unit/common -p 'test_py2x_smoke*.py'`
- `python3 tools/check_noncpp_east3_contract.py --skip-transpile`
- `python3 tools/check_py2x_transpile.py --target <lang>` (for each target language)

### 3.2 Non-C++ Backend Health Matrix (Post Linked Program)

- Evaluate the non-C++ backend recovery baseline in the order `static_contract -> common_smoke -> target_smoke -> transpile -> parity`.
- Run `parity` only for targets that passed every earlier gate. Targets with earlier failures must not be counted as parity failures.
- Keep `toolchain_missing` separate from `parity_fail`, using the `runtime_parity_check.py` skip as the infra baseline.
- In the 2026-03-08 snapshot, Wave 1 is `js/ts` green and `rs/cs` `toolchain_missing`. Wave 2 (`go/java/kotlin/swift/scala`) and Wave 3 (`ruby/lua/php/nim`) are also `toolchain_missing` for all 18 sample parity cases.
- Daily family-level health checks are run with commands such as `python3 tools/check_noncpp_backend_health.py --family wave1`, and a family is `green` when `broken_targets == 0`.
- `toolchain_missing` does not break the family; it is shown in a separate counter.
- `tools/run_local_ci.py` includes `python3 tools/check_noncpp_backend_health.py --family all --skip-parity`, permanently placing smoke/transpile gates that do not depend on parity into daily regression.
- `tools/run_local_ci.py` also includes `python3 tools/check_jsonvalue_decode_boundaries.py`, stopping increments in which JSON artifact boundaries in selfhost/host slip back to raw `json.loads(...)`.

### 3.3 Full-Target Sample Parity Completion Condition

- The canonical parity target order is `cpp,rs,cs,js,ruby,lua,php,ts,go,java,swift,kotlin,scala,nim`. This must match the return order of `list_parity_targets()`.
- "All-target parity green" means that when running `python3 tools/runtime_parity_check.py --targets cpp,rs,cs,js,ruby,lua,php,ts,go,java,swift,kotlin,scala,nim --case-root sample --all-samples --ignore-unstable-stdout --east3-opt-level 2 --cpp-codegen-opt 3`, every target and all 18 sample cases finish as `ok` only.
- In the full-green judgment, `toolchain_missing` is not treated as an exception. The following must all be zero: `case_missing`, `python_failed`, `python_artifact_missing`, `toolchain_missing`, `transpile_failed`, `run_failed`, `output_mismatch`, `artifact_presence_mismatch`, `artifact_missing`, `artifact_size_mismatch`, `artifact_crc32_mismatch`.
- Even when checking target groups separately, the criterion stays the same.
  - baseline target: `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples --east3-opt-level 2 --cpp-codegen-opt 3`
  - JS/TS: `python3 tools/runtime_parity_check.py --targets js,ts --case-root sample --all-samples --ignore-unstable-stdout --east3-opt-level 2`
  - compiled targets: `python3 tools/runtime_parity_check.py --targets rs,cs,go,java,kotlin,swift,scala --case-root sample --all-samples --ignore-unstable-stdout --east3-opt-level 2`
  - scripting / mixed targets: `python3 tools/runtime_parity_check.py --targets ruby,lua,php,nim --case-root sample --all-samples --ignore-unstable-stdout --east3-opt-level 2`
- The canonical wrapper for daily full-target reruns is `python3 tools/check_all_target_sample_parity.py --summary-dir work/logs/all_target_sample_parity`. The wrapper runs the four groups above in order and writes the merged result to `all-target-summary.json`.

### 3.4 Debian 12 Parity Bootstrap Snapshot

- As of 2026-03-08, the current machine for the bootstrap snapshot was Debian 12 (`bookworm`) with `root`.
- Bootstrap commands for compiled targets:
  - `apt-get update`
  - `apt-get install -y rustc mono-mcs golang-go openjdk-17-jdk kotlin scala nim`
  - `apt-get install -y binutils-gold gcc git libcurl4-openssl-dev libedit-dev libpython3-dev libsqlite3-dev uuid-dev gnupg2`
  - `curl -fL -o /opt/swift-6.2.2-RELEASE-debian12.tar.gz https://download.swift.org/swift-6.2.2-release/debian12/swift-6.2.2-RELEASE/swift-6.2.2-RELEASE-debian12.tar.gz`
  - `tar -xf /opt/swift-6.2.2-RELEASE-debian12.tar.gz -C /opt`
  - `ln -sfn /opt/swift-6.2.2-RELEASE-debian12/usr/bin/swift /usr/local/bin/swift`
  - `ln -sfn /opt/swift-6.2.2-RELEASE-debian12/usr/bin/swiftc /usr/local/bin/swiftc`
- Bootstrap command for scripting / mixed targets:
  - `apt-get install -y ruby lua5.4 php-cli`
- After bootstrap, `runner_needs` is considered verified to be `OK` for `cpp,rs,cs,js,ruby,lua,php,ts,go,java,swift,kotlin,scala,nim`.

## 4. Update Rules

- When a new script is added under `tools/`, update this `docs/ja/spec/spec-tools.md` at the same time.
- Each script description must state in one line what it exists to automate.
- If there is a destructive change (argument contract change, deprecation, consolidation), also synchronize related command examples in `docs/ja/tutorial/how-to-use.md`.
- Sample regeneration is triggered not by transpiler source diffs, but by minor-or-greater updates in `src/toolchain/misc/transpiler_versions.json`.
- Commits that modify transpiler-related files (`src/py2*.py`, `src/pytra/**`, `src/toolchain/emit/**`, `src/toolchain/emit/**/profiles/**`) must pass `tools/check_transpiler_version_gate.py`.
- When sample regeneration happens because of a version bump, use `tools/run_regen_on_version_bump.py --verify-cpp-on-diff` so only the C++ cases that produced generation diffs are compile/run verified.
