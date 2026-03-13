#!/usr/bin/env python3
"""Guard the baseline inventory for the cpp py_runtime upstream-fallback shrink."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import cpp_pyruntime_upstream_fallback_inventory as inventory_mod


TEXT_SUFFIXES = {".py", ".cpp", ".h", ".md"}


def _iter_text_files(scope: Path) -> list[Path]:
    if scope.is_file():
        return [scope]
    return [
        path
        for path in sorted(scope.rglob("*"))
        if path.is_file() and path.suffix in TEXT_SUFFIXES
    ]


def _count_matches(scope_rel: str, matcher_kind: str, needle: str) -> int:
    scope = ROOT / scope_rel
    if matcher_kind == "literal":
        return sum(
            path.read_text(encoding="utf-8").count(needle)
            for path in _iter_text_files(scope)
        )
    if matcher_kind == "regex":
        pattern = re.compile(needle)
        return sum(
            len(pattern.findall(path.read_text(encoding="utf-8")))
            for path in _iter_text_files(scope)
        )
    raise ValueError(f"unsupported matcher kind: {matcher_kind}")


def _collect_inventory_issues() -> list[str]:
    issues: list[str] = []
    rows = inventory_mod.iter_cpp_pyruntime_upstream_fallback_inventory()
    seen_ids: set[str] = set()
    seen_buckets: set[str] = set()
    if inventory_mod.HEADER_LINE_BASELINE <= 0:
        issues.append("header line baseline must stay positive")
    for row in rows:
        inventory_id = row["inventory_id"]
        if inventory_id in seen_ids:
            issues.append(f"duplicate inventory id: {inventory_id}")
        seen_ids.add(inventory_id)
        bucket = row["bucket"]
        if bucket not in inventory_mod.INVENTORY_BUCKET_ORDER:
            issues.append(f"unknown inventory bucket: {inventory_id}: {bucket}")
        seen_buckets.add(bucket)
        matcher_kind = row["matcher_kind"]
        if matcher_kind not in inventory_mod.MATCHER_KIND_ORDER:
            issues.append(f"unknown matcher kind: {inventory_id}: {matcher_kind}")
        if row["shrink_stage"] not in inventory_mod.SHRINK_STAGE_ORDER:
            issues.append(
                f"unknown shrink stage: {inventory_id}: {row['shrink_stage']}"
            )
        if row["expected_count"] <= 0:
            issues.append(f"non-positive expected count: {inventory_id}")
        scope = ROOT / row["scope_rel"]
        if not scope.exists():
            issues.append(f"missing scope path: {inventory_id}: {row['scope_rel']}")
        for ref in row["evidence_refs"]:
            rel = ref["relpath"]
            path = ROOT / rel
            if not path.exists():
                issues.append(f"missing evidence path: {inventory_id}: {rel}")
                continue
            text = path.read_text(encoding="utf-8")
            if ref["needle"] not in text:
                issues.append(
                    f"missing evidence needle: {inventory_id}: {rel}: {ref['needle']}"
                )
    bucket_order = set(inventory_mod.INVENTORY_BUCKET_ORDER)
    if not seen_buckets <= bucket_order:
        issues.append("inventory buckets escaped the fixed upstream-fallback taxonomy")
    required_nonempty = {"header_bulk", "cpp_emitter_residual"}
    if not required_nonempty <= seen_buckets:
        issues.append("required upstream-fallback buckets became empty")
    return issues


def _collect_inventory_count_issues() -> list[str]:
    issues: list[str] = []
    for row in inventory_mod.iter_cpp_pyruntime_upstream_fallback_inventory():
        actual = _count_matches(
            scope_rel=row["scope_rel"],
            matcher_kind=row["matcher_kind"],
            needle=row["needle"],
        )
        if actual != row["expected_count"]:
            issues.append(
                f"baseline count drifted: {row['inventory_id']}: {actual} != {row['expected_count']}"
            )
    return issues


def _collect_header_line_issues() -> list[str]:
    header = ROOT / "src/runtime/cpp/native/core/py_runtime.h"
    with header.open("r", encoding="utf-8") as handle:
        actual = sum(1 for _ in handle)
    if actual != inventory_mod.HEADER_LINE_BASELINE:
        return [
            "header line baseline drifted: "
            f"{actual} != {inventory_mod.HEADER_LINE_BASELINE}"
        ]
    return []


def main() -> int:
    issues = (
        _collect_inventory_issues()
        + _collect_inventory_count_issues()
        + _collect_header_line_issues()
    )
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] cpp py_runtime upstream fallback inventory is locked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
