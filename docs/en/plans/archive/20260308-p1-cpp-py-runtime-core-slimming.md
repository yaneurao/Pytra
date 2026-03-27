<a href="../../../ja/plans/archive/20260308-p1-cpp-py-runtime-core-slimming.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Shrink C++ `py_runtime` Down to Low-Level Glue

Last updated: 2026-03-08

Related TODO:
- Completed. See `ID: P1-CPP-PY-RUNTIME-SLIM-01` in `docs/en/todo/archive/20260308.md`.

Background:
- `native/core/py_runtime.h` had accumulated higher-level built-in semantics that could be expressed in pure Python or generated runtime lanes.
- That made the low-level C++ runtime core too large, and it made it harder to share semantics across targets.
- The long-term direction is to leave only low-level ABI/object/container/process glue in `native/core` and push higher-level helpers into generated lanes.

Objective:
- Move pure-Python-expressible built-in semantics out of `native/core/py_runtime.h`.
- Keep `core` centered on ABI/object/container/process glue.
- Clarify which parts belong in `generated/built_in`, `generated/core`, `native/built_in`, or must remain in `native/core`.

Acceptance criteria:
- `native/core/py_runtime.h` is reduced toward low-level glue only
- collection/string helpers that belong in generated lanes are moved out
- runtime symbol index, build graph, and representative tests follow the new ownership
- layout guards prevent removed transitive includes from re-entering

## Task Breakdown

- [x] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S1-01] Inventory `native/core/py_runtime.h` and classify symbols by ownership.
- [x] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S1-02] Document what may remain in `py_runtime` and what must move out.
- [x] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S2-01] Fix the SoT-side destinations under `src/pytra/built_in/*.py`.
- [x] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S2-02] Define the generator/layout contract for `generated/core` and `generated/built_in`.
- [x] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S3-01] Move string/collection semantics out of `py_runtime.h`.
- [x] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S3-02] Reorganize `py_runtime.h` around low-level glue and minimize include aggregation.
- [x] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S4-01] Update runtime symbol index, build graph, and representative tests.
- [x] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S4-02] Re-run parity, sync docs, and add guards before closing.

## Key Migration Results

- `py_split`, `py_splitlines`, and `py_count` were moved into `src/pytra/built_in/string_ops.py`.
- `str::split`, `splitlines`, `count`, and `join` were moved from `native/core/py_runtime.h` to generated helper delegates.
- Direct built-in includes were added where needed, and transitive includes from `py_runtime.h` were reduced.
- Runtime symbol index and build-graph tests were updated to lock in the new ownership.

## Decision Log

- 2026-03-08 [ID: P1-CPP-PY-RUNTIME-SLIM-01-S3-01]: `string_ops` became the canonical generated lane for representative string helpers, and `py_range` kept its helper ABI through `@abi(ret="value")`.
- 2026-03-08 [ID: P1-CPP-PY-RUNTIME-SLIM-01-S3-02]: `py_runtime.h` was slimmed by removing transitive includes for `sequence`, `iter_ops`, and `predicates`, while direct built-in headers were included where actually needed.
- 2026-03-08 [ID: P1-CPP-PY-RUNTIME-SLIM-01-S4-01]: Runtime symbol index and build-graph regressions were updated so `string_ops` and `sequence` ownership are fixed by tests rather than convention.
- 2026-03-08 [ID: P1-CPP-PY-RUNTIME-SLIM-01-S4-02]: Layout guards were extended to block re-entry of removed transitive includes, and fixture/sample parity remained green.
