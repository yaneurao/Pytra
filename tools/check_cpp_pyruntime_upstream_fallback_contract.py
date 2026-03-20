#!/usr/bin/env python3
"""Guard the object-only versus typed-lane boundary for cpp py_runtime shrink."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import cpp_pyruntime_upstream_fallback_contract as contract_mod
from src.toolchain.compiler import cpp_pyruntime_upstream_fallback_inventory as inventory_mod
from tools import check_cpp_pyruntime_contract_inventory as contract_inventory_mod
from tools import check_cpp_pyruntime_header_surface as header_surface_mod


def _row_map() -> dict[str, dict[str, object]]:
    return {
        row["inventory_id"]: row
        for row in inventory_mod.iter_cpp_pyruntime_upstream_fallback_inventory()
    }


def _collect_partition_issues() -> list[str]:
    issues: list[str] = []
    if not (ROOT / contract_mod.CPP_PYRUNTIME_UPSTREAM_FALLBACK_PLAN_JA).exists():
        issues.append(
            f"missing japanese plan: {contract_mod.CPP_PYRUNTIME_UPSTREAM_FALLBACK_PLAN_JA}"
        )
    if not (ROOT / contract_mod.CPP_PYRUNTIME_UPSTREAM_FALLBACK_PLAN_EN).exists():
        issues.append(
            f"missing english plan: {contract_mod.CPP_PYRUNTIME_UPSTREAM_FALLBACK_PLAN_EN}"
        )
    if contract_mod.BOUNDARY_CLASS_ORDER != (
        "object_only_compat_header",
        "any_object_boundary_header",
        "typed_lane_must_not_use",
    ):
        issues.append("boundary class order drifted")
    rows = _row_map()
    object_only = set(contract_mod.OBJECT_ONLY_COMPAT_HEADER_IDS)
    any_object = set(contract_mod.ANY_OBJECT_BOUNDARY_HEADER_IDS)
    typed_forbidden = set(contract_mod.TYPED_LANE_MUST_NOT_USE_IDS)
    if object_only & any_object or object_only & typed_forbidden or any_object & typed_forbidden:
        issues.append("boundary partitions overlap")
    inventory_ids = set(rows)
    if object_only | any_object | typed_forbidden != inventory_ids:
        issues.append("boundary partitions do not cover the full upstream fallback inventory")
    for inventory_id in sorted(object_only):
        row = rows.get(inventory_id)
        if row is None:
            issues.append(f"missing object-only header inventory id: {inventory_id}")
            continue
        if row["bucket"] != "header_bulk":
            issues.append(f"object-only header id escaped header bulk: {inventory_id}")
        if row["shrink_stage"] not in {
            "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-01",
            "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-02",
        }:
            issues.append(f"object-only header stage drifted: {inventory_id}")
    for inventory_id in sorted(any_object):
        row = rows.get(inventory_id)
        if row is None:
            issues.append(f"missing Any/object boundary inventory id: {inventory_id}")
            continue
        if row["bucket"] != "header_bulk":
            issues.append(f"Any/object boundary id escaped header bulk: {inventory_id}")
        if row["shrink_stage"] != "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-03":
            issues.append(f"Any/object boundary stage drifted: {inventory_id}")
    for inventory_id in sorted(typed_forbidden):
        row = rows.get(inventory_id)
        if row is None:
            issues.append(f"missing typed-lane forbidden inventory id: {inventory_id}")
            continue
        if row["bucket"] == "header_bulk":
            issues.append(f"typed-lane forbidden id leaked back into header bulk: {inventory_id}")
    return issues


def _collect_boundary_guard_issues() -> list[str]:
    issues: list[str] = []
    if header_surface_mod.EXPECTED_BUCKETS["object_bridge_mutation"] != {
        'static inline void py_append(object& v, const U& item) {'
    }:
        issues.append("header surface object-bridge mutation bucket drifted")
    if contract_inventory_mod.EXPECTED_BUCKETS["typed_lane_removable"] != set():
        issues.append("typed-lane removable bucket must stay empty until shrink slices land")
    object_bridge_required = contract_inventory_mod.EXPECTED_BUCKETS["object_bridge_required"]
    if object_bridge_required != {
        ("py_append", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
        ("py_pop", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
    }:
        issues.append("cross-runtime object-bridge required bucket drifted")
    shared = contract_inventory_mod.EXPECTED_BUCKETS["shared_runtime_contract"]
    if ("py_append", "src/toolchain/emit/cpp/emitter/cpp_emitter.py") in shared:
        issues.append("cpp typed-lane append re-entered the shared runtime contract bucket")
    if ("py_append", "src/toolchain/emit/cs/emitter/cs_emitter.py") in shared:
        issues.append("cross-runtime bytes append helper leaked into shared runtime contract bucket")
    return issues


def main() -> int:
    issues = _collect_partition_issues() + _collect_boundary_guard_issues()
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] cpp py_runtime upstream fallback boundary is locked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
