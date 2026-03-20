from __future__ import annotations

import unittest

from src.toolchain.compiler import backend_conformance_inventory as inventory_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod
from tools import check_backend_conformance_inventory as check_mod


class CheckBackendConformanceInventoryTest(unittest.TestCase):
    def test_inventory_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_inventory_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_lane_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_lane_issues(), [])

    def test_fixture_class_order_is_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.CONFORMANCE_FIXTURE_CLASS_ORDER,
            ("syntax", "builtin", "pytra_std"),
        )

    def test_fixture_class_category_map_is_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.CONFORMANCE_FIXTURE_CLASS_CATEGORY_MAP,
            {
                "syntax": ("syntax",),
                "builtin": ("builtin",),
                "pytra_std": ("stdlib",),
            },
        )

    def test_fixture_allowed_prefixes_are_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.CONFORMANCE_FIXTURE_ALLOWED_PREFIXES,
            {
                "syntax": (
                    "test/fixtures/core/",
                    "test/fixtures/control/",
                    "test/fixtures/oop/",
                    "test/fixtures/collections/",
                ),
                "builtin": (
                    "test/fixtures/control/",
                    "test/fixtures/oop/",
                    "test/fixtures/signature/",
                    "test/fixtures/strings/",
                    "test/fixtures/typing/",
                ),
                "pytra_std": ("test/fixtures/stdlib/",),
            },
        )

    def test_lane_order_is_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.CONFORMANCE_LANE_ORDER,
            ("parse", "east", "east3_lowering", "emit", "runtime"),
        )

    def test_lane_harness_contract_is_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.iter_conformance_lane_harness(),
            (
                {
                    "lane": "parse",
                    "harness_kind": "frontend_parse_diagnostic",
                    "producer_entrypoint": "toolchain.compile.core_entrypoints.convert_source_to_east_with_backend",
                    "compare_unit": "success_or_structured_error",
                },
                {
                    "lane": "east",
                    "harness_kind": "east_document_compare",
                    "producer_entrypoint": "toolchain.compile.core_entrypoints.convert_source_to_east_with_backend",
                    "compare_unit": "normalized_east_document",
                },
                {
                    "lane": "east3_lowering",
                    "harness_kind": "east3_document_compare",
                    "producer_entrypoint": "toolchain.compile.east3.lower_east2_to_east3_document",
                    "compare_unit": "normalized_east3_document",
                },
                {
                    "lane": "emit",
                    "harness_kind": "backend_emit_compare",
                    "producer_entrypoint": "toolchain.compiler.backend_registry.emit_source_typed",
                    "compare_unit": "normalized_source_or_fail_closed_diagnostic",
                },
                {
                    "lane": "runtime",
                    "harness_kind": "runtime_parity_compare",
                    "producer_entrypoint": "tools.runtime_parity_check.main",
                    "compare_unit": "normalized_stdout_exitcode_artifact_digest",
                },
            ),
        )

    def test_fixture_lane_policy_is_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.iter_conformance_fixture_lane_policy(),
            (
                {
                    "fixture_class": "syntax",
                    "lane_policy": {
                        "parse": "required",
                        "east": "required",
                        "east3_lowering": "required",
                        "emit": "required",
                        "runtime": "case_runtime",
                    },
                },
                {
                    "fixture_class": "builtin",
                    "lane_policy": {
                        "parse": "required",
                        "east": "required",
                        "east3_lowering": "required",
                        "emit": "required",
                        "runtime": "case_runtime",
                    },
                },
                {
                    "fixture_class": "pytra_std",
                    "lane_policy": {
                        "parse": "required",
                        "east": "required",
                        "east3_lowering": "required",
                        "emit": "required",
                        "runtime": "module_runtime_strategy",
                    },
                },
            ),
        )

    def test_representative_conformance_feature_ids_match_p5_handoff(self) -> None:
        self.assertEqual(
            {entry["feature_id"] for entry in inventory_mod.iter_representative_conformance_fixture_inventory()},
            {entry["feature_id"] for entry in feature_contract_mod.iter_representative_conformance_handoff()},
        )

    def test_fixture_classification_is_fixed(self) -> None:
        fixture_classes = {
            entry["feature_id"]: entry["fixture_class"]
            for entry in inventory_mod.iter_representative_conformance_fixture_inventory()
        }
        self.assertEqual(
            fixture_classes,
            {
                "syntax.assign.tuple_destructure": "syntax",
                "syntax.expr.lambda": "syntax",
                "syntax.expr.list_comprehension": "syntax",
                "syntax.control.for_range": "syntax",
                "syntax.control.try_raise": "syntax",
                "syntax.oop.virtual_dispatch": "syntax",
                "builtin.iter.range": "builtin",
                "builtin.iter.enumerate": "builtin",
                "builtin.iter.zip": "builtin",
                "builtin.type.isinstance": "builtin",
                "builtin.bit.invert_and_mask": "builtin",
                "stdlib.json.loads_dumps": "pytra_std",
                "stdlib.pathlib.path_ops": "pytra_std",
                "stdlib.enum.enum_and_intflag": "pytra_std",
                "stdlib.argparse.parse_args": "pytra_std",
                "stdlib.math.imported_symbols": "pytra_std",
                "stdlib.re.sub": "pytra_std",
            },
        )

    def test_conformance_seed_manifest_contract_is_fixed(self) -> None:
        self.assertEqual(
            set(inventory_mod.build_backend_conformance_seed_manifest().keys()),
            {
                "inventory_version",
                "fixture_class_order",
                "fixture_class_category_map",
                "fixture_allowed_prefixes",
                "lane_order",
                "lane_harness",
                "fixture_lane_policy",
                "representative_conformance_fixtures",
            },
        )


if __name__ == "__main__":
    unittest.main()
