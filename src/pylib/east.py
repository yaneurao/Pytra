#!/usr/bin/env python3
"""Python source -> EAST converter facade (pylib)."""

from __future__ import annotations

import sys as _bootstrap_sys

_bootstrap_src = __file__.replace("\\", "/").rsplit("/", 2)[0]
if _bootstrap_src not in _bootstrap_sys.path:
    _bootstrap_sys.path.insert(0, _bootstrap_src)

from pylib.pathlib import Path
from pylib import sys

src_root = Path(__file__).resolve().parents[1]
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from common.east_parts import (  # noqa: F401
    BorrowKind,
    EastBuildError,
    FLOAT_TYPES,
    INT_TYPES,
    convert_path,
    convert_source_to_east,
    convert_source_to_east_self_hosted,
    convert_source_to_east_with_backend,
    main,
    render_east_human_cpp,
)

if __name__ == "__main__":
    raise SystemExit(main())
