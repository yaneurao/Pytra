<a href="../../../ja/plans/archive/20260312-p2-relative-import-backend-coverage.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P2: Relative-Import Backend Coverage Contract

Last updated: 2026-03-12

Related TODO:
- `ID: P2-RELATIVE-IMPORT-BACKEND-COVERAGE-01` in `docs/ja/todo/index.md`

Background:
- Relative imports are already supported in the frontend / import graph / CLI contract, and C++ is now locked through multi-file build/run smoke.
- However, the project does not yet state backend by backend how much of that contract is actually verified, so it is easy to conflate "not yet verified" with "unsupported" or "fully supported."
- Before expanding the Pytra-NES-style project layout to more backends, the current verification coverage needs to be inventoried explicitly.

Goal:
- Lock the current relative-import verification coverage by backend and make it explicit that only C++ is build/run locked today while non-C++ lanes remain unverified.
- Provide a baseline checker and docs handoff that later non-C++ rollout tasks can attach to.

Scope:
- Add a canonical backend-relative-import coverage inventory
- Add a checker and unit tests
- Record the staged rollout order in TODO / plan docs

Out of scope:
- Implementing relative imports for Rust / C# / other backends
- Expanding support claims in the public support matrix
- Redesigning relative import semantics

Acceptance criteria:
- The canonical inventory covers `cpp, rs, cs, go, java, js, kotlin, lua, nim, php, ruby, scala, swift, ts`.
- Only `cpp` is fixed as `build_run_locked`; all other backends are fixed as `not_locked`.
- Coverage drift fails closed through the checker and unit tests.

Verification commands:
- `python3 tools/check/check_relative_import_backend_coverage.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `python3 tools/check/check_todo_priority.py`
- `git diff --check`

Decision log:
- 2026-03-12: After the immediate C++ multi-file runtime blocker was resolved, the next step was defined as locking current backend coverage first rather than jumping directly into a non-C++ rollout.
- 2026-03-12: The support-matrix handoff was fixed as verification coverage only, not as a widened support claim: `cpp=build_run_locked`, non-C++ backends remain `not_locked`.

## Breakdown

- [x] [ID: P2-RELATIVE-IMPORT-BACKEND-COVERAGE-01-S1-01] Lock the live plan / TODO and the representative backend coverage taxonomy.
- [x] [ID: P2-RELATIVE-IMPORT-BACKEND-COVERAGE-01-S2-01] Add the backend coverage inventory, checker, and unit tests.
- [x] [ID: P2-RELATIVE-IMPORT-BACKEND-COVERAGE-01-S2-02] Synced docs / support-matrix handoff wording to the current coverage baseline.
