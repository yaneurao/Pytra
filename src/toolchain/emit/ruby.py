#!/usr/bin/env python3
"""Standalone Ruby backend: EAST3 JSON / link-output.json → Ruby source.

Thin wrapper around east2x.py --target ruby.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 -m toolchain.emit.ruby INPUT.json -o out/output.rb
    python3 -m toolchain.emit.ruby link-output.json -o out/output.rb
"""

from __future__ import annotations

import sys

from toolchain.emit import all as _emit_all


def main() -> int:
    argv = sys.argv[1:]
    return _emit_all.main(["--target", "ruby"] + argv)


if __name__ == "__main__":
    sys.exit(main())
