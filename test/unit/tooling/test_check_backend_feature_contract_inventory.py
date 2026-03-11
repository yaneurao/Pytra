from __future__ import annotations

import unittest

from src.toolchain.compiler import backend_feature_contract_inventory as inventory_mod
from tools import check_backend_feature_contract_inventory as check_mod


class CheckBackendFeatureContractInventoryTest(unittest.TestCase):
    def test_inventory_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_inventory_issues(), [])

    def test_categories_have_stable_order(self) -> None:
        self.assertEqual(inventory_mod.CATEGORY_ORDER, ("syntax", "builtin", "stdlib"))

    def test_category_naming_rules_are_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.CATEGORY_NAMING_RULES,
            {
                "syntax": "syntax.<area>.<feature>",
                "builtin": "builtin.<domain>.<feature>",
                "stdlib": "stdlib.<module>.<feature>",
            },
        )

    def test_representative_inventory_contains_all_categories(self) -> None:
        categories = {entry["category"] for entry in inventory_mod.iter_representative_feature_inventory()}
        self.assertEqual(categories, set(inventory_mod.CATEGORY_ORDER))

    def test_representative_inventory_ids_are_stable(self) -> None:
        self.assertEqual(
            {entry["feature_id"] for entry in inventory_mod.iter_representative_feature_inventory()},
            {
                "syntax.assign.tuple_destructure",
                "syntax.expr.lambda",
                "syntax.expr.list_comprehension",
                "syntax.control.for_range",
                "syntax.control.try_raise",
                "syntax.oop.virtual_dispatch",
                "builtin.iter.range",
                "builtin.iter.enumerate",
                "builtin.iter.zip",
                "builtin.type.isinstance",
                "builtin.bit.invert_and_mask",
                "stdlib.json.loads_dumps",
                "stdlib.pathlib.path_ops",
                "stdlib.enum.enum_and_intflag",
                "stdlib.argparse.parse_args",
                "stdlib.math.imported_symbols",
                "stdlib.re.sub",
            },
        )


if __name__ == "__main__":
    unittest.main()
