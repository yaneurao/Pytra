"""Machine-readable baseline inventory for the cpp py_runtime upstream-fallback shrink."""

from __future__ import annotations

from typing import Final, TypedDict


CPP_PYRUNTIME_UPSTREAM_FALLBACK_TODO_ID: Final[str] = (
    "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01"
)
CPP_PYRUNTIME_UPSTREAM_FALLBACK_PLAN_JA: Final[str] = (
    "docs/ja/plans/p2-cpp-pyruntime-upstream-fallback-shrink.md"
)
CPP_PYRUNTIME_UPSTREAM_FALLBACK_PLAN_EN: Final[str] = (
    "docs/en/plans/p2-cpp-pyruntime-upstream-fallback-shrink.md"
)

HEADER_LINE_BASELINE: Final[int] = 1295

INVENTORY_BUCKET_ORDER: Final[tuple[str, ...]] = (
    "header_bulk",
    "cpp_emitter_residual",
    "generated_runtime_residual",
    "sample_cpp_residual",
)

MATCHER_KIND_ORDER: Final[tuple[str, ...]] = ("literal", "regex")

SHRINK_STAGE_ORDER: Final[tuple[str, ...]] = (
    "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S1-01",
    "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-01",
    "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-02",
    "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-03",
    "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S3-01",
)


class UpstreamFallbackEvidenceRef(TypedDict):
    relpath: str
    needle: str


class UpstreamFallbackInventoryEntry(TypedDict):
    inventory_id: str
    bucket: str
    scope_rel: str
    matcher_kind: str
    needle: str
    expected_count: int
    shrink_stage: str
    evidence_refs: tuple[UpstreamFallbackEvidenceRef, ...]
    notes: str


CPP_PYRUNTIME_UPSTREAM_FALLBACK_INVENTORY_V1: Final[
    tuple[UpstreamFallbackInventoryEntry, ...]
] = (
    {
        "inventory_id": "header_object_bridge_mut_list_cast",
        "bucket": "header_bulk",
        "scope_rel": "src/runtime/cpp/core/py_runtime.h",
        "matcher_kind": "literal",
        "needle": (
            'static inline list<object>& obj_to_list_ref_or_raise(object& v, const char* ctx = "obj_to_list_ref_or_raise") {'
        ),
        "expected_count": 1,
        "shrink_stage": "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-01",
        "evidence_refs": (
            {
                "relpath": "src/runtime/cpp/core/py_runtime.h",
                "needle": 'static inline list<object>& obj_to_list_ref_or_raise(object& v, const char* ctx = "obj_to_list_ref_or_raise") {',
            },
        ),
        "notes": "Mutable object-to-list bridge still lives in the header until typed callers move upstream.",
    },
    {
        "inventory_id": "header_object_bridge_const_list_cast",
        "bucket": "header_bulk",
        "scope_rel": "src/runtime/cpp/core/py_runtime.h",
        "matcher_kind": "literal",
        "needle": (
            'static inline const list<object>& obj_to_list_ref_or_raise(const object& v, const char* ctx = "obj_to_list_ref_or_raise") {'
        ),
        "expected_count": 1,
        "shrink_stage": "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-02",
        "evidence_refs": (
            {
                "relpath": "src/runtime/cpp/core/py_runtime.h",
                "needle": 'static inline const list<object>& obj_to_list_ref_or_raise(const object& v, const char* ctx = "obj_to_list_ref_or_raise") {',
            },
        ),
        "notes": "Const object-to-list bridge remains because generated runtime artifacts still consume it.",
    },
    {
        "inventory_id": "header_object_bridge_py_at",
        "bucket": "header_bulk",
        "scope_rel": "src/runtime/cpp/core/py_runtime.h",
        "matcher_kind": "literal",
        "needle": "static inline object py_at(const object& v, int64 idx) {",
        "expected_count": 1,
        "shrink_stage": "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-01",
        "evidence_refs": (
            {
                "relpath": "src/runtime/cpp/core/py_runtime.h",
                "needle": "static inline object py_at(const object& v, int64 idx) {",
            },
        ),
        "notes": "Object-only index bridge is still present in the header surface.",
    },
    {
        "inventory_id": "header_object_bridge_py_append",
        "bucket": "header_bulk",
        "scope_rel": "src/runtime/cpp/core/py_runtime.h",
        "matcher_kind": "literal",
        "needle": "static inline void py_append(object& v, const U& item) {",
        "expected_count": 1,
        "shrink_stage": "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-02",
        "evidence_refs": (
            {
                "relpath": "src/runtime/cpp/core/py_runtime.h",
                "needle": "static inline void py_append(object& v, const U& item) {",
            },
        ),
        "notes": "The only remaining py_append surface in the header is the object bridge.",
    },
    {
        "inventory_id": "header_typed_list_copy_from_object",
        "bucket": "header_bulk",
        "scope_rel": "src/runtime/cpp/core/py_runtime.h",
        "matcher_kind": "literal",
        "needle": "static inline list<T> py_copy_typed_list_from_object(const object& value, const char* ctx) {",
        "expected_count": 1,
        "shrink_stage": "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-03",
        "evidence_refs": (
            {
                "relpath": "src/runtime/cpp/core/py_runtime.h",
                "needle": "static inline list<T> py_copy_typed_list_from_object(const object& value, const char* ctx) {",
            },
        ),
        "notes": "Typed list reconstruction from object stays as the main object-to-typed fallback block.",
    },
    {
        "inventory_id": "header_generic_make_object_fallback",
        "bucket": "header_bulk",
        "scope_rel": "src/runtime/cpp/core/py_runtime.h",
        "matcher_kind": "literal",
        "needle": "static inline object make_object(const T& v) {",
        "expected_count": 1,
        "shrink_stage": "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-03",
        "evidence_refs": (
            {
                "relpath": "src/runtime/cpp/core/py_runtime.h",
                "needle": "static inline object make_object(const T& v) {",
            },
        ),
        "notes": "Generic boxing fallback still exists for Any/object boundaries and needs typed-path callers reduced first.",
    },
    {
        "inventory_id": "header_generic_py_to_object_fallback",
        "bucket": "header_bulk",
        "scope_rel": "src/runtime/cpp/core/py_runtime.h",
        "matcher_kind": "literal",
        "needle": "static inline T py_to(const object& v) {",
        "expected_count": 1,
        "shrink_stage": "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-03",
        "evidence_refs": (
            {
                "relpath": "src/runtime/cpp/core/py_runtime.h",
                "needle": "static inline T py_to(const object& v) {",
            },
        ),
        "notes": "Generic unboxing fallback remains the main upstream target for typed-path shrink.",
    },
    {
        "inventory_id": "header_object_py_to_call_sites",
        "bucket": "header_bulk",
        "scope_rel": "src/runtime/cpp/core/py_runtime.h",
        "matcher_kind": "regex",
        "needle": r"py_to<[^>]+>\([^\n]*object",
        "expected_count": 1,
        "shrink_stage": "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-03",
        "evidence_refs": (
            {
                "relpath": "src/runtime/cpp/core/py_runtime.h",
                "needle": 'static_assert(!::std::is_same_v<T, T>, "py_to<T>(object): unsupported target type");',
            },
        ),
        "notes": "After retiring the char* reboxing helpers, only the generic unsupported-target guard still matches the object py_to regex inside the header.",
    },
    {
        "inventory_id": "cpp_emitter_object_list_bridge_sites",
        "bucket": "cpp_emitter_residual",
        "scope_rel": "src/toolchain/emit/cpp/emitter",
        "matcher_kind": "literal",
        "needle": "obj_to_list_ref_or_raise(",
        "expected_count": 1,
        "shrink_stage": "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-01",
        "evidence_refs": (
            {
                "relpath": "src/toolchain/emit/cpp/emitter/call.py",
                "needle": 'return f\'obj_to_list_ref_or_raise({owner_expr}, "{ctx}")\'',
            },
        ),
        "notes": "Emitter now centralizes object-list bridge rendering in the helper definition only.",
    },
)


def iter_cpp_pyruntime_upstream_fallback_inventory() -> tuple[UpstreamFallbackInventoryEntry, ...]:
    return CPP_PYRUNTIME_UPSTREAM_FALLBACK_INVENTORY_V1
