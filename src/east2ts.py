#!/usr/bin/env python3
"""Standalone TypeScript backend: EAST3 JSON / link-output.json → TypeScript source.

Thin wrapper around east2x.py --target ts.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 east2ts.py INPUT.json -o out/output.ts
    python3 east2ts.py link-output.json -o out/output.ts
"""

from __future__ import annotations

import sys

import east2x


def main() -> int:
    argv = sys.argv[1:]
    return east2x.main(["--target", "ts"] + argv)


if __name__ == "__main__":
    sys.exit(main())
