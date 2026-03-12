from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_cpp_pyruntime_residual_thin_seam_contract as contract_mod


class CheckCppPyRuntimeResidualThinSeamContractTest(unittest.TestCase):
    def test_contract_issues_are_empty(self) -> None:
        self.assertEqual(contract_mod._collect_issues(), [])

    def test_object_bridge_mutation_classification_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.OBJECT_BRIDGE_MUTATION_CLASSIFICATION,
            {
                "header_residual": {
                    'static inline void py_append(object& v, const U& item) {'
                },
                "must_remain_crossruntime": {
                    ("py_append", "src/backends/cs/emitter/cs_emitter.py"),
                    ("py_pop", "src/backends/cs/emitter/cs_emitter.py"),
                },
                "already_backend_localized_cpp": set(),
            },
        )

    def test_shared_type_id_classification_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.SHARED_TYPE_ID_THIN_SEAM_CLASSIFICATION,
            contract_mod.SHARED_TYPE_ID_THIN_SEAM_TARGETS,
        )
        self.assertEqual(
            contract_mod.SHARED_TYPE_ID_THIN_SEAM_TARGETS,
            {
                "cpp": {
                    "future_reducible": {
                        ("py_runtime_value_type_id", "src/backends/cpp/emitter/cpp_emitter.py"),
                    },
                    "must_remain_until_runtime_task": {
                        ("py_runtime_value_isinstance", "src/backends/cpp/emitter/runtime_expr.py"),
                        ("py_runtime_value_isinstance", "src/backends/cpp/emitter/stmt.py"),
                        ("py_runtime_type_id_is_subtype", "src/backends/cpp/emitter/runtime_expr.py"),
                        ("py_runtime_type_id_issubclass", "src/backends/cpp/emitter/runtime_expr.py"),
                    },
                },
                "rs": {
                    "future_reducible": set(),
                    "must_remain_until_runtime_task": {
                        ("py_runtime_value_type_id", "src/backends/rs/emitter/rs_emitter.py"),
                        ("py_runtime_value_isinstance", "src/backends/rs/emitter/rs_emitter.py"),
                        ("py_runtime_type_id_is_subtype", "src/backends/rs/emitter/rs_emitter.py"),
                        ("py_runtime_type_id_issubclass", "src/backends/rs/emitter/rs_emitter.py"),
                    },
                },
                "cs": {
                    "future_reducible": set(),
                    "must_remain_until_runtime_task": {
                        ("py_runtime_value_type_id", "src/backends/cs/emitter/cs_emitter.py"),
                        ("py_runtime_value_isinstance", "src/backends/cs/emitter/cs_emitter.py"),
                        ("py_runtime_type_id_is_subtype", "src/backends/cs/emitter/cs_emitter.py"),
                        ("py_runtime_type_id_issubclass", "src/backends/cs/emitter/cs_emitter.py"),
                    },
                },
            },
        )

    def test_active_task_identity_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.ACTIVE_TASK_ID,
            "P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01",
        )
        self.assertEqual(
            contract_mod.ACTIVE_PLAN_PATH,
            "docs/ja/plans/p5-cpp-pyruntime-residual-thin-seam-shrink.md",
        )


if __name__ == "__main__":
    unittest.main()
