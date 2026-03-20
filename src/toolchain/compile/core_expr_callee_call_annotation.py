#!/usr/bin/env python3
"""Self-hosted EAST expression parser helpers for callee-call annotation clusters."""

from __future__ import annotations

from typing import Any

from toolchain.frontends.signature_registry import lookup_stdlib_method_return_type


class _ShExprCalleeCallAnnotationMixin:
    def _infer_attr_call_return_type(self, owner: dict[str, Any] | None, attr: str) -> str:
        """属性呼び出しの戻り型を owner type から推定する。"""
        if not isinstance(owner, dict):
            return "unknown"
        owner_t = self._owner_expr_resolved_type(owner)
        if owner_t == "unknown":
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

    def _infer_call_expr_return_type(
        self,
        callee: dict[str, Any] | None,
        args: list[dict[str, Any]],
    ) -> tuple[str, str]:
        """呼び出し式の戻り型と name-callee 名を推定する。"""
        if not isinstance(callee, dict):
            return "unknown", ""
        kind = str(callee.get("kind", ""))
        fn_name = ""
        if kind == "Name":
            fn_name = str(callee.get("id", ""))
            return self._infer_named_call_return_type(fn_name=fn_name, args=args), fn_name
        if kind == "Attribute":
            owner = callee.get("value")
            attr = str(callee.get("attr", ""))
            return self._infer_attr_call_return_type(
                owner if isinstance(owner, dict) else None,
                attr,
            ), fn_name
        if kind == "Lambda":
            return str(callee.get("return_type", "unknown")), fn_name
        return "unknown", fn_name

    def _apply_named_callee_call_annotation(
        self,
        payload: dict[str, Any],
        *,
        fn_name: str,
        args: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """named callee-call apply を helper へ寄せる。"""
        return self._annotate_named_call_expr(
            payload,
            fn_name=fn_name,
            args=args,
        )

    def _apply_attr_callee_call_annotation(
        self,
        payload: dict[str, Any],
        *,
        callee: dict[str, Any],
    ) -> dict[str, Any]:
        """attr callee-call apply を helper へ寄せる。"""
        return self._annotate_attr_call_expr(
            payload,
            callee=callee,
        )

    def _apply_callee_call_annotation(
        self,
        payload: dict[str, Any],
        *,
        callee: dict[str, Any],
        fn_name: str,
        args: list[dict[str, Any]],
        callee_kind: str,
    ) -> dict[str, Any]:
        """callee kind ごとの call annotation 適用を helper へ寄せる。"""
        if callee_kind == "named":
            return self._apply_named_callee_call_annotation(
                payload,
                fn_name=fn_name,
                args=args,
            )
        if callee_kind == "attr":
            return self._apply_attr_callee_call_annotation(
                payload,
                callee=callee,
            )
        return payload

    def _resolve_callee_call_annotation_kind(
        self,
        *,
        callee: dict[str, Any],
        fn_name: str,
    ) -> str:
        """callee kind ごとの call annotation 分類を helper へ寄せる。"""
        if fn_name != "":
            return "named"
        if callee.get("kind") == "Attribute":
            return "attr"
        return ""

    def _resolve_callee_call_annotation_state(
        self,
        *,
        callee: dict[str, Any],
        fn_name: str,
    ) -> str:
        """callee-call の kind resolve を annotation-state helper へ寄せる。"""
        return self._resolve_callee_call_annotation_kind(
            callee=callee,
            fn_name=fn_name,
        )

    def _annotate_callee_call_expr(
        self,
        payload: dict[str, Any],
        *,
        callee: dict[str, Any],
        fn_name: str,
        args: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """callee kind ごとの call annotation dispatch を helper へ寄せる。"""
        callee_kind = self._resolve_callee_call_annotation_state(
            callee=callee,
            fn_name=fn_name,
        )
        return self._apply_callee_call_annotation(
            payload,
            callee=callee,
            fn_name=fn_name,
            args=args,
            callee_kind=callee_kind,
        )
