#!/usr/bin/env python3
"""Compatibility shim — delegates to toolchain.emit.all.

Canonical entry point is now ``toolchain.emit.all`` (or per-language
``toolchain.emit.cpp``, ``toolchain.emit.rs``, etc.).
"""

from __future__ import annotations

import sys

from toolchain.emit.all import main

if __name__ == "__main__":
    sys.exit(main())
