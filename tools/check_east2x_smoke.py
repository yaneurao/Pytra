#!/usr/bin/env python3
"""Smoke check for east2x EAST3(JSON) -> target code path."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = [
    "sample/ir/01_mandelbrot.east3.json",
    "test/ir/core_add.east3.json",
]
EXT_BY_TARGET = {
    "cpp": ".cpp",
    "rs": ".rs",
    "js": ".js",
}


def _parse_csv(raw: str) -> list[str]:
    out: list[str] = []
    for part in raw.split(","):
        item = part.strip()
        if item != "":
            out.append(item)
    return out


def _run(cmd: list[str]) -> tuple[bool, str]:
    cp = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if cp.returncode == 0:
        return True, ""
    msg = cp.stderr.strip() or cp.stdout.strip() or f"exit={cp.returncode}"
    first = msg.splitlines()[0] if msg else "unknown error"
    return False, first


def _normalize_stem(path: Path) -> str:
    name = path.name
    if name.endswith(".east3.json"):
        return name[: -len(".east3.json")]
    if name.endswith(".json"):
        return name[: -len(".json")]
    return path.stem


def main() -> int:
    ap = argparse.ArgumentParser(description="Run east2x smoke checks from fixed EAST3 fixtures")
    ap.add_argument("--targets", default="cpp,rs,js", help="comma separated targets")
    ap.add_argument(
        "--cases",
        default=",".join(DEFAULT_CASES),
        help="comma separated case paths (repository relative)",
    )
    args = ap.parse_args()

    targets = _parse_csv(args.targets)
    if len(targets) == 0:
        print("error: no targets selected", file=sys.stderr)
        return 2
    unsupported = [t for t in targets if t not in EXT_BY_TARGET]
    if len(unsupported) > 0:
        print("error: unsupported target(s): " + ", ".join(sorted(unsupported)), file=sys.stderr)
        return 2

    case_rels = _parse_csv(args.cases)
    if len(case_rels) == 0:
        print("error: no cases selected", file=sys.stderr)
        return 2

    case_paths: list[Path] = []
    for rel in case_rels:
        path = ROOT / rel
        if not path.exists():
            print("error: missing case file: " + rel, file=sys.stderr)
            return 2
        case_paths.append(path)

    out_root = ROOT / "out" / "east2x_smoke"
    out_root.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    total = 0
    for target in targets:
        ext = EXT_BY_TARGET[target]
        for case_path in case_paths:
            total += 1
            stem = _normalize_stem(case_path)
            out_path = out_root / target / f"{stem}{ext}"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            cmd = [
                "python3",
                "src/toolchain/emit/all.py",
                str(case_path),
                "--target",
                target,
                "--no-runtime-hook",
                "-o",
                str(out_path),
            ]
            ok, detail = _run(cmd)
            if not ok:
                failures.append(f"{target}:{case_path.relative_to(ROOT)}: {detail}")
                continue
            if not out_path.exists():
                failures.append(f"{target}:{case_path.relative_to(ROOT)}: output missing")
                continue
            if out_path.read_text(encoding="utf-8").strip() == "":
                failures.append(f"{target}:{case_path.relative_to(ROOT)}: output empty")
                continue
            print(f"[OK] {target} <- {case_path.relative_to(ROOT)}")

    if len(failures) > 0:
        for line in failures:
            print("[FAIL] " + line)
        print(f"[SUMMARY] failed {len(failures)}/{total}")
        return 1

    print(f"[SUMMARY] pass {total}/{total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
