#!/usr/bin/env python3
"""Standalone JavaScript backend: EAST3 JSON / link-output.json → JavaScript source.

Thin wrapper around east2x.py --target js.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 east2js.py INPUT.json -o out/output.js
    python3 east2js.py link-output.json -o out/output.js
"""

from __future__ import annotations

import sys

import east2x


def main() -> int:
    argv = sys.argv[1:]
    return east2x.main(["--target", "js"] + argv)


if __name__ == "__main__":
    sys.exit(main())
