"""Default EAST3 optimizer pass registrations."""

from __future__ import annotations

from pytra.compiler.east_parts.east3_opt_passes.noop_pass import NoOpPass


def build_default_passes() -> list[object]:
    """v1 骨格の既定 pass 列。"""
    return [NoOpPass()]

