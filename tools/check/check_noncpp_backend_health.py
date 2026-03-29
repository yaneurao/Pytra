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
SMOKE_PYTHONPATH = "src:.:tools/unittest"
FAMILY_ORDER: tuple[str, ...] = ("wave1", "wave2", "wave3")


@dataclass(frozen=True)
class TargetSpec:
    target: str
    family: str
    smoke_rel: str
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
    common_smoke: str
    target_smoke: str
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
    "rs": TargetSpec("rs", "wave1", "tools/unittest/emit/rs/test_py2rs_smoke.py"),
    "cs": TargetSpec("cs", "wave1", "tools/unittest/emit/cs/test_py2cs_smoke.py"),
    "js": TargetSpec(
        "js",
        "wave1",
        "tools/unittest/emit/js/test_py2js_smoke.py",
        ("--skip-east3-contract-tests",),
    ),
    "ts": TargetSpec(
        "ts",
        "wave1",
        "tools/unittest/emit/ts/test_py2ts_smoke.py",
        ("--skip-east3-contract-tests",),
    ),
    "go": TargetSpec("go", "wave2", "tools/unittest/emit/go/test_py2go_smoke.py"),
    "java": TargetSpec("java", "wave2", "tools/unittest/emit/java/test_py2java_smoke.py"),
    "kotlin": TargetSpec("kotlin", "wave2", "tools/unittest/emit/kotlin/test_py2kotlin_smoke.py"),
    "swift": TargetSpec("swift", "wave2", "tools/unittest/emit/swift/test_py2swift_smoke.py"),
    "scala": TargetSpec("scala", "wave2", "tools/unittest/emit/scala/test_py2scala_smoke.py"),
    "ruby": TargetSpec("ruby", "wave3", "tools/unittest/emit/rb/test_py2rb_smoke.py"),
    "lua": TargetSpec("lua", "wave3", "tools/unittest/emit/lua/test_py2lua_smoke.py"),
    "php": TargetSpec("php", "wave3", "tools/unittest/emit/php/test_py2php_smoke.py"),
    "nim": TargetSpec("nim", "wave3", "tools/unittest/emit/nim/test_py2nim_smoke.py"),
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


def _run_common_smoke() -> StepResult:
    return _run_command(
        [
            "python3",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tools/unittest/common",
            "-p",
            "test_py2x_smoke*.py",
        ],
        env={"PYTHONPATH": SMOKE_PYTHONPATH},
    )


def _run_target_smoke(spec: TargetSpec) -> StepResult:
    smoke_path = Path(spec.smoke_rel)
    return _run_command(
        [
            "python3",
            "-m",
            "unittest",
            "discover",
            "-s",
            str(smoke_path.parent),
            "-p",
            smoke_path.name,
        ],
        env={"PYTHONPATH": SMOKE_PYTHONPATH},
    )


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
                "tools/check/runtime_parity_check.py",
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


def _blocked_health(spec: TargetSpec, *, primary_failure: str, detail: str, static_status: str, common_status: str) -> TargetHealth:
    return TargetHealth(
        target=spec.target,
        family=spec.family,
        static_contract=static_status,
        common_smoke=common_status,
        target_smoke="blocked",
        transpile="blocked",
        parity="blocked",
        primary_failure=primary_failure,
        detail=detail,
    )


def collect_target_health(specs: list[TargetSpec], *, skip_parity: bool) -> list[TargetHealth]:
    static_result = _run_static_contract()
    common_result = _run_common_smoke() if static_result.status == "pass" else StepResult("blocked", "")
    health_rows: list[TargetHealth] = []
    for spec in specs:
        if static_result.status != "pass":
            health_rows.append(
                _blocked_health(
                    spec,
                    primary_failure="static_contract_fail",
                    detail=static_result.detail,
                    static_status="fail",
                    common_status="blocked",
                )
            )
            continue
        if common_result.status != "pass":
            health_rows.append(
                _blocked_health(
                    spec,
                    primary_failure="common_smoke_fail",
                    detail=common_result.detail,
                    static_status="pass",
                    common_status="fail",
                )
            )
            continue

        smoke_result = _run_target_smoke(spec)
        if smoke_result.status != "pass":
            health_rows.append(
                TargetHealth(
                    target=spec.target,
                    family=spec.family,
                    static_contract="pass",
                    common_smoke="pass",
                    target_smoke="fail",
                    transpile="blocked",
                    parity="blocked",
                    primary_failure="target_smoke_fail",
                    detail=smoke_result.detail,
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
                    common_smoke="pass",
                    target_smoke="pass",
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
                    common_smoke="pass",
                    target_smoke="pass",
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
                common_smoke="pass",
                target_smoke="pass",
                transpile="pass",
                parity=parity_status,
                primary_failure=primary_failure,
                detail=parity_result.detail,
            )
        )
    return health_rows


def summarize_families(health_rows: list[TargetHealth]) -> list[FamilyHealth]:
    rows_by_family: dict[str, list[TargetHealth]] = {name: [] for name in FAMILY_ORDER}
    for row in health_rows:
        rows_by_family.setdefault(row.family, []).append(row)

    out: list[FamilyHealth] = []
    for family in FAMILY_ORDER:
        rows = rows_by_family.get(family, [])
        if len(rows) == 0:
            continue
        ok_targets = sum(1 for row in rows if row.primary_failure == "ok")
        toolchain_missing_targets = sum(
            1 for row in rows if row.primary_failure == "toolchain_missing"
        )
        broken_rows = [
            row
            for row in rows
            if row.primary_failure not in ("ok", "toolchain_missing")
        ]
        primary_failures = tuple(sorted({row.primary_failure for row in broken_rows}))
        out.append(
            FamilyHealth(
                family=family,
                status="broken" if len(broken_rows) > 0 else "green",
                total_targets=len(rows),
                ok_targets=ok_targets,
                toolchain_missing_targets=toolchain_missing_targets,
                broken_targets=len(broken_rows),
                primary_failures=primary_failures,
            )
        )
    return out


def _resolve_selected_specs(*, family_args: list[str], targets_arg: str) -> list[TargetSpec]:
    if targets_arg.strip() != "":
        names = [item.strip() for item in targets_arg.split(",") if item.strip() != ""]
    else:
        families = family_args if len(family_args) > 0 else ["all"]
        if "all" in families:
            names = [name for family in FAMILY_ORDER for name in FAMILY_TARGETS[family]]
        else:
            seen: set[str] = set()
            names = []
            for family in FAMILY_ORDER:
                if family not in families:
                    continue
                for name in FAMILY_TARGETS[family]:
                    if name in seen:
                        continue
                    seen.add(name)
                    names.append(name)
    unknown = [name for name in names if name not in TARGET_SPECS]
    if len(unknown) > 0:
        raise ValueError("unknown targets: " + ",".join(sorted(unknown)))
    return [TARGET_SPECS[name] for name in names]


def main() -> int:
    ap = argparse.ArgumentParser(description="aggregate non-cpp backend health gates by family")
    ap.add_argument(
        "--family",
        action="append",
        choices=("all",) + FAMILY_ORDER,
        default=[],
        help="family to inspect (default: all)",
    )
    ap.add_argument(
        "--targets",
        default="",
        help="comma separated explicit target ids (overrides --family)",
    )
    ap.add_argument(
        "--skip-parity",
        action="store_true",
        help="stop after transpile gate and skip parity execution",
    )
    ap.add_argument(
        "--summary-json",
        default="",
        help="optional path to write machine-readable health summary",
    )
    args = ap.parse_args()

    try:
        specs = _resolve_selected_specs(family_args=args.family, targets_arg=args.targets)
    except ValueError as exc:
        print("[FAIL]", str(exc))
        return 2

    rows = collect_target_health(specs, skip_parity=args.skip_parity)
    family_rows = summarize_families(rows)

    for row in rows:
        print(
            "TARGET "
            + f"{row.target} family={row.family} "
            + f"static={row.static_contract} common={row.common_smoke} "
            + f"smoke={row.target_smoke} transpile={row.transpile} parity={row.parity} "
            + f"primary={row.primary_failure}"
        )
        if row.detail != "":
            print(f"  detail: {row.detail}")

    for family in family_rows:
        failures = ",".join(family.primary_failures) if len(family.primary_failures) > 0 else "-"
        print(
            "FAMILY "
            + f"{family.family} status={family.status} total={family.total_targets} "
            + f"ok={family.ok_targets} toolchain_missing={family.toolchain_missing_targets} "
            + f"broken={family.broken_targets} primary_failures={failures}"
        )

    broken_targets = sum(
        1 for row in rows if row.primary_failure not in ("ok", "toolchain_missing")
    )
    toolchain_missing_targets = sum(1 for row in rows if row.primary_failure == "toolchain_missing")
    print(
        "SUMMARY "
        + f"targets={len(rows)} broken={broken_targets} "
        + f"toolchain_missing={toolchain_missing_targets} "
        + f"families={len(family_rows)}"
    )

    if args.summary_json != "":
        out_path = Path(args.summary_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(
                {
                    "targets": [asdict(row) for row in rows],
                    "families": [
                        {
                            "family": row.family,
                            "status": row.status,
                            "total_targets": row.total_targets,
                            "ok_targets": row.ok_targets,
                            "toolchain_missing_targets": row.toolchain_missing_targets,
                            "broken_targets": row.broken_targets,
                            "primary_failures": list(row.primary_failures),
                        }
                        for row in family_rows
                    ],
                    "broken_targets": broken_targets,
                    "toolchain_missing_targets": toolchain_missing_targets,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    return 0 if broken_targets == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
