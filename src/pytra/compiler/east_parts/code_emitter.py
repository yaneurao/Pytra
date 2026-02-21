"""EAST ベースの言語エミッタ共通基底。"""

from __future__ import annotations

from pytra.std.typing import Any


class CodeEmitter:
    """EAST -> 各言語のコード生成で共通利用する最小基底クラス。"""
    doc: dict[str, Any]
    profile: dict[str, Any]
    hooks: dict[str, Any]
    lines: list[str]
    indent: int
    tmp_id: int
    scope_stack: list[set[str]]
    passthrough_cpp_block: bool

    def __init__(
        self,
        east_doc: dict[str, Any] = {},
        profile: dict[str, Any] = {},
        hooks: dict[str, Any] = {},
    ) -> None:
        """共通の出力状態と一時変数カウンタを初期化する。"""
        self.init_base_state(east_doc, profile, hooks)

    def init_base_state(
        self,
        east_doc: dict[str, Any],
        profile: dict[str, Any],
        hooks: dict[str, Any],
    ) -> None:
        """基底状態（doc/profile/hooks/出力バッファ）を再初期化する。"""
        self.doc = east_doc
        self.profile = profile
        self.hooks = hooks
        self.lines = self._empty_lines()
        self.indent = 0
        self.tmp_id = 0
        self.scope_stack = self._root_scope_stack()
        self.passthrough_cpp_block = False

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

    def merge_call_args(self, args: list[str], kw: dict[str, str]) -> list[str]:
        """`args + keyword values` の結合結果を返す。"""
        if len(kw) == 0:
            return args
        out: list[str] = []
        i = 0
        while i < len(args):
            out.append(args[i])
            i += 1
        kw_keys: list[str] = []
        for key in kw:
            if isinstance(key, str):
                kw_keys.append(key)
        k = 0
        while k < len(kw_keys):
            key = kw_keys[k]
            out.append(kw[key])
            k += 1
        return out

    def hook_on_emit_stmt(self, stmt: dict[str, Any]) -> bool | None:
        """`on_emit_stmt` フック。既定では何もしない。"""
        if "on_emit_stmt" in self.hooks:
            fn = self.hooks["on_emit_stmt"]
            if fn is not None:
                return fn(self, stmt)
        return None

    def hook_on_emit_stmt_kind(
        self,
        kind: str,
        stmt: dict[str, Any],
    ) -> bool | None:
        """`on_emit_stmt_kind` フック。既定では何もしない。"""
        if "on_emit_stmt_kind" in self.hooks:
            fn = self.hooks["on_emit_stmt_kind"]
            if fn is not None:
                return fn(self, kind, stmt)
        return None

    def hook_on_render_call(
        self,
        call_node: dict[str, Any],
        func_node: dict[str, Any],
        rendered_args: list[str],
        rendered_kwargs: dict[str, str],
    ) -> str:
        """`on_render_call` フック。既定では何もしない。"""
        if "on_render_call" in self.hooks:
            fn = self.hooks["on_render_call"]
            if fn is not None:
                v = fn(self, call_node, func_node, rendered_args, rendered_kwargs)
                if isinstance(v, str):
                    return v
        return ""

    def hook_on_render_binop(
        self,
        binop_node: dict[str, Any],
        left: str,
        right: str,
    ) -> str:
        """`on_render_binop` フック。既定では何もしない。"""
        if "on_render_binop" in self.hooks:
            fn = self.hooks["on_render_binop"]
            if fn is not None:
                v = fn(self, binop_node, left, right)
                if isinstance(v, str):
                    return v
        return ""

    def hook_on_render_expr_kind(
        self,
        kind: str,
        expr_node: dict[str, Any],
    ) -> str:
        """`on_render_expr_kind` フック。既定では何もしない。"""
        if "on_render_expr_kind" in self.hooks:
            fn = self.hooks["on_render_expr_kind"]
            if fn is not None:
                v = fn(self, kind, expr_node)
                if isinstance(v, str):
                    return v
        return ""

    def hook_on_render_expr_complex(
        self,
        expr_node: dict[str, Any],
    ) -> str:
        """複雑式（JoinedStr/Lambda/Comp 系）用フック。既定では何もしない。"""
        if "on_render_expr_complex" in self.hooks:
            fn = self.hooks["on_render_expr_complex"]
            if fn is not None:
                v = fn(self, expr_node)
                if isinstance(v, str):
                    return v
        return ""

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

    def emit_scoped_stmt_list(self, stmts: list[dict[str, Any]], scope_names: set[str]) -> None:
        """現在 indent 位置でスコープを1段積み、文リストを出力する。"""
        self.indent += 1
        self.scope_stack.append(scope_names)
        self.emit_stmt_list(stmts)
        self.scope_stack.pop()
        self.indent -= 1

    def emit_with_scope(self, scope_names: set[str], body_fn: list[Any]) -> None:
        """現在 indent 位置でスコープを1段積み、文リスト本体を出力する。"""
        self.indent += 1
        self.scope_stack.append(scope_names)
        for stmt in body_fn:
            self.emit_stmt(stmt)  # type: ignore[arg-type]
        self.scope_stack.pop()
        self.indent -= 1

    def emit_scoped_block(self, open_line: str, stmts: list[dict[str, Any]], scope_names: set[str]) -> None:
        """`open_line` を出力し、スコープ付きで文リストを出して block を閉じる。"""
        self.emit(open_line)
        self.emit_scoped_stmt_list(stmts, scope_names)
        self.emit_block_close()

    def next_tmp(self, prefix: str = "__tmp") -> str:
        """衝突しない一時変数名を生成する。"""
        self.tmp_id += 1
        return f"{prefix}_{self.tmp_id}"

    def rename_if_reserved(
        self,
        name: str,
        reserved_words: set[str],
        rename_prefix: str,
        renamed_symbols: dict[str, str],
    ) -> str:
        """予約語衝突時のリネーム結果を返し、必要ならキャッシュへ保存する。"""
        if name in renamed_symbols:
            return renamed_symbols[name]
        if name in reserved_words:
            return f"{rename_prefix}{name}"
        return name

    def render_name_ref(
        self,
        node_dict: dict[str, Any],
        reserved_words: set[str],
        rename_prefix: str,
        renamed_symbols: dict[str, str],
        default_name: str = "_",
    ) -> str:
        """Name ノードから識別子を取り出し、予約語衝突を避けて返す。"""
        name = self.any_dict_get_str(node_dict, "id", "")
        if name == "" and "id" in node_dict:
            raw = node_dict["id"]
            if raw is not None:
                if not isinstance(raw, bool) and not isinstance(raw, int) and not isinstance(raw, float):
                    if not isinstance(raw, dict) and not isinstance(raw, list) and not isinstance(raw, set):
                        raw_txt = str(raw)
                        if raw_txt not in {"", "None", "{}", "[]"}:
                            name = raw_txt
        if name == "":
            name = default_name
        return self.rename_if_reserved(name, reserved_words, rename_prefix, renamed_symbols)

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
        if isinstance(v, str):
            s = self.any_to_str(v)
            if s != "":
                return s
            return default_value
        if v is None:
            return default_value
        if isinstance(v, bool) or isinstance(v, int) or isinstance(v, float):
            return default_value
        if isinstance(v, dict) or isinstance(v, list) or isinstance(v, set):
            return default_value
        s2 = str(v)
        if s2 == "" or s2 == "None":
            return default_value
        return s2

    def any_dict_get_int(self, obj: dict[str, Any], key: str, default_value: int = 0) -> int:
        """dict 風入力から整数を取得し、失敗時は既定値を返す。"""
        if not isinstance(obj, dict):
            return default_value
        if key not in obj:
            return default_value
        v = obj[key]
        if isinstance(v, bool):
            if bool(v):
                return 1
            return 0
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
        if not isinstance(v, list):
            return []
        return self.any_to_list(v)

    def any_dict_get_dict(self, obj: dict[str, Any], key: str) -> dict[str, Any]:
        """dict 風入力から dict を取得し、失敗時は空 dict を返す。"""
        if not isinstance(obj, dict):
            return {}
        if key not in obj:
            return {}
        v = obj[key]
        if not isinstance(v, dict):
            return {}
        return self.any_to_dict_or_empty(v)

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

    def any_to_str_list(self, v: Any) -> list[str]:
        """動的値を `list[str]` へ安全に変換する。"""
        out: list[str] = []
        for item in self.any_to_list(v):
            s = self.any_to_str(item)
            if s == "" and item is not None:
                s = str(item)
            if s != "":
                out.append(s)
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
        if isinstance(v, str):
            return v
        if v is None:
            return ""
        if isinstance(v, bool) or isinstance(v, int) or isinstance(v, float):
            return ""
        if isinstance(v, dict) or isinstance(v, list) or isinstance(v, set):
            return ""
        txt = str(v)
        if txt in {"", "None", "{}", "[]"}:
            return ""
        return txt

    def any_to_bool(self, v: Any) -> bool:
        """動的値を bool に安全に変換する。変換不能なら False。"""
        if isinstance(v, bool):
            return bool(v)
        return False

    def get_expr_type(self, expr: Any) -> str:
        """式ノードから解決済み型文字列を取得する。"""
        expr_node = self.any_to_dict_or_empty(expr)
        resolved = self.any_dict_get_str(expr_node, "resolved_type", "")
        if resolved != "":
            return self.normalize_type_name(resolved)
        if self.any_dict_has(expr_node, "resolved_type"):
            raw: Any = None
            if "resolved_type" in expr_node:
                raw = expr_node["resolved_type"]
            if isinstance(raw, str):
                txt = self.any_to_str(raw)
                if txt == "":
                    txt = str(raw)
                if txt not in {"", "None", "{}", "[]"}:
                    return self.normalize_type_name(txt)
            elif raw is not None and not isinstance(raw, bool) and not isinstance(raw, int) and not isinstance(raw, float):
                if not isinstance(raw, dict) and not isinstance(raw, list) and not isinstance(raw, set):
                    txt2 = str(raw)
                    if txt2 not in {"", "None", "{}", "[]"}:
                        return self.normalize_type_name(txt2)
        return ""

    def _node_kind_from_dict(self, node_dict: dict[str, Any]) -> str:
        """dict 化済みノードの `kind` を文字列として安全に返す。"""
        if len(node_dict) == 0:
            return ""
        kind = self.any_dict_get_str(node_dict, "kind", "")
        if kind != "":
            return kind
        if "kind" not in node_dict:
            return ""
        raw = node_dict["kind"]
        if raw is None:
            return ""
        if isinstance(raw, bool) or isinstance(raw, int) or isinstance(raw, float):
            return ""
        if isinstance(raw, dict) or isinstance(raw, list) or isinstance(raw, set):
            return ""
        txt = str(raw)
        if txt in {"", "None", "{}", "[]"}:
            return ""
        return txt

    def node_kind(self, node: Any) -> str:
        """ノードの `kind` を文字列として安全に返す。"""
        node_dict = self.any_to_dict_or_empty(node)
        return self._node_kind_from_dict(node_dict)

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
        s = str(t).strip()
        if s == "":
            return ""
        if s == "int":
            return "int64"
        if s == "float":
            return "float64"
        if s == "byte":
            return "uint8"
        if s == "any":
            return "Any"
        if s == "object":
            return "object"
        if s.find("|") != -1:
            parts = self.split_union(s)
            if len(parts) > 1:
                out_parts: list[str] = []
                i = 0
                while i < len(parts):
                    out_parts.append(self.normalize_type_name(parts[i]))
                    i += 1
                return "|".join(out_parts)
        if s.startswith("list[") and s.endswith("]"):
            inner = s[5:-1]
            inner_norm = self.normalize_type_name(inner)
            return "list[" + inner_norm + "]"
        if s.startswith("set[") and s.endswith("]"):
            inner = s[4:-1]
            inner_norm = self.normalize_type_name(inner)
            return "set[" + inner_norm + "]"
        if s.startswith("tuple[") and s.endswith("]"):
            inner = s[6:-1]
            elems = self.split_generic(inner)
            out_elems: list[str] = []
            i = 0
            while i < len(elems):
                out_elems.append(self.normalize_type_name(elems[i]))
                i += 1
            return "tuple[" + ", ".join(out_elems) + "]"
        if s.startswith("dict[") and s.endswith("]"):
            inner = s[5:-1]
            elems = self.split_generic(inner)
            if len(elems) == 2:
                return "dict[" + self.normalize_type_name(elems[0]) + ", " + self.normalize_type_name(elems[1]) + "]"
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
            for p in parts:
                if p == "None" or p == s:
                    continue
                if self.is_any_like_type(p):
                    return True
            return False
        return False

    def is_list_type(self, t: str) -> bool:
        """型文字列が list[...] かを返す。"""
        return t.startswith("list[")

    def is_set_type(self, t: str) -> bool:
        """型文字列が set[...] かを返す。"""
        return t.startswith("set[")

    def is_dict_type(self, t: str) -> bool:
        """型文字列が dict[...] かを返す。"""
        return t.startswith("dict[")

    def is_indexable_sequence_type(self, t: str) -> bool:
        """添字アクセス可能なシーケンス型か判定する。"""
        return t.startswith("list[") or t.startswith("tuple[") or t == "str" or t == "bytes" or t == "bytearray"

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

    def declare_in_current_scope(self, name: str) -> None:
        """現在スコープへ宣言済み名を追加する（selfhost互換で再代入する）。"""
        scope = self.current_scope()
        scope.add(name)
        self.scope_stack[-1] = scope

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
        if not (c0 == "_" or (c0 >= "a" and c0 <= "z") or (c0 >= "A" and c0 <= "Z")):
            return False
        for ch in text[1:]:
            if not (ch == "_" or (ch >= "a" and ch <= "z") or (ch >= "A" and ch <= "Z") or (ch >= "0" and ch <= "9")):
                return False
        return True

    def _strip_outer_parens(self, text: str) -> str:
        """式全体を囲う不要な最外括弧を安全に取り除く。"""
        s: str = text
        while len(s) > 0:
            ch = s[0:1]
            if ch not in {" ", "\t", "\n", "\r", "\f", "\v"}:
                break
            s = s[1:]
        while len(s) > 0:
            ch = s[-1:]
            if ch not in {" ", "\t", "\n", "\r", "\f", "\v"}:
                break
            s = s[:-1]

        while len(s) >= 2 and s.startswith("(") and s.endswith(")"):
            depth = 0
            in_str = False
            esc = False
            quote = ""
            wrapped = True
            i = 0
            n = len(s)
            while i < n:
                ch = s[i : i + 1]
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
                while len(s) > 0:
                    ch = s[0:1]
                    if ch not in {" ", "\t", "\n", "\r", "\f", "\v"}:
                        break
                    s = s[1:]
                while len(s) > 0:
                    ch = s[-1:]
                    if ch not in {" ", "\t", "\n", "\r", "\f", "\v"}:
                        break
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
        while len(s) > 0:
            ch = s[0:1]
            if ch not in {" ", "\t", "\n", "\r", "\f", "\v"}:
                break
            s = s[1:]
        while len(s) > 0:
            ch = s[-1:]
            if ch not in {" ", "\t", "\n", "\r", "\f", "\v"}:
                break
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
        self._emit_trivia_items(trivia)

    def emit_module_leading_trivia(self) -> None:
        """モジュール先頭のコメント/空行 trivia を出力する。"""
        if "module_leading_trivia" not in self.doc:
            return
        trivia = self.any_to_dict_list(self.doc["module_leading_trivia"])
        if len(trivia) == 0:
            return
        self._emit_trivia_items(trivia)

    def _parse_passthrough_comment(self, text: str) -> dict[str, Any]:
        """`# Pytra::cpp` / `# Pytra::pass` 記法を解釈して directive を返す。"""
        out: dict[str, Any] = {}
        raw = self._trim_ws(text)
        prefix = ""
        if raw.startswith("Pytra::cpp"):
            prefix = "Pytra::cpp"
        elif raw.startswith("Pytra::pass"):
            prefix = "Pytra::pass"
        if prefix == "":
            return out
        rest = raw[len(prefix) :]
        if rest.startswith(":"):
            rest = rest[1:]
        rest = self._trim_ws(rest)
        if rest == "begin":
            out["kind"] = "begin"
            out["text"] = ""
            return out
        if rest == "end":
            out["kind"] = "end"
            out["text"] = ""
            return out
        out["kind"] = "line"
        out["text"] = rest
        return out

    def _emit_trivia_items(self, trivia: list[dict[str, Any]]) -> None:
        """trivia をコメント/空行/パススルー行として出力する。"""
        for item in trivia:
            k = self.any_dict_get_str(item, "kind", "")
            if k == "comment":
                txt = self.any_dict_get_str(item, "text", "")
                directive = self._parse_passthrough_comment(txt)
                d_kind = self.any_dict_get_str(directive, "kind", "")
                if self.passthrough_cpp_block:
                    if d_kind == "end":
                        self.passthrough_cpp_block = False
                        continue
                    if d_kind == "begin":
                        continue
                    if d_kind == "line":
                        line_txt = self.any_dict_get_str(directive, "text", "")
                        if line_txt != "":
                            self.emit(line_txt)
                        continue
                    self.emit(txt)
                    continue
                if d_kind == "begin":
                    self.passthrough_cpp_block = True
                    continue
                if d_kind == "end":
                    continue
                if d_kind == "line":
                    line_txt = self.any_dict_get_str(directive, "text", "")
                    if line_txt != "":
                        self.emit(line_txt)
                    continue
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
        if len(expr_dict) == 0 or self._node_kind_from_dict(expr_dict) != "Call":
            return False
        func = self.any_to_dict_or_empty(expr_dict.get("func"))
        if self._node_kind_from_dict(func) != "Attribute":
            return False
        if self.any_dict_get_str(func, "attr", "") != "__init__":
            return False
        owner = self.any_to_dict_or_empty(func.get("value"))
        if self._node_kind_from_dict(owner) != "Call":
            return False
        owner_func = self.any_to_dict_or_empty(owner.get("func"))
        if self._node_kind_from_dict(owner_func) != "Name":
            return False
        if self.any_dict_get_str(owner_func, "id", "") != "super":
            return False
        args = self.any_to_list(expr_dict.get("args"))
        kws = self.any_to_list(expr_dict.get("keywords"))
        return len(args) == 0 and len(kws) == 0

    def render_cond(self, expr: Any) -> str:
        """条件式文脈向けに式を真偽値へ正規化して出力する。"""
        expr_node = self.any_to_dict_or_empty(expr)
        if len(expr_node) == 0:
            return "false"
        t = self.get_expr_type(expr)
        body_raw = self.render_expr(expr)
        body = self._strip_outer_parens(body_raw)
        if body == "":
            # selfhost 経路で一部式レンダが空文字に崩れる場合の保険。
            rep_obj: Any = None
            if "repr" in expr_node:
                rep_obj = expr_node["repr"]
            rep_txt = self.any_to_str(rep_obj)
            body = self._strip_outer_parens(self._trim_ws(rep_txt))
        if body == "":
            return "false"
        if t == "bool":
            return body
        if t == "str" or t.startswith("list[") or t.startswith("dict[") or t.startswith("set[") or t.startswith("tuple["):
            return self.truthy_len_expr(body)
        return body
