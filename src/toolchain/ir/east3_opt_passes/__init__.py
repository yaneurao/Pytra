"""Default EAST3 optimizer pass registrations."""

from __future__ import annotations

from toolchain.ir.east3_opt_passes.dict_str_key_normalization_pass import DictStrKeyNormalizationPass
from toolchain.ir.east3_opt_passes.cpp_list_value_local_hint_pass import CppListValueLocalHintPass
from toolchain.ir.east3_opt_passes.empty_init_shorthand_pass import EmptyInitShorthandPass
from toolchain.ir.east3_opt_passes.expression_normalization_pass import ExpressionNormalizationPass
from toolchain.ir.east3_opt_passes.identity_py_to_elision_pass import IdentityPyToElisionPass
from toolchain.ir.east3_opt_passes.lifetime_analysis_pass import LifetimeAnalysisPass
from toolchain.ir.east3_opt_passes.literal_cast_fold_pass import LiteralCastFoldPass
from toolchain.ir.east3_opt_passes.loop_invariant_cast_hoist_pass import LoopInvariantCastHoistPass
from toolchain.ir.east3_opt_passes.loop_invariant_hoist_lite_pass import LoopInvariantHoistLitePass
from toolchain.ir.east3_opt_passes.numeric_cast_chain_reduction_pass import NumericCastChainReductionPass
from toolchain.ir.east3_opt_passes.noop_cast_cleanup_pass import NoOpCastCleanupPass
from toolchain.ir.east3_opt_passes.non_escape_interprocedural_pass import NonEscapeInterproceduralPass
from toolchain.ir.east3_opt_passes.range_for_canonicalization_pass import RangeForCanonicalizationPass
from toolchain.ir.east3_opt_passes.safe_reserve_hint_pass import SafeReserveHintPass
from toolchain.ir.east3_opt_passes.strength_reduction_float_loop_pass import StrengthReductionFloatLoopPass
from toolchain.ir.east3_opt_passes.typed_enumerate_normalization_pass import TypedEnumerateNormalizationPass
from toolchain.ir.east3_opt_passes.typed_repeat_materialization_pass import TypedRepeatMaterializationPass
from toolchain.ir.east3_opt_passes.tuple_target_direct_expansion_pass import TupleTargetDirectExpansionPass
from toolchain.ir.east3_opt_passes.unused_loop_var_elision_pass import UnusedLoopVarElisionPass


def build_default_passes() -> list[object]:
    """`O1` 既定 pass 列。"""
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
        NonEscapeInterproceduralPass(),
        CppListValueLocalHintPass(),
        LifetimeAnalysisPass(),
        LoopInvariantCastHoistPass(),
        UnusedLoopVarElisionPass(),
        LoopInvariantHoistLitePass(),
        StrengthReductionFloatLoopPass(),
    ]
