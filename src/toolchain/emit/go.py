#!/usr/bin/env python3
"""Go backend: DEPRECATED — redirects to toolchain2 Go emitter.

Use `pytra-cli.py build --target go` or `pytra-cli2 -build --target=go` instead.
"""

from __future__ import annotations
import sys


def main() -> int:
    print("Go backend has been migrated to toolchain2.", file=sys.stderr)
    print("Use: pytra-cli.py build INPUT.py --target go --run", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
