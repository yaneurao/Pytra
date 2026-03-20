"""Default C++ optimizer pass registrations."""

from __future__ import annotations

from toolchain.emit.cpp.optimizer.passes.binop_normalize_pass import CppBinOpNormalizePass
from toolchain.emit.cpp.optimizer.passes.brace_omit_hint_pass import CppBraceOmitHintPass
from toolchain.emit.cpp.optimizer.passes.cast_call_normalize_pass import CppCastCallNormalizePass
from toolchain.emit.cpp.optimizer.passes.compare_normalize_pass import CppCompareNormalizePass
from toolchain.emit.cpp.optimizer.passes.const_condition_pass import CppConstConditionPass
from toolchain.emit.cpp.optimizer.passes.dead_temp_pass import CppDeadTempPass
from toolchain.emit.cpp.optimizer.passes.forcore_direct_unpack_hint_pass import CppForcoreDirectUnpackHintPass
from toolchain.emit.cpp.optimizer.passes.for_iter_mode_hint_pass import CppForIterModeHintPass
from toolchain.emit.cpp.optimizer.passes.noop_cast_pass import CppNoOpCastPass
from toolchain.emit.cpp.optimizer.passes.noop_pass import CppNoOpPass
from toolchain.emit.cpp.optimizer.passes.range_for_shape_pass import CppRangeForShapePass
from toolchain.emit.cpp.optimizer.passes.runtime_fastpath_pass import CppRuntimeFastPathPass


def build_default_cpp_passes() -> list[object]:
    """Default pass sequence for phase-2 rollout."""
    return [
        CppNoOpPass(),
        CppDeadTempPass(),
        CppNoOpCastPass(),
        CppCastCallNormalizePass(),
        CppCompareNormalizePass(),
        CppBinOpNormalizePass(),
        CppConstConditionPass(),
        CppRangeForShapePass(),
        CppForcoreDirectUnpackHintPass(),
        CppForIterModeHintPass(),
        CppBraceOmitHintPass(),
        CppRuntimeFastPathPass(),
    ]
