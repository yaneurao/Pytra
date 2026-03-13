from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.toolchain.compiler import multilang_extern_runtime_realign_contract as contract_mod
from src.toolchain.frontends import extern_var
from tools import check_multilang_extern_runtime_realign_contract as check_mod


class CheckMultilangExternRuntimeRealignContractTest(unittest.TestCase):
    def test_contract_shape_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_contract_shape_issues(), [])

    def test_runtime_symbol_index_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_runtime_symbol_index_issues(), [])

    def test_doc_wiring_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_doc_wiring_issues(), [])

    def test_extern_category_order_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.EXTERN_CATEGORY_ORDER,
            (
                "runtime_extern_declaration_only",
                "native_owner_implementation",
                "ambient_global_extern",
                "host_fallback_extern_expr",
            ),
        )

    def test_ambient_extern_targets_are_fixed(self) -> None:
        self.assertEqual(contract_mod.AMBIENT_EXTERN_TARGETS, ("js", "ts"))
        self.assertEqual(
            tuple(sorted(extern_var._AMBIENT_EXTERN_SUPPORTED_TARGETS)),
            contract_mod.AMBIENT_EXTERN_TARGETS,
        )

    def test_runtime_extern_key_contract_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.RUNTIME_EXTERN_CONTRACT_ALLOWED_KEYS,
            ("schema_version", "function_symbols", "value_symbols"),
        )
        self.assertEqual(
            contract_mod.RUNTIME_EXTERN_SYMBOL_ALLOWED_KEYS,
            ("schema_version", "kind"),
        )
        self.assertEqual(contract_mod.RUNTIME_EXTERN_SYMBOL_KIND_ORDER, ("function", "value"))

    def test_runtime_module_order_is_inventory_order(self) -> None:
        self.assertEqual(
            contract_mod.RUNTIME_EXTERN_MODULE_ORDER,
            (
                "pytra.std.math",
                "pytra.std.time",
                "pytra.std.os",
                "pytra.std.os_path",
                "pytra.std.sys",
                "pytra.std.glob",
                "pytra.built_in.io_ops",
                "pytra.built_in.scalar_ops",
            ),
        )

    def test_contract_manifest_shape_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.build_multilang_extern_runtime_realign_contract_manifest(),
            {
                "category_order": contract_mod.EXTERN_CATEGORY_ORDER,
                "ambient_targets": contract_mod.AMBIENT_EXTERN_TARGETS,
                "runtime_module_order": contract_mod.RUNTIME_EXTERN_MODULE_ORDER,
                "runtime_extern_contract_allowed_keys": contract_mod.RUNTIME_EXTERN_CONTRACT_ALLOWED_KEYS,
                "runtime_extern_symbol_allowed_keys": contract_mod.RUNTIME_EXTERN_SYMBOL_ALLOWED_KEYS,
                "runtime_extern_symbol_kind_order": contract_mod.RUNTIME_EXTERN_SYMBOL_KIND_ORDER,
            },
        )

    def test_plan_and_spec_doc_targets_are_fixed(self) -> None:
        self.assertEqual(
            set(contract_mod.SPEC_WIRING_RULES_JA.keys()),
            {"docs/ja/spec/spec-abi.md", "docs/ja/spec/spec-runtime.md"},
        )
        self.assertEqual(
            set(contract_mod.SPEC_WIRING_RULES_EN.keys()),
            {"docs/en/spec/spec-abi.md", "docs/en/spec/spec-runtime.md"},
        )
        self.assertEqual(
            set(contract_mod.PLAN_WIRING_RULES_JA.keys()),
            {"docs/ja/plans/p2-multilang-extern-runtime-realign.md"},
        )
        self.assertEqual(
            set(contract_mod.PLAN_WIRING_RULES_EN.keys()),
            {"docs/en/plans/p2-multilang-extern-runtime-realign.md"},
        )


if __name__ == "__main__":
    unittest.main()
