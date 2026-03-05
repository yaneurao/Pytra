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


# /src/pytra_cli.py -> project root is parents[1]
ROOT = Path(__file__).resolve().parents[1]
PY2X = ROOT / "src" / "py2x.py"
GEN_MAKEFILE = ROOT / "tools" / "gen_makefile_from_manifest.py"
PYTHON = sys.executable or "python3"

DEFAULT_OUTPUT_DIR = "out"
DEFAULT_EXE = "app.out"
DEFAULT_STD = "c++20"
DEFAULT_COMPILER = "g++"
DEFAULT_OPT = "-O2"
SUPPORTED_TARGETS = [
    "cpp",
    "rs",
    "cs",
    "js",
    "ts",
    "go",
    "java",
    "swift",
    "kotlin",
    "scala",
    "lua",
    "ruby",
    "php",
    "nim",
]
TARGET_EXT: dict[str, str] = {
    "cpp": ".cpp",
    "rs": ".rs",
    "cs": ".cs",
    "js": ".js",
    "ts": ".ts",
    "go": ".go",
    "java": ".java",
    "swift": ".swift",
    "kotlin": ".kt",
    "scala": ".scala",
    "lua": ".lua",
    "ruby": ".rb",
    "php": ".php",
    "nim": ".nim",
}

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


def _run(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: float | None = None,
    *,
    stdout_to_stderr: bool = False,
) -> int:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.stdout:
        if stdout_to_stderr:
            print(proc.stdout, end="", file=sys.stderr)
        else:
            print(proc.stdout, end="")
    if proc.returncode != 0:
        if proc.stderr:
            print(proc.stderr, end="", file=sys.stderr)
        return proc.returncode
    if proc.stderr:
        # Keep warnings for compatibility.
        print(proc.stderr, end="", file=sys.stderr)
    return 0


def _require_make_available() -> str:
    make_path = shutil.which("make")
    if make_path is None:
        raise RuntimeError("make not found in PATH")
    return make_path


def _resolve_output_path(input_path: Path, target: str, args: argparse.Namespace) -> Path:
    if args.output != "":
        return Path(args.output)
    out_dir = Path(args.output_dir) if args.output_dir else Path(DEFAULT_OUTPUT_DIR)
    stem = input_path.stem if input_path.stem != "" else "output"
    if target == "java":
        return out_dir / "Main.java"
    ext = TARGET_EXT.get(target, "")
    if ext == "":
        return out_dir / stem
    return out_dir / f"{stem}{ext}"


def _run_py2x_target(
    input_path: Path,
    target: str,
    output_path: Path,
    argv: list[str],
    *,
    stdout_to_stderr: bool = False,
) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        PYTHON,
        str(PY2X),
        str(input_path),
        "--target",
        target,
        "--output",
        str(output_path),
    ]
    cmd.extend(argv)
    return _run(cmd, cwd=Path.cwd(), stdout_to_stderr=stdout_to_stderr)


def _run_interpreter_build(output_path: Path, target: str, run_after_build: bool) -> int:
    if not run_after_build:
        return 0
    if target == "js":
        return _run(["node", str(output_path)], cwd=Path.cwd())
    if target == "ts":
        return _run(["npx", "-y", "tsx", str(output_path)], cwd=Path.cwd())
    if target == "ruby":
        return _run(["ruby", str(output_path)], cwd=Path.cwd())
    if target == "lua":
        return _run(["lua", str(output_path)], cwd=Path.cwd())
    if target == "php":
        return _run(["php", str(output_path)], cwd=Path.cwd())
    return 0


def _build_noncpp(input_path: Path, target: str, args: argparse.Namespace, passthrough: list[str]) -> int:
    output_path = _resolve_output_path(input_path, target, args)
    if output_path.exists() and output_path.is_dir():
        print(f"error: output path is a directory: {output_path}", file=sys.stderr)
        return 1

    rc = _run_py2x_target(input_path, target, output_path, passthrough, stdout_to_stderr=True)
    if rc != 0:
        return rc

    if target in {"js", "ts", "ruby", "lua", "php"}:
        return _run_interpreter_build(output_path, target, args.run)

    out_dir = output_path.parent
    stem = input_path.stem if input_path.stem != "" else "output"

    if target == "rs":
        exe_path = out_dir / f"{stem}_rs.out"
        rc = _run(
            ["rustc", "-O", str(output_path), "-o", str(exe_path)],
            cwd=Path.cwd(),
            stdout_to_stderr=True,
        )
        if rc != 0 or not args.run:
            return rc
        return _run([str(exe_path)], cwd=Path.cwd())

    if target == "cs":
        exe_path = out_dir / f"{stem}_cs.exe"
        rc = _run(
            [
                "mcs",
                "-warn:0",
                f"-out:{exe_path}",
                str(output_path),
                str(ROOT / "src/runtime/cs/pytra-core/built_in/py_runtime.cs"),
                str(ROOT / "src/runtime/cs/pytra-core/built_in/time.cs"),
                str(ROOT / "src/runtime/cs/pytra-core/built_in/math.cs"),
                str(ROOT / "src/runtime/cs/pytra-gen/utils/png.cs"),
                str(ROOT / "src/runtime/cs/pytra-gen/utils/gif.cs"),
                str(ROOT / "src/runtime/cs/pytra-core/std/pathlib.cs"),
                str(ROOT / "src/runtime/cs/pytra-core/std/json.cs"),
            ],
            cwd=Path.cwd(),
            stdout_to_stderr=True,
        )
        if rc != 0 or not args.run:
            return rc
        return _run(["mono", str(exe_path)], cwd=Path.cwd())

    if target == "go":
        exe_path = out_dir / f"{stem}_go.out"
        rc = _run(
            [
                "go",
                "build",
                "-o",
                str(exe_path),
                str(output_path),
                str(out_dir / "py_runtime.go"),
                str(out_dir / "png.go"),
                str(out_dir / "gif.go"),
            ],
            cwd=Path.cwd(),
            stdout_to_stderr=True,
        )
        if rc != 0 or not args.run:
            return rc
        return _run([str(exe_path)], cwd=Path.cwd())

    if target == "java":
        rc = _run(
            [
                "javac",
                "-sourcepath",
                str(out_dir),
                str(out_dir / "Main.java"),
                str(out_dir / "PyRuntime.java"),
                str(out_dir / "png.java"),
                str(out_dir / "gif.java"),
            ],
            cwd=Path.cwd(),
            stdout_to_stderr=True,
        )
        if rc != 0 or not args.run:
            return rc
        return _run(["java", "-cp", str(out_dir), "Main"], cwd=Path.cwd())

    if target == "swift":
        exe_path = out_dir / f"{stem}_swift.out"
        rc = _run(
            [
                "swiftc",
                "-O",
                str(output_path),
                str(out_dir / "py_runtime.swift"),
                str(out_dir / "image_runtime.swift"),
                "-o",
                str(exe_path),
            ],
            cwd=Path.cwd(),
            stdout_to_stderr=True,
        )
        if rc != 0 or not args.run:
            return rc
        return _run([str(exe_path)], cwd=Path.cwd())

    if target == "kotlin":
        jar_path = out_dir / f"{stem}_kotlin.jar"
        rc = _run(
            [
                "kotlinc",
                str(output_path),
                str(out_dir / "py_runtime.kt"),
                str(out_dir / "image_runtime.kt"),
                "-include-runtime",
                "-d",
                str(jar_path),
            ],
            cwd=Path.cwd(),
            stdout_to_stderr=True,
        )
        if rc != 0 or not args.run:
            return rc
        return _run(["java", "-jar", str(jar_path)], cwd=Path.cwd())

    if target == "scala":
        if not args.run:
            return 0
        return _run(
            [
                "scala",
                "run",
                str(out_dir / "py_runtime.scala"),
                str(out_dir / "image_runtime.scala"),
                str(output_path),
            ],
            cwd=Path.cwd(),
            stdout_to_stderr=True,
        )

    if target == "nim":
        exe_path = out_dir / f"{stem}_nim.out"
        nimcache_path = out_dir / f"nimcache_{stem}"
        cmd = [
            "nim",
            "c",
            "--hints:off",
            "--verbosity:0",
            f"--nimcache:{nimcache_path}",
            f"-o:{exe_path}",
        ]
        if args.run:
            cmd.append("-r")
        cmd.append(str(output_path))
        return _run(cmd, cwd=Path.cwd(), stdout_to_stderr=True)

    print(f"error: unsupported build target: {target}", file=sys.stderr)
    return 1


def _manifest_path(output_dir: Path, args: argparse.Namespace) -> Path:
    if args.output != "":
        # py2cpp treats explicit output as single-file; for build path we keep
        # output_dir semantics only.
        return output_dir / "manifest.json"
    return output_dir / "manifest.json"


def _run_py2cpp(input_path: Path, output_dir: Path, argv: list[str]) -> int:
    cmd = [
        PYTHON,
        str(PY2X),
        str(input_path),
        "--target",
        "cpp",
        "--multi-file",
        "--output-dir",
        str(output_dir),
    ]
    cmd.extend(argv)
    return _run(cmd, cwd=Path.cwd(), stdout_to_stderr=True)


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
    return _run(cmd, cwd=Path.cwd(), stdout_to_stderr=True)


def _run_make(
    makefile_path: Path,
    target: str | None = None,
    timeout: float | None = None,
    *,
    stdout_to_stderr: bool = False,
) -> int:
    _require_make_available()
    cmd = ["make", "-f", str(makefile_path)]
    if target:
        cmd.append(target)
    return _run(cmd, cwd=makefile_path.parent, timeout=timeout, stdout_to_stderr=stdout_to_stderr)


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

    rc = _run_make(makefile_path, timeout=None, stdout_to_stderr=True)
    if rc != 0:
        return rc

    if args.run:
        exe_path = output_dir / args.exe
        if exe_path.exists() and exe_path.is_file():
            return _run([str(exe_path)], cwd=Path.cwd())
        return _run_make(makefile_path, target="run")
    return 0


def _transpile_cpp(input_path: Path, args: argparse.Namespace, passthrough: list[str]) -> int:
    cmd = [PYTHON, str(PY2X), str(input_path), "--target", "cpp"]
    if args.output != "":
        cmd.extend(["--output", args.output])
    if args.output_dir != DEFAULT_OUTPUT_DIR:
        cmd.extend(["--output-dir", args.output_dir])
    cmd.extend(passthrough)
    return _run(cmd, cwd=Path.cwd())


def _resolve_rs_output_path(input_path: Path, args: argparse.Namespace) -> Path:
    if args.output != "":
        return Path(args.output)
    out_dir = Path(args.output_dir) if args.output_dir else Path(DEFAULT_OUTPUT_DIR)
    stem = input_path.stem
    if stem == "":
        stem = "output"
    return out_dir / f"{stem}.rs"


def _transpile_rs(input_path: Path, args: argparse.Namespace, passthrough: list[str]) -> int:
    output_path = _resolve_rs_output_path(input_path, args)
    if output_path.exists() and output_path.is_dir():
        print(f"error: output path is a directory: {output_path}", file=sys.stderr)
        return 1
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [PYTHON, str(PY2X), str(input_path), "--target", "rs", "--output", str(output_path)]
    cmd.extend(passthrough)
    return _run(cmd, cwd=Path.cwd())


def _resolve_scala_output_path(input_path: Path, args: argparse.Namespace) -> Path:
    if args.output != "":
        return Path(args.output)
    out_dir = Path(args.output_dir) if args.output_dir else Path(DEFAULT_OUTPUT_DIR)
    stem = input_path.stem
    if stem == "":
        stem = "output"
    return out_dir / f"{stem}.scala"


def _transpile_scala(input_path: Path, args: argparse.Namespace, passthrough: list[str]) -> int:
    output_path = _resolve_scala_output_path(input_path, args)
    if output_path.exists() and output_path.is_dir():
        print(f"error: output path is a directory: {output_path}", file=sys.stderr)
        return 1
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [PYTHON, str(PY2X), str(input_path), "--target", "scala", "--output", str(output_path)]
    cmd.extend(passthrough)
    return _run(cmd, cwd=Path.cwd())


def _parse(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    argv = _normalize_args(argv)
    ap = argparse.ArgumentParser(description="pytra unified CLI (v1)")
    ap.add_argument("input", help="Input Python source path")
    ap.add_argument("--target", default="cpp", choices=SUPPORTED_TARGETS, help="target language")
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
    if args.build:
        passthrough_args.extend(passthrough)
        if args.target != "cpp":
            return _build_noncpp(input_path, args.target, args, passthrough_args)
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
        return _build_cpp(input_path, args, passthrough_args)

    passthrough_args.extend(passthrough)
    if args.target == "cpp":
        return _transpile_cpp(input_path, args, passthrough_args)
    if args.target == "rs":
        return _transpile_rs(input_path, args, passthrough_args)
    if args.target in {"cs", "js", "ts", "go", "java", "swift", "kotlin", "lua", "ruby", "php", "nim"}:
        output_path = _resolve_output_path(input_path, args.target, args)
        if output_path.exists() and output_path.is_dir():
            print(f"error: output path is a directory: {output_path}", file=sys.stderr)
            return 1
        return _run_py2x_target(input_path, args.target, output_path, passthrough_args)
    if args.target == "scala":
        return _transpile_scala(input_path, args, passthrough_args)
    print(f"error: unsupported target: {args.target}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
