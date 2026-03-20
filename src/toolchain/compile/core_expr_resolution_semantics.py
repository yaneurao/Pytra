#!/usr/bin/env python3
"""Self-hosted EAST expression resolution semantics helpers."""

from __future__ import annotations

from typing import Any

from toolchain.frontends.frontend_semantics import lookup_stdlib_method_semantic_tag
from toolchain.frontends.signature_registry import lookup_stdlib_attribute_type
from toolchain.frontends.signature_registry import lookup_stdlib_imported_symbol_return_type
from toolchain.frontends.signature_registry import lookup_stdlib_method_runtime_binding
from toolchain.frontends.signature_registry import lookup_stdlib_method_runtime_call
from toolchain.compile.core_parse_context import _SH_IMPORT_MODULES
from toolchain.compile.core_parse_context import _SH_IMPORT_SYMBOLS
from toolchain.compile.core_runtime_call_semantics import _sh_infer_known_name_call_return_type
from toolchain.compile.core_runtime_call_semantics import _sh_lookup_noncpp_attr_runtime_call
from toolchain.compile.core_stmt_text_semantics import _sh_infer_item_type


class _ShExprResolutionSemanticsMixin:
    def _callable_return_type(self, t: str) -> str:
        """`callable[...]` 型文字列から戻り型だけを抽出する。"""
        if not (t.startswith("callable[") and t.endswith("]")):
            return "unknown"
        core = t[len("callable[") : -1]
        p = core.rfind("->")
        if p < 0:
            return "unknown"
        out = core[p + 2 :].strip()
        return out if out != "" else "unknown"

    def _lookup_method_return(self, cls_name: str, method: str) -> str:
        """クラス継承を辿ってメソッド戻り型を解決する。"""
        cur: str = cls_name
        while True:
            methods: dict[str, str] = {}
            if cur in self.class_method_return_types:
                methods = self.class_method_return_types[cur]
            if method in methods:
                value_obj: Any = methods[method]
                if isinstance(value_obj, str):
                    return value_obj
                return str(value_obj)
            next_cur_obj: Any = None
            if cur in self.class_base:
                next_cur_obj = self.class_base[cur]
            if not isinstance(next_cur_obj, str):
                break
            cur = next_cur_obj
        return "unknown"

    def _lookup_builtin_method_return(self, cls_name: str, method: str) -> str:
        """既知の組み込み型メソッドの戻り型を補助的に解決する。"""
        methods: dict[str, str] = {}
        if cls_name == "str":
            methods = {
                "strip": "str",
                "lstrip": "str",
                "rstrip": "str",
                "upper": "str",
                "lower": "str",
                "capitalize": "str",
                "split": "list[str]",
                "splitlines": "list[str]",
            }
        return methods.get(method, "unknown")

    def _resolve_named_call_declared_return_type(
        self,
        *,
        fn_name: str,
    ) -> str:
        """named-call の declared fallback 戻り型を helper へ寄せる。"""
        if fn_name in self.fn_return_types:
            return self.fn_return_types[fn_name]
        if fn_name in self.class_method_return_types:
            return fn_name
        return self._callable_return_type(str(self.name_types.get(fn_name, "unknown")))

    def _resolve_named_call_return_state(
        self,
        *,
        fn_name: str,
        args: list[dict[str, Any]],
    ) -> tuple[str, str]:
        """named-call の imported/declaration return state を helper へ寄せる。"""
        stdlib_imported_ret = (
            lookup_stdlib_imported_symbol_return_type(fn_name, _SH_IMPORT_SYMBOLS)
            if fn_name != ""
            else ""
        )
        call_ret = _sh_infer_known_name_call_return_type(
            fn_name,
            args,
            stdlib_imported_ret,
            infer_item_type=_sh_infer_item_type,
        )
        declared_ret = self._resolve_named_call_declared_return_type(
            fn_name=fn_name,
        )
        return call_ret, declared_ret

    def _infer_named_call_return_type(
        self,
        *,
        fn_name: str,
        args: list[dict[str, Any]],
    ) -> str:
        """Name callee の戻り型推論を helper へ寄せる。"""
        call_ret, declared_ret = self._resolve_named_call_return_state(
            fn_name=fn_name,
            args=args,
        )
        if call_ret != "":
            return call_ret
        return declared_ret

    def _lookup_attr_expr_metadata(
        self,
        owner_expr: dict[str, Any] | None,
        owner_type: str,
        attr_name: str,
    ) -> dict[str, str]:
        """属性アクセスの型と runtime metadata lookup を共有 helper へ寄せる。"""
        attr_t = "unknown"
        if (
            isinstance(owner_expr, dict)
            and owner_expr.get("kind") == "Name"
            and owner_expr.get("id") == "self"
        ):
            maybe_field_t = self.name_types.get(attr_name)
            if isinstance(maybe_field_t, str) and maybe_field_t != "":
                attr_t = maybe_field_t
        runtime_call = ""
        semantic_tag = ""
        module_id = ""
        runtime_symbol = ""
        std_attr_t = lookup_stdlib_attribute_type(owner_type, attr_name)
        if std_attr_t != "":
            attr_t = std_attr_t
            runtime_call = lookup_stdlib_method_runtime_call(owner_type, attr_name)
            semantic_tag = lookup_stdlib_method_semantic_tag(attr_name)
            if runtime_call != "":
                module_id, runtime_symbol = lookup_stdlib_method_runtime_binding(owner_type, attr_name)
        noncpp_module_id, noncpp_runtime_call = _sh_lookup_noncpp_attr_runtime_call(
            owner_expr,
            attr_name,
            import_modules=_SH_IMPORT_MODULES,
            import_symbols=_SH_IMPORT_SYMBOLS,
        )
        return {
            "resolved_type": attr_t,
            "runtime_call": runtime_call,
            "semantic_tag": semantic_tag,
            "module_id": module_id,
            "runtime_symbol": runtime_symbol,
            "noncpp_module_id": noncpp_module_id,
            "noncpp_runtime_call": noncpp_runtime_call,
        }

    def _split_generic_types(self, s: str) -> list[str]:
        """ジェネリック型引数をトップレベルカンマで分割する。"""
        out: list[str] = []
        depth = 0
        start = 0
        for i, ch in enumerate(s):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            elif ch == "," and depth == 0:
                out.append(s[start:i].strip())
                start = i + 1
        out.append(s[start:].strip())
        return out

    def _split_union_types(self, s: str) -> list[str]:
        """Union 型引数をトップレベル `|` で分割する。"""
        out: list[str] = []
        depth = 0
        start = 0
        for i, ch in enumerate(s):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            elif ch == "|" and depth == 0:
                out.append(s[start:i].strip())
                start = i + 1
        out.append(s[start:].strip())
        return out

    def _is_forbidden_object_receiver_type(self, t: str) -> bool:
        """object レシーバ禁止ルールに該当する型か判定する。"""
        s = t.strip()
        if s in {"object", "Any", "any"}:
            return True
        if "|" in s:
            parts = self._split_union_types(s)
            return any(p in {"object", "Any", "any"} for p in parts if p != "None")
        return False

    def _is_forbidden_dynamic_helper_type(self, t: str) -> bool:
        """decode-first helper に直接渡してはいけない動的型か判定する。"""
        s = t.strip()
        if s in {"object", "Any", "any"}:
            return True
        if "|" in s:
            parts = self._split_union_types(s)
            return any(p in {"object", "Any", "any"} for p in parts if p != "None")
        return False

    def _guard_dynamic_helper_receiver(self, helper_name: str, owner_t: str, source_span: dict[str, int]) -> None:
        """dynamic helper の receiver が decode-first 契約に違反していないか検査する。"""
        if not self._is_forbidden_dynamic_helper_type(owner_t):
            return
        raise self._raise_expr_build_error(
            kind="unsupported_syntax",
            message=f"{helper_name}() does not accept object/Any receivers under decode-first constraints",
            source_span=source_span,
            hint=f"Decode JSON values to a concrete type before calling {helper_name}().",
        )

    def _guard_dynamic_helper_args(
        self,
        helper_name: str,
        args: list[dict[str, Any]],
        source_span: dict[str, int],
    ) -> None:
        """dynamic helper に object/Any 引数が直接渡っていないか検査する。"""
        for arg in args:
            if not isinstance(arg, dict):
                continue
            arg_t = str(arg.get("resolved_type", "unknown")).strip()
            if arg_t == "":
                arg_t = "unknown"
            if self._is_forbidden_dynamic_helper_type(arg_t):
                raise self._raise_expr_build_error(
                    kind="unsupported_syntax",
                    message=f"{helper_name}() does not accept object/Any values under decode-first constraints",
                    source_span=source_span,
                    hint=f"Decode JSON values to a concrete type before calling {helper_name}().",
                )
