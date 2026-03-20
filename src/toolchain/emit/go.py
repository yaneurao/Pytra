#!/usr/bin/env python3
"""Standalone Go backend: EAST3 JSON / link-output.json → Go source.

Thin wrapper around east2x.py --target go.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 east2go.py INPUT.json -o out/output.go
    python3 east2go.py link-output.json -o out/output.go
"""

from __future__ import annotations

import sys

import east2x


def main() -> int:
    argv = sys.argv[1:]
    return east2x.main(["--target", "go"] + argv)


if __name__ == "__main__":
    sys.exit(main())
