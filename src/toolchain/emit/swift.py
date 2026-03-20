#!/usr/bin/env python3
"""Standalone Swift backend: EAST3 JSON / link-output.json → Swift source.

Thin wrapper around east2x.py --target swift.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 -m toolchain.emit.swift INPUT.json -o out/output.swift
    python3 -m toolchain.emit.swift link-output.json -o out/output.swift
"""

from __future__ import annotations

import sys

from toolchain.emit import all as _emit_all


def main() -> int:
    argv = sys.argv[1:]
    return _emit_all.main(["--target", "swift"] + argv)


if __name__ == "__main__":
    sys.exit(main())
