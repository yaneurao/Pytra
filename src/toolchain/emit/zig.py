#!/usr/bin/env python3
"""Zig backend: link-output.json → Zig multi-file output.

Usage:
    python3 -m toolchain.emit.zig LINK_OUTPUT.json --output-dir out/zig/
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from toolchain.emit.zig.emitter import transpile_to_zig_native
from toolchain.emit.loader import emit_all_modules

_RUNTIME_DIR = Path(__file__).resolve().parents[2] / "runtime" / "zig" / "built_in"


def _copy_runtime(output_dir: str) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for f in _RUNTIME_DIR.iterdir():
        if f.is_file():
            shutil.copy2(f, out / f.name)


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) == 0 or argv[0] in ("-h", "--help"):
        print("usage: toolchain.emit.zig LINK_OUTPUT.json --output-dir DIR")
        return 0

    input_path = ""
    output_dir = "out/zig"
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

    rc = emit_all_modules(input_path, output_dir, ".zig", transpile_to_zig_native)
    if rc == 0:
        _copy_runtime(output_dir)
    return rc


if __name__ == "__main__":
    sys.exit(main())
