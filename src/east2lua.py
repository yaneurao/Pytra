#!/usr/bin/env python3
"""Standalone Lua backend: EAST3 JSON / link-output.json → Lua source.

Thin wrapper around east2x.py --target lua.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 east2lua.py INPUT.json -o out/output.lua
    python3 east2lua.py link-output.json -o out/output.lua
"""

from __future__ import annotations

import sys

import east2x


def main() -> int:
    argv = sys.argv[1:]
    return east2x.main(["--target", "lua"] + argv)


if __name__ == "__main__":
    sys.exit(main())
