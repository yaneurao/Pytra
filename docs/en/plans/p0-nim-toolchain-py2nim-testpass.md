<a href="../../ja/plans/p0-nim-toolchain-py2nim-testpass.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Install Nim Toolchain + Implement py2nim + Pass Tests

Last updated: 2026-03-03

Related TODO:
- `ID: P0-NIM-TOOLCHAIN-PY2NIM-01` in `docs/ja/todo/index.md`

Background:
- The current `main` has only a skeleton under `src/hooks/nim/`, and CLI entrypoint `src/py2nim.py` is not in place.
- The Nim path equivalent to PR #3 could not boot as-is due to import breakage (reference to `hooks.js`).
- The environment had no Nim compiler installed (`which nim` was empty), so compile/run regression checks for generated code could not be executed.

Goal:
- Install the Nim compiler in this environment and make version-pinned operation reproducible.
- Implement `py2nim.py` as an EAST3-only CLI, and make conversion/execution possible with separated Nim runtime.
- Pass Nim target tests and transpile checks under `test/`, and lock the regression path.

In scope:
- Toolchain installation procedure (Nim install / version pin / existence check)
- `src/py2nim.py`
- `src/toolchain/emit/nim/emitter/*` (if needed, migrate from `src/hooks/nim`)
- `src/runtime/nim/pytra/py_runtime.nim`
- `test/unit/test_py2nim_smoke.py` and Nim fixtures
- `tools/check_py2nim_transpile.py`

Out of scope:
- Nim backend performance optimization (benchmark improvements)
- Simultaneous completion of full-sample parity (first prioritize test path and basic executability)
- Design changes for non-Nim backends

Acceptance criteria:
- `nim --version` is executable in this environment, with reproducible installation steps recorded.
- `python3 src/py2nim.py <fixture.py> -o <out.nim>` generates `.nim` and runtime.
- `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2nim_smoke.py' -v` passes.
- `python3 tools/check_py2nim_transpile.py` passes.
- Added Nim path does not break existing major checks (at least `tools/check_py2cpp_transpile.py`).

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `nim --version`
- `python3 tools/check_py2nim_transpile.py`
- `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2nim_smoke.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

Decision log:
- 2026-03-02: Per user instruction, opened this as P0 up to Nim compiler installation, `py2nim.py` implementation, and test pass under `test/`.
- 2026-03-02: Existing `src/hooks/nim/` skeleton is reusable, but to avoid import breakage we chose to reorganize responsibilities around `src/toolchain/emit/nim/`.
- 2026-03-03: [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S1-01] Installed Nim 1.6.10 with `apt-get install -y nim`, adding `nim` command to the environment.
- 2026-03-03: [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S1-02] Verified toolchain operation with `nim --version` and `nim c -r` on `/tmp/pytra_nim_smoke.nim`.
- 2026-03-03: [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-01] Added `src/toolchain/emit/nim/emitter` and removed dependency on `src/hooks/nim` (eventually removed `src/hooks/nim` itself).
- 2026-03-03: [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-02] Implemented `src/py2nim.py` (EAST3 only / separated runtime copy / explicit stage2 rejection).
- 2026-03-03: [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-03] Wired Nim native emitter under `toolchain.emit.nim` and added `include \"py_runtime.nim\"` at the top of generated code.
- 2026-03-03: [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-04] Added `src/runtime/nim/pytra/py_runtime.nim`, providing `py_int/py_float/py_truthy/py_mod/write_rgb_png`.
- 2026-03-03: [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-01] Added `test/unit/test_py2nim_smoke.py`, reusing existing `test/fixtures/core|control|oop` to lock CLI/conversion path.
- 2026-03-03: [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-02] Added `tools/check_py2nim_transpile.py` and confirmed `checked=7 ok=7 fail=0`.
- 2026-03-03: [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-03] Ran `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2nim_smoke.py' -v` and confirmed 7 passes. Also confirmed generation/compile success with `python3 src/py2nim.py sample/py/01_mandelbrot.py -o /tmp/pytra_nim_01.nim` and `nim c /tmp/pytra_nim_01.nim`.
- 2026-03-03: [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-04] Ran `python3 tools/check_py2cpp_transpile.py` and confirmed no regression: `checked=140 ok=140 fail=0 skipped=6`.

## Breakdown

- [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S1-01] Decide Nim compiler installation method (package manager/version pin) and install in this environment.
- [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S1-02] Verify toolchain operation with `nim --version` and minimal compile run, and record reproduction steps.
- [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-01] Reorganize Nim backend implementation under `src/toolchain/emit/nim/emitter/` and remove dependency on `src/hooks/nim`.
- [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-02] Implement `src/py2nim.py` and provide CLI path satisfying EAST3-only, separated runtime copy, and fail-closed behavior.
- [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-03] Build minimum support in Nim native emitter (functions/branches/loops/key expressions) so known fixtures can be converted.
- [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-04] Build `src/runtime/nim/pytra/py_runtime.nim` and lock reference contracts from generated code.
- [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-01] Add `test/unit/test_py2nim_smoke.py` and required fixtures, and lock minimal regression for Nim path.
- [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-02] Add `tools/check_py2nim_transpile.py` to include batch transpile regression.
- [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-03] Run Nim target tests/checks, confirm pass, and record results.
- [x] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-04] Confirm no regression with existing major checks (`check_py2cpp_transpile`, etc.).
