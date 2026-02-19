"""EAST ベースの言語エミッタ共通基底。"""

from __future__ import annotations

from pylib.typing import Any


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
        east_doc: dict[str, Any] = {},
        profile: dict[str, Any] = {},
        hooks: dict[str, Any] = {},
    ) -> None:
        """共通の出力状態と一時変数カウンタを初期化する。"""
        self.doc = east_doc
        self.profile = profile
        self.hooks = hooks
        self.lines = self._empty_lines()
        self.indent = 0
        self.tmp_id = 0
        self.scope_stack = self._root_scope_stack()

    def _empty_lines(self) -> list[str]:
        """空の `list[str]` を返す。"""
        out: list[str] = []
        return out

    def _root_scope_stack(self) -> list[set[str]]:
        """最上位 1 スコープだけを持つ初期スコープスタックを返す。"""
        return [set()]

    def emit_stmt(self, stmt: dict[str, Any]) -> None:
        """文ノード出力フック。派生クラス側で実装する。"""
        return

    def render_expr(self, expr: Any) -> str:
        """式ノード出力フック。派生クラス側で実装する。"""
        return ""

    def emit(self, line: str = "") -> None:
        """現在のインデントで1行を出力バッファへ追加する。"""
        self.lines.append(("    " * self.indent) + line)

    def emit_stmt_list(self, stmts: list[dict[str, Any]]) -> None:
        for stmt in stmts:
            self.emit_stmt(stmt)  # type: ignore[attr-defined]

    def hook_on_emit_stmt(self, stmt: dict[str, Any]) -> bool | None:
        """`on_emit_stmt` フック。既定では何もしない。"""
        return None

    def hook_on_emit_stmt_kind(
        self,
        kind: str,
        stmt: dict[str, Any],
    ) -> bool | None:
        """`on_emit_stmt_kind` フック。既定では何もしない。"""
        return None

    def hook_on_render_call(
        self,
        call_node: dict[str, Any],
        func_node: dict[str, Any],
        rendered_args: list[str],
        rendered_kwargs: dict[str, str],
    ) -> str | None:
        """`on_render_call` フック。既定では何もしない。"""
        return None

    def hook_on_render_binop(
        self,
        binop_node: dict[str, Any],
        left: str,
        right: str,
    ) -> str | None:
        """`on_render_binop` フック。既定では何もしない。"""
        return None

    def hook_on_render_expr_kind(
        self,
        kind: str,
        expr_node: dict[str, Any],
    ) -> str | None:
        """`on_render_expr_kind` フック。既定では何もしない。"""
        return None

    def hook_on_render_expr_complex(
        self,
        expr_node: dict[str, Any],
    ) -> str | None:
        """複雑式（JoinedStr/Lambda/Comp 系）用フック。既定では何もしない。"""
        return None

    def syntax_text(self, key: str, default_value: str) -> str:
        """profile.syntax からテンプレート文字列を取得する。"""
        syn = self.any_to_dict_or_empty(self.profile.get("syntax"))
        v = self.any_dict_get_str(syn, key, default_value)
        if v != "":
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

    def emit_function_open(self, ret: str, name: str, args: str) -> None:
        """関数ブロック開始行を出力する。"""
        self.emit(
            self.syntax_line(
                "function_open",
                "{ret} {name}({args}) {",
                {"ret": ret, "name": name, "args": args},
            )
        )

    def emit_ctor_open(self, name: str, args: str) -> None:
        """コンストラクタ開始行を出力する。"""
        self.emit(self.syntax_line("ctor_open", "{name}({args}) {", {"name": name, "args": args}))

    def emit_dtor_open(self, name: str) -> None:
        """デストラクタ開始行を出力する。"""
        self.emit(self.syntax_line("dtor_open", "~{name}() {", {"name": name}))

    def emit_class_open(self, name: str, base_txt: str) -> None:
        """クラス/構造体開始行を出力する。"""
        self.emit(self.syntax_line("class_open", "struct {name}{base_txt} {", {"name": name, "base_txt": base_txt}))

    def emit_class_close(self) -> None:
        """クラス/構造体終端行を出力する。"""
        self.emit(self.syntax_text("class_close", "};"))

    def emit_block_close(self) -> None:
        """汎用ブロック終端行を出力する。"""
        self.emit(self.syntax_text("block_close", "}"))

    def emit_scoped_stmt_list(self, stmts: list[dict[str, Any]], scope_names: Any = None) -> None:
        """現在 indent 位置でスコープを1段積み、文リストを出力する。"""
        self.indent += 1
        next_scope: set[str] = set()
        if isinstance(scope_names, set):
            next_scope = scope_names
        self.scope_stack.append(next_scope)
        self.emit_stmt_list(stmts)
        self.scope_stack.pop()
        self.indent -= 1

    def emit_with_scope(self, scope_names: Any, body_fn: Any) -> None:
        """現在 indent 位置でスコープを1段積み、文リスト本体を出力する。"""
        self.indent += 1
        next_scope: set[str] = set()
        if isinstance(scope_names, set):
            next_scope = scope_names
        self.scope_stack.append(next_scope)
        if isinstance(body_fn, list):
            for stmt in self.any_to_list(body_fn):
                self.emit_stmt(stmt)  # type: ignore[arg-type]
        self.scope_stack.pop()
        self.indent -= 1

    def emit_scoped_block(self, open_line: str, stmts: list[dict[str, Any]], scope_names: Any = None) -> None:
        """`open_line` を出力し、スコープ付きで文リストを出して block を閉じる。"""
        self.emit(open_line)
        self.emit_scoped_stmt_list(stmts, scope_names)
        self.emit_block_close()

    def next_tmp(self, prefix: str = "__tmp") -> str:
        """衝突しない一時変数名を生成する。"""
        self.tmp_id += 1
        return f"{prefix}_{self.tmp_id}"

    def any_dict_get(self, obj: dict[str, Any], key: str, default_value: Any) -> Any:
        """dict 風入力から key を取得し、失敗時は既定値を返す。"""
        if not isinstance(obj, dict):
            return default_value
        if key in obj:
            return obj[key]
        return default_value

    def any_dict_has(self, obj: dict[str, Any], key: str) -> bool:
        """dict 風入力が key を持つか判定する。"""
        if not isinstance(obj, dict):
            return False
        return key in obj

    def any_dict_get_str(self, obj: dict[str, Any], key: str, default_value: str = "") -> str:
        """dict 風入力から文字列を取得し、失敗時は既定値を返す。"""
        if not isinstance(obj, dict):
            return default_value
        if key not in obj:
            return default_value
        v = obj[key]
        return v if isinstance(v, str) else default_value

    def any_dict_get_int(self, obj: dict[str, Any], key: str, default_value: int = 0) -> int:
        """dict 風入力から整数を取得し、失敗時は既定値を返す。"""
        if not isinstance(obj, dict):
            return default_value
        if key not in obj:
            return default_value
        v = obj[key]
        if isinstance(v, int):
            return int(v)
        return default_value

    def any_dict_get_bool(self, obj: dict[str, Any], key: str, default_value: bool = False) -> bool:
        """dict 風入力から真偽値を取得し、失敗時は既定値を返す。"""
        if not isinstance(obj, dict):
            return default_value
        if key not in obj:
            return default_value
        v = obj[key]
        if isinstance(v, bool):
            return bool(v)
        return default_value

    def any_dict_get_list(self, obj: dict[str, Any], key: str) -> list[Any]:
        """dict 風入力から list を取得し、失敗時は空 list を返す。"""
        if not isinstance(obj, dict):
            return []
        if key not in obj:
            return []
        v = obj[key]
        if isinstance(v, list):
            return v
        return []

    def any_dict_get_dict(self, obj: dict[str, Any], key: str) -> dict[str, Any]:
        """dict 風入力から dict を取得し、失敗時は空 dict を返す。"""
        if not isinstance(obj, dict):
            return {}
        if key not in obj:
            return {}
        v = obj[key]
        if isinstance(v, dict):
            return v
        return {}

    def any_to_dict(self, v: Any) -> dict[str, Any] | None:
        """動的値を dict に安全に変換する。変換不能なら None。"""
        if isinstance(v, dict):
            return v
        return None

    def any_to_dict_or_empty(self, v: Any) -> dict[str, Any]:
        """動的値を dict に安全に変換する。変換不能なら空 dict。"""
        if isinstance(v, dict):
            return v
        return {}

    def any_to_list(self, v: Any) -> list[Any]:
        """動的値を list に安全に変換する。変換不能なら空 list。"""
        out: list[Any] = []
        if isinstance(v, list):
            out = v
        return out

    def any_to_dict_list(self, v: Any) -> list[dict[str, Any]]:
        """動的値を `list[dict]` へ安全に変換する。"""
        out: list[dict[str, Any]] = []
        for item in self.any_to_list(v):
            if isinstance(item, dict):
                out.append(item)
        return out

    def any_to_str(self, v: Any) -> str:
        """動的値を str に安全に変換する。変換不能なら空文字。"""
        out = ""
        if isinstance(v, str):
            out = v
        return out

    def any_to_bool(self, v: Any) -> bool:
        """動的値を bool に安全に変換する。変換不能なら False。"""
        if isinstance(v, bool):
            return bool(v)
        return False

    def get_expr_type(self, expr: Any) -> str:
        """式ノードから解決済み型文字列を取得する。"""
        expr_node = self.any_to_dict_or_empty(expr)
        return self.any_dict_get_str(expr_node, "resolved_type", "")

    def is_name(self, node: Any, name: str | None = None) -> bool:
        node_dict = self.any_to_dict_or_empty(node)
        if self.any_dict_get_str(node_dict, "kind", "") != "Name":
            return False
        if name is None:
            return True
        return self.any_dict_get_str(node_dict, "id", "") == name

    def is_call(self, node: Any) -> bool:
        node_dict = self.any_to_dict_or_empty(node)
        return self.any_dict_get_str(node_dict, "kind", "") == "Call"

    def is_attr(self, node: Any, attr: str | None = None) -> bool:
        node_dict = self.any_to_dict_or_empty(node)
        if self.any_dict_get_str(node_dict, "kind", "") != "Attribute":
            return False
        if attr is None:
            return True
        return self.any_dict_get_str(node_dict, "attr", "") == attr

    def split_generic(self, s: str) -> list[str]:
        if s == "":
            out0: list[str] = []
            return out0
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
            if ch == "[" or ch == "(":
                depth += 1
            elif ch == "]" or ch == ")":
                depth -= 1
            elif ch == "|" and depth == 0:
                part: str = s[start:i].strip()
                if part != "":
                    out.append(part)
                start = i + 1
        tail: str = s[start:].strip()
        if tail != "":
            out.append(tail)
        return out

    def normalize_type_name(self, t: str) -> str:
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

    def is_any_like_type(self, t: str) -> bool:
        """Any 同等（Any/object/unknown/Union 含む）型か判定する。"""
        s = self.normalize_type_name(t)
        if s == "":
            return False
        if s == "Any" or s == "object" or s == "unknown":
            return True
        if s.find("|") != -1:
            parts = self.split_union(s)
            if len(parts) == 1 and parts[0] == s:
                return False
            return any(self.is_any_like_type(p) for p in parts if p != "None" and p != s)
        return False

    def is_list_type(self, t: str) -> bool:
        """型文字列が list[...] かを返す。"""
        return t[:5] == "list["

    def is_set_type(self, t: str) -> bool:
        """型文字列が set[...] かを返す。"""
        return t[:4] == "set["

    def is_dict_type(self, t: str) -> bool:
        """型文字列が dict[...] かを返す。"""
        return t[:5] == "dict["

    def is_indexable_sequence_type(self, t: str) -> bool:
        """添字アクセス可能なシーケンス型か判定する。"""
        return t[:5] == "list[" or t == "str" or t == "bytes" or t == "bytearray"

    def _is_forbidden_object_receiver_type_text(self, s: str) -> bool:
        """object レシーバ禁止ルールに抵触する型文字列か判定する。"""
        if s == "Any" or s == "object" or s == "any":
            return True
        if s.find("|") != -1:
            parts = self.split_union(s)
            for p in parts:
                if p == "None":
                    continue
                if p == "Any" or p == "object" or p == "any":
                    return True
            return False
        return False

    def is_forbidden_object_receiver_type(self, t: str) -> bool:
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
        for ch in text[1:]:
            if not (ch == "_" or ("a" <= ch <= "z") or ("A" <= ch <= "Z") or ("0" <= ch <= "9")):
                return False
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
            for i, ch in enumerate(s):
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == quote:
                        in_str = False
                    continue
                if ch == "'" or ch == '"':
                    in_str = True
                    quote = ch
                    continue
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0 and i != len(s) - 1:
                        wrapped = False
                        break
            if wrapped and depth == 0:
                s = s[1:-1]
                while len(s) > 0 and s[0] in ws:
                    s = s[1:]
                while len(s) > 0 and s[-1] in ws:
                    s = s[:-1]
                continue
            break
        return s

    def is_plain_name_expr(self, expr: Any) -> bool:
        """式が単純な Name ノードかを判定する。"""
        d = self.any_to_dict_or_empty(expr)
        return self.any_dict_get_str(d, "kind", "") == "Name"

    def _expr_repr_eq(self, a: Any, b: Any) -> bool:
        """2つの式 repr が同一かを比較する。"""
        da = self.any_to_dict_or_empty(a)
        db = self.any_to_dict_or_empty(b)
        if len(da) == 0 or len(db) == 0:
            return False
        ra = self.any_dict_get_str(da, "repr", "")
        rb = self.any_dict_get_str(db, "repr", "")
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
        if "leading_trivia" not in stmt:
            return
        trivia = self.any_to_dict_list(stmt["leading_trivia"])
        if len(trivia) == 0:
            return
        for item in trivia:
            k = self.any_dict_get_str(item, "kind", "")
            if k == "comment":
                txt = self.any_dict_get_str(item, "text", "")
                self.emit(self.comment_line_prefix() + txt)
            elif k == "blank":
                cnt = self.any_dict_get_int(item, "count", 1)
                n = cnt if cnt > 0 else 1
                for _ in range(n):
                    self.emit("")

    def emit_module_leading_trivia(self) -> None:
        """モジュール先頭のコメント/空行 trivia を出力する。"""
        if "module_leading_trivia" not in self.doc:
            return
        trivia = self.any_to_dict_list(self.doc["module_leading_trivia"])
        if len(trivia) == 0:
            return
        for item in trivia:
            k = self.any_dict_get_str(item, "kind", "")
            if k == "comment":
                txt = self.any_dict_get_str(item, "text", "")
                self.emit(self.comment_line_prefix() + txt)
            elif k == "blank":
                cnt = self.any_dict_get_int(item, "count", 1)
                n = cnt if cnt > 0 else 1
                for _ in range(n):
                    self.emit("")

    def _is_negative_const_index(self, node: Any) -> bool:
        """添字ノードが負の定数インデックスかを判定する。"""
        node_dict = self.any_to_dict_or_empty(node)
        if len(node_dict) == 0:
            return False
        kind = self.any_dict_get_str(node_dict, "kind", "")
        if kind == "Constant":
            if not self.any_dict_has(node_dict, "value"):
                return False
            v = node_dict["value"]
            if isinstance(v, int):
                return int(v) < 0
            if isinstance(v, str):
                try:
                    return int(v) < 0
                except ValueError:
                    return False
            return False
        if kind == "UnaryOp" and self.any_dict_get_str(node_dict, "op", "") == "USub":
            if not self.any_dict_has(node_dict, "operand"):
                return False
            opd = self.any_to_dict_or_empty(node_dict["operand"])
            if self.any_dict_get_str(opd, "kind", "") == "Constant":
                if not self.any_dict_has(opd, "value"):
                    return False
                ov = opd["value"]
                if isinstance(ov, int):
                    return int(ov) > 0
                if isinstance(ov, str):
                    try:
                        return int(ov) > 0
                    except ValueError:
                        return False
        return False

    def _is_redundant_super_init_call(self, expr: Any) -> bool:
        """暗黙基底 ctor 呼び出しと等価な super().__init__ かを判定する。"""
        expr_dict = self.any_to_dict_or_empty(expr)
        if len(expr_dict) == 0 or self.any_dict_get_str(expr_dict, "kind", "") != "Call":
            return False
        if not self.any_dict_has(expr_dict, "func"):
            return False
        func = self.any_to_dict_or_empty(expr_dict["func"])
        if self.any_dict_get_str(func, "kind", "") != "Attribute":
            return False
        if self.any_dict_get_str(func, "attr", "") != "__init__":
            return False
        if not self.any_dict_has(func, "value"):
            return False
        owner = self.any_to_dict_or_empty(func["value"])
        if self.any_dict_get_str(owner, "kind", "") != "Call":
            return False
        if not self.any_dict_has(owner, "func"):
            return False
        owner_func = self.any_to_dict_or_empty(owner["func"])
        if self.any_dict_get_str(owner_func, "kind", "") != "Name":
            return False
        if self.any_dict_get_str(owner_func, "id", "") != "super":
            return False
        args: Any = None
        kws: Any = None
        if self.any_dict_has(expr_dict, "args"):
            args = expr_dict["args"]
        if self.any_dict_has(expr_dict, "keywords"):
            kws = expr_dict["keywords"]
        return isinstance(args, list) and len(args) == 0 and isinstance(kws, list) and len(kws) == 0

    def render_cond(self, expr: Any) -> str:
        """条件式文脈向けに式を真偽値へ正規化して出力する。"""
        expr_node = self.any_to_dict_or_empty(expr)
        if len(expr_node) == 0:
            return "false"
        t = self.get_expr_type(expr)
        body = self._strip_outer_parens(self.render_expr(expr))
        if t == "bool":
            return body
        if t == "str" or t[:5] == "list[" or t[:5] == "dict[" or t[:4] == "set[" or t[:6] == "tuple[":
            return self.truthy_len_expr(body)
        return body
