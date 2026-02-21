"""EAST -> C# transpiler."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.cs.hooks.cs_hooks import build_cs_hooks
from pytra.compiler.east_parts.code_emitter import CodeEmitter
from pytra.std import json
from pytra.std.pathlib import Path


def cs_string_lit(text: str) -> str:
    """C# の文字列リテラルへエスケープ変換する。"""
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


def load_cs_profile() -> dict[str, Any]:
    """C# 用 profile を読み込む。"""
    profile_path = Path("src/profiles/cs/profile.json")
    if not profile_path.exists():
        this_file = str(__file__)
        src_pos = this_file.rfind("/src/")
        if src_pos >= 0:
            src_root = this_file[: src_pos + 4]
            profile_path = Path(src_root + "/profiles/cs/profile.json")
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


def load_cs_hooks(profile: dict[str, Any]) -> dict[str, Any]:
    """C# 用 hook を読み込む。"""
    _ = profile
    hooks = build_cs_hooks()
    if isinstance(hooks, dict):
        return hooks
    return {}


class CSharpEmitter(CodeEmitter):
    """EAST を C# ソースへ変換するエミッタ。"""

    def __init__(self, east_doc: dict[str, Any]) -> None:
        profile = load_cs_profile()
        hooks = load_cs_hooks(profile)
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
        self.declared_var_types: dict[str, str] = {}
        self.class_names: set[str] = set()
        self.current_class_name: str = ""
        self.in_method_scope: bool = False
        self.needs_enumerate_helper: bool = False

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

    def _module_id_to_cs_namespace(self, module_id: str) -> str:
        """Python 形式モジュール名を C# namespace 文字列へ変換する。"""
        if module_id == "":
            return ""
        return module_id

    def _collect_using_lines(self, body: list[dict[str, Any]], meta: dict[str, Any]) -> list[str]:
        """import 情報を C# using 行へ変換する。"""
        out: list[str] = [
            "using System;",
            "using System.Collections.Generic;",
            "using System.Linq;",
        ]
        seen: set[str] = set(out)

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
                if module_id == "browser" or module_id.startswith("browser."):
                    i += 1
                    continue
                ns = self._module_id_to_cs_namespace(module_id)
                if ns == "":
                    i += 1
                    continue
                if binding_kind == "module":
                    if local_name != "":
                        leaf = self._last_dotted_name(module_id)
                        if local_name != leaf:
                            _add("using " + self._safe_name(local_name) + " = " + ns + ";")
                        else:
                            _add("using " + ns + ";")
                    else:
                        _add("using " + ns + ";")
                elif binding_kind == "symbol" and export_name != "":
                    if local_name != "" and local_name != export_name:
                        _add("using " + self._safe_name(local_name) + " = " + ns + "." + export_name + ";")
                i += 1
            return out

        for stmt in body:
            kind = self.any_dict_get_str(stmt, "kind", "")
            if kind == "Import":
                for ent in self._dict_stmt_list(stmt.get("names")):
                    module_id = self.any_to_str(ent.get("name"))
                    if module_id == "" or module_id.startswith("__future__") or module_id in {"typing", "pytra.std.typing"}:
                        continue
                    if module_id == "browser" or module_id.startswith("browser."):
                        continue
                    ns = self._module_id_to_cs_namespace(module_id)
                    if ns == "":
                        continue
                    asname = self.any_to_str(ent.get("asname"))
                    if asname != "":
                        _add("using " + self._safe_name(asname) + " = " + ns + ";")
                    else:
                        _add("using " + ns + ";")
            elif kind == "ImportFrom":
                module_id = self.any_to_str(stmt.get("module"))
                if module_id == "" or module_id.startswith("__future__") or module_id in {"typing", "pytra.std.typing"}:
                    continue
                if module_id == "browser" or module_id.startswith("browser."):
                    continue
                ns = self._module_id_to_cs_namespace(module_id)
                if ns == "":
                    continue
                _add("using " + ns + ";")
                for ent in self._dict_stmt_list(stmt.get("names")):
                    sym = self.any_to_str(ent.get("name"))
                    asname = self.any_to_str(ent.get("asname"))
                    if sym == "" or sym == "*":
                        continue
                    if asname != "" and asname != sym:
                        _add("using " + self._safe_name(asname) + " = " + ns + "." + sym + ";")
        return out

    def _cs_type(self, east_type: str) -> str:
        """EAST 型名を C# 型名へ変換する。"""
        t = self.normalize_type_name(east_type)
        if t == "":
            return "object"
        if t in self.type_map:
            mapped = self.type_map[t]
            if mapped != "":
                return mapped
        if t.startswith("list[") and t.endswith("]"):
            inner = t[5:-1].strip()
            return "List<" + self._cs_type(inner) + ">"
        if t.startswith("set[") and t.endswith("]"):
            inner = t[4:-1].strip()
            return "HashSet<" + self._cs_type(inner) + ">"
        if t.startswith("dict[") and t.endswith("]"):
            parts = self.split_generic(t[5:-1].strip())
            if len(parts) == 2:
                return "Dictionary<" + self._cs_type(parts[0]) + ", " + self._cs_type(parts[1]) + ">"
        if t.startswith("tuple[") and t.endswith("]"):
            parts = self.split_generic(t[6:-1].strip())
            rendered: list[str] = []
            for part in parts:
                rendered.append(self._cs_type(part))
            return "(" + ", ".join(rendered) + ")"
        if self._contains_text(t, "|"):
            parts = self.split_union(t)
            non_none: list[str] = []
            has_none = False
            for part in parts:
                if part == "None":
                    has_none = True
                else:
                    non_none.append(part)
            if has_none and len(non_none) == 1:
                base = self._cs_type(non_none[0])
                if base in {"byte", "sbyte", "short", "ushort", "int", "uint", "long", "ulong", "float", "double", "bool"}:
                    return base + "?"
                return base
            return "object"
        if t == "None":
            return "void"
        return t

    def _typed_list_literal(self, expr_d: dict[str, Any]) -> str:
        """List リテラルを C# 式へ描画する。"""
        list_t = self.get_expr_type(expr_d)
        elem_t = "object"
        if list_t.startswith("list[") and list_t.endswith("]"):
            elem_t = self._cs_type(list_t[5:-1].strip())
        elts = self.any_to_list(expr_d.get("elts"))
        if len(elts) == 0:
            return "new List<" + elem_t + ">()"
        rendered: list[str] = []
        for elt in elts:
            rendered.append(self.render_expr(elt))
        return "new List<" + elem_t + "> { " + ", ".join(rendered) + " }"

    def _typed_dict_literal(self, expr_d: dict[str, Any]) -> str:
        """Dict リテラルを C# 式へ描画する。"""
        dict_t = self.get_expr_type(expr_d)
        key_t = "object"
        val_t = "object"
        if dict_t.startswith("dict[") and dict_t.endswith("]"):
            parts = self.split_generic(dict_t[5:-1].strip())
            if len(parts) == 2:
                key_t = self._cs_type(parts[0])
                val_t = self._cs_type(parts[1])

        pairs: list[str] = []
        entries = self.any_to_list(expr_d.get("entries"))
        if len(entries) > 0:
            i = 0
            while i < len(entries):
                ent = self.any_to_dict_or_empty(entries[i])
                k = self.render_expr(ent.get("key"))
                v = self.render_expr(ent.get("value"))
                pairs.append("{ " + k + ", " + v + " }")
                i += 1
        else:
            keys = self.any_to_list(expr_d.get("keys"))
            vals = self.any_to_list(expr_d.get("values"))
            i = 0
            while i < len(keys) and i < len(vals):
                pairs.append("{ " + self.render_expr(keys[i]) + ", " + self.render_expr(vals[i]) + " }")
                i += 1

        if len(pairs) == 0:
            return "new Dictionary<" + key_t + ", " + val_t + ">()"
        return "new Dictionary<" + key_t + ", " + val_t + "> { " + ", ".join(pairs) + " }"

    def transpile(self) -> str:
        """モジュール全体を C# ソースへ変換する。"""
        self.lines = []
        self.scope_stack = [set()]
        self.declared_var_types = {}
        self.needs_enumerate_helper = False
        self.in_method_scope = False

        module = self.doc
        body = self._dict_stmt_list(module.get("body"))
        meta = self.any_to_dict_or_empty(module.get("meta"))
        self.load_import_bindings_from_meta(meta)
        self.emit_module_leading_trivia()

        using_lines = self._collect_using_lines(body, meta)
        for line in using_lines:
            self.emit(line)
        self.emit("")

        self.class_names = set()
        for stmt in body:
            if self.any_dict_get_str(stmt, "kind", "") == "ClassDef":
                name = self.any_to_str(stmt.get("name"))
                if name != "":
                    self.class_names.add(name)

        top_level_stmts: list[dict[str, Any]] = []
        function_stmts: list[dict[str, Any]] = []
        class_stmts: list[dict[str, Any]] = []

        for stmt in body:
            kind = self.any_dict_get_str(stmt, "kind", "")
            if kind == "Import" or kind == "ImportFrom":
                continue
            if kind == "FunctionDef":
                function_stmts.append(stmt)
                continue
            if kind == "ClassDef":
                class_stmts.append(stmt)
                continue
            top_level_stmts.append(stmt)

        for cls in class_stmts:
            self.emit_leading_comments(cls)
            self._emit_class(cls)
            self.emit("")

        self.emit("public static class Program")
        self.emit("{")
        self.indent += 1

        for fn in function_stmts:
            self.emit_leading_comments(fn)
            self._emit_function(fn, in_class=None)
            self.emit("")

        if self.needs_enumerate_helper:
            self._emit_enumerate_helper()
            self.emit("")

        main_body = list(top_level_stmts) + self._dict_stmt_list(module.get("main_guard_body"))
        self.emit("public static void Main(string[] args)")
        self.emit("{")
        self.indent += 1
        self.emit_scoped_stmt_list(main_body, {"args"})
        self.indent -= 1
        self.emit("}")

        self.indent -= 1
        self.emit("}")

        return "\n".join(self.lines) + ("\n" if len(self.lines) > 0 else "")

    def _emit_enumerate_helper(self) -> None:
        """enumerate() 用の最小 helper を出力する。"""
        self.emit("private static IEnumerable<(long, T)> PytraEnumerate<T>(IEnumerable<T> source, long start = 0)")
        self.emit("{")
        self.indent += 1
        self.emit("long i = start;")
        self.emit("foreach (T item in source)")
        self.emit("{")
        self.indent += 1
        self.emit("yield return (i, item);")
        self.emit("i += 1;")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")

    def _emit_class(self, stmt: dict[str, Any]) -> None:
        """ClassDef を C# class として出力する。"""
        class_name_raw = self.any_to_str(stmt.get("name"))
        class_name = self._safe_name(class_name_raw)
        prev_class = self.current_class_name
        prev_method_scope = self.in_method_scope
        self.current_class_name = class_name_raw

        self.emit("public class " + class_name)
        self.emit("{")
        self.indent += 1

        field_types = self.any_to_dict_or_empty(stmt.get("field_types"))
        for field_name, field_t_obj in field_types.items():
            if not isinstance(field_name, str):
                continue
            field_t = self._cs_type(self.any_to_str(field_t_obj))
            self.emit("public " + field_t + " " + self._safe_name(field_name) + ";")

        members = self._dict_stmt_list(stmt.get("body"))
        for member in members:
            kind = self.any_dict_get_str(member, "kind", "")
            if kind == "AnnAssign":
                line = self._render_class_static_annassign(member)
                if line != "":
                    self.emit(line)
            elif kind == "Assign":
                line = self._render_class_static_assign(member)
                if line != "":
                    self.emit(line)

        init_fn: dict[str, Any] | None = None
        for member in members:
            if self.any_dict_get_str(member, "kind", "") == "FunctionDef" and self.any_to_str(member.get("name")) == "__init__":
                init_fn = member
                break

        if init_fn is not None:
            self.emit("")
            self._emit_function(init_fn, in_class=class_name_raw)
        elif len(field_types) == 0:
            self.emit("")
            self.emit("public " + class_name + "()")
            self.emit("{")
            self.emit("}")

        for member in members:
            if self.any_dict_get_str(member, "kind", "") != "FunctionDef":
                continue
            if self.any_to_str(member.get("name")) == "__init__":
                continue
            self.emit("")
            self._emit_function(member, in_class=class_name_raw)

        self.indent -= 1
        self.emit("}")

        self.current_class_name = prev_class
        self.in_method_scope = prev_method_scope

    def _render_class_static_annassign(self, stmt: dict[str, Any]) -> str:
        """class body の AnnAssign を static field 宣言へ変換する。"""
        target = self.any_to_dict_or_empty(stmt.get("target"))
        if self.any_dict_get_str(target, "kind", "") != "Name":
            return ""
        name_raw = self.any_dict_get_str(target, "id", "")
        if name_raw == "":
            return ""
        ann = self.any_to_str(stmt.get("annotation"))
        decl = self.any_to_str(stmt.get("decl_type"))
        t = ann
        if t == "":
            t = decl
        if t == "":
            t = self.get_expr_type(stmt.get("value"))
        cs_t = self._cs_type(t)
        name = self._safe_name(name_raw)
        val_obj = stmt.get("value")
        if val_obj is None:
            return "public static " + cs_t + " " + name + ";"
        return "public static " + cs_t + " " + name + " = " + self.render_expr(val_obj) + ";"

    def _render_class_static_assign(self, stmt: dict[str, Any]) -> str:
        """class body の Assign を static field 宣言へ変換する。"""
        target = self.any_to_dict_or_empty(stmt.get("target"))
        if len(target) == 0:
            targets = self._dict_stmt_list(stmt.get("targets"))
            if len(targets) > 0:
                target = targets[0]
        if self.any_dict_get_str(target, "kind", "") != "Name":
            return ""
        name_raw = self.any_dict_get_str(target, "id", "")
        if name_raw == "":
            return ""
        value_obj = stmt.get("value")
        val_type = self.get_expr_type(value_obj)
        cs_t = self._cs_type(val_type)
        if cs_t == "":
            cs_t = "object"
        return "public static " + cs_t + " " + self._safe_name(name_raw) + " = " + self.render_expr(value_obj) + ";"

    def _emit_function(self, fn: dict[str, Any], in_class: str | None) -> None:
        """FunctionDef を C# メソッドとして出力する。"""
        prev_declared = dict(self.declared_var_types)
        prev_method_scope = self.in_method_scope
        self.in_method_scope = in_class is not None

        fn_name_raw = self.any_to_str(fn.get("name"))
        fn_name = self._safe_name(fn_name_raw)
        arg_order = self.any_to_str_list(fn.get("arg_order"))
        arg_types = self.any_to_dict_or_empty(fn.get("arg_types"))
        args: list[str] = []
        scope_names: set[str] = set()

        is_constructor = in_class is not None and fn_name_raw == "__init__"
        emit_static = in_class is None

        if in_class is not None:
            if len(arg_order) > 0 and arg_order[0] == "self":
                arg_order = arg_order[1:]

        for arg_name in arg_order:
            safe = self._safe_name(arg_name)
            arg_east_t = self.any_to_str(arg_types.get(arg_name))
            arg_cs_t = self._cs_type(arg_east_t)
            if arg_cs_t == "":
                arg_cs_t = "object"
            args.append(arg_cs_t + " " + safe)
            scope_names.add(arg_name)
            self.declared_var_types[arg_name] = self.normalize_type_name(arg_east_t)

        if is_constructor:
            class_name = self._safe_name(in_class if in_class is not None else "")
            self.emit("public " + class_name + "(" + ", ".join(args) + ")")
        else:
            ret_east = self.normalize_type_name(self.any_to_str(fn.get("return_type")))
            ret_cs = self._cs_type(ret_east)
            if ret_cs == "":
                ret_cs = "void"
            static_kw = "static " if emit_static else ""
            self.emit("public " + static_kw + ret_cs + " " + fn_name + "(" + ", ".join(args) + ")")

        self.emit("{")
        body = self._dict_stmt_list(fn.get("body"))
        self.emit_scoped_stmt_list(body, scope_names)
        self.emit("}")

        self.declared_var_types = prev_declared
        self.in_method_scope = prev_method_scope

    def emit_stmt(self, stmt: dict[str, Any]) -> None:
        """文ノードを C# へ出力する。"""
        self.emit_leading_comments(stmt)
        if self.hook_on_emit_stmt(stmt) is True:
            return
        kind = self.any_dict_get_str(stmt, "kind", "")
        if self.hook_on_emit_stmt_kind(kind, stmt) is True:
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
                value = self.render_expr(stmt.get("value"))
                self.emit(self.syntax_line("return_value", "return {value};", {"value": value}))
            return
        if kind == "Raise":
            exc = stmt.get("exc")
            if exc is None:
                self.emit("throw new Exception(\"raise\");")
            else:
                self.emit("throw " + self.render_expr(exc) + ";")
            return
        if kind == "Try":
            self._emit_try(stmt)
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

        self.emit("// unsupported stmt: " + kind)

    def _emit_try(self, stmt: dict[str, Any]) -> None:
        """Try/Except/Finally を C# の try/catch/finally へ変換する。"""
        self.emit("try")
        self.emit("{")
        self.emit_scoped_stmt_list(self._dict_stmt_list(stmt.get("body")), set())
        handlers = self._dict_stmt_list(stmt.get("handlers"))
        finalbody = self._dict_stmt_list(stmt.get("finalbody"))
        if len(handlers) > 0:
            first = handlers[0]
            ex_name = self.any_to_str(first.get("name"))
            if ex_name == "":
                ex_name = "ex"
            self.emit("} catch (Exception " + self._safe_name(ex_name) + ") {")
            self.emit_scoped_stmt_list(self._dict_stmt_list(first.get("body")), {ex_name})
            if len(handlers) > 1:
                self.emit("    // unsupported: additional except handlers are ignored")
        if len(finalbody) > 0:
            self.emit("} finally {")
            self.emit_scoped_stmt_list(finalbody, set())
        self.emit("}")

    def _emit_if(self, stmt: dict[str, Any]) -> None:
        cond = self.render_cond(stmt.get("test"))
        self.emit(self.syntax_line("if_open", "if ({cond}) {", {"cond": cond}))
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
        self.emit(self.syntax_line("while_open", "while ({cond}) {", {"cond": cond}))
        body = self._dict_stmt_list(stmt.get("body"))
        self.emit_scoped_stmt_list(body, set())
        self.emit(self.syntax_text("block_close", "}"))

    def _emit_for_range(self, stmt: dict[str, Any]) -> None:
        target_node = self.any_to_dict_or_empty(stmt.get("target"))
        target_name = self.any_dict_get_str(target_node, "id", "_i")
        target = self._safe_name(target_name)
        target_type = self._cs_type(self.any_to_str(stmt.get("target_type")))
        start = self.render_expr(stmt.get("start"))
        stop = self.render_expr(stmt.get("stop"))
        step = self.render_expr(stmt.get("step"))
        range_mode = self.any_to_str(stmt.get("range_mode"))
        cond = target + " < " + stop
        if range_mode == "descending":
            cond = target + " > " + stop
        self.emit("for (" + target_type + " " + target + " = " + start + "; " + cond + "; " + target + " += " + step + ") {")
        body = self._dict_stmt_list(stmt.get("body"))
        self.emit_scoped_stmt_list(body, {target_name})
        self.emit("}")

    def _iter_is_dict_items(self, iter_node: Any) -> bool:
        """反復対象が `dict.items()` か判定する。"""
        node = self.any_to_dict_or_empty(iter_node)
        if self.any_dict_get_str(node, "kind", "") != "Call":
            return False
        fn = self.any_to_dict_or_empty(node.get("func"))
        if self.any_dict_get_str(fn, "kind", "") != "Attribute":
            return False
        attr = self.any_dict_get_str(fn, "attr", "")
        return attr == "items"

    def _emit_for(self, stmt: dict[str, Any]) -> None:
        target_node = self.any_to_dict_or_empty(stmt.get("target"))
        target_kind = self.any_dict_get_str(target_node, "kind", "")
        iter_node = stmt.get("iter")
        iter_expr = self.render_expr(iter_node)
        iter_type = self.get_expr_type(iter_node)
        body = self._dict_stmt_list(stmt.get("body"))

        if iter_type.startswith("dict[") and not self._iter_is_dict_items(iter_node):
            iter_expr = "(" + iter_expr + ").Keys"

        if target_kind == "Tuple":
            elts = self.tuple_elements(target_node)
            if len(elts) == 2:
                a_node = self.any_to_dict_or_empty(elts[0])
                b_node = self.any_to_dict_or_empty(elts[1])
                a_raw = self.any_dict_get_str(a_node, "id", "_k")
                b_raw = self.any_dict_get_str(b_node, "id", "_v")
                a = self._safe_name(a_raw)
                b = self._safe_name(b_raw)
                tmp = self.next_tmp("__it")
                self.emit("foreach (var " + tmp + " in " + iter_expr + ") {")
                if self._iter_is_dict_items(iter_node):
                    self.emit("var " + a + " = " + tmp + ".Key;")
                    self.emit("var " + b + " = " + tmp + ".Value;")
                else:
                    self.emit("var " + a + " = " + tmp + ".Item1;")
                    self.emit("var " + b + " = " + tmp + ".Item2;")
                self.emit_scoped_stmt_list(body, {a_raw, b_raw})
                self.emit("}")
                return

        target_raw = self.any_dict_get_str(target_node, "id", "_it")
        target = self._safe_name(target_raw)
        self.emit(self.syntax_line("for_open", "foreach (var {target} in {iter}) {", {"target": target, "iter": iter_expr}))
        self.emit_scoped_stmt_list(body, {target_raw})
        self.emit("}")

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
        decl = self.any_to_str(stmt.get("decl_type"))
        t_east = ann
        if t_east == "":
            t_east = decl
        if t_east == "":
            t_east = self.get_expr_type(stmt.get("value"))
        t_cs = self._cs_type(t_east)
        value_obj = stmt.get("value")
        declare = self.any_dict_get_bool(stmt, "declare", True)

        if declare and not self.is_declared(name_raw):
            self.declare_in_current_scope(name_raw)
            self.declared_var_types[name_raw] = self.normalize_type_name(t_east)
            if value_obj is None:
                if t_cs == "" or t_cs == "object":
                    self.emit("object " + name + ";")
                else:
                    self.emit(t_cs + " " + name + ";")
            else:
                value = self.render_expr(value_obj)
                if t_cs == "" or t_cs == "object":
                    self.emit("var " + name + " = " + value + ";")
                else:
                    self.emit(t_cs + " " + name + " = " + value + ";")
            return

        if value_obj is not None:
            self.emit(name + " = " + self.render_expr(value_obj) + ";")

    def _emit_assign(self, stmt: dict[str, Any]) -> None:
        target = self.any_to_dict_or_empty(stmt.get("target"))
        if len(target) == 0:
            targets = self._dict_stmt_list(stmt.get("targets"))
            if len(targets) > 0:
                target = targets[0]
        value_obj = stmt.get("value")
        value = self.render_expr(value_obj)
        target_kind = self.any_dict_get_str(target, "kind", "")

        if target_kind == "Name":
            name_raw = self.any_dict_get_str(target, "id", "_")
            name = self._safe_name(name_raw)
            declare = self.any_dict_get_bool(stmt, "declare", False)
            if declare and not self.is_declared(name_raw):
                self.declare_in_current_scope(name_raw)
                t_east = self.get_expr_type(value_obj)
                if t_east != "":
                    self.declared_var_types[name_raw] = t_east
                t_cs = self._cs_type(t_east)
                if t_cs == "" or t_cs == "object":
                    self.emit("var " + name + " = " + value + ";")
                else:
                    self.emit(t_cs + " " + name + " = " + value + ";")
                return
            self.emit(name + " = " + value + ";")
            return

        if target_kind == "Tuple":
            names = self.tuple_elements(target)
            if len(names) == 2:
                a = self.render_expr(names[0])
                b = self.render_expr(names[1])
                tmp = self.next_tmp("__tmp")
                self.emit("var " + tmp + " = " + value + ";")
                self.emit(a + " = " + tmp + ".Item1;")
                self.emit(b + " = " + tmp + ".Item2;")
                return

        self.emit(self.render_expr(target) + " = " + value + ";")

    def _emit_augassign(self, stmt: dict[str, Any]) -> None:
        target = self.render_expr(stmt.get("target"))
        value = self.render_expr(stmt.get("value"))
        op = self.any_to_str(stmt.get("op"))
        mapped = self.aug_ops.get(op, "+=")
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
            if op == "In":
                terms.append("(" + right + ".Contains(" + cur_left + "))")
            elif op == "NotIn":
                terms.append("(!" + right + ".Contains(" + cur_left + "))")
            else:
                op_txt = self.cmp_ops.get(op, "==")
                terms.append("(" + cur_left + " " + op_txt + " " + right + ")")
            cur_left = right
            i += 1
        if len(terms) == 1:
            return terms[0]
        return "(" + " && ".join(terms) + ")"

    def _render_len_call(self, arg_expr: str, arg_node: Any) -> str:
        """len(x) を C# 式へ変換する。"""
        t = self.get_expr_type(arg_node)
        if t == "str":
            return "(" + arg_expr + ").Length"
        if t.startswith("list[") or t.startswith("dict[") or t.startswith("set[") or t in {"bytes", "bytearray"}:
            return "(" + arg_expr + ").Count"
        return "(" + arg_expr + ").Count()"

    def _render_name_call(self, fn_name_raw: str, rendered_args: list[str], arg_nodes: list[Any]) -> str:
        """組み込み関数呼び出しを C# 式へ変換する。"""
        fn_name = self._safe_name(fn_name_raw)
        if fn_name_raw in self.class_names:
            return "new " + fn_name_raw + "(" + ", ".join(rendered_args) + ")"
        if fn_name_raw == "print":
            if len(rendered_args) == 0:
                return "Console.WriteLine()"
            if len(rendered_args) == 1:
                return "Console.WriteLine(" + rendered_args[0] + ")"
            return "Console.WriteLine(string.Join(\" \", new object[] { " + ", ".join(rendered_args) + " }))"
        if fn_name_raw == "len" and len(rendered_args) == 1:
            return self._render_len_call(rendered_args[0], arg_nodes[0] if len(arg_nodes) > 0 else None)
        if fn_name_raw == "str" and len(rendered_args) == 1:
            return "Convert.ToString(" + rendered_args[0] + ")"
        if fn_name_raw == "int" and len(rendered_args) == 1:
            return "Convert.ToInt64(" + rendered_args[0] + ")"
        if fn_name_raw == "float" and len(rendered_args) == 1:
            return "Convert.ToDouble(" + rendered_args[0] + ")"
        if fn_name_raw == "bool" and len(rendered_args) == 1:
            return "Convert.ToBoolean(" + rendered_args[0] + ")"
        if fn_name_raw == "Exception":
            if len(rendered_args) >= 1:
                return "new Exception(" + rendered_args[0] + ")"
            return "new Exception(\"Exception\")"
        if fn_name_raw == "enumerate":
            self.needs_enumerate_helper = True
            if len(rendered_args) == 1:
                return "Program.PytraEnumerate(" + rendered_args[0] + ")"
            if len(rendered_args) >= 2:
                return "Program.PytraEnumerate(" + rendered_args[0] + ", " + rendered_args[1] + ")"
        return fn_name + "(" + ", ".join(rendered_args) + ")"

    def _render_attr_call(self, owner_node: dict[str, Any], attr_raw: str, rendered_args: list[str]) -> str:
        """属性呼び出しを C# 式へ変換する。"""
        owner_expr = self.render_expr(owner_node)
        owner_type = self.get_expr_type(owner_node)

        if owner_type == "str":
            if attr_raw == "join" and len(rendered_args) == 1:
                return "string.Join(" + owner_expr + ", " + rendered_args[0] + ")"

        if owner_type.startswith("list[") or owner_type in {"bytes", "bytearray"}:
            if attr_raw == "append" and len(rendered_args) == 1:
                return owner_expr + ".Add(" + rendered_args[0] + ")"
            if attr_raw == "clear" and len(rendered_args) == 0:
                return owner_expr + ".Clear()"
            if attr_raw == "pop" and len(rendered_args) == 0:
                return owner_expr + "[" + owner_expr + ".Count - 1]"

        if owner_type.startswith("dict["):
            if attr_raw == "get":
                if len(rendered_args) == 1:
                    k = rendered_args[0]
                    return "(" + owner_expr + ".ContainsKey(" + k + ") ? " + owner_expr + "[" + k + "] : default)"
                if len(rendered_args) >= 2:
                    k = rendered_args[0]
                    d = rendered_args[1]
                    return "(" + owner_expr + ".ContainsKey(" + k + ") ? " + owner_expr + "[" + k + "] : " + d + ")"
            if attr_raw == "items" and len(rendered_args) == 0:
                return owner_expr
            if attr_raw == "keys" and len(rendered_args) == 0:
                return owner_expr + ".Keys"
            if attr_raw == "values" and len(rendered_args) == 0:
                return owner_expr + ".Values"

        attr = self._safe_name(attr_raw)
        return owner_expr + "." + attr + "(" + ", ".join(rendered_args) + ")"

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
            return self._render_name_call(fn_name_raw, rendered_args, arg_nodes)

        if fn_kind == "Attribute":
            owner_node = self.any_to_dict_or_empty(fn_node.get("value"))
            attr_raw = self.any_dict_get_str(fn_node, "attr", "")
            return self._render_attr_call(owner_node, attr_raw, rendered_args)

        fn_expr = self.render_expr(fn_node)
        return fn_expr + "(" + ", ".join(rendered_args) + ")"

    def render_expr(self, expr: Any) -> str:
        """式ノードを C# へ描画する。"""
        expr_d = self.any_to_dict_or_empty(expr)
        if len(expr_d) == 0:
            return "null"
        kind = self.any_dict_get_str(expr_d, "kind", "")

        hook_leaf = self.hook_on_render_expr_leaf(kind, expr_d)
        if hook_leaf != "":
            return hook_leaf

        if kind == "Name":
            name = self.any_dict_get_str(expr_d, "id", "_")
            if name == "self" and self.in_method_scope:
                return "this"
            return self._safe_name(name)

        if kind == "Constant":
            tag, non_str = self.render_constant_non_string_common(expr, expr_d, "null", "null")
            if tag == "1":
                return non_str
            return cs_string_lit(self.any_to_str(expr_d.get("value")))

        if kind == "Attribute":
            owner_node = self.any_to_dict_or_empty(expr_d.get("value"))
            owner_kind = self.any_dict_get_str(owner_node, "kind", "")
            if owner_kind == "Name" and self.any_dict_get_str(owner_node, "id", "") == "self" and self.in_method_scope:
                return "this." + self._safe_name(self.any_dict_get_str(expr_d, "attr", ""))
            return self.render_expr(owner_node) + "." + self._safe_name(self.any_dict_get_str(expr_d, "attr", ""))

        if kind == "UnaryOp":
            op = self.any_dict_get_str(expr_d, "op", "")
            operand = self.render_expr(expr_d.get("operand"))
            if op == "USub":
                return "(-" + operand + ")"
            if op == "Not":
                return "(!" + operand + ")"
            return operand

        if kind == "BinOp":
            op = self.any_to_str(expr_d.get("op"))
            left_node = self.any_to_dict_or_empty(expr_d.get("left"))
            right_node = self.any_to_dict_or_empty(expr_d.get("right"))
            left = self._wrap_for_binop_operand(self.render_expr(left_node), left_node, op, is_right=False)
            right = self._wrap_for_binop_operand(self.render_expr(right_node), right_node, op, is_right=True)
            custom = self.hook_on_render_binop(expr_d, left, right)
            if custom != "":
                return custom
            if op == "FloorDiv":
                return "((long)Math.Floor((double)(" + left + ") / (double)(" + right + ")))"
            mapped = self.bin_ops.get(op, "+")
            return "(" + left + " " + mapped + " " + right + ")"

        if kind == "Compare":
            return self._render_compare(expr_d)

        if kind == "BoolOp":
            vals = self.any_to_list(expr_d.get("values"))
            op = self.any_to_str(expr_d.get("op"))
            return self.render_boolop_common(vals, op, and_token="&&", or_token="||", empty_literal="false")

        if kind == "Call":
            hook = self.hook_on_render_call(expr_d, self.any_to_dict_or_empty(expr_d.get("func")), [], {})
            if hook != "":
                return hook
            return self._render_call(expr_d)

        if kind == "IfExp":
            return self._render_ifexp_expr(expr_d)

        if kind == "List":
            return self._typed_list_literal(expr_d)

        if kind == "Tuple":
            elts = self.tuple_elements(expr_d)
            rendered: list[str] = []
            for elt in elts:
                rendered.append(self.render_expr(elt))
            if len(rendered) == 1:
                return "(" + rendered[0] + ",)"
            return "(" + ", ".join(rendered) + ")"

        if kind == "Dict":
            return self._typed_dict_literal(expr_d)

        if kind == "Subscript":
            owner = self.render_expr(expr_d.get("value"))
            idx = self.render_expr(expr_d.get("slice"))
            return owner + "[(int)(" + idx + ")]"

        if kind == "Lambda":
            args = self.any_to_list(self.any_to_dict_or_empty(expr_d.get("args")).get("args"))
            names: list[str] = []
            for arg in args:
                names.append(self._safe_name(self.any_to_str(self.any_to_dict_or_empty(arg).get("arg"))))
            body = self.render_expr(expr_d.get("body"))
            return "(" + ", ".join(names) + ") => " + body

        hook_complex = self.hook_on_render_expr_complex(expr_d)
        if hook_complex != "":
            return hook_complex

        rep = self.any_to_str(expr_d.get("repr"))
        if rep != "":
            return rep
        return "null"

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
            return rendered + ".Length != 0"
        if t.startswith("list[") or t.startswith("dict[") or t.startswith("set[") or t.startswith("tuple["):
            return rendered + ".Count != 0"
        if t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64"}:
            return rendered + " != 0"
        return rendered


def transpile_to_csharp(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを C# コードへ変換する。"""
    emitter = CSharpEmitter(east_doc)
    return emitter.transpile()
