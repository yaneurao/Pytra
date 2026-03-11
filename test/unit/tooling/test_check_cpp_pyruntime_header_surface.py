from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_cpp_pyruntime_header_surface as surface_mod


class CheckCppPyRuntimeHeaderSurfaceTest(unittest.TestCase):
    def test_expected_and_observed_surface_match(self) -> None:
        self.assertEqual(
            surface_mod._collect_observed_pairs(),
            surface_mod._collect_expected_pairs(),
        )

    def test_buckets_do_not_overlap(self) -> None:
        self.assertEqual(surface_mod._collect_bucket_overlaps(), [])

    def test_object_bridge_bucket_is_object_only(self) -> None:
        snippets = surface_mod.EXPECTED_BUCKETS["object_bridge_mutation"]
        self.assertTrue(all("object& v" in snippet for snippet in snippets))
        self.assertIn('static inline void py_append(object& v, const U& item) {', snippets)
        self.assertIn('static inline object py_pop(object& v) {', snippets)

    def test_typed_collection_compat_bucket_stays_small(self) -> None:
        snippets = surface_mod.EXPECTED_BUCKETS["typed_collection_compat"]
        self.assertEqual(snippets, set())

    def test_shared_type_id_bucket_is_thin_compat_only(self) -> None:
        snippets = surface_mod.EXPECTED_BUCKETS["shared_type_id_compat"]
        self.assertEqual(snippets, set())

    def test_handoff_issues_are_empty(self) -> None:
        self.assertEqual(surface_mod._collect_handoff_issues(), [])

    def test_handoff_bucket_partition_is_stable(self) -> None:
        self.assertEqual(
            surface_mod.HANDOFF_BUCKETS,
            {
                "removable_after_emitter_shrink": {
                    "typed_collection_compat",
                    "shared_type_id_compat",
                },
                "followup_residual_caller_owned": {
                    "object_bridge_mutation",
                },
            },
        )

    def test_followup_residual_caller_handoff_is_documented(self) -> None:
        self.assertEqual(
            surface_mod.FOLLOWUP_TASK_ID,
            "P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01",
        )
        self.assertEqual(
            surface_mod.FOLLOWUP_PLAN_PATH,
            "docs/ja/plans/p4-crossruntime-pyruntime-residual-caller-shrink.md",
        )


if __name__ == "__main__":
    unittest.main()
