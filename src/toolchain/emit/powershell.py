#!/usr/bin/env python3
"""Standalone PowerShell backend: EAST3 JSON / link-output.json → PowerShell source.

Thin wrapper around east2x.py --target powershell.
For C++ use east2cpp.py instead (multi-file, import-isolated).

Usage:
    python3 -m toolchain.emit.powershell INPUT.json -o out/output.ps1
    python3 -m toolchain.emit.powershell link-output.json -o out/output.ps1
"""

from __future__ import annotations

import sys

from toolchain.emit import all as _emit_all


def main() -> int:
    argv = sys.argv[1:]
    return _emit_all.main(["--target", "powershell"] + argv)


if __name__ == "__main__":
    sys.exit(main())
