#!/usr/bin/env python3
"""Guard the residual helper categories that remain in py_runtime.h."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HEADER = ROOT / "src/runtime/cpp/native/core/py_runtime.h"

EXPECTED_BUCKETS = {
    "object_bridge_mutation": {
        'static inline void py_append(object& v, const U& item) {',
        'static inline void py_set_at(object& v, I idx, const U& item) {',
        'static inline void py_extend(object& v, const list<object>& items) {',
        'static inline void py_extend(object& v, const object& items) {',
        'static inline object py_pop(object& v) {',
        'static inline object py_pop(object& v, int64 idx) {',
        'static inline void py_clear(object& v) {',
        'static inline void py_reverse(object& v) {',
        'static inline void py_sort(object& v) {',
    },
    "typed_collection_compat": set(),
    "shared_type_id_compat": set(),
}

HANDOFF_BUCKETS = {
    "removable_after_emitter_shrink": {
        "typed_collection_compat",
        "shared_type_id_compat",
    },
    "followup_residual_caller_owned": {
        "object_bridge_mutation",
    },
}

FOLLOWUP_TASK_ID = "P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01"
FOLLOWUP_PLAN_PATH = "docs/ja/plans/p4-crossruntime-pyruntime-residual-caller-shrink.md"


def _header_text() -> str:
    return HEADER.read_text(encoding="utf-8")


def _collect_observed_pairs() -> set[tuple[str, str]]:
    text = _header_text()
    observed: set[tuple[str, str]] = set()
    for bucket, snippets in EXPECTED_BUCKETS.items():
        for snippet in snippets:
            if snippet in text:
                observed.add((bucket, snippet))
    return observed


def _collect_expected_pairs() -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for bucket, snippets in EXPECTED_BUCKETS.items():
        for snippet in snippets:
            out.add((bucket, snippet))
    return out


def _collect_bucket_overlaps() -> list[str]:
    issues: list[str] = []
    bucket_names = list(EXPECTED_BUCKETS.keys())
    for idx, left_name in enumerate(bucket_names):
        left = EXPECTED_BUCKETS[left_name]
        for right_name in bucket_names[idx + 1 :]:
            overlap = left & EXPECTED_BUCKETS[right_name]
            for snippet in sorted(overlap):
                issues.append(
                    f"bucket overlap: {left_name} and {right_name} both include {snippet}"
                )
    return issues


def _collect_inventory_issues() -> list[str]:
    observed = _collect_observed_pairs()
    expected = _collect_expected_pairs()
    issues = _collect_bucket_overlaps()
    for bucket, snippet in sorted(expected - observed):
        issues.append(f"expected header snippet missing: {bucket}: {snippet}")
    return issues


def _collect_handoff_issues() -> list[str]:
    issues: list[str] = []
    bucket_names = set(EXPECTED_BUCKETS.keys())
    removable = set(HANDOFF_BUCKETS["removable_after_emitter_shrink"])
    residual = set(HANDOFF_BUCKETS["followup_residual_caller_owned"])
    if removable | residual != bucket_names:
        issues.append("handoff buckets do not cover the same header buckets as EXPECTED_BUCKETS")
    if removable & residual:
        issues.append("handoff buckets overlap between removable and follow-up residual ownership")
    for bucket in sorted(removable):
        if EXPECTED_BUCKETS[bucket] != set():
            issues.append(f"removable-after-emitter bucket is not empty: {bucket}")
    for bucket in sorted(residual):
        if EXPECTED_BUCKETS[bucket] == set():
            issues.append(f"follow-up residual bucket unexpectedly empty: {bucket}")
    if not (ROOT / FOLLOWUP_PLAN_PATH).exists():
        issues.append(f"follow-up plan missing: {FOLLOWUP_PLAN_PATH}")
    return issues


def main() -> int:
    issues = _collect_inventory_issues()
    issues.extend(_collect_handoff_issues())
    if not issues:
        print("[OK] cpp py_runtime header surface is classified")
        return 0
    for issue in issues:
        print(issue, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
