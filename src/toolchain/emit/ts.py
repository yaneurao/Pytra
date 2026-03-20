#!/usr/bin/env python3
"""Standalone TypeScript backend: EAST3 JSON / link-output.json → TypeScript source.

Thin wrapper around east2x.py --target ts.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 -m toolchain.emit.ts INPUT.json -o out/output.ts
    python3 -m toolchain.emit.ts link-output.json -o out/output.ts
"""

from __future__ import annotations

import sys

from toolchain.emit import all as _emit_all


def main() -> int:
    argv = sys.argv[1:]
    return _emit_all.main(["--target", "ts"] + argv)


if __name__ == "__main__":
    sys.exit(main())
