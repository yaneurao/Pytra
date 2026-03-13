#!/usr/bin/env python3
"""Self-hosted EAST expression parser helpers for named-call annotation clusters."""

from __future__ import annotations

from typing import Any

from toolchain.ir.core_parse_context import _SH_IMPORT_SYMBOLS
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_anyall_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_collection_ctor_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_enumerate_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_exception_ctor_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_fixed_runtime_builtin_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_iterator_builtin_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_minmax_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_noncpp_symbol_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_open_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_ordchr_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_scalar_ctor_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_stdlib_function_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_stdlib_symbol_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_annotate_type_predicate_call_expr
from toolchain.ir.core_runtime_call_semantics import _sh_infer_enumerate_item_type
from toolchain.ir.core_runtime_call_semantics import _sh_lookup_named_call_dispatch
from toolchain.ir.core_stmt_text_semantics import _sh_infer_item_type


class _ShExprNamedCallAnnotationMixin:
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
        if fn_name in {"Exception", "RuntimeError", "NotImplementedError"}:
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
