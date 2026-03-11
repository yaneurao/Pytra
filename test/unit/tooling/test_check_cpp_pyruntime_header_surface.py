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
        self.assertEqual(
            snippets,
            {
                'static inline uint32 py_runtime_type_id(const T& v) {',
                'static inline bool py_isinstance(const T& value, uint32 expected_type_id) {',
            },
        )


if __name__ == "__main__":
    unittest.main()
