"""Default C++ optimizer pass registrations."""

from __future__ import annotations

from hooks.cpp.optimizer.passes.noop_pass import CppNoOpPass


def build_default_cpp_passes() -> list[object]:
    """Phase-1 default pass sequence."""
    return [CppNoOpPass()]

