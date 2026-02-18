#!/usr/bin/env python3
"""Summarize recurring selfhost C++ compile error patterns."""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path


def normalize_error_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^.*?:\d+:\d+:\s*error:\s*", "", line)
    line = re.sub(r"‘[^’]*’", "<?>", line)
    line = re.sub(r"'[^']*'", "'<?>'", line)
    line = re.sub(r"\b\d+\b", "N", line)
    return line


def main() -> int:
    log_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("selfhost/py2cpp.compile.log")
    if not log_path.exists():
        print(f"missing: {log_path}")
        return 1

    counter: Counter[str] = Counter()
    examples: dict[str, str] = {}
    total = 0
    with log_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if "error:" not in line:
                continue
            total += 1
            key = normalize_error_line(line)
            counter[key] += 1
            if key not in examples:
                examples[key] = line.strip()

    print(f"total_errors={total}")
    for msg, count in counter.most_common(20):
        print(f"{count:4d}  {msg}")
        print(f"      ex: {examples.get(msg, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
