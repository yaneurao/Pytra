"""EAST -> Rust transpiler."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.rs.hooks.rs_hooks import build_rs_hooks
from pytra.compiler.east_parts.code_emitter import CodeEmitter


def load_rs_profile() -> dict[str, Any]:
    """Rust 用 profile を読み込む。"""
    return CodeEmitter.load_profile_with_includes(
        "src/profiles/rs/profile.json",
        anchor_file=__file__,
    )


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
        self.class_base_map: dict[str, str] = {}
        self.class_field_types: dict[str, dict[str, str]] = {}
        self.declared_var_types: dict[str, str] = {}
        self.uses_pyany: bool = False

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

    def _doc_mentions_any(self, node: Any) -> bool:
        """EAST 全体に `Any/object` 型が含まれるかを粗く判定する。"""
        if isinstance(node, dict):
            for _k, v in node.items():
                if self._doc_mentions_any(v):
                    return True
            return False
        if isinstance(node, list):
            for item in node:
                if self._doc_mentions_any(item):
                    return True
            return False
        if isinstance(node, str):
            t = self.normalize_type_name(node)
            if t == "Any" or t == "object":
                return True
            if self._contains_text(t, "Any") or self._contains_text(t, "object"):
                return True
        return False

    def _is_any_type(self, east_type: str) -> bool:
        t = self.normalize_type_name(east_type)
        return t == "Any" or t == "object"

    def _is_int_type(self, east_type: str) -> bool:
        t = self.normalize_type_name(east_type)
        return t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}

    def _is_float_type(self, east_type: str) -> bool:
        t = self.normalize_type_name(east_type)
        return t in {"float32", "float64"}

    def _dict_key_value_types(self, east_type: str) -> tuple[str, str]:
        t = self.normalize_type_name(east_type)
        if not t.startswith("dict[") or not t.endswith("]"):
            return "", ""
        parts = self.split_generic(t[5:-1].strip())
        if len(parts) != 2:
            return "", ""
        return self.normalize_type_name(parts[0]), self.normalize_type_name(parts[1])

    def _is_dict_with_any_value(self, east_type: str) -> bool:
        key_t, val_t = self._dict_key_value_types(east_type)
        _ = key_t
        return self._is_any_type(val_t)

    def _dict_get_owner_value_type(self, call_node: Any) -> str:
        """`dict.get(...)` 呼び出しなら owner の value 型を返す。"""
        call_d = self.any_to_dict_or_empty(call_node)
        if self.any_dict_get_str(call_d, "kind", "") != "Call":
            return ""
        fn = self.any_to_dict_or_empty(call_d.get("func"))
        if self.any_dict_get_str(fn, "kind", "") != "Attribute":
            return ""
        if self.any_dict_get_str(fn, "attr", "") != "get":
            return ""
        owner = self.any_to_dict_or_empty(fn.get("value"))
        owner_t = self.normalize_type_name(self.get_expr_type(owner))
        if owner_t.startswith("dict["):
            _key_t, val_t = self._dict_key_value_types(owner_t)
            return val_t
        return ""

    def _dict_items_owner_type(self, call_node: Any) -> str:
        """`dict.items()` 呼び出しなら owner の dict 型を返す。"""
        call_d = self.any_to_dict_or_empty(call_node)
        if self.any_dict_get_str(call_d, "kind", "") != "Call":
            return ""
        fn = self.any_to_dict_or_empty(call_d.get("func"))
        if self.any_dict_get_str(fn, "kind", "") != "Attribute":
            return ""
        if self.any_dict_get_str(fn, "attr", "") != "items":
            return ""
        owner = self.any_to_dict_or_empty(fn.get("value"))
        owner_t = self.normalize_type_name(self.get_expr_type(owner))
        if owner_t.startswith("dict["):
            return owner_t
        return ""

    def _emit_pyany_runtime(self) -> None:
        """Any/object 用の最小ランタイム（PyAny）を出力する。"""
        self.emit("#[derive(Clone, Debug, Default)]")
        self.emit("enum PyAny {")
        self.indent += 1
        self.emit("Int(i64),")
        self.emit("Float(f64),")
        self.emit("Bool(bool),")
        self.emit("Str(String),")
        self.emit("Dict(::std::collections::BTreeMap<String, PyAny>),")
        self.emit("List(Vec<PyAny>),")
        self.emit("Set(Vec<PyAny>),")
        self.emit("#[default]")
        self.emit("None,")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_any_as_dict(v: PyAny) -> ::std::collections::BTreeMap<String, PyAny> {")
        self.indent += 1
        self.emit("match v {")
        self.indent += 1
        self.emit("PyAny::Dict(d) => d,")
        self.emit("_ => ::std::collections::BTreeMap::new(),")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_any_to_i64(v: &PyAny) -> i64 {")
        self.indent += 1
        self.emit("match v {")
        self.indent += 1
        self.emit("PyAny::Int(n) => *n,")
        self.emit("PyAny::Float(f) => *f as i64,")
        self.emit("PyAny::Bool(b) => if *b { 1 } else { 0 },")
        self.emit("PyAny::Str(s) => s.parse::<i64>().unwrap_or(0),")
        self.emit("_ => 0,")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_any_to_f64(v: &PyAny) -> f64 {")
        self.indent += 1
        self.emit("match v {")
        self.indent += 1
        self.emit("PyAny::Int(n) => *n as f64,")
        self.emit("PyAny::Float(f) => *f,")
        self.emit("PyAny::Bool(b) => if *b { 1.0 } else { 0.0 },")
        self.emit("PyAny::Str(s) => s.parse::<f64>().unwrap_or(0.0),")
        self.emit("_ => 0.0,")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_any_to_bool(v: &PyAny) -> bool {")
        self.indent += 1
        self.emit("match v {")
        self.indent += 1
        self.emit("PyAny::Int(n) => *n != 0,")
        self.emit("PyAny::Float(f) => *f != 0.0,")
        self.emit("PyAny::Bool(b) => *b,")
        self.emit("PyAny::Str(s) => !s.is_empty(),")
        self.emit("PyAny::Dict(d) => !d.is_empty(),")
        self.emit("PyAny::List(xs) => !xs.is_empty(),")
        self.emit("PyAny::Set(xs) => !xs.is_empty(),")
        self.emit("PyAny::None => false,")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_any_to_string(v: &PyAny) -> String {")
        self.indent += 1
        self.emit("match v {")
        self.indent += 1
        self.emit("PyAny::Int(n) => n.to_string(),")
        self.emit("PyAny::Float(f) => f.to_string(),")
        self.emit("PyAny::Bool(b) => b.to_string(),")
        self.emit("PyAny::Str(s) => s.clone(),")
        self.emit("PyAny::Dict(d) => format!(\"{:?}\", d),")
        self.emit("PyAny::List(xs) => format!(\"{:?}\", xs),")
        self.emit("PyAny::Set(xs) => format!(\"{:?}\", xs),")
        self.emit("PyAny::None => String::new(),")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")

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
        if self._is_any_type(t):
            self.uses_pyany = True
            return "PyAny::None"
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

    def _refine_decl_type_from_value(self, declared_type: str, value_node: Any) -> str:
        """`Any` を含む宣言型より値側の具体型が有用なら値側を優先する。"""
        d = self.normalize_type_name(declared_type)
        if d == "":
            return self.get_expr_type(value_node)
        v = self.normalize_type_name(self.get_expr_type(value_node))
        if v == "":
            return d
        if self.is_any_like_type(d):
            return v
        if self._contains_text(d, "Any"):
            # `dict[str, Any]` などのコンテナ注釈は、Rust 側の型整合を優先して
            # 宣言型を保持する。値側推論で過度に具体化すると、混在値辞書が壊れる。
            if d.startswith("dict[") or d.startswith("list[") or d.startswith("tuple["):
                return d
            if d.startswith("dict[") and v.startswith("dict["):
                return v
            if d.startswith("list[") and v.startswith("list["):
                return v
            if d.startswith("tuple[") and v.startswith("tuple["):
                return v
        return d

    def _rust_type(self, east_type: str) -> str:
        """EAST 型名を Rust 型名へ変換する。"""
        t = self.normalize_type_name(east_type)
        if t == "":
            return "i64"
        if self._is_any_type(t):
            self.uses_pyany = True
            return "PyAny"
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
            any_like = False
            non_none: list[str] = []
            has_none = False
            for part in parts:
                if part == "None":
                    has_none = True
                elif self._is_any_type(part):
                    any_like = True
                else:
                    non_none.append(part)
            if any_like:
                self.uses_pyany = True
                return "PyAny"
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
        self.uses_pyany = self._doc_mentions_any(self.doc)

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
        if self.uses_pyany:
            self._emit_pyany_runtime()
            self.emit("")

        self.class_names = set()
        self.class_base_map = self._collect_class_base_map(body)
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

        self.emit("#[derive(Clone, Debug)]")
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
        arg_usage = self.any_to_dict_or_empty(fn.get("arg_usage"))
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
            usage = self.any_to_str(arg_usage.get(arg_name))
            is_mut = usage == "reassigned" or usage == "mutable" or usage == "write"
            prefix = "mut " if is_mut else ""
            args_text_list.append(f"{prefix}{safe}: {arg_t}")
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
        self.emit_if_stmt_skeleton(
            cond,
            self._dict_stmt_list(stmt.get("body")),
            self._dict_stmt_list(stmt.get("orelse")),
            if_open_default="if {cond} {",
            else_open_default="} else {",
        )

    def _emit_while(self, stmt: dict[str, Any]) -> None:
        cond = self.render_cond(stmt.get("test"))
        self.emit_while_stmt_skeleton(
            cond,
            self._dict_stmt_list(stmt.get("body")),
            while_open_default="while {cond} {",
        )

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
        body_scope: set[str] = set()
        body_scope.add(self.any_dict_get_str(target_node, "id", target))
        body = self._dict_stmt_list(stmt.get("body"))
        self.emit_scoped_block_with_tail_lines(
            self.syntax_line("for_range_open", "while {cond} {", {"cond": cond}),
            body,
            body_scope,
            [f"{target} += {step};"],
        )

    def _emit_for(self, stmt: dict[str, Any]) -> None:
        target_node = self.any_to_dict_or_empty(stmt.get("target"))
        target_name = self.any_dict_get_str(target_node, "id", "_it")
        target = self._safe_name(target_name)
        body_scope: set[str] = set()
        target_kind = self.any_dict_get_str(target_node, "kind", "")
        if target_kind == "Name":
            body_scope.add(target_name)
        elif target_kind == "Tuple":
            elts = self.tuple_elements(target_node)
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
        iter_d = self.any_to_dict_or_empty(iter_node)
        iter_expr = self.render_expr(iter_node)
        iter_type = self.get_expr_type(iter_node)
        iter_is_attr_view = False
        if self.any_dict_get_str(iter_d, "kind", "") == "Call":
            fn_d = self.any_to_dict_or_empty(iter_d.get("func"))
            if self.any_dict_get_str(fn_d, "kind", "") == "Attribute":
                attr_name = self.any_dict_get_str(fn_d, "attr", "")
                if attr_name == "items" or attr_name == "keys" or attr_name == "values":
                    iter_is_attr_view = True
        if iter_type == "" or iter_type == "unknown":
            iter_type = self._dict_items_owner_type(iter_node)
        iter_key_t = ""
        iter_val_t = ""
        if iter_type.startswith("dict["):
            iter_key_t, iter_val_t = self._dict_key_value_types(iter_type)
        if iter_type == "str":
            iter_expr = iter_expr + ".chars()"
        elif (
            iter_type.startswith("list[")
            or iter_type.startswith("set[")
            or iter_type.startswith("dict[")
        ) and not iter_is_attr_view:
            iter_expr = "(" + iter_expr + ").clone()"

        if target_kind == "Tuple":
            elts = self.tuple_elements(target_node)
            if len(elts) >= 2 and iter_key_t != "" and iter_val_t != "":
                k_node = self.any_to_dict_or_empty(elts[0])
                v_node = self.any_to_dict_or_empty(elts[1])
                if self.any_dict_get_str(k_node, "kind", "") == "Name":
                    self.declared_var_types[self.any_dict_get_str(k_node, "id", "")] = iter_key_t
                if self.any_dict_get_str(v_node, "kind", "") == "Name":
                    self.declared_var_types[self.any_dict_get_str(v_node, "id", "")] = iter_val_t

        body = self._dict_stmt_list(stmt.get("body"))
        self.emit_scoped_block(
            self.syntax_line("for_open", "for {target} in {iter} {", {"target": target, "iter": iter_expr}),
            body,
            body_scope,
        )

    def _render_as_pyany(self, expr: Any) -> str:
        """式を `PyAny` へ昇格する。"""
        expr_d = self.any_to_dict_or_empty(expr)
        kind = self.any_dict_get_str(expr_d, "kind", "")
        src_t = self.normalize_type_name(self.get_expr_type(expr))
        self.uses_pyany = True
        if src_t == "PyAny" or self._is_any_type(src_t):
            return self.render_expr(expr)
        if kind == "Dict":
            return "PyAny::Dict(" + self._render_dict_expr(expr_d, force_any_values=True) + ")"
        if kind == "List":
            items = self.any_to_list(expr_d.get("elts"))
            vals: list[str] = []
            for item in items:
                vals.append(self._render_as_pyany(item))
            return "PyAny::List(vec![" + ", ".join(vals) + "])"
        if kind == "Set":
            items = self.any_to_list(expr_d.get("elements"))
            if len(items) == 0:
                items = self.any_to_list(expr_d.get("elts"))
            vals: list[str] = []
            for item in items:
                vals.append(self._render_as_pyany(item))
            return "PyAny::Set(vec![" + ", ".join(vals) + "])"
        rendered = self.render_expr(expr)
        if self._is_int_type(src_t):
            return "PyAny::Int((" + rendered + ") as i64)"
        if self._is_float_type(src_t):
            return "PyAny::Float((" + rendered + ") as f64)"
        if src_t == "bool":
            return "PyAny::Bool(" + rendered + ")"
        if src_t == "str":
            return "PyAny::Str((" + rendered + ").to_string())"
        if src_t == "None":
            return "PyAny::None"
        return "PyAny::Str(format!(\"{:?}\", " + rendered + "))"

    def _render_dict_expr(self, expr_d: dict[str, Any], *, force_any_values: bool = False) -> str:
        """Dict リテラルを Rust `BTreeMap::from([...])` へ描画する。"""
        dict_t = self.normalize_type_name(self.get_expr_type(expr_d))
        key_t = ""
        val_t = ""
        if dict_t.startswith("dict[") and dict_t.endswith("]"):
            key_t, val_t = self._dict_key_value_types(dict_t)
        if force_any_values:
            val_t = "Any"

        pairs: list[str] = []
        entries = self.any_to_list(expr_d.get("entries"))
        if len(entries) > 0:
            i = 0
            while i < len(entries):
                ent = self.any_to_dict_or_empty(entries[i])
                key_node = ent.get("key")
                val_node = ent.get("value")
                key_txt = self.render_expr(key_node)
                if key_t == "str":
                    key_txt = "(" + key_txt + ").to_string()"
                val_txt = self.render_expr(val_node)
                if self._is_any_type(val_t):
                    val_txt = self._render_as_pyany(val_node)
                pairs.append("(" + key_txt + ", " + val_txt + ")")
                i += 1
        else:
            keys = self.any_to_list(expr_d.get("keys"))
            vals = self.any_to_list(expr_d.get("values"))
            i = 0
            while i < len(keys) and i < len(vals):
                key_node = keys[i]
                val_node = vals[i]
                key_txt = self.render_expr(key_node)
                if key_t == "str":
                    key_txt = "(" + key_txt + ").to_string()"
                val_txt = self.render_expr(val_node)
                if self._is_any_type(val_t):
                    val_txt = self._render_as_pyany(val_node)
                pairs.append("(" + key_txt + ", " + val_txt + ")")
                i += 1
        return "::std::collections::BTreeMap::from([" + ", ".join(pairs) + "])"

    def _render_value_for_decl_type(self, value_obj: Any, target_type: str) -> str:
        """宣言型に合わせて右辺式を補正する。"""
        t = self.normalize_type_name(target_type)
        value_d = self.any_to_dict_or_empty(value_obj)
        value_kind = self.any_dict_get_str(value_d, "kind", "")
        if self._is_any_type(t):
            return self._render_as_pyany(value_obj)
        if self._is_dict_with_any_value(t):
            if value_kind == "Dict":
                return self._render_dict_expr(value_d, force_any_values=True)
            rendered = self.render_expr(value_obj)
            src_t = self.normalize_type_name(self.get_expr_type(value_obj))
            if self._is_any_type(src_t):
                self.uses_pyany = True
                return "py_any_as_dict(" + rendered + ")"
            if value_kind == "Call":
                owner_val_t = self._dict_get_owner_value_type(value_obj)
                if self._is_any_type(owner_val_t):
                    self.uses_pyany = True
                    return "py_any_as_dict(" + rendered + ")"
            return rendered
        return self.render_expr(value_obj)

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
        else:
            t_east = self._refine_decl_type_from_value(t_east, stmt.get("value"))
        t = self._rust_type(t_east)
        self.declare_in_current_scope(name_raw)
        self.declared_var_types[name_raw] = self.normalize_type_name(t_east)

        value_obj = stmt.get("value")
        if value_obj is None:
            self.emit(self.syntax_line("annassign_decl_noinit", "let mut {target}: {type};", {"target": name, "type": t}))
            return
        value = self._render_value_for_decl_type(value_obj, t_east)
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
            names: list[Any] = self.tuple_elements(target)
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
        target_obj = stmt.get("target")
        value_obj = stmt.get("value")
        target = self.render_expr(target_obj)
        value = self.render_expr(value_obj)
        op = self.any_to_str(stmt.get("op"))
        mapped = self.aug_ops.get(op, "")
        if mapped == "":
            mapped = "+="
        target_t = self.normalize_type_name(self.get_expr_type(target_obj))
        value_t = self.normalize_type_name(self.get_expr_type(value_obj))
        if self._is_any_type(value_t):
            self.uses_pyany = True
            if self._is_int_type(target_t):
                value = "py_any_to_i64(&" + value + ")"
            elif self._is_float_type(target_t):
                value = "py_any_to_f64(&" + value + ")"
            elif target_t == "bool":
                value = "py_any_to_bool(&" + value + ")"
            elif target_t == "str" and mapped == "+=":
                value = "py_any_to_string(&" + value + ")"
        self.emit(self.syntax_line("augassign_apply", "{target} {op} {value};", {"target": target, "op": mapped, "value": value}))

    def _collect_class_base_map(self, body: list[dict[str, Any]]) -> dict[str, str]:
        """ClassDef から `child -> base` の継承表を抽出する。"""
        out: dict[str, str] = {}
        for stmt in body:
            if self.any_dict_get_str(stmt, "kind", "") != "ClassDef":
                continue
            child = self.any_to_str(stmt.get("name"))
            if child == "":
                continue
            base = self.any_to_str(stmt.get("base"))
            if base != "":
                out[child] = self.normalize_type_name(base)
        return out

    def _is_class_subtype(self, actual: str, expected: str) -> bool:
        """`actual` が `expected` の派生型かを継承表で判定する。"""
        cur = self.normalize_type_name(actual)
        want = self.normalize_type_name(expected)
        if cur == "" or want == "":
            return False
        if cur == want:
            return True
        visited: set[str] = set()
        while cur != "" and cur not in visited:
            visited.add(cur)
            if cur == want:
                return True
            if cur not in self.class_base_map:
                break
            cur = self.normalize_type_name(self.class_base_map[cur])
        return False

    def _render_isinstance_type_check(self, value_expr: str, value_node: Any, type_name: str) -> str:
        """`isinstance(x, T)` の `T` を Rust 式へ lower する。"""
        expected = self.normalize_type_name(type_name)
        if expected == "object":
            return "true"
        actual = self.normalize_type_name(self.get_expr_type(value_node))
        if actual == "":
            return "false"

        expected_is_bool = expected == "bool"
        expected_is_int = self._is_int_type(expected)
        expected_is_float = self._is_float_type(expected)
        expected_is_str = expected == "str"
        expected_is_list = expected.startswith("list[") or expected == "list"
        expected_is_dict = expected.startswith("dict[") or expected == "dict"
        expected_is_set = expected.startswith("set[") or expected == "set"

        if self._is_any_type(actual):
            self.uses_pyany = True
            if expected_is_bool:
                return "matches!(" + value_expr + ", PyAny::Bool(_))"
            if expected_is_int:
                return "matches!(" + value_expr + ", PyAny::Int(_))"
            if expected_is_float:
                return "matches!(" + value_expr + ", PyAny::Float(_))"
            if expected_is_str:
                return "matches!(" + value_expr + ", PyAny::Str(_))"
            if expected_is_list:
                return "matches!(" + value_expr + ", PyAny::List(_))"
            if expected_is_dict:
                return "matches!(" + value_expr + ", PyAny::Dict(_))"
            if expected_is_set:
                return "matches!(" + value_expr + ", PyAny::Set(_))"
            return "false"

        actual_parts = self.split_union(actual)
        if len(actual_parts) == 0:
            actual_parts = [actual]
        for part_raw in actual_parts:
            part = self.normalize_type_name(part_raw)
            if part == "" or part == "None":
                continue
            if expected_is_bool and part == "bool":
                return "true"
            if expected_is_int and self._is_int_type(part):
                return "true"
            if expected_is_float and self._is_float_type(part):
                return "true"
            if expected_is_str and part == "str":
                return "true"
            if expected_is_list and (part.startswith("list[") or part == "bytes" or part == "bytearray"):
                return "true"
            if expected_is_dict and part.startswith("dict["):
                return "true"
            if expected_is_set and part.startswith("set["):
                return "true"
            if expected in self.class_names and part in self.class_names and self._is_class_subtype(part, expected):
                return "true"
        return "false"

    def _render_isinstance_call(self, rendered_args: list[str], arg_nodes: list[Any]) -> str:
        """`isinstance(...)` 呼び出しを Rust へ lower する。"""
        if len(rendered_args) != 2:
            return "false"
        rhs_node = self.any_to_dict_or_empty(arg_nodes[1] if len(arg_nodes) > 1 else None)
        rhs_kind = self.any_dict_get_str(rhs_node, "kind", "")
        if rhs_kind == "Name":
            rhs_name = self.any_dict_get_str(rhs_node, "id", "")
            lowered = self._render_isinstance_type_check(rendered_args[0], arg_nodes[0] if len(arg_nodes) > 0 else None, rhs_name)
            if lowered != "":
                return lowered
            return "false"
        if rhs_kind == "Tuple":
            checks: list[str] = []
            for elt in self.tuple_elements(rhs_node):
                e_node = self.any_to_dict_or_empty(elt)
                if self.any_dict_get_str(e_node, "kind", "") != "Name":
                    continue
                e_name = self.any_dict_get_str(e_node, "id", "")
                lowered = self._render_isinstance_type_check(rendered_args[0], arg_nodes[0] if len(arg_nodes) > 0 else None, e_name)
                if lowered != "":
                    checks.append(lowered)
            if len(checks) > 0:
                return "(" + " || ".join(checks) + ")"
        return "false"

    def _render_compare(self, expr: dict[str, Any]) -> str:
        left = self.render_expr(expr.get("left"))
        ops = self.any_to_str_list(expr.get("ops"))
        comps = self.any_to_list(expr.get("comparators"))
        return self.render_compare_chain_common(left, ops, comps, self.cmp_ops, empty_literal="false")

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
            if fn_name_raw == "isinstance":
                return self._render_isinstance_call(rendered_args, arg_nodes)
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
                arg_t = self.normalize_type_name(self.get_expr_type(arg_nodes[0] if len(arg_nodes) > 0 else None))
                arg_any = self._is_any_type(arg_t)
                if not arg_any and len(arg_nodes) > 0 and (arg_t == "" or arg_t == "unknown"):
                    arg_any = self._is_any_type(self._dict_get_owner_value_type(arg_nodes[0]))
                if arg_any:
                    self.uses_pyany = True
                    return "py_any_to_string(&" + rendered_args[0] + ")"
                return rendered_args[0] + ".to_string()"
            if fn_name_raw == "int" and len(rendered_args) == 1:
                arg_t = self.normalize_type_name(self.get_expr_type(arg_nodes[0] if len(arg_nodes) > 0 else None))
                arg_any = self._is_any_type(arg_t)
                if not arg_any and len(arg_nodes) > 0 and (arg_t == "" or arg_t == "unknown"):
                    arg_any = self._is_any_type(self._dict_get_owner_value_type(arg_nodes[0]))
                if arg_any:
                    self.uses_pyany = True
                    return "py_any_to_i64(&" + rendered_args[0] + ")"
                return rendered_args[0] + " as i64"
            if fn_name_raw == "float" and len(rendered_args) == 1:
                arg_t = self.normalize_type_name(self.get_expr_type(arg_nodes[0] if len(arg_nodes) > 0 else None))
                arg_any = self._is_any_type(arg_t)
                if not arg_any and len(arg_nodes) > 0 and (arg_t == "" or arg_t == "unknown"):
                    arg_any = self._is_any_type(self._dict_get_owner_value_type(arg_nodes[0]))
                if arg_any:
                    self.uses_pyany = True
                    return "py_any_to_f64(&" + rendered_args[0] + ")"
                return rendered_args[0] + " as f64"
            if fn_name_raw == "bool" and len(rendered_args) == 1:
                arg_t = self.normalize_type_name(self.get_expr_type(arg_nodes[0] if len(arg_nodes) > 0 else None))
                arg_any = self._is_any_type(arg_t)
                if not arg_any and len(arg_nodes) > 0 and (arg_t == "" or arg_t == "unknown"):
                    arg_any = self._is_any_type(self._dict_get_owner_value_type(arg_nodes[0]))
                if arg_any:
                    self.uses_pyany = True
                    return "py_any_to_bool(&" + rendered_args[0] + ")"
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
                _k_t, owner_val_t = self._dict_key_value_types(owner_type)
                if attr_raw == "get" and len(rendered_args) == 1:
                    return owner_expr + ".get(&" + rendered_args[0] + ").cloned().unwrap_or_default()"
                if attr_raw == "get" and len(rendered_args) >= 2:
                    default_txt = rendered_args[1]
                    if self._is_any_type(owner_val_t) and len(arg_nodes) >= 2:
                        self.uses_pyany = True
                        default_txt = self._render_as_pyany(arg_nodes[1])
                    return owner_expr + ".get(&" + rendered_args[0] + ").cloned().unwrap_or(" + default_txt + ")"
            return owner_expr + "." + attr + "(" + ", ".join(rendered_args) + ")"

        fn_expr = self.render_expr(fn_node)
        return fn_expr + "(" + ", ".join(rendered_args) + ")"

    def render_expr(self, expr: Any) -> str:
        """式ノードを Rust へ描画する。"""
        expr_d = self.any_to_dict_or_empty(expr)
        if len(expr_d) == 0:
            return "()"
        kind = self.any_dict_get_str(expr_d, "kind", "")

        hook_specific = self.hook_on_render_expr_kind_specific(kind, expr_d)
        if hook_specific != "":
            return hook_specific
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
            return self.quote_string_literal(val)
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
            vals = self.any_to_list(expr_d.get("values"))
            op = self.any_to_str(expr_d.get("op"))
            return self.render_boolop_common(vals, op, and_token="&&", or_token="||", empty_literal="false")
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
            elts: list[Any] = self.tuple_elements(expr_d)
            rendered = []
            for elt in elts:
                rendered.append(self.render_expr(elt))
            if len(rendered) == 1:
                return "(" + rendered[0] + ",)"
            return "(" + ", ".join(rendered) + ")"
        if kind == "Dict":
            return self._render_dict_expr(expr_d, force_any_values=False)
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
