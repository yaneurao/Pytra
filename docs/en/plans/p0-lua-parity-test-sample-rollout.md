# P0: Full Lua parity completion (test/fixture + sample)

Last updated: 2026-03-01

Related TODO:
- `ID: P0-LUA-PARITY-ALL-01` in `docs/ja/todo/index.md`
- Dependency: `ID: P0-LUA-SAMPLE01-RUNTIME-01` (resolve runtime gaps in sample/01)

Background:
- User requirement prioritizes parity-match verification for Lua on both `test/` and `sample/`.
- Current Lua parity history mixes checks from `toolchain_missing` environments, and lacks a full-run record under an available execution environment.
- Also, `sample/lua/01` still has runtime-mapping gaps (`perf_counter`/`png`), which can block parity for all samples.

Goal:
- For the Lua backend, complete parity runs in an available execution environment for fixtures (`test/fixtures`) and samples (`sample/py`), and lock output matching.
- Besides stdout match, continuously verify artifact size matching for image-output cases.

Scope:
- `tools/runtime_parity_check.py`
- `test/unit/test_runtime_parity_check_cli.py` (if needed)
- `test/unit/test_py2lua_smoke.py`
- `src/hooks/lua/emitter/lua_native_emitter.py` (fixes for parity mismatches)
- `src/runtime/lua/*` (if needed)
- `sample/lua/*.lua` (regeneration checks)

Out of scope:
- Performance optimization for Lua backend
- Readability improvements of Lua syntax (handled in a separate task)
- Parity improvements for other language backends

Acceptance criteria:
- Confirm no increase in known failures (14 stdlib/imports cases) in `check_py2lua_transpile.py`.
- Fixture parity (`test/` root) fully passes for the executable target set on Lua.
- Sample parity (18 `sample/py` cases) fully passes under `--targets lua --all-samples`.
- `artifact_size_mismatch` is 0 in image-output cases.
- Record results in the plan decision log and lock recurrence-detection pipeline (unit/CLI).

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2lua_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2lua*.py' -v`
- `python3 tools/runtime_parity_check.py --case-root fixture --targets lua --ignore-unstable-stdout`
- `python3 tools/runtime_parity_check.py --case-root sample --targets lua --all-samples --ignore-unstable-stdout`
- `python3 tools/regenerate_samples.py --langs lua --force`

Breakdown:
- [x] [ID: P0-LUA-PARITY-ALL-01-S1-01] Finalize Lua parity scope (fixture target cases / all 18 samples) and lock execution procedure.
- [x] [ID: P0-LUA-PARITY-ALL-01-S1-02] Resolve unresolved items in dependency task `P0-LUA-SAMPLE01-RUNTIME-01` and remove sample parity blockers.
- [x] [ID: P0-LUA-PARITY-ALL-01-S2-01] Run `runtime_parity_check --case-root fixture --targets lua`, fix mismatches, and reach all pass.
- [x] [ID: P0-LUA-PARITY-ALL-01-S2-02] Run `runtime_parity_check --case-root sample --targets lua --all-samples`, fix mismatches, and reach all pass.
- [x] [ID: P0-LUA-PARITY-ALL-01-S2-03] Confirm artifact-size match for image cases (`artifact_size_mismatch=0`) and complete required runtime/emitter fixes.
- [x] [ID: P0-LUA-PARITY-ALL-01-S3-01] Record parity execution results in the decision log, and add unit/CLI regressions (if needed) to lock recurrence detection.

Decision log:
- 2026-03-01: By user instruction, filed P0 task to verify Lua parity match on both `test/` (fixture) and `sample/`.
- 2026-03-01: Finalized target scope as `fixture: math_extended/pathlib_extended` (cases currently handled by runtime_parity) and `sample: all 01..18`.
- 2026-03-01: Confirmed dependency task (sample/01 runtime mapping) was completed, and judged runtime-gap blockers (`perf_counter/png`) for sample parity as resolved.
- 2026-03-01: Fixed fixture parity mismatches:
  - Added `py_assert_all/py_assert_eq/py_assert_true` imports to Lua runtime mapping.
  - Added `math` compatibility helpers (`fabs/log10/pow`).
  - Added minimal `pathlib.Path` runtime (`/`, `mkdir`, `exists`, `write_text`, `read_text`, `name/stem/parent`).
  - Adjusted `print` to Python-compatible representation (`True/False/None`).
  - Added `break/continue` lowering (`break` / `goto continue_label`), fixed attribute `AnnAssign`, and corrected `main` guard call.
- 2026-03-01: `python3 tools/runtime_parity_check.py --case-root fixture --targets lua --ignore-unstable-stdout` passed (2/2).
- 2026-03-01: `python3 tools/runtime_parity_check.py --case-root sample --targets lua --all-samples --ignore-unstable-stdout` was incomplete (pass=3, fail=15).
  - Incomplete breakdown: 12 transpile failures due to unimplemented `pytra.runtime/pytra.utils gif`, and run failures for `18_mini_language_interpreter` due to missing Lua features (`enumerate`, etc.).
- 2026-03-01: Updated Lua emitter and resolved sample parity blockers:
  - Unified Python truthiness (`while xs:`/`if xs:`) to `__pytra_truthy(...)`.
  - Lowered `dict.get(key, default)` into Lua expressions with nil checks.
  - Added `str.isdigit/isalpha/isalnum` helpers.
  - Lowered `In/NotIn` into `__pytra_contains(...)`.
  - Normalized constant/dynamic negative indexing (including `[-1]`) into Lua indexing.
  - Initialized fields in dataclass (`ClassDef(dataclass=True)`) `new(args)`.
  - Lowered `str + str` to Lua concatenation `..`.
- 2026-03-01: `python3 tools/runtime_parity_check.py --case-root fixture --targets lua --ignore-unstable-stdout` passed (2/2, fail=0).
- 2026-03-01: `python3 tools/runtime_parity_check.py --case-root sample --targets lua --all-samples --ignore-unstable-stdout` passed (18/18, fail=0).
- 2026-03-01: Confirmed `category_counts={'ok': 18}` in summary JSON (`out/lua_sample_parity_summary.json`), satisfying `artifact_size_mismatch=0`.
- 2026-03-01: `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2lua_smoke.py' -v` passed (32 tests, 0 fail).
- 2026-03-01: `python3 tools/check_py2lua_transpile.py` returned `checked=103 ok=89 fail=14 skipped=39` (known stdlib/imports failures), with no new failures introduced by these changes.
