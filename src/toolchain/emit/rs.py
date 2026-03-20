#!/usr/bin/env python3
"""Standalone Rust backend: EAST3 JSON / link-output.json → Rust source.

Thin wrapper around east2x.py --target rs.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 east2rs.py INPUT.json -o out/output.rs
    python3 east2rs.py link-output.json -o out/output.rs
"""

from __future__ import annotations

import sys

import east2x


def main() -> int:
    argv = sys.argv[1:]
    return east2x.main(["--target", "rs"] + argv)


if __name__ == "__main__":
    sys.exit(main())
