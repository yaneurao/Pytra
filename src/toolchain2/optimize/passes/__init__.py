"""Default EAST3 optimizer pass registrations for toolchain2."""

from __future__ import annotations

from toolchain2.optimize.passes.noop_cast_cleanup import NoOpCastCleanupPass
from toolchain2.optimize.passes.literal_cast_fold import LiteralCastFoldPass
from toolchain2.optimize.passes.identity_py_to_elision import IdentityPyToElisionPass
from toolchain2.optimize.passes.numeric_cast_chain_reduction import NumericCastChainReductionPass
from toolchain2.optimize.passes.range_for_canonicalization import RangeForCanonicalizationPass
from toolchain2.optimize.passes.expression_normalization import ExpressionNormalizationPass
from toolchain2.optimize.passes.empty_init_shorthand import EmptyInitShorthandPass
from toolchain2.optimize.passes.safe_reserve_hint import SafeReserveHintPass
from toolchain2.optimize.passes.typed_enumerate_normalization import TypedEnumerateNormalizationPass
from toolchain2.optimize.passes.typed_repeat_materialization import TypedRepeatMaterializationPass
from toolchain2.optimize.passes.dict_str_key_normalization import DictStrKeyNormalizationPass
from toolchain2.optimize.passes.tuple_target_direct_expansion import TupleTargetDirectExpansionPass
from toolchain2.optimize.passes.lifetime_analysis import LifetimeAnalysisPass
from toolchain2.optimize.passes.unused_loop_var_elision import UnusedLoopVarElisionPass
from toolchain2.optimize.passes.strength_reduction_float_loop import StrengthReductionFloatLoopPass

from toolchain2.optimize.optimizer import East3OptimizerPass


def build_local_only_passes() -> list[East3OptimizerPass]:
    """Default local optimizer pass list."""
    return [
        NoOpCastCleanupPass(),
        LiteralCastFoldPass(),
        IdentityPyToElisionPass(),
        NumericCastChainReductionPass(),
        RangeForCanonicalizationPass(),
        ExpressionNormalizationPass(),
        EmptyInitShorthandPass(),
        SafeReserveHintPass(),
        TypedEnumerateNormalizationPass(),
        TypedRepeatMaterializationPass(),
        DictStrKeyNormalizationPass(),
        TupleTargetDirectExpansionPass(),
        LifetimeAnalysisPass(),
        UnusedLoopVarElisionPass(),
        StrengthReductionFloatLoopPass(),
    ]


def build_default_passes() -> list[East3OptimizerPass]:
    """Backward-compatible default local pass list."""
    return build_local_only_passes()
