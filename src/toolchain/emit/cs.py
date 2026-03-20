#!/usr/bin/env python3
"""Standalone C# backend: EAST3 JSON / link-output.json → C# source.

Thin wrapper around east2x.py --target cs.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 east2cs.py INPUT.json -o out/output.cs
    python3 east2cs.py link-output.json -o out/output.cs
"""

from __future__ import annotations

import sys

import east2x


def main() -> int:
    argv = sys.argv[1:]
    return east2x.main(["--target", "cs"] + argv)


if __name__ == "__main__":
    sys.exit(main())
