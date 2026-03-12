from __future__ import annotations

import unittest

from toolchain.compiler import backend_parity_longtail_rollout_inventory as inventory_mod
from tools import check_backend_parity_longtail_rollout_inventory as check_mod


class CheckBackendParityLongtailRolloutInventoryTest(unittest.TestCase):
    def test_inventory_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_inventory_issues(), [])

    def test_bundle_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_bundle_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_backend_order_and_next_bundle_are_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.LONGTAIL_BACKEND_ORDER,
            ("js", "ts", "lua", "rb", "php"),
        )
        self.assertEqual(
            tuple(bundle["bundle_id"] for bundle in inventory_mod.iter_longtail_rollout_bundles()),
            ("js_ts_bundle", "lua_rb_php_bundle"),
        )
        self.assertEqual(inventory_mod.LONGTAIL_ROLLOUT_HANDOFF_V1["completed_backends"], ("js", "ts"))
        self.assertEqual(inventory_mod.LONGTAIL_ROLLOUT_HANDOFF_V1["next_backend"], "lua")
        self.assertEqual(inventory_mod.LONGTAIL_ROLLOUT_HANDOFF_V1["next_bundle"], "lua_rb_php_bundle")

    def test_bundle_feature_pairs_cover_exact_residual_set(self) -> None:
        residual_pairs = {
            (cell["backend"], cell["feature_id"])
            for cell in inventory_mod.iter_longtail_rollout_residual_cells()
        }
        bundled_pairs = {
            (backend, feature_id)
            for bundle in inventory_mod.iter_longtail_rollout_bundles()
            for backend, feature_ids in bundle["feature_ids_by_backend"].items()
            for feature_id in feature_ids
        }
        self.assertEqual(residual_pairs, bundled_pairs)

    def test_residual_feature_ids_by_backend_are_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.LONGTAIL_RESIDUAL_FEATURE_IDS_BY_BACKEND_V1,
            {
                "js": (
                ),
                "ts": (
                ),
                "lua": (
                    "syntax.assign.tuple_destructure",
                    "syntax.expr.lambda",
                    "syntax.expr.list_comprehension",
                    "syntax.control.try_raise",
                    "builtin.iter.enumerate",
                    "stdlib.json.loads_dumps",
                    "stdlib.pathlib.path_ops",
                    "stdlib.enum.enum_and_intflag",
                    "stdlib.argparse.parse_args",
                    "stdlib.math.imported_symbols",
                    "stdlib.re.sub",
                ),
                "rb": (
                    "syntax.assign.tuple_destructure",
                    "syntax.expr.lambda",
                    "syntax.expr.list_comprehension",
                    "syntax.control.for_range",
                    "syntax.control.try_raise",
                    "builtin.iter.range",
                    "builtin.iter.enumerate",
                    "builtin.iter.zip",
                    "stdlib.json.loads_dumps",
                    "stdlib.pathlib.path_ops",
                    "stdlib.enum.enum_and_intflag",
                    "stdlib.argparse.parse_args",
                    "stdlib.math.imported_symbols",
                    "stdlib.re.sub",
                ),
                "php": (
                    "syntax.assign.tuple_destructure",
                    "syntax.expr.lambda",
                    "syntax.expr.list_comprehension",
                    "syntax.control.try_raise",
                    "builtin.iter.enumerate",
                    "stdlib.json.loads_dumps",
                    "stdlib.pathlib.path_ops",
                    "stdlib.enum.enum_and_intflag",
                    "stdlib.argparse.parse_args",
                    "stdlib.math.imported_symbols",
                    "stdlib.re.sub",
                ),
            },
        )


if __name__ == "__main__":
    unittest.main()
