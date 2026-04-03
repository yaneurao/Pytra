# P10-REORG: Inventory, consolidation, and registry for tools/ and tools/unittest/

Last updated: 2026-03-28
Status: Not started

## Background

Agents have been adding files to `tools/` and `tools/unittest/` without a registry, making it impossible to keep track of them.

- `tools/` has 36 scripts, with unnecessary and unknown-purpose files mixed in
- The responsibilities of the `tools/unittest/` subfolders (backends, common, compile, ir, link, selfhost, toolchain2, tooling) are not defined anywhere
- Agents add files without reading AGENTS.md, so rules alone cannot prevent this

## Design Approach

### Folder structure for tools/

Prohibit placing files directly under `tools/` and classify them into subdirectories.

```
tools/
  check/    — CI checks and verification (check_*.py, runtime_parity_check.py, etc.)
  gen/      — Code generation, golden generation, sample regeneration (generate_*.py, regenerate_*.py, etc.)
  run/      — Batch execution (run_local_ci.py, run_regen_on_version_bump.py)
  unittest/ — Unit tests (moved from tools/unittest/)
```

Files placed directly under `tools/` are considered unmanaged and are immediately subject to deletion.

### Consolidation of tools/unittest/ into tools/unittest/

Move test files from `tools/unittest/` into `tools/unittest/`. Both tests and tools are "things to run during development" and should be managed in a single location under `tools/`.

### Registry

Use `tools/README.md` as the registry, listing the purpose of every subdirectory and file. Files not in the registry are subject to deletion. A CI check reconciles the registry against actual files and fails if there is a discrepancy.

## Subtasks

1. [ID: P10-REORG-S1] Inventory all scripts in `tools/` (delete unnecessary ones, investigate unknown-purpose ones)
2. [ID: P10-REORG-S2] Create `tools/check/`, `tools/gen/`, `tools/run/` and move existing scripts into them
3. [ID: P10-REORG-S3] Inventory all subfolders and test files in `tools/unittest/` (delete unnecessary ones, identify toolchain1 leftovers)
4. [ID: P10-REORG-S4] Move `tools/unittest/` to `tools/unittest/` and restructure subfolders to match the toolchain2 pipeline
5. [ID: P10-REORG-S5] Update all `tools/` and `tools/unittest/` path references across source and documentation
6. [ID: P10-REORG-S6] Create `tools/README.md` as a registry, listing the purpose of every subdirectory and file
7. [ID: P10-REORG-S7] Add a CI check that reconciles against the registry (fail if any file is not listed)
8. [ID: P10-REORG-S8] Add rules to AGENTS.md: "no new files directly under `tools/`" and "no file additions without simultaneously updating the registry"

## Acceptance Criteria

1. No script files exist directly under `tools/`
2. `tools/unittest/` is consolidated into `tools/unittest/`
3. All files are listed in `tools/README.md`
4. The registry reconciliation check runs in CI
5. All path references in source and documentation are updated

## Decision Log

- 2026-03-28: Discussed the management problem with `tools/` and `tools/unittest/`. Decided on the approach: a registry + CI reconciliation check + consolidation under a single `tools/` location. Queued as P10 (last to be done).
