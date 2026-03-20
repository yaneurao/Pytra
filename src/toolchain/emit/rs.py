#!/usr/bin/env python3
"""Standalone Rust backend: EAST3 JSON / link-output.json → Rust source.

Thin wrapper around east2x.py --target rs.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 -m toolchain.emit.rs INPUT.json -o out/output.rs
    python3 -m toolchain.emit.rs link-output.json -o out/output.rs
"""

from __future__ import annotations

import sys

from toolchain.emit import all as _emit_all


def main() -> int:
    argv = sys.argv[1:]
    return _emit_all.main(["--target", "rs"] + argv)


if __name__ == "__main__":
    sys.exit(main())
