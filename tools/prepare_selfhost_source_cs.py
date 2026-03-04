#!/usr/bin/env python3
"""Prepare C# selfhost seed source from unified `py2x.py`.

This utility keeps the historical command name for compatibility, but the
source of truth is now `src/py2x.py`.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_PY2X = ROOT / "src" / "py2x.py"
DST_SELFHOST = ROOT / "selfhost" / "py2x_cs.py"


def main() -> int:
    if not SRC_PY2X.exists():
        raise RuntimeError("missing source: src/py2x.py")
    DST_SELFHOST.parent.mkdir(parents=True, exist_ok=True)
    DST_SELFHOST.write_text(SRC_PY2X.read_text(encoding="utf-8"), encoding="utf-8")
    print("[OK] wrote " + str(DST_SELFHOST.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
