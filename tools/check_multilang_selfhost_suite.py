#!/usr/bin/env python3
"""Run periodic non-C++ selfhost checks (stage1 + multistage)."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    cp = subprocess.run(cmd, cwd=str(ROOT))
    return int(cp.returncode)


def _read_rows(report: Path) -> list[list[str]]:
    if not report.exists():
        return []
    rows: list[list[str]] = []
    for raw in report.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line.startswith("| "):
            continue
        if line.startswith("|---"):
            continue
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) == 0:
            continue
        if parts[0] == "lang":
            continue
        rows.append(parts)
    return rows


def _print_stage1_summary(report: Path) -> None:
    rows = _read_rows(report)
    if len(rows) == 0:
        print(f"[WARN] no stage1 rows: {report}")
        return
    print("[stage1 summary]")
    for row in rows:
        lang = row[0]
        stage1 = row[1]
        stage2 = row[3]
        note = row[4]
        if stage1 == "pass" and stage2 in {"pass", "blocked", "skip"}:
            continue
        print(f"- {lang}: stage1={stage1} stage2={stage2} note={note}")


def _print_multistage_summary(report: Path) -> None:
    rows = _read_rows(report)
    if len(rows) == 0:
        print(f"[WARN] no multistage rows: {report}")
        return
    print("[multistage summary]")
    for row in rows:
        lang = row[0]
        stage2 = row[2]
        stage3 = row[3]
        category = row[4]
        note = row[5]
        if category in {"pass"}:
            continue
        if stage2 == "pass" and stage3 == "pass":
            continue
        print(f"- {lang}: stage2={stage2} stage3={stage3} category={category} note={note}")


def main() -> int:
    stage1_report = ROOT / "docs" / "ja" / "plans" / "p1-multilang-selfhost-status.md"
    multistage_report = ROOT / "docs" / "ja" / "plans" / "p1-multilang-selfhost-multistage-status.md"

    cmds = [
        ["python3", "tools/check_multilang_selfhost_stage1.py", "--out", str(stage1_report.relative_to(ROOT))],
        ["python3", "tools/check_multilang_selfhost_multistage.py", "--out", str(multistage_report.relative_to(ROOT))],
    ]
    for cmd in cmds:
        rc = _run(cmd)
        if rc != 0:
            print(f"[FAIL] {' '.join(cmd)}")
            return rc

    _print_stage1_summary(stage1_report)
    _print_multistage_summary(multistage_report)
    print("[OK] multilang selfhost suite completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
