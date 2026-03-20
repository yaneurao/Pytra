#!/usr/bin/env python3
"""Standalone Scala backend: EAST3 JSON / link-output.json → Scala source.

Thin wrapper around east2x.py --target scala.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 -m toolchain.emit.scala INPUT.json -o out/output.scala
    python3 -m toolchain.emit.scala link-output.json -o out/output.scala
"""

from __future__ import annotations

import sys

from toolchain.emit import all as _emit_all


def main() -> int:
    argv = sys.argv[1:]
    return _emit_all.main(["--target", "scala"] + argv)


if __name__ == "__main__":
    sys.exit(main())
