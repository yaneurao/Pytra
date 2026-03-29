<a href="../../../ja/plans/archive/20260312-p5-powershell-csharp-host-profile.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P5 PowerShell Host Profile For C# Backend

Last updated: 2026-03-12

Purpose:
- Define a PowerShell host profile that launches the existing C# backend output, instead of implementing a new pure PowerShell backend.
- Package the `.cs` output from `py2cs` together with runtime files into a representative build/run flow that can be launched from `pwsh`.
- Establish a lower-cost execution path than a pure PowerShell backend by assuming Windows / PowerShell 7 / .NET-style tooling.

Background:
- The current C# backend, judging from [CSharpEmitter](/workspace/Pytra/src/backends/cs/emitter/cs_emitter.py) and the smoke/selfhost flow, already targets a conservative surface strongly shaped by Mono `mcs` compatibility.
- Because of that, building a PowerShell host around the C# backend is far more realistic than implementing PowerShell as a new target language from scratch.
- Emulator-like code such as Pytra-NES, with bit ops, classes, bytes, and file I/O, fits C# much better than pure PowerShell, so `pwsh launcher + cs backend` is the more practical direction.
- However, runtime bundling, multi-file `.cs` compilation, `dotnet` / `csc` / `Add-Type` fallback, and the `Main` entrypoint contract are not yet defined.

Out of scope:
- Implementing PowerShell as a pure target backend.
- A full rewrite of the C# backend itself.
- Full compatibility guarantees across both Windows PowerShell 5.1 and PowerShell 7.x.
- Guaranteed PowerShell-host support on non-Windows environments.

Acceptance criteria:
- The representative `pwsh + cs backend` setup and required toolchain (`pwsh`, `dotnet` or `csc`) are fixed in the plan.
- Responsibility boundaries are documented for the launcher `.ps1`, generated `.cs`, bundled runtime `.cs`, output layout, and `Main` entrypoint.
- Build-driver priority and fail-closed conditions are defined for `dotnet`, `csc`, and `Add-Type`.
- Representative smoke / parity / docs regression points are identified.
- The `docs/en/` mirror follows the Japanese source plan.

Representative layout:
- The launcher uses `run.ps1` as the canonical filename.
- The generated entry source lives at `src/Program.cs` and keeps `public static void Main(string[] args)`.
- Runtime support sources live under `runtime/` as separate `.cs` files instead of being merged into the generated entry.
- The canonical build artifact is `build/Program.exe`.

Verification commands:
- `python3 tools/check/check_powershell_cs_host_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_powershell_cs_host_contract.py'`
- `python3 tools/check/check_todo_priority.py`
- `git diff --check`

## Child tasks

- [x] [ID: P5-POWERSHELL-CS-HOST-01-S1-01] Fix the representative assumptions and non-goals for the `pwsh + cs backend` lane (Windows / PowerShell 7 / `dotnet` or `csc`).
- [x] [ID: P5-POWERSHELL-CS-HOST-01-S2-01] Define launcher `.ps1` responsibilities plus the generated `.cs`, runtime `.cs`, output layout, and `Main` entrypoint contract.
- [x] [ID: P5-POWERSHELL-CS-HOST-01-S2-02] Set the build-driver priority (`dotnet`, `csc`, `Add-Type`) and fail-closed conditions.
- [x] [ID: P5-POWERSHELL-CS-HOST-01-S3-01] Design the representative smoke / sample parity / CLI profile path and make the delta from current `py2cs` smoke explicit.
- [x] [ID: P5-POWERSHELL-CS-HOST-01-S4-01] Organize docs / how-to-use / user caveats so this profile can be promoted into TODO later.

## Decision log

- 2026-03-20: **This plan is retired due to a strategy change.** After an experimental direct PowerShell emitter proved that native PowerShell code generation is viable, the `pwsh + py2cs` host profile approach is withdrawn. PowerShell will be implemented as an independent pure target backend instead. The C# host profile contract artifacts (`powershell_cs_host_contract.py`, `check_powershell_cs_host_contract.py`, and related tests) are no longer in use.
- 2026-03-12: A pure PowerShell backend has poor language fit for bit operations, bytes, classes, and runtime packaging, so this plan is explicitly limited to a PowerShell host for the C# backend.
- 2026-03-12: This remains low priority and mainly experimental host infrastructure, so it is tracked as `P5`.
- 2026-03-12: `S1-01` fixes `pwsh / Windows / PowerShell 7 / dotnet-or-csc required / Add-Type optional` as the canonical baseline and routes doc drift through `check_powershell_cs_host_contract.py`.
- 2026-03-12: `S2-01` fixes the representative layout as `run.ps1`, `src/Program.cs`, `runtime/*.cs`, and `build/Program.exe`, with the launcher preserving generated `Program.Main(string[] args)` instead of synthesizing its own entrypoint.
- 2026-03-12: `S2-02` fixes the build-driver priority as `dotnet` -> `csc` -> `Add-Type`, and keeps `Add-Type` as the last non-canonical fallback instead of a representative smoke/parity path that requires a persistent `build/Program.exe`.
- 2026-03-12: `S3-01` fixes the current anchor as `tools/unittest/emit/cs/test_py2cs_smoke.py` while separating future PowerShell-host regression lanes into `tools/unittest/tooling/test_powershell_cs_host_profile.py`, `tools/check/check_powershell_cs_host_sample_parity.py`, and `tools/unittest/tooling/test_pytra_cli_powershell_cs_host_profile.py`. The explicit delta from current `py2cs` smoke is launcher staging, runtime bundling, driver selection, compiled execution, sample parity, and CLI profile selection.
- 2026-03-12: `S3-01` fixes the representative sample/parity anchor as `sample/py/01_mandelbrot.py`, and fixes the CLI profile anchor as `src/pytra-cli.py` plus `src/toolchain/compiler/pytra_cli_profiles.py`.
- 2026-03-12: `S4-01` updates README/how-to-use to state that PowerShell is a `pwsh + py2cs` host profile rather than a pure backend, and that the current user-facing lane still stops at `py2cs` smoke plus manual compile/run.
