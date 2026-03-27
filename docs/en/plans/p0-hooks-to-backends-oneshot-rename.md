<a href="../../ja/plans/p0-hooks-to-backends-oneshot-rename.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Bulk Rename `src/hooks` -> `src/backends` (Highest Priority)

Last updated: 2026-03-03

Related TODO:
- `ID: P0-HOOKS-TO-BACKENDS-RENAME-01` in `docs/ja/todo/index.md`

Background:
- The current `src/hooks/` does not contain hook snippets in practice; it contains the actual backend implementations for each language (lower/optimizer/emitter/extensions).
- This naming/implementation mismatch has caused duplicated expressions like `hooks/<lang>/hooks` and confusion about ownership.
- Per user instruction, we will not do phased migration; we will do a one-shot rename to `src/toolchain/emit/` and converge as top priority.

Goal:
- Standardize the canonical backend implementation path to `src/toolchain/emit/<lang>/` and remove ambiguity from the `hooks` name.
- Update existing imports/CLI/tests/docs in the same change so no rename-origin breakage remains.

In scope:
- Directory move: `src/hooks/** -> src/toolchain/emit/**`
- Import reference updates: `src/py2*.py`, `src/pytra/**`, `tools/**`, `test/**`
- Spec/usage docs updates: `docs/ja/spec/*`, `docs/en/spec/*`, `docs/ja/how-to-use.md`, `docs/en/how-to-use.md`
- Temporary compatibility layer as needed (`src/hooks`-side re-export), short-lived only

Out of scope:
- Adding backend features or changing optimization behavior
- EAST spec changes
- Runtime API semantic changes

Acceptance criteria:
- `src/toolchain/emit/<lang>/` becomes the only canonical location for backend implementations.
- Imports in the repository reference `toolchain.emit.*` in principle, with no remaining direct `hooks.*` references (except intentional compatibility layers).
- Major `py2*.py` CLIs and `check_py2*_transpile.py` pass without regression.
- Specs are updated to `backends` responsibilities, and `hooks` is clearly documented as compatibility/deprecation scope.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `rg -n "from hooks\\.|import hooks\\." src test tools`
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

## Breakdown

- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S1-01] Inventory the current `src/hooks/**` structure and finalize the 1:1 move map to `src/toolchain/emit/**`.
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S1-02] Enumerate all import reference points impacted by the rename (`src/`, `tools/`, `test/`) and lock update ordering.
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S2-01] Move `src/hooks` to `src/backends` in one shot while preserving package init files.
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S2-02] Bulk-update imports in `src/py2*.py` and compiler/utility code from `hooks.*` to `toolchain.emit.*`.
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S2-03] Bulk-update imports in `tools/**` and `test/**` to `toolchain.emit.*` and restore test execution paths.
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S2-04] Add only the minimal compatibility layer (`src/hooks` re-export) if required to prevent immediate external breakage (do not add if unnecessary).
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S3-01] Update `src/hooks` references to `src/backends` in `docs/ja` / `docs/en` specs and guides.
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S3-02] Update responsibility descriptions in `spec-folder` / `spec-dev` to `backends`, and explicitly mark `hooks` as compatibility/deprecation scope.
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S4-01] Re-run transpile checks for all targets and verify there is no import breakage caused by the rename.
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S4-02] Audit remaining `hooks.*` references via `rg`, explicitly document remaining reasons, and converge.

Decision log:
- 2026-03-02: Per user instruction, opened this as "top-priority among top-priority (highest P0)" to resolve the `src/hooks` naming inconsistency via one-shot rename to `src/backends`.
- 2026-03-03: Moved `src/hooks` to `src/backends` in one shot and updated imports in `src/py2*.py` / `src/toolchain/emit/**` / `tools/**` / `test/**` to `toolchain.emit.*`.
- 2026-03-03: Fixed rename side effects where blanket replacement turned `hooks.to_dict()` into `toolchain.emit.to_dict()` in `cpp/cs/rs hooks` implementations and `code_emitter.py`.
- 2026-03-03: Updated `src/hooks` wording to `src/backends` in current docs (`docs/ja|en/spec/*.md`, `docs/ja|en/how-to-use.md`) (archive excluded).
- 2026-03-03: Major check results were `check_py2cpp_transpile: checked=136 ok=136 fail=0 skipped=6`, `check_py2rs_transpile: checked=131 ok=131 fail=0 skipped=10`. `check_py2cs_transpile` was `checked=135 ok=133 fail=2 skipped=6` (`yield_generator_min.py`, `tuple_assign.py` known failures), and no rename-origin import breakage was observed.
- 2026-03-03: `check_py2go/swift/kotlin/lua/scala/php` passed. Failures in `check_py2js/check_py2ts` were existing assertion failures in `test_east3_cpp_bridge` (tuple loop header), and failures in `check_py2java/check_py2rb` were known `control/finally` failures; all confirmed not to be `hooks -> backends` rename import errors.
- 2026-03-03: Chose not to add a compatibility layer (`src/hooks` re-export). Reason: all in-repo references were already updated to `toolchain.emit.*`, and leaving a compatibility layer would delay convergence to `src/backends` normalization.
- 2026-03-03: Audit across `src/test/tools` found 0 remaining `from hooks.` / `import hooks.` / `src/hooks/` / `src.hooks.` references. `src/hooks` under `docs/*/spec/archive` remains intentionally for history retention.
