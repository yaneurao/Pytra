# P0: Split `py2x` Entrypoints (Normal `py2x.py` / Self-host `py2x-selfhost.py`)

Last updated: 2026-03-03

Related TODO:
- `ID: P0-PY2X-DUAL-ENTRYPOINT-01` in `docs/ja/todo/index.md`

Background:
- For normal execution, we want lazy import of only the target backend; for self-host execution, dynamic import is unavailable and static import is required.
- If one entrypoint tries to satisfy both at once, self-host-incompatible code (for example conditional imports) tends to leak in.
- We need role separation: one entrypoint for normal execution and one for self-host execution.

Goal:
- Clarify `py2x.py` as normal-execution-only (host, lazy import).
- Split out `py2x-selfhost.py` as self-host-only (static eager import) and lock self-host compatibility.
- Keep existing `py2*.py` wrappers on normal path (`py2x.py`) to minimize behavior diffs.

In scope:
- `src/py2x.py` (normal path)
- `src/py2x-selfhost.py` (new)
- Lazy/eager configuration of backend registry
- Self-host execution path (minimal only)
- Docs (entrypoint usage policy)

Out of scope:
- Backend output-quality improvements
- Runtime API spec changes
- Full-scale remediation of all self-host failure cases

Acceptance criteria:
- Normal usage uses `py2x.py` with target-based lazy import enabled.
- Self-host usage uses `py2x-selfhost.py`, works with static imports only, and includes no dynamic import.
- Existing normal usage path via `py2*.py` wrappers remains non-regressed.
- Docs clearly describe normal/self-host entrypoint usage split.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p test_py2x_cli.py`
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2php_transpile.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/check_py2nim_transpile.py`

## Breakdown

- [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S1-01] Audit current `py2x` path constraints and ownership boundaries for normal execution / self-host execution.
- [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S1-02] Define contracts (allowed/prohibited items) for `py2x.py` (host) and `py2x-selfhost.py` (self-host).
- [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S2-01] Refactor `py2x.py` into host-lazy-only implementation (remove self-host conditional branches).
- [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S2-02] Add `py2x-selfhost.py` and provide equivalent CLI using static eager imports only.
- [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S2-03] Split backend-registry dependency between host/self-host and make boundary violations detectable.
- [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S3-01] Run unit/transpile regressions and confirm no regressions on normal path.
- [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S3-02] Run smoke/minimal regressions on self-host path and confirm no dependency on dynamic import.
- [x] [ID: P0-PY2X-DUAL-ENTRYPOINT-01-S3-03] Update docs with usage split and migration procedure.

Decision log:
- 2026-03-03: Adopted two-track split policy: normal uses `py2x.py` (lazy), self-host uses `py2x-selfhost.py` (static).
- 2026-03-03: Current-state audit confirmed `src/py2x.py` depends on `pytra.compiler.backend_registry` (eager import of all backends), and `py2*.py` wrappers share the normal path via `pytra.compiler.py2x_wrapper.run_py2x_for_target`.
- 2026-03-03: Fixed contract as follows. Host (`py2x.py`): dynamic import allowed, target-scoped lazy import required. Self-host (`py2x-selfhost.py`): dynamic import prohibited, only static eager import allowed. CLI contract (`--target`, layer options, EAST3 fixed) remains identical for both.
- 2026-03-03: Replaced `src/pytra/compiler/backend_registry.py` with host-lazy registry using `importlib.import_module` + target-specific loader + `_SPEC_CACHE` to lazy-load only required backend. Separated prior eager registry as `src/pytra/compiler/backend_registry_static.py`.
- 2026-03-03: Added `src/py2x-selfhost.py` and introduced self-host-only entrypoint referencing `backend_registry_static`. Fixed `src/py2x.py` to normal path using `backend_registry` (host-lazy).
- 2026-03-03: To avoid import cycles, removed package-level re-export of `east1_build` from `src/pytra/compiler/east_parts/__init__.py` and allowed explicit imports only.
- 2026-03-03: Added `test/unit/test_py2x_entrypoints_contract.py` for boundary-violation detection, and locked unit checks for `py2x`/`py2x-selfhost` registry binding, host-registry lazy import behavior, target-limited import, and spec cache usage.
- 2026-03-03: Ran and passed the following regressions: `test_py2x_cli.py`, `test_py2x_entrypoints_contract.py`, `check_py2{rs,js,php,scala,nim}_transpile.py`, `check_noncpp_east3_contract.py --skip-transpile`, `check_transpiler_version_gate.py --base-ref HEAD`.
- 2026-03-03: Added usage split for `py2x.py` / `py2x-selfhost.py` (normal=host-lazy, self-host=static eager) to `docs/ja/how-to-use.md` and `docs/en/how-to-use.md`.
