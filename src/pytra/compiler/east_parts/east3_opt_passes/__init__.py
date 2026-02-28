"""Default EAST3 optimizer pass registrations."""

from __future__ import annotations

from pytra.compiler.east_parts.east3_opt_passes.literal_cast_fold_pass import LiteralCastFoldPass
from pytra.compiler.east_parts.east3_opt_passes.loop_invariant_cast_hoist_pass import LoopInvariantCastHoistPass
from pytra.compiler.east_parts.east3_opt_passes.loop_invariant_hoist_lite_pass import LoopInvariantHoistLitePass
from pytra.compiler.east_parts.east3_opt_passes.numeric_cast_chain_reduction_pass import NumericCastChainReductionPass
from pytra.compiler.east_parts.east3_opt_passes.noop_cast_cleanup_pass import NoOpCastCleanupPass
from pytra.compiler.east_parts.east3_opt_passes.range_for_canonicalization_pass import RangeForCanonicalizationPass
from pytra.compiler.east_parts.east3_opt_passes.strength_reduction_float_loop_pass import StrengthReductionFloatLoopPass
from pytra.compiler.east_parts.east3_opt_passes.typed_enumerate_normalization_pass import TypedEnumerateNormalizationPass
from pytra.compiler.east_parts.east3_opt_passes.typed_repeat_materialization_pass import TypedRepeatMaterializationPass
from pytra.compiler.east_parts.east3_opt_passes.unused_loop_var_elision_pass import UnusedLoopVarElisionPass


def build_default_passes() -> list[object]:
    """`O1` 既定 pass 列。"""
    return [
        NoOpCastCleanupPass(),
        LiteralCastFoldPass(),
        NumericCastChainReductionPass(),
        RangeForCanonicalizationPass(),
        TypedEnumerateNormalizationPass(),
        TypedRepeatMaterializationPass(),
        LoopInvariantCastHoistPass(),
        UnusedLoopVarElisionPass(),
        LoopInvariantHoistLitePass(),
        StrengthReductionFloatLoopPass(),
    ]
