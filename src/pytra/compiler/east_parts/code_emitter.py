"""EAST ベースの言語エミッタ共通基底。"""

from __future__ import annotations

from pytra.std.typing import Any


class EmitterHooks:
    """CodeEmitter へ注入する hook 関数を保持する薄いコンテナ。"""

    hooks: dict[str, Any]

    def __init__(self) -> None:
        self.hooks = {}

    def add(self, name: str, fn: Any) -> None:
        """hook を登録する。空名は無視する。"""
        if name == "":
            return
        self.hooks[name] = fn

    def to_dict(self) -> dict[str, Any]:
        """CodeEmitter へ渡せる dict 形式へ変換する。"""
        out: dict[str, Any] = {}
        for key, val in self.hooks.items():
            out[key] = val
        return out


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
    opt_level: str
    import_modules: dict[str, str]
    import_symbols: dict[str, dict[str, str]]

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
        self.opt_level = "2"
        import_modules: dict[str, str] = {}
        import_symbols: dict[str, dict[str, str]] = {}
        self.import_modules = import_modules
        self.import_symbols = import_symbols

    def _empty_lines(self) -> list[str]:
        """空の `list[str]` を返す。"""
        return []

    def _root_scope_stack(self) -> list[set[str]]:
        """最上位 1 スコープだけを持つ初期スコープスタックを返す。"""
        return [set()]

    def emit_stmt(self, stmt: dict[str, Any]) -> None:
        """文ノード出力フック。派生クラス側で実装する。"""
        return

    def render_expr(self, expr: Any) -> str:
        """式ノード出力フック。派生クラス側で実装する。"""
        return ""

    def apply_cast(self, rendered_expr: str, to_type: str) -> str:
        """式へ型キャストを適用する。既定実装は何も変更しない。"""
        _ = to_type
        return rendered_expr

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
        out: list[str] = list(args)
        kw_keys: list[str] = []
        for key, _ in kw.items():
            kw_keys.append(key)
        for key in kw_keys:
            out.append(kw[key])
        return out

    def merge_call_kw_values(self, args: list[str], kw_values: list[str]) -> list[str]:
        """`args + kw_values` を順序保持で結合する。"""
        out: list[str] = list(args)
        if len(kw_values) == 0:
            return out
        for val in kw_values:
            out.append(val)
        return out

    def merge_call_arg_nodes(self, arg_nodes: list[Any], kw_nodes: list[Any]) -> list[Any]:
        """位置引数ノードとキーワード値ノードを順序保持で結合する。"""
        out: list[Any] = list(arg_nodes)
        if len(kw_nodes) == 0:
            return out
        for node in kw_nodes:
            out.append(node)
        return out

    def unpack_prepared_call_parts(self, call_parts: dict[str, Any]) -> dict[str, Any]:
        """`_prepare_call_parts` 結果を型付きの扱いやすい形へ変換する。"""
        fn = self.any_to_dict_or_empty(call_parts.get("fn"))
        fn_name = self.any_to_str(call_parts.get("fn_name"))
        arg_nodes = self.any_to_list(call_parts.get("arg_nodes"))
        args_raw = self.any_to_list(call_parts.get("args"))
        args: list[str] = []
        for item in args_raw:
            args.append(self.any_to_str(item))
        kw_raw = self.any_to_dict_or_empty(call_parts.get("kw"))
        kw_values_raw = self.any_to_list(call_parts.get("kw_values"))
        kw_values: list[str] = []
        for item in kw_values_raw:
            kw_values.append(self.any_to_str(item))
        kw: dict[str, str] = {}
        for k, v in kw_raw.items():
            if isinstance(k, str):
                kw[k] = self.any_to_str(v)
        kw_nodes = self.any_to_list(call_parts.get("kw_nodes"))
        first_arg = call_parts.get("first_arg")
        out: dict[str, Any] = {}
        out["fn"] = fn
        out["fn_name"] = fn_name
        out["arg_nodes"] = arg_nodes
        out["args"] = args
        out["kw"] = kw
        out["kw_values"] = kw_values
        out["kw_nodes"] = kw_nodes
        out["first_arg"] = first_arg
        return out

    def validate_call_receiver_or_raise(self, fn_node: dict[str, Any]) -> None:
        """`obj.method(...)` の object レシーバ禁止ルールを検証する。"""
        if self._node_kind_from_dict(fn_node) != "Attribute":
            return
        owner_node: object = fn_node.get("value")
        owner_t = self.get_expr_type(owner_node)
        if self.is_forbidden_object_receiver_type(owner_t):
            raise RuntimeError(
                "object receiver method call is forbidden by language constraints"
            )

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

    def hook_on_render_module_method(
        self,
        module_name: str,
        attr: str,
        rendered_args: list[str],
        rendered_kwargs: dict[str, str],
        arg_nodes: list[Any],
    ) -> str:
        """`on_render_module_method` フック。既定では何もしない。"""
        if "on_render_module_method" in self.hooks:
            fn = self.hooks["on_render_module_method"]
            if fn is not None:
                v = fn(self, module_name, attr, rendered_args, rendered_kwargs, arg_nodes)
                if isinstance(v, str):
                    return v
        return ""

    def hook_on_render_object_method(
        self,
        owner_type: str,
        owner_expr: str,
        attr: str,
        rendered_args: list[str],
    ) -> str:
        """`on_render_object_method` フック。既定では何もしない。"""
        if "on_render_object_method" in self.hooks:
            fn = self.hooks["on_render_object_method"]
            if fn is not None:
                v = fn(self, owner_type, owner_expr, attr, rendered_args)
                if isinstance(v, str):
                    return v
        return ""

    def hook_on_render_class_method(
        self,
        owner_type: str,
        attr: str,
        func_node: dict[str, Any],
        rendered_args: list[str],
        rendered_kwargs: dict[str, str],
        arg_nodes: list[Any],
    ) -> str:
        """`on_render_class_method` フック。既定では何もしない。"""
        if "on_render_class_method" in self.hooks:
            fn = self.hooks["on_render_class_method"]
            if fn is not None:
                v = fn(self, owner_type, attr, func_node, rendered_args, rendered_kwargs, arg_nodes)
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

    def any_to_str_dict_or_empty(self, v: Any) -> dict[str, str]:
        """動的値を `dict[str, str]` へ安全に変換する。"""
        out: dict[str, str] = {}
        raw = self.any_to_dict_or_empty(v)
        for k, val in raw.items():
            if isinstance(k, str):
                out[k] = self.any_to_str(val)
        return out

    def any_to_dict_list(self, v: Any) -> list[dict[str, Any]]:
        """動的値を `list[dict]` へ安全に変換する。"""
        out: list[dict[str, Any]] = []
        for item in self.any_to_list(v):
            if isinstance(item, dict):
                out.append(item)
        return out

    def _dict_stmt_list(self, raw: Any) -> list[dict[str, Any]]:
        """動的値から `list[dict]` を安全に取り出す。"""
        out: list[dict[str, Any]] = []
        for item in self.any_to_list(raw):
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
                for part in parts:
                    out_parts.append(self.normalize_type_name(part))
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
            for elem in elems:
                out_elems.append(self.normalize_type_name(elem))
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
        for i in range(len(self.scope_stack) - 1, -1, -1):
            scope: set[str] = self.scope_stack[i]
            if name in scope:
                return True
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
        s: str = self._trim_ws(text)

        while len(s) >= 2 and s.startswith("(") and s.endswith(")"):
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
                s = self._trim_ws(s)
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
        return text.strip()

    def _contains_text(self, text: str, needle: str) -> bool:
        """`needle in text` 相当を selfhost でも安全に判定する。"""
        if needle == "":
            return True
        return text.find(needle) >= 0

    def _last_dotted_name(self, name: str) -> str:
        """`a.b.c` の末尾要素 `c` を返す。"""
        last = name
        for i, ch in enumerate(name):
            if ch == ".":
                last = name[i + 1 :]
        return last

    def _opt_ge(self, level: int) -> bool:
        """最適化レベルが指定値以上かを返す。"""
        cur = 3
        if self.opt_level in {"0", "1", "2", "3"}:
            cur = int(self.opt_level)
        return cur >= level

    def _resolve_imported_module_name(self, name: str) -> str:
        """import で束縛された識別子名を実モジュール名へ解決する。"""
        if name in self.import_modules:
            mod_name = self.import_modules[name]
            if mod_name != "":
                return mod_name

        if name in self.import_symbols:
            sym = self.import_symbols[name]
            parent = sym.get("module", "")
            child = sym.get("name", "")
            if parent != "" and child != "":
                return f"{parent}.{child}"
        sym_fallback = self._resolve_imported_symbol(name)
        parent_fb = sym_fallback.get("module", "")
        child_fb = sym_fallback.get("name", "")
        if parent_fb != "" and child_fb != "":
            return f"{parent_fb}.{child_fb}"
        return ""

    def _resolve_imported_symbol(self, name: str) -> dict[str, str]:
        """from-import で束縛された識別子を返す（無ければ空 dict）。"""
        if name in self.import_symbols:
            sym0 = self.import_symbols[name]
            out0: dict[str, str] = {}
            mod0 = sym0.get("module", "")
            nm0 = sym0.get("name", "")
            if mod0 != "":
                out0["module"] = mod0
            if nm0 != "":
                out0["name"] = nm0
            return out0

        meta = self.any_to_dict_or_empty(self.doc.get("meta"))
        refs = self.any_to_dict_list(meta.get("qualified_symbol_refs"))
        for ref in refs:
            local_name = self.any_to_str(ref.get("local_name"))
            if local_name == name:
                module_id = self.any_to_str(ref.get("module_id"))
                symbol = self.any_to_str(ref.get("symbol"))
                if module_id != "" and symbol != "":
                    out_ref: dict[str, str] = {}
                    out_ref["module"] = module_id
                    out_ref["name"] = symbol
                    return out_ref

        binds = self.any_to_dict_list(meta.get("import_bindings"))
        for ent in binds:
            if self.any_to_str(ent.get("binding_kind")) == "symbol":
                local_name = self.any_to_str(ent.get("local_name"))
                if local_name == name:
                    module_id = self.any_to_str(ent.get("module_id"))
                    export_name = self.any_to_str(ent.get("export_name"))
                    if module_id != "" and export_name != "":
                        out_bind: dict[str, str] = {}
                        out_bind["module"] = module_id
                        out_bind["name"] = export_name
                        return out_bind
        out: dict[str, str] = {}
        return out

    def attr_name(self, attr_node: dict[str, Any]) -> str:
        """Attribute ノードから属性名を安全に取り出す。"""
        attr = self.any_to_str(attr_node.get("attr"))
        if attr != "":
            return attr
        raw = attr_node.get("attr")
        if raw is None:
            return ""
        if isinstance(raw, bool) or isinstance(raw, int) or isinstance(raw, float):
            return ""
        if isinstance(raw, dict) or isinstance(raw, list) or isinstance(raw, set):
            return ""
        text = str(raw)
        if text in {"", "None", "{}", "[]"}:
            return ""
        return text

    def resolve_attribute_owner_type(
        self,
        owner_obj: Any,
        owner_node: dict[str, Any],
        declared_var_types: dict[str, str],
    ) -> str:
        """Attribute owner の型を解決し、必要なら宣言型で上書きする。"""
        owner_t = self.get_expr_type(owner_obj)
        if self._node_kind_from_dict(owner_node) != "Name":
            return owner_t
        owner_name = self.any_dict_get_str(owner_node, "id", "")
        if owner_name == "":
            return owner_t
        if owner_name in declared_var_types:
            declared_owner_t = declared_var_types[owner_name]
            if declared_owner_t not in {"", "unknown"}:
                return declared_owner_t
        return owner_t

    def resolve_attribute_owner_context(self, owner_obj: Any, owner_expr: str) -> dict[str, Any]:
        """Attribute owner の kind/expr/module をまとめて解決する。"""
        owner_node = self.any_to_dict_or_empty(owner_obj)
        owner_kind = self._node_kind_from_dict(owner_node)
        wrapped_owner_expr = owner_expr
        if owner_kind in {"BinOp", "BoolOp", "Compare", "IfExp"}:
            wrapped_owner_expr = f"({owner_expr})"
        owner_module = ""
        if owner_kind in {"Name", "Attribute"}:
            owner_module = self._resolve_imported_module_name(owner_expr)
            if owner_module == "" and owner_expr.startswith("pytra."):
                owner_module = owner_expr
        out: dict[str, Any] = {}
        out["node"] = owner_node
        out["kind"] = owner_kind
        out["expr"] = wrapped_owner_expr
        out["module"] = owner_module
        return out

    def resolve_call_attribute_context(
        self,
        owner_obj: Any,
        owner_rendered: str,
        fn_node: dict[str, Any],
        declared_var_types: dict[str, str],
    ) -> dict[str, str]:
        """`Call(Attribute)` の owner/module/type/attr 解決をまとめて返す。"""
        owner_ctx = self.resolve_attribute_owner_context(owner_obj, owner_rendered)
        owner = self.any_to_dict_or_empty(owner_ctx.get("node"))
        owner_expr = self.any_dict_get_str(owner_ctx, "expr", "")
        owner_mod = self.any_dict_get_str(owner_ctx, "module", "")
        owner_t = self.resolve_attribute_owner_type(owner_obj, owner, declared_var_types)
        attr = self.attr_name(fn_node)
        out: dict[str, str] = {}
        out["owner_expr"] = owner_expr
        out["owner_mod"] = owner_mod
        out["owner_type"] = owner_t
        out["attr"] = attr
        return out

    def _can_runtime_cast_target(self, target_t: str) -> bool:
        """実行時キャストを安全に適用できる型か判定する。"""
        if target_t == "" or target_t in {"unknown", "Any", "object"}:
            return False
        if self._contains_text(target_t, "|") or self._contains_text(target_t, "Any") or self._contains_text(target_t, "None"):
            return False
        return True

    def is_boxed_object_expr(self, expr_txt: str) -> bool:
        """式が既に object boxing 済みなら True を返す。"""
        if expr_txt.startswith("make_object("):
            return True
        if expr_txt == "object{}":
            return True
        return False

    def infer_rendered_arg_type(
        self,
        rendered_arg: str,
        arg_type: str,
        declared_var_types: dict[str, str],
    ) -> str:
        """ノード型が unknown のとき、描画済み式から型ヒントを補完する。"""
        if arg_type not in {"", "unknown"}:
            return arg_type
        text = self._strip_outer_parens(rendered_arg.strip())
        if text in declared_var_types:
            declared_t = self.normalize_type_name(declared_var_types[text])
            if declared_t != "":
                return declared_t
        return arg_type

    def _is_std_runtime_call(self, runtime_call: str) -> bool:
        """`std::` 直呼び出しとして扱う runtime_call か判定する。"""
        return runtime_call[0:5] == "std::" or runtime_call[0:7] == "::std::"

    def _cpp_expr_to_module_name(self, expr: str) -> str:
        """`pytra::std::x` 形式の C++ 式を `pytra.std.x` へ戻す。"""
        if expr.startswith("pytra::"):
            return expr.replace("::", ".")
        return ""

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

    def _one_char_str_const(self, node: Any) -> str:
        """1文字文字列定数ならその実文字を返す。"""
        nd = self.any_to_dict_or_empty(node)
        if len(nd) == 0 or self._node_kind_from_dict(nd) != "Constant":
            return ""
        v = ""
        if "value" in nd:
            v = self.any_to_str(nd["value"])
        if v == "":
            return ""
        if len(v) == 1:
            return v
        if len(v) == 2 and v[0:1] == "\\":
            c = v[1:2]
            if c == "n":
                return "\n"
            if c == "r":
                return "\r"
            if c == "t":
                return "\t"
            if c == "\\":
                return "\\"
            if c == "'":
                return "'"
            if c == "0":
                return "\0"
            return ""
        return ""

    def _const_int_literal(self, node: Any) -> int | None:
        """整数定数ノードを `int` として返す（取得できない場合は None）。"""
        nd = self.any_to_dict_or_empty(node)
        if len(nd) == 0:
            return None
        kind = self._node_kind_from_dict(nd)
        if kind == "Constant":
            if "value" not in nd:
                return None
            val = nd["value"]
            if isinstance(val, bool):
                return None
            if isinstance(val, int):
                return int(val)
            if isinstance(val, str):
                txt = self.any_to_str(val)
                if txt == "":
                    return None
                try:
                    return int(txt)
                except ValueError:
                    return None
            return None
        if kind == "UnaryOp" and self.any_dict_get_str(nd, "op", "") == "USub":
            opd = self.any_to_dict_or_empty(nd.get("operand"))
            if self._node_kind_from_dict(opd) != "Constant":
                return None
            if "value" not in opd:
                return None
            oval = opd["value"]
            if isinstance(oval, bool):
                return None
            if isinstance(oval, int):
                return -int(oval)
            if isinstance(oval, str):
                txt = self.any_to_str(oval)
                if txt == "":
                    return None
                try:
                    return -int(txt)
                except ValueError:
                    return None
        return None

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

    def _prepare_call_parts(
        self,
        expr: dict[str, Any],
    ) -> dict[str, Any]:
        """Call ノードの前処理（func/args/kw 展開）を共通化する。"""
        fn_obj: object = expr.get("func")
        fn_name = self.render_expr(fn_obj)
        arg_nodes_obj: object = self.any_dict_get_list(expr, "args")
        arg_nodes = self.any_to_list(arg_nodes_obj)
        args: list[str] = []
        for arg_node in arg_nodes:
            args.append(self.render_expr(arg_node))
        keywords_obj: object = self.any_dict_get_list(expr, "keywords")
        keywords = self.any_to_list(keywords_obj)
        first_arg: object = expr
        if len(arg_nodes) > 0:
            first_arg = arg_nodes[0]
        kw: dict[str, str] = {}
        kw_values: list[str] = []
        kw_nodes: list[Any] = []
        for k in keywords:
            kd = self.any_to_dict_or_empty(k)
            if len(kd) > 0:
                kw_name = self.any_to_str(kd.get("arg"))
                if kw_name != "":
                    kw_val_node: Any = kd.get("value")
                    kw_val = self.render_expr(kw_val_node)
                    kw[kw_name] = kw_val
                    kw_values.append(kw_val)
                    kw_nodes.append(kw_val_node)
        out: dict[str, Any] = {}
        out["fn"] = fn_obj
        out["fn_name"] = fn_name
        out["arg_nodes"] = arg_nodes
        out["args"] = args
        out["kw"] = kw
        out["kw_values"] = kw_values
        out["kw_nodes"] = kw_nodes
        out["first_arg"] = first_arg
        return out

    def _render_ifexp_expr(self, expr: dict[str, Any]) -> str:
        """IfExp（三項演算）を式へ変換する。"""
        body = self.render_expr(expr.get("body"))
        orelse = self.render_expr(expr.get("orelse"))
        casts = self._dict_stmt_list(expr.get("casts"))
        for c in casts:
            on = self.any_to_str(c.get("on"))
            to_t = self.any_to_str(c.get("to"))
            if on == "body":
                body = self.apply_cast(body, to_t)
            elif on == "orelse":
                orelse = self.apply_cast(orelse, to_t)
        test_expr = self.render_expr(expr.get("test"))
        return f"({test_expr} ? {body} : {orelse})"

    def _binop_precedence(self, op_name: str) -> int:
        """二項演算子の優先順位を返す。"""
        if op_name in {"Mult", "Div", "FloorDiv", "Mod"}:
            return 12
        if op_name in {"Add", "Sub"}:
            return 11
        if op_name in {"LShift", "RShift"}:
            return 10
        if op_name == "BitAnd":
            return 9
        if op_name == "BitXor":
            return 8
        if op_name == "BitOr":
            return 7
        return 0

    def _wrap_for_binop_operand(
        self,
        rendered: str,
        operand_expr: dict[str, Any],
        parent_op: str,
        is_right: bool = False,
    ) -> str:
        """二項演算の結合順を壊さないため必要時に括弧を補う。"""
        if len(operand_expr) == 0:
            return rendered
        kind = self.any_dict_get_str(operand_expr, "kind", "")
        if kind in {"IfExp", "BoolOp", "Compare"}:
            return f"({rendered})"
        if kind != "BinOp":
            return rendered

        child_op = self.any_dict_get_str(operand_expr, "op", "")
        parent_prec = self._binop_precedence(parent_op)
        child_prec = self._binop_precedence(child_op)
        if child_prec < parent_prec:
            return f"({rendered})"
        # Keep explicit grouping for multiplication with a division subtree, e.g. a * (b / c).
        if parent_op == "Mult" and child_op in {"Div", "FloorDiv"}:
            return f"({rendered})"
        if is_right and child_prec == parent_prec and parent_op in {"Sub", "Div", "FloorDiv", "Mod", "LShift", "RShift"}:
            return f"({rendered})"
        return rendered

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
