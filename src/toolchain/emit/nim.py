#!/usr/bin/env python3
"""Standalone Nim backend: EAST3 JSON / link-output.json → Nim source.

Thin wrapper around east2x.py --target nim.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 east2nim.py INPUT.json -o out/output.nim
    python3 east2nim.py link-output.json -o out/output.nim
"""

from __future__ import annotations

import sys

import east2x


def main() -> int:
    argv = sys.argv[1:]
    return east2x.main(["--target", "nim"] + argv)


if __name__ == "__main__":
    sys.exit(main())
