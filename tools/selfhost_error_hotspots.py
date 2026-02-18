#!/usr/bin/env python3
"""Show selfhost compile error hotspots by generated C++ function."""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path


FUNC_RE = re.compile(
    r"^\s*(?:[A-Za-z_][A-Za-z0-9_:<>*&\s]*\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*\{\s*$"
)
ERR_LINE_RE = re.compile(r"^.*?:(\d+):\d+:\s*error:\s*(.*)$")
CPP_KEYWORDS = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
}


def build_func_ranges(cpp_lines: list[str]) -> list[tuple[int, int, str]]:
    starts: list[tuple[int, str]] = []
    for i, line in enumerate(cpp_lines, start=1):
        m = FUNC_RE.match(line)
        if not m:
            continue
        name = m.group(1)
        if name in CPP_KEYWORDS:
            continue
        starts.append((i, name))

    ranges: list[tuple[int, int, str]] = []
    for idx, (ln, name) in enumerate(starts):
        end = starts[idx + 1][0] - 1 if idx + 1 < len(starts) else len(cpp_lines)
        ranges.append((ln, end, name))
    return ranges


def find_func(line_no: int, ranges: list[tuple[int, int, str]]) -> str:
    for start, end, name in ranges:
        if start <= line_no <= end:
            return name
    return "<global>"


def main() -> int:
    cpp_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("selfhost/py2cpp.cpp")
    log_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("selfhost/py2cpp.compile.log")
    if not cpp_path.exists():
        print(f"missing: {cpp_path}")
        return 1
    if not log_path.exists():
        print(f"missing: {log_path}")
        return 1

    cpp_lines = cpp_path.read_text(encoding="utf-8", errors="replace").splitlines()
    ranges = build_func_ranges(cpp_lines)

    by_func: Counter[str] = Counter()
    by_msg: dict[str, Counter[str]] = {}
    total = 0
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = ERR_LINE_RE.match(line)
        if not m:
            continue
        total += 1
        ln = int(m.group(1))
        msg = m.group(2).strip()
        fn = find_func(ln, ranges)
        by_func[fn] += 1
        if fn not in by_msg:
            by_msg[fn] = Counter()
        by_msg[fn][msg] += 1

    print(f"total_errors={total}")
    for fn, count in by_func.most_common(12):
        print(f"{count:4d}  {fn}")
        for msg, mcount in by_msg[fn].most_common(3):
            print(f"      {mcount:3d}  {msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
