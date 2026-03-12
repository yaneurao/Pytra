#!/usr/bin/env python3
"""Guard the residual thin-seam classification for the C++ py_runtime shrink plan."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_cpp_pyruntime_header_surface as header_surface
from tools import check_crossruntime_pyruntime_emitter_inventory as emitter_inventory


ACTIVE_TASK_ID = "P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01"
ACTIVE_PLAN_PATH = "docs/ja/plans/p5-cpp-pyruntime-residual-thin-seam-shrink.md"

OBJECT_BRIDGE_MUTATION_CLASSIFICATION = {
    "header_residual": {
        'static inline void py_append(object& v, const U& item) {'
    },
    "must_remain_crossruntime": {
        ("py_append", "src/backends/cs/emitter/cs_emitter.py"),
        ("py_pop", "src/backends/cs/emitter/cs_emitter.py"),
    },
    "already_backend_localized_cpp": set(),
}

SHARED_TYPE_ID_THIN_SEAM_CLASSIFICATION = {
    "cpp": emitter_inventory.FUTURE_CPP_SHARED_TYPE_ID_CLASSIFICATION,
    "rs": emitter_inventory.FUTURE_RS_SHARED_TYPE_ID_CLASSIFICATION,
    "cs": emitter_inventory.FUTURE_CS_SHARED_TYPE_ID_CLASSIFICATION,
}

SHARED_TYPE_ID_THIN_SEAM_TARGETS = {
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
}


def _collect_issues() -> list[str]:
    issues: list[str] = []
    if not (ROOT / ACTIVE_PLAN_PATH).exists():
        issues.append(f"active plan missing: {ACTIVE_PLAN_PATH}")
    if (
        header_surface.EXPECTED_BUCKETS["object_bridge_mutation"]
        != OBJECT_BRIDGE_MUTATION_CLASSIFICATION["header_residual"]
    ):
        issues.append("object-bridge header residual drifted")
    if (
        emitter_inventory.EXPECTED_BUCKETS["crossruntime_mutation_helper_residual"]
        != OBJECT_BRIDGE_MUTATION_CLASSIFICATION["must_remain_crossruntime"]
    ):
        issues.append("cross-runtime mutation seam classification drifted")
    if (
        emitter_inventory.EXPECTED_BUCKETS["cpp_emitter_object_bridge_residual"]
        != OBJECT_BRIDGE_MUTATION_CLASSIFICATION["already_backend_localized_cpp"]
    ):
        issues.append("cpp object-bridge residual classification drifted")
    if emitter_inventory.FUTURE_FOLLOWUP_TASK_ID != ACTIVE_TASK_ID:
        issues.append("future follow-up task drifted from active residual-thin-seam task")
    if emitter_inventory.FUTURE_FOLLOWUP_PLAN_PATH != ACTIVE_PLAN_PATH:
        issues.append("future follow-up plan path drifted from active residual-thin-seam plan")
    if (
        emitter_inventory.FUTURE_CPP_SHARED_TYPE_ID_CLASSIFICATION
        != SHARED_TYPE_ID_THIN_SEAM_TARGETS["cpp"]
    ):
        issues.append("cpp shared type-id thin-seam classification drifted")
    if (
        emitter_inventory.FUTURE_RS_SHARED_TYPE_ID_CLASSIFICATION
        != SHARED_TYPE_ID_THIN_SEAM_TARGETS["rs"]
    ):
        issues.append("rs shared type-id thin-seam classification drifted")
    if (
        emitter_inventory.FUTURE_CS_SHARED_TYPE_ID_CLASSIFICATION
        != SHARED_TYPE_ID_THIN_SEAM_TARGETS["cs"]
    ):
        issues.append("cs shared type-id thin-seam classification drifted")
    if emitter_inventory._collect_cpp_future_shared_type_id_classification_issues():
        issues.append("cpp future shared type-id classification helper reported drift")
    if emitter_inventory._collect_future_bucket_classification_issues(
        label="future rs shared type-id classification",
        classification=emitter_inventory.FUTURE_RS_SHARED_TYPE_ID_CLASSIFICATION,
        expected_future_reducible=SHARED_TYPE_ID_THIN_SEAM_TARGETS["rs"]["future_reducible"],
        expected_must_remain=SHARED_TYPE_ID_THIN_SEAM_TARGETS["rs"]["must_remain_until_runtime_task"],
        expected_bucket=emitter_inventory.EXPECTED_BUCKETS["rs_emitter_shared_type_id_residual"],
        required_prefix="src/backends/rs/",
    ):
        issues.append("rs future shared type-id classification helper reported drift")
    if emitter_inventory._collect_future_bucket_classification_issues(
        label="future cs shared type-id classification",
        classification=emitter_inventory.FUTURE_CS_SHARED_TYPE_ID_CLASSIFICATION,
        expected_future_reducible=SHARED_TYPE_ID_THIN_SEAM_TARGETS["cs"]["future_reducible"],
        expected_must_remain=SHARED_TYPE_ID_THIN_SEAM_TARGETS["cs"]["must_remain_until_runtime_task"],
        expected_bucket=emitter_inventory.EXPECTED_BUCKETS["cs_emitter_shared_type_id_residual"],
        required_prefix="src/backends/cs/",
    ):
        issues.append("cs future shared type-id classification helper reported drift")
    return issues


def main() -> int:
    issues = _collect_issues()
    if not issues:
        print("[OK] cpp py_runtime residual thin-seam classification is locked")
        return 0
    for issue in issues:
        print(issue, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
