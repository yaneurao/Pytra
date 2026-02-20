"""pytra.std.time_impl: native hook declarations.

このモジュールは C++ 側 `time-impl` に委譲される関数シグネチャのみを持つ。
"""

from __future__ import annotations


def perf_counter() -> float:
    # C++ では hand-written time-impl 側で実装される。
    return 0.0

