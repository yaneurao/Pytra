#!/usr/bin/env python3
"""Project CLI entrypoint for Pytra tools."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


# /src/pytra/cli.py -> project root is parents[2]
ROOT = Path(__file__).resolve().parents[2]
PY2CPP = ROOT / "src" / "py2cpp.py"
GEN_MAKEFILE = ROOT / "tools" / "gen_makefile_from_manifest.py"
PYTHON = sys.executable or "python3"

DEFAULT_OUTPUT_DIR = "out"
DEFAULT_EXE = "app.out"
DEFAULT_STD = "c++20"
DEFAULT_COMPILER = "g++"
DEFAULT_OPT = "-O2"

_OPT_SHORT_RE = re.compile(r"^-O[0-3]$")


def _normalize_args(argv: list[str]) -> list[str]:
    """Normalize CLI flags that argparse otherwise treats as missing-values errors."""
    normalized: list[str] = []
    idx = 0
    while idx < len(argv):
        token = argv[idx]
        if token == "--opt":
            if idx + 1 < len(argv) and _OPT_SHORT_RE.match(argv[idx + 1]):
                normalized.append(f"--opt={argv[idx + 1]}")
                idx += 2
                continue
        if _OPT_SHORT_RE.match(token):
            normalized.append(f"--opt={token}")
            idx += 1
            continue
        normalized.append(token)
        idx += 1
    return normalized


def _run(cmd: list[str], cwd: Path | None = None, timeout: float | None = None) -> int:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.returncode != 0:
        if proc.stderr:
            print(proc.stderr, end="")
        return proc.returncode
    if proc.stderr:
        # Keep warnings for compatibility.
        print(proc.stderr, end="")
    return 0


def _require_make_available() -> str:
    make_path = shutil.which("make")
    if make_path is None:
        raise RuntimeError("make not found in PATH")
    return make_path


def _manifest_path(output_dir: Path, args: argparse.Namespace) -> Path:
    if args.output != "":
        # py2cpp treats explicit output as single-file; for build path we keep
        # output_dir semantics only.
        return output_dir / "manifest.json"
    return output_dir / "manifest.json"


def _run_py2cpp(input_path: Path, output_dir: Path, argv: list[str]) -> int:
    cmd = [PYTHON, str(PY2CPP), str(input_path), "--multi-file", "--output-dir", str(output_dir)]
    cmd.extend(argv)
    return _run(cmd, cwd=ROOT)


def _run_makefile_generator(manifest_path: Path, makefile_path: Path, args: argparse.Namespace) -> int:
    cmd = [
        PYTHON,
        str(GEN_MAKEFILE),
        str(manifest_path),
        "-o",
        str(makefile_path),
        "--exe",
        args.exe,
        "--compiler",
        args.compiler,
        "--std",
        args.std,
        f"--opt={args.opt}",
    ]
    return _run(cmd, cwd=ROOT)


def _run_make(makefile_path: Path, target: str | None = None, timeout: float | None = None) -> int:
    _require_make_available()
    cmd = ["make", "-f", str(makefile_path)]
    if target:
        cmd.append(target)
    return _run(cmd, cwd=makefile_path.parent, timeout=timeout)


def _build_cpp(input_path: Path, args: argparse.Namespace, passthrough: list[str]) -> int:
    output_dir = (Path(args.output_dir) if args.output_dir else Path(DEFAULT_OUTPUT_DIR))
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.compiler == "":
        raise ValueError("invalid --compiler")
    if args.std == "":
        raise ValueError("invalid --std")
    if args.opt == "":
        raise ValueError("invalid --opt")
    if args.exe == "":
        raise ValueError("invalid --exe")

    rc = _run_py2cpp(input_path, output_dir, passthrough)
    if rc != 0:
        return rc

    manifest_path = _manifest_path(output_dir, args)
    if not manifest_path.exists():
        print(f"error: manifest not found after transpile: {manifest_path}", file=sys.stderr)
        return 1

    makefile_path = output_dir / "Makefile"
    rc = _run_makefile_generator(manifest_path, makefile_path, args)
    if rc != 0:
        return rc

    rc = _run_make(makefile_path, timeout=None)
    if rc != 0:
        return rc

    if args.run:
        return _run_make(makefile_path, target="run")
    return 0


def _transpile_cpp(input_path: Path, args: argparse.Namespace, passthrough: list[str]) -> int:
    cmd = [PYTHON, str(PY2CPP), str(input_path)]
    if args.output != "":
        cmd.extend(["--output", args.output])
    if args.output_dir != DEFAULT_OUTPUT_DIR:
        cmd.extend(["--output-dir", args.output_dir])
    cmd.extend(passthrough)
    return _run(cmd, cwd=ROOT)


def _parse(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    argv = _normalize_args(argv)
    ap = argparse.ArgumentParser(description="pytra unified CLI (v1)")
    ap.add_argument("input", help="Input Python source path")
    ap.add_argument("--target", default="cpp", choices=["cpp"], help="target language")
    ap.add_argument("--build", action="store_true", help="transpile then build in one step")
    ap.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="output dir for multi-file")
    ap.add_argument("--output", default="", help="output file for non-build single-file mode")
    ap.add_argument("--compiler", default=DEFAULT_COMPILER, help="C++ compiler for make-based build")
    ap.add_argument("--std", default=DEFAULT_STD, help="C++ standard")
    ap.add_argument("--opt", default=DEFAULT_OPT, help="C++ optimize flag")
    ap.add_argument("--exe", default=DEFAULT_EXE, help="output executable name for generated Makefile")
    ap.add_argument("--run", action="store_true", help="run after build")
    ap.add_argument("--codegen-opt", type=int, choices=[0, 1, 2, 3], help="py2cpp optimization level")
    return ap.parse_known_args(argv)


def main(argv: list[str]) -> int:
    try:
        args, passthrough = _parse(argv)
    except SystemExit as exc:
        code = exc.code
        if isinstance(code, int):
            return code
        return 1

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"error: input not found: {input_path}", file=sys.stderr)
        return 1

    passthrough_args: list[str] = []
    codegen_opt = args.codegen_opt
    if codegen_opt is not None:
        passthrough_args.extend([f"-O{codegen_opt}"])
    if args.target != "cpp":
        print(f"error: unsupported target: {args.target}", file=sys.stderr)
        return 1

    if args.build:
        if args.output != "":
            print("error: --output is not supported with --build. Use --exe", file=sys.stderr)
            return 1
        if not args.output_dir:
            print("error: --output-dir is required for --build", file=sys.stderr)
            return 1
        if args.compiler == "" or args.std == "" or args.opt == "":
            # Keep consistent with earlier strict CLI behavior and fail early for
            # obviously broken values.
            print("error: invalid build options", file=sys.stderr)
            return 1
        if args.run and args.build:
            # keep supported, no-op precheck here for readability
            pass
        passthrough_args.extend(passthrough)
        return _build_cpp(input_path, args, passthrough_args)

    passthrough_args.extend(passthrough)
    return _transpile_cpp(input_path, args, passthrough_args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
