#!/usr/bin/env python3
"""Standalone JavaScript backend: EAST3 JSON / link-output.json → JavaScript source.

Thin wrapper around east2x.py --target js.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 -m toolchain.emit.js INPUT.json -o out/output.js
    python3 -m toolchain.emit.js link-output.json -o out/output.js
"""

from __future__ import annotations

import sys

from toolchain.emit import all as _emit_all


def main() -> int:
    argv = sys.argv[1:]
    return _emit_all.main(["--target", "js"] + argv)


if __name__ == "__main__":
    sys.exit(main())
