#!/usr/bin/env python3
"""Pytra unified CLI v2: compile / link / emit / build.

All stages are dispatched as subprocess calls, making this selfhost-compatible.
The same code path works in both Python host and C++ selfhost binary.

Usage:
    pytra compile INPUT.py -o out.east
    pytra link out.east --output-dir out/linked/
    pytra emit --target cpp out/linked/link-output.json --output-dir out/cpp/
    pytra build INPUT.py --output-dir out/ --exe app.out
    pytra build INPUT.py --output-dir out/ --exe app.out --run
"""

from __future__ import annotations

from pytra.std import sys
from pytra.std.pathlib import Path
from pytra.std.subprocess import run as subprocess_run
from pytra.std.subprocess import CompletedProcess


def _fatal(msg: str) -> None:
    sys.write_stderr("error: " + msg + "\n")
    sys.exit(2)


def _find_src_dir() -> str:
    """Locate src/ directory relative to this script."""
    # __file__ is src/pytra-cli2.py, so src/ is the parent
    p = Path(__file__).resolve().parent
    return str(p)


def _python() -> str:
    """Return the Python interpreter path."""
    import sys as _stdlib_sys
    return _stdlib_sys.executable or "python3"


def _src_env() -> dict[str, str]:
    """Return env dict with PYTHONPATH including src/."""
    return {"PYTHONPATH": _find_src_dir()}


def _run(cmd: list[str]) -> CompletedProcess:
    """Run a subprocess with PYTHONPATH set."""
    return subprocess_run(cmd, env=_src_env())


# ---------- compile ----------

def cmd_compile(argv: list[str]) -> int:
    """pytra compile INPUT.py [-o OUTPUT.east] [options...]"""
    src_dir = _find_src_dir()
    cmd = [_python(), src_dir + "/toolchain/compile/cli.py"] + argv
    result = _run(cmd)
    return result.returncode


# ---------- link ----------

def cmd_link(argv: list[str]) -> int:
    """pytra link INPUT.py [--output-dir DIR] [--target TARGET] [options...]"""
    src_dir = _find_src_dir()
    cmd = [_python(), src_dir + "/toolchain/link/cli.py"] + argv
    result = _run(cmd)
    return result.returncode


# ---------- emit ----------

def cmd_emit(argv: list[str]) -> int:
    """pytra emit --target TARGET LINK_OUTPUT.json --output-dir DIR"""
    target = ""
    remaining: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "--target" and i + 1 < len(argv):
            target = argv[i + 1]
            i += 2
            continue
        remaining.append(argv[i])
        i += 1

    if target == "":
        _fatal("pytra emit: --target is required")
    src_dir = _find_src_dir()
    emit_script = src_dir + "/toolchain/emit/" + target + ".py"
    if not Path(emit_script).exists():
        # Fallback to all.py for unknown targets
        emit_script = src_dir + "/toolchain/emit/all.py"
        remaining = ["--target", target] + remaining
    cmd = [_python(), emit_script] + remaining
    result = _run(cmd)
    return result.returncode


# ---------- build ----------

def cmd_build(argv: list[str]) -> int:
    """pytra build INPUT.py --output-dir DIR [--target TARGET] [--exe NAME] [--run]"""
    # Parse args
    input_file = ""
    output_dir = "out"
    target = "cpp"
    exe_name = "app.out"
    do_run = False
    passthrough: list[str] = []
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--output-dir" and i + 1 < len(argv):
            output_dir = argv[i + 1]
            i += 2
            continue
        if tok == "--target" and i + 1 < len(argv):
            target = argv[i + 1]
            i += 2
            continue
        if tok == "--exe" and i + 1 < len(argv):
            exe_name = argv[i + 1]
            i += 2
            continue
        if tok == "--run":
            do_run = True
            i += 1
            continue
        if tok.startswith("-"):
            passthrough.append(tok)
            i += 1
            continue
        if input_file == "":
            input_file = tok
        i += 1

    if input_file == "":
        _fatal("pytra build: input file is required")

    src_dir = _find_src_dir()
    linked_dir = output_dir + "/.pytra_linked"

    # Stage 1: compile + link
    link_cmd = [
        _python(), src_dir + "/toolchain/link/cli.py",
        input_file,
        "--target", target,
        "--output-dir", linked_dir,
    ]
    link_cmd.extend(passthrough)
    result = _run(link_cmd)
    if result.returncode != 0:
        return result.returncode

    link_output = linked_dir + "/link-output.json"

    # Stage 2: emit
    emit_argv = ["--target", target, link_output, "--output-dir", output_dir]
    rc = cmd_emit(emit_argv)
    if rc != 0:
        return rc

    # Stage 3: build (C++ only for now)
    if target == "cpp":
        # Generate Makefile
        makefile_gen = src_dir + "/../tools/gen_makefile_from_manifest.py"
        manifest = output_dir + "/manifest.json"
        makefile = output_dir + "/Makefile"
        gen_cmd = [
            _python(), makefile_gen,
            manifest,
            "-o", makefile,
            "--exe", exe_name,
        ]
        result = _run(gen_cmd)
        if result.returncode != 0:
            return result.returncode

        # Run make
        make_cmd = ["make", "-C", output_dir]
        result = _run(make_cmd)
        if result.returncode != 0:
            return result.returncode

        # Run if requested
        if do_run:
            exe_path = output_dir + "/" + exe_name
            result = _run([exe_path])
            return result.returncode

    return 0


# ---------- main ----------

def _print_help() -> None:
    print("usage: pytra <command> [options]")
    print("")
    print("commands:")
    print("  compile   .py → .east (EAST3 JSON)")
    print("  link      .east → linked EAST (link-output.json)")
    print("  emit      linked EAST → target source")
    print("  build     .py → executable (compile + link + emit + g++)")
    print("")
    print("examples:")
    print("  pytra compile foo.py -o foo.east")
    print("  pytra link foo.east --output-dir out/linked/ --target cpp")
    print("  pytra emit --target cpp out/linked/link-output.json --output-dir out/cpp/")
    print("  pytra build foo.py --output-dir out/ --exe app.out --run")


def main() -> int:
    argv: list[str] = sys.argv[1:]
    if len(argv) == 0:
        _print_help()
        return 0

    cmd = argv[0]
    rest = argv[1:]

    if cmd == "-h" or cmd == "--help":
        _print_help()
        return 0
    if cmd == "compile":
        return cmd_compile(rest)
    if cmd == "link":
        return cmd_link(rest)
    if cmd == "emit":
        return cmd_emit(rest)
    if cmd == "build":
        return cmd_build(rest)

    # Default: treat as build (backward compat with ./pytra INPUT.py --build)
    return cmd_build(argv)


if __name__ == "__main__":
    sys.exit(main())
