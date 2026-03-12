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

    def test_manifest_shape_is_fixed(self) -> None:
        self.assertEqual(
            set(contract_mod.build_powershell_cs_host_contract_manifest().keys()),
            {
                "profile",
                "assumptions",
                "required_executable_groups",
                "optional_host_mechanisms",
                "non_goals",
            },
        )
