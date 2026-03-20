#!/usr/bin/env python3
"""Standalone Lua backend: EAST3 JSON / link-output.json → Lua source.

Thin wrapper around east2x.py --target lua.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 -m toolchain.emit.lua INPUT.json -o out/output.lua
    python3 -m toolchain.emit.lua link-output.json -o out/output.lua
"""

from __future__ import annotations

import sys

from toolchain.emit import all as _emit_all


def main() -> int:
    argv = sys.argv[1:]
    return _emit_all.main(["--target", "lua"] + argv)


if __name__ == "__main__":
    sys.exit(main())
