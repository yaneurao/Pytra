<a href="../../../ja/plans/archive/20260312-p0-backends-common-foundation.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Introduce the `backends/common` Foundation (`CodeEmitter` + Profile Consolidation)

Last updated: 2026-03-03

Related TODO:
- `ID: P0-BACKENDS-COMMON-FOUNDATION-01` in `docs/ja/todo/index.md`

Background:
- The shared base `CodeEmitter` / `EmitterHooks` currently live in `src/pytra/compiler/east_parts/code_emitter.py`, which crosses backend responsibility boundaries.
- Profile JSON is consolidated under `src/profiles/*`, while backend implementations live under `src/backends/<lang>/*`, resulting in duplicated placement conventions.
- As backend code is being organized around `lower / optimizer / emitter`, there is no explicit home for shared infrastructure, so import paths and maintenance flow are fragmented.

Goal:
- Introduce `src/backends/common/` as the canonical location for shared backend infrastructure.
- Consolidate `CodeEmitter` / `EmitterHooks` and shared profile assets into `backends/common`, and make responsibility boundaries explicit.
- Move language-specific profiles to `src/backends/<lang>/profiles/` to increase backend self-containment.

In scope:
- Add `src/backends/common/` (`emitter`, `profiles`, and required helper modules)
- Move `CodeEmitter` / `EmitterHooks` / profile JSON (shared + language-specific)
- Update import paths (`src/backends/**`, `src/py2*.py`, `tools/**`, `test/**`)
- Update spec docs (folder responsibility boundaries and profile placement conventions)

Out of scope:
- Backend feature additions or optimization logic changes
- EAST spec changes
- Runtime API spec changes

Acceptance criteria:
- Canonical imports for `CodeEmitter` / `EmitterHooks` are unified under `src/backends/common/**`.
- Direct references to `src/profiles/` are removed, and profiles are organized under `src/backends/common/profiles` and `src/backends/<lang>/profiles`.
- Major `py2*` transpile checks pass with no regressions.
- `backends/common` and profile placement rules are reflected in `docs/ja/spec` (and `docs/en/spec` when needed).

Verification commands (planned):
- `python3 tools/check/check_todo_priority.py`
- `rg -n "pytra\\.compiler\\.east_parts\\.code_emitter|src/profiles/" src tools test`
- `python3 tools/check/check_py2cpp_transpile.py`
- `python3 tools/check/check_py2rs_transpile.py`
- `python3 tools/check/check_py2cs_transpile.py`
- `python3 tools/check/check_py2go_transpile.py`
- `python3 tools/check/check_py2java_transpile.py`
- `python3 tools/check/check_py2swift_transpile.py`
- `python3 tools/check/check_py2kotlin_transpile.py`
- `python3 tools/check/check_py2rb_transpile.py`
- `python3 tools/check/check_py2lua_transpile.py`
- `python3 tools/check/check_py2scala_transpile.py`
- `python3 tools/check/check_py2nim_transpile.py`

## Breakdown

- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S1-01] Inventory current placements and reference points for shared assets (`CodeEmitter` / hooks / profile loader / profile JSON).
- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S1-02] Define placement conventions and dependency direction for `backends/common` and `backends/<lang>/profiles`.
- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S2-01] Create `src/backends/common` and relocate `CodeEmitter` / `EmitterHooks`.
- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S2-02] Move `src/profiles/common/*` to `src/backends/common/profiles/*`.
- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S2-03] Move `src/profiles/<lang>/*` to `src/backends/<lang>/profiles/*` and update references.
- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S2-04] Add compatibility shims for legacy import paths (minimum necessary) to prevent breakage during phased migration.
- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S3-01] Remove remaining direct references to `src/profiles/` and legacy `code_emitter` references via `rg` audit.
- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S3-02] Run major transpile checks and verify no regressions caused by the refactor.
- [x] [ID: P0-BACKENDS-COMMON-FOUNDATION-01-S3-03] Reflect responsibility boundaries and folder conventions in `docs/ja/spec` (and `docs/en/spec` if needed).

Decision log:
- 2026-03-03: Per user direction, we reviewed the split placement of `src/profiles` and `CodeEmitter` and finalized introducing `backends/common` as top priority (P0).
- 2026-03-03: Moved the canonical `CodeEmitter` / `EmitterHooks` implementation to `src/backends/common/emitter/code_emitter.py`; converted legacy `src/pytra/compiler/east_parts/code_emitter.py` into a compatibility shim.
- 2026-03-03: Relocated profile JSON to `src/backends/common/profiles` and `src/backends/{cpp,rs,cs,js}/profiles`, and updated references across emitters, tests, and version-gate checks.
- 2026-03-03: Confirmed by `rg` audit that no direct references remain to `src/profiles` or legacy `code_emitter` imports; also confirmed passing results for `check_py2{cpp,rs,cs,js,go,java,swift,kotlin,rb,lua,scala,ts,nim}_transpile.py` and `check_transpiler_version_gate.py`.
- 2026-03-03: Updated `docs/ja/spec` / `docs/en/spec` references from `src/profiles`, `src/common`, and legacy `code_emitter` to `src/backends/**/profiles`, `src/backends/common`, and the new `code_emitter` path, synchronizing responsibility-boundary descriptions with current implementation.
