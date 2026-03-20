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
                    ("py_append", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
                    ("py_pop", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
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
                        ("py_runtime_value_type_id", "src/toolchain/emit/cpp/emitter/cpp_emitter.py"),
                    },
                    "must_remain_until_runtime_task": {
                        ("py_runtime_value_isinstance", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
                        ("py_runtime_value_isinstance", "src/toolchain/emit/cpp/emitter/stmt.py"),
                        ("py_runtime_type_id_is_subtype", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
                        ("py_runtime_type_id_issubclass", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
                    },
                },
                "rs": {
                    "future_reducible": set(),
                    "must_remain_until_runtime_task": {
                        ("py_runtime_value_type_id", "src/toolchain/emit/rs/emitter/rs_emitter.py"),
                        ("py_runtime_value_isinstance", "src/toolchain/emit/rs/emitter/rs_emitter.py"),
                        ("py_runtime_type_id_is_subtype", "src/toolchain/emit/rs/emitter/rs_emitter.py"),
                        ("py_runtime_type_id_issubclass", "src/toolchain/emit/rs/emitter/rs_emitter.py"),
                    },
                },
                "cs": {
                    "future_reducible": set(),
                    "must_remain_until_runtime_task": {
                        ("py_runtime_value_type_id", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
                        ("py_runtime_value_isinstance", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
                        ("py_runtime_type_id_is_subtype", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
                        ("py_runtime_type_id_issubclass", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
                    },
                },
            },
        )

    def test_active_task_identity_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.ACTIVE_TASK_ID,
            "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01",
        )
        self.assertEqual(
            contract_mod.ACTIVE_PLAN_PATH,
            "docs/ja/plans/p2-cpp-pyruntime-upstream-fallback-shrink.md",
        )


if __name__ == "__main__":
    unittest.main()
