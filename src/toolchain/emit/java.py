#!/usr/bin/env python3
"""Standalone Java backend: EAST3 JSON / link-output.json → Java source.

Thin wrapper around east2x.py --target java.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 east2java.py INPUT.json -o out/output.java
    python3 east2java.py link-output.json -o out/output.java
"""

from __future__ import annotations

import sys

import east2x


def main() -> int:
    argv = sys.argv[1:]
    return east2x.main(["--target", "java"] + argv)


if __name__ == "__main__":
    sys.exit(main())
