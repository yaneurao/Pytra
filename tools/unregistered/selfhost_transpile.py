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


def build_bridge_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if base_env is None else base_env)
    prev_py_path = env.get("PYTHONPATH", "")
    src_path = str((ROOT / "src").resolve())
    if prev_py_path == "":
        env["PYTHONPATH"] = src_path
    elif src_path not in prev_py_path.split(os.pathsep):
        env["PYTHONPATH"] = src_path + os.pathsep + prev_py_path
    return env


def build_selfhost_cmd_base(selfhost_bin: Path, selfhost_target: str) -> list[str]:
    cmd: list[str] = [str(selfhost_bin)]
    if selfhost_target != "":
        cmd.extend(["--target", selfhost_target])
    return cmd


def build_selfhost_transpile_cmd(
    selfhost_cmd_base: list[str],
    input_path: Path,
    output_path: Path,
) -> list[str]:
    return [*selfhost_cmd_base, str(input_path), "-o", str(output_path)]


def build_python_to_east_json_cmd(input_path: Path, east_json: Path) -> list[str]:
    return [
        sys.executable,
        "-c",
        (
            "import json,sys; "
            "from toolchain.misc.east import convert_path; "
            "from pytra.std.pathlib import Path; "
            "obj=convert_path(Path(sys.argv[1]), parser_backend='self_hosted'); "
            "obj=obj.get('east', obj) if isinstance(obj, dict) else obj; "
            "open(sys.argv[2],'w',encoding='utf-8').write(json.dumps(obj, ensure_ascii=False, indent=2))"
        ),
        str(input_path),
        str(east_json),
    ]


def _resolve_selfhost_target(selfhost_bin: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    cp = subprocess.run([str(selfhost_bin), "--help"], cwd=str(ROOT), capture_output=True, text=True)
    text = (cp.stdout or "") + "\n" + (cp.stderr or "")
    if "--target" in text:
        return "cpp"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="run selfhost transpiler with temporary EAST JSON input")
    ap.add_argument("input", help="Input Python source (.py) or EAST JSON (.json)")
    ap.add_argument("-o", "--output", required=True, help="Output C++ file path")
    ap.add_argument("--selfhost-bin", default="work/selfhost/py2cpp.out", help="Selfhost binary path")
    ap.add_argument("--target", default="auto", help="target passed to selfhost binary (auto|\"\"|cpp)")
    args = ap.parse_args()

    selfhost_bin = ROOT / args.selfhost_bin
    if not selfhost_bin.exists():
        print(f"error: selfhost binary not found: {selfhost_bin}")
        return 1

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    selfhost_target = _resolve_selfhost_target(selfhost_bin, str(args.target))
    selfhost_cmd_base = build_selfhost_cmd_base(selfhost_bin, selfhost_target)

    if input_path.suffix == ".json":
        cp = subprocess.run(
            build_selfhost_transpile_cmd(selfhost_cmd_base, input_path, output_path),
            cwd=str(ROOT),
        )
        return int(cp.returncode)

    if input_path.suffix != ".py":
        print("error: input must be .py or .json")
        return 1

    with tempfile.TemporaryDirectory() as td:
        east_json = Path(td) / (input_path.stem + ".east.json")
        env = build_bridge_env()
        conv = subprocess.run(
            build_python_to_east_json_cmd(input_path, east_json),
            cwd=str(ROOT),
            env=env,
        )
        if conv.returncode != 0:
            return int(conv.returncode)
        cp = subprocess.run(
            build_selfhost_transpile_cmd(selfhost_cmd_base, east_json, output_path),
            cwd=str(ROOT),
        )
        return int(cp.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
