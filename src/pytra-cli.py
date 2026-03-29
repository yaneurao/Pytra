#!/usr/bin/env python3
"""Pytra unified CLI v2: compile / link / emit / build.

All stages are dispatched as subprocess calls, making this selfhost-compatible.
The same code path works in both Python host and C++ selfhost binary.

Usage:
    pytra compile INPUT.py -o out.east
    pytra link INPUT.py --output-dir out/ --target cpp
    pytra emit --target cpp out/manifest.json --output-dir out/emit/
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
    """pytra emit --target TARGET MANIFEST.json --output-dir DIR"""
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


def _build_go_via_toolchain2(
    input_file: str, output_dir: str, emit_dir: str,
    exe_name: str, do_build: bool, do_run: bool, single_output: str,
) -> int:
    """Build Go target via toolchain2 pipeline (parse→resolve→compile→optimize→link→emit)."""
    import sys as _sys
    src_dir = _find_src_dir()
    cli2 = src_dir + "/pytra-cli2.py"

    # Use pytra-cli2 -build to generate Go source
    build_cmd = [_python(), cli2, "-build", input_file, "--target", "go", "-o", emit_dir]
    result = _run(build_cmd)
    if result.returncode != 0:
        return result.returncode

    # Copy all runtime .go files (flattened into emit_dir for Go)
    import os as _os_walk
    import shutil as _shutil
    runtime_root = src_dir + "/runtime/go"
    for _dirpath, _dirnames, _filenames in _os_walk.walk(runtime_root):
        for _fn in _filenames:
            if _fn.endswith(".go"):
                _shutil.copy(_dirpath + "/" + _fn, emit_dir + "/" + _fn)

    if single_output != "":
        entry_stem = Path(input_file).stem
        generated = Path(emit_dir) / (entry_stem + ".go")
        if generated.exists():
            so_path = Path(single_output)
            so_path.parent.mkdir(parents=True, exist_ok=True)
            so_path.write_text(generated.read_text(encoding="utf-8"), encoding="utf-8")

    if not do_build and not do_run:
        return 0

    # go build + run: write go.mod, build, execute
    import os as _os
    go_mod_path = Path(emit_dir) / "go.mod"
    go_mod_path.write_text("module pytra_app\n\ngo 1.22\n", encoding="utf-8")

    go_files: list[str] = []
    for f in sorted(_os.listdir(emit_dir)):
        if f.endswith(".go"):
            go_files.append(emit_dir + "/" + f)
    if len(go_files) == 0:
        _fatal("no .go files found in " + emit_dir)

    go_exe = emit_dir + "/" + exe_name
    go_build_cmd = ["go", "build", "-o", go_exe] + go_files
    result = _run(go_build_cmd)
    if result.returncode != 0:
        return result.returncode

    result = _run([go_exe])
    return result.returncode


def _build_cpp_via_toolchain2(
    input_file: str, output_dir: str, emit_dir: str,
    exe_name: str, do_build: bool, do_run: bool, single_output: str,
) -> int:
    """Build C++ target via toolchain2 pipeline."""
    src_dir = _find_src_dir()
    cli2 = src_dir + "/pytra-cli2.py"

    build_cmd = [_python(), cli2, "-build", input_file, "--target", "cpp", "-o", emit_dir]
    result = _run(build_cmd)
    if result.returncode != 0:
        return result.returncode

    entry_stem = Path(input_file).stem
    generated = Path(emit_dir) / (entry_stem + ".cpp")
    if single_output != "" and generated.exists():
        so_path = Path(single_output)
        so_path.parent.mkdir(parents=True, exist_ok=True)
        so_path.write_text(generated.read_text(encoding="utf-8"), encoding="utf-8")

    if not do_build and not do_run:
        return 0

    import os as _os

    cpp_files: list[str] = []
    for dirpath, _dirnames, filenames in _os.walk(emit_dir):
        for name in sorted(filenames):
            if name.endswith(".cpp"):
                cpp_files.append(dirpath + "/" + name)

    runtime_root = Path(src_dir) / "runtime" / "cpp"
    native_sources: list[str] = [str(runtime_root / "core" / "io.cpp")]
    for bucket in ("std", "utils"):
        native_dir = runtime_root / bucket
        if not native_dir.exists():
            continue
        for cpp_path in sorted(native_dir.glob("*.cpp"), key=lambda p: str(p)):
            hdr_name = cpp_path.with_suffix(".h").name
            generated_hdr = Path(emit_dir) / bucket / hdr_name
            if generated_hdr.exists():
                native_sources.append(str(cpp_path))

    if len(cpp_files) == 0:
        _fatal("no .cpp files found in " + emit_dir)

    cpp_exe = emit_dir + "/" + exe_name
    compile_cmd = [
        "g++",
        "-std=c++20",
        "-O0",
        "-I", emit_dir,
        "-I", src_dir,
        "-I", src_dir + "/runtime/cpp",
        "-o", cpp_exe,
    ] + cpp_files + native_sources
    result = _run(compile_cmd)
    if result.returncode != 0:
        return result.returncode

    if not do_run:
        return 0

    result = _run([cpp_exe])
    return result.returncode


# ---------- build ----------

def cmd_build(argv: list[str], *, default_build: bool = True) -> int:
    """pytra build INPUT.py --output-dir DIR [--target TARGET] [--exe NAME] [--run] [-o FILE]"""
    # Parse args
    input_file = ""
    output_dir = "out"
    single_output = ""
    target = "cpp"
    exe_name = "app.out"
    do_build = default_build
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
            do_build = True
            i += 1
            continue
        if tok == "--build":
            do_build = True
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

    # When -o is given, emit into a temporary directory so that runtime files
    # produced by emitters do not pollute the -o parent.  Only the transpiled
    # entry file is copied out to the requested path.
    import tempfile as _tempfile
    _tmp_emit_dir_obj: object = None  # prevent premature cleanup
    if single_output != "":
        _tmp_emit_dir_obj = _tempfile.TemporaryDirectory()
        output_dir = _tmp_emit_dir_obj.name  # type: ignore[union-attr]

    src_dir = _find_src_dir()
    emit_dir = output_dir + "/emit"

    # Go target: delegate to new toolchain2 pipeline
    if target == "go":
        return _build_go_via_toolchain2(input_file, output_dir, emit_dir, exe_name, do_build, do_run, single_output)
    if target == "cpp":
        return _build_cpp_via_toolchain2(input_file, output_dir, emit_dir, exe_name, do_build, do_run, single_output)

    # Stage 1: compile + link (writes manifest.json + east3/ into output_dir)
    link_cmd = [
        _python(), src_dir + "/toolchain/link/cli.py",
        input_file,
        "--target", target,
        "--output-dir", output_dir,
    ]
    link_cmd.extend(passthrough)
    result = _run(link_cmd)
    if result.returncode != 0:
        return result.returncode

    link_output = output_dir + "/manifest.json"

    # Stage 2: emit (writes target source into emit/ subdirectory)
    emit_argv = ["--target", target, link_output, "--output-dir", emit_dir]
    rc = cmd_emit(emit_argv)
    if rc != 0:
        return rc

    # If -o was given, copy only the transpiled entry file to the requested path
    if single_output != "":
        entry_stem = Path(input_file).stem
        # Find the generated file in emit_dir matching the entry stem
        generated = Path(emit_dir) / (entry_stem + "." + target)
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
            generated = Path(emit_dir) / (entry_stem + "." + ext)
        so_path = Path(single_output)
        so_path.parent.mkdir(parents=True, exist_ok=True)
        if generated.exists():
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
    entry_output = emit_dir + "/" + entry_stem + "." + ext

    if target == "cpp":
        # C++: Makefile → make → exe
        makefile_gen = src_dir + "/../tools/gen/gen_makefile_from_manifest.py"
        manifest = emit_dir + "/manifest.json"
        makefile = emit_dir + "/Makefile"
        gen_cmd = [
            _python(), makefile_gen,
            manifest,
            "-o", makefile,
            "--exe", exe_name,
        ]
        result = _run(gen_cmd)
        if result.returncode != 0:
            return result.returncode
        make_cmd = ["make", "-C", emit_dir]
        result = _run(make_cmd)
        if result.returncode != 0:
            return result.returncode
        if do_run:
            result = _run([emit_dir + "/" + exe_name])
            return result.returncode
        return 0

    # Non-C++ targets: run with language-specific runner
    if do_run:
        # Runner commands per target language.
        # pytra.std.subprocess で呼ぶため selfhost 互換。
        runner_map: dict[str, list[str]] = {
            "js": ["node"],
            "ts": ["npx", "-y", "tsx"],
            "ruby": ["ruby"],
            "lua": ["lua"],
            "php": ["php", "-d", "memory_limit=8G"],
            "scala": ["scala", "run"],
            # nim is handled above with explicit compile + run
            "julia": ["julia"],
            "dart": ["dart", "run"],
            "powershell": ["pwsh", "-File"],
        }
        # Compiled languages: compile first, then run
        compile_map: dict[str, list[list[str]]] = {
            "rs": [["rustc", "-O", entry_output, "-o", emit_dir + "/" + exe_name]],
            # swift is handled below (needs all .swift files)
        }
        compile_run_map: dict[str, list[str]] = {
            "rs": [emit_dir + "/" + exe_name],
            # swift is handled below
        }

        import os as _os

        # C#: collect all .cs in emit_dir, compile with mcs, run with mono
        # utils/*.cs in emit_dir are emitter output (wrong class names);
        # replace with generated runtime from src/runtime/cs/generated/utils/.
        if target == "cs":
            cs_exe = emit_dir + "/" + entry_stem + "_cs.exe"
            cs_files: list[str] = []
            for root_dir, dirs, files in _os.walk(emit_dir):
                for f in sorted(files):
                    if f.endswith(".cs"):
                        rel = _os.path.relpath(_os.path.join(root_dir, f), emit_dir)
                        if rel.startswith("utils/") or rel.startswith("utils\\"):
                            continue
                        cs_files.append(_os.path.join(root_dir, f))
            gen_utils = _find_src_dir() + "/runtime/cs/generated/utils"
            if _os.path.isdir(gen_utils):
                for root_dir, dirs, files in _os.walk(gen_utils):
                    for f in sorted(files):
                        if f.endswith(".cs") and f != "assertions.cs":
                            cs_files.append(_os.path.join(root_dir, f))
            mcs_cmd = ["mcs", "-warn:0", "-out:" + cs_exe] + cs_files
            result = _run(mcs_cmd)
            if result.returncode != 0:
                return result.returncode
            result = _run(["mono", cs_exe])
            return result.returncode

        # Go: collect all .go in emit_dir, go build, then run exe
        if target == "go":
            go_exe = emit_dir + "/" + exe_name
            go_files: list[str] = []
            for f in sorted(_os.listdir(emit_dir)):
                if f.endswith(".go"):
                    go_files.append(emit_dir + "/" + f)
            build_cmd = ["go", "build", "-o", go_exe] + go_files
            result = _run(build_cmd)
            if result.returncode != 0:
                return result.returncode
            result = _run([go_exe])
            return result.returncode

        # Java: javac all .java in emit_dir (recursive), then java main class
        if target == "java":
            java_files: list[str] = []
            for root_dir, dirs, files in _os.walk(emit_dir):
                for f in sorted(files):
                    if f.endswith(".java"):
                        java_files.append(_os.path.join(root_dir, f))
            javac_cmd = ["javac", "-encoding", "UTF-8"] + java_files
            result = _run(javac_cmd)
            if result.returncode != 0:
                return result.returncode
            # Include all subdirectories in classpath
            cp_parts = [emit_dir]
            for sub in sorted(_os.listdir(emit_dir)):
                sub_path = emit_dir + "/" + sub
                if _os.path.isdir(sub_path):
                    cp_parts.append(sub_path)
            cp = ":".join(cp_parts)
            result = _run(["java", "-cp", cp, "Main"])
            return result.returncode

        # Swift: swiftc all .swift in emit_dir (recursive) → exe
        if target == "swift":
            swift_exe = emit_dir + "/" + exe_name
            swift_files: list[str] = []
            for root_dir, dirs, files in _os.walk(emit_dir):
                for f in sorted(files):
                    if f.endswith(".swift"):
                        swift_files.append(_os.path.join(root_dir, f))
            swiftc_cmd = ["swiftc"] + swift_files + ["-o", swift_exe]
            result = _run(swiftc_cmd)
            if result.returncode != 0:
                return result.returncode
            result = _run([swift_exe])
            return result.returncode

        # Nim: nim c all .nim entry, then run exe
        # Nim requires valid identifiers for module names (no leading digits).
        # Use `nim c` + explicit -o to avoid the restriction of `nim r`.
        # Rename entry file if its stem starts with a digit.
        if target == "nim":
            nim_exe = emit_dir + "/" + exe_name
            nim_entry = entry_output
            if not _os.path.exists(nim_entry):
                alt = emit_dir + "/main.nim"
                if _os.path.exists(alt):
                    nim_entry = alt
            # Rename entry file when the stem starts with a digit
            nim_stem = _os.path.basename(nim_entry)
            if nim_stem[:1].isdigit():
                safe_name = "m_" + nim_stem
                safe_path = emit_dir + "/" + safe_name
                _os.rename(nim_entry, safe_path)
                nim_entry = safe_path
            nim_cmd = ["nim", "c", "--hints:off", "--warnings:off", "--path:" + emit_dir, "-o:" + nim_exe, nim_entry]
            result = _run(nim_cmd)
            if result.returncode != 0:
                return result.returncode
            result = _run([nim_exe])
            return result.returncode

        # Kotlin: kotlinc all .kt → jar, then java -cp jar main
        if target == "kotlin":
            kt_files: list[str] = []
            for root_dir, dirs, files in _os.walk(emit_dir):
                for f in sorted(files):
                    if f.endswith(".kt"):
                        kt_files.append(_os.path.join(root_dir, f))
            jar_path = emit_dir + "/" + entry_stem + ".jar"
            kotlinc_cmd = ["kotlinc"] + kt_files + ["-include-runtime", "-d", jar_path]
            result = _run(kotlinc_cmd)
            if result.returncode != 0:
                return result.returncode
            result = _run(["java", "-jar", jar_path])
            return result.returncode

        if target in compile_map:
            for compile_cmd in compile_map[target]:
                result = _run(compile_cmd)
                if result.returncode != 0:
                    return result.returncode
            if target in compile_run_map:
                result = _run(compile_run_map[target])
                return result.returncode
            return 0

        # Scala: collect all .scala files recursively for scala run
        if target == "scala":
            scala_files: list[str] = []
            for root_dir, dirs, files in _os.walk(emit_dir):
                for f in sorted(files):
                    if f.endswith(".scala"):
                        scala_files.append(_os.path.join(root_dir, f))
            run_cmd = ["scala-cli", "run", "--jvm", "17"] + scala_files
            result = _run(run_cmd)
            return result.returncode

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
    print("  link      .py → linked EAST (manifest.json + east3/)")
    print("  emit      linked EAST → target source (emit/)")
    print("  build     .py → executable (compile + link + emit + g++)")
    print("")
    print("examples:")
    print("  pytra compile foo.py -o foo.east")
    print("  pytra link foo.py --output-dir out/ --target cpp")
    print("  pytra emit --target cpp out/manifest.json --output-dir out/emit/")
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
        return cmd_build(rest, default_build=True)

    # Default: treat as transpile-only unless --build/--run is requested.
    return cmd_build(argv, default_build=False)


if __name__ == "__main__":
    sys.exit(main())
