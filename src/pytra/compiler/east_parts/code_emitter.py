"""EAST ベースの言語エミッタ共通基底。"""

from __future__ import annotations

from pytra.std.typing import Any
from pytra.std import json
from pytra.std.pathlib import Path


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
    import_symbol_modules: set[str]
    current_class_name: str | None
    current_class_static_fields: set[str]
    class_base: dict[str, str]
    class_method_names: dict[str, set[str]]
    class_field_owner_unique: dict[str, str]
    class_method_owner_unique: dict[str, str]
    ref_classes: set[str]
    dynamic_hooks_enabled: bool

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
        self.import_symbol_modules = set()
        self.current_class_name = None
        self.current_class_static_fields = set()
        self.class_base = {}
        class_method_names: dict[str, set[str]] = {}
        self.class_method_names = class_method_names
        self.class_field_owner_unique = {}
        self.class_method_owner_unique = {}
        self.ref_classes = set()
        self.dynamic_hooks_enabled = True

    def _empty_lines(self) -> list[str]:
        """空の `list[str]` を返す。"""
        return []

    def _root_scope_stack(self) -> list[set[str]]:
        """最上位 1 スコープだけを持つ初期スコープスタックを返す。"""
        return [set()]

    @staticmethod
    def escape_string_for_literal(text: str) -> str:
        """C 系言語向けの最小文字列エスケープを返す。"""
        out_parts: list[str] = []
        for ch in text:
            if ch == "\\":
                out_parts.append("\\\\")
            elif ch == "\"":
                out_parts.append("\\\"")
            elif ch == "\n":
                out_parts.append("\\n")
            elif ch == "\r":
                out_parts.append("\\r")
            elif ch == "\t":
                out_parts.append("\\t")
            else:
                out_parts.append(ch)
        return "".join(out_parts)

    def quote_string_literal(self, text: str, quote: str = "\"") -> str:
        """エスケープ済み文字列を引用符で囲んで返す。"""
        q = quote
        if q == "":
            q = "\""
        return q + CodeEmitter.escape_string_for_literal(text) + q

    @staticmethod
    def _load_json_dict(path: Path) -> dict[str, Any]:
        """JSON ファイルを辞書として読み込む。失敗時は空辞書。"""
        if not path.exists():
            return {}
        raw_obj: dict[str, Any] = {}
        try:
            txt = path.read_text(encoding="utf-8")
            raw_obj = json.loads(txt)
        except Exception:
            return {}
        raw = raw_obj
        if isinstance(raw, dict):
            return raw
        return {}

    @staticmethod
    def _resolve_src_root(anchor_file: str) -> str:
        """`.../src/...` パスから `.../src` ルートを推定して返す。"""
        if anchor_file.startswith("src/"):
            return "src"
        if anchor_file.startswith("src\\"):
            return "src"
        pos = anchor_file.rfind("/src/")
        if pos < 0:
            return ""
        return anchor_file[: pos + 4]

    @staticmethod
    def load_profile_with_includes(
        profile_rel_path: str,
        anchor_file: str = "",
    ) -> dict[str, Any]:
        """`profile.json` + include 断片を読み込み、1つの dict に統合する。"""
        profile_path = Path(profile_rel_path)
        if not profile_path.exists() and anchor_file != "":
            src_root = CodeEmitter._resolve_src_root(anchor_file)
            if src_root != "":
                rel = profile_rel_path
                if rel.startswith("src/"):
                    rel = rel[4:]
                profile_path = Path(src_root) / rel
        meta = CodeEmitter._load_json_dict(profile_path)
        if len(meta) == 0:
            return {}

        profile_root = profile_path.parent
        out: dict[str, Any] = {}
        includes_obj = meta.get("include")
        includes: list[str] = []
        includes_raw: list[Any] = []
        if isinstance(includes_obj, list):
            includes_raw = includes_obj

        for item_obj in includes_raw:
            if isinstance(item_obj, str) and item_obj != "":
                includes.append(item_obj)

        for rel in includes:
            piece = CodeEmitter._load_json_dict(profile_root / rel)
            for key, val in piece.items():
                out[key] = val

        for key, val in meta.items():
            if key != "include":
                out[key] = val
        return out

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

    def prepare_call_context(self, expr: dict[str, Any]) -> dict[str, Any]:
        """Call ノードの前処理結果を unpack 済み文脈として返す。"""
        return self.unpack_prepared_call_parts(self._prepare_call_parts(expr))

    def validate_call_receiver_or_raise(self, fn_node: dict[str, Any]) -> None:
        """`obj.method(...)` の object レシーバ禁止ルールを検証する。"""
        if self._node_kind_from_dict(fn_node) != "Attribute":
            return
        owner_node: object = fn_node.get("value")
        owner_t = self.get_expr_type(owner_node)
        if self.is_forbidden_object_receiver_type(owner_t):
            attr = self.attr_name(fn_node)
            owner_cls = self.class_field_owner_unique.get(attr, "")
            owner_m_cls = self.class_method_owner_unique.get(attr, "")
            if (
                owner_cls in self.ref_classes
                or owner_m_cls in self.ref_classes
            ):
                return
        if self.is_forbidden_object_receiver_type(owner_t):
            raise RuntimeError(
                "object receiver method call is forbidden by language constraints"
            )

    def _lookup_hook(self, name: str) -> Any | None:
        """hook 名から call 可能な値を取得する。未定義時は `None`。"""
        if name in self.hooks:
            fn = self.hooks[name]
            if fn is not None:
                return fn
        return None

    def set_dynamic_hooks_enabled(self, enabled: bool) -> None:
        """dynamic hook 呼び出しを有効/無効に切り替える。"""
        self.dynamic_hooks_enabled = True if enabled else False

    def _call_hook(
        self,
        name: str,
        arg0: Any = None,
        arg1: Any = None,
        arg2: Any = None,
        arg3: Any = None,
        arg4: Any = None,
        arg5: Any = None,
        argc: int = 0,
    ) -> Any:
        """hook 呼び出しを 1 箇所へ集約する。未定義時は `None`。"""
        if not self.dynamic_hooks_enabled:
            return None
        fn = self._lookup_hook(name)
        if fn is None:
            return None
        if argc <= 0:
            return fn(self)
        if argc == 1:
            return fn(self, arg0)
        if argc == 2:
            return fn(self, arg0, arg1)
        if argc == 3:
            return fn(self, arg0, arg1, arg2)
        if argc == 4:
            return fn(self, arg0, arg1, arg2, arg3)
        if argc == 5:
            return fn(self, arg0, arg1, arg2, arg3, arg4)
        if argc == 6:
            return fn(self, arg0, arg1, arg2, arg3, arg4, arg5)
        return None

    def _call_hook1(self, name: str, arg0: Any) -> Any:
        return self._call_hook(name, arg0, None, None, None, None, None, 1)

    def _call_hook2(self, name: str, arg0: Any, arg1: Any) -> Any:
        return self._call_hook(name, arg0, arg1, None, None, None, None, 2)

    def _call_hook3(self, name: str, arg0: Any, arg1: Any, arg2: Any) -> Any:
        return self._call_hook(name, arg0, arg1, arg2, None, None, None, 3)

    def _call_hook4(self, name: str, arg0: Any, arg1: Any, arg2: Any, arg3: Any) -> Any:
        return self._call_hook(name, arg0, arg1, arg2, arg3, None, None, 4)

    def _call_hook5(
        self,
        name: str,
        arg0: Any,
        arg1: Any,
        arg2: Any,
        arg3: Any,
        arg4: Any,
    ) -> Any:
        return self._call_hook(name, arg0, arg1, arg2, arg3, arg4, None, 5)

    def _call_hook6(
        self,
        name: str,
        arg0: Any,
        arg1: Any,
        arg2: Any,
        arg3: Any,
        arg4: Any,
        arg5: Any,
    ) -> Any:
        return self._call_hook(name, arg0, arg1, arg2, arg3, arg4, arg5, 6)

    def hook_on_emit_stmt(self, stmt: dict[str, Any]) -> bool | None:
        """`on_emit_stmt` フック。既定では何もしない。"""
        v = self._call_hook1("on_emit_stmt", stmt)
        if isinstance(v, bool):
            return True if v else False
        return None

    def hook_on_emit_stmt_kind(
        self,
        kind: str,
        stmt: dict[str, Any],
    ) -> bool | None:
        """`on_emit_stmt_kind` を解決し、未処理時は fallback へ委譲する。"""
        handled_specific = self.hook_on_emit_stmt_kind_specific(kind, stmt)
        if isinstance(handled_specific, bool) and handled_specific:
            return True
        v = self._call_hook2("on_emit_stmt_kind", kind, stmt)
        if isinstance(v, bool) and v:
            return True
        if self._emit_stmt_kind_fallback(kind, stmt):
            return True
        if isinstance(v, bool):
            return False
        return handled_specific

    def _emit_stmt_kind_fallback(
        self,
        kind: str,
        stmt: dict[str, Any],
    ) -> bool:
        """文 kind の既定 fallback。基底では未処理。"""
        _ = kind
        _ = stmt
        return False

    def hook_on_stmt_omit_braces(
        self,
        kind: str,
        stmt: dict[str, Any],
        default_value: bool,
    ) -> bool:
        """制御構文の brace 省略可否を hook で上書きする。"""
        v = self._call_hook3("on_stmt_omit_braces", kind, stmt, default_value)
        if isinstance(v, bool):
            return v
        return default_value

    def hook_on_for_range_mode(
        self,
        stmt: dict[str, Any],
        default_mode: str,
    ) -> str:
        """ForRange の mode（ascending/descending/dynamic）を hook で上書きする。"""
        mode = default_mode
        if mode == "":
            mode = "dynamic"
        v = self._call_hook2("on_for_range_mode", stmt, mode)
        if isinstance(v, str) and v != "":
            return v
        return mode

    def hook_on_render_call(
        self,
        call_node: dict[str, Any],
        func_node: dict[str, Any],
        rendered_args: list[str],
        rendered_kwargs: dict[str, str],
    ) -> str:
        """`on_render_call` フック。既定では何もしない。"""
        v = self._call_hook4("on_render_call", call_node, func_node, rendered_args, rendered_kwargs)
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
        v = self._call_hook5("on_render_module_method", module_name, attr, rendered_args, rendered_kwargs, arg_nodes)
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
        v = self._call_hook4("on_render_object_method", owner_type, owner_expr, attr, rendered_args)
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
        v = self._call_hook6("on_render_class_method", owner_type, attr, func_node, rendered_args, rendered_kwargs, arg_nodes)
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
        v = self._call_hook3("on_render_binop", binop_node, left, right)
        if isinstance(v, str):
            return v
        return ""

    def _kind_hook_suffix(self, kind: str) -> str:
        """`Name` / `IfExp` などを hook 名 suffix 用 snake_case へ正規化する。"""
        text = kind.strip()
        if text == "":
            return ""
        raw: list[str] = []
        n = len(text)
        for i, ch in enumerate(text):
            if ("A" <= ch) and (ch <= "Z"):
                prev_ch = text[i - 1] if i > 0 else ""
                next_ch = text[i + 1] if i + 1 < n else ""
                prev_is_lower_or_digit = (("a" <= prev_ch) and (prev_ch <= "z")) or (
                    ("0" <= prev_ch) and (prev_ch <= "9")
                )
                next_is_lower = ("a" <= next_ch) and (next_ch <= "z")
                if len(raw) > 0 and raw[-1] != "_" and (prev_is_lower_or_digit or next_is_lower):
                    raw.append("_")
                raw.append(chr(ord(ch) + 32))
                continue
            is_lower = ("a" <= ch) and (ch <= "z")
            is_digit = ("0" <= ch) and (ch <= "9")
            if is_lower or is_digit:
                raw.append(ch)
            elif len(raw) > 0 and raw[-1] != "_":
                raw.append("_")
        joined = "".join(raw).strip("_")
        out_chars: list[str] = []
        for ch in joined:
            if ch == "_" and len(out_chars) > 0 and out_chars[-1] == "_":
                continue  # 連続したアンダースコアを除去
            out_chars.append(ch)
        return "".join(out_chars)

    def _stmt_kind_hook_name(self, kind: str) -> str:
        """文 kind 専用 hook 名（`on_emit_stmt_<kind>`）を返す。"""
        suffix = self._kind_hook_suffix(kind)
        if suffix == "":
            return ""
        return "on_emit_stmt_" + suffix

    def hook_on_emit_stmt_kind_specific(
        self,
        kind: str,
        stmt: dict[str, Any],
    ) -> bool | None:
        """kind 別文フック（`on_emit_stmt_<kind>`）を呼び出す。"""
        hook_name = self._stmt_kind_hook_name(kind)
        if hook_name == "":
            return None
        v = self._call_hook2(hook_name, kind, stmt)
        if isinstance(v, bool):
            return True if v else False
        return None

    def _render_expr_kind_hook_suffix(self, kind: str) -> str:
        """`Name` / `IfExp` などを式 hook 名用 snake_case へ正規化する。"""
        return self._kind_hook_suffix(kind)

    def _render_expr_kind_hook_name(self, kind: str) -> str:
        """式 kind 専用 hook 名（`on_render_expr_<kind>`）を返す。"""
        suffix = self._render_expr_kind_hook_suffix(kind)
        if suffix == "":
            return ""
        return "on_render_expr_" + suffix

    def hook_on_render_expr_kind_specific(
        self,
        kind: str,
        expr_node: dict[str, Any],
    ) -> str:
        """kind 別 hook（`on_render_expr_<kind>`）を呼び出す。"""
        hook_name = self._render_expr_kind_hook_name(kind)
        if hook_name == "":
            return ""
        v = self._call_hook2(hook_name, kind, expr_node)
        if isinstance(v, str):
            return v
        return ""

    def hook_on_render_expr_kind(
        self,
        kind: str,
        expr_node: dict[str, Any],
    ) -> str:
        """式 kind hook を `specific -> generic -> complex/leaf` 順で解決する。"""
        rendered_specific = self.hook_on_render_expr_kind_specific(kind, expr_node)
        if rendered_specific != "":
            return rendered_specific
        v = self._call_hook2("on_render_expr_kind", kind, expr_node)
        if isinstance(v, str) and v != "":
            return v
        if kind in {"JoinedStr", "Lambda", "ListComp", "SetComp", "DictComp"}:
            rendered_complex = self.hook_on_render_expr_complex(expr_node)
            if rendered_complex != "":
                return rendered_complex
        if kind in {"Name", "Constant", "Attribute"}:
            rendered_leaf = self.hook_on_render_expr_leaf(kind, expr_node)
            if rendered_leaf != "":
                return rendered_leaf
        return ""

    def hook_on_render_expr_leaf(
        self,
        kind: str,
        expr_node: dict[str, Any],
    ) -> str:
        """`Name/Constant/Attribute` などの leaf 式向けフック。"""
        v = self._call_hook2("on_render_expr_leaf", kind, expr_node)
        if isinstance(v, str):
            return v
        return ""

    def hook_on_render_expr_complex(
        self,
        expr_node: dict[str, Any],
    ) -> str:
        """複雑式（JoinedStr/Lambda/Comp 系）用フック。既定では何もしない。"""
        v = self._call_hook1("on_render_expr_complex", expr_node)
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

    def emit_with_scope(self, scope_names: set[str], body_fn: list[dict[str, Any]]) -> None:
        """現在 indent 位置でスコープを1段積み、文リスト本体を出力する。"""
        self.indent += 1
        self.scope_stack.append(scope_names)
        for stmt in body_fn:
            self.emit_stmt(stmt)
        self.scope_stack.pop()
        self.indent -= 1

    def emit_scoped_block(self, open_line: str, stmts: list[dict[str, Any]], scope_names: set[str]) -> None:
        """`open_line` を出力し、スコープ付きで文リストを出して block を閉じる。"""
        self.emit(open_line)
        self.emit_scoped_stmt_list(stmts, scope_names)
        self.emit_block_close()

    def emit_scoped_block_with_tail_lines(
        self,
        open_line: str,
        stmts: list[dict[str, Any]],
        scope_names: set[str],
        tail_lines: list[str],
    ) -> None:
        """スコープ付き block の末尾へ生テキスト行を挿入して閉じる。"""
        self.emit(open_line)
        self.indent += 1
        self.scope_stack.append(scope_names)
        self.emit_stmt_list(stmts)
        for line in tail_lines:
            self.emit(line)
        self.scope_stack.pop()
        self.indent -= 1
        self.emit_block_close()

    def emit_if_stmt_skeleton(
        self,
        cond_expr: str,
        body_stmts: list[dict[str, Any]],
        else_stmts: list[dict[str, Any]],
        if_open_default: str = "if ({cond}) {",
        else_open_default: str = "} else {",
        body_scope: set[str] | None = None,
        else_scope: set[str] | None = None,
    ) -> None:
        """`if/else` の開閉ブロックとスコープ処理を共通出力する。"""
        b_scope = body_scope if body_scope is not None else set()
        e_scope = else_scope if else_scope is not None else set()
        self.emit(self.syntax_line("if_open", if_open_default, {"cond": cond_expr}))
        self.emit_scoped_stmt_list(body_stmts, b_scope)
        if len(else_stmts) == 0:
            self.emit(self.syntax_text("block_close", "}"))
            return
        self.emit(self.syntax_text("else_open", else_open_default))
        self.emit_scoped_stmt_list(else_stmts, e_scope)
        self.emit(self.syntax_text("block_close", "}"))

    def emit_while_stmt_skeleton(
        self,
        cond_expr: str,
        body_stmts: list[dict[str, Any]],
        while_open_default: str = "while ({cond}) {",
        body_scope: set[str] | None = None,
    ) -> None:
        """`while` の開閉ブロックとスコープ処理を共通出力する。"""
        b_scope = body_scope if body_scope is not None else set()
        self.emit(self.syntax_line("while_open", while_open_default, {"cond": cond_expr}))
        self.emit_scoped_stmt_list(body_stmts, b_scope)
        self.emit(self.syntax_text("block_close", "}"))

    def prepare_if_stmt_parts(
        self,
        stmt: dict[str, Any],
        *,
        cond_empty_default: str = "false",
    ) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
        """If ノードの条件式/本体/else 本体を共通前処理して返す。"""
        cond_expr = self.render_cond(stmt.get("test"))
        if cond_expr == "":
            cond_expr = cond_empty_default
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        else_stmts = self._dict_stmt_list(stmt.get("orelse"))
        return cond_expr, body_stmts, else_stmts

    def prepare_while_stmt_parts(
        self,
        stmt: dict[str, Any],
        *,
        cond_empty_default: str = "false",
    ) -> tuple[str, list[dict[str, Any]]]:
        """While ノードの条件式/本体を共通前処理して返す。"""
        cond_expr = self.render_cond(stmt.get("test"))
        if cond_expr == "":
            cond_expr = cond_empty_default
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        return cond_expr, body_stmts

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
                        if not self._is_empty_dynamic_text(raw_txt):
                            name = raw_txt
        if name == "":
            name = default_name
        return self.rename_if_reserved(name, reserved_words, rename_prefix, renamed_symbols)

    def render_name_expr_common(
        self,
        expr_d: dict[str, Any],
        reserved_words: set[str],
        rename_prefix: str,
        renamed_symbols: dict[str, str],
        default_name: str = "_",
        rewrite_self: bool = False,
        self_is_declared: bool = True,
        self_rendered: str = "*this",
    ) -> str:
        """Name ノードの共通描画（予約語回避 + 任意の self 置換）を行う。"""
        name_txt = self.any_dict_get_str(expr_d, "id", "")
        if rewrite_self and name_txt == "self" and not self_is_declared:
            return self_rendered
        return self.render_name_ref(
            expr_d,
            reserved_words,
            rename_prefix,
            renamed_symbols,
            default_name,
        )

    def render_constant_non_string_common(
        self,
        expr: Any,
        expr_d: dict[str, Any],
        none_non_any_literal: str,
        none_any_literal: str,
    ) -> tuple[str, str]:
        """Constant ノードのうち非文字列系（bool/None/数値など）を共通描画する。"""
        v = expr_d.get("value")
        raw_repr = self.any_to_str(expr_d.get("repr"))
        if raw_repr != "" and not isinstance(v, bool) and v is not None and not isinstance(v, str):
            return "1", raw_repr
        if isinstance(v, bool):
            return "1", ("true" if str(v) == "True" else "false")
        if v is None:
            t = self.get_expr_type(expr)
            if self.is_any_like_type(t):
                return "1", none_any_literal
            return "1", none_non_any_literal
        if isinstance(v, str):
            return "0", ""
        return "1", str(v)

    def render_constant_expr_common(
        self,
        expr: Any,
        expr_d: dict[str, Any],
        none_non_any_literal: str,
        none_any_literal: str,
        bytes_ctor_name: str = "bytes",
        bytes_lit_fn_name: str = "py_bytes_lit",
    ) -> str:
        """Constant ノードの基本描画を共通化する。"""
        v = expr_d.get("value")
        common_pair = self.render_constant_non_string_common(
            expr,
            expr_d,
            none_non_any_literal,
            none_any_literal,
        )
        common_handled = str(common_pair[0]) == "1"
        common_non_str = str(common_pair[1])
        if common_handled:
            return common_non_str
        if isinstance(v, str):
            v_txt = str(v)
            v_ty = self.get_expr_type(expr)
            if v_ty in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
                try:
                    int(v_txt)
                    return v_txt
                except Exception:
                    pass
            if v_ty in {"float32", "float64"}:
                try:
                    float(v_txt)
                    return v_txt
                except Exception:
                    pass
            if v_ty == "bytes":
                raw = self.any_to_str(expr_d.get("repr"))
                if raw != "":
                    qpos = -1
                    for i, ch in enumerate(raw):
                        if ch in {'"', "'"}:
                            qpos = i
                            break
                    if qpos >= 0:
                        return f"{bytes_lit_fn_name}({raw[qpos:]})"
                return f"{bytes_ctor_name}({self.quote_string_literal(v_txt)})"
            return self.quote_string_literal(v_txt)
        return str(v)

    def _normalize_runtime_module_name(self, module_name: str) -> str:
        """言語固有の module 名正規化ポイント。既定実装は入力をそのまま返す。"""
        return module_name

    def _lookup_module_attr_runtime_call(self, module_name: str, attr: str) -> str:
        """`module.attr` -> runtime_call 解決ポイント。既定実装は未解決。"""
        _ = module_name
        _ = attr
        return ""

    def _module_name_to_cpp_namespace(self, module_name: str) -> str:
        """module 名 -> C++ namespace 解決ポイント。既定実装は未解決。"""
        _ = module_name
        return ""

    def _make_missing_symbol_import_error(self, base_name: str, attr: str) -> Exception:
        """`from-import` 束縛名の module 参照エラーを生成する。"""
        return RuntimeError(
            "Module names are not bound by from-import statements: "
            + base_name
            + "."
            + attr
        )

    def render_attribute_expr_common(self, expr_d: dict[str, Any]) -> str:
        """Attribute ノードの基本描画を共通化する。"""
        owner_t = self.get_expr_type(expr_d.get("value"))
        if self.is_forbidden_object_receiver_type(owner_t):
            raise RuntimeError(
                "object receiver method call / attribute access is forbidden by language constraints"
            )
        base_rendered = self.render_expr(expr_d.get("value"))
        base_ctx = self.resolve_attribute_owner_context(expr_d.get("value"), base_rendered)
        base = self.any_dict_get_str(base_ctx, "expr", "")
        base_node = self.any_to_dict_or_empty(base_ctx.get("node"))
        base_kind = self._node_kind_from_dict(base_node)
        attr = self.attr_name(expr_d)
        direct_self_or_class = self.render_attribute_self_or_class_access(
            base,
            attr,
            self.current_class_name,
            self.current_class_static_fields,
            self.class_base,
            self.class_method_names,
        )
        if direct_self_or_class != "":
            return direct_self_or_class
        base_module_name = self._normalize_runtime_module_name(
            self.any_dict_get_str(base_ctx, "module", "")
        )
        if base_module_name != "":
            mapped = self._lookup_module_attr_runtime_call(base_module_name, attr)
            ns = self._module_name_to_cpp_namespace(base_module_name)
            direct_module = self.render_attribute_module_access(
                base_module_name,
                attr,
                mapped,
                ns,
            )
            if direct_module != "":
                return direct_module
        if base_kind == "Name":
            base_name = self.any_to_str(base_node.get("id"))
            if (
                base_name != ""
                and not self.is_declared(base_name)
                and base_name not in self.import_modules
                and base_name in self.import_symbol_modules
            ):
                raise self._make_missing_symbol_import_error(base_name, attr)
        bt = self.get_expr_type(expr_d.get("value"))
        if bt in self.ref_classes:
            return f"{base}->{attr}"
        return f"{base}.{attr}"

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

    def _is_empty_dynamic_text(txt: str) -> bool:
        """動的値から得た文字列が有効値かどうかを判定する。"""
        return txt in {"", "None", "{}", "[]"}

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
        if self._is_empty_dynamic_text(s2):
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

    def tuple_elements(self, tuple_node: dict[str, Any]) -> list[Any]:
        """Tuple ノード要素を `elements` / `elts` 両対応で返す。"""
        out = self.any_to_list(tuple_node.get("elements"))
        if len(out) > 0:
            return out
        return self.any_to_list(tuple_node.get("elts"))

    def fallback_tuple_target_names_from_repr(self, target: dict[str, Any]) -> list[str]:
        """tuple target 要素が欠落したとき、`repr` から識別子候補を復元する。"""
        out: list[str] = []
        repr_txt = self.any_dict_get_str(target, "repr", "")
        if repr_txt == "" or "," not in repr_txt:
            return out
        parts: list[str] = []
        cur = ""
        for ch in repr_txt:
            if ch == ",":
                parts.append(cur.strip())
                cur = ""
            else:
                cur += ch
        parts.append(cur.strip())
        for nm in parts:
            if nm == "":
                continue
            ok = True
            for i, ch in enumerate(nm):
                if i == 0:
                    is_head_ok = ch == "_" or (("a" <= ch) and (ch <= "z")) or (("A" <= ch) and (ch <= "Z"))
                    if not is_head_ok:
                        ok = False
                        break
                else:
                    is_body_ok = (
                        ch == "_"
                        or (("a" <= ch) and (ch <= "z"))
                        or (("A" <= ch) and (ch <= "Z"))
                        or (("0" <= ch) and (ch <= "9"))
                    )
                    if not is_body_ok:
                        ok = False
                        break
            if ok:
                out.append(nm)
        return out

    def fallback_tuple_target_names_from_stmt(
        self,
        target: dict[str, Any],
        stmt: dict[str, Any],
    ) -> list[str]:
        """`target` と `stmt` の `repr` を使ってタプル代入名の復元を試みる。"""
        fallback_names = self.fallback_tuple_target_names_from_repr(target)
        if len(fallback_names) > 0:
            return fallback_names
        stmt_repr = self.any_dict_get_str(stmt, "repr", "")
        if stmt_repr == "":
            return fallback_names
        eq_pos = stmt_repr.find("=")
        lhs_txt = stmt_repr
        if eq_pos >= 0:
            lhs_txt = stmt_repr[:eq_pos]
        if lhs_txt == "":
            return fallback_names
        pseudo_target = {"repr": lhs_txt}
        return self.fallback_tuple_target_names_from_repr(pseudo_target)

    def target_bound_names(self, target: dict[str, Any]) -> set[str]:
        """for ターゲットが束縛する識別子名を収集する。"""
        names: set[str] = set()
        if not isinstance(target, dict) or len(target) == 0:
            return names
        kind = self._node_kind_from_dict(target)
        if kind == "Name":
            names.add(self.any_dict_get_str(target, "id", "_"))
            return names
        if kind == "Tuple":
            elems = self.tuple_elements(target)
            for elem in elems:
                e_dict = self.any_to_dict_or_empty(elem)
                if self._node_kind_from_dict(e_dict) == "Name":
                    names.add(self.any_dict_get_str(e_dict, "id", "_"))
        return names

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
        if self._is_empty_dynamic_text(txt):
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
                if not self._is_empty_dynamic_text(txt):
                    return self.normalize_type_name(txt)
            elif raw is not None and not isinstance(raw, bool) and not isinstance(raw, int) and not isinstance(raw, float):
                if not isinstance(raw, dict) and not isinstance(raw, list) and not isinstance(raw, set):
                    txt2 = str(raw)
                    if not self._is_empty_dynamic_text(txt2):
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
        if self._is_empty_dynamic_text(txt):
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

    @staticmethod
    def load_type_map(
        profile: dict[str, Any],
        defaults: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """profile `types`（`types.types` 互換）を型マップとして読み込む。"""
        out: dict[str, str] = {}
        if isinstance(defaults, dict):
            for key, val in defaults.items():
                if isinstance(key, str) and isinstance(val, str) and key != "" and val != "":
                    out[key] = val
        if not isinstance(profile, dict):
            return out
        raw_types = profile.get("types")
        type_section = raw_types if isinstance(raw_types, dict) else {}
        nested_types = type_section.get("types")
        source = nested_types if isinstance(nested_types, dict) and len(nested_types) > 0 else type_section
        for key, val in source.items():
            if isinstance(key, str) and isinstance(val, str) and key != "" and val != "":
                out[key] = val
        return out

    def normalize_type_and_lookup_map(
        self,
        east_type: str,
        type_map: dict[str, str],
    ) -> tuple[str, str]:
        """型名を正規化し、`type_map` の直接マッピング結果を返す。"""
        norm = self.normalize_type_name(east_type)
        if norm == "":
            return "", ""
        mapped = ""
        if norm in type_map:
            mapped = self.any_to_str(type_map.get(norm))
        if mapped == "":
            return norm, ""
        return norm, mapped

    def split_union_non_none(self, union_type: str) -> tuple[list[str], bool]:
        """Union 型を `None` とそれ以外（重複除去）へ分解する。"""
        t = self.normalize_type_name(union_type)
        if t == "":
            return [], False
        if t.find("|") < 0:
            if t == "None":
                return [], True
            return [t], False
        parts = self.split_union(t)
        non_none: list[str] = []
        seen: set[str] = set()
        has_none = False
        for part in parts:
            p = self.normalize_type_name(part)
            if p == "":
                continue
            if p == "None":
                has_none = True
                continue
            if p in seen:
                continue
            seen.add(p)
            non_none.append(p)
        return non_none, has_none

    def type_generic_args(self, east_type: str, base_name: str) -> list[str]:
        """`list[T]` などの generic 型引数を `base_name` 指定で返す。"""
        t = self.normalize_type_name(east_type)
        if t == "":
            return []
        prefix = base_name + "["
        if not t.startswith(prefix) or not t.endswith("]"):
            return []
        inner = t[len(prefix):-1].strip()
        if inner == "":
            return []
        return self.split_generic(inner)

    def render_boolop_common(
        self,
        values: list[Any],
        op: str,
        *,
        and_token: str = "&&",
        or_token: str = "||",
        empty_literal: str = "false",
    ) -> str:
        """`BoolOp`（And/Or）の共通描画を行う。"""
        return self.render_boolop_chain_common(
            values,
            op,
            and_token,
            or_token,
            empty_literal,
            False,
            True,
        )

    def render_boolop_chain_common(
        self,
        values: list[Any],
        op: str,
        and_token: str = "&&",
        or_token: str = "||",
        empty_literal: str = "false",
        wrap_each: bool = False,
        wrap_whole: bool = True,
    ) -> str:
        """`BoolOp` のトークン連結を共通描画する。"""
        mapped = and_token
        if op == "Or":
            mapped = or_token
        rendered: list[str] = []
        for val in values:
            txt = self.render_expr(val)
            if wrap_each:
                txt = "(" + txt + ")"
            rendered.append(txt)
        if len(rendered) == 0:
            return empty_literal
        out = (" " + mapped + " ").join(rendered)
        if wrap_whole:
            return "(" + out + ")"
        return out

    def render_compare_chain_common(
        self,
        left_expr: str,
        ops: list[str],
        comparators: list[Any],
        cmp_map: dict[str, str],
        *,
        empty_literal: str = "false",
        in_pattern: str = "",
        not_in_pattern: str = "",
    ) -> str:
        """比較連鎖（`a < b < c`）の共通描画を行う。"""
        if len(ops) == 0 or len(comparators) == 0:
            return empty_literal
        right_exprs: list[str] = []
        pair_count = len(ops)
        if len(comparators) < pair_count:
            pair_count = len(comparators)
        for i in range(pair_count):
            right_exprs.append(self.render_expr(comparators[i]))
        return self.render_compare_chain_from_rendered(
            left_expr,
            ops,
            right_exprs,
            cmp_map,
            empty_literal,
            in_pattern,
            not_in_pattern,
            True,
            True,
        )

    def render_compare_chain_from_rendered(
        self,
        left_expr: str,
        ops: list[str],
        right_exprs: list[str],
        cmp_map: dict[str, str],
        empty_literal: str = "false",
        in_pattern: str = "",
        not_in_pattern: str = "",
        wrap_terms: bool = False,
        wrap_whole: bool = False,
    ) -> str:
        """描画済み比較項から比較連鎖を組み立てる。"""
        if len(ops) == 0 or len(right_exprs) == 0:
            return empty_literal
        terms: list[str] = []
        cur_left = left_expr
        pair_count = len(ops)
        if len(right_exprs) < pair_count:
            pair_count = len(right_exprs)
        for i in range(pair_count):
            op = ops[i]
            right = right_exprs[i]
            term: str = ""
            if op == "In" and in_pattern != "":
                term = in_pattern.replace("{left}", cur_left).replace("{right}", right)
            elif op == "NotIn" and not_in_pattern != "":
                term = not_in_pattern.replace("{left}", cur_left).replace("{right}", right)
            else:
                op_txt = cmp_map.get(op, "==")
                term = cur_left + " " + op_txt + " " + right
            if wrap_terms:
                term = "(" + term + ")"
            terms.append(term)
            cur_left = right
        if len(terms) == 0:
            return empty_literal
        if len(terms) == 1:
            return terms[0]
        out = " && ".join(terms)
        if wrap_whole:
            return "(" + out + ")"
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
        """現在スコープへ宣言済み名を追加する。"""
        if len(self.scope_stack) == 0:
            self.scope_stack.append(set())
        self.scope_stack[-1].add(name)

    def is_declared(self, name: str) -> bool:
        """指定名がどこかの有効スコープで宣言済みか判定する。"""
        for i in range(len(self.scope_stack) - 1, -1, -1):
            scope: set[str] = self.scope_stack[i]
            if name in scope:
                return True
        return False

    def primary_assign_target(self, stmt: dict[str, Any]) -> dict[str, Any]:
        """`Assign` から主対象ノード（`target` / 先頭 `targets`）を返す。"""
        target = self.any_to_dict_or_empty(stmt.get("target"))
        if len(target) > 0:
            return target
        targets = self._dict_stmt_list(stmt.get("targets"))
        if len(targets) > 0:
            return targets[0]
        return {}

    def emit_tuple_assign_with_tmp(
        self,
        target_node: dict[str, Any],
        value_expr: str,
        *,
        tmp_prefix: str = "__tmp",
        tmp_decl_template: str = "auto {tmp} = {value};",
        item_expr_template: str = "{tmp}[{index}]",
        assign_template: str = "{target} = {item};",
        index_offset: int = 0,
    ) -> bool:
        """2要素 tuple 代入の `tmp` lower を共通出力する。"""
        if self.any_dict_get_str(target_node, "kind", "") != "Tuple":
            return False
        names = self.tuple_elements(target_node)
        if len(names) != 2:
            return False
        rendered_targets: list[str] = []
        for node in names:
            rendered_targets.append(self.render_expr(node))
        tmp_name = self.next_tmp(tmp_prefix)
        self.emit(
            tmp_decl_template.replace("{tmp}", tmp_name).replace("{value}", value_expr)
        )
        for i, target_txt in enumerate(rendered_targets):
            idx_txt = str(i + index_offset)
            item_expr = item_expr_template.replace("{tmp}", tmp_name).replace("{index}", idx_txt)
            line = (
                assign_template.replace("{target}", target_txt).replace("{item}", item_expr)
            )
            self.emit(line)
        return True

    def should_declare_name_binding(
        self,
        stmt: dict[str, Any],
        name_raw: str,
        default_declare: bool,
    ) -> bool:
        """Name 代入時に新規宣言が必要かを共通判定する。"""
        if name_raw == "":
            return False
        declare = self.stmt_declare_flag(stmt, default_declare)
        return declare and not self.is_declared(name_raw)

    def stmt_declare_flag(self, stmt: dict[str, Any], default_declare: bool) -> bool:
        """`stmt.declare` を bool/int 互換で解釈し、宣言フラグを返す。"""
        if not isinstance(stmt, dict):
            return default_declare
        if "declare" not in stmt:
            return default_declare
        raw = stmt.get("declare")
        if isinstance(raw, bool):
            return bool(raw)
        if isinstance(raw, int):
            return raw != 0
        return default_declare

    def render_augassign_basic(
        self,
        stmt: dict[str, Any],
        aug_ops: dict[str, str],
        default_op: str = "+=",
    ) -> tuple[str, str, str]:
        """`AugAssign` の target/value/op を共通取得する。"""
        target = self.render_expr(stmt.get("target"))
        value = self.render_expr(stmt.get("value"))
        op = self.any_to_str(stmt.get("op"))
        mapped = aug_ops.get(op, default_op)
        if mapped == "":
            mapped = default_op
        return target, value, mapped

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

    def render_truthy_cond_common(
        self,
        expr: Any,
        str_non_empty_pattern: str,
        collection_non_empty_pattern: str,
        number_non_zero_pattern: str = "{expr} != 0",
    ) -> str:
        """条件式向けの truthy 判定（str/collection/number）を共通描画する。"""
        node = self.any_to_dict_or_empty(expr)
        if len(node) == 0:
            return "false"
        t = self.get_expr_type(expr)
        rendered = self._strip_outer_parens(self.render_expr(expr))
        if rendered == "":
            return "false"
        if t == "bool":
            return rendered
        if t == "str":
            return str_non_empty_pattern.replace("{expr}", rendered)
        if t.startswith("list[") or t.startswith("dict[") or t.startswith("set[") or t.startswith("tuple["):
            return collection_non_empty_pattern.replace("{expr}", rendered)
        if t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64"}:
            return number_non_zero_pattern.replace("{expr}", rendered)
        return rendered

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

    def load_import_bindings_from_meta(self, meta: dict[str, Any]) -> None:
        """`meta.import_bindings`（+ legacy メタ）から import 解決テーブルを初期化する。"""
        self.import_modules = {}
        self.import_symbols = {}
        self.import_symbol_modules = set()

        binds = self.any_to_dict_list(meta.get("import_bindings"))
        refs = self.any_to_dict_list(meta.get("qualified_symbol_refs"))

        if len(binds) > 0:
            for ref in refs:
                self._add_symbol_binding(
                    self.any_to_str(ref.get("local_name")),
                    self.any_to_str(ref.get("module_id")),
                    self.any_to_str(ref.get("symbol")),
                )

            for ent in binds:
                binding_kind = self.any_to_str(ent.get("binding_kind"))
                local_name = self.any_to_str(ent.get("local_name"))
                module_id = self.any_to_str(ent.get("module_id"))
                if binding_kind == "module":
                    if local_name != "" and module_id != "":
                        self.import_modules[local_name] = module_id
                elif binding_kind == "symbol" and len(refs) == 0:
                    self._add_symbol_binding(local_name, module_id, self.any_to_str(ent.get("export_name")))

            if len(self.import_symbols) == 0:
                legacy_symbols = self.any_to_dict_or_empty(meta.get("import_symbols"))
                for local_name_obj, sym_obj in legacy_symbols.items():
                    if not isinstance(local_name_obj, str):
                        continue
                    local_name = local_name_obj
                    sym = sym_obj if isinstance(sym_obj, dict) else {}
                    self._add_symbol_binding(
                        local_name,
                        self.any_dict_get_str(sym, "module", ""),
                        self.any_dict_get_str(sym, "name", ""),
                    )
            if len(self.import_modules) == 0:
                legacy_modules = self.any_to_dict_or_empty(meta.get("import_modules"))
                for local_name_obj, module_id_obj in legacy_modules.items():
                    if not isinstance(local_name_obj, str):
                        continue
                    module_id = self.any_to_str(module_id_obj)
                    if module_id != "":
                        self.import_modules[local_name_obj] = module_id
            return

        legacy_symbols_fallback = self.any_to_dict_or_empty(meta.get("import_symbols"))
        for local_name_obj, sym_obj in legacy_symbols_fallback.items():
            if not isinstance(local_name_obj, str):
                continue
            local_name = local_name_obj
            sym = sym_obj if isinstance(sym_obj, dict) else {}
            self._add_symbol_binding(
                local_name,
                self.any_dict_get_str(sym, "module", ""),
                self.any_dict_get_str(sym, "name", ""),
            )
        legacy_modules_fallback = self.any_to_dict_or_empty(meta.get("import_modules"))
        for local_name_obj, module_id_obj in legacy_modules_fallback.items():
            if not isinstance(local_name_obj, str):
                continue
            module_id = self.any_to_str(module_id_obj)
            if module_id != "":
                self.import_modules[local_name_obj] = module_id

    def _add_symbol_binding(self, local_name: str, module_id: str, export_name: str) -> None:
        """from-import のローカル束縛を import 解決テーブルへ追加する。"""
        if local_name == "" or module_id == "" or export_name == "":
            return
        sym: dict[str, str] = {}
        sym["module"] = module_id
        sym["name"] = export_name
        self.import_symbols[local_name] = sym
        self.import_symbol_modules.add(module_id)

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
        if self._is_empty_dynamic_text(text):
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

    def render_attribute_self_or_class_access(
        self,
        base: str,
        attr: str,
        current_class_name: str | None,
        current_class_static_fields: set[str],
        class_base: dict[str, str],
        class_method_names: dict[str, set[str]],
    ) -> str:
        """`self.x` / `Class.x` の基本変換を共通処理する。"""
        if base == "self" or base == "*this":
            if current_class_name is not None and attr in current_class_static_fields:
                return f"{current_class_name}::{attr}"
            return f"this->{attr}"
        if base in class_base or base in class_method_names:
            return f"{base}::{attr}"
        return ""

    def render_attribute_module_access(
        self,
        base_module_name: str,
        attr: str,
        mapped_runtime: str,
        namespace_name: str,
    ) -> str:
        """`module.attr` の基本変換（runtime map / namespace）を共通処理する。"""
        if base_module_name == "" or attr == "":
            return ""
        if mapped_runtime != "":
            return mapped_runtime
        if namespace_name != "":
            return f"{namespace_name}::{attr}"
        return ""

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

    def _emit_passthrough_directive_line(self, directive: dict[str, Any]) -> bool:
        """pass-through directive が line の場合に行を出力する。"""
        if self.any_dict_get_str(directive, "kind", "") != "line":
            return False
        line_txt = self.any_dict_get_str(directive, "text", "")
        if line_txt != "":
            self.emit(line_txt)
        return True

    def _handle_comment_trivia_directive(self, txt: str) -> bool:
        """コメント trivia の pass-through directive を処理したら True を返す。"""
        directive = self._parse_passthrough_comment(txt)
        d_kind = self.any_dict_get_str(directive, "kind", "")
        if self.passthrough_cpp_block:
            if d_kind == "end":
                self.passthrough_cpp_block = False
                return True
            if d_kind == "begin":
                return True
            if self._emit_passthrough_directive_line(directive):
                return True
            self.emit(txt)
            return True
        if d_kind == "begin":
            self.passthrough_cpp_block = True
            return True
        if d_kind == "end":
            return True
        if self._emit_passthrough_directive_line(directive):
            return True
        return False

    def _emit_blank_trivia_item(self, item: dict[str, Any]) -> None:
        """blank trivia を空行として出力する。"""
        cnt = self.any_dict_get_int(item, "count", 1)
        n = cnt if cnt > 0 else 1
        for _ in range(n):
            self.emit("")

    def _emit_trivia_items(self, trivia: list[dict[str, Any]]) -> None:
        """trivia をコメント/空行/パススルー行として出力する。"""
        for item in trivia:
            k = self.any_dict_get_str(item, "kind", "")
            if k == "comment":
                txt = self.any_dict_get_str(item, "text", "")
                if self._handle_comment_trivia_directive(txt):
                    continue
                self.emit(self.comment_line_prefix() + txt)
            elif k == "blank":
                self._emit_blank_trivia_item(item)

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
        return self.render_ifexp_common(test_expr, body, orelse)

    def render_ifexp_common(
        self,
        test_expr: str,
        body_expr: str,
        orelse_expr: str,
        *,
        test_node: dict[str, Any] | None = None,
        fold_bool_literal: bool = False,
    ) -> str:
        """IfExp の式組み立てを共通化する。"""
        if fold_bool_literal:
            node = test_node if isinstance(test_node, dict) else {}
            if self._node_kind_from_dict(node) == "Constant" and isinstance(node.get("value"), bool):
                return body_expr if bool(node.get("value")) else orelse_expr
            if self._node_kind_from_dict(node) == "Name":
                ident = self.any_to_str(node.get("id"))
                if ident == "True":
                    return body_expr
                if ident == "False":
                    return orelse_expr
            t = test_expr.strip()
            if t == "true":
                return body_expr
            if t == "false":
                return orelse_expr
        return f"({test_expr} ? {body_expr} : {orelse_expr})"

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
