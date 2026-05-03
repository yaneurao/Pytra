#!/usr/bin/env python3
"""Canonical all-target sample parity runner."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PARITY_CHECK = ROOT / "tools" / "check" / "runtime_parity_check.py"

PARITY_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("cpp", ("cpp",)),
    ("js_ts", ("js", "ts")),
    ("compiled", ("rs", "cs", "go", "java", "kotlin", "swift", "scala")),
    ("scripting_mixed", ("ruby", "lua", "php", "nim", "powershell")),
)


def group_names() -> tuple[str, ...]:
    return tuple(name for name, _targets in PARITY_GROUPS)


def parse_groups(raw: str) -> list[str]:
    if raw.strip() == "":
        return list(group_names())
    requested = [part.strip() for part in raw.split(",") if part.strip() != ""]
    unknown = [name for name in requested if name not in group_names()]
    if unknown:
        raise ValueError("unknown group(s): " + ", ".join(unknown))
    return requested


def group_targets(name: str) -> tuple[str, ...]:
    for group_name, targets in PARITY_GROUPS:
        if group_name == name:
            return targets
    raise KeyError(name)


def build_group_command(
    group_name: str,
    *,
    opt_level: str,
    cpp_codegen_opt: str,
    summary_json: Path | None,
) -> list[str]:
    cmd = [
        sys.executable,
        str(RUNTIME_PARITY_CHECK),
        "--targets",
        ",".join(group_targets(group_name)),
        "--case-root",
        "sample",
        "--opt-level",
        opt_level,
    ]
    if summary_json is not None:
        cmd.extend(["--summary-json", str(summary_json)])
    return cmd


def merge_summary_json(summary_dir: Path, selected_groups: list[str], opt_level: str, cpp_codegen_opt: str) -> dict[str, object]:
    group_summaries: dict[str, object] = {}
    all_targets: list[str] = []
    all_cases: list[str] = []
    category_counts: dict[str, int] = {}
    records: list[dict[str, object]] = []
    case_total = 0
    case_pass = 0
    case_fail = 0
    for group_name in selected_groups:
        summary_path = summary_dir / f"{group_name}.json"
        summary_obj = json.loads(summary_path.read_text(encoding="utf-8"))
        group_summaries[group_name] = summary_obj
        case_total += int(summary_obj.get("case_total", 0))
        case_pass += int(summary_obj.get("case_pass", 0))
        case_fail += int(summary_obj.get("case_fail", 0))
        for target in summary_obj.get("targets", []):
            if isinstance(target, str) and target not in all_targets:
                all_targets.append(target)
        for case in summary_obj.get("cases", []):
            if isinstance(case, str) and case not in all_cases:
                all_cases.append(case)
        for category, count in dict(summary_obj.get("category_counts", {})).items():
            if isinstance(category, str):
                category_counts[category] = category_counts.get(category, 0) + int(count)
        for rec in summary_obj.get("records", []):
            if isinstance(rec, dict):
                records.append(rec)
    return {
        "case_root": "sample",
        "groups": selected_groups,
        "targets": all_targets,
        "cases": all_cases,
        "case_total": case_total,
        "case_pass": case_pass,
        "case_fail": case_fail,
        "category_counts": category_counts,
        "records": records,
        "opt_level": opt_level,
        "cpp_codegen_opt": cpp_codegen_opt,
        "group_summaries": group_summaries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run canonical all-target sample parity groups.")
    parser.add_argument(
        "--groups",
        default=",".join(group_names()),
        help="comma-separated subset of groups: " + ",".join(group_names()),
    )
    parser.add_argument("--opt-level", default="2")
    parser.add_argument("--cpp-codegen-opt", default="3")
    parser.add_argument(
        "--summary-dir",
        default="",
        help="optional directory to store per-group JSON and merged summary",
    )
    args = parser.parse_args()

    try:
        selected_groups = parse_groups(args.groups)
    except ValueError as exc:
        print(f"[FAIL] {exc}")
        return 2

    summary_dir = Path(args.summary_dir) if args.summary_dir != "" else None
    if summary_dir is not None:
        summary_dir.mkdir(parents=True, exist_ok=True)

    failed_groups: list[str] = []
    for group_name in selected_groups:
        print(f"== GROUP {group_name} ==")
        group_summary = None if summary_dir is None else summary_dir / f"{group_name}.json"
        cmd = build_group_command(
            group_name,
            opt_level=str(args.opt_level),
            cpp_codegen_opt=str(args.cpp_codegen_opt),
            summary_json=group_summary,
        )
        completed = subprocess.run(cmd, cwd=ROOT, check=False)
        if completed.returncode != 0:
            failed_groups.append(group_name)

    if summary_dir is not None:
        merged = merge_summary_json(summary_dir, selected_groups, str(args.opt_level), str(args.cpp_codegen_opt))
        merged_path = summary_dir / "all-target-summary.json"
        merged_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if failed_groups:
        print("[FAIL] groups=" + ",".join(failed_groups))
        return 1
    print("[OK] all target sample parity groups passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
