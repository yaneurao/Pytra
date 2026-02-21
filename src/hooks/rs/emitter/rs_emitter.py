"""EAST -> Rust transpiler."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.rs.hooks.rs_hooks import build_rs_hooks
from pytra.compiler.east_parts.code_emitter import CodeEmitter
from pytra.std import json
from pytra.std.pathlib import Path


def rust_string_lit(text: str) -> str:
    """Rust の文字列リテラルへエスケープ変換する。"""
    out = "\""
    i = 0
    while i < len(text):
        ch = text[i : i + 1]
        if ch == "\\":
            out += "\\\\"
        elif ch == "\"":
            out += "\\\""
        elif ch == "\n":
            out += "\\n"
        elif ch == "\r":
            out += "\\r"
        elif ch == "\t":
            out += "\\t"
        else:
            out += ch
        i += 1
    out += "\""
    return out


def _load_profile_piece(path: Path) -> dict[str, Any]:
    """JSON プロファイル断片を読み込む。失敗時は空 dict。"""
    if not path.exists():
        return {}
    try:
        txt = path.read_text(encoding="utf-8")
        raw = json.loads(txt)
    except Exception:
        return {}
    if isinstance(raw, dict):
        return raw
    return {}


def load_rs_profile() -> dict[str, Any]:
    """Rust 用 profile を読み込む。"""
    profile_path = Path("src/profiles/rs/profile.json")
    profile_root = profile_path.parent
    meta = _load_profile_piece(profile_path)
    out: dict[str, Any] = {}
    includes_obj = meta.get("include")
    includes: list[str] = []
    if isinstance(includes_obj, list):
        for item in includes_obj:
            if isinstance(item, str) and item != "":
                includes.append(item)
    i = 0
    while i < len(includes):
        rel = includes[i]
        piece = _load_profile_piece(profile_root / rel)
        for key, val in piece.items():
            out[key] = val
        i += 1
    for key, val in meta.items():
        if key != "include":
            out[key] = val
    return out


def load_rs_hooks(profile: dict[str, Any]) -> dict[str, Any]:
    """Rust 用 hook を読み込む。"""
    _ = profile
    hooks = build_rs_hooks()
    if isinstance(hooks, dict):
        return hooks
    return {}


class RustEmitter(CodeEmitter):
    """EAST を Rust ソースへ変換する最小エミッタ。"""

    def __init__(self, east_doc: dict[str, Any]) -> None:
        profile = load_rs_profile()
        hooks = load_rs_hooks(profile)
        self.init_base_state(east_doc, profile, hooks)
        raw_types = self.any_to_dict_or_empty(profile.get("types"))
        nested_types = self.any_to_dict_or_empty(raw_types.get("types"))
        if len(nested_types) > 0:
            self.type_map = self.any_to_str_dict_or_empty(nested_types)
        else:
            self.type_map = self.any_to_str_dict_or_empty(raw_types)
        operators = self.any_to_dict_or_empty(profile.get("operators"))
        self.bin_ops = self.any_to_str_dict_or_empty(operators.get("binop"))
        self.cmp_ops = self.any_to_str_dict_or_empty(operators.get("cmp"))
        self.aug_ops = self.any_to_str_dict_or_empty(operators.get("aug"))
        syntax = self.any_to_dict_or_empty(profile.get("syntax"))
        identifiers = self.any_to_dict_or_empty(syntax.get("identifiers"))
        self.reserved_words: set[str] = set(self.any_to_str_list(identifiers.get("reserved_words")))
        self.rename_prefix = self.any_to_str(identifiers.get("rename_prefix"))
        if self.rename_prefix == "":
            self.rename_prefix = "py_"
        self.function_return_types: dict[str, str] = {}
        self.class_names: set[str] = set()
        self.class_field_types: dict[str, dict[str, str]] = {}
        self.declared_var_types: dict[str, str] = {}

    def get_expr_type(self, expr: Any) -> str:
        """解決済み型 + ローカル宣言テーブルで式型を返す。"""
        t = super().get_expr_type(expr)
        if t not in {"", "unknown"}:
            return t
        node = self.any_to_dict_or_empty(expr)
        if self.any_dict_get_str(node, "kind", "") == "Name":
            name = self.any_dict_get_str(node, "id", "")
            if name in self.declared_var_types:
                return self.normalize_type_name(self.declared_var_types[name])
        return t

    def _safe_name(self, name: str) -> str:
        return self.rename_if_reserved(name, self.reserved_words, self.rename_prefix, {})

    def _tuple_elements(self, tuple_node: dict[str, Any]) -> list[Any]:
        """Tuple ノード要素を `elements` / `elts` 両対応で返す。"""
        out = self.any_to_list(tuple_node.get("elements"))
        if len(out) > 0:
            return out
        return self.any_to_list(tuple_node.get("elts"))

    def _module_id_to_rust_use_path(self, module_id: str) -> str:
        """Python 形式モジュール名を Rust `use` パスへ変換する。"""
        if module_id == "":
            return ""
        return "crate::" + module_id.replace(".", "::")

    def _collect_use_lines(self, body: list[dict[str, Any]], meta: dict[str, Any]) -> list[str]:
        """import 情報を Rust `use` 行へ変換する。"""
        out: list[str] = []
        seen: set[str] = set()

        def _add(line: str) -> None:
            if line == "" or line in seen:
                return
            seen.add(line)
            out.append(line)

        bindings = self.any_to_dict_list(meta.get("import_bindings"))
        if len(bindings) > 0:
            i = 0
            while i < len(bindings):
                ent = bindings[i]
                binding_kind = self.any_to_str(ent.get("binding_kind"))
                module_id = self.any_to_str(ent.get("module_id"))
                local_name = self.any_to_str(ent.get("local_name"))
                export_name = self.any_to_str(ent.get("export_name"))
                if module_id.startswith("__future__") or module_id in {"typing", "pytra.std.typing"}:
                    i += 1
                    continue
                base_path = self._module_id_to_rust_use_path(module_id)
                if binding_kind == "module" and base_path != "":
                    line = "use " + base_path
                    leaf = self._last_dotted_name(module_id)
                    if local_name != "" and local_name != leaf:
                        line += " as " + self._safe_name(local_name)
                    _add(line + ";")
                elif binding_kind == "symbol" and base_path != "" and export_name != "":
                    line = "use " + base_path + "::" + export_name
                    if local_name != "" and local_name != export_name:
                        line += " as " + self._safe_name(local_name)
                    _add(line + ";")
                i += 1
            return out

        for stmt in body:
            kind = self.any_dict_get_str(stmt, "kind", "")
            if kind == "Import":
                for ent in self._dict_stmt_list(stmt.get("names")):
                    module_id = self.any_to_str(ent.get("name"))
                    if module_id == "" or module_id.startswith("__future__") or module_id in {"typing", "pytra.std.typing"}:
                        continue
                    base_path = self._module_id_to_rust_use_path(module_id)
                    if base_path == "":
                        continue
                    asname = self.any_to_str(ent.get("asname"))
                    line = "use " + base_path
                    leaf = self._last_dotted_name(module_id)
                    if asname != "" and asname != leaf:
                        line += " as " + self._safe_name(asname)
                    _add(line + ";")
            elif kind == "ImportFrom":
                module_id = self.any_to_str(stmt.get("module"))
                if module_id == "" or module_id.startswith("__future__") or module_id in {"typing", "pytra.std.typing"}:
                    continue
                base_path = self._module_id_to_rust_use_path(module_id)
                if base_path == "":
                    continue
                for ent in self._dict_stmt_list(stmt.get("names")):
                    name = self.any_to_str(ent.get("name"))
                    if name == "":
                        continue
                    asname = self.any_to_str(ent.get("asname"))
                    line = "use " + base_path + "::" + name
                    if asname != "" and asname != name:
                        line += " as " + self._safe_name(asname)
                    _add(line + ";")
        return out

    def _infer_default_for_type(self, east_type: str) -> str:
        """型ごとの既定値（Rust）を返す。"""
        t = self.normalize_type_name(east_type)
        if t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
            return "0"
        if t in {"float32", "float64"}:
            return "0.0"
        if t == "bool":
            return "false"
        if t == "str":
            return "String::new()"
        if t == "bytes" or t == "bytearray" or t.startswith("list["):
            return "Vec::new()"
        if t.startswith("set["):
            return "::std::collections::BTreeSet::new()"
        if t.startswith("dict["):
            return "::std::collections::BTreeMap::new()"
        if t.startswith("tuple["):
            return "()"
        if t == "None":
            return "()"
        if t.startswith("Option[") and t.endswith("]"):
            return "None"
        if t in self.class_names:
            return f"{t}::new()"
        return "Default::default()"

    def _rust_type(self, east_type: str) -> str:
        """EAST 型名を Rust 型名へ変換する。"""
        t = self.normalize_type_name(east_type)
        if t == "":
            return "i64"
        if t in self.type_map:
            mapped = self.type_map[t]
            if mapped != "":
                return mapped
        if t.startswith("list[") and t.endswith("]"):
            inner = t[5:-1].strip()
            return f"Vec<{self._rust_type(inner)}>"
        if t.startswith("set[") and t.endswith("]"):
            inner = t[4:-1].strip()
            return f"::std::collections::BTreeSet<{self._rust_type(inner)}>"
        if t.startswith("dict[") and t.endswith("]"):
            parts = self.split_generic(t[5:-1].strip())
            if len(parts) == 2:
                return (
                    "::std::collections::BTreeMap<"
                    + self._rust_type(parts[0])
                    + ", "
                    + self._rust_type(parts[1])
                    + ">"
                )
        if t.startswith("tuple[") and t.endswith("]"):
            parts = self.split_generic(t[6:-1].strip())
            rendered: list[str] = []
            for part in parts:
                rendered.append(self._rust_type(part))
            if len(rendered) == 1:
                return f"({rendered[0]},)"
            return "(" + ", ".join(rendered) + ")"
        if t.find("|") >= 0:
            parts = self.split_union(t)
            non_none: list[str] = []
            has_none = False
            for part in parts:
                if part == "None":
                    has_none = True
                else:
                    non_none.append(part)
            if has_none and len(non_none) == 1:
                return f"Option<{self._rust_type(non_none[0])}>"
            return "String"
        if t == "None":
            return "()"
        return t

    def transpile(self) -> str:
        """モジュール全体を Rust ソースへ変換する。"""
        self.lines = []
        self.scope_stack = [set()]
        self.declared_var_types = {}

        module = self.doc
        body = self._dict_stmt_list(module.get("body"))
        meta = self.any_to_dict_or_empty(module.get("meta"))
        self.load_import_bindings_from_meta(meta)
        self.emit_module_leading_trivia()
        use_lines = self._collect_use_lines(body, meta)
        for line in use_lines:
            self.emit(line)
        if len(use_lines) > 0:
            self.emit("")

        self.class_names = set()
        self.function_return_types = {}
        for stmt in body:
            kind = self.any_dict_get_str(stmt, "kind", "")
            if kind == "ClassDef":
                class_name = self.any_to_str(stmt.get("name"))
                if class_name != "":
                    self.class_names.add(class_name)
            if kind == "FunctionDef":
                fn_name = self.any_to_str(stmt.get("name"))
                ret_type = self.normalize_type_name(self.any_to_str(stmt.get("return_type")))
                if fn_name != "":
                    self.function_return_types[fn_name] = ret_type

        top_level_stmts: list[dict[str, Any]] = []
        for stmt in body:
            kind = self.any_dict_get_str(stmt, "kind", "")
            if kind == "Import" or kind == "ImportFrom":
                continue
            if kind == "FunctionDef":
                self.emit_leading_comments(stmt)
                self._emit_function(stmt, in_class=None)
                self.emit("")
                continue
            if kind == "ClassDef":
                self.emit_leading_comments(stmt)
                self._emit_class(stmt)
                self.emit("")
                continue
            top_level_stmts.append(stmt)

        main_guard_body = self._dict_stmt_list(module.get("main_guard_body"))
        should_emit_main = len(main_guard_body) > 0 or len(top_level_stmts) > 0
        if should_emit_main:
            self.emit("fn main() {")
            scope: set[str] = set()
            self.emit_scoped_stmt_list(top_level_stmts + main_guard_body, scope)
            self.emit("}")

        return "\n".join(self.lines) + ("\n" if len(self.lines) > 0 else "")

    def _emit_class(self, stmt: dict[str, Any]) -> None:
        """ClassDef を最小構成の `struct + impl` として出力する。"""
        class_name = self._safe_name(self.any_to_str(stmt.get("name")))
        field_types = self.any_to_dict_or_empty(stmt.get("field_types"))
        norm_field_types: dict[str, str] = {}
        for key, val in field_types.items():
            if isinstance(key, str):
                norm_field_types[key] = self.normalize_type_name(self.any_to_str(val))
        self.class_field_types[class_name] = norm_field_types

        if len(norm_field_types) == 0:
            self.emit(f"struct {class_name};")
        else:
            self.emit(f"struct {class_name} {{")
            self.indent += 1
            for name, t in norm_field_types.items():
                self.emit(f"{self._safe_name(name)}: {self._rust_type(t)},")
            self.indent -= 1
            self.emit("}")

        self.emit(f"impl {class_name} {{")
        self.indent += 1
        self._emit_constructor(class_name, stmt, norm_field_types)
        members = self._dict_stmt_list(stmt.get("body"))
        for member in members:
            if self.any_dict_get_str(member, "kind", "") != "FunctionDef":
                continue
            name = self.any_to_str(member.get("name"))
            if name == "__init__":
                continue
            self.emit("")
            self._emit_function(member, in_class=class_name)
        self.indent -= 1
        self.emit("}")

    def _emit_constructor(self, class_name: str, cls: dict[str, Any], field_types: dict[str, str]) -> None:
        """`__init__` から `new` を生成する。"""
        init_fn: dict[str, Any] | None = None
        body = self._dict_stmt_list(cls.get("body"))
        for member in body:
            if self.any_dict_get_str(member, "kind", "") == "FunctionDef" and self.any_to_str(member.get("name")) == "__init__":
                init_fn = member
                break

        arg_items: list[str] = []
        init_scope: set[str] = set()
        if init_fn is not None:
            arg_order = self.any_to_str_list(init_fn.get("arg_order"))
            arg_types = self.any_to_dict_or_empty(init_fn.get("arg_types"))
            for arg_name in arg_order:
                if arg_name == "self":
                    continue
                arg_type = self._rust_type(self.any_to_str(arg_types.get(arg_name)))
                safe = self._safe_name(arg_name)
                arg_items.append(f"{safe}: {arg_type}")
                init_scope.add(arg_name)

        args_text = ", ".join(arg_items)
        self.emit(f"fn new({args_text}) -> Self {{")
        self.indent += 1

        field_values: dict[str, str] = {}
        for field_name, field_t in field_types.items():
            field_values[field_name] = self._infer_default_for_type(field_t)

        if init_fn is not None:
            init_body = self._dict_stmt_list(init_fn.get("body"))
            for stmt in init_body:
                if self.any_dict_get_str(stmt, "kind", "") == "Assign":
                    target = self.any_to_dict_or_empty(stmt.get("target"))
                    if len(target) == 0:
                        targets = self._dict_stmt_list(stmt.get("targets"))
                        if len(targets) > 0:
                            target = targets[0]
                    if self.any_dict_get_str(target, "kind", "") != "Attribute":
                        continue
                    owner = self.any_to_dict_or_empty(target.get("value"))
                    if self.any_dict_get_str(owner, "kind", "") != "Name":
                        continue
                    if self.any_to_str(owner.get("id")) != "self":
                        continue
                    field_name = self.any_to_str(target.get("attr"))
                    if field_name == "":
                        continue
                    field_values[field_name] = self.render_expr(stmt.get("value"))

        if len(field_types) == 0:
            if len(init_scope) > 0:
                args_names: list[str] = []
                for arg_name in init_scope:
                    args_names.append(self._safe_name(arg_name))
                self.emit("let _ = (" + ", ".join(args_names) + ");")
            self.emit("Self")
        else:
            self.emit("Self {")
            self.indent += 1
            for field_name in field_types.keys():
                safe = self._safe_name(field_name)
                self.emit(f"{safe}: {field_values.get(field_name, 'Default::default()')},")
            self.indent -= 1
            self.emit("}")

        self.indent -= 1
        self.emit("}")

    def _emit_function(self, fn: dict[str, Any], in_class: str | None) -> None:
        """FunctionDef を Rust 関数として出力する。"""
        fn_name_raw = self.any_to_str(fn.get("name"))
        fn_name = self._safe_name(fn_name_raw)
        arg_order = self.any_to_str_list(fn.get("arg_order"))
        arg_types = self.any_to_dict_or_empty(fn.get("arg_types"))
        args_text_list: list[str] = []
        scope_names: set[str] = set()

        if in_class is not None:
            if len(arg_order) > 0 and arg_order[0] == "self":
                args_text_list.append("&self")
                scope_names.add("self")
                arg_order = arg_order[1:]

        for arg_name in arg_order:
            safe = self._safe_name(arg_name)
            arg_t = self._rust_type(self.any_to_str(arg_types.get(arg_name)))
            args_text_list.append(f"{safe}: {arg_t}")
            scope_names.add(arg_name)
            self.declared_var_types[arg_name] = self.normalize_type_name(self.any_to_str(arg_types.get(arg_name)))

        ret_t_east = self.normalize_type_name(self.any_to_str(fn.get("return_type")))
        ret_t = self._rust_type(ret_t_east)
        ret_txt = ""
        if ret_t != "()":
            ret_txt = " -> " + ret_t
        line = self.syntax_line(
            "function_open",
            "fn {name}({args}){ret_txt} {",
            {"name": fn_name, "args": ", ".join(args_text_list), "ret_txt": ret_txt},
        )
        self.emit(line)

        body = self._dict_stmt_list(fn.get("body"))
        self.emit_scoped_stmt_list(body, scope_names)
        self.emit("}")

    def emit_stmt(self, stmt: dict[str, Any]) -> None:
        """文ノードを Rust へ出力する。"""
        self.emit_leading_comments(stmt)
        hooked = self.hook_on_emit_stmt(stmt)
        if hooked is True:
            return
        kind = self.any_dict_get_str(stmt, "kind", "")
        hooked_kind = self.hook_on_emit_stmt_kind(kind, stmt)
        if hooked_kind is True:
            return

        if kind == "Pass":
            self.emit(self.syntax_text("pass_stmt", "// pass"))
            return
        if kind == "Break":
            self.emit(self.syntax_text("break_stmt", "break;"))
            return
        if kind == "Continue":
            self.emit(self.syntax_text("continue_stmt", "continue;"))
            return
        if kind == "Expr":
            expr_txt = self.render_expr(stmt.get("value"))
            self.emit(self.syntax_line("expr_stmt", "{expr};", {"expr": expr_txt}))
            return
        if kind == "Return":
            if stmt.get("value") is None:
                self.emit(self.syntax_text("return_void", "return;"))
            else:
                val = self.render_expr(stmt.get("value"))
                self.emit(self.syntax_line("return_value", "return {value};", {"value": val}))
            return
        if kind == "AnnAssign":
            self._emit_annassign(stmt)
            return
        if kind == "Assign":
            self._emit_assign(stmt)
            return
        if kind == "AugAssign":
            self._emit_augassign(stmt)
            return
        if kind == "If":
            self._emit_if(stmt)
            return
        if kind == "While":
            self._emit_while(stmt)
            return
        if kind == "ForRange":
            self._emit_for_range(stmt)
            return
        if kind == "For":
            self._emit_for(stmt)
            return
        if kind == "Import" or kind == "ImportFrom":
            return

        # 未対応文はコメント化して処理継続する。
        self.emit("// unsupported stmt: " + kind)

    def _emit_if(self, stmt: dict[str, Any]) -> None:
        cond = self.render_cond(stmt.get("test"))
        self.emit(self.syntax_line("if_open", "if {cond} {", {"cond": cond}))
        body = self._dict_stmt_list(stmt.get("body"))
        self.emit_scoped_stmt_list(body, set())
        orelse = self._dict_stmt_list(stmt.get("orelse"))
        if len(orelse) == 0:
            self.emit(self.syntax_text("block_close", "}"))
            return
        self.emit(self.syntax_text("else_open", "} else {"))
        self.emit_scoped_stmt_list(orelse, set())
        self.emit(self.syntax_text("block_close", "}"))

    def _emit_while(self, stmt: dict[str, Any]) -> None:
        cond = self.render_cond(stmt.get("test"))
        self.emit(self.syntax_line("while_open", "while {cond} {", {"cond": cond}))
        body = self._dict_stmt_list(stmt.get("body"))
        self.emit_scoped_stmt_list(body, set())
        self.emit(self.syntax_text("block_close", "}"))

    def _emit_for_range(self, stmt: dict[str, Any]) -> None:
        target_node = self.any_to_dict_or_empty(stmt.get("target"))
        target = self._safe_name(self.any_dict_get_str(target_node, "id", "_i"))
        target_type = self._rust_type(self.any_to_str(stmt.get("target_type")))
        start = self.render_expr(stmt.get("start"))
        stop = self.render_expr(stmt.get("stop"))
        step = self.render_expr(stmt.get("step"))
        range_mode = self.any_to_str(stmt.get("range_mode"))

        self.emit(f"let mut {target}: {target_type} = {start};")
        cond = f"{target} < {stop}"
        if range_mode == "descending":
            cond = f"{target} > {stop}"
        self.emit(self.syntax_line("for_range_open", "while {cond} {", {"cond": cond}))
        body_scope: set[str] = set()
        body_scope.add(self.any_dict_get_str(target_node, "id", target))
        body = self._dict_stmt_list(stmt.get("body"))
        self.indent += 1
        self.scope_stack.append(body_scope)
        self.emit_stmt_list(body)
        self.emit(f"{target} += {step};")
        self.scope_stack.pop()
        self.indent -= 1
        self.emit(self.syntax_text("block_close", "}"))

    def _emit_for(self, stmt: dict[str, Any]) -> None:
        target_node = self.any_to_dict_or_empty(stmt.get("target"))
        target_name = self.any_dict_get_str(target_node, "id", "_it")
        target = self._safe_name(target_name)
        body_scope: set[str] = set()
        target_kind = self.any_dict_get_str(target_node, "kind", "")
        if target_kind == "Name":
            body_scope.add(target_name)
        elif target_kind == "Tuple":
            elts = self._tuple_elements(target_node)
            parts: list[str] = []
            for elt in elts:
                d = self.any_to_dict_or_empty(elt)
                if self.any_dict_get_str(d, "kind", "") == "Name":
                    name = self.any_dict_get_str(d, "id", "_")
                    parts.append(self._safe_name(name))
                    body_scope.add(name)
                else:
                    parts.append("_")
            if len(parts) == 1:
                target = "(" + parts[0] + ",)"
            elif len(parts) > 1:
                target = "(" + ", ".join(parts) + ")"

        iter_node = stmt.get("iter")
        iter_expr = self.render_expr(iter_node)
        iter_type = self.get_expr_type(iter_node)
        if iter_type == "str":
            iter_expr = iter_expr + ".chars()"
        elif iter_type.startswith("list[") or iter_type.startswith("set[") or iter_type.startswith("dict["):
            iter_expr = "(" + iter_expr + ").clone()"

        self.emit(self.syntax_line("for_open", "for {target} in {iter} {", {"target": target, "iter": iter_expr}))
        body = self._dict_stmt_list(stmt.get("body"))
        self.emit_scoped_stmt_list(body, body_scope)
        self.emit(self.syntax_text("block_close", "}"))

    def _emit_annassign(self, stmt: dict[str, Any]) -> None:
        target = self.any_to_dict_or_empty(stmt.get("target"))
        target_kind = self.any_dict_get_str(target, "kind", "")
        if target_kind != "Name":
            t = self.render_expr(target)
            v = self.render_expr(stmt.get("value"))
            self.emit(self.syntax_line("annassign_assign", "{target} = {value};", {"target": t, "value": v}))
            return

        name_raw = self.any_dict_get_str(target, "id", "_")
        name = self._safe_name(name_raw)
        ann = self.any_to_str(stmt.get("annotation"))
        decl_t = self.any_to_str(stmt.get("decl_type"))
        t_east = ann if ann != "" else decl_t
        if t_east == "":
            t_east = self.get_expr_type(stmt.get("value"))
        t = self._rust_type(t_east)
        self.declare_in_current_scope(name_raw)
        self.declared_var_types[name_raw] = self.normalize_type_name(t_east)

        value_obj = stmt.get("value")
        if value_obj is None:
            self.emit(self.syntax_line("annassign_decl_noinit", "let mut {target}: {type};", {"target": name, "type": t}))
            return
        value = self.render_expr(value_obj)
        self.emit(
            self.syntax_line(
                "annassign_decl_init",
                "let mut {target}: {type} = {value};",
                {"target": name, "type": t, "value": value},
            )
        )

    def _emit_assign(self, stmt: dict[str, Any]) -> None:
        target = self.any_to_dict_or_empty(stmt.get("target"))
        if len(target) == 0:
            targets = self._dict_stmt_list(stmt.get("targets"))
            if len(targets) > 0:
                target = targets[0]
        value = self.render_expr(stmt.get("value"))
        if self.any_dict_get_str(target, "kind", "") == "Name":
            name_raw = self.any_dict_get_str(target, "id", "_")
            name = self._safe_name(name_raw)
            declare = self.any_dict_get_bool(stmt, "declare", False)
            if declare and not self.is_declared(name_raw):
                self.declare_in_current_scope(name_raw)
                t = self.get_expr_type(stmt.get("value"))
                if t != "":
                    self.declared_var_types[name_raw] = t
                self.emit(self.syntax_line("assign_decl_init", "let mut {target} = {value};", {"target": name, "value": value}))
                return
            self.emit(self.syntax_line("assign_set", "{target} = {value};", {"target": name, "value": value}))
            return

        if self.any_dict_get_str(target, "kind", "") == "Tuple":
            names: list[Any] = self._tuple_elements(target)
            if len(names) == 2:
                a = self.render_expr(names[0])
                b = self.render_expr(names[1])
                tmp = self.next_tmp("__tmp")
                self.emit(f"let {tmp} = {value};")
                self.emit(f"{a} = {tmp}.0;")
                self.emit(f"{b} = {tmp}.1;")
                return

        rendered_target = self.render_expr(target)
        self.emit(self.syntax_line("assign_set", "{target} = {value};", {"target": rendered_target, "value": value}))

    def _emit_augassign(self, stmt: dict[str, Any]) -> None:
        target = self.render_expr(stmt.get("target"))
        value = self.render_expr(stmt.get("value"))
        op = self.any_to_str(stmt.get("op"))
        mapped = self.aug_ops.get(op, "")
        if mapped == "":
            mapped = "+="
        self.emit(self.syntax_line("augassign_apply", "{target} {op} {value};", {"target": target, "op": mapped, "value": value}))

    def _render_compare(self, expr: dict[str, Any]) -> str:
        left = self.render_expr(expr.get("left"))
        ops = self.any_to_str_list(expr.get("ops"))
        comps = self.any_to_list(expr.get("comparators"))
        if len(ops) == 0 or len(comps) == 0:
            return "false"
        terms: list[str] = []
        cur_left = left
        i = 0
        while i < len(ops) and i < len(comps):
            op = ops[i]
            right = self.render_expr(comps[i])
            op_txt = self.cmp_ops.get(op, "==")
            terms.append(f"({cur_left} {op_txt} {right})")
            cur_left = right
            i += 1
        if len(terms) == 1:
            return terms[0]
        return "(" + " && ".join(terms) + ")"

    def _render_call(self, expr: dict[str, Any]) -> str:
        parts = self.unpack_prepared_call_parts(self._prepare_call_parts(expr))
        fn_node = self.any_to_dict_or_empty(parts.get("fn"))
        fn_kind = self.any_dict_get_str(fn_node, "kind", "")
        args = self.any_to_list(parts.get("args"))
        arg_nodes = self.any_to_list(parts.get("arg_nodes"))

        rendered_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_args.append(self.any_to_str(args[i]))
            i += 1

        if fn_kind == "Name":
            fn_name_raw = self.any_dict_get_str(fn_node, "id", "")
            fn_name = self._safe_name(fn_name_raw)
            if fn_name_raw in self.class_names:
                return f"{fn_name_raw}::new(" + ", ".join(rendered_args) + ")"
            if fn_name_raw == "print":
                if len(rendered_args) == 0:
                    return "println!(\"\")"
                if len(rendered_args) == 1:
                    return "println!(\"{}\", " + rendered_args[0] + ")"
                return "println!(\"{:?}\", (" + ", ".join(rendered_args) + "))"
            if fn_name_raw == "len" and len(rendered_args) == 1:
                arg_type = self.get_expr_type(arg_nodes[0] if len(arg_nodes) > 0 else None)
                if arg_type.startswith("dict["):
                    return rendered_args[0] + ".len() as i64"
                return rendered_args[0] + ".len() as i64"
            if fn_name_raw == "str" and len(rendered_args) == 1:
                return rendered_args[0] + ".to_string()"
            if fn_name_raw == "int" and len(rendered_args) == 1:
                return rendered_args[0] + " as i64"
            if fn_name_raw == "float" and len(rendered_args) == 1:
                return rendered_args[0] + " as f64"
            if fn_name_raw == "bool" and len(rendered_args) == 1:
                return "(" + rendered_args[0] + " != 0)"
            return fn_name + "(" + ", ".join(rendered_args) + ")"

        if fn_kind == "Attribute":
            owner_expr = self.render_expr(fn_node.get("value"))
            owner_node = self.any_to_dict_or_empty(fn_node.get("value"))
            owner_type = self.get_expr_type(owner_node)
            attr_raw = self.any_dict_get_str(fn_node, "attr", "")
            attr = self._safe_name(attr_raw)
            if attr_raw == "items" and len(rendered_args) == 0:
                return "(" + owner_expr + ").clone().into_iter()"
            if attr_raw == "keys" and len(rendered_args) == 0:
                return "(" + owner_expr + ").keys().cloned()"
            if attr_raw == "values" and len(rendered_args) == 0:
                return "(" + owner_expr + ").values().cloned()"
            if owner_type.startswith("list[") or owner_type in {"bytes", "bytearray"}:
                if attr_raw == "append" and len(rendered_args) == 1:
                    return owner_expr + ".push(" + rendered_args[0] + ")"
                if attr_raw == "pop" and len(rendered_args) == 0:
                    return owner_expr + ".pop().unwrap_or_default()"
                if attr_raw == "clear" and len(rendered_args) == 0:
                    return owner_expr + ".clear()"
            if owner_type.startswith("dict["):
                if attr_raw == "get" and len(rendered_args) == 1:
                    return owner_expr + ".get(&" + rendered_args[0] + ").cloned().unwrap_or_default()"
                if attr_raw == "get" and len(rendered_args) >= 2:
                    return owner_expr + ".get(&" + rendered_args[0] + ").cloned().unwrap_or(" + rendered_args[1] + ")"
            return owner_expr + "." + attr + "(" + ", ".join(rendered_args) + ")"

        fn_expr = self.render_expr(fn_node)
        return fn_expr + "(" + ", ".join(rendered_args) + ")"

    def render_expr(self, expr: Any) -> str:
        """式ノードを Rust へ描画する。"""
        expr_d = self.any_to_dict_or_empty(expr)
        if len(expr_d) == 0:
            return "()"
        kind = self.any_dict_get_str(expr_d, "kind", "")

        hook_leaf = self.hook_on_render_expr_leaf(kind, expr_d)
        if hook_leaf != "":
            return hook_leaf

        if kind == "Name":
            name = self.any_dict_get_str(expr_d, "id", "_")
            return self._safe_name(name)
        if kind == "Constant":
            tag, non_str = self.render_constant_non_string_common(expr, expr_d, "()", "()")
            if tag == "1":
                return non_str
            val = self.any_to_str(expr_d.get("value"))
            return rust_string_lit(val)
        if kind == "Attribute":
            owner = self.render_expr(expr_d.get("value"))
            attr = self._safe_name(self.any_dict_get_str(expr_d, "attr", ""))
            return owner + "." + attr
        if kind == "UnaryOp":
            op = self.any_dict_get_str(expr_d, "op", "")
            right = self.render_expr(expr_d.get("operand"))
            if op == "USub":
                return "(-" + right + ")"
            if op == "Not":
                return "(!" + right + ")"
            return right
        if kind == "BinOp":
            left_node = self.any_to_dict_or_empty(expr_d.get("left"))
            right_node = self.any_to_dict_or_empty(expr_d.get("right"))
            left = self._wrap_for_binop_operand(self.render_expr(left_node), left_node, self.any_dict_get_str(expr_d, "op", ""), is_right=False)
            right = self._wrap_for_binop_operand(self.render_expr(right_node), right_node, self.any_dict_get_str(expr_d, "op", ""), is_right=True)
            custom = self.hook_on_render_binop(expr_d, left, right)
            if custom != "":
                return custom
            op = self.any_to_str(expr_d.get("op"))
            mapped = self.bin_ops.get(op, "+")
            return "(" + left + " " + mapped + " " + right + ")"
        if kind == "Compare":
            return self._render_compare(expr_d)
        if kind == "BoolOp":
            op = self.any_to_str(expr_d.get("op"))
            mapped = "&&"
            if op == "Or":
                mapped = "||"
            vals = self.any_to_list(expr_d.get("values"))
            rendered: list[str] = []
            for val in vals:
                rendered.append(self.render_expr(val))
            if len(rendered) == 0:
                return "false"
            return "(" + (" " + mapped + " ").join(rendered) + ")"
        if kind == "Call":
            call_hook = self.hook_on_render_call(expr_d, self.any_to_dict_or_empty(expr_d.get("func")), [], {})
            if call_hook != "":
                return call_hook
            return self._render_call(expr_d)
        if kind == "IfExp":
            return self._render_ifexp_expr(expr_d)
        if kind == "List":
            elts = self.any_to_list(expr_d.get("elts"))
            rendered: list[str] = []
            for elt in elts:
                rendered.append(self.render_expr(elt))
            return "vec![" + ", ".join(rendered) + "]"
        if kind == "Tuple":
            elts: list[Any] = self._tuple_elements(expr_d)
            rendered = []
            for elt in elts:
                rendered.append(self.render_expr(elt))
            if len(rendered) == 1:
                return "(" + rendered[0] + ",)"
            return "(" + ", ".join(rendered) + ")"
        if kind == "Dict":
            keys = self.any_to_list(expr_d.get("keys"))
            vals = self.any_to_list(expr_d.get("values"))
            pairs: list[str] = []
            i = 0
            while i < len(keys) and i < len(vals):
                pairs.append("(" + self.render_expr(keys[i]) + ", " + self.render_expr(vals[i]) + ")")
                i += 1
            return "::std::collections::BTreeMap::from([" + ", ".join(pairs) + "])"
        if kind == "Subscript":
            owner = self.render_expr(expr_d.get("value"))
            idx = self.render_expr(expr_d.get("slice"))
            return owner + "[" + idx + " as usize]"
        if kind == "Lambda":
            args = self.any_to_list(self.any_to_dict_or_empty(expr_d.get("args")).get("args"))
            names: list[str] = []
            for arg in args:
                names.append(self._safe_name(self.any_to_str(self.any_to_dict_or_empty(arg).get("arg"))))
            body = self.render_expr(expr_d.get("body"))
            return "|" + ", ".join(names) + "| " + body

        hook_complex = self.hook_on_render_expr_complex(expr_d)
        if hook_complex != "":
            return hook_complex
        return self.any_to_str(expr_d.get("repr"))

    def render_cond(self, expr: Any) -> str:
        """条件式向け描画（数値等を bool 条件へ寄せる）。"""
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
            return "!" + rendered + ".is_empty()"
        if t.startswith("list[") or t.startswith("dict[") or t.startswith("set[") or t.startswith("tuple["):
            return rendered + ".len() != 0"
        if t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64"}:
            return rendered + " != 0"
        return rendered
def transpile_to_rust(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを Rust コードへ変換する。"""
    emitter = RustEmitter(east_doc)
    return emitter.transpile()
