from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import powershell_cs_host_contract as contract_mod


JA_PLAN = ROOT / "docs/ja/plans/archive/20260312-p5-powershell-csharp-host-profile.md"
EN_PLAN = ROOT / "docs/en/plans/archive/20260312-p5-powershell-csharp-host-profile.md"
JA_TODO_ARCHIVE_INDEX = ROOT / "docs/ja/todo/archive/index.md"
EN_TODO_ARCHIVE_INDEX = ROOT / "docs/en/todo/archive/index.md"
JA_TODO_ARCHIVE_DAY = ROOT / "docs/ja/todo/archive/20260312.md"
EN_TODO_ARCHIVE_DAY = ROOT / "docs/en/todo/archive/20260312.md"
JA_README = ROOT / "docs/ja/README.md"
EN_README = ROOT / "README.md"
JA_HOWTO = ROOT / "docs/ja/tutorial/how-to-use.md"
EN_HOWTO = ROOT / "docs/en/how-to-use.md"

EXPECTED_JA_PLAN_PHRASES = (
    "PowerShell を新しい backend として実装する代わりに、既存の C# backend を PowerShell から起動する host profile を定義する。",
    "Windows / PowerShell 7 / .NET 系 toolchain を前提に、`pure PowerShell backend` より低コストな実行経路を確立する。",
    "PowerShell を target language とする pure backend 実装。",
    "PowerShell 5.1 と 7.x の完全互換保証。",
    "非 Windows 環境での PowerShell host 動作保証。",
    "[x] [ID: P5-POWERSHELL-CS-HOST-01-S1-01]",
    "[x] [ID: P5-POWERSHELL-CS-HOST-01-S2-01]",
    "[x] [ID: P5-POWERSHELL-CS-HOST-01-S2-02]",
    "[x] [ID: P5-POWERSHELL-CS-HOST-01-S3-01]",
    "[x] [ID: P5-POWERSHELL-CS-HOST-01-S4-01]",
    "`test/unit/toolchain/emit/cs/test_py2cs_smoke.py`",
    "`test/unit/tooling/test_powershell_cs_host_profile.py`",
    "`tools/check_powershell_cs_host_sample_parity.py`",
    "`test/unit/tooling/test_pytra_cli_powershell_cs_host_profile.py`",
    "`sample/py/01_mandelbrot.py`",
    "`src/pytra-cli.py`",
    "`src/toolchain/compiler/pytra_cli_profiles.py`",
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
    "[x] [ID: P5-POWERSHELL-CS-HOST-01-S3-01]",
    "[x] [ID: P5-POWERSHELL-CS-HOST-01-S4-01]",
    "`test/unit/toolchain/emit/cs/test_py2cs_smoke.py`",
    "`test/unit/tooling/test_powershell_cs_host_profile.py`",
    "`tools/check_powershell_cs_host_sample_parity.py`",
    "`test/unit/tooling/test_pytra_cli_powershell_cs_host_profile.py`",
    "`sample/py/01_mandelbrot.py`",
    "`src/pytra-cli.py`",
    "`src/toolchain/compiler/pytra_cli_profiles.py`",
    "`run.ps1`",
    "`src/Program.cs`",
    "`runtime/`",
    "`build/Program.exe`",
    "`public static void Main(string[] args)`",
    "`dotnet` -> `csc` -> `Add-Type`",
    "last non-canonical fallback",
)

EXPECTED_JA_ARCHIVE_INDEX_PHRASES = (
    "[2026-03-12 / P5-POWERSHELL-CS-HOST-01]",
    "../plans/archive/20260312-p5-powershell-csharp-host-profile.md",
)

EXPECTED_EN_ARCHIVE_INDEX_PHRASES = (
    "[2026-03-12 / P5-POWERSHELL-CS-HOST-01]",
    "../plans/archive/20260312-p5-powershell-csharp-host-profile.md",
)

EXPECTED_JA_ARCHIVE_DAY_PHRASES = (
    "## 2026-03-12 移管: C# backend 用 PowerShell host profile complete",
    "[ID: P5-POWERSHELL-CS-HOST-01]",
    "`pwsh + py2cs` host profile",
    "PowerShell を target language とする pure backend ではありません。",
)

EXPECTED_EN_ARCHIVE_DAY_PHRASES = (
    "## 2026-03-12 migration: PowerShell host profile for the C# backend complete",
    "[ID: P5-POWERSHELL-CS-HOST-01]",
    "`pwsh + py2cs` host profile",
    "PowerShell as a pure target backend remains out of scope.",
)

EXPECTED_JA_README_PHRASES = (
    "PowerShell、Dart、Julliaは対応作業中です。",
    "`pwsh + py2cs` host profile として整理中であり、pure backend ではありません。",
)

EXPECTED_EN_README_PHRASES = (
    "PowerShell, Dart, and Julia are currently in progress.",
    "PowerShell is being organized as a `pwsh + py2cs` host profile rather than a pure backend.",
)

EXPECTED_JA_HOWTO_PHRASES = (
    "## PowerShell host profile（実験中）",
    "`pwsh + py2cs` host profile を整理中です。",
    "PowerShell を target language とする pure backend ではありません。",
    "`dotnet -> csc -> Add-Type`",
    "`test/unit/toolchain/emit/cs/test_py2cs_smoke.py` は backend transpile smoke に留まります。",
)

EXPECTED_EN_HOWTO_PHRASES = (
    "## PowerShell Host Profile (Experimental)",
    "Pytra is currently organizing a `pwsh + py2cs` host profile.",
    "This is not a pure PowerShell target backend.",
    "`dotnet -> csc -> Add-Type`",
    "`test/unit/toolchain/emit/cs/test_py2cs_smoke.py` remains a backend-transpile smoke only.",
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
    if contract_mod.REPRESENTATIVE_VERIFICATION_LANES != {
        "existing_backend_smoke": "test/unit/toolchain/emit/cs/test_py2cs_smoke.py",
        "future_host_smoke": "test/unit/tooling/test_powershell_cs_host_profile.py",
        "sample_parity_input": "sample/py/01_mandelbrot.py",
        "future_sample_parity": "tools/check_powershell_cs_host_sample_parity.py",
        "cli_entrypoint": "src/pytra-cli.py",
        "cli_profile_inventory": "src/toolchain/compiler/pytra_cli_profiles.py",
        "future_cli_profile_regression": "test/unit/tooling/test_pytra_cli_powershell_cs_host_profile.py",
    }:
        issues.append("representative verification lanes drifted")
    if contract_mod.CURRENT_PY2CS_SMOKE_BASELINE != {
        "runner": "test/unit/toolchain/emit/cs/test_py2cs_smoke.py",
        "covers_backend_transpile": True,
        "covers_generated_program_cs": True,
        "covers_pwsh_launcher": False,
        "covers_runtime_source_bundling": False,
        "covers_build_driver_selection": False,
        "covers_compiled_execution": False,
        "covers_sample_parity": False,
        "covers_cli_profile_selection": False,
    }:
        issues.append("current py2cs smoke baseline drifted")
    if set(contract_mod.HOST_PROFILE_DELTA_FROM_PY2CS_SMOKE.keys()) != {
        "transpile_only_scope",
        "launcher_gap",
        "runtime_layout_gap",
        "driver_selection_gap",
        "compiled_execution_gap",
        "sample_parity_gap",
        "cli_profile_gap",
    }:
        issues.append("host profile delta key set drifted")
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
        "representative_verification_lanes",
        "current_py2cs_smoke_baseline",
        "host_profile_delta_from_py2cs_smoke",
        "non_goals",
        "output_layout",
        "entrypoint_contract",
        "runtime_cs_files",
        "launcher_responsibilities",
        "docs_targets",
        "user_caveat_summary",
    }:
        issues.append("contract manifest keys drifted")
    if contract_mod.REPRESENTATIVE_DOC_TARGETS != {
        "ja_readme": "docs/ja/README.md",
        "en_readme": "README.md",
        "ja_usage": "docs/ja/tutorial/how-to-use.md",
        "en_usage": "docs/en/how-to-use.md",
    }:
        issues.append("representative docs targets drifted")
    if set(contract_mod.USER_CAVEAT_SUMMARY.keys()) != {
        "not_pure_backend",
        "current_user_lane",
    }:
        issues.append("user caveat summary keys drifted")
    return issues


def _collect_docs_issues() -> list[str]:
    issues: list[str] = []
    ja_plan = JA_PLAN.read_text(encoding="utf-8")
    en_plan = EN_PLAN.read_text(encoding="utf-8")
    ja_todo_archive_index = JA_TODO_ARCHIVE_INDEX.read_text(encoding="utf-8")
    en_todo_archive_index = EN_TODO_ARCHIVE_INDEX.read_text(encoding="utf-8")
    ja_todo_archive_day = JA_TODO_ARCHIVE_DAY.read_text(encoding="utf-8")
    en_todo_archive_day = EN_TODO_ARCHIVE_DAY.read_text(encoding="utf-8")
    ja_readme = JA_README.read_text(encoding="utf-8")
    en_readme = EN_README.read_text(encoding="utf-8")
    ja_howto = JA_HOWTO.read_text(encoding="utf-8")
    en_howto = EN_HOWTO.read_text(encoding="utf-8")
    for phrase in EXPECTED_JA_PLAN_PHRASES:
        if phrase not in ja_plan:
            issues.append(f"missing phrase in ja plan: {phrase}")
    for phrase in EXPECTED_EN_PLAN_PHRASES:
        if phrase not in en_plan:
            issues.append(f"missing phrase in en plan: {phrase}")
    for phrase in EXPECTED_JA_ARCHIVE_INDEX_PHRASES:
        if phrase not in ja_todo_archive_index:
            issues.append(f"missing phrase in ja todo archive index: {phrase}")
    for phrase in EXPECTED_EN_ARCHIVE_INDEX_PHRASES:
        if phrase not in en_todo_archive_index:
            issues.append(f"missing phrase in en todo archive index: {phrase}")
    for phrase in EXPECTED_JA_ARCHIVE_DAY_PHRASES:
        if phrase not in ja_todo_archive_day:
            issues.append(f"missing phrase in ja todo archive day: {phrase}")
    for phrase in EXPECTED_EN_ARCHIVE_DAY_PHRASES:
        if phrase not in en_todo_archive_day:
            issues.append(f"missing phrase in en todo archive day: {phrase}")
    for phrase in EXPECTED_JA_README_PHRASES:
        if phrase not in ja_readme:
            issues.append(f"missing phrase in ja readme: {phrase}")
    for phrase in EXPECTED_EN_README_PHRASES:
        if phrase not in en_readme:
            issues.append(f"missing phrase in en readme: {phrase}")
    for phrase in EXPECTED_JA_HOWTO_PHRASES:
        if phrase not in ja_howto:
            issues.append(f"missing phrase in ja howto: {phrase}")
    for phrase in EXPECTED_EN_HOWTO_PHRASES:
        if phrase not in en_howto:
            issues.append(f"missing phrase in en howto: {phrase}")
    return issues


def main() -> int:
    issues = _collect_contract_issues() + _collect_docs_issues()
    if issues:
        raise SystemExit("\n".join(issues))
    print("[OK] powershell cs host contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
