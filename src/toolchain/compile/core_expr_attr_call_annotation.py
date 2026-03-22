#!/usr/bin/env python3
"""Self-hosted EAST expression parser helpers for attr-call annotation clusters."""

from __future__ import annotations

from typing import Any

from toolchain.frontends.signature_registry import lookup_stdlib_method_return_type
from toolchain.compile.core_entrypoints import _make_east_build_error
from toolchain.compile.core_parse_context import _SH_IMPORT_MODULES, _SH_CLASS_BASE
from toolchain.compile.core_runtime_call_semantics import _sh_annotate_runtime_method_call_expr


class _ShExprAttrCallAnnotationMixin:
    def _infer_attr_call_return_type(self, owner: dict[str, Any] | None, attr: str) -> str:
        """属性呼び出しの戻り型を owner type から推定する。"""
        if not isinstance(owner, dict):
            return "unknown"
        owner_t = self._owner_expr_resolved_type(owner)
        if owner_t == "unknown":
            # For import module calls (math.sin etc.), try function return type
            if owner.get("kind") == "Name":
                owner_id = str(owner.get("id", ""))
                if owner_id in _SH_IMPORT_MODULES:
                    from toolchain.frontends.signature_registry import lookup_stdlib_function_return_type
                    fn_ret = lookup_stdlib_function_return_type(attr)
                    if fn_ret != "":
                        return fn_ret
            return "unknown"
        if owner_t == "PyFile" and attr in {"close", "write"}:
            return "None"
        call_ret = self._lookup_method_return(owner_t, attr)
        if call_ret == "unknown":
            call_ret = self._lookup_builtin_method_return(owner_t, attr)
        stdlib_method_ret = lookup_stdlib_method_return_type(owner_t, attr)
        if stdlib_method_ret != "":
            return stdlib_method_ret
        return call_ret

    def _owner_expr_resolved_type(self, owner_expr: dict[str, Any]) -> str:
        """owner expr から resolved_type を取る処理を helper へ寄せる。"""
        owner_t = str(owner_expr.get("resolved_type", "unknown"))
        if str(owner_expr.get("kind", "")) == "Name":
            owner_t = self.name_types.get(str(owner_expr.get("id", "")), owner_t)
        return owner_t

    def _resolve_attr_callee_attr_name(
        self,
        *,
        callee: dict[str, Any],
    ) -> str:
        """Attribute callee の attr 名抽出を helper へ寄せる。"""
        return str(callee.get("attr", ""))

    def _resolve_attr_callee(
        self,
        *,
        callee: dict[str, Any],
        source_span: dict[str, int],
    ) -> tuple[dict[str, Any] | None, str, str]:
        """Attribute callee の owner / type / attr 抽出を helper へ寄せる。"""
        attr = self._resolve_attr_callee_attr_name(callee=callee)
        owner = callee.get("value")
        owner_expr = owner if isinstance(owner, dict) else None
        owner_t = (
            self._resolve_attr_expr_owner_state(
                owner_expr=owner_expr,
                attr_name=attr,
                source_span=source_span,
            )
            if owner_expr is not None
            else "unknown"
        )
        return owner_expr, owner_t, attr

    def _payload_source_span(self, payload: dict[str, Any]) -> dict[str, int]:
        """payload から source_span dict を正規化して取り出す。"""
        source_span = payload.get("source_span")
        return source_span if isinstance(source_span, dict) else {}

    def _resolve_attr_call_annotation_state(
        self,
        *,
        payload: dict[str, Any],
        callee: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, str, str]:
        """Attribute call の source span normalize と callee resolve を helper へ寄せる。"""
        return self._resolve_attr_callee(
            callee=callee,
            source_span=self._payload_source_span(payload),
        )

    def _annotate_attr_call_expr(
        self,
        payload: dict[str, Any],
        *,
        callee: dict[str, Any],
    ) -> dict[str, Any]:
        """Attribute callee の annotation を shared parser helper へ寄せる。"""
        owner_expr, owner_t, attr = self._resolve_attr_call_annotation_state(
            payload=payload,
            callee=callee,
        )
        return self._apply_attr_call_expr_annotation(
            payload=payload,
            owner_expr=owner_expr,
            owner_t=owner_t,
            attr=attr,
        )

    def _resolve_attr_expr_owner_state(
        self,
        *,
        owner_expr: dict[str, Any],
        attr_name: str,
        source_span: dict[str, int],
    ) -> str:
        """Attribute access の owner 型判定と preflight guard を helper へ寄せる。"""
        owner_t = self._owner_expr_resolved_type(owner_expr)
        # import モジュール名は型ではないので forbidden ガード対象外
        owner_kind = str(owner_expr.get("kind", ""))
        if owner_kind == "Name":
            owner_id = str(owner_expr.get("id", ""))
            if owner_id in _SH_IMPORT_MODULES:
                return owner_t
            # クラス名のクラス属性アクセス (e.g. Color.RED) は許可
            if owner_id in _SH_CLASS_BASE:
                return owner_t
        # super() コールは親クラスへの委譲なので forbidden ガード対象外
        if owner_kind == "Call":
            func = owner_expr.get("func")
            if isinstance(func, dict) and str(func.get("id", "")) == "super":
                return owner_t
        if attr_name in {"keys", "items", "values"}:
            self._guard_dynamic_helper_receiver(
                helper_name=attr_name,
                owner_t=owner_t,
                source_span=source_span,
            )
        # "unknown" は name_types 未追跡（モジュールレベル）の場合が多い。
        # Name ノードの unknown は false positive が頻発するため一般 attr guard では許可する。
        # dynamic helper guard (keys/items/values) では上で別途捕捉済み。
        if owner_t.strip() == "unknown":
            return owner_t
        if self._is_forbidden_object_receiver_type(owner_t):
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message="object receiver attribute/method access is forbidden by language constraints",
                source_span=source_span,
                hint="Cast or assign to a concrete type before attribute/method access.",
            )
        return owner_t

    def _apply_runtime_method_call_expr_annotation(
        self,
        *,
        payload: dict[str, Any],
        owner_expr: dict[str, Any] | None,
        owner_t: str,
        attr: str,
    ) -> None:
        """runtime method-call annotation 適用を helper へ寄せる。"""
        _sh_annotate_runtime_method_call_expr(
            payload,
            owner_type=owner_t,
            attr=attr,
            runtime_owner=owner_expr,
        )

    def _apply_attr_call_expr_annotation(
        self,
        *,
        payload: dict[str, Any],
        owner_expr: dict[str, Any] | None,
        owner_t: str,
        attr: str,
    ) -> dict[str, Any]:
        """Attribute callee annotation の適用を helper へ寄せる。"""
        self._apply_runtime_method_call_expr_annotation(
            payload=payload,
            owner_expr=owner_expr,
            owner_t=owner_t,
            attr=attr,
        )
        return payload
