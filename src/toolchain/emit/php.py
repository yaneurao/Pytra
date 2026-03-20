#!/usr/bin/env python3
"""Standalone PHP backend: EAST3 JSON / link-output.json → PHP source.

Thin wrapper around east2x.py --target php.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 -m toolchain.emit.php INPUT.json -o out/output.php
    python3 -m toolchain.emit.php link-output.json -o out/output.php
"""

from __future__ import annotations

import sys

from toolchain.emit import all as _emit_all


def main() -> int:
    argv = sys.argv[1:]
    return _emit_all.main(["--target", "php"] + argv)


if __name__ == "__main__":
    sys.exit(main())
