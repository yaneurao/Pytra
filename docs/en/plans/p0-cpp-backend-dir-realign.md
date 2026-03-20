# P0: Realign C++ Backend Directories (5 Folders -> `lower/optimizer/emitter`)

Last updated: 2026-03-02

Related TODO:
- `ID: P0-CPP-DIR-REALIGN-01` in `docs/ja/todo/index.md`

Background:
- Under `src/toolchain/emit/cpp/`, the folders `hooks/`, `header/`, `multifile/`, `profile/`, and `runtime_emit/` still remain and do not match the target responsibility boundary (`lower/optimizer/emitter`).
- These five folders are currently referenced mainly by `py2cpp.py` and `emitter`; they are not shared components used by `lower`/`optimizer`.
- Keeping this mixed layout increases maintenance cost for responsibility tracing, migration decisions, and selfhost pathways in the C++ backend.

Goal:
- Realign implementation boundaries in `src/toolchain/emit/cpp/` around `lower/optimizer/emitter`, and remove helper folders from the backend root.
- Consolidate functionality from the five folders into `emitter` by responsibility, and simplify the import surface from `py2cpp.py`.

In scope:
- `src/toolchain/emit/cpp/hooks/*`
- `src/toolchain/emit/cpp/header/*`
- `src/toolchain/emit/cpp/multifile/*`
- `src/toolchain/emit/cpp/profile/*`
- `src/toolchain/emit/cpp/runtime_emit/*`
- `src/toolchain/emit/cpp/emitter/*` (new destination modules)
- `src/py2cpp.py` (import / callsite updates)
- Related unit tests and check scripts

Out of scope:
- Simultaneous reorganization of non-C++ backends
- Changes to EAST3 / C++ IR specs themselves
- Relocation of `src/profiles/cpp/*.json`

Acceptance criteria:
- `hooks/`, `header/`, `multifile/`, `profile/`, and `runtime_emit/` no longer exist directly under `src/toolchain/emit/cpp/`.
- Legacy imports (`toolchain.emit.cpp.hooks|header|multifile|profile|runtime_emit`) are removed from production code.
- Main `py2cpp.py` pathways (single-file / multi-file / emit-runtime-cpp) run with no regressions.
- C++ regressions pass (unit + transpile check + sample regeneration).

Implementation policy:
1. Reclassify the responsibilities of the five folders and migrate them to new modules under `emitter`.
2. Bulk-update imports at reference sites to new paths, then remove old packages in phases.
3. Add a guard (unit test or check script) to detect reintroduction of old imports.
4. Verify no regressions with regression tests and sample regeneration.

Placement policy (draft):
- `hooks/` -> `emitter/hooks_registry.py`
- `profile/` -> `emitter/profile_loader.py`
- `runtime_emit/` -> `emitter/runtime_paths.py`
- `header/` -> `emitter/header_builder.py`
- `multifile/` -> `emitter/multifile_writer.py`

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_cpp_*' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --force`

## Breakdown

- [x] [ID: P0-CPP-DIR-REALIGN-01-S1-01] Inventory responsibilities and references (`py2cpp`/`emitter`/tests) for the current five folders and finalize destinations.
- [x] [ID: P0-CPP-DIR-REALIGN-01-S1-02] Finalize the new directory policy (destination module names under `emitter`) and document naming conventions.
- [x] [ID: P0-CPP-DIR-REALIGN-01-S2-01] Move `profile` under `emitter` and update imports in `py2cpp`/`CppEmitter`.
- [x] [ID: P0-CPP-DIR-REALIGN-01-S2-02] Move `hooks` under `emitter` and update hook-factory callsites.
- [x] [ID: P0-CPP-DIR-REALIGN-01-S2-03] Move `runtime_emit` under `emitter` and update module include/runtime-path resolution.
- [x] [ID: P0-CPP-DIR-REALIGN-01-S2-04] Move `header` under `emitter` and update header-generation pathways.
- [x] [ID: P0-CPP-DIR-REALIGN-01-S2-05] Move `multifile` under `emitter` and update multi-file output pathways.
- [x] [ID: P0-CPP-DIR-REALIGN-01-S2-06] Remove the legacy five folders and unify `toolchain.emit.cpp.*` imports to new paths.
- [x] [ID: P0-CPP-DIR-REALIGN-01-S3-01] Add regression tests/checks (`rg`-based or unit) to prevent old-import reintroduction.
- [x] [ID: P0-CPP-DIR-REALIGN-01-S3-02] Run unit/transpile/sample regressions, confirm no regressions, and satisfy completion criteria.

## S1-01 Inventory Results (2026-03-02)

| Current folder | Primary responsibility | Primary references | Destination (final) |
| --- | --- | --- | --- |
| `toolchain/emit/cpp/profile/` | C++ profile loader / operator map / hooks loader | `src/py2cpp.py`, `toolchain/emit/cpp/emitter/*` | `toolchain/emit/cpp/emitter/profile_loader.py` |
| `toolchain/emit/cpp/hooks/` | C++ emitter hook registry (`build_cpp_hooks`) | `toolchain/emit/cpp/profile/cpp_profile.py`, `src/py2cpp.py`, tests | `toolchain/emit/cpp/emitter/hooks_registry.py` |
| `toolchain/emit/cpp/runtime_emit/` | Runtime path / include / namespace resolution | `src/py2cpp.py`, `toolchain/emit/cpp/emitter/module.py` | `toolchain/emit/cpp/emitter/runtime_paths.py` |
| `toolchain/emit/cpp/header/` | EAST -> C++ header generation | `src/py2cpp.py` | `toolchain/emit/cpp/emitter/header_builder.py` |
| `toolchain/emit/cpp/multifile/` | Multi-file output orchestration | `src/py2cpp.py` | `toolchain/emit/cpp/emitter/multifile_writer.py` |

Notes:
- Verified that all five folders are not shared components for `lower`/`optimizer`; they are helper modules around `emitter` or the CLI bridge.
- Therefore, this task consolidates them under `emitter` rather than moving anything under `lower/optimizer`.

## S1-02 Naming and Import Conventions (2026-03-02)

- Canonical directories directly under `src/toolchain/emit/cpp/` are limited to `lower/`, `optimizer/`, and `emitter/`.
- Helper modules are placed directly under `emitter/` with these names:
  - `profile_loader.py`
  - `hooks_registry.py`
  - `runtime_paths.py`
  - `header_builder.py`
  - `multifile_writer.py`
- Legacy imports (`toolchain.emit.cpp.{profile,hooks,runtime_emit,header,multifile}`) are disallowed after phased migration.
- `py2cpp.py` imports backend helpers only from `toolchain.emit.cpp.emitter.*`.
- Backward-compat aliases are allowed only during migration and are removed upon completion of `S2-06`.

Decision log:
- 2026-03-02: Per user direction, filed cleanup of the five root-level folders in `src/toolchain/emit/cpp/` (`hooks/header/multifile/profile/runtime_emit`) as P0.
- 2026-03-02: For this task, adopted a policy to relocate the five folders into one of `lower/optimizer/emitter`, with no treatment as shared/common modules.
- 2026-03-02: [ID: P0-CPP-DIR-REALIGN-01-S1-01] Inventoried responsibilities/references of the five folders and finalized destinations as five modules under `emitter`.
- 2026-03-02: [ID: P0-CPP-DIR-REALIGN-01-S1-02] Documented naming conventions and import boundaries (unify to `toolchain.emit.cpp.emitter.*`).
- 2026-03-02: [ID: P0-CPP-DIR-REALIGN-01-S2-01] Moved `src/toolchain/emit/cpp/profile/cpp_profile.py` to `src/toolchain/emit/cpp/emitter/profile_loader.py`, updated imports in `py2cpp`/`CppEmitter`/related helpers, and validated no regressions with `check_py2cpp_transpile.py` and `test_language_profile.py`.
- 2026-03-02: [ID: P0-CPP-DIR-REALIGN-01-S2-02] Moved `src/toolchain/emit/cpp/hooks/cpp_hooks.py` to `src/toolchain/emit/cpp/emitter/hooks_registry.py`, updated hook-factory references in `py2cpp`, profile loader, and `profiles/cpp/profile.json`, and verified no regressions with `test_cpp_hooks.py` and `check_py2cpp_transpile.py`.
- 2026-03-02: [ID: P0-CPP-DIR-REALIGN-01-S2-03] Moved `src/toolchain/emit/cpp/runtime_emit/cpp_runtime_emit.py` to `src/toolchain/emit/cpp/emitter/runtime_paths.py`, updated runtime-path imports in `py2cpp`/`CppModuleEmitter`, and verified no regressions with `test_py2cpp_features.py -k runtime_module_tail_and_namespace_support_compiler_tree` and `check_py2cpp_transpile.py`.
- 2026-03-03: [ID: P0-CPP-DIR-REALIGN-01-S2-04] Moved `src/toolchain/emit/cpp/header/cpp_header.py` to `src/toolchain/emit/cpp/emitter/header_builder.py` and updated imports in `py2cpp`.
- 2026-03-03: [ID: P0-CPP-DIR-REALIGN-01-S2-05] Moved `src/toolchain/emit/cpp/multifile/cpp_multifile.py` to `src/toolchain/emit/cpp/emitter/multifile_writer.py` and updated imports in the multi-file output path.
- 2026-03-03: [ID: P0-CPP-DIR-REALIGN-01-S2-06] Removed Python implementations under `src/toolchain/emit/cpp/{hooks,header,multifile,profile,runtime_emit}` and removed legacy import references.
- 2026-03-03: [ID: P0-CPP-DIR-REALIGN-01-S3-01] Added `tools/check_cpp_backend_layout.py`, enabling fail-closed checks for remaining legacy folders and old imports.
- 2026-03-03: [ID: P0-CPP-DIR-REALIGN-01-S3-02] Ran `check_cpp_backend_layout.py` / `check_py2cpp_boundary.py` / `check_py2cpp_transpile.py` / `sample/py/01 -> py2cpp` and confirmed no regressions in the relocated scope.
