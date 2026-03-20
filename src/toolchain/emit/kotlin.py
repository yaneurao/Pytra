#!/usr/bin/env python3
"""Standalone Kotlin backend: EAST3 JSON / link-output.json → Kotlin source.

Thin wrapper around east2x.py --target kotlin.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 east2kotlin.py INPUT.json -o out/output.kt
    python3 east2kotlin.py link-output.json -o out/output.kt
"""

from __future__ import annotations

import sys

import east2x


def main() -> int:
    argv = sys.argv[1:]
    return east2x.main(["--target", "kotlin"] + argv)


if __name__ == "__main__":
    sys.exit(main())
