from __future__ import annotations

REPRESENTATIVE_HOST_PROFILE = {
    "profile_id": "powershell_cs_host_v1",
    "backend": "cs",
    "host_shell": "pwsh",
    "host_shell_version": "7.x",
    "host_os": "windows",
    "toolchain_policy": "dotnet_or_csc_required",
}

REPRESENTATIVE_ASSUMPTIONS = {
    "backend_scope": "Reuse the existing C# backend instead of introducing a new PowerShell backend.",
    "host_platform": "The representative host lane targets Windows with PowerShell 7 (`pwsh`).",
    "compiler_driver": "At least one of `dotnet` or `csc` must be available for the representative lane.",
    "host_profile_shape": "The representative host profile is `pwsh + py2cs`, not a pure PowerShell target.",
}

REQUIRED_EXECUTABLE_GROUPS = {
    "host_shell": ("pwsh",),
    "compiler_driver": ("dotnet", "csc"),
}

OPTIONAL_HOST_MECHANISMS = ("Add-Type",)

REPRESENTATIVE_BUILD_DRIVER_PRIORITY = (
    "dotnet_build",
    "csc_compile",
    "add_type_load",
)

BUILD_DRIVER_EXECUTABLE_REQUIREMENTS = {
    "dotnet_build": ("pwsh", "dotnet"),
    "csc_compile": ("pwsh", "csc"),
    "add_type_load": ("pwsh",),
}

BUILD_DRIVER_FAIL_CLOSED_RULES = {
    "dotnet_build": "Use first when `dotnet` is available. Fail closed if `src/Program.cs`, required `runtime/*.cs`, or the canonical `build/Program.exe` artifact cannot be produced.",
    "csc_compile": "Use only when `dotnet` is unavailable and `csc` is available. Fail closed if direct compilation of generated plus runtime sources fails or `build/Program.exe` cannot be written.",
    "add_type_load": "Use only as the last fallback when neither `dotnet` nor `csc` is available. Fail closed for representative smoke/parity lanes, multi-file runtime bundling, or any flow that requires a persistent `build/Program.exe` artifact.",
}

REPRESENTATIVE_VERIFICATION_LANES = {
    "existing_backend_smoke": "tools/unittest/emit/cs/test_py2cs_smoke.py",
    "future_host_smoke": "test/unit/tooling/test_powershell_cs_host_profile.py",
    "sample_parity_input": "sample/py/01_mandelbrot.py",
    "future_sample_parity": "tools/check_powershell_cs_host_sample_parity.py",
    "cli_entrypoint": "src/pytra-cli.py",
    "cli_profile_inventory": "src/toolchain/compiler/pytra_cli_profiles.py",
    "future_cli_profile_regression": "test/unit/tooling/test_pytra_cli_powershell_cs_host_profile.py",
}

CURRENT_PY2CS_SMOKE_BASELINE = {
    "runner": "tools/unittest/emit/cs/test_py2cs_smoke.py",
    "covers_backend_transpile": True,
    "covers_generated_program_cs": True,
    "covers_pwsh_launcher": False,
    "covers_runtime_source_bundling": False,
    "covers_build_driver_selection": False,
    "covers_compiled_execution": False,
    "covers_sample_parity": False,
    "covers_cli_profile_selection": False,
}

HOST_PROFILE_DELTA_FROM_PY2CS_SMOKE = {
    "transpile_only_scope": "Current `py2cs` smoke validates backend transpilation and generated `Program.cs`, not a PowerShell host run/build lane.",
    "launcher_gap": "Current smoke does not validate `run.ps1` responsibility or argument forwarding.",
    "runtime_layout_gap": "Current smoke does not validate `src/Program.cs` plus `runtime/*.cs` staging.",
    "driver_selection_gap": "Current smoke does not validate `dotnet` / `csc` / `Add-Type` driver selection.",
    "compiled_execution_gap": "Current smoke does not validate producing and executing the representative `build/Program.exe` artifact from PowerShell.",
    "sample_parity_gap": "Current smoke does not validate representative sample parity through the PowerShell host profile.",
    "cli_profile_gap": "Current smoke does not validate a dedicated `pwsh + cs` profile in `src/pytra-cli.py` and `src/toolchain/compiler/pytra_cli_profiles.py`.",
}

NON_GOALS = {
    "pure_powershell_backend": "Do not implement PowerShell as a pure target backend.",
    "csharp_backend_rewrite": "Do not rewrite the C# backend itself.",
    "powershell_5_1_full_compat": "Do not guarantee full compatibility across both Windows PowerShell 5.1 and PowerShell 7.x.",
    "non_windows_support": "Do not guarantee PowerShell-host support on non-Windows environments.",
}

REPRESENTATIVE_OUTPUT_LAYOUT = {
    "launcher_rel": "run.ps1",
    "generated_entry_rel": "src/Program.cs",
    "runtime_source_dir_rel": "runtime",
    "build_output_dir_rel": "build",
    "build_artifact_rel": "build/Program.exe",
}

REPRESENTATIVE_ENTRYPOINT_CONTRACT = {
    "class_name": "Program",
    "method_name": "Main",
    "signature": "public static void Main(string[] args)",
    "generated_entry_owns_main": True,
    "runtime_sources_define_main": False,
}

REPRESENTATIVE_RUNTIME_CS_FILES = (
    "py_runtime.cs",
    "time.cs",
    "math.cs",
    "pathlib.cs",
    "json.cs",
    "png.cs",
    "gif.cs",
)

LAUNCHER_RESPONSIBILITIES = {
    "stage_generated_entry": "Stage the generated entry source at `src/Program.cs` without rewriting `Program.Main`.",
    "stage_runtime_sources": "Copy the selected runtime `.cs` support files into `runtime/` and keep them separate from the generated entry source.",
    "delegate_compile_or_load": "Delegate compile/load to the selected host driver rather than synthesizing backend logic inside PowerShell.",
    "forward_program_args": "Forward user CLI arguments to the compiled `Program.Main(string[] args)` entrypoint.",
    "fail_closed_missing_layout": "Fail closed when `run.ps1`, `src/Program.cs`, required runtime `.cs`, or the `build/` output layout is missing.",
}

REPRESENTATIVE_DOC_TARGETS = {
    "ja_readme": "docs/ja/README.md",
    "en_readme": "README.md",
    "ja_usage": "docs/ja/tutorial/how-to-use.md",
    "en_usage": "docs/en/how-to-use.md",
}

USER_CAVEAT_SUMMARY = {
    "not_pure_backend": "PowerShell support is tracked as a future `pwsh + py2cs` host profile, not as a pure target backend.",
    "current_user_lane": "Current user-facing execution remains `py2cs` transpile plus manual C# compile/run. `run.ps1` host smoke, sample parity, and CLI profile lanes are still future work.",
}


def build_powershell_cs_host_contract_manifest() -> dict[str, object]:
    return {
        "profile": dict(REPRESENTATIVE_HOST_PROFILE),
        "assumptions": dict(REPRESENTATIVE_ASSUMPTIONS),
        "required_executable_groups": {
            key: list(values) for key, values in REQUIRED_EXECUTABLE_GROUPS.items()
        },
        "optional_host_mechanisms": list(OPTIONAL_HOST_MECHANISMS),
        "build_driver_priority": list(REPRESENTATIVE_BUILD_DRIVER_PRIORITY),
        "build_driver_executable_requirements": {
            key: list(values)
            for key, values in BUILD_DRIVER_EXECUTABLE_REQUIREMENTS.items()
        },
        "build_driver_fail_closed_rules": dict(BUILD_DRIVER_FAIL_CLOSED_RULES),
        "representative_verification_lanes": dict(REPRESENTATIVE_VERIFICATION_LANES),
        "current_py2cs_smoke_baseline": dict(CURRENT_PY2CS_SMOKE_BASELINE),
        "host_profile_delta_from_py2cs_smoke": dict(HOST_PROFILE_DELTA_FROM_PY2CS_SMOKE),
        "non_goals": dict(NON_GOALS),
        "output_layout": dict(REPRESENTATIVE_OUTPUT_LAYOUT),
        "entrypoint_contract": dict(REPRESENTATIVE_ENTRYPOINT_CONTRACT),
        "runtime_cs_files": list(REPRESENTATIVE_RUNTIME_CS_FILES),
        "launcher_responsibilities": dict(LAUNCHER_RESPONSIBILITIES),
        "docs_targets": dict(REPRESENTATIVE_DOC_TARGETS),
        "user_caveat_summary": dict(USER_CAVEAT_SUMMARY),
    }
