from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import powershell_cs_host_contract as contract_mod


JA_PLAN = ROOT / "docs/ja/plans/p5-powershell-csharp-host-profile.md"
EN_PLAN = ROOT / "docs/en/plans/p5-powershell-csharp-host-profile.md"
JA_TODO = ROOT / "docs/ja/todo/index.md"
EN_TODO = ROOT / "docs/en/todo/index.md"

EXPECTED_JA_PLAN_PHRASES = (
    "PowerShell を新しい backend として実装する代わりに、既存の C# backend を PowerShell から起動する host profile を定義する。",
    "Windows / PowerShell 7 / .NET 系 toolchain を前提に、`pure PowerShell backend` より低コストな実行経路を確立する。",
    "PowerShell を target language とする pure backend 実装。",
    "PowerShell 5.1 と 7.x の完全互換保証。",
    "非 Windows 環境での PowerShell host 動作保証。",
    "[x] [ID: P5-POWERSHELL-CS-HOST-01-S1-01]",
    "[x] [ID: P5-POWERSHELL-CS-HOST-01-S2-01]",
    "[x] [ID: P5-POWERSHELL-CS-HOST-01-S2-02]",
    "`run.ps1`",
    "`src/Program.cs`",
    "`runtime/`",
    "`build/Program.exe`",
    "`public static void Main(string[] args)`",
    "`dotnet` -> `csc` -> `Add-Type`",
    "最後段の non-canonical fallback",
)

EXPECTED_EN_PLAN_PHRASES = (
    "Define a PowerShell host profile that launches the existing C# backend output, instead of implementing a new pure PowerShell backend.",
    "Establish a lower-cost execution path than a pure PowerShell backend by assuming Windows / PowerShell 7 / .NET-style tooling.",
    "Implementing PowerShell as a pure target backend.",
    "Full compatibility guarantees across both Windows PowerShell 5.1 and PowerShell 7.x.",
    "Guaranteed PowerShell-host support on non-Windows environments.",
    "[x] [ID: P5-POWERSHELL-CS-HOST-01-S1-01]",
    "[x] [ID: P5-POWERSHELL-CS-HOST-01-S2-01]",
    "[x] [ID: P5-POWERSHELL-CS-HOST-01-S2-02]",
    "`run.ps1`",
    "`src/Program.cs`",
    "`runtime/`",
    "`build/Program.exe`",
    "`public static void Main(string[] args)`",
    "`dotnet` -> `csc` -> `Add-Type`",
    "last non-canonical fallback",
)

EXPECTED_JA_TODO_PHRASES = (
    "[ID: P5-POWERSHELL-CS-HOST-01]",
    "`pwsh`",
    "`dotnet` / `csc` / `Add-Type`",
    "pure PowerShell backend は対象外",
    "`run.ps1` / `src/Program.cs` / `runtime/*.cs` / `build/Program.exe`",
    "`dotnet -> csc -> Add-Type`",
)

EXPECTED_EN_TODO_PHRASES = (
    "[ID: P5-POWERSHELL-CS-HOST-01]",
    "`pwsh + py2cs`",
    "`dotnet` / `csc` / `Add-Type`",
    "pure PowerShell target backend stays out of scope",
    "`run.ps1` / `src/Program.cs` / `runtime/*.cs` / `build/Program.exe`",
    "`dotnet -> csc -> Add-Type`",
)


def _collect_contract_issues() -> list[str]:
    issues: list[str] = []
    if contract_mod.REPRESENTATIVE_HOST_PROFILE != {
        "profile_id": "powershell_cs_host_v1",
        "backend": "cs",
        "host_shell": "pwsh",
        "host_shell_version": "7.x",
        "host_os": "windows",
        "toolchain_policy": "dotnet_or_csc_required",
    }:
        issues.append("representative host profile drifted")
    if contract_mod.REQUIRED_EXECUTABLE_GROUPS != {
        "host_shell": ("pwsh",),
        "compiler_driver": ("dotnet", "csc"),
    }:
        issues.append("required executable groups drifted")
    if contract_mod.OPTIONAL_HOST_MECHANISMS != ("Add-Type",):
        issues.append("optional host mechanisms drifted")
    if contract_mod.REPRESENTATIVE_BUILD_DRIVER_PRIORITY != (
        "dotnet_build",
        "csc_compile",
        "add_type_load",
    ):
        issues.append("build driver priority drifted")
    if contract_mod.BUILD_DRIVER_EXECUTABLE_REQUIREMENTS != {
        "dotnet_build": ("pwsh", "dotnet"),
        "csc_compile": ("pwsh", "csc"),
        "add_type_load": ("pwsh",),
    }:
        issues.append("build driver executable requirements drifted")
    if set(contract_mod.BUILD_DRIVER_FAIL_CLOSED_RULES.keys()) != {
        "dotnet_build",
        "csc_compile",
        "add_type_load",
    }:
        issues.append("build driver fail-closed rule keys drifted")
    if set(contract_mod.NON_GOALS.keys()) != {
        "pure_powershell_backend",
        "csharp_backend_rewrite",
        "powershell_5_1_full_compat",
        "non_windows_support",
    }:
        issues.append("non-goal key set drifted")
    if contract_mod.REPRESENTATIVE_OUTPUT_LAYOUT != {
        "launcher_rel": "run.ps1",
        "generated_entry_rel": "src/Program.cs",
        "runtime_source_dir_rel": "runtime",
        "build_output_dir_rel": "build",
        "build_artifact_rel": "build/Program.exe",
    }:
        issues.append("representative output layout drifted")
    if contract_mod.REPRESENTATIVE_ENTRYPOINT_CONTRACT != {
        "class_name": "Program",
        "method_name": "Main",
        "signature": "public static void Main(string[] args)",
        "generated_entry_owns_main": True,
        "runtime_sources_define_main": False,
    }:
        issues.append("representative entrypoint contract drifted")
    if contract_mod.REPRESENTATIVE_RUNTIME_CS_FILES != (
        "py_runtime.cs",
        "time.cs",
        "math.cs",
        "pathlib.cs",
        "json.cs",
        "png.cs",
        "gif.cs",
    ):
        issues.append("representative runtime cs file set drifted")
    if set(contract_mod.LAUNCHER_RESPONSIBILITIES.keys()) != {
        "stage_generated_entry",
        "stage_runtime_sources",
        "delegate_compile_or_load",
        "forward_program_args",
        "fail_closed_missing_layout",
    }:
        issues.append("launcher responsibility key set drifted")
    manifest = contract_mod.build_powershell_cs_host_contract_manifest()
    if set(manifest.keys()) != {
        "profile",
        "assumptions",
        "required_executable_groups",
        "optional_host_mechanisms",
        "build_driver_priority",
        "build_driver_executable_requirements",
        "build_driver_fail_closed_rules",
        "non_goals",
        "output_layout",
        "entrypoint_contract",
        "runtime_cs_files",
        "launcher_responsibilities",
    }:
        issues.append("contract manifest keys drifted")
    return issues


def _collect_docs_issues() -> list[str]:
    issues: list[str] = []
    ja_plan = JA_PLAN.read_text(encoding="utf-8")
    en_plan = EN_PLAN.read_text(encoding="utf-8")
    ja_todo = JA_TODO.read_text(encoding="utf-8")
    en_todo = EN_TODO.read_text(encoding="utf-8")
    for phrase in EXPECTED_JA_PLAN_PHRASES:
        if phrase not in ja_plan:
            issues.append(f"missing phrase in ja plan: {phrase}")
    for phrase in EXPECTED_EN_PLAN_PHRASES:
        if phrase not in en_plan:
            issues.append(f"missing phrase in en plan: {phrase}")
    for phrase in EXPECTED_JA_TODO_PHRASES:
        if phrase not in ja_todo:
            issues.append(f"missing phrase in ja todo: {phrase}")
    for phrase in EXPECTED_EN_TODO_PHRASES:
        if phrase not in en_todo:
            issues.append(f"missing phrase in en todo: {phrase}")
    return issues


def main() -> int:
    issues = _collect_contract_issues() + _collect_docs_issues()
    if issues:
        raise SystemExit("\n".join(issues))
    print("[OK] powershell cs host contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
