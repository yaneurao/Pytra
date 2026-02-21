#!/usr/bin/env python3
"""Summarize recurring selfhost C++ compile error patterns."""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

FUNC_RE = re.compile(
    r"^\s*(?:[A-Za-z_][A-Za-z0-9_:<>*&\s]*\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*\{\s*$"
)
CPP_KEYWORDS = {"if", "for", "while", "switch", "catch"}
ERR_LINE_RE = re.compile(r"^.*?:(\d+):\d+:\s*error:\s*(.*)$")


def normalize_error_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^.*?:\d+:\d+:\s*error:\s*", "", line)
    line = re.sub(r"‘[^’]*’", "<?>", line)
    line = re.sub(r"'[^']*'", "'<?>'", line)
    line = re.sub(r"\b\d+\b", "N", line)
    return line


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
    log_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("selfhost/py2cpp.compile.log")
    cpp_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("selfhost/py2cpp.cpp")
    if not log_path.exists():
        print(f"missing: {log_path}")
        return 1

    counter: Counter[str] = Counter()
    examples: dict[str, str] = {}
    any_hotspots: Counter[str] = Counter()
    any_examples: dict[str, str] = {}
    total = 0

    ranges: list[tuple[int, int, str]] = []
    if cpp_path.exists():
        cpp_lines = cpp_path.read_text(encoding="utf-8", errors="replace").splitlines()
        ranges = build_func_ranges(cpp_lines)

    with log_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if "error:" not in line:
                continue
            total += 1
            key = normalize_error_line(line)
            counter[key] += 1
            if key not in examples:
                examples[key] = line.strip()
            if "std::any" in line:
                m = ERR_LINE_RE.match(line)
                fn = "<global>"
                if m is not None and len(ranges) > 0:
                    fn = find_func(int(m.group(1)), ranges)
                any_hotspots[fn] += 1
                if fn not in any_examples:
                    any_examples[fn] = line.strip()

    print(f"total_errors={total}")
    for msg, count in counter.most_common(20):
        print(f"{count:4d}  {msg}")
        print(f"      ex: {examples.get(msg, '')}")
    if len(any_hotspots) > 0:
        print("std_any_hotspots:")
        for fn, count in any_hotspots.most_common(12):
            print(f"{count:4d}  {fn}")
            print(f"      ex: {any_examples.get(fn, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
