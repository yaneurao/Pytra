#!/usr/bin/env python3
"""Canonical runtime parity check entry point.

The implementation lives in ``runtime_parity_check_fast.py``.  This module
keeps the long-standing command name and re-exports shared helper APIs used by
tooling such as selfhost parity.
"""

from __future__ import annotations

import sys
from pathlib import Path

CHECK_DIR = Path(__file__).resolve().parent
if str(CHECK_DIR) not in sys.path:
    sys.path.insert(0, str(CHECK_DIR))

from runtime_parity_shared import *  # noqa: F401,F403


def main() -> int:
    from runtime_parity_check_fast import main as fast_main  # type: ignore

    return fast_main()


if __name__ == "__main__":
    raise SystemExit(main())
