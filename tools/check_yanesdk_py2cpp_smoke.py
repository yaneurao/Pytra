#!/usr/bin/env python3
"""Smoke-check py2cpp on canonical Yanesdk library + game scripts."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY2CPP = ROOT / "src" / "py2cpp.py"


def _run_one(src: Path, out: Path) -> tuple[bool, str]:
    cp = subprocess.run(
        ["python3", str(PY2CPP), str(src), "-o", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if cp.returncode == 0:
        return True, ""
    msg = cp.stderr.strip() or cp.stdout.strip()
    first = msg.splitlines()[0] if msg else "unknown error"
    return False, first


def collect_targets(root: Path) -> list[Path]:
    library = root / "Yanesdk" / "yanesdk" / "yanesdk.py"
    docs_root = root / "Yanesdk" / "docs"
    games: list[Path] = []
    if docs_root.exists():
        for p in sorted(docs_root.rglob("*.py")):
            if p.name == "yanesdk.py":
                continue
            games.append(p)
    out: list[Path] = []
    if library.exists():
        out.append(library)
    out.extend(games)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="check py2cpp smoke on Yanesdk canonical files")
    ap.add_argument("--verbose", action="store_true", help="print passing files")
    args = ap.parse_args()

    targets = collect_targets(ROOT)
    if len(targets) == 0:
        print("skipped: Yanesdk sources not found")
        return 0

    fails: list[tuple[str, str]] = []
    ok = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "out.cpp"
        for src in targets:
            rel = str(src.relative_to(ROOT))
            good, msg = _run_one(src, out)
            if good:
                ok += 1
                if args.verbose:
                    print("OK", rel)
            else:
                fails.append((rel, msg))

    print(f"checked={len(targets)} ok={ok} fail={len(fails)}")
    if fails:
        for rel, msg in fails:
            print(f"FAIL {rel}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
