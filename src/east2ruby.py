#!/usr/bin/env python3
"""Standalone Ruby backend: EAST3 JSON / link-output.json → Ruby source.

Thin wrapper around east2x.py --target ruby.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 east2ruby.py INPUT.json -o out/output.rb
    python3 east2ruby.py link-output.json -o out/output.rb
"""

from __future__ import annotations

import sys

import east2x


def main() -> int:
    argv = sys.argv[1:]
    return east2x.main(["--target", "ruby"] + argv)


if __name__ == "__main__":
    sys.exit(main())
