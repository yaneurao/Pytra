from __future__ import annotations

import unittest

from src.toolchain.compiler import powershell_cs_host_contract as contract_mod
from tools import check_powershell_cs_host_contract as check_mod


class CheckPowershellCsHostContractTest(unittest.TestCase):
    """Retired: C# host profile plan was replaced by native PowerShell backend (2026-03-20).

    These tests verify the frozen contract snapshot and remain to prevent
    accidental reuse of the old contract module.  The docs-drift check is
    skipped because the documentation now describes the native backend.
    """

    def test_contract_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_contract_issues(), [])

    @unittest.skip("Retired: docs now describe native PowerShell backend, not C# host profile")
    def test_docs_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_docs_issues(), [])

    def test_representative_host_profile_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.REPRESENTATIVE_HOST_PROFILE,
            {
                "profile_id": "powershell_cs_host_v1",
                "backend": "cs",
                "host_shell": "pwsh",
                "host_shell_version": "7.x",
                "host_os": "windows",
                "toolchain_policy": "dotnet_or_csc_required",
            },
        )

    def test_required_executable_groups_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.REQUIRED_EXECUTABLE_GROUPS,
            {
                "host_shell": ("pwsh",),
                "compiler_driver": ("dotnet", "csc"),
            },
        )
        self.assertEqual(contract_mod.OPTIONAL_HOST_MECHANISMS, ("Add-Type",))

    def test_build_driver_priority_and_requirements_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.REPRESENTATIVE_BUILD_DRIVER_PRIORITY,
            (
                "dotnet_build",
                "csc_compile",
                "add_type_load",
            ),
        )
        self.assertEqual(
            contract_mod.BUILD_DRIVER_EXECUTABLE_REQUIREMENTS,
            {
                "dotnet_build": ("pwsh", "dotnet"),
                "csc_compile": ("pwsh", "csc"),
                "add_type_load": ("pwsh",),
            },
        )

    def test_build_driver_fail_closed_rule_keys_are_fixed(self) -> None:
        self.assertEqual(
            set(contract_mod.BUILD_DRIVER_FAIL_CLOSED_RULES.keys()),
            {
                "dotnet_build",
                "csc_compile",
                "add_type_load",
            },
        )

    def test_verification_lanes_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.REPRESENTATIVE_VERIFICATION_LANES,
            {
                "existing_backend_smoke": "test/unit/toolchain/emit/cs/test_py2cs_smoke.py",
                "future_host_smoke": "test/unit/tooling/test_powershell_cs_host_profile.py",
                "sample_parity_input": "sample/py/01_mandelbrot.py",
                "future_sample_parity": "tools/check_powershell_cs_host_sample_parity.py",
                "cli_entrypoint": "src/pytra-cli.py",
                "cli_profile_inventory": "src/toolchain/compiler/pytra_cli_profiles.py",
                "future_cli_profile_regression": "test/unit/tooling/test_pytra_cli_powershell_cs_host_profile.py",
            },
        )

    def test_current_py2cs_smoke_baseline_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.CURRENT_PY2CS_SMOKE_BASELINE,
            {
                "runner": "test/unit/toolchain/emit/cs/test_py2cs_smoke.py",
                "covers_backend_transpile": True,
                "covers_generated_program_cs": True,
                "covers_pwsh_launcher": False,
                "covers_runtime_source_bundling": False,
                "covers_build_driver_selection": False,
                "covers_compiled_execution": False,
                "covers_sample_parity": False,
                "covers_cli_profile_selection": False,
            },
        )

    def test_host_profile_delta_keys_are_fixed(self) -> None:
        self.assertEqual(
            set(contract_mod.HOST_PROFILE_DELTA_FROM_PY2CS_SMOKE.keys()),
            {
                "transpile_only_scope",
                "launcher_gap",
                "runtime_layout_gap",
                "driver_selection_gap",
                "compiled_execution_gap",
                "sample_parity_gap",
                "cli_profile_gap",
            },
        )

    def test_non_goals_are_fixed(self) -> None:
        self.assertEqual(
            set(contract_mod.NON_GOALS.keys()),
            {
                "pure_powershell_backend",
                "csharp_backend_rewrite",
                "powershell_5_1_full_compat",
                "non_windows_support",
            },
        )

    def test_output_layout_and_entrypoint_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.REPRESENTATIVE_OUTPUT_LAYOUT,
            {
                "launcher_rel": "run.ps1",
                "generated_entry_rel": "src/Program.cs",
                "runtime_source_dir_rel": "runtime",
                "build_output_dir_rel": "build",
                "build_artifact_rel": "build/Program.exe",
            },
        )
        self.assertEqual(
            contract_mod.REPRESENTATIVE_ENTRYPOINT_CONTRACT,
            {
                "class_name": "Program",
                "method_name": "Main",
                "signature": "public static void Main(string[] args)",
                "generated_entry_owns_main": True,
                "runtime_sources_define_main": False,
            },
        )

    def test_runtime_cs_files_and_launcher_responsibilities_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.REPRESENTATIVE_RUNTIME_CS_FILES,
            (
                "py_runtime.cs",
                "time.cs",
                "math.cs",
                "pathlib.cs",
                "json.cs",
                "png.cs",
                "gif.cs",
            ),
        )
        self.assertEqual(
            set(contract_mod.LAUNCHER_RESPONSIBILITIES.keys()),
            {
                "stage_generated_entry",
                "stage_runtime_sources",
                "delegate_compile_or_load",
                "forward_program_args",
                "fail_closed_missing_layout",
            },
        )

    def test_manifest_shape_is_fixed(self) -> None:
        self.assertEqual(
            set(contract_mod.build_powershell_cs_host_contract_manifest().keys()),
            {
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
            },
        )

    def test_docs_targets_and_user_caveat_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.REPRESENTATIVE_DOC_TARGETS,
            {
                "ja_readme": "docs/ja/README.md",
                "en_readme": "README.md",
                "ja_usage": "docs/ja/tutorial/how-to-use.md",
                "en_usage": "docs/en/how-to-use.md",
            },
        )
        self.assertEqual(
            set(contract_mod.USER_CAVEAT_SUMMARY.keys()),
            {
                "not_pure_backend",
                "current_user_lane",
            },
        )
