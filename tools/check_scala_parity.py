#!/usr/bin/env python3
"""Run Scala parity checks for sample and positive fixture cases."""

from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PARITY_CHECK = ROOT / "tools" / "runtime_parity_check.py"
DEFAULT_FIXTURE_MANIFEST = ROOT / "test" / "fixtures" / "scala_positive_manifest.txt"


def _load_fixture_cases(path: Path) -> list[str]:
    out: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line == "" or line.startswith("#"):
            continue
        out.append(line)
    return out


def _run(cmd: list[str]) -> int:
    print("$ " + shlex.join(cmd))
    cp = subprocess.run(cmd, cwd=ROOT, check=False)
    return int(cp.returncode)


def main() -> int:
    ap = argparse.ArgumentParser(description="run Scala parity checks (sample + positive fixtures)")
    ap.add_argument(
        "--east3-opt-level",
        default="1",
        choices=("0", "1", "2"),
        help="EAST3 optimizer level passed to runtime_parity_check.py (default: 1)",
    )
    ap.add_argument(
        "--fixture-manifest",
        default=str(DEFAULT_FIXTURE_MANIFEST),
        help="fixture positive case manifest path (default: test/fixtures/scala_positive_manifest.txt)",
    )
    ap.add_argument(
        "--summary-dir",
        default="out",
        help="directory to write summary json files (default: out)",
    )
    ap.add_argument(
        "--skip-fixture",
        action="store_true",
        help="run only sample parity",
    )
    args = ap.parse_args()

    summary_dir = (ROOT / args.summary_dir).resolve()
    summary_dir.mkdir(parents=True, exist_ok=True)

    sample_summary = summary_dir / "scala_parity_sample_summary.json"
    sample_cmd = [
        "python3",
        str(RUNTIME_PARITY_CHECK),
        "--case-root",
        "sample",
        "--targets",
        "scala",
        "--all-samples",
        "--east3-opt-level",
        args.east3_opt_level,
        "--summary-json",
        str(sample_summary),
    ]
    sample_code = _run(sample_cmd)

    fixture_code = 0
    if not args.skip_fixture:
        manifest_path = Path(args.fixture_manifest)
        if not manifest_path.is_absolute():
            manifest_path = (ROOT / manifest_path).resolve()
        cases = _load_fixture_cases(manifest_path)
        if len(cases) == 0:
            print(f"[ERROR] no fixture cases in manifest: {manifest_path}")
            return 2
        fixture_summary = summary_dir / "scala_parity_fixture_summary.json"
        fixture_cmd = [
            "python3",
            str(RUNTIME_PARITY_CHECK),
            "--case-root",
            "fixture",
            "--targets",
            "scala",
            *cases,
            "--east3-opt-level",
            args.east3_opt_level,
            "--summary-json",
            str(fixture_summary),
        ]
        fixture_code = _run(fixture_cmd)

    if sample_code == 0 and fixture_code == 0:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
