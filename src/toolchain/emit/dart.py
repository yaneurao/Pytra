#!/usr/bin/env python3
"""Dart backend: link-output.json → Dart multi-file output.

Usage:
    python3 -m toolchain.emit.dart LINK_OUTPUT.json --output-dir out/dart/
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from toolchain.emit.dart.emitter import transpile_to_dart_native
from toolchain.emit.loader import emit_all_modules


def _copy_runtime(output_dir: str) -> None:
    """Copy py_runtime.dart to each directory containing generated .dart files."""
    src_dir = Path(__file__).resolve().parent.parent.parent
    runtime_src = src_dir / "runtime" / "dart" / "built_in" / "py_runtime.dart"
    if not runtime_src.exists():
        return
    out = Path(output_dir)
    # Copy runtime to all directories containing .dart files
    dirs_seen: set[str] = set()
    for dart_file in out.rglob("*.dart"):
        parent = str(dart_file.parent)
        if parent not in dirs_seen:
            dirs_seen.add(parent)
            dest = dart_file.parent / "py_runtime.dart"
            if not dest.exists():
                shutil.copy2(str(runtime_src), str(dest))


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) == 0 or argv[0] in ("-h", "--help"):
        print("usage: toolchain.emit.dart LINK_OUTPUT.json --output-dir DIR")
        return 0

    input_path = ""
    output_dir = "out/dart"
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--output-dir" and i + 1 < len(argv):
            output_dir = argv[i + 1]
            i += 2
            continue
        if not tok.startswith("-") and input_path == "":
            input_path = tok
        i += 1

    if input_path == "":
        print("error: input link-output.json is required", file=sys.stderr)
        return 1

    rc = emit_all_modules(input_path, output_dir, ".dart", transpile_to_dart_native)
    if rc == 0:
        _copy_runtime(output_dir)
    return rc


if __name__ == "__main__":
    sys.exit(main())
