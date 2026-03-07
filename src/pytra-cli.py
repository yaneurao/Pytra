#!/usr/bin/env python3
"""Project CLI entrypoint for Pytra tools."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from toolchain.compiler.pytra_cli_profiles import (
    SUPPORTED_TARGETS,
    TargetProfile,
    get_target_profile,
    make_noncpp_build_plan,
    resolve_output_path as resolve_profile_output_path,
    validate_profile_option_compatibility,
)


# /src/pytra-cli.py -> project root is parents[1]
ROOT = Path(__file__).resolve().parents[1]
PY2X = ROOT / "src" / "py2x.py"
GEN_MAKEFILE = ROOT / "tools" / "gen_makefile_from_manifest.py"
PYTHON = sys.executable or "python3"

DEFAULT_OUTPUT_DIR = "out"
DEFAULT_EXE = "app.out"
DEFAULT_STD = "c++20"
DEFAULT_COMPILER = "g++"
DEFAULT_OPT = "-O2"
_OPT_SHORT_RE = re.compile(r"^-O[0-3]$")
_CPP_LINKED_MAX_DIRNAME = ".pytra_linked"


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
    return _run_proc(cmd, cwd=cwd, timeout=timeout, stdout_to_stderr=stdout_to_stderr).returncode


def _run_proc(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: float | None = None,
    *,
    stdout_to_stderr: bool = False,
) -> subprocess.CompletedProcess[str]:
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
        return proc
    if proc.stderr:
        # Keep warnings for compatibility.
        print(proc.stderr, end="", file=sys.stderr)
    return proc


def _reported_manifest_path(stdout: str, *, cwd: Path) -> Path | None:
    lines = stdout.splitlines()
    idx = len(lines) - 1
    while idx >= 0:
        line = lines[idx].strip()
        if line.startswith("manifest:"):
            raw_path = line[len("manifest:") :].strip()
            if raw_path == "":
                return None
            path = Path(raw_path)
            if path.is_absolute():
                return path
            return (cwd / path).resolve()
        idx -= 1
    return None


def _resolve_cpp_manifest_path(stdout: str, output_dir: Path) -> Path | None:
    reported = _reported_manifest_path(stdout, cwd=Path.cwd())
    if reported is not None:
        return reported
    fallback = (output_dir / "manifest.json").resolve()
    if fallback.exists():
        return fallback
    return None


def _require_manifest_exists(path: Path | None) -> Path | None:
    if path is None:
        return None
    if path.exists():
        return path
    return None


def _require_make_available() -> str:
    make_path = shutil.which("make")
    if make_path is None:
        raise RuntimeError("make not found in PATH")
    return make_path


def _resolve_output_path(input_path: Path, profile: TargetProfile, args: argparse.Namespace) -> Path:
    return resolve_profile_output_path(input_path, profile.target, args.output, args.output_dir)


def _run_py2x_target(
    input_path: Path,
    profile: TargetProfile,
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
        profile.target,
        "--output",
        str(output_path),
    ]
    cmd.extend(argv)
    return _run(cmd, cwd=Path.cwd(), stdout_to_stderr=stdout_to_stderr)


def _build_noncpp(input_path: Path, profile: TargetProfile, args: argparse.Namespace, passthrough: list[str]) -> int:
    output_path = _resolve_output_path(input_path, profile, args)
    if output_path.exists() and output_path.is_dir():
        print(f"error: output path is a directory: {output_path}", file=sys.stderr)
        return 1

    rc = _run_py2x_target(input_path, profile, output_path, passthrough, stdout_to_stderr=True)
    if rc != 0:
        return rc

    plan = make_noncpp_build_plan(
        root=ROOT,
        target=profile.target,
        output_path=output_path,
        source_stem=input_path.stem,
        run_after_build=args.run,
    )
    if isinstance(plan.build_cmd, list):
        rc = _run(plan.build_cmd, cwd=Path.cwd(), stdout_to_stderr=True)
        if rc != 0:
            return rc
    if isinstance(plan.run_cmd, list):
        return _run(plan.run_cmd, cwd=Path.cwd())
    return 0


def _run_py2cpp(input_path: Path, output_dir: Path, argv: list[str]) -> tuple[int, Path | None]:
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
    proc = _run_proc(cmd, cwd=Path.cwd(), stdout_to_stderr=True)
    manifest_path = None
    if proc.returncode == 0:
        manifest_path = _require_manifest_exists(_resolve_cpp_manifest_path(proc.stdout or "", output_dir))
    return int(proc.returncode), manifest_path


def _has_passthrough_flag(argv: list[str], flag: str) -> bool:
    for token in argv:
        if token == flag or token.startswith(flag + "="):
            return True
    return False


def _has_layer_option_key(argv: list[str], flag: str, key: str) -> bool:
    idx = 0
    while idx < len(argv):
        token = argv[idx]
        if token == flag and idx + 1 < len(argv):
            item = argv[idx + 1]
            if item == key or item.startswith(key + "="):
                return True
            idx += 2
            continue
        if token.startswith(flag + "="):
            raw = token[len(flag) + 1 :]
            if raw == key or raw.startswith(key + "="):
                return True
        idx += 1
    return False


def _cpp_max_linked_stage_args(argv: list[str]) -> tuple[list[str], list[str]]:
    stage1 = list(argv)
    if not _has_passthrough_flag(stage1, "--east3-opt-level"):
        stage1.extend(["--east3-opt-level", "2"])

    stage2 = list(argv)
    if not _has_layer_option_key(stage2, "--optimizer-option", "cpp_opt_level"):
        stage2.extend(["--optimizer-option", "cpp_opt_level=2"])
    return stage1, stage2


def _run_py2cpp_linked_max(input_path: Path, output_dir: Path, argv: list[str]) -> tuple[int, Path | None]:
    linked_dir = output_dir / _CPP_LINKED_MAX_DIRNAME
    linked_dir.mkdir(parents=True, exist_ok=True)
    link_stage_argv, emit_stage_argv = _cpp_max_linked_stage_args(argv)

    link_cmd = [
        PYTHON,
        str(PY2X),
        str(input_path),
        "--target",
        "cpp",
        "--link-only",
        "--output-dir",
        str(linked_dir),
    ]
    link_cmd.extend(link_stage_argv)
    link_proc = _run_proc(link_cmd, cwd=Path.cwd(), stdout_to_stderr=True)
    if link_proc.returncode != 0:
        return int(link_proc.returncode), None

    link_output_path = linked_dir / "link-output.json"
    if not link_output_path.exists():
        print(f"error: link-output not found after linked optimize under: {linked_dir}", file=sys.stderr)
        return 1, None

    emit_cmd = [
        PYTHON,
        str(PY2X),
        str(link_output_path),
        "--target",
        "cpp",
        "--from-link-output",
        "--output-dir",
        str(output_dir),
    ]
    emit_cmd.extend(emit_stage_argv)
    emit_proc = _run_proc(emit_cmd, cwd=Path.cwd(), stdout_to_stderr=True)
    manifest_path = None
    if emit_proc.returncode == 0:
        manifest_path = _require_manifest_exists(_resolve_cpp_manifest_path(emit_proc.stdout or "", output_dir))
    return int(emit_proc.returncode), manifest_path


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


def _build_cpp(input_path: Path, args: argparse.Namespace, passthrough: list[str], *, use_linked_max_route: bool = False) -> int:
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

    if use_linked_max_route:
        rc, manifest_path = _run_py2cpp_linked_max(input_path, output_dir, passthrough)
    else:
        rc, manifest_path = _run_py2cpp(input_path, output_dir, passthrough)
    if rc != 0:
        return rc

    if manifest_path is None:
        print(f"error: manifest not found after transpile under: {output_dir}", file=sys.stderr)
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


def _transpile_cpp(
    input_path: Path,
    args: argparse.Namespace,
    passthrough: list[str],
    *,
    use_linked_max_route: bool = False,
) -> int:
    if use_linked_max_route:
        if args.output != "":
            print(
                "error: --output is not supported with --target cpp --codegen-opt 3. Use --output-dir.",
                file=sys.stderr,
            )
            return 1
        output_dir = (Path(args.output_dir) if args.output_dir else Path(DEFAULT_OUTPUT_DIR)).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        rc, _manifest_path = _run_py2cpp_linked_max(input_path, output_dir, passthrough)
        return rc

    cmd = [PYTHON, str(PY2X), str(input_path), "--target", "cpp"]
    if args.output != "":
        cmd.extend(["--output", args.output])
    if args.output_dir != DEFAULT_OUTPUT_DIR:
        cmd.extend(["--output-dir", args.output_dir])
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
    try:
        profile = get_target_profile(args.target)
    except RuntimeError as ex:
        print("error: " + str(ex), file=sys.stderr)
        return 1
    incompat = validate_profile_option_compatibility(
        profile,
        codegen_opt=args.codegen_opt,
        build=bool(args.build),
        compiler=args.compiler,
        std=args.std,
        opt=args.opt,
        exe=args.exe,
    )
    if incompat != "":
        print("error: " + incompat, file=sys.stderr)
        return 1

    passthrough_args: list[str] = []
    codegen_opt = args.codegen_opt
    use_cpp_linked_max_route = profile.target == "cpp" and codegen_opt == 3
    if codegen_opt is not None and not use_cpp_linked_max_route:
        passthrough_args.extend([f"-O{codegen_opt}"])
    if args.build:
        passthrough_args.extend(passthrough)
        if profile.build_driver == "noncpp":
            return _build_noncpp(input_path, profile, args, passthrough_args)
        if profile.build_driver == "cpp_make":
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
            return _build_cpp(
                input_path,
                args,
                passthrough_args,
                use_linked_max_route=use_cpp_linked_max_route,
            )
        print("error: unsupported build driver: " + profile.build_driver, file=sys.stderr)
        return 1

    passthrough_args.extend(passthrough)
    if profile.build_driver == "cpp_make":
        return _transpile_cpp(
            input_path,
            args,
            passthrough_args,
            use_linked_max_route=use_cpp_linked_max_route,
        )
    output_path = _resolve_output_path(input_path, profile, args)
    if output_path.exists() and output_path.is_dir():
        print(f"error: output path is a directory: {output_path}", file=sys.stderr)
        return 1
    return _run_py2x_target(input_path, profile, output_path, passthrough_args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
