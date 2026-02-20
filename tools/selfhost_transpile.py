#!/usr/bin/env python3
"""Transpile via selfhost binary with a temporary EAST JSON bridge.

This is a transitional tool while selfhost `.py` parsing is not enabled yet.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description="run selfhost transpiler with temporary EAST JSON input")
    ap.add_argument("input", help="Input Python source (.py) or EAST JSON (.json)")
    ap.add_argument("-o", "--output", required=True, help="Output C++ file path")
    ap.add_argument("--selfhost-bin", default="selfhost/py2cpp.out", help="Selfhost binary path")
    args = ap.parse_args()

    selfhost_bin = ROOT / args.selfhost_bin
    if not selfhost_bin.exists():
        print(f"error: selfhost binary not found: {selfhost_bin}")
        return 1

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    if input_path.suffix == ".json":
        cp = subprocess.run([str(selfhost_bin), str(input_path), "-o", str(output_path)], cwd=str(ROOT))
        return int(cp.returncode)

    if input_path.suffix != ".py":
        print("error: input must be .py or .json")
        return 1

    with tempfile.TemporaryDirectory() as td:
        east_json = Path(td) / (input_path.stem + ".east.json")
        env = dict(os.environ)
        prev_py_path = env.get("PYTHONPATH", "")
        src_path = str((ROOT / "src").resolve())
        if prev_py_path == "":
            env["PYTHONPATH"] = src_path
        else:
            env["PYTHONPATH"] = src_path + os.pathsep + prev_py_path
        conv = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import json,sys; "
                    "from pytra.compiler.east import convert_path; "
                    "from pytra.std.pathlib import Path; "
                    "obj=convert_path(Path(sys.argv[1]), parser_backend='self_hosted'); "
                    "obj=obj.get('east', obj) if isinstance(obj, dict) else obj; "
                    "open(sys.argv[2],'w',encoding='utf-8').write(json.dumps(obj, ensure_ascii=False, indent=2))"
                ),
                str(input_path),
                str(east_json),
            ],
            cwd=str(ROOT),
            env=env,
        )
        if conv.returncode != 0:
            return int(conv.returncode)
        cp = subprocess.run([str(selfhost_bin), str(east_json), "-o", str(output_path)], cwd=str(ROOT))
        return int(cp.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
