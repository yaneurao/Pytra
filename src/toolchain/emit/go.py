#!/usr/bin/env python3
"""Go backend: manifest.json → Go multi-file output."""

from __future__ import annotations
import sys

from toolchain.emit.go.emitter import transpile_to_go
from toolchain.emit.loader import emit_all_modules


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) == 0 or argv[0] in ("-h", "--help"):
        print("usage: toolchain.emit.go MANIFEST.json --output-dir DIR")
        return 0

    input_path = ""
    output_dir = "work/tmp/go"
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
        print("error: input manifest.json is required", file=sys.stderr)
        return 1

    return emit_all_modules(input_path, output_dir, ".go", transpile_to_go, lang="go", flat=True)


if __name__ == "__main__":
    sys.exit(main())
