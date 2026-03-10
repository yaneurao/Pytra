#!/usr/bin/env python3
"""Self-hosted EAST expression annotation helpers for attr/subscript parsing."""

from __future__ import annotations

from typing import Any


class _ShExprAttrSubscriptAnnotationMixin:
    def _apply_attr_expr_annotation(
        self,
        *,
        node: dict[str, Any],
        owner_expr: dict[str, Any],
        attr_name: str,
        attr_runtime_call: str,
        attr_semantic_tag: str,
        attr_module_id: str,
        attr_runtime_symbol: str,
        noncpp_module_attr_runtime_call: str,
        noncpp_module_id: str,
    ) -> dict[str, Any]:
        """Attribute access node への annotation 適用を helper へ寄せる。"""
        self._apply_runtime_attr_expr_annotation(
            node=node,
            owner_expr=owner_expr,
            attr_runtime_call=attr_runtime_call,
            attr_semantic_tag=attr_semantic_tag,
            attr_module_id=attr_module_id,
            attr_runtime_symbol=attr_runtime_symbol,
        )
        self._apply_noncpp_attr_expr_annotation(
            node=node,
            attr_name=attr_name,
            noncpp_module_attr_runtime_call=noncpp_module_attr_runtime_call,
            noncpp_module_id=noncpp_module_id,
        )
        return node

    def _annotate_attr_expr(
        self,
        *,
        owner_expr: dict[str, Any],
        attr_name: str,
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """Attribute access node の生成と annotation を parser helper へ寄せる。"""
        (
            resolved_type,
            attr_runtime_call,
            attr_semantic_tag,
            attr_module_id,
            attr_runtime_symbol,
            noncpp_module_attr_runtime_call,
            noncpp_module_id,
        ) = self._resolve_attr_expr_annotation_state(
            owner_expr=owner_expr,
            attr_name=attr_name,
            source_span=source_span,
        )
        node = self._build_attr_expr_payload(
            source_span=source_span,
            owner_expr=owner_expr,
            attr_name=attr_name,
            resolved_type=resolved_type,
            repr_text=repr_text,
        )
        return self._apply_attr_expr_annotation(
            node=node,
            owner_expr=owner_expr,
            attr_name=attr_name,
            attr_runtime_call=attr_runtime_call,
            attr_semantic_tag=attr_semantic_tag,
            attr_module_id=attr_module_id,
            attr_runtime_symbol=attr_runtime_symbol,
            noncpp_module_attr_runtime_call=noncpp_module_attr_runtime_call,
            noncpp_module_id=noncpp_module_id,
        )

    def _resolve_attr_expr_annotation(
        self,
        *,
        attr_meta: dict[str, Any],
    ) -> tuple[str, str, str, str, str, str, str]:
        """Attribute access metadata dict の field unpack を helper へ寄せる。"""
        resolved_type = str(attr_meta.get("resolved_type", "unknown"))
        attr_runtime_call = str(attr_meta.get("runtime_call", ""))
        attr_semantic_tag = str(attr_meta.get("semantic_tag", ""))
        attr_module_id = str(attr_meta.get("module_id", ""))
        attr_runtime_symbol = str(attr_meta.get("runtime_symbol", ""))
        noncpp_module_attr_runtime_call = str(attr_meta.get("noncpp_runtime_call", ""))
        noncpp_module_id = str(attr_meta.get("noncpp_module_id", ""))
        return (
            resolved_type,
            attr_runtime_call,
            attr_semantic_tag,
            attr_module_id,
            attr_runtime_symbol,
            noncpp_module_attr_runtime_call,
            noncpp_module_id,
        )

    def _resolve_attr_expr_metadata(
        self,
        *,
        owner_expr: dict[str, Any],
        owner_t: str,
        attr_name: str,
    ) -> tuple[str, str, str, str, str, str, str]:
        """Attribute access metadata の lookup と unpack を helper へ寄せる。"""
        attr_meta = self._lookup_attr_expr_metadata(owner_expr, owner_t, attr_name)
        return self._resolve_attr_expr_annotation(
            attr_meta=attr_meta,
        )

    def _resolve_attr_expr_annotation_state(
        self,
        *,
        owner_expr: dict[str, Any],
        attr_name: str,
        source_span: dict[str, int],
    ) -> tuple[str, str, str, str, str, str, str]:
        """Attribute access の owner-state と metadata resolve を helper へ寄せる。"""
        owner_t = self._resolve_attr_expr_owner_state(
            owner_expr=owner_expr,
            attr_name=attr_name,
            source_span=source_span,
        )
        (
            resolved_type,
            attr_runtime_call,
            attr_semantic_tag,
            attr_module_id,
            attr_runtime_symbol,
            noncpp_module_attr_runtime_call,
            noncpp_module_id,
        ) = self._resolve_attr_expr_metadata(
            owner_expr=owner_expr,
            owner_t=owner_t,
            attr_name=attr_name,
        )
        return (
            resolved_type,
            attr_runtime_call,
            attr_semantic_tag,
            attr_module_id,
            attr_runtime_symbol,
            noncpp_module_attr_runtime_call,
            noncpp_module_id,
        )

    def _resolve_subscript_expr_annotation_state(
        self,
        *,
        owner_expr: dict[str, Any],
    ) -> str:
        """Subscript / slice の owner-type resolve を helper へ寄せる。"""
        return self._owner_expr_resolved_type(owner_expr)

    def _resolve_subscript_expr_build_kind(
        self,
        *,
        index_expr: dict[str, Any] | None,
        lower: dict[str, Any] | None,
        upper: dict[str, Any] | None,
    ) -> str:
        """Subscript / Slice の build 分岐を helper へ寄せる。"""
        if index_expr is None or lower is not None or upper is not None:
            return "slice"
        return "index"

    def _resolve_subscript_expr_apply_state(
        self,
        *,
        owner_expr: dict[str, Any],
        index_expr: dict[str, Any] | None,
        lower: dict[str, Any] | None,
        upper: dict[str, Any] | None,
    ) -> tuple[str, str]:
        """Subscript / Slice の annotation-state resolve を helper へ寄せる。"""
        owner_t = self._resolve_subscript_expr_annotation_state(
            owner_expr=owner_expr,
        )
        build_kind = self._resolve_subscript_expr_build_kind(
            index_expr=index_expr,
            lower=lower,
            upper=upper,
        )
        return owner_t, build_kind

    def _apply_slice_subscript_expr_build(
        self,
        *,
        owner_expr: dict[str, Any],
        owner_t: str,
        lower: dict[str, Any] | None,
        upper: dict[str, Any] | None,
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """slice subscript build apply を helper へ寄せる。"""
        return self._build_slice_subscript_expr(
            owner_expr=owner_expr,
            owner_t=owner_t,
            lower=lower,
            upper=upper,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _apply_index_subscript_expr_build(
        self,
        *,
        owner_expr: dict[str, Any],
        owner_t: str,
        index_expr: dict[str, Any] | None,
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """index subscript build apply を helper へ寄せる。"""
        assert index_expr is not None
        return self._build_index_subscript_expr(
            owner_expr=owner_expr,
            owner_t=owner_t,
            index_expr=index_expr,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _apply_subscript_expr_build(
        self,
        *,
        build_kind: str,
        owner_expr: dict[str, Any],
        owner_t: str,
        index_expr: dict[str, Any] | None,
        lower: dict[str, Any] | None,
        upper: dict[str, Any] | None,
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """Subscript / Slice の build dispatch を helper へ寄せる。"""
        if build_kind == "slice":
            return self._apply_slice_subscript_expr_build(
                owner_expr=owner_expr,
                owner_t=owner_t,
                lower=lower,
                upper=upper,
                source_span=source_span,
                repr_text=repr_text,
            )
        return self._apply_index_subscript_expr_build(
            owner_expr=owner_expr,
            owner_t=owner_t,
            index_expr=index_expr,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _annotate_subscript_expr(
        self,
        *,
        owner_expr: dict[str, Any],
        index_expr: dict[str, Any] | None = None,
        lower: dict[str, Any] | None = None,
        upper: dict[str, Any] | None = None,
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """Subscript / slice node の構築を parser helper へ寄せる。"""
        owner_t, build_kind = self._resolve_subscript_expr_apply_state(
            owner_expr=owner_expr,
            index_expr=index_expr,
            lower=lower,
            upper=upper,
        )
        return self._apply_subscript_expr_build(
            build_kind=build_kind,
            owner_expr=owner_expr,
            owner_t=owner_t,
            index_expr=index_expr,
            lower=lower,
            upper=upper,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _subscript_result_type(self, container_type: str) -> str:
        """添字アクセスの結果型をコンテナ型から推論する。"""
        if container_type.startswith("list[") and container_type.endswith("]"):
            inner = container_type[5:-1].strip()
            return inner if inner != "" else "unknown"
        if container_type.startswith("dict[") and container_type.endswith("]"):
            inner = self._split_generic_types(container_type[5:-1].strip())
            if len(inner) == 2 and inner[1] != "":
                return inner[1]
            return "unknown"
        if container_type == "str":
            return "str"
        if container_type in {"bytes", "bytearray"}:
            return "uint8"
        return "unknown"
