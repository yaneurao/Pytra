#!/usr/bin/env python3
"""Aggregate non-C++ backend health gates into one family-oriented checker."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FAMILY_ORDER: tuple[str, ...] = ("wave1", "wave2", "wave3")


@dataclass(frozen=True)
class TargetSpec:
    target: str
    family: str
    transpile_extra_flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class StepResult:
    status: str
    detail: str = ""


@dataclass(frozen=True)
class TargetHealth:
    target: str
    family: str
    static_contract: str
    transpile: str
    parity: str
    primary_failure: str
    detail: str


@dataclass(frozen=True)
class FamilyHealth:
    family: str
    status: str
    total_targets: int
    ok_targets: int
    toolchain_missing_targets: int
    broken_targets: int
    primary_failures: tuple[str, ...]


TARGET_SPECS: dict[str, TargetSpec] = {
    "rs": TargetSpec("rs", "wave1"),
    "cs": TargetSpec("cs", "wave1"),
    "js": TargetSpec("js", "wave1", ("--skip-east3-contract-tests",)),
    "ts": TargetSpec("ts", "wave1", ("--skip-east3-contract-tests",)),
    "go": TargetSpec("go", "wave2"),
    "java": TargetSpec("java", "wave2"),
    "kotlin": TargetSpec("kotlin", "wave2"),
    "swift": TargetSpec("swift", "wave2"),
    "scala": TargetSpec("scala", "wave2"),
    "ruby": TargetSpec("ruby", "wave3"),
    "lua": TargetSpec("lua", "wave3"),
    "php": TargetSpec("php", "wave3"),
    "nim": TargetSpec("nim", "wave3"),
}

FAMILY_TARGETS: dict[str, tuple[str, ...]] = {
    "wave1": ("rs", "cs", "js", "ts"),
    "wave2": ("go", "java", "kotlin", "swift", "scala"),
    "wave3": ("ruby", "lua", "php", "nim"),
}


def _first_line(*texts: str) -> str:
    for text in texts:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped != "":
                return stripped
    return "unknown error"


def _run_command(cmd: list[str], *, env: dict[str, str] | None = None) -> StepResult:
    proc_env = os.environ.copy()
    if env is not None:
        proc_env.update(env)
    cp = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=proc_env,
    )
    if cp.returncode == 0:
        return StepResult("pass", "")
    return StepResult("fail", _first_line(cp.stderr, cp.stdout))


def _run_static_contract() -> StepResult:
    return _run_command(["python3", "tools/check/check_noncpp_east3_contract.py", "--skip-transpile"])


def _run_target_transpile(spec: TargetSpec) -> StepResult:
    return _run_command(
        [
            "python3",
            "tools/check/check_py2x_transpile.py",
            "--target",
            spec.target,
            *spec.transpile_extra_flags,
        ]
    )


def _classify_parity_summary(summary: dict[str, object], target: str) -> StepResult:
    records_any = summary.get("records")
    records = records_any if isinstance(records_any, list) else []
    target_records = [
        rec
        for rec in records
        if isinstance(rec, dict) and str(rec.get("target", "")).strip() == target
    ]
    categories = {
        str(rec.get("category", "")).strip()
        for rec in target_records
        if str(rec.get("category", "")).strip() != ""
    }
    if categories == {"toolchain_missing"}:
        return StepResult("toolchain_missing", f"toolchain missing in {len(target_records)} cases")

    case_fail = int(summary.get("case_fail", 0) or 0)
    if case_fail == 0 and (categories == set() or categories <= {"ok"}):
        case_total = int(summary.get("case_total", 0) or 0)
        case_pass = int(summary.get("case_pass", case_total) or 0)
        return StepResult("ok", f"cases={case_pass}/{case_total}")

    for rec in target_records:
        if not isinstance(rec, dict):
            continue
        category = str(rec.get("category", "")).strip()
        if category in ("", "ok", "toolchain_missing"):
            continue
        case_name = str(rec.get("case", "")).strip()
        detail = str(rec.get("detail", "")).strip()
        prefix = case_name + ": " if case_name != "" else ""
        if detail != "":
            return StepResult("fail", prefix + detail)
        return StepResult("fail", prefix + category)

    if case_fail != 0:
        return StepResult("fail", f"parity failed: case_fail={case_fail}")
    return StepResult("fail", "unexpected parity summary")


def _run_target_parity(spec: TargetSpec) -> StepResult:
    with tempfile.TemporaryDirectory() as td:
        summary_path = Path(td) / "summary.json"
        cp = subprocess.run(
            [
                "python3",
                "tools/check/runtime_parity_check_fast.py",
                "--targets",
                spec.target,
                "--case-root",
                "sample",
                "--ignore-unstable-stdout",
                "--summary-json",
                str(summary_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if not summary_path.exists():
            return StepResult("fail", _first_line(cp.stderr, cp.stdout))
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        result = _classify_parity_summary(summary, spec.target)
        if result.status == "fail" and result.detail == "":
            return StepResult("fail", _first_line(cp.stderr, cp.stdout))
        return result


def _blocked_health(spec: TargetSpec, *, primary_failure: str, detail: str, static_status: str) -> TargetHealth:
    return TargetHealth(
        target=spec.target,
        family=spec.family,
        static_contract=static_status,
        transpile="blocked",
        parity="blocked",
        primary_failure=primary_failure,
        detail=detail,
    )


def collect_target_health(specs: list[TargetSpec], *, skip_parity: bool) -> list[TargetHealth]:
    static_result = _run_static_contract()
    health_rows: list[TargetHealth] = []
    for spec in specs:
        if static_result.status != "pass":
            health_rows.append(
                _blocked_health(
                    spec,
                    primary_failure="static_contract_fail",
                    detail=static_result.detail,
                    static_status="fail",
                )
            )
            continue

        transpile_result = _run_target_transpile(spec)
        if transpile_result.status != "pass":
            health_rows.append(
                TargetHealth(
                    target=spec.target,
                    family=spec.family,
                    static_contract="pass",
                    transpile="fail",
                    parity="blocked",
                    primary_failure="transpile_fail",
                    detail=transpile_result.detail,
                )
            )
            continue

        if skip_parity:
            health_rows.append(
                TargetHealth(
                    target=spec.target,
                    family=spec.family,
                    static_contract="pass",
                    transpile="pass",
                    parity="skipped",
                    primary_failure="ok",
                    detail="parity skipped",
                )
            )
            continue

        parity_result = _run_target_parity(spec)
        parity_status = parity_result.status
        primary_failure = "ok"
        if parity_status == "toolchain_missing":
            primary_failure = "toolchain_missing"
        elif parity_status != "ok":
            primary_failure = "parity_fail"
        health_rows.append(
            TargetHealth(
                target=spec.target,
                family=spec.family,
                static_contract="pass",
                transpile="pass",
                parity=parity_status,
                primary_failure=primary_failure,
                detail=parity_result.detail,
            )
        )
    return health_rows


def summarize_families(health_rows: list[TargetHealth]) -> list[FamilyHealth]:
    by_family: dict[str, list[TargetHealth]] = {}
    for row in health_rows:
        by_family.setdefault(row.family, []).append(row)
    summaries: list[FamilyHealth] = []
    for family in FAMILY_ORDER:
        rows = by_family.get(family, [])
        total = len(rows)
        ok = sum(1 for r in rows if r.primary_failure == "ok")
        tm = sum(1 for r in rows if r.primary_failure == "toolchain_missing")
        broken = total - ok - tm
        fails = tuple(r.primary_failure for r in rows if r.primary_failure not in ("ok", "toolchain_missing"))
        status = "ok" if broken == 0 else "fail"
        summaries.append(FamilyHealth(family, status, total, ok, tm, broken, fails))
    return summaries


def main() -> int:
    parser = argparse.ArgumentParser(description="Non-C++ backend health checker")
    parser.add_argument("--target", action="append", help="Limit to specific target(s)")
    parser.add_argument("--family", action="append", help="Limit to specific family(ies)")
    parser.add_argument("--skip-parity", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--help-targets", action="store_true")
    args = parser.parse_args()

    if args.help_targets:
        for name, spec in TARGET_SPECS.items():
            print(f"{name:10s} {spec.family}")
        return 0

    specs: list[TargetSpec] = []
    if args.target:
        for t in args.target:
            if t in TARGET_SPECS:
                specs.append(TARGET_SPECS[t])
    elif args.family:
        for fam in args.family:
            for t in FAMILY_TARGETS.get(fam, ()):
                specs.append(TARGET_SPECS[t])
    else:
        for fam in FAMILY_ORDER:
            for t in FAMILY_TARGETS[fam]:
                specs.append(TARGET_SPECS[t])

    health_rows = collect_target_health(specs, skip_parity=args.skip_parity)
    families = summarize_families(health_rows)

    if args.json:
        out = {
            "targets": [asdict(h) for h in health_rows],
            "families": [asdict(f) for f in families],
        }
        print(json.dumps(out, indent=2))
    else:
        for row in health_rows:
            icon = "OK" if row.primary_failure == "ok" else ("SKIP" if row.primary_failure == "toolchain_missing" else "FAIL")
            print(f"  [{icon}] {row.target:10s} static={row.static_contract} transpile={row.transpile} parity={row.parity}")
            if row.primary_failure not in ("ok", "toolchain_missing"):
                print(f"           {row.detail}")
        print()
        for fam in families:
            icon = "OK" if fam.status == "ok" else "FAIL"
            print(f"[{icon}] {fam.family}: {fam.ok_targets}/{fam.total_targets} ok, {fam.toolchain_missing_targets} toolchain_missing, {fam.broken_targets} broken")

    any_fail = any(f.status != "ok" for f in families)
    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
