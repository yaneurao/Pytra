#!/usr/bin/env python3
"""Self-hosted EAST expression parser helpers for call argument parsing."""

from __future__ import annotations

from typing import Any

from toolchain.ir.core_ast_builders import _sh_make_comp_generator
from toolchain.ir.core_ast_builders import _sh_make_list_comp_expr
from toolchain.ir.core_builder_base import _sh_make_name_expr
from toolchain.ir.core_builder_base import _sh_make_tuple_expr
from toolchain.ir.core_stmt_text_semantics import _sh_split_top_commas


class _ShExprCallArgParserMixin:
    def _consume_call_arg_loop_comma_token(self) -> dict[str, Any]:
        """call argument loop の `,` consume を helper へ寄せる。"""
        return self._eat(",")

    def _apply_call_arg_loop_continue_state(self) -> bool:
        """call argument loop の continue state apply を helper へ寄せる。"""
        return self._resolve_call_arg_loop_continue_kind()

    def _resolve_call_arg_loop_continue_kind(self) -> bool:
        """call argument loop の continue kind 判定を helper へ寄せる。"""
        return self._cur()["k"] != ")"

    def _parse_call_args(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Call expr の位置引数と keyword 引数を parser helper へ寄せる。"""
        args: list[dict[str, Any]] = []
        keywords: list[dict[str, Any]] = []
        if self._resolve_call_args_empty_state():
            return self._apply_call_args_empty_state(
                args=args,
                keywords=keywords,
            )
        return self._consume_call_arg_entries(
            args=args,
            keywords=keywords,
        )

    def _consume_call_arg_entries(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """call argument 非空 loop を helper へ寄せる。"""
        self._consume_call_arg_entries_loop(
            args=args,
            keywords=keywords,
        )
        args, keywords = self._resolve_call_arg_entries_result_state(
            args=args,
            keywords=keywords,
        )
        return self._apply_call_arg_entries_result_state(
            args=args,
            keywords=keywords,
        )

    def _resolve_call_arg_entries_result_state(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """call argument 非空 loop の result state resolve を helper へ寄せる。"""
        return self._resolve_call_arg_entries_result_state_value(
            args=args,
            keywords=keywords,
        )

    def _resolve_call_arg_entries_result_state_value(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """call argument 非空 loop の result state value を helper へ寄せる。"""
        return self._apply_call_args_empty_state(
            args=args,
            keywords=keywords,
        )

    def _apply_call_arg_entries_result_state(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """call argument 非空 loop の result state apply を helper へ寄せる。"""
        return self._apply_call_arg_entries_result_state_result(
            args=args,
            keywords=keywords,
        )

    def _apply_call_arg_entries_result_state_result(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """call argument 非空 loop の result return を helper へ寄せる。"""
        return args, keywords

    def _consume_call_arg_entries_loop(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> None:
        """call argument 非空 loop 本体を helper へ寄せる。"""
        while True:
            should_continue = self._resolve_call_arg_entries_loop_state(
                args=args,
                keywords=keywords,
            )
            if not self._apply_call_arg_entries_loop_state(should_continue=should_continue):
                break

    def _resolve_call_arg_entries_loop_state(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> bool:
        """call argument 非空 loop の continue state を helper へ寄せる。"""
        return self._resolve_call_arg_entries_loop_state_value(
            args=args,
            keywords=keywords,
        )

    def _resolve_call_arg_entries_loop_state_value(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> bool:
        """call argument 非空 loop の continue state value を helper へ寄せる。"""
        return self._consume_call_arg_loop_entry(
            args=args,
            keywords=keywords,
        )

    def _apply_call_arg_entries_loop_state(self, *, should_continue: bool) -> bool:
        """call argument 非空 loop の continue apply を helper へ寄せる。"""
        return self._apply_call_arg_entries_loop_state_result(
            should_continue=should_continue,
        )

    def _apply_call_arg_entries_loop_state_result(
        self,
        *,
        should_continue: bool,
    ) -> bool:
        """call argument 非空 loop の continue result を helper へ寄せる。"""
        return should_continue

    def _consume_call_arg_loop_entry(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> bool:
        """call argument loop 1周分の処理を helper へ寄せる。"""
        arg_entry, keyword_entry = self._resolve_call_arg_loop_entry_state()
        return self._apply_call_arg_loop_entry_state(
            args=args,
            keywords=keywords,
            arg_entry=arg_entry,
            keyword_entry=keyword_entry,
        )

    def _resolve_call_arg_loop_entry_state(
        self,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument loop 1周分の state resolve を helper へ寄せる。"""
        return self._resolve_call_arg_loop_entry_state_value()

    def _resolve_call_arg_loop_entry_state_value(
        self,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument loop 1周分の state value を helper へ寄せる。"""
        return self._parse_call_arg_entry()

    def _apply_call_arg_loop_entry_state(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        arg_entry: dict[str, Any] | None,
        keyword_entry: dict[str, Any] | None,
    ) -> bool:
        """call argument loop 1周分の state apply を helper へ寄せる。"""
        return self._apply_call_arg_loop_entry_state_result(
            args=args,
            keywords=keywords,
            arg_entry=arg_entry,
            keyword_entry=keyword_entry,
        )

    def _apply_call_arg_loop_entry_state_result(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        arg_entry: dict[str, Any] | None,
        keyword_entry: dict[str, Any] | None,
    ) -> bool:
        """call argument loop 1周分の state result apply を helper へ寄せる。"""
        self._apply_call_arg_entry(
            args=args,
            keywords=keywords,
            arg_entry=arg_entry,
            keyword_entry=keyword_entry,
        )
        return self._advance_call_arg_loop()

    def _resolve_call_args_empty_state(self) -> bool:
        """call argument list の空 `)` 判定を helper へ寄せる。"""
        return self._resolve_call_args_empty_kind()

    def _resolve_call_args_empty_kind(self) -> bool:
        """call argument list の空 `)` kind probe を helper へ寄せる。"""
        return self._cur()["k"] == ")"

    def _apply_call_args_empty_state(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """call argument list の空-state apply を helper へ寄せる。"""
        return self._apply_call_args_empty_state_result(
            args=args,
            keywords=keywords,
        )

    def _apply_call_args_empty_state_result(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """call argument list の空-state result return を helper へ寄せる。"""
        return args, keywords

    def _dict_stmt_list(self, raw: Any) -> list[dict[str, Any]]:
        """動的値から `list[dict]` を安全に取り出す。"""
        out: list[dict[str, Any]] = []
        if not isinstance(raw, list):
            return out
        for item in raw:
            if isinstance(item, dict):
                out.append(item)
        return out

    def _node_kind_from_dict(self, node_dict: dict[str, Any]) -> str:
        """dict 化されたノードから kind を安全に文字列取得する。"""
        if not isinstance(node_dict, dict):
            return ""
        kind = node_dict.get("kind")
        if isinstance(kind, str):
            return kind.strip()
        if kind is None:
            return ""
        txt = str(kind).strip()
        return txt if txt != "" else ""

    def _iter_item_type(self, iter_expr: dict[str, Any] | None) -> str:
        """for 反復対象の要素型を推論する。"""
        if not isinstance(iter_expr, dict):
            return "unknown"
        t = str(iter_expr.get("resolved_type", "unknown"))
        if t.startswith("List[") and t.endswith("]"):
            t = "list[" + t[5:-1] + "]"
        if t.startswith("Set[") and t.endswith("]"):
            t = "set[" + t[4:-1] + "]"
        if t.startswith("Dict[") and t.endswith("]"):
            t = "dict[" + t[5:-1] + "]"
        if t == "range":
            return "int64"
        if t.startswith("list[") and t.endswith("]"):
            inner = t[5:-1].strip()
            return inner if inner != "" else "unknown"
        if t.startswith("set[") and t.endswith("]"):
            inner = t[4:-1].strip()
            return inner if inner != "" else "unknown"
        if t == "bytearray" or t == "bytes":
            return "uint8"
        if t == "str":
            return "str"
        return "unknown"

    def _parse_name_comp_target(self) -> dict[str, Any] | None:
        """内包表現ターゲットの `NAME` / `NAME, ...` 分岐を helper へ寄せる。"""
        if self._cur()["k"] != "NAME":
            return None
        first = self._eat("NAME")
        first_name = str(first["v"])
        first_t = self.name_types.get(first_name, "unknown")
        first_node = _sh_make_name_expr(
            self._node_span(first["s"], first["e"]),
            first_name,
            resolved_type=first_t,
        )
        if self._cur()["k"] != ",":
            return first_node
        elems: list[dict[str, Any]] = [first_node]
        last_e = first["e"]
        while self._cur()["k"] == ",":
            self._eat(",")
            if self._cur()["k"] != "NAME":
                break
            nm_tok = self._eat("NAME")
            nm = str(nm_tok["v"])
            t = self.name_types.get(nm, "unknown")
            elems.append(_sh_make_name_expr(self._node_span(nm_tok["s"], nm_tok["e"]), nm, resolved_type=t))
            last_e = nm_tok["e"]
        return _sh_make_tuple_expr(
            self._node_span(first["s"], last_e),
            elems,
            repr_text=self._src_slice(first["s"], last_e),
        )

    def _parse_tuple_comp_target(self) -> dict[str, Any] | None:
        """内包表現ターゲットの `(` tuple 分岐を helper へ寄せる。"""
        if self._cur()["k"] != "(":
            return None
        l = self._eat("(")
        elems: list[dict[str, Any]] = []
        elems.append(self._parse_comp_target())
        while self._cur()["k"] == ",":
            self._eat(",")
            if self._cur()["k"] == ")":
                break
            elems.append(self._parse_comp_target())
        r = self._eat(")")
        return _sh_make_tuple_expr(
            self._node_span(l["s"], r["e"]),
            elems,
            resolved_type="tuple[unknown]",
            repr_text=self._src_slice(l["s"], r["e"]),
        )

    def _collect_and_bind_comp_target_types(
        self,
        target_expr: dict[str, Any],
        value_type: str,
        snapshots: dict[str, str],
    ) -> None:
        """内包ターゲットの各 Name へ一時的に型を設定する。"""
        kind = self._node_kind_from_dict(target_expr)
        if kind == "Name":
            nm = str(target_expr.get("id", "")).strip()
            if nm == "":
                return
            if nm not in snapshots:
                snapshots[nm] = str(self.name_types.get(nm, ""))
            target_expr["resolved_type"] = value_type
            self.name_types[nm] = value_type
            return

        if kind != "Tuple":
            return

        target_elements = self._dict_stmt_list(target_expr.get("elements"))
        elem_types: list[str] = []
        if isinstance(value_type, str) and value_type.startswith("tuple[") and value_type.endswith("]"):
            inner = value_type[6:-1].strip()
            if inner != "":
                elem_types = [p.strip() for p in _sh_split_top_commas(inner)]
        for idx, elem in enumerate(target_elements):
            if not isinstance(elem, dict):
                continue
            et = value_type
            if idx < len(elem_types):
                et0 = elem_types[idx]
                if et0 != "":
                    et = et0
            self._collect_and_bind_comp_target_types(elem, et, snapshots)

    def _restore_comp_target_types(self, snapshots: dict[str, str]) -> None:
        """内包ターゲット一時型束縛を復元する。"""
        for nm, old_t in snapshots.items():
            if old_t == "":
                self.name_types.pop(nm, None)
            else:
                self.name_types[nm] = old_t
