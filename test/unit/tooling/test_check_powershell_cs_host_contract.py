from __future__ import annotations

import unittest

from src.toolchain.compiler import powershell_cs_host_contract as contract_mod
from tools import check_powershell_cs_host_contract as check_mod


class CheckPowershellCsHostContractTest(unittest.TestCase):
    def test_contract_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_contract_issues(), [])

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
                "non_goals",
                "output_layout",
                "entrypoint_contract",
                "runtime_cs_files",
                "launcher_responsibilities",
            },
        )
