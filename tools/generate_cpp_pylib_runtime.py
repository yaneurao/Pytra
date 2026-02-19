#!/usr/bin/env python3
"""Generate C++ pylib runtime implementation files from src/pylib/tra/*.py."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SPECS = [
    ("src/pylib/tra/png.py", "src/runtime/cpp/pylib/generated/png_impl.cpp"),
    ("src/pylib/tra/gif.py", "src/runtime/cpp/pylib/generated/gif_impl.cpp"),
]


def transpile_to_cpp(source_rel: str) -> str:
    source = ROOT / source_rel
    with tempfile.TemporaryDirectory() as tmp:
        out_cpp = Path(tmp) / "out.cpp"
        cmd = ["python3", "src/py2cpp.py", str(source), "--no-main", "-o", str(out_cpp)]
        p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        if p.returncode != 0:
            raise RuntimeError(f"failed: {' '.join(cmd)}\n{p.stderr}")
        return out_cpp.read_text(encoding="utf-8")


def normalize_generated_text(text: str, source_rel: str) -> str:
    banner = (
        "// AUTO-GENERATED FILE. DO NOT EDIT.\n"
        f"// source: {source_rel}\n"
        "// command: python3 tools/generate_cpp_pylib_runtime.py\n\n"
    )
    return banner + text.rstrip() + "\n"


def write_or_check(target_rel: str, text: str, check: bool) -> bool:
    target = ROOT / target_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    current = target.read_text(encoding="utf-8") if target.exists() else ""
    if current == text:
        return False
    if check:
        print(f"[DIFF] {target_rel}")
        return True
    target.write_text(text, encoding="utf-8")
    print(f"[WRITE] {target_rel}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="only check generated files are up-to-date")
    args = ap.parse_args()

    changed = False
    for source_rel, target_rel in SPECS:
        raw = transpile_to_cpp(source_rel)
        text = normalize_generated_text(raw, source_rel)
        if write_or_check(target_rel, text, args.check):
            changed = True

    if args.check and changed:
        print("[FAIL] generated cpp pylib files are stale")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

