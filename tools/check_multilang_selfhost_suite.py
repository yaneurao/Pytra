#!/usr/bin/env python3
"""Run periodic non-C++ selfhost checks (stage1 + multistage)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from src.toolchain.compiler.backend_registry_diagnostics import classify_parity_note_detail
from tools.selfhost_parity_summary import build_summary_row
from tools.selfhost_parity_summary import print_summary_block


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
    summaries = [summary for row in rows if (summary := _stage1_row_to_summary(row)) is not None]
    print_summary_block("stage1", summaries, skip_pass=True)


def _print_multistage_summary(report: Path) -> None:
    rows = _read_rows(report)
    if len(rows) == 0:
        print(f"[WARN] no multistage rows: {report}")
        return
    summaries = [summary for row in rows if (summary := _multistage_row_to_summary(row)) is not None]
    print_summary_block("multistage", summaries, skip_pass=True)


def _stage1_detail_category(stage1: str, mode: str, stage2: str, note: str) -> str:
    inferred_detail = classify_parity_note_detail(note)
    mode_lc = mode.lower()
    if inferred_detail == "toolchain_missing":
        return "toolchain_missing"
    if inferred_detail in {"preview_only", "not_implemented", "unsupported_by_design", "blocked"}:
        return inferred_detail
    if stage1 == "pass" and stage2 in {"pass", "blocked", "skip"}:
        return "pass"
    if stage1 == "missing_toolchain":
        return "toolchain_missing"
    if mode_lc == "preview":
        return "preview_only"
    if stage2 == "blocked":
        return "blocked"
    return "regression"


def _stage1_row_to_summary(row: list[str]):
    if len(row) < 5:
        return None
    lang = row[0]
    stage1 = row[1]
    mode = row[2]
    stage2 = row[3]
    note = row[4]
    detail = _stage1_detail_category(stage1, mode, stage2, note)
    return build_summary_row("stage1", lang, detail, note)


def _multistage_row_to_summary(row: list[str]):
    if len(row) < 6:
        return None
    lang = row[0]
    detail = row[4]
    note = row[5]
    return build_summary_row("multistage", lang, detail, note)


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
