#!/usr/bin/env python3
"""Standalone PHP backend: EAST3 JSON / link-output.json → PHP source.

Thin wrapper around east2x.py --target php.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 east2php.py INPUT.json -o out/output.php
    python3 east2php.py link-output.json -o out/output.php
"""

from __future__ import annotations

import sys

import east2x


def main() -> int:
    argv = sys.argv[1:]
    return east2x.main(["--target", "php"] + argv)


if __name__ == "__main__":
    sys.exit(main())
