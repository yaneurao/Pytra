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
        "non_goals": dict(NON_GOALS),
        "output_layout": dict(REPRESENTATIVE_OUTPUT_LAYOUT),
        "entrypoint_contract": dict(REPRESENTATIVE_ENTRYPOINT_CONTRACT),
        "runtime_cs_files": list(REPRESENTATIVE_RUNTIME_CS_FILES),
        "launcher_responsibilities": dict(LAUNCHER_RESPONSIBILITIES),
    }
