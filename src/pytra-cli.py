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
        _fatal("pytra emit: unknown target '" + target + "'")
    cmd = [_python(), emit_script] + remaining
    result = _run(cmd)
    return result.returncode


# ---------- build ----------

def cmd_build(argv: list[str]) -> int:
    """pytra build INPUT.py --output-dir DIR [--target TARGET] [--exe NAME] [--run] [-o FILE]"""
    # Parse args
    input_file = ""
    output_dir = "out"
    single_output = ""
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
        if (tok == "-o" or tok == "--output") and i + 1 < len(argv):
            single_output = argv[i + 1]
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
    # When -o is given, use its parent as output_dir
    if single_output != "":
        so_parent = str(Path(single_output).parent)
        if so_parent != "" and so_parent != ".":
            output_dir = so_parent
        else:
            output_dir = "."

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

    # Stage 2: emit (all languages use --output-dir)
    emit_argv = ["--target", target, link_output, "--output-dir", output_dir]
    rc = cmd_emit(emit_argv)
    if rc != 0:
        return rc

    # If -o was given, rename the entry output file to the requested name
    if single_output != "":
        entry_stem = Path(input_file).stem
        # Find the generated file in output_dir matching the entry stem
        generated = Path(output_dir) / (entry_stem + "." + target)
        if not generated.exists():
            # Try common extensions
            ext_map: dict[str, str] = {
                "cpp": "cpp", "rs": "rs", "cs": "cs", "js": "js", "ts": "ts",
                "go": "go", "java": "java", "swift": "swift", "kotlin": "kt",
                "scala": "scala", "lua": "lua", "ruby": "rb", "php": "php",
                "nim": "nim", "powershell": "ps1", "julia": "jl", "dart": "dart",
                "zig": "zig",
            }
            ext = ext_map.get(target, target)
            generated = Path(output_dir) / (entry_stem + "." + ext)
        so_path = Path(single_output)
        so_path.parent.mkdir(parents=True, exist_ok=True)
        if generated.exists() and str(generated.resolve()) != str(so_path.resolve()):
            so_path.write_text(generated.read_text(encoding="utf-8"), encoding="utf-8")

    # Stage 3: build + run
    entry_stem = Path(input_file).stem
    ext_map: dict[str, str] = {
        "cpp": "cpp", "rs": "rs", "cs": "cs", "js": "js", "ts": "ts",
        "go": "go", "java": "java", "swift": "swift", "kotlin": "kt",
        "scala": "scala", "lua": "lua", "ruby": "rb", "php": "php",
        "nim": "nim", "powershell": "ps1", "julia": "jl", "dart": "dart",
    }
    ext = ext_map.get(target, target)
    entry_output = output_dir + "/" + entry_stem + "." + ext

    if target == "cpp":
        # C++: Makefile → make → exe
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
        make_cmd = ["make", "-C", output_dir]
        result = _run(make_cmd)
        if result.returncode != 0:
            return result.returncode
        if do_run:
            result = _run([output_dir + "/" + exe_name])
            return result.returncode
        return 0

    # Non-C++ targets: run with language-specific runner
    if do_run:
        # Runner commands per target language.
        # pytra.std.subprocess で呼ぶため selfhost 互換。
        runner_map: dict[str, list[str]] = {
            "js": ["node"],
            "ts": ["npx", "-y", "tsx"],
            "go": ["go", "run"],
            "java": ["java"],
            "ruby": ["ruby"],
            "lua": ["lua"],
            "php": ["php"],
            "scala": ["scala", "run"],
            "nim": ["nim", "r"],
            "julia": ["julia"],
            "dart": ["dart", "run"],
            "powershell": ["pwsh", "-File"],
        }
        # Compiled languages: compile first, then run
        compile_map: dict[str, list[list[str]]] = {
            "rs": [["rustc", "-O", entry_output, "-o", output_dir + "/" + exe_name]],
            "cs": [["dotnet-script", entry_output]],
            "swift": [["swiftc", entry_output, "-o", output_dir + "/" + exe_name]],
            "kotlin": [["kotlinc", entry_output, "-include-runtime", "-d", output_dir + "/" + entry_stem + ".jar"]],
        }
        compile_run_map: dict[str, list[str]] = {
            "rs": [output_dir + "/" + exe_name],
            "swift": [output_dir + "/" + exe_name],
            "kotlin": ["java", "-cp", output_dir + "/" + entry_stem + ".jar", "pytra_" + entry_stem.replace("-", "_")],
        }

        if target in compile_map:
            for compile_cmd in compile_map[target]:
                result = _run(compile_cmd)
                if result.returncode != 0:
                    return result.returncode
            if target in compile_run_map:
                result = _run(compile_run_map[target])
                return result.returncode
            return 0

        if target in runner_map:
            run_cmd = runner_map[target] + [entry_output]
            result = _run(run_cmd)
            return result.returncode

        _fatal("pytra build --run: no runner configured for target '" + target + "'")

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
