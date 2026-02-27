#!/usr/bin/env python3
"""Extract C++/Rust runtime gap rankings from README performance table."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class GapRow:
    no: str
    workload: str
    cpp: float
    rust: float

    @property
    def rs_over_cpp(self) -> float:
        if self.cpp == 0.0:
            return 0.0
        return self.rust / self.cpp

    @property
    def cpp_over_rs(self) -> float:
        if self.rust == 0.0:
            return 0.0
        return self.cpp / self.rust

    @property
    def diff(self) -> float:
        return self.rust - self.cpp


ROW_RE = re.compile(
    r"^\|\s*(\d{2})\s*\|([^|]+)\|([0-9]+(?:\.[0-9]+)?)\|([0-9]+(?:\.[0-9]+)?)\|([0-9]+(?:\.[0-9]+)?)\|"
)


def _parse_rows(readme_path: Path) -> list[GapRow]:
    rows: list[GapRow] = []
    text = readme_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        m = ROW_RE.match(line)
        if m is None:
            continue
        no, workload, _py, cpp, rust = m.groups()
        rows.append(GapRow(no=no, workload=workload.strip(), cpp=float(cpp), rust=float(rust)))
    return rows


def _render_table(rows: list[GapRow], slower: bool, top_n: int) -> str:
    title = "Rust slower than C++ (rs/cpp desc)" if slower else "Rust faster than C++ (cpp/rs desc)"
    out: list[str] = []
    out.append("### " + title)
    out.append("| No | Workload | C++ (s) | Rust (s) | Ratio | Diff (rs-cpp) |")
    out.append("|---|---|---:|---:|---:|---:|")
    if slower:
        ordered = sorted(rows, key=lambda r: r.rs_over_cpp, reverse=True)
        for r in ordered[:top_n]:
            out.append(
                f"| {r.no} | {r.workload} | {r.cpp:.3f} | {r.rust:.3f} | {r.rs_over_cpp:.2f}x | {r.diff:+.3f} |"
            )
    else:
        ordered = sorted(rows, key=lambda r: r.cpp_over_rs, reverse=True)
        for r in ordered[:top_n]:
            out.append(
                f"| {r.no} | {r.workload} | {r.cpp:.3f} | {r.rust:.3f} | {r.cpp_over_rs:.2f}x | {r.diff:+.3f} |"
            )
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract C++/Rust runtime gap ranking from README table")
    parser.add_argument("--readme", default="README.md", help="README path relative to repo root")
    parser.add_argument("--top", type=int, default=8, help="rows per ranking table")
    parser.add_argument("--emit-json", default="", help="optional output JSON path")
    args = parser.parse_args()

    readme_path = ROOT / args.readme
    if not readme_path.is_file():
        raise RuntimeError("readme not found: " + str(readme_path))

    rows = _parse_rows(readme_path)
    if len(rows) == 0:
        raise RuntimeError("no runtime table rows found in: " + str(readme_path))

    print("# C++ vs Rust gap report")
    print("")
    print("source: " + str(readme_path.relative_to(ROOT)))
    print("rows:", len(rows))
    print("")
    print(_render_table(rows, slower=True, top_n=args.top))
    print("")
    print(_render_table(rows, slower=False, top_n=args.top))

    if args.emit_json != "":
        out_path = ROOT / args.emit_json
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "source": str(readme_path.relative_to(ROOT)),
            "rows": [asdict(r) for r in rows],
            "rust_slower_rank": [
                {
                    "no": r.no,
                    "workload": r.workload,
                    "cpp": r.cpp,
                    "rust": r.rust,
                    "ratio": r.rs_over_cpp,
                    "diff": r.diff,
                }
                for r in sorted(rows, key=lambda x: x.rs_over_cpp, reverse=True)
            ],
            "rust_faster_rank": [
                {
                    "no": r.no,
                    "workload": r.workload,
                    "cpp": r.cpp,
                    "rust": r.rust,
                    "ratio": r.cpp_over_rs,
                    "diff": r.diff,
                }
                for r in sorted(rows, key=lambda x: x.cpp_over_rs, reverse=True)
            ],
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("")
        print("json:", str(out_path.relative_to(ROOT)))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
