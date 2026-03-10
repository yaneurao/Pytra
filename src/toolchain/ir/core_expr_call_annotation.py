#!/usr/bin/env python3
"""Self-hosted EAST expression parser helpers for call/callee annotation orchestration."""

from __future__ import annotations

from typing import Any
from toolchain.frontends.signature_registry import lookup_stdlib_method_return_type


class _ShExprCallAnnotationMixin:
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

    def _resolve_call_expr_annotation_state(
        self,
        *,
        callee: dict[str, Any],
        args: list[dict[str, Any]],
        source_span: dict[str, int],
    ) -> tuple[str, str]:
        """call annotation 前段の return-type 推論と guard を helper へ寄せる。"""
        call_ret, fn_name = self._infer_call_expr_return_type(callee, args)
        self._guard_named_call_args(
            fn_name=fn_name,
            args=args,
            source_span=source_span,
        )
        return call_ret, fn_name

    def _apply_call_expr_annotation(
        self,
        *,
        callee: dict[str, Any],
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        source_span: dict[str, int],
        repr_text: str,
        call_ret: str,
        fn_name: str,
    ) -> dict[str, Any]:
        """Call expr annotation 適用を helper へ寄せる。"""
        payload = self._build_call_expr_payload(
            callee=callee,
            args=args,
            keywords=keywords,
            source_span=source_span,
            repr_text=repr_text,
            call_ret=call_ret,
        )
        return self._annotate_callee_call_expr(
            payload,
            callee=callee,
            fn_name=fn_name,
            args=args,
        )

    def _annotate_call_expr(
        self,
        *,
        callee: dict[str, Any],
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """Call expr の payload 構築と annotation を parser helper へ寄せる。"""
        call_ret, fn_name = self._resolve_call_expr_annotation_state(
            callee=callee,
            args=args,
            source_span=source_span,
        )
        return self._apply_call_expr_annotation(
            callee=callee,
            args=args,
            keywords=keywords,
            source_span=source_span,
            repr_text=repr_text,
            call_ret=call_ret,
            fn_name=fn_name,
        )

    def _resolve_named_call_dispatch_kind(
        self,
        *,
        call_dispatch: dict[str, str],
    ) -> str:
        """named-call dispatch kind の分類を helper へ寄せる。"""
        if str(call_dispatch.get("builtin_runtime_call", "")) != "":
            return "builtin"
        if (
            str(call_dispatch.get("stdlib_fn_runtime_call", "")) != ""
            or str(call_dispatch.get("stdlib_symbol_runtime_call", "")) != ""
            or str(call_dispatch.get("noncpp_symbol_runtime_call", "")) != ""
        ):
            return "runtime"
        return ""

    def _resolve_named_call_annotation_state(
        self,
        *,
        fn_name: str,
    ) -> tuple[dict[str, str], str]:
        """named-call dispatch の lookup と分類決定を helper へ寄せる。"""
        call_dispatch = self._resolve_named_call_dispatch(fn_name=fn_name)
        dispatch_kind = self._resolve_named_call_dispatch_kind(
            call_dispatch=call_dispatch,
        )
        return call_dispatch, dispatch_kind

    def _annotate_named_call_expr(
        self,
        payload: dict[str, Any],
        *,
        fn_name: str,
        args: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Name callee の annotation dispatch を parser helper へ寄せる。"""
        call_dispatch, dispatch_kind = self._resolve_named_call_annotation_state(
            fn_name=fn_name,
        )
        return self._apply_named_call_dispatch(
            payload=payload,
            fn_name=fn_name,
            args=args,
            dispatch_kind=dispatch_kind,
            call_dispatch=call_dispatch,
        )

    def _annotate_builtin_named_call_expr(
        self,
        payload: dict[str, Any],
        *,
        fn_name: str,
        args: list[dict[str, Any]],
        call_dispatch: dict[str, str],
    ) -> dict[str, Any] | None:
        """builtin named-call の annotation dispatch を parser helper へ寄せる。"""
        semantic_tag, dispatch_kind, use_truthy_runtime, iter_element_type = (
            self._resolve_builtin_named_call_annotation_state(
                fn_name=fn_name,
                args=args,
                call_dispatch=call_dispatch,
            )
        )
        return self._apply_builtin_named_call_dispatch(
            payload=payload,
            fn_name=fn_name,
            args=args,
            dispatch_kind=dispatch_kind,
            semantic_tag=semantic_tag,
            use_truthy_runtime=use_truthy_runtime,
            iter_element_type=iter_element_type,
        )

    def _resolve_runtime_named_call_dispatch(
        self,
        *,
        call_dispatch: dict[str, str],
    ) -> tuple[str, str, str, str, str]:
        """runtime named-call dispatch field unpack を helper へ寄せる。"""
        stdlib_fn_runtime_call = str(call_dispatch.get("stdlib_fn_runtime_call", ""))
        stdlib_symbol_runtime_call = str(call_dispatch.get("stdlib_symbol_runtime_call", ""))
        noncpp_symbol_runtime_call = str(call_dispatch.get("noncpp_symbol_runtime_call", ""))
        stdlib_fn_semantic_tag = str(call_dispatch.get("stdlib_fn_semantic_tag", ""))
        stdlib_symbol_semantic_tag = str(call_dispatch.get("stdlib_symbol_semantic_tag", ""))
        return (
            stdlib_fn_runtime_call,
            stdlib_symbol_runtime_call,
            noncpp_symbol_runtime_call,
            stdlib_fn_semantic_tag,
            stdlib_symbol_semantic_tag,
        )

    def _resolve_runtime_named_call_kind(
        self,
        *,
        stdlib_fn_runtime_call: str,
        stdlib_symbol_runtime_call: str,
        noncpp_symbol_runtime_call: str,
    ) -> str:
        """runtime named-call の分類決定を helper へ寄せる。"""
        if stdlib_fn_runtime_call != "":
            return "stdlib_function"
        if stdlib_symbol_runtime_call != "":
            return "stdlib_symbol"
        if noncpp_symbol_runtime_call != "":
            return "noncpp_symbol"
        return ""

    def _resolve_runtime_named_call_annotation(
        self,
        *,
        call_dispatch: dict[str, str],
    ) -> tuple[str, str, str, str, str, str]:
        """runtime named-call の unpack と kind 判定を helper へ寄せる。"""
        (
            stdlib_fn_runtime_call,
            stdlib_symbol_runtime_call,
            noncpp_symbol_runtime_call,
            stdlib_fn_semantic_tag,
            stdlib_symbol_semantic_tag,
        ) = self._resolve_runtime_named_call_dispatch(
            call_dispatch=call_dispatch,
        )
        dispatch_kind = self._resolve_runtime_named_call_kind(
            stdlib_fn_runtime_call=stdlib_fn_runtime_call,
            stdlib_symbol_runtime_call=stdlib_symbol_runtime_call,
            noncpp_symbol_runtime_call=noncpp_symbol_runtime_call,
        )
        return (
            dispatch_kind,
            stdlib_fn_runtime_call,
            stdlib_symbol_runtime_call,
            noncpp_symbol_runtime_call,
            stdlib_fn_semantic_tag,
            stdlib_symbol_semantic_tag,
        )

    def _resolve_runtime_named_call_apply_state(
        self,
        *,
        call_dispatch: dict[str, str],
    ) -> tuple[str, str, str]:
        """runtime named-call apply 用の state を helper へ寄せる。"""
        (
            dispatch_kind,
            stdlib_fn_runtime_call,
            stdlib_symbol_runtime_call,
            noncpp_symbol_runtime_call,
            stdlib_fn_semantic_tag,
            stdlib_symbol_semantic_tag,
        ) = self._resolve_runtime_named_call_annotation(
            call_dispatch=call_dispatch,
        )
        if dispatch_kind == "stdlib_function":
            return dispatch_kind, stdlib_fn_runtime_call, stdlib_fn_semantic_tag
        if dispatch_kind == "stdlib_symbol":
            return dispatch_kind, stdlib_symbol_runtime_call, stdlib_symbol_semantic_tag
        if dispatch_kind == "noncpp_symbol":
            return dispatch_kind, noncpp_symbol_runtime_call, ""
        return "", "", ""

    def _annotate_runtime_named_call_expr(
        self,
        payload: dict[str, Any],
        *,
        fn_name: str,
        call_dispatch: dict[str, str],
    ) -> dict[str, Any] | None:
        """stdlib / non-C++ named-call dispatch を parser helper へ寄せる。"""
        dispatch_kind, runtime_call, semantic_tag = self._resolve_runtime_named_call_apply_state(
            call_dispatch=call_dispatch,
        )
        return self._apply_runtime_named_call_dispatch(
            payload=payload,
            fn_name=fn_name,
            dispatch_kind=dispatch_kind,
            runtime_call=runtime_call,
            semantic_tag=semantic_tag,
        )

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
