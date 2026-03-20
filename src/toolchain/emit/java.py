#!/usr/bin/env python3
"""Standalone Java backend: EAST3 JSON / link-output.json → Java source.

Thin wrapper around east2x.py --target java.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 -m toolchain.emit.java INPUT.json -o out/output.java
    python3 -m toolchain.emit.java link-output.json -o out/output.java
"""

from __future__ import annotations

import sys

from toolchain.emit import all as _emit_all


def main() -> int:
    argv = sys.argv[1:]
    return _emit_all.main(["--target", "java"] + argv)


if __name__ == "__main__":
    sys.exit(main())
