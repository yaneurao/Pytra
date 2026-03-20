#!/usr/bin/env python3
"""Standalone Kotlin backend: EAST3 JSON / link-output.json → Kotlin source.

Thin wrapper around east2x.py --target kotlin.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 -m toolchain.emit.kotlin INPUT.json -o out/output.kt
    python3 -m toolchain.emit.kotlin link-output.json -o out/output.kt
"""

from __future__ import annotations

import sys

from toolchain.emit import all as _emit_all


def main() -> int:
    argv = sys.argv[1:]
    return _emit_all.main(["--target", "kotlin"] + argv)


if __name__ == "__main__":
    sys.exit(main())
