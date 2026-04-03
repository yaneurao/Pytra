<a href="../../ja/spec/spec-setup.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Development Environment Setup

This document describes the steps to get a local development environment up and running immediately after a `git clone`.

## 1. Prerequisites

- Python 3.10 or later
- g++ (if checking C++ parity)
- Set `PYTHONPATH=src` (specify it in each command, or `export` it in the shell)

## 2. Generating Golden Files

Golden files (east1/east2/east3/east3-opt/linked/selfhost) are not managed by git (covered by `.gitignore`). They do not exist locally right after cloning, so generate them by running:

```bash
PYTHONPATH=src python3 tools/gen/regenerate_golden.py
```

This generates golden files for all stages — fixture / sample / stdlib / pytra. The parity check depends on these golden files, so run this first.

**Note: If golden files already exist, do not regenerate them.** Regenerating while another agent is working will overwrite the golden files and change test results. If regeneration is needed, wait for a user instruction.

## 3. Generating the Runtime EAST Cache

`src/runtime/east/` is a cache generated from `src/pytra/{built_in,std,utils}/*.py`; the linker uses it to resolve stdlib type information when linking multi-module programs. This is also not managed by git.

```bash
PYTHONPATH=src python3 tools/check/check_east3_golden.py --check-runtime-east --update
```

### Freshness Check

If you modify Python source files under `src/pytra/`, the runtime EAST may become stale. Omit `--update` to perform a diff check only:

```bash
PYTHONPATH=src python3 tools/check/check_east3_golden.py --check-runtime-east
```

## 4. Summary of Execution Order

Run the following in order immediately after cloning:

```bash
# 1. Generate golden files
PYTHONPATH=src python3 tools/gen/regenerate_golden.py

# 2. Generate the runtime EAST
PYTHONPATH=src python3 tools/check/check_east3_golden.py --check-runtime-east --update

# 3. Parity check (example: C++)
PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets cpp
```

## 5. Notes

- During normal development, golden files and the runtime EAST are already generated. There is no need to regenerate them every time.
- Regeneration is only needed right after cloning or when a source change makes them stale.
- Do not commit golden files. Manual editing is also prohibited.
- For details on the canonical tools, see [spec-tools.md](./spec-tools.md).
