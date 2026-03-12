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

NON_GOALS = {
    "pure_powershell_backend": "Do not implement PowerShell as a pure target backend.",
    "csharp_backend_rewrite": "Do not rewrite the C# backend itself.",
    "powershell_5_1_full_compat": "Do not guarantee full compatibility across both Windows PowerShell 5.1 and PowerShell 7.x.",
    "non_windows_support": "Do not guarantee PowerShell-host support on non-Windows environments.",
}


def build_powershell_cs_host_contract_manifest() -> dict[str, object]:
    return {
        "profile": dict(REPRESENTATIVE_HOST_PROFILE),
        "assumptions": dict(REPRESENTATIVE_ASSUMPTIONS),
        "required_executable_groups": {
            key: list(values) for key, values in REQUIRED_EXECUTABLE_GROUPS.items()
        },
        "optional_host_mechanisms": list(OPTIONAL_HOST_MECHANISMS),
        "non_goals": dict(NON_GOALS),
    }
