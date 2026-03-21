#!/usr/bin/env python3
"""Compatibility shim — delegates to pytra-cli.py.

Canonical entry point is now ``pytra-cli.py`` (or ``./pytra``).
"""

from __future__ import annotations

import sys
import os

if __name__ == "__main__":
    src_dir = os.path.dirname(os.path.abspath(__file__))
    cli_path = os.path.join(src_dir, "pytra-cli.py")
    os.execv(sys.executable, [sys.executable, cli_path] + sys.argv[1:])
