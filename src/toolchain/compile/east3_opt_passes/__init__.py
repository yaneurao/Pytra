"""Default EAST3 optimizer pass registrations."""

from __future__ import annotations

from toolchain.compile.east3_opt_passes.any_annotation_prohibition_pass import AnyAnnotationProhibitionPass
from toolchain.compile.east3_opt_passes.dict_str_key_normalization_pass import DictStrKeyNormalizationPass
from toolchain.compile.east3_opt_passes.cpp_list_value_local_hint_pass import ContainerValueLocalHintPass
from toolchain.compile.east3_opt_passes.empty_init_shorthand_pass import EmptyInitShorthandPass
from toolchain.compile.east3_opt_passes.expression_normalization_pass import ExpressionNormalizationPass
from toolchain.compile.east3_opt_passes.identity_py_to_elision_pass import IdentityPyToElisionPass
from toolchain.compile.east3_opt_passes.lifetime_analysis_pass import LifetimeAnalysisPass
from toolchain.compile.east3_opt_passes.literal_cast_fold_pass import LiteralCastFoldPass
# LoopInvariantCastHoistPass / LoopInvariantHoistLitePass are disabled:
# target language compilers perform the same optimization, and the synthetic
# variable names (__hoisted_cast_N) break source-code correspondence.
from toolchain.compile.east3_opt_passes.numeric_cast_chain_reduction_pass import NumericCastChainReductionPass
from toolchain.compile.east3_opt_passes.noop_cast_cleanup_pass import NoOpCastCleanupPass
from toolchain.compile.east3_opt_passes.range_for_canonicalization_pass import RangeForCanonicalizationPass
from toolchain.compile.east3_opt_passes.safe_reserve_hint_pass import SafeReserveHintPass
from toolchain.compile.east3_opt_passes.strength_reduction_float_loop_pass import StrengthReductionFloatLoopPass
from toolchain.compile.east3_opt_passes.typed_enumerate_normalization_pass import TypedEnumerateNormalizationPass
from toolchain.compile.east3_opt_passes.typed_repeat_materialization_pass import TypedRepeatMaterializationPass
from toolchain.compile.east3_opt_passes.tuple_target_direct_expansion_pass import TupleTargetDirectExpansionPass
from toolchain.compile.east3_opt_passes.unused_loop_var_elision_pass import UnusedLoopVarElisionPass
from toolchain.compile.east3_opt_passes.non_escape_interprocedural_pass import NonEscapeInterproceduralPass


def build_local_only_passes() -> list[object]:
    """`EAST3 local optimizer` の既定 pass 列。"""
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


def build_global_post_link_passes() -> list[object]:
    """`LinkedProgramOptimizer` が担う module rewrite pass 列。"""
    return [
        NonEscapeInterproceduralPass(),
        ContainerValueLocalHintPass(),
    ]


def build_default_passes() -> list[object]:
    """後方互換込みの既定 local pass 列。"""
    return build_local_only_passes()
