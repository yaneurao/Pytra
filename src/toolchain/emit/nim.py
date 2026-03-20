#!/usr/bin/env python3
"""Standalone Nim backend: EAST3 JSON / link-output.json → Nim source.

Thin wrapper around east2x.py --target nim.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 -m toolchain.emit.nim INPUT.json -o out/output.nim
    python3 -m toolchain.emit.nim link-output.json -o out/output.nim
"""

from __future__ import annotations

import sys

from toolchain.emit import all as _emit_all


def main() -> int:
    argv = sys.argv[1:]
    return _emit_all.main(["--target", "nim"] + argv)


if __name__ == "__main__":
    sys.exit(main())
