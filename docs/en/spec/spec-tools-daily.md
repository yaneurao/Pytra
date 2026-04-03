<a href="../../ja/spec/spec-tools-daily.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# `tools/` — Daily Operation Tools

[Back to index](./spec-tools.md)

## 1. Regression Checks and Verification

- `tools/run/run_local_ci.py`
  - Purpose: Run the local minimum CI suite in one shot (version gate + todo priority guard + runtime layer split guard + non-C++ emitter runtime-call hardcoding guard + emitter forbidden runtime implementation symbol guard + non-C++ backend health gate + conditional sample regeneration + transpile regression + unit tests + selfhost build + diff).
- `tools/check/check_tools_ledger.py`
  - Purpose: Verify that every script in `tools/check/`, `tools/gen/`, and `tools/run/` is listed in the `tools/README.md` ledger, and fail any file not in the ledger. Also fails if a `.py` file is placed directly under `tools/`.
- `tools/check/check_mapping_json.py`
  - Purpose: Validate `src/runtime/<lang>/mapping.json` for all languages (valid JSON, presence of `calls` key, presence of `builtin_prefix`, presence of required entry `env.target`, no empty-string entries). Included in `run_local_ci.py`.
- `tools/check/check_jsonvalue_decode_boundaries.py`
  - Purpose: Verify that `json.loads_obj(...)` is the canonical call at JSON artifact boundaries in `pytra-cli.py` / `east2x.py` / `toolchain/compile/east_io.py` / `toolchain/link/*`, and fail fast on any reintroduction of raw `json.loads(...)`.
- `tools/check/check_py2x_transpile.py`
  - Purpose: Batch-convert `test/fixtures/` and `sample/py` using `pytra-cli.py --target <lang>` and detect failing cases. This is the unified transpile checker for all languages.
  - Main options: `--target <lang>` (`cpp`, `rs`, `js`, `cs`, `go`, `java`, `ts`, `swift`, `kotlin`, `scala`, etc.)
  - Note: The former per-language scripts (`check_py2cpp_transpile.py` and 9 others) have been retired and deleted.
- `tools/check/check_east3_golden.py`
  - Purpose: EAST3 snapshot tests (diff between golden files in `test/east3_fixtures/` and the EAST3 output). `--check-runtime-east` checks the freshness of `.east` files under `src/runtime/east/`. `--update` regenerates them.
- `tools/check/verify_image_runtime_parity.py`
  - Purpose: Verify parity between the Python source of truth and the C++ image runtime (PNG/GIF).
- `tools/check/check_runtime_std_sot_guard.py`
  - Purpose: Audit that `src/pytra/std/*.py` / `src/pytra/utils/*.py` are treated as the source of truth; enforce `src/runtime/{rs,cs}/generated/**` as the canonical generated lane for `rs/cs`; fail handwritten re-entry into the legacy `pytra-gen` lane (currently guarded: `json/assertions/re/typing`). Also verifies the full responsibility boundary of C++ `std/utils` (`generated/native` ownership + required manual implementation split).
- `tools/check/check_runtime_core_gen_markers.py`
  - Purpose: For `rs/cs`, enforce `source/generated-by` markers in the canonical generated lane (`src/runtime/<lang>/generated/**`) while treating legacy `pytra-gen/pytra-core` only as a scan target for unmigrated backends. For C++, also require markers in `src/runtime/cpp/generated/core/**`, forbid them in `src/runtime/cpp/native/core/**`, and audit marker contamination if legacy `src/runtime/cpp/core/**` reappears (based on `tools/runtime_core_gen_markers_allowlist.txt`).
  - Note: C++ `generated/built_in` / `generated/std` / `generated/utils` are audited under the same marker contract, and increments that break the `generated/core` low-level-pure-helper-lane assumption are stopped.
- `tools/check/check_runtime_pytra_gen_naming.py`
  - Purpose: Validate `std|utils` placement and pass-through naming in the canonical generated lane (`src/runtime/<lang>/generated/**` for `rs/cs`, `pytra-gen/**` for unmigrated backends); fail naming/layout violations like `image_runtime.*` / `runtime/*.php` (based on `tools/runtime_pytra_gen_naming_allowlist.txt`).
- `tools/check/check_emitter_runtimecall_guardrails.py`
  - Purpose: Detect increments where non-C++ emitters hardcode runtime/stdlib function names in `if/elif` string branches, and fail anything outside the allowlist (`tools/emitter_runtimecall_guardrails_allowlist.txt`).
- `tools/check/check_emitter_forbidden_runtime_symbols.py`
  - Purpose: Detect increments that introduce forbidden runtime implementation symbols (`__pytra_write_rgb_png` / `__pytra_save_gif` / `__pytra_grayscale_palette`) in `src/toolchain/emit/*/emitter/*.py`, and fail anything outside the allowlist (`tools/emitter_forbidden_runtime_symbols_allowlist.txt`).
- `tools/gen/gen_makefile_from_manifest.py`
  - Purpose: Take a `manifest.json` and generate a `Makefile` that includes `all`, `run`, and `clean` targets.
- `tools/gen/regenerate_samples.py`
  - Purpose: Regenerate each `sample/<lang>` from `sample/py`.
  - Main option: `--verify-cpp-on-diff` (compile/run verification via `runtime_parity_check.py --targets cpp` for only the cases that produced C++ generation diffs)
- `tools/run/run_regen_on_version_bump.py`
  - Purpose: Regenerate samples and re-run only affected languages.
- `tools/run/sync_todo_history_translation.py`
  - Purpose: Treat `docs/ja/todo/archive` as the source of truth, synchronize date-file skeletons and the index in `docs/en/todo/archive`, and detect missed syncs with `--check`.

## 2. Emitter Change Stop-Ship Checklist (Required)

- Applies to: commits that modify `src/toolchain/emit/*/emitter/*.py`.
- Before committing, always run the following 3 commands:
  - `python3 tools/check/check_emitter_runtimecall_guardrails.py`
  - `python3 tools/check/check_emitter_forbidden_runtime_symbols.py`
  - `python3 tools/check/check_noncpp_east3_contract.py`
- If any of the 3 commands returns `FAIL`, treat it as Stop-Ship: committing, pushing, and requesting review are all prohibited.
- During review, confirm the following 3 checklist items:
  - [ ] Execution logs for the 3 commands above are present.
  - [ ] There are no increments of forbidden runtime implementation symbols in `src/toolchain/emit/*/emitter/*.py`.
  - [ ] Runtime/stdlib call resolution uses only the EAST3 source of truth (`runtime_call` / `resolved_runtime_call` / `resolved_runtime_source`).

## 3. Build and Generation

- `tools/gen/gen_makefile_from_manifest.py`
  - Purpose: Take a `manifest.json` and generate a `Makefile` including `all`, `run`, and `clean`.
- `tools/gen/regenerate_samples.py`
  - Purpose: Regenerate each `sample/<lang>` from `sample/py`.
  - Main option: `--verify-cpp-on-diff` (compile/run verification via `runtime_parity_check.py --targets cpp` for only the cases that produced C++ generation diffs)
- `tools/run/run_regen_on_version_bump.py`
  - Purpose: Regenerate samples and re-run only the affected languages.
- `tools/run/sync_todo_history_translation.py`
  - Purpose: Treat `docs/ja/todo/archive` as the source of truth, synchronize date-file skeletons and the index in `docs/en/todo/archive`, and detect missed syncs with `--check`.

## 4. Golden File Generation

- `tools/gen/generate_golden.py`
  - Purpose: Use the current `toolchain/` to batch-generate golden files for each stage (east1 / east2 / east3 / east3-opt) under `test/`. These are the reference data for verifying whether `toolchain2/`'s own implementation matches.
  - Main options: `--stage={east1,east2,east3,east3-opt}`, `-o OUTPUT_DIR`, `--from=python`, `--sample-dir`
  - Design document: `docs/ja/plans/plan-pipeline-redesign.md` §6.1
  - Note: Golden file generation must be centralized in this tool. Individual agents must not generate golden files with their own scripts.
