<a href="../../../ja/plans/archive/20260312-p1-relative-import-multifile-runtime-hardening.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Hardening Multi-File Runtime Smoke for Relative Imports

Last updated: 2026-03-12

Related TODO:
- `ID: P1-RELATIVE-IMPORT-MULTIFILE-RUNTIME-HARDENING-01` in `docs/ja/todo/index.md`

Background:
- Relative imports are already implemented in the frontend / import graph / CLI contract, and `py2x.py` already has nested package project-style transpile regressions.
- However, representative regressions that take a package tree like Pytra-NES through `--multi-file` C++ output and all the way through build/run are still thin.
- Current coverage leans toward successful transpilation or partial generated-source inspection, so the end-to-end contract including runtime link / namespace / manifest build is weaker than it should be.

Goal:
- Lock a representative contract where a nested-package relative-import chain succeeds through `py2x.py --target cpp --multi-file`, `tools/build_multi_cpp.py`, and final execution.
- Reconfirm the already-implemented relative import behavior on a Pytra-NES-style project layout and make regressions fail fast.

Scope:
- Add multi-file C++ build/run regressions for nested-package relative imports
- Strengthen runtime smoke for bare parent imports and package-local relative imports
- Small manifest / module-label / namespace fixes if needed
- Sync TODO / plan wording to the current contract

Out of scope:
- Adding new relative import syntax
- Simultaneous rollout to Rust / C# / other backends
- Large redesign of import graph implementation

Acceptance criteria:
- Nested-package input containing `from .cpu.runner import run` and `from ..util.bits import low_nibble` succeeds through `--multi-file`, build, and run.
- Bare parent relative imports such as `from .. import helper` also succeed through `--multi-file`, build, and run.
- The existing fail-closed contract for relative-import root escape remains intact.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k relative`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-12: Since relative imports are already supported, filed this as a `P1` runtime smoke hardening task for Pytra-NES-style project layouts rather than as a new language-feature task.
- 2026-03-12: Chose two representative runtime smoke lanes to lock through C++ multi-file build/run: `from .cpu.runner import run` + `from ..util.bits import low_nibble`, and `from .. import helper`.
- 2026-03-12: Normalized `from .. import helper` into a module-alias binding during validation so multi-file C++ consistently treats it as a namespace-qualified module call rather than as a plain symbol binding.

## Breakdown

- [x] [ID: P1-RELATIVE-IMPORT-MULTIFILE-RUNTIME-HARDENING-01-S1-01] Lock the current gap in plan / TODO and choose representative nested-package runtime smoke cases.
- [x] [ID: P1-RELATIVE-IMPORT-MULTIFILE-RUNTIME-HARDENING-01-S2-01] Added a multi-file C++ build/run regression for a nested-package relative import chain.
- [x] [ID: P1-RELATIVE-IMPORT-MULTIFILE-RUNTIME-HARDENING-01-S2-02] Added a multi-file C++ build/run regression for a bare parent relative import.
- [x] [ID: P1-RELATIVE-IMPORT-MULTIFILE-RUNTIME-HARDENING-01-S3-01] Synced docs / plan / TODO and focused regressions to the current contract, then closed the task.
