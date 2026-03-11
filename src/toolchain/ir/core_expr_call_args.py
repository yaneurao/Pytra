#!/usr/bin/env python3
"""Self-hosted EAST expression parser helpers for call argument parsing."""

from __future__ import annotations

from typing import Any

from toolchain.ir.core_entrypoints import _make_east_build_error
from toolchain.ir.core_ast_builders import _sh_make_comp_generator
from toolchain.ir.core_ast_builders import _sh_make_keyword_arg
from toolchain.ir.core_ast_builders import _sh_make_list_comp_expr
from toolchain.ir.core_ast_builders import _sh_make_starred_expr
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

    def _parse_comp_target(self) -> dict[str, Any]:
        """内包表現のターゲット（name / tuple）を解析する。"""
        name_target = self._parse_name_comp_target()
        if name_target is not None:
            return name_target
        tuple_target = self._parse_tuple_comp_target()
        if tuple_target is not None:
            return tuple_target
        tok = self._cur()
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message="invalid comprehension target in call argument",
            source_span=self._node_span(tok["s"], tok["e"]),
            hint="Use name or tuple target in generator expression.",
        )

    def _parse_call_arg_expr(self) -> dict[str, Any]:
        """呼び出し引数式を解析し、必要なら generator 引数へ lower する。"""
        from toolchain.ir.core_expr_shell import _sh_parse_expr

        if self._resolve_call_arg_expr_is_starred():
            return self._parse_starred_call_arg_expr()
        first = self._parse_ifexp()
        if not (self._cur()["k"] == "NAME" and self._cur()["v"] == "for"):
            return first

        snapshots: dict[str, str] = {}
        generators: list[dict[str, Any]] = []
        first_norm = first
        end_node: Any = first

        def _reparse_expr(expr_node: dict[str, Any]) -> dict[str, Any]:
            expr_repr = expr_node.get("repr")
            if not isinstance(expr_repr, str) or expr_repr == "":
                return expr_node
            return _sh_parse_expr(
                expr_repr,
                line_no=self.line_no,
                col_base=int(expr_node.get("source_span", {}).get("col", self.col_base)),
                name_types=self.name_types,
                fn_return_types=self.fn_return_types,
                class_method_return_types=self.class_method_return_types,
                class_base=self.class_base,
            )

        while self._cur()["k"] == "NAME" and self._cur()["v"] == "for":
            self._eat("NAME")
            target = self._parse_comp_target()
            in_tok = self._eat("NAME")
            if in_tok["v"] != "in":
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="expected 'in' in generator expression",
                    source_span=self._node_span(in_tok["s"], in_tok["e"]),
                    hint="Use `for x in iterable` form.",
                )
            iter_expr = self._parse_or()
            if not isinstance(iter_expr, dict):
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="unsupported iterator expression in generator argument",
                    source_span=self._node_span(
                        int(iter_expr["source_span"]["col"]) if isinstance(iter_expr, dict) else self.col_base,
                        int(iter_expr["source_span"]["end_col"]) if isinstance(iter_expr, dict) else self.col_base + 1,
                    ),
                    hint="Use a resolvable iterable expression.",
                )

            conds: list[dict[str, Any]] = []
            while self._cur()["k"] == "NAME" and self._cur()["v"] == "if":
                self._eat("NAME")
                conds.append(self._parse_or())
            conds_norm: list[dict[str, Any]] = list(conds)

            tgt_ty = self._iter_item_type(iter_expr)
            if tgt_ty != "unknown":
                self._collect_and_bind_comp_target_types(target, tgt_ty, snapshots)
                if len(generators) == 0:
                    first_norm = _reparse_expr(first)
                conds_norm = [_reparse_expr(cond) if isinstance(cond, dict) else cond for cond in conds]

            if len(conds_norm) > 0:
                end_node = conds_norm[-1]
            else:
                end_node = iter_expr

            generators.append(_sh_make_comp_generator(target, iter_expr, conds_norm))

        self._restore_comp_target_types(snapshots)
        s = int(first["source_span"]["col"]) - self.col_base
        if not isinstance(end_node, dict):
            return first
        e = int(end_node["source_span"]["end_col"]) - self.col_base
        return _sh_make_list_comp_expr(
            self._node_span(s, e),
            first_norm,
            generators,
            repr_text=self._src_slice(s, e),
            lowered_kind="GeneratorArg",
        )

    def _resolve_call_arg_expr_is_starred(self) -> bool:
        """call argument expr の starred 開始判定を helper へ寄せる。"""
        return self._cur()["k"] == "*"

    def _parse_starred_call_arg_expr(self) -> dict[str, Any]:
        """call argument 位置の `*expr` を `Starred` として保持する。"""
        star_tok = self._eat("*")
        value_expr = self._parse_ifexp()
        end_col = int(value_expr.get("source_span", {}).get("end_col", star_tok["e"]))
        source_span = self._node_span(star_tok["s"], end_col - self.col_base)
        repr_text = self._src_slice(star_tok["s"], end_col - self.col_base)
        return _sh_make_starred_expr(
            source_span,
            value_expr,
            resolved_type=str(value_expr.get("resolved_type", "unknown")),
            repr_text=repr_text,
        )

    def _parse_call_arg_entry(
        self,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument 1件分の positional/keyword 分岐を parser helper へ寄せる。"""
        save_pos, name_tok, is_keyword = self._resolve_call_arg_entry_state()
        return self._apply_call_arg_entry_state(
            save_pos=save_pos,
            name_tok=name_tok,
            is_keyword=is_keyword,
        )

    def _resolve_call_arg_entry_state(
        self,
    ) -> tuple[int | None, dict[str, Any] | None, bool]:
        """call argument 1件分の token/state resolve を helper へ寄せる。"""
        if not self._resolve_call_arg_entry_has_name():
            return None, None, False
        save_pos = self._resolve_call_arg_entry_save_pos()
        name_tok = self._consume_call_arg_entry_name_token()
        return save_pos, name_tok, self._resolve_call_arg_entry_kind()

    def _resolve_call_arg_entry_has_name(self) -> bool:
        """call argument entry の `NAME` 開始判定を helper へ寄せる。"""
        return self._cur()["k"] == "NAME"

    def _resolve_call_arg_entry_save_pos(self) -> int:
        """call argument entry の save pos 取得を helper へ寄せる。"""
        return self.pos

    def _resolve_call_arg_entry_kind(self) -> bool:
        """call argument 1件分の keyword 判定を helper へ寄せる。"""
        return self._resolve_call_arg_entry_is_keyword()

    def _resolve_call_arg_entry_is_keyword(self) -> bool:
        """call argument entry の keyword kind 判定を helper へ寄せる。"""
        return self._cur()["k"] == "="

    def _consume_call_arg_entry_name_token(self) -> dict[str, Any]:
        """call argument entry の `NAME` consume を helper へ寄せる。"""
        return self._eat("NAME")

    def _resolve_call_arg_entry_name_value(self, *, name_tok: dict[str, Any]) -> str:
        """call argument entry の `NAME` value 取得を helper へ寄せる。"""
        return str(name_tok["v"])

    def _apply_call_arg_entry_state(
        self,
        *,
        save_pos: int | None,
        name_tok: dict[str, Any] | None,
        is_keyword: bool,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument 1件分の positional/keyword apply を helper へ寄せる。"""
        if is_keyword and name_tok is not None:
            return self._apply_keyword_call_arg_entry(
                name_tok=name_tok,
            )
        return self._apply_positional_call_arg_entry(
            save_pos=save_pos,
        )

    def _apply_keyword_call_arg_entry(
        self,
        *,
        name_tok: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument 1件分の keyword apply を helper へ寄せる。"""
        kw_name, kw_val = self._resolve_keyword_call_arg_entry_state(name_tok=name_tok)
        return self._apply_keyword_call_arg_build(
            kw_name=kw_name,
            kw_val=kw_val,
        )

    def _apply_keyword_call_arg_build(
        self,
        *,
        kw_name: str,
        kw_val: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument keyword の node build を helper へ寄せる。"""
        return None, _sh_make_keyword_arg(kw_name, kw_val)

    def _resolve_keyword_call_arg_entry_state(
        self,
        *,
        name_tok: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """call argument keyword の name/value state resolve を helper へ寄せる。"""
        self._consume_keyword_call_arg_equals_token()
        kw_val = self._parse_ifexp()
        kw_name = self._resolve_call_arg_entry_name_value(name_tok=name_tok)
        return self._apply_keyword_call_arg_entry_state(
            kw_name=kw_name,
            kw_val=kw_val,
        )

    def _apply_keyword_call_arg_entry_state(
        self,
        *,
        kw_name: str,
        kw_val: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """call argument keyword の state apply を helper へ寄せる。"""
        return kw_name, kw_val

    def _consume_keyword_call_arg_equals_token(self) -> dict[str, Any]:
        """call argument keyword の `=` consume を helper へ寄せる。"""
        return self._eat("=")

    def _apply_positional_call_arg_entry(
        self,
        *,
        save_pos: int | None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument 1件分の positional apply を helper へ寄せる。"""
        self._apply_call_arg_entry_save_pos(save_pos=save_pos)
        arg_expr = self._resolve_positional_call_arg_entry_state()
        return self._apply_positional_call_arg_build_state(arg_expr=arg_expr)

    def _resolve_positional_call_arg_entry_state(self) -> dict[str, Any]:
        """call argument positional の value state resolve を helper へ寄せる。"""
        return self._parse_call_arg_expr()

    def _apply_positional_call_arg_build_state(
        self,
        *,
        arg_expr: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument positional の build state apply を helper へ寄せる。"""
        return self._apply_positional_call_arg_build(arg_expr=arg_expr)

    def _apply_positional_call_arg_build(
        self,
        *,
        arg_expr: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument positional の node build を helper へ寄せる。"""
        return arg_expr, None

    def _apply_call_arg_entry_save_pos(self, *, save_pos: int | None) -> None:
        """call argument positional apply の save_pos 復帰を helper へ寄せる。"""
        if save_pos is not None:
            self.pos = save_pos

    def _apply_call_arg_entry(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        arg_entry: dict[str, Any] | None,
        keyword_entry: dict[str, Any] | None,
    ) -> None:
        """call argument loop の positional/keyword append を helper へ寄せる。"""
        is_keyword_entry = self._resolve_call_arg_loop_entry_kind(keyword_entry=keyword_entry)
        return self._apply_call_arg_loop_entry_kind(
            args=args,
            keywords=keywords,
            arg_entry=arg_entry,
            keyword_entry=keyword_entry,
            is_keyword_entry=is_keyword_entry,
        )

    def _resolve_call_arg_loop_entry_kind(
        self,
        *,
        keyword_entry: dict[str, Any] | None,
    ) -> bool:
        """call argument loop entry の dispatch kind を helper へ寄せる。"""
        return keyword_entry is not None

    def _apply_call_arg_loop_entry_kind(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        arg_entry: dict[str, Any] | None,
        keyword_entry: dict[str, Any] | None,
        is_keyword_entry: bool,
    ) -> None:
        """call argument loop entry の dispatch apply を helper へ寄せる。"""
        has_keyword_entry = self._resolve_call_arg_loop_entry_apply_state(
            is_keyword_entry=is_keyword_entry,
            keyword_entry=keyword_entry,
        )
        return self._apply_call_arg_loop_entry_apply_state(
            args=args,
            keywords=keywords,
            arg_entry=arg_entry,
            keyword_entry=keyword_entry,
            has_keyword_entry=has_keyword_entry,
        )

    def _resolve_call_arg_loop_entry_apply_state(
        self,
        *,
        is_keyword_entry: bool,
        keyword_entry: dict[str, Any] | None,
    ) -> bool:
        """call argument loop entry の keyword apply state を helper へ寄せる。"""
        return is_keyword_entry and keyword_entry is not None

    def _apply_call_arg_loop_entry_apply_state(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        arg_entry: dict[str, Any] | None,
        keyword_entry: dict[str, Any] | None,
        has_keyword_entry: bool,
    ) -> None:
        """call argument loop entry の keyword/positional apply を helper へ寄せる。"""
        if has_keyword_entry and keyword_entry is not None:
            return self._apply_keyword_call_arg_loop_entry(
                keywords=keywords,
                keyword_entry=keyword_entry,
            )
        return self._apply_positional_call_arg_loop_entry(
            args=args,
            arg_entry=arg_entry,
        )

    def _apply_keyword_call_arg_loop_entry(
        self,
        *,
        keywords: list[dict[str, Any]],
        keyword_entry: dict[str, Any],
    ) -> None:
        """call argument loop の keyword append を helper へ寄せる。"""
        return self._apply_keyword_call_arg_loop_entry_build(
            keywords=keywords,
            keyword_entry=keyword_entry,
        )

    def _apply_keyword_call_arg_loop_entry_build(
        self,
        *,
        keywords: list[dict[str, Any]],
        keyword_entry: dict[str, Any],
    ) -> None:
        """call argument loop の keyword node append を helper へ寄せる。"""
        keywords.append(keyword_entry)

    def _apply_positional_call_arg_loop_entry(
        self,
        *,
        args: list[dict[str, Any]],
        arg_entry: dict[str, Any] | None,
    ) -> None:
        """call argument loop の positional append を helper へ寄せる。"""
        has_arg_entry = self._resolve_positional_call_arg_loop_entry_state(arg_entry=arg_entry)
        return self._apply_positional_call_arg_loop_entry_state(
            args=args,
            arg_entry=arg_entry,
            has_arg_entry=has_arg_entry,
        )

    def _resolve_positional_call_arg_loop_entry_state(
        self,
        *,
        arg_entry: dict[str, Any] | None,
    ) -> bool:
        """call argument loop の positional append state を helper へ寄せる。"""
        return arg_entry is not None

    def _apply_positional_call_arg_loop_entry_state(
        self,
        *,
        args: list[dict[str, Any]],
        arg_entry: dict[str, Any] | None,
        has_arg_entry: bool,
    ) -> None:
        """call argument loop の positional append apply を helper へ寄せる。"""
        if has_arg_entry and arg_entry is not None:
            return self._apply_positional_call_arg_loop_entry_build(
                args=args,
                arg_entry=arg_entry,
            )

    def _apply_positional_call_arg_loop_entry_build(
        self,
        *,
        args: list[dict[str, Any]],
        arg_entry: dict[str, Any],
    ) -> None:
        """call argument loop の positional node append を helper へ寄せる。"""
        args.append(arg_entry)

    def _advance_call_arg_loop(self) -> bool:
        """call argument loop の comma/terminator 制御を helper へ寄せる。"""
        has_comma = self._resolve_call_arg_loop_state()
        return self._apply_call_arg_loop_state(has_comma=has_comma)

    def _resolve_call_arg_loop_state(self) -> bool:
        """call argument loop の comma state resolve を helper へ寄せる。"""
        return self._cur()["k"] == ","

    def _apply_call_arg_loop_state(self, *, has_comma: bool) -> bool:
        """call argument loop の comma/terminator apply を helper へ寄せる。"""
        if not has_comma:
            return False
        self._consume_call_arg_loop_comma_token()
        return self._apply_call_arg_loop_continue_state()

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
