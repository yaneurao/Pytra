"""Default C++ optimizer pass registrations."""

from __future__ import annotations

from hooks.cpp.optimizer.passes.const_condition_pass import CppConstConditionPass
from hooks.cpp.optimizer.passes.dead_temp_pass import CppDeadTempPass
from hooks.cpp.optimizer.passes.noop_cast_pass import CppNoOpCastPass
from hooks.cpp.optimizer.passes.noop_pass import CppNoOpPass
from hooks.cpp.optimizer.passes.range_for_shape_pass import CppRangeForShapePass
from hooks.cpp.optimizer.passes.runtime_fastpath_pass import CppRuntimeFastPathPass


def build_default_cpp_passes() -> list[object]:
    """Default pass sequence for phase-2 rollout."""
    return [
        CppNoOpPass(),
        CppDeadTempPass(),
        CppNoOpCastPass(),
        CppConstConditionPass(),
        CppRangeForShapePass(),
        CppRuntimeFastPathPass(),
    ]
