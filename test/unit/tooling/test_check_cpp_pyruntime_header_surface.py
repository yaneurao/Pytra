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
        self.assertEqual(len(snippets), 1)

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
            "P0-CPP-PYRUNTIME-FINAL-SHRINK-01",
        )
        self.assertEqual(
            surface_mod.FOLLOWUP_PLAN_PATH,
            "docs/ja/plans/archive/20260312-p0-cpp-pyruntime-final-shrink.md",
        )

    def test_bundle_order_is_locked_to_active_final_shrink(self) -> None:
        self.assertEqual(
            surface_mod.BUNDLE_ORDER,
            (
                "P0-CPP-PYRUNTIME-FINAL-SHRINK-01-S1-01",
                "P0-CPP-PYRUNTIME-FINAL-SHRINK-01-S2-01",
                "P0-CPP-PYRUNTIME-FINAL-SHRINK-01-S2-02",
                "P0-CPP-PYRUNTIME-FINAL-SHRINK-01-S3-01",
            ),
        )

    def test_target_end_state_is_locked(self) -> None:
        self.assertEqual(
            surface_mod.TARGET_END_STATE,
            {
                "object_bridge_mutation": "remove or reduce to the minimum object-only seam",
                "typed_collection_compat": "must stay empty",
                "shared_type_id_compat": "must stay empty",
                "shared_type_id_thin_helpers": {
                    "py_runtime_type_id_is_subtype",
                    "py_runtime_type_id_issubclass",
                    "py_runtime_object_type_id",
                    "py_runtime_object_isinstance",
                },
            },
        )

    def test_header_rejects_legacy_generic_alias_signatures(self) -> None:
        self.assertEqual(
            surface_mod.LEGACY_ALIAS_SIGNATURES,
            {
                "static inline uint32 py_runtime_type_id(",
                "static inline bool py_isinstance(",
                "static inline bool py_is_subtype(",
                "static inline bool py_issubclass(",
            },
        )
        self.assertEqual(
            [
                issue
                for issue in surface_mod._collect_handoff_issues()
                if issue.startswith("legacy generic alias returned to py_runtime.h:")
            ],
            [],
        )


if __name__ == "__main__":
    unittest.main()
