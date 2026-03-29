<a href="../../ja/plans/p0-src-layout-toolchain-pytra-runtime-split.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Reorganize `src` Layout (`toolchain` / `pytra` / `runtime`)

Last updated: 2026-03-03

Related TODO:
- `ID: P0-SRC-LAYOUT-SPLIT-01` in `docs/ja/todo/index.md`

Background:
- Today, `src/pytra` mixes the transpiler core (`frontends` / `ir` / `compiler`) with libraries referenced during transpilation (`std` / `utils` / `built_in`).
- In contrast, `src/runtime` contains artifacts used at execution time of transpiled code, which is a clearly different responsibility.
- Because folder responsibilities are mixed, deciding where to edit carries high development overhead.

Goal:
- Reorganize `src` into three responsibility-based tracks and clarify boundaries.
  - `src/toolchain`: transpiler core
  - `src/pytra`: libraries referenced during transpilation (Python namespace)
  - `src/runtime`: runtime for transpiled code execution
- Move `frontends` / `ir` / `compiler` out of `src/pytra`; keep `pytra` centered on `std` / `utils` / `built_in`.
- Do a bulk switch to canonical paths with no backward-compatibility layer.

In scope:
- Directory moves:
  - `src/pytra/frontends/** -> src/toolchain/frontends/**`
  - `src/pytra/ir/** -> src/toolchain/ir/**`
  - `src/pytra/compiler/** -> src/toolchain/misc/**`
- Import updates:
  - Update old `pytra.frontends` / `pytra.ir` / `pytra.compiler` references in `src/`, `tools/`, and `test/` to new paths
- Documentation updates:
  - `docs/ja/spec/*` (and `docs/en/spec/*` if needed)

Out of scope:
- Backend feature additions or optimization-logic changes
- Runtime API spec changes
- Sample benchmark value updates

Backward-compatibility policy:
- Do not create re-export shims for old import paths.
- Remove/replace old-path references in bulk; treat leftovers as failures.

Acceptance criteria:
- `src/toolchain/{frontends,ir,compiler}` exist, and old `src/pytra/{frontends,ir,compiler}` no longer exist.
- `src/pytra` converges to a `std` / `utils` / `built_in` centered structure.
- No old references remain in the repository (`from pytra.frontends` / `from pytra.ir` / `from pytra.compiler`) with no intentional exceptions.
- Main transpile / unit regressions pass.

Verification commands (planned):
- `python3 tools/check/check_todo_priority.py`
- `rg -n "pytra\\.(frontends|ir|compiler)" src tools test`
- `python3 tools/check/check_pytra_layer_boundaries.py`
- `python3 tools/check/check_py2cpp_transpile.py`
- `python3 tools/check/check_py2rs_transpile.py`
- `python3 tools/check/check_py2js_transpile.py`
- `python3 tools/check/check_py2ts_transpile.py`
- `python3 tools/check/check_py2go_transpile.py`
- `python3 tools/check/check_py2java_transpile.py`
- `python3 tools/check/check_py2kotlin_transpile.py`
- `python3 tools/check/check_py2swift_transpile.py`
- `python3 tools/check/check_py2rb_transpile.py`
- `python3 tools/check/check_py2lua_transpile.py`
- `python3 tools/check/check_py2scala_transpile.py`
- `python3 tools/check/check_py2php_transpile.py`
- `python3 tools/check/check_py2nim_transpile.py`

## Breakdown

- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S1-01] Inventory responsibilities and reference points for current `src/pytra/{frontends,ir,compiler,std,utils,built_in}`.
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S1-02] Finalize new layout rules (`toolchain` / `pytra` / `runtime`) and dependency direction in `docs/ja/spec/spec-folder.md`.
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S1-03] Document migration rules banning old import paths (no backward compatibility).
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S2-01] Create `src/toolchain/frontends` and move `src/pytra/frontends` in bulk.
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S2-02] Create `src/toolchain/ir` and move `src/pytra/ir` in bulk.
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S2-03] Create `src/toolchain/compiler` and move `src/pytra/compiler` in bulk.
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S2-04] Remove empty directories/unnecessary leftovers under `src/pytra` and organize around `std/utils/built_in`.
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S3-01] Bulk-update imports in `src/`, `tools/`, `test/` to new paths (no shim additions).
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S3-02] Align import paths in CLI entries (`pytra-cli.py`, `pytra-cli.py`, `py2*.py`) with new structure.
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S3-03] Add a check script to fail-fast detect old `pytra.frontends|ir|compiler` references.
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S4-01] Run major unit/transpile regressions and confirm no regression.
- [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S4-02] Reflect new directory responsibilities and paths in `docs/ja/spec` (and `docs/en/spec` if needed).

## S1-01 Inventory Results

### Responsibilities under `src/pytra` (current)

| Area | `.py` files | Primary responsibility | Main external reference points |
|---|---:|---|---|
| `frontends` | 7 | Parse Python input, build import graph, signature/semantic decisions | `src/py2cpp.py`, `pytra.compiler.transpile_cli`, `pytra.ir.core` |
| `ir` | 30 | EAST1/2/3 definitions, lowering, optimizer, pipeline | `pytra.frontends.transpile_cli`, `pytra.compiler.east_parts.*` |
| `compiler` | 44 | Compatibility shims, backend registry, CLI helpers, `east_parts` compatibility layer | `src/py2*.py`, `src/ir2lang.py`, `tools/*`, `tools/unittest/*` |
| `std` | 19 | std compatibility layer resolved during transpilation (`typing/pathlib/json/...`) | `src/py2*.py`, `src/toolchain/emit/*`, `test/fixtures/stdlib/*` |
| `utils` | 4 | Helpers used by transpilation targets (`assertions/png/gif`) | `sample/py/*`, `test/fixtures/*`, `tools/check/verify_image_runtime_parity.py` |
| `built_in` | 2 | Built-in compatibility helpers (`type_id`, etc.) | `tools/unittest/test_pytra_built_in_type_id.py` |

### Measured reference points (`src/tools/test`)

- `frontends`: 105 references (`src:104 / tools:0 / test:1`)
- `ir`: 247 references (`src:246 / tools:0 / test:1`)
- `compiler`: 275 references (`src:102 / tools:10 / test:163`)
- `std`: 526 references (`src:432 / tools:2 / test:92`)
- `utils`: 211 references (`src:0 / tools:1 / test:210`)
- `built_in`: 1 reference (`src:0 / tools:0 / test:1`)

### Dependency-direction findings (to resolve in S2/S3)

- `frontends -> ir` and `ir -> frontends` coexist, forming cyclic dependencies (`transpile_cli` and `ir.core` are mutually dependent).
- `compiler` already functions as a compatibility-shim layer and is a concentrated dependency point from `src/py2*.py` / `tools` / `test`.
- `std/utils/built_in` are broadly used as reference libraries at transpile time, so they are not targets to move to `toolchain`.

Decision log:
- 2026-03-03: Per user instruction, opened a P0 plan to reorganize `src` responsibility boundaries into `toolchain` / `pytra` / `runtime`.
- 2026-03-03: Chose not to provide backward-compatibility layers (old import re-exports), and adopted bulk removal of old paths during migration.
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S1-01] Inventoried responsibilities and references across six areas in `src/pytra`; confirmed concentrated dependency on `compiler` and cyclic dependency between `frontends`/`ir`.
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S1-02] Updated `docs/ja/spec/spec-folder.md`; fixed `src/toolchain/{frontends,ir,compiler}` as canonical placement and `src/pytra` as reference-library-only with defined dependency direction.
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S1-03] Added old-import ban rules to `spec-folder` (`pytra.frontends|ir|compiler` no new additions, no shim additions, plus `rg` check procedure).
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S2-01] Created `src/toolchain/frontends`, moved `src/pytra/frontends/*.py`, updated imports to `toolchain.frontends.*`, and confirmed passing `tools/check/check_pytra_layer_boundaries.py` and `test_pytra_layer_bootstrap`.
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S2-02] Created `src/toolchain/ir`, moved `src/pytra/ir/*.py`, updated references in `frontends`/`compiler.east_parts`/`test`/`tools` to `toolchain.compile.*`, and confirmed passing `check_pytra_layer_boundaries`, `test_pytra_layer_bootstrap`, and `py2cpp/py2x` conversion smoke.
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S2-03] Created `src/toolchain/compiler`, moved `src/pytra/compiler`, switched imports in `py2x/py2*.py`, `toolchain/emit/cpp`, `tools`, `test`, and `selfhost` to `toolchain.compiler.*`, and updated fixed-path dependencies (`prepare_selfhost_source`/`signature_registry`/`east_stage_boundary`) to new placement.
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S2-04] Confirmed `frontends`/`ir`/`compiler` directories are gone from `src/pytra`; converged `pytra` to `std`/`utils`/`built_in` plus minimal entry points (`__init__.py`, `cli.py`).
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S3-01] Bulk-updated imports in `src/tools/test/selfhost`; via `rg`, confirmed old `pytra.frontends|pytra.ir|pytra.compiler` imports are zero (including `src.pytra.*`).
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S3-02] Unified imports in `pytra-cli.py` / `pytra-cli.py` / `py2*.py` / `ir2lang.py` to `toolchain.compiler.*`, removing old `pytra.compiler` dependency from CLI entry points.
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S3-03] Extended `tools/check/check_pytra_layer_boundaries.py` with legacy-import scan (`src/tools/test/selfhost` target), fail-fast detecting `pytra.frontends|pytra.ir|pytra.compiler` (including `src.pytra.*`) as `legacy import path is forbidden` (syntax-error fixtures are skipped).
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S4-01] Ran major regressions and confirmed all pass (fail=0): `check_east_stage_boundary`/`check_pytra_layer_boundaries` and `check_py2{cpp,rs,js,ts,go,java,kotlin,swift,rb,lua,scala,php,nim}_transpile.py`.
- 2026-03-03: [ID: P0-SRC-LAYOUT-SPLIT-01-S4-02] Scanned `docs/ja/spec` and `docs/en/spec` (excluding `archive`) and updated old `src/pytra/{frontends,ir,compiler}` references to `src/toolchain/{frontends,ir,compiler}` to align doc paths with current implementation.
