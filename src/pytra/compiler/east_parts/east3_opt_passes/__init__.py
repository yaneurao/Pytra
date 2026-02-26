"""Default EAST3 optimizer pass registrations."""

from __future__ import annotations

from pytra.compiler.east_parts.east3_opt_passes.literal_cast_fold_pass import LiteralCastFoldPass
from pytra.compiler.east_parts.east3_opt_passes.noop_cast_cleanup_pass import NoOpCastCleanupPass


def build_default_passes() -> list[object]:
    """`O1` 既定 pass 列。"""
    return [
        NoOpCastCleanupPass(),
        LiteralCastFoldPass(),
    ]
