"""Default C++ optimizer pass registrations."""

from __future__ import annotations

from backends.cpp.optimizer.passes.brace_omit_hint_pass import CppBraceOmitHintPass
from backends.cpp.optimizer.passes.cast_call_normalize_pass import CppCastCallNormalizePass
from backends.cpp.optimizer.passes.compare_normalize_pass import CppCompareNormalizePass
from backends.cpp.optimizer.passes.const_condition_pass import CppConstConditionPass
from backends.cpp.optimizer.passes.dead_temp_pass import CppDeadTempPass
from backends.cpp.optimizer.passes.for_iter_mode_hint_pass import CppForIterModeHintPass
from backends.cpp.optimizer.passes.noop_cast_pass import CppNoOpCastPass
from backends.cpp.optimizer.passes.noop_pass import CppNoOpPass
from backends.cpp.optimizer.passes.range_for_shape_pass import CppRangeForShapePass
from backends.cpp.optimizer.passes.runtime_fastpath_pass import CppRuntimeFastPathPass


def build_default_cpp_passes() -> list[object]:
    """Default pass sequence for phase-2 rollout."""
    return [
        CppNoOpPass(),
        CppDeadTempPass(),
        CppNoOpCastPass(),
        CppCastCallNormalizePass(),
        CppCompareNormalizePass(),
        CppConstConditionPass(),
        CppRangeForShapePass(),
        CppForIterModeHintPass(),
        CppBraceOmitHintPass(),
        CppRuntimeFastPathPass(),
    ]
