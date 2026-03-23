#!/usr/bin/env python3
"""Summarize selfhost compile errors into coarse categories."""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path


def categorize(line: str) -> str | None:
    if "error:" not in line:
        return None
    if "before ‘default’" in line or "before 'default'" in line:
        return "keyword_collision"
    if "make_object(std::any)" in line or "cannot convert ‘object’" in line or "no match for ‘operator=’" in line:
        return "object_any_mismatch"
    if "RcHandle" in line and ".get(" in line:
        return "dict_attr_access_mismatch"
    return "other"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: selfhost_error_report.py <build.stderr.log>", file=sys.stderr)
        return 2
    p = Path(sys.argv[1])
    if not p.exists():
        print(f"missing file: {p}", file=sys.stderr)
        return 2
    counter: Counter[str] = Counter()
    for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
        cat = categorize(ln)
        if cat is not None:
            counter[cat] += 1
    total = sum(counter.values())
    print(f"total_errors={total}")
    for k, v in counter.most_common():
        print(f"{k}={v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

