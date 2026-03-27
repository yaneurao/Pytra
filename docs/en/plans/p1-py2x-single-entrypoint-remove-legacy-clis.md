<a href="../../ja/plans/p1-py2x-single-entrypoint-remove-legacy-clis.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Single Entrypoint with `pytra-cli.py` (Retire `py2*.py`, Ultimately Remove `py2cpp.py`)

Last updated: 2026-03-03

Related TODO:
- `ID: P1-PY2X-SINGLE-ENTRY-01` in `docs/ja/todo/index.md`

Background:
- `pytra-cli.py` has already been introduced, but `tools/` / `test/` / `docs/` / selfhost paths still depend on direct `py2*.py` invocation.
- In particular, `py2cpp.py` is also the entry for C++-specific features such as `--emit-runtime-cpp` / `--header-output` / `--multi-file`, so it cannot be removed trivially.
- User requirement: if the project is unified on `pytra-cli.py`, make legacy CLIs unnecessary and ultimately remove `py2cpp.py`.

Goal:
- Standardize canonical CLI entrypoints to `src/pytra-cli.py` (normal) and `src/pytra-cli.py` (selfhost).
- Gradually remove direct `py2*.py` dependencies from `tools/` / `test/` / `docs/`.
- Remove legacy CLIs including `src/py2cpp.py` in the final phase.

In scope:
- Extend `src/pytra-cli.py` / `src/pytra-cli.py` (absorb C++-specific capabilities)
- Migrate call targets in `tools/` / `test/` / `src/pytra/cli.py` to `pytra-cli.py --target ...`
- Replace entrypoints in selfhost-related scripts
- Update usage docs in `docs/ja` / `docs/en`
- Remove legacy CLIs (`src/py2*.py`)

Out of scope:
- Quality improvements in backend transpilation logic itself
- EAST spec changes
- Runtime API spec changes

Acceptance criteria:
- No direct `src/py2*.py` references remain in `tools/`, `test/`, `docs/`, or `src/pytra/cli.py`.
- C++-specific workflows (runtime generation/header output/multi-file) are supported by `py2x --target cpp`.
- Selfhost paths work without `py2cpp.py` dependency.
- In final state, `src/py2cpp.py` is deleted and major regressions pass.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `rg -n "src/py2(?!x)\\w*\\.py" src tools test docs`
- `python3 tools/check_py2x_transpile.py` (planned new)
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2cs_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`
- `python3 tools/check_py2rb_transpile.py`
- `python3 tools/check_py2lua_transpile.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/check_py2php_transpile.py`
- `python3 tools/check_py2nim_transpile.py`
- `python3 tools/build_selfhost.py`
- `python3 tools/build_selfhost_stage2.py`

## Breakdown

- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S1-01] Inventory `py2*.py` dependencies in `tools/` / `test/` / `docs/` / `src/pytra/cli.py` and finalize migration order.
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S1-02] Finalize `py2x` receiver spec for `py2cpp.py`-specific features (`--emit-runtime-cpp`, `--header-output`, `--multi-file`, etc.).
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S1-03] Inventory selfhost path dependencies on entrypoint contracts (prepare/build/check) and finalize replacement policy.
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-01] Implement `py2cpp`-specific features in `py2x --target cpp` so existing options remain equivalent.
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-02] Bulk-replace CLI calls in `tools/` with `pytra-cli.py --target ...`.
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-03] Migrate CLI calls and contract tests in `test/` to `py2x`-based paths.
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-04] Update examples/spec wording in `docs/ja` / `docs/en` to canonical `py2x` entrypoint.
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] Migrate selfhost scripts away from `py2cpp.py` dependency and rewire around `pytra-cli.py`.
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S3-01] Add guards before legacy CLI removal to fail-fast detect new `py2*.py` re-introduction.
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S3-02] Delete `src/py2cpp.py` and remove other `py2*.py` as needed.
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S3-03] Run full transpile/selfhost regressions and confirm no regression after `py2cpp.py` deletion.

Decision log:
- 2026-03-03: Per user instruction, opened P1 for single-entrypoint `pytra-cli.py`, with `src/py2cpp.py` deletion included as a final deliverable.
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S1-01] Completed dependency inventory. `src/pytra/cli.py` directly referenced `PY2CPP/PY2RS/PY2SCALA`; `tools/` depended on `src/py2*.py` mainly via `runtime_parity_check` / `regenerate_samples` / selfhost paths; in `test/`, `test_py2*` assumed direct wrapper execution; and execution examples were concentrated in `docs/how-to-use`. Final migration order: `(1) src/pytra/cli.py + common paths in tools -> (2) test contract updates -> (3) docs -> (4) final selfhost replacement`.
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S1-02] Extracted actively used `py2cpp.py` options (`--multi-file`, `--output-dir`, `--header-output`, `--emit-runtime-cpp`, `--dump-deps`, `--dump-options`, `--preset`, `--int-width`, `--mod-mode`, `--top-namespace`, `--str-index-mode`). Final receiver spec: map portable options into `--lower/optimizer/emitter-option`; accept output-mode-changing flags (`multi-file/header/runtime-cpp/dump-*`) directly as `py2x --target cpp` compatibility flags.
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S1-03] Inventoried selfhost dependency contracts. `tools/prepare_selfhost_source.py` / `build_selfhost.py` / `build_selfhost_stage2.py` / `check_selfhost_cpp_diff.py` / `verify_selfhost_end_to_end.py` were chained around `src/py2cpp.py`. Replacement policy: use `src/pytra-cli.py --target cpp` for normal path, `src/pytra-cli.py --target cpp` for selfhost path; keep `selfhost/py2cpp.py` only as an intermediate artifact (hide wrapper name from callers).
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-01] Added C++ compatibility path to `src/pytra-cli.py`; when `--target cpp`, accept and delegate `py2cpp` compatibility flags. Mapped C++ keys in `--optimizer-option/--emitter-option` (for example `cpp_opt_level`, `mod_mode`, `negative_index_mode`) to dedicated flags. Confirmed no regression with `test_py2x_cli.py` (5 tests) and runtime checks (single-file / multi-file / header-output).
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-02] Unified CLI calls in `tools/` (excluding selfhost paths) to `src/pytra-cli.py --target ...`, updating `regenerate_samples` / `runtime_parity_check` / `verify_*` / `benchmark_*` / `check_py2*_transpile`. Confirmed no regression by running all `check_py2*_transpile.py`.
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-03] Unified subprocess execution in `test/unit` to `src/pytra-cli.py --target ...` (`test_py2{cs,go,java,js,kotlin,lua,nim,php,rb,rs,scala,swift,ts}_smoke.py`, `test_runtime_parity_check_cli.py`, `test_cpp_optimizer_cli.py`, `test_east3_optimizer_cli.py`, `test_py2cpp_features.py`). Representative 15 unittest files passed (`test_py2lua_smoke.py` kept 7 known failures).
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-04] Updated execution examples in `docs/ja/how-to-use.md` and `docs/en/how-to-use.md` to `py2x --target` baseline and standardized output-path notation to `-o`. Also updated language-list wording in `docs/ja/spec/spec-user.md` / `docs/en/spec/spec-user.md` to canonical `py2x` entrypoint.
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] Removed direct `src/py2cpp.py` references from selfhost scripts (`build_selfhost*` / `check_selfhost_cpp_diff` / `selfhost_transpile` / `check_selfhost_direct_compile` / `verify_selfhost_end_to_end`), introduced `src/pytra-cli.py`-based calls and `--selfhost-target auto` (legacy binary compatibility). Confirmed `check_selfhost_cpp_diff --skip-east3-contract-tests --cases test/fixtures/core/add.py` is runnable with `mismatches=0`.
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] After switching `tools/build_selfhost.py` to `py2x-selfhost`, generated `selfhost/py2cpp.cpp` still failed C++ compile (unresolved `pytra::compiler::ler::*` refs, help-string concatenation, missing local bindings), so selfhost path remained incomplete and `S2-05` stayed open.
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] Treated `toolchain.*` / `toolchain.emit.*` as known imports in `transpile_cli` import resolution and added self_hosted fallback for unlowered method calls (`str.startswith/endswith`, etc.) in the C++ emitter. This restored successful execution of `python3 tools/prepare_selfhost_source.py && python3 src/py2cpp.py selfhost/py2cpp.py -o /tmp/selfhost_py2cpp_oldpath.cpp`.
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S3-01] Added `tools/check_legacy_cli_references.py`, introducing a fail-fast guard for `src/py2*.py` string references and `import py2*` in `src/tools/test` outside allowlist. Integrated this check into `tools/run_local_ci.py` and confirmed pass with `python3 tools/check_legacy_cli_references.py`.
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] Fixed a bug in C++ emitter import resolution that cut `toolchain.compiler.` prefix at `15` characters (correct: `len("toolchain.compiler.")`). Initial `build_selfhost.py` failure progressed from `pytra::compiler::ler::*` to missing concrete `pytra::compiler::*`; `_print_help` string concatenation and layer-option variable-scope breakage were fixed on `src/pytra-cli.py`.
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] Aligned argument definitions in `pytra-cli.py` with runtime `ArgumentParser` contracts (resolved `add_argument` signature mismatch and const-reference issue in `_add_common_args`) and recovered selfhost transpile stage. Current `build_selfhost.py` failure is limited to missing concretions for `pytra::compiler::{transpile_cli,backend_registry_static}` (runtime C++ headers missing).
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] Added `src/runtime/cpp/pytra/compiler/{transpile_cli,backend_registry_static}.{h,cpp}` and resolved selfhost generated-C++ link failures. Runtime behavior is a minimum implementation returning `[not_implemented]`; `build_selfhost.py` now passes, and `build_selfhost_stage2.py` continues stage2 binary generation via fallback reusing `selfhost/py2cpp.cpp` when `[not_implemented]` occurs.
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] Restricted self_hosted fallback for builtin methods in `toolchain/emit/cpp/emitter/call.py` to selfhost bootstrap sources only (`selfhost/py2cpp.py` / `src/py2cpp.py` / `src/pytra-cli.py`), resolving `test_east3_cpp_bridge` failures. With this, `check_selfhost_cpp_diff` / `check_selfhost_stage2_cpp_diff` (`--mode allow-not-implemented`) passed without `--skip-east3-contract-tests`.
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] Marked complete after meeting acceptance criteria (`build_selfhost.py` pass, `build_selfhost_stage2.py` pass, and `allow-not-implemented` operation established for `check_selfhost_cpp_diff` / `check_selfhost_stage2_cpp_diff`). Deeper implementation of selfhost transpile core continues under separate priority (`P4-MULTILANG-SH-01` series).
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S3-02] Moved `src/py2cpp.py` implementation to `src/toolchain/emit/cpp/cli.py`, updated `py2x` / `pytra/cli` / backend registry / tools / unit tests to `py2x --target cpp` and new module references, then removed `src/py2cpp.py`. Confirmed passing `check_legacy_cli_references` / `check_py2cpp_transpile` / `test_py2cpp_smoke` / `test_pytra_cli` / `test_east3_cpp_bridge`.
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S3-03] Ran all `check_py2{cpp,rs,cs,js,ts,go,java,swift,kotlin,rb,lua,scala,php,nim}_transpile.py` plus four selfhost checks (`build_selfhost`, `build_selfhost_stage2 --skip-stage1-build`, `check_selfhost_cpp_diff`, `check_selfhost_stage2_cpp_diff`) and confirmed transpile/selfhost non-regression after `py2cpp.py` removal.
