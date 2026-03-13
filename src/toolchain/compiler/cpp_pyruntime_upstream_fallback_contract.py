"""Contract partition for the cpp py_runtime upstream-fallback shrink."""

from __future__ import annotations

from typing import Final


CPP_PYRUNTIME_UPSTREAM_FALLBACK_TASK_ID: Final[str] = (
    "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01"
)
CPP_PYRUNTIME_UPSTREAM_FALLBACK_PLAN_JA: Final[str] = (
    "docs/ja/plans/p2-cpp-pyruntime-upstream-fallback-shrink.md"
)
CPP_PYRUNTIME_UPSTREAM_FALLBACK_PLAN_EN: Final[str] = (
    "docs/en/plans/p2-cpp-pyruntime-upstream-fallback-shrink.md"
)

BOUNDARY_CLASS_ORDER: Final[tuple[str, ...]] = (
    "object_only_compat_header",
    "any_object_boundary_header",
    "typed_lane_must_not_use",
)

OBJECT_ONLY_COMPAT_HEADER_IDS: Final[tuple[str, ...]] = (
    "header_object_bridge_mut_list_cast",
    "header_object_bridge_const_list_cast",
    "header_object_bridge_py_at",
    "header_object_bridge_py_append",
)

ANY_OBJECT_BOUNDARY_HEADER_IDS: Final[tuple[str, ...]] = (
    "header_typed_list_copy_from_object",
    "header_generic_make_object_fallback",
    "header_generic_py_to_object_fallback",
    "header_object_py_to_call_sites",
    "header_dict_key_charptr_object_coercion",
)

TYPED_LANE_MUST_NOT_USE_IDS: Final[tuple[str, ...]] = (
    "cpp_emitter_boxed_list_seed_sites",
    "cpp_emitter_object_list_bridge_sites",
    "generated_runtime_object_list_bridge_sites",
    "generated_runtime_boxed_list_seed_sites",
    "generated_runtime_generic_index_sites",
    "sample_cpp_py_append_sites",
    "sample_cpp_generic_index_sites",
)
