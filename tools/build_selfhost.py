#!/usr/bin/env python3
"""Build selfhost transpiler C++ binary end-to-end.

Steps:
1) prepare selfhost/py2cpp.py from src/py2cpp.py
2) sync src/runtime -> selfhost/runtime
3) transpile selfhost/py2cpp.py -> selfhost/py2cpp.cpp
4) compile with runtime cpp sources
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELFHOST = ROOT / "selfhost"
SRC_RUNTIME = ROOT / "src" / "runtime"
SELFHOST_RUNTIME = SELFHOST / "runtime"
CPP_OUT = SELFHOST / "py2cpp.cpp"
BIN_OUT = SELFHOST / "py2cpp.out"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    proc = subprocess.run(cmd, cwd=str(cwd or ROOT), text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def runtime_cpp_sources() -> list[str]:
    files = sorted(SELFHOST_RUNTIME.rglob("*.cpp"))
    return [str(p) for p in files]


def patch_cpp_main_to_call_pytra_main(cpp_path: Path) -> None:
    text = cpp_path.read_text(encoding="utf-8")
    old = (
        "int main(int argc, char** argv) {\n"
        "    pytra_configure_from_argv(argc, argv);\n"
        "    return 0;\n"
        "}\n"
    )
    new = (
        "int main(int argc, char** argv) {\n"
        "    pytra_configure_from_argv(argc, argv);\n"
        "    list<str> __args = list<str>{};\n"
        "    int i = 1;\n"
        "    while (i < argc) {\n"
        "        __args.append(str(argv[i]));\n"
        "        i += 1;\n"
        "    }\n"
        "    return static_cast<int>(__pytra_main(__args));\n"
        "}\n"
    )
    if old in text:
        text = text.replace(old, new, 1)
    cpp_path.write_text(text, encoding="utf-8")


def main() -> int:
    run(["python3", "tools/prepare_selfhost_source.py"]) 

    SELFHOST_RUNTIME.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SRC_RUNTIME, SELFHOST_RUNTIME, dirs_exist_ok=True)

    run(["python3", "src/py2cpp.py", "selfhost/py2cpp.py", "-o", str(CPP_OUT)])
    patch_cpp_main_to_call_pytra_main(CPP_OUT)

    cpp_sources = runtime_cpp_sources()
    cmd = [
        "g++",
        "-std=c++17",
        "-O2",
        "-Iselfhost",
        str(CPP_OUT),
        *cpp_sources,
        "-o",
        str(BIN_OUT),
    ]
    run(cmd)

    print(str(BIN_OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
