<a href="../../../ja/plans/archive/20260307-p0-cpp-os-path-wrapper-retirement.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Retire the C++ `os.path` Wrapper ABI

Last updated: 2026-03-07

Related TODO:
- `docs/ja/todo/index.md` `ID: P0-CPP-OSPATH-WRAPPER-RETIRE-01`

Summary:
- Remove the temporary `py_os_path_*` wrapper ABI from the C++ runtime.
- Make `pytra::std::os_path::*` the canonical runtime-call target again.

Why this was needed:
- `os_path.gen.h` is the canonical generated declaration surface derived from SoT.
- `os_path.ext.h` only existed to declare temporary wrapper names used by old runtime-call mapping.
- That compatibility layer looked like duplicate ownership and obscured the actual source of truth.

Target state:
- keep `os_path.gen.h`
- keep `os_path.ext.cpp` only for namespace implementation
- remove `os_path.ext.h`
- point runtime-call mapping back to `pytra::std::os_path::*`

Phases:
- inventory the wrapper dependency
- update runtime-call mapping
- delete the header-only wrapper layer
- regenerate public shims and symbol index
- archive the plan

Acceptance:
- `runtime_calls.json` resolves `os.path` helpers to canonical namespace symbols
- `os_path.ext.h` is gone
- public header `pytra/std/os_path.h` no longer needs the wrapper include

Decision log:
- 2026-03-07: `os_path.ext.h` was not the canonical declaration surface; it was only a temporary ABI shim and should be retired.
