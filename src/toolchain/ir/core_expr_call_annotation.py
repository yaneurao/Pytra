#!/usr/bin/env python3
"""Self-hosted EAST expression parser helpers for call/callee annotation orchestration."""

from __future__ import annotations

from typing import Any
from toolchain.frontends.signature_registry import lookup_stdlib_method_return_type
from toolchain.ir.core_ast_builders import _sh_make_call_expr
from toolchain.ir.core_entrypoints import _make_east_build_error
from toolchain.ir.core_parse_context import _SH_IMPORT_MODULES
from toolchain.ir.core_parse_context import _SH_IMPORT_SYMBOLS
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_anyall_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_collection_ctor_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_enumerate_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_exception_ctor_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_fixed_runtime_builtin_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_iterator_builtin_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_minmax_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_noncpp_attr_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_noncpp_symbol_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_open_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_ordchr_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_runtime_method_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_scalar_ctor_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_stdlib_function_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_stdlib_symbol_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_type_predicate_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_infer_enumerate_item_type
from toolchain.ir.core_runtime_call_semantics import _sh_lookup_named_call_dispatch
from toolchain.ir.core_stmt_text_semantics import _sh_infer_item_type


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
        if str(call_dispatch.get("builtin_semantic_tag", "")) != "":
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

    def _guard_named_call_args(
        self,
        *,
        fn_name: str,
        args: list[dict[str, Any]],
        source_span: dict[str, int],
    ) -> None:
        """decode-first 制約がある named-call 引数検査を helper へ寄せる。"""
        if fn_name in {"sum", "zip", "sorted", "min", "max"}:
            self._guard_dynamic_helper_args(
                helper_name=fn_name,
                args=args,
                source_span=source_span,
            )

    def _build_call_expr_payload(
        self,
        *,
        callee: dict[str, Any],
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        source_span: dict[str, int],
        repr_text: str,
        call_ret: str,
    ) -> dict[str, Any]:
        """Call expr payload 組み立てを helper へ寄せる。"""
        return _sh_make_call_expr(
            source_span,
            callee,
            args,
            keywords,
            resolved_type=call_ret,
            repr_text=repr_text,
        )

    def _apply_named_call_dispatch(
        self,
        payload: dict[str, Any],
        *,
        fn_name: str,
        args: list[dict[str, Any]],
        call_dispatch: dict[str, str],
        dispatch_kind: str,
    ) -> dict[str, Any]:
        """named-call dispatch の annotation 適用を helper へ寄せる。"""
        if dispatch_kind == "builtin":
            return self._apply_builtin_named_call_annotation(
                payload,
                fn_name=fn_name,
                args=args,
                call_dispatch=call_dispatch,
            )
        if dispatch_kind == "runtime":
            return self._apply_runtime_named_call_annotation(
                payload,
                fn_name=fn_name,
                call_dispatch=call_dispatch,
            )
        return payload

    def _coalesce_optional_annotation_payload(
        self,
        *,
        payload: dict[str, Any],
        annotated_payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """optional annotation payload の fallback を helper へ寄せる。"""
        return payload if annotated_payload is None else annotated_payload

    def _apply_builtin_named_call_annotation(
        self,
        payload: dict[str, Any],
        *,
        fn_name: str,
        args: list[dict[str, Any]],
        call_dispatch: dict[str, str],
    ) -> dict[str, Any]:
        """builtin named-call apply を helper へ寄せる。"""
        builtin_payload = self._annotate_builtin_named_call_expr(
            payload,
            fn_name=fn_name,
            args=args,
            call_dispatch=call_dispatch,
        )
        return self._coalesce_optional_annotation_payload(
            payload=payload,
            annotated_payload=builtin_payload,
        )

    def _apply_runtime_named_call_annotation(
        self,
        payload: dict[str, Any],
        *,
        fn_name: str,
        call_dispatch: dict[str, str],
    ) -> dict[str, Any]:
        """runtime named-call apply を helper へ寄せる。"""
        runtime_payload = self._annotate_runtime_named_call_expr(
            payload,
            fn_name=fn_name,
            call_dispatch=call_dispatch,
        )
        return self._coalesce_optional_annotation_payload(
            payload=payload,
            annotated_payload=runtime_payload,
        )

    def _resolve_named_call_dispatch(
        self,
        *,
        fn_name: str,
    ) -> dict[str, str]:
        """named-call dispatch lookup を helper へ寄せる。"""
        return _sh_lookup_named_call_dispatch(
            fn_name,
            import_symbols=_SH_IMPORT_SYMBOLS,
        )

    def _should_use_truthy_runtime_for_bool_ctor(
        self,
        *,
        args: list[dict[str, Any]],
    ) -> bool:
        """bool(...) が truthy runtime helper を使うべきか判定する。"""
        if len(args) != 1:
            return False
        arg0 = args[0]
        if not isinstance(arg0, dict):
            return False
        arg0_t = str(arg0.get("resolved_type", "unknown"))
        return self._is_forbidden_object_receiver_type(arg0_t)

    def _resolve_builtin_named_call_semantic_tag(
        self,
        *,
        call_dispatch: dict[str, str],
    ) -> str:
        """builtin named-call dispatch の semantic tag unpack を helper へ寄せる。"""
        return str(call_dispatch.get("builtin_semantic_tag", ""))

    def _resolve_builtin_named_call_kind(self, *, fn_name: str) -> str:
        """builtin named-call の分類決定を helper へ寄せる。"""
        if fn_name in {"print", "len", "range", "zip", "str"}:
            return "fixed_runtime"
        if fn_name in {"int", "float", "bool"}:
            return "scalar_ctor"
        if fn_name in {"min", "max"}:
            return "minmax"
        if fn_name in {"Exception", "RuntimeError"}:
            return "exception_ctor"
        if fn_name == "open":
            return "open"
        if fn_name in {"iter", "next", "reversed"}:
            return "iterator"
        if fn_name == "enumerate":
            return "enumerate"
        if fn_name in {"any", "all"}:
            return "anyall"
        if fn_name in {"ord", "chr"}:
            return "ordchr"
        if fn_name in {"bytes", "bytearray", "list", "set", "dict"}:
            return "collection_ctor"
        if fn_name in {"isinstance", "issubclass"}:
            return "type_predicate"
        return ""

    def _resolve_builtin_named_call_dispatch(
        self,
        *,
        fn_name: str,
        call_dispatch: dict[str, str],
    ) -> tuple[str, str]:
        """builtin named-call の semantic tag / kind 解決を helper へ寄せる。"""
        semantic_tag = self._resolve_builtin_named_call_semantic_tag(
            call_dispatch=call_dispatch,
        )
        dispatch_kind = self._resolve_builtin_named_call_kind(
            fn_name=fn_name,
        )
        return semantic_tag, dispatch_kind

    def _resolve_builtin_named_call_annotation_state(
        self,
        *,
        fn_name: str,
        args: list[dict[str, Any]],
        call_dispatch: dict[str, str],
    ) -> tuple[str, str, bool, str]:
        """builtin named-call の annotation 前段 state を helper へ寄せる。"""
        semantic_tag, dispatch_kind = self._resolve_builtin_named_call_dispatch(
            fn_name=fn_name,
            call_dispatch=call_dispatch,
        )
        use_truthy_runtime = self._resolve_builtin_named_call_truthy_state(
            fn_name=fn_name,
            dispatch_kind=dispatch_kind,
            args=args,
        )
        iter_element_type = self._resolve_builtin_named_call_iter_element_type(
            dispatch_kind=dispatch_kind,
            args=args,
        )
        return semantic_tag, dispatch_kind, use_truthy_runtime, iter_element_type

    def _resolve_builtin_named_call_truthy_state(
        self,
        *,
        fn_name: str,
        dispatch_kind: str,
        args: list[dict[str, Any]],
    ) -> bool:
        """builtin named-call の truthy-runtime 特例を helper へ寄せる。"""
        return (
            dispatch_kind == "scalar_ctor"
            and fn_name == "bool"
            and self._should_use_truthy_runtime_for_bool_ctor(args=args)
        )

    def _resolve_builtin_named_call_iter_element_type(
        self,
        *,
        dispatch_kind: str,
        args: list[dict[str, Any]],
    ) -> str:
        """builtin named-call の enumerate item 型推論を helper へ寄せる。"""
        if dispatch_kind == "enumerate":
            return _sh_infer_enumerate_item_type(
                args,
                infer_item_type=_sh_infer_item_type,
            )
        return "unknown"

    def _apply_fixed_runtime_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """fixed-runtime builtin apply を helper へ寄せる。"""
        return _sh_annotate_fixed_runtime_builtin_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_scalar_ctor_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        args: list[dict[str, Any]],
        use_truthy_runtime: bool,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """scalar ctor builtin apply を helper へ寄せる。"""
        return _sh_annotate_scalar_ctor_call_expr(
            payload,
            fn_name=fn_name,
            arg_count=len(args),
            use_truthy_runtime=use_truthy_runtime,
            semantic_tag=semantic_tag,
        )

    def _apply_minmax_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """min/max builtin apply を helper へ寄せる。"""
        return _sh_annotate_minmax_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_exception_ctor_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """exception ctor builtin apply を helper へ寄せる。"""
        return _sh_annotate_exception_ctor_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_open_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        semantic_tag: str,
    ) -> dict[str, Any]:
        """open builtin apply を helper へ寄せる。"""
        return _sh_annotate_open_call_expr(
            payload,
            semantic_tag=semantic_tag,
        )

    def _apply_iterator_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """iterator builtin apply を helper へ寄せる。"""
        return _sh_annotate_iterator_builtin_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_enumerate_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        iter_element_type: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """enumerate builtin apply を helper へ寄せる。"""
        return _sh_annotate_enumerate_call_expr(
            payload,
            iter_element_type=iter_element_type,
            semantic_tag=semantic_tag,
        )

    def _apply_anyall_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """any/all builtin apply を helper へ寄せる。"""
        return _sh_annotate_anyall_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_ordchr_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """ord/chr builtin apply を helper へ寄せる。"""
        return _sh_annotate_ordchr_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_collection_ctor_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """collection ctor builtin apply を helper へ寄せる。"""
        return _sh_annotate_collection_ctor_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_type_predicate_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """type predicate builtin apply を helper へ寄せる。"""
        return _sh_annotate_type_predicate_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_builtin_named_call_dispatch(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        args: list[dict[str, Any]],
        dispatch_kind: str,
        semantic_tag: str,
        use_truthy_runtime: bool,
        iter_element_type: str,
    ) -> dict[str, Any] | None:
        """builtin named-call dispatch の annotation 適用を helper へ寄せる。"""
        if dispatch_kind == "fixed_runtime":
            return self._apply_fixed_runtime_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "scalar_ctor":
            return self._apply_scalar_ctor_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                args=args,
                use_truthy_runtime=use_truthy_runtime,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "minmax":
            return self._apply_minmax_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "exception_ctor":
            return self._apply_exception_ctor_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "open":
            return self._apply_open_builtin_named_call_annotation(
                payload=payload,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "iterator":
            return self._apply_iterator_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "enumerate":
            return self._apply_enumerate_builtin_named_call_annotation(
                payload=payload,
                iter_element_type=iter_element_type,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "anyall":
            return self._apply_anyall_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "ordchr":
            return self._apply_ordchr_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "collection_ctor":
            return self._apply_collection_ctor_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "type_predicate":
            return self._apply_type_predicate_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        return None

    def _apply_stdlib_function_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        runtime_call: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """stdlib function named-call annotation 適用を helper へ寄せる。"""
        return _sh_annotate_stdlib_function_call_expr(
            payload,
            fn_name=fn_name,
            runtime_call=runtime_call,
            semantic_tag=semantic_tag,
        )

    def _apply_stdlib_symbol_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        runtime_call: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """stdlib symbol named-call annotation 適用を helper へ寄せる。"""
        return _sh_annotate_stdlib_symbol_call_expr(
            payload,
            fn_name=fn_name,
            runtime_call=runtime_call,
            import_symbols=_SH_IMPORT_SYMBOLS,
            semantic_tag=semantic_tag,
        )

    def _apply_noncpp_symbol_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        runtime_call: str,
    ) -> dict[str, Any]:
        """non-C++ symbol named-call annotation 適用を helper へ寄せる。"""
        return _sh_annotate_noncpp_symbol_call_expr(
            payload,
            fn_name=fn_name,
            runtime_call=runtime_call,
            import_symbols=_SH_IMPORT_SYMBOLS,
        )

    def _apply_runtime_named_call_dispatch(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        dispatch_kind: str,
        runtime_call: str,
        semantic_tag: str,
    ) -> dict[str, Any] | None:
        """runtime named-call dispatch の annotation 適用を helper へ寄せる。"""
        if dispatch_kind == "stdlib_function":
            return self._apply_stdlib_function_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                runtime_call=runtime_call,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "stdlib_symbol":
            return self._apply_stdlib_symbol_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                runtime_call=runtime_call,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "noncpp_symbol":
            return self._apply_noncpp_symbol_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                runtime_call=runtime_call,
            )
        return None

    def _resolve_attr_expr_owner_state(
        self,
        *,
        owner_expr: dict[str, Any],
        attr_name: str,
        source_span: dict[str, int],
    ) -> str:
        """Attribute access の owner 型判定と preflight guard を helper へ寄せる。"""
        owner_t = self._owner_expr_resolved_type(owner_expr)
        if attr_name in {"keys", "items", "values"}:
            self._guard_dynamic_helper_receiver(
                helper_name=attr_name,
                owner_t=owner_t,
                source_span=source_span,
            )
        if self._is_forbidden_object_receiver_type(owner_t):
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message="object receiver attribute/method access is forbidden by language constraints",
                source_span=source_span,
                hint="Cast or assign to a concrete type before attribute/method access.",
            )
        return owner_t

    def _apply_noncpp_attr_call_expr_annotation(
        self,
        *,
        payload: dict[str, Any],
        owner_expr: dict[str, Any] | None,
        attr: str,
    ) -> None:
        """non-C++ attr-call annotation 適用を helper へ寄せる。"""
        _sh_annotate_noncpp_attr_call_expr(
            payload,
            owner_expr=owner_expr,
            attr_name=attr,
            import_modules=_SH_IMPORT_MODULES,
            import_symbols=_SH_IMPORT_SYMBOLS,
        )

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
        self._apply_noncpp_attr_call_expr_annotation(
            payload=payload,
            owner_expr=owner_expr,
            attr=attr,
        )
        self._apply_runtime_method_call_expr_annotation(
            payload=payload,
            owner_expr=owner_expr,
            owner_t=owner_t,
            attr=attr,
        )
        return payload
