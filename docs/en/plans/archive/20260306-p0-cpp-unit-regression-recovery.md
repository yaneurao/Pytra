<a href="../../../ja/plans/archive/20260306-p0-cpp-unit-regression-recovery.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Root-Fix C++ Unit Regressions (Normalize SoT/IR/Emitter/Runtime Contracts)

Last updated: 2026-03-06

Related TODO:
- `docs/ja/todo/index.md` `ID: P0-CPP-REGRESSION-RECOVERY-01`

Background:
- As of 2026-03-06, C++ sample parity and fixture parity were green.
- However, `python3 -m unittest discover -s test/unit/backends/cpp -p test_*.py` was still failing.
- The failures were concentrated in four categories:
  - generated runtime breakage (`json`, `argparse`)
  - import/include and runtime-module resolution
  - container/iterator/comprehension semantics
  - emitter/CLI contract breakage
- The multi-file compile helpers had already been tightened to compile only runtime sources that were actually included, so these were real contract failures, not false positives from unrelated runtime files.

Goal:
- Fix the C++ unit regressions at the correct responsibility boundaries instead of patching generated files.
- Re-green unit tests, fixture parity, and sample parity without directly editing `.gen.*`.

Scope:
- `src/pytra/{built_in,std,utils}/`
- `src/backends/cpp/`
- import/runtime resolution paths under `src/toolchain/`
- C++ build tools
- C++ backend unit tests

Out of scope:
- non-C++ backends
- benchmark work
- temporary direct edits to `.gen.*`
- adding new runtime API surface

Acceptance:
- C++ backend unit suite passes
- fixture parity passes
- sample parity passes
- representative generated runtimes (`json`, `argparse`, `png`, `gif`, `time`, `pathlib`, `os`, `glob`) are regenerated correctly from SoT

Breakdown:
- classify failures by ownership
- fix `json` generated runtime through SoT/emission contracts
- fix `argparse` generated runtime through SoT/default-arg/class emission contracts
- restore public include/runtime-module resolution for `png/gif/time/pathlib`
- restore metadata-driven helper routing for `os.path` and `glob`
- fix `dict.items/get`, `any()`, dict/set comprehension semantics
- fix emitter / CLI contract regressions
- rerun unit + fixture/sample parity and close the plan

Decision log:
- 2026-03-06: `.gen.*` direct edits were explicitly forbidden; all fixes had to go back to SoT, IR/lower, emitter, or runtime generation rules.
- 2026-03-06: the unit failures were classified into generated-runtime, import/include, owner/module metadata, container semantics, and emitter/CLI responsibilities.
- 2026-03-06: representative fixes covered `json`, `argparse`, public shim includes, `os.path` helper routing, dict/item adapter behavior, and stmt/CLI contract cleanup.
- 2026-03-06: after the fixes, the full C++ unit suite, fixture parity, and sample parity all passed again.
