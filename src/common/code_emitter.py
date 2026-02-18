"""EAST ベースの言語エミッタ共通基底。"""

from __future__ import annotations

from typing import Any


class CodeEmitter:
    """EAST -> 各言語のコード生成で共通利用する最小基底クラス。"""
    doc: dict[str, Any]
    profile: dict[str, Any]
    hooks: Any
    lines: list[str]
    indent: int
    tmp_id: int
    scope_stack: list[set[str]]

    def __init__(
        self,
        east_doc: dict[str, Any],
        profile: dict[str, Any] | None = None,
        hooks: dict[str, Any] | None = None,
    ) -> None:
        """共通の出力状態と一時変数カウンタを初期化する。"""
        self.doc = east_doc
        self.profile = profile if profile is not None else {}
        self.hooks = hooks if hooks is not None else {}
        self.lines = []
        self.indent = 0
        self.tmp_id = 0
        self.scope_stack = [set()]

    def emit_stmt(self, stmt: Any) -> None:
        """文ノード出力フック。派生クラス側で実装する。"""
        return

    def render_expr(self, expr: Any) -> str:
        """式ノード出力フック。派生クラス側で実装する。"""
        return ""

    def emit(self, line: str = "") -> None:
        """現在のインデントで1行を出力バッファへ追加する。"""
        self.lines.append(("    " * self.indent) + line)

    def emit_stmt_list(self, stmts: list[Any]) -> None:
        for stmt in stmts:
            self.emit_stmt(stmt)  # type: ignore[attr-defined]

    def hook_on_emit_stmt(self, emitter: Any, stmt: dict[str, Any]) -> bool | None:
        """`on_emit_stmt` フック。既定では何もしない。"""
        return None

    def hook_on_render_call(
        self,
        emitter: Any,
        call_node: dict[str, Any],
        func_node: dict[str, Any],
        rendered_args: list[str],
        rendered_kwargs: dict[str, str],
    ) -> str | None:
        """`on_render_call` フック。既定では何もしない。"""
        return None

    def hook_on_render_binop(
        self,
        emitter: Any,
        binop_node: dict[str, Any],
        left: str,
        right: str,
    ) -> str | None:
        """`on_render_binop` フック。既定では何もしない。"""
        return None

    def syntax_text(self, key: str, default_value: str) -> str:
        """profile.syntax からテンプレート文字列を取得する。"""
        syn = self.any_to_dict(self.profile.get("syntax"))
        if syn is None:
            return default_value
        v = syn.get(key)
        if isinstance(v, str) and v != "":
            return v
        return default_value

    def syntax_line(
        self,
        key: str,
        default_value: str,
        values: dict[str, str],
    ) -> str:
        """profile.syntax のテンプレートを format 展開して返す。"""
        text = self.syntax_text(key, default_value)
        out = text
        for k, v in values.items():
            out = out.replace("{" + str(k) + "}", str(v))
        return out

    def next_tmp(self, prefix: str = "__tmp") -> str:
        """衝突しない一時変数名を生成する。"""
        self.tmp_id += 1
        return f"{prefix}_{self.tmp_id}"

    def any_dict_get(self, obj: dict[str, Any] | None, key: str, default_value: Any) -> Any:
        """dict 風入力から key を取得し、失敗時は既定値を返す。"""
        d = obj if isinstance(obj, dict) else None
        if d is None:
            return default_value
        return d.get(key, default_value)

    def any_to_dict(self, v: Any) -> dict[str, Any] | None:
        """動的値を dict に安全に変換する。変換不能なら None。"""
        out: dict[str, Any] | None = None
        if isinstance(v, dict):
            out = v
        return out

    def any_to_dict_or_empty(self, v: Any) -> dict[str, Any]:
        """動的値を dict に安全に変換する。変換不能なら空 dict。"""
        d = self.any_to_dict(v)
        return d if d is not None else {}

    def any_to_list(self, v: Any) -> list[Any]:
        """動的値を list に安全に変換する。変換不能なら空 list。"""
        out: list[Any] = []
        if isinstance(v, list):
            out = v
        return out

    def any_to_str(self, v: Any) -> str:
        """動的値を str に安全に変換する。変換不能なら空文字。"""
        out = ""
        if isinstance(v, str):
            out = v
        return out

    def get_expr_type(self, expr: Any) -> str:
        """式ノードから解決済み型文字列を取得する。"""
        expr_node = self.any_to_dict(expr)
        if expr_node is None:
            return ""
        t = self.any_dict_get(expr_node, "resolved_type", "")
        return t if isinstance(t, str) else ""

    def is_name(self, node: Any, name: str | None = None) -> bool:
        node_dict = self.any_to_dict(node)
        if node_dict is None:
            return False
        if self.any_dict_get(node_dict, "kind", "") != "Name":
            return False
        if name is None:
            return True
        return str(self.any_dict_get(node_dict, "id", "")) == name

    def is_call(self, node: Any) -> bool:
        node_dict = self.any_to_dict(node)
        if node_dict is None:
            return False
        return self.any_dict_get(node_dict, "kind", "") == "Call"

    def is_attr(self, node: Any, attr: str | None = None) -> bool:
        node_dict = self.any_to_dict(node)
        if node_dict is None:
            return False
        if self.any_dict_get(node_dict, "kind", "") != "Attribute":
            return False
        if attr is None:
            return True
        return str(self.any_dict_get(node_dict, "attr", "")) == attr

    def split_generic(self, s: str) -> list[str]:
        if s == "":
            return []
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

    def split_union(self, s: str) -> list[str]:
        out: list[str] = []
        depth = 0
        start = 0
        for i, ch in enumerate(s):
            if ch in {"[", "("}:
                depth += 1
            elif ch in {"]", ")"}:
                depth -= 1
            elif ch == "|" and depth == 0:
                part = s[start:i].strip()
                if part != "":
                    out.append(part)
                start = i + 1
        tail = s[start:].strip()
        if tail != "":
            out.append(tail)
        return out

    def normalize_type_name(self, t: Any) -> str:
        """型名エイリアスを内部表現へ正規化する。"""
        if not isinstance(t, str):
            return ""
        s = str(t)
        if s == "byte":
            return "uint8"
        if s == "any":
            return "Any"
        if s == "object":
            return "object"
        return s

    def is_any_like_type(self, t: Any) -> bool:
        """Any 同等（Any/object/unknown/Union 含む）型か判定する。"""
        s = self.normalize_type_name(t)
        if s == "":
            return False
        if s in {"Any", "object", "unknown"}:
            return True
        if "|" in s:
            parts = self.split_union(s)
            if len(parts) == 1 and parts[0] == s:
                return False
            return any(self.is_any_like_type(p) for p in parts if p != "None" and p != s)
        return False

    def is_list_type(self, t: Any) -> bool:
        """型文字列が list[...] かを返す。"""
        if not isinstance(t, str):
            return False
        return t[:5] == "list["

    def is_set_type(self, t: Any) -> bool:
        """型文字列が set[...] かを返す。"""
        if not isinstance(t, str):
            return False
        return t[:4] == "set["

    def is_dict_type(self, t: Any) -> bool:
        """型文字列が dict[...] かを返す。"""
        if not isinstance(t, str):
            return False
        return t[:5] == "dict["

    def is_indexable_sequence_type(self, t: Any) -> bool:
        """添字アクセス可能なシーケンス型か判定する。"""
        if not isinstance(t, str):
            return False
        return t[:5] == "list[" or t in {"str", "bytes", "bytearray"}

    def _is_forbidden_object_receiver_type_text(self, s: str) -> bool:
        """object レシーバ禁止ルールに抵触する型文字列か判定する。"""
        if s in {"Any", "object", "any"}:
            return True
        if "|" in s:
            parts = self.split_union(s)
            for p in parts:
                if p == "None":
                    continue
                if p in {"Any", "object", "any"}:
                    return True
            return False
        return False

    def is_forbidden_object_receiver_type(self, t: Any) -> bool:
        """object レシーバ禁止ルールに抵触する型か判定する。"""
        s = self.normalize_type_name(t)
        return self._is_forbidden_object_receiver_type_text(s)

    def current_scope(self) -> set[str]:
        """現在のスコープで宣言済みの識別子集合を返す。"""
        return self.scope_stack[-1]

    def is_declared(self, name: str) -> bool:
        """指定名がどこかの有効スコープで宣言済みか判定する。"""
        i = len(self.scope_stack) - 1
        while i >= 0:
            scope: set[str] = self.scope_stack[i]
            if name in scope:
                return True
            i -= 1
        return False

    def _is_identifier_expr(self, text: str) -> bool:
        """式文字列が単純な識別子のみかを判定する。"""
        if len(text) == 0:
            return False
        c0 = text[0:1]
        if not (c0 == "_" or ("a" <= c0 <= "z") or ("A" <= c0 <= "Z")):
            return False
        i = 1
        while i < len(text):
            ch = text[i]
            if not (ch == "_" or ("a" <= ch <= "z") or ("A" <= ch <= "Z") or ("0" <= ch <= "9")):
                return False
            i += 1
        return True

    def _strip_outer_parens(self, text: str) -> str:
        """式全体を囲う不要な最外括弧を安全に取り除く。"""
        s: str = text
        ws: set[str] = {" ", "\t", "\n", "\r", "\f", "\v"}
        while len(s) > 0 and s[0] in ws:
            s = s[1:]
        while len(s) > 0 and s[-1] in ws:
            s = s[:-1]

        while len(s) >= 2 and s[:1] == "(" and s[-1:] == ")":
            depth = 0
            in_str = False
            esc = False
            quote = ""
            wrapped = True
            i = 0
            while i < len(s):
                ch = s[i]
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == quote:
                        in_str = False
                    i += 1
                    continue
                if ch == "'" or ch == '"':
                    in_str = True
                    quote = ch
                    i += 1
                    continue
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0 and i != len(s) - 1:
                        wrapped = False
                        break
                i += 1
            if wrapped and depth == 0:
                s = s[1:-1]
                while len(s) > 0 and s[0] in ws:
                    s = s[1:]
                while len(s) > 0 and s[-1] in ws:
                    s = s[:-1]
                continue
            break
        return s

    def is_plain_name_expr(self, expr: dict[str, Any] | None) -> bool:
        """式が単純な Name ノードかを判定する。"""
        if expr is None:
            return False
        return self.any_dict_get(expr, "kind", "") == "Name"

    def _expr_repr_eq(self, a: dict[str, Any] | None, b: dict[str, Any] | None) -> bool:
        """2つの式 repr が同一かを比較する。"""
        if not isinstance(a, dict) or not isinstance(b, dict):
            return False
        ra = self.any_dict_get(a, "repr", "")
        rb = self.any_dict_get(b, "repr", "")
        if not isinstance(ra, str) or not isinstance(rb, str):
            return False
        return self._trim_ws(ra) == self._trim_ws(rb)

    def _trim_ws(self, text: str) -> str:
        """先頭末尾の空白を除いた文字列を返す。"""
        s = text
        ws: set[str] = {" ", "\t", "\n", "\r", "\f", "\v"}
        while len(s) > 0 and s[0] in ws:
            s = s[1:]
        while len(s) > 0 and s[-1] in ws:
            s = s[:-1]
        return s

    def comment_line_prefix(self) -> str:
        """単行コメント出力時の接頭辞を返す。"""
        return "// "

    def truthy_len_expr(self, rendered: str) -> str:
        """シーケンス真偽判定に使う式を返す。"""
        return f"py_len({rendered}) != 0"

    def emit_leading_comments(self, stmt: dict[str, Any]) -> None:
        """EAST の leading_trivia をコメント/空行として出力する。"""
        trivia = self.any_dict_get(stmt, "leading_trivia", [])
        if not isinstance(trivia, list):
            return
        for item in trivia:
            if not isinstance(item, dict):
                continue
            k = self.any_dict_get(item, "kind", "")
            if k == "comment":
                txt = self.any_dict_get(item, "text", "")
                if isinstance(txt, str):
                    self.emit(self.comment_line_prefix() + txt)
            elif k == "blank":
                cnt = self.any_dict_get(item, "count", 1)
                n = int(cnt) if isinstance(cnt, int) and cnt > 0 else 1
                for _ in range(n):
                    self.emit("")

    def emit_module_leading_trivia(self) -> None:
        """モジュール先頭のコメント/空行 trivia を出力する。"""
        trivia = self.any_dict_get(self.doc, "module_leading_trivia", [])
        if not isinstance(trivia, list):
            return
        for item in trivia:
            if not isinstance(item, dict):
                continue
            k = self.any_dict_get(item, "kind", "")
            if k == "comment":
                txt = self.any_dict_get(item, "text", "")
                if isinstance(txt, str):
                    self.emit(self.comment_line_prefix() + txt)
            elif k == "blank":
                cnt = self.any_dict_get(item, "count", 1)
                n = int(cnt) if isinstance(cnt, int) and cnt > 0 else 1
                for _ in range(n):
                    self.emit("")

    def _is_negative_const_index(self, node: dict[str, Any] | None) -> bool:
        """添字ノードが負の定数インデックスかを判定する。"""
        if node is None:
            return False
        kind = str(self.any_dict_get(node, "kind", ""))
        if kind == "Constant":
            v = self.any_dict_get(node, "value", None)
            if isinstance(v, int):
                return int(v) < 0
            if isinstance(v, str):
                try:
                    return int(v) < 0
                except ValueError:
                    return False
            return False
        if kind == "UnaryOp" and self.any_dict_get(node, "op", "") == "USub":
            opd = self.any_to_dict_or_empty(self.any_dict_get(node, "operand", None))
            if self.any_dict_get(opd, "kind", "") == "Constant":
                ov = self.any_dict_get(opd, "value", None)
                if isinstance(ov, int):
                    return int(ov) > 0
                if isinstance(ov, str):
                    try:
                        return int(ov) > 0
                    except ValueError:
                        return False
        return False

    def _is_redundant_super_init_call(self, expr: dict[str, Any] | None) -> bool:
        """暗黙基底 ctor 呼び出しと等価な super().__init__ かを判定する。"""
        if expr is None or self.any_dict_get(expr, "kind", "") != "Call":
            return False
        func = self.any_to_dict_or_empty(self.any_dict_get(expr, "func", None))
        if self.any_dict_get(func, "kind", "") != "Attribute":
            return False
        if str(self.any_dict_get(func, "attr", "")) != "__init__":
            return False
        owner = self.any_to_dict_or_empty(self.any_dict_get(func, "value", None))
        if self.any_dict_get(owner, "kind", "") != "Call":
            return False
        owner_func = self.any_to_dict_or_empty(self.any_dict_get(owner, "func", None))
        if self.any_dict_get(owner_func, "kind", "") != "Name":
            return False
        if str(self.any_dict_get(owner_func, "id", "")) != "super":
            return False
        args = self.any_dict_get(expr, "args", [])
        kws = self.any_dict_get(expr, "keywords", [])
        return isinstance(args, list) and len(args) == 0 and isinstance(kws, list) and len(kws) == 0

    def render_cond(self, expr: Any) -> str:
        """条件式文脈向けに式を真偽値へ正規化して出力する。"""
        expr_node = self.any_to_dict(expr)
        if expr_node is None:
            return "false"
        t = self.get_expr_type(expr_node)
        body = self._strip_outer_parens(self.render_expr(expr_node))
        if t in {"bool"}:
            return body
        if t == "str" or t[:5] == "list[" or t[:5] == "dict[" or t[:4] == "set[" or t[:6] == "tuple[":
            return self.truthy_len_expr(body)
        return body


# Backward compatibility for staged migration.
BaseEmitter = CodeEmitter
