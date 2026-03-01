"""EAST -> C# transpiler."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.cs.hooks.cs_hooks import build_cs_hooks
from pytra.compiler.east_parts.code_emitter import CodeEmitter


def load_cs_profile() -> dict[str, Any]:
    """C# 用 profile を読み込む。"""
    return CodeEmitter.load_profile_with_includes(
        "src/profiles/cs/profile.json",
        "src/py2cs.py",
    )


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
        profile = CodeEmitter.load_profile_with_includes("src/profiles/cs/profile.json", "src/py2cs.py")
        hooks: dict[str, Any] = {}
        self.init_base_state(east_doc, profile, hooks)
        self.type_map = CodeEmitter.load_type_map(profile)
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
        self.class_base_map: dict[str, str] = {}
        self.current_class_name: str = ""
        self.current_class_field_types: dict[str, str] = {}
        self.in_method_scope: bool = False
        self.needs_enumerate_helper: bool = False
        self.needs_dict_str_object_helper: bool = False
        self.current_return_east_type: str = ""
        self.top_function_names: set[str] = set()

    def get_expr_type(self, expr: Any) -> str:
        """解決済み型 + ローカル宣言テーブルで式型を返す。"""
        expr_node = self.any_to_dict_or_empty(expr)
        t = self.any_dict_get_str(expr_node, "resolved_type", "")
        if t != "":
            t = self.normalize_type_name(t)
        elif self.any_dict_has(expr_node, "resolved_type"):
            raw = expr_node["resolved_type"] if "resolved_type" in expr_node else None
            if isinstance(raw, str):
                txt = self.any_to_str(raw)
                if txt == "":
                    txt = str(raw)
                if not self._is_empty_dynamic_text(txt):
                    t = self.normalize_type_name(txt)
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
        if module_id in {"math", "time", "dataclasses"}:
            return ""
        if module_id.startswith("pytra."):
            return "Pytra.CsModule"
        return module_id

    def _module_alias_target(self, module_id: str, export_name: str, binding_kind: str) -> str:
        """既知モジュール import を C# alias 先へ解決する。"""
        if binding_kind == "module":
            if module_id == "math":
                return "Pytra.CsModule.math"
            if module_id == "time":
                return "Pytra.CsModule.time"
            if module_id in {"pytra.runtime", "pytra.utils"}:
                return "Pytra.CsModule"
            return ""
        if binding_kind == "symbol":
            if module_id in {"pytra.runtime", "pytra.utils"} and export_name == "png":
                return "Pytra.CsModule.png_helper"
            if module_id in {"pytra.runtime", "pytra.utils"} and export_name == "gif":
                return "Pytra.CsModule.gif_helper"
            if module_id in {"pathlib", "pytra.std.pathlib"} and export_name == "Path":
                return "Pytra.CsModule.py_path"
            return ""
        return ""

    def _walk_node_names(self, node: Any, out: set[str]) -> None:
        """ノード配下の Name.id を収集する（Import/ImportFrom 自身は除外）。"""
        if isinstance(node, dict):
            node_dict = self.any_to_dict_or_empty(node)
            kind = self.any_dict_get_str(node_dict, "kind", "")
            if kind == "Import" or kind == "ImportFrom":
                return
            if kind == "Name":
                name = self.any_dict_get_str(node_dict, "id", "")
                if name != "":
                    out.add(name)
                return
            for key in node_dict:
                if key == "comments":
                    continue
                self._walk_node_names(node_dict[key], out)
            return
        if isinstance(node, list):
            for item in node:
                self._walk_node_names(item, out)

    def _collect_used_names(self, body: list[dict[str, Any]], main_guard_body: list[dict[str, Any]]) -> set[str]:
        """モジュール全体で実際に参照される識別子名を収集する。"""
        used: set[str] = set()
        for stmt in body:
            self._walk_node_names(stmt, used)
        for stmt in main_guard_body:
            self._walk_node_names(stmt, used)
        return used

    def _add_unique_using_line(self, out: list[str], seen: set[str], line: str) -> None:
        """using 行を重複排除しつつ追加する。"""
        if line == "" or line in seen:
            return
        seen.add(line)
        out.append(line)

    def _collect_using_lines(
        self,
        body: list[dict[str, Any]],
        meta: dict[str, Any],
        used_names: set[str],
    ) -> list[str]:
        """import 情報を C# using 行へ変換する。"""
        out: list[str] = []
        seen: set[str] = set(out)

        self._add_unique_using_line(out, seen, "using System;")
        self._add_unique_using_line(out, seen, "using System.Collections.Generic;")
        self._add_unique_using_line(out, seen, "using System.Linq;")
        self._add_unique_using_line(out, seen, "using Pytra.CsModule;")

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
                alias_target = self._module_alias_target(module_id, export_name, binding_kind)
                if alias_target != "" and local_name != "" and local_name in used_names:
                    self._add_unique_using_line(out, seen, "using " + self._safe_name(local_name) + " = " + alias_target + ";")
                    i += 1
                    continue
                if binding_kind == "symbol" and module_id in {"time", "dataclasses"}:
                    i += 1
                    continue
                ns = self._module_id_to_cs_namespace(module_id)
                if ns == "":
                    i += 1
                    continue
                if binding_kind == "module":
                    if local_name != "":
                        if local_name not in used_names:
                            i += 1
                            continue
                        leaf = self._last_dotted_name(module_id)
                        if local_name != leaf:
                            self._add_unique_using_line(out, seen, "using " + self._safe_name(local_name) + " = " + ns + ";")
                        else:
                            self._add_unique_using_line(out, seen, "using " + ns + ";")
                    else:
                        self._add_unique_using_line(out, seen, "using " + ns + ";")
                elif binding_kind == "symbol" and export_name != "":
                    if local_name != "" and local_name in used_names:
                        if local_name != export_name:
                            self._add_unique_using_line(out, seen, "using " + self._safe_name(local_name) + " = " + ns + "." + export_name + ";")
                i += 1
            return out

        for stmt in body:
            kind = self.any_dict_get_str(stmt, "kind", "")
            if kind == "Import":
                for ent in self._dict_stmt_list(stmt.get("names")):
                    module_id = self.any_to_str(ent.get("name"))
                    asname = self.any_to_str(ent.get("asname"))
                    if module_id == "" or module_id.startswith("__future__") or module_id in {"typing", "pytra.std.typing"}:
                        continue
                    if module_id == "browser" or module_id.startswith("browser."):
                        continue
                    alias_target = self._module_alias_target(module_id, "", "module")
                    if alias_target != "":
                        if asname != "":
                            if asname not in used_names:
                                continue
                            self._add_unique_using_line(out, seen, "using " + self._safe_name(asname) + " = " + alias_target + ";")
                        else:
                            leaf_alias = self._last_dotted_name(module_id)
                            if leaf_alias in used_names:
                                self._add_unique_using_line(out, seen, "using " + self._safe_name(leaf_alias) + " = " + alias_target + ";")
                        continue
                    ns = self._module_id_to_cs_namespace(module_id)
                    if ns == "":
                        continue
                    if asname != "":
                        if asname not in used_names:
                            continue
                        self._add_unique_using_line(out, seen, "using " + self._safe_name(asname) + " = " + ns + ";")
                    else:
                        leaf = self._last_dotted_name(module_id)
                        if leaf not in used_names:
                            continue
                        self._add_unique_using_line(out, seen, "using " + ns + ";")
            elif kind == "ImportFrom":
                module_id = self.any_to_str(stmt.get("module"))
                if module_id == "" or module_id.startswith("__future__") or module_id in {"typing", "pytra.std.typing"}:
                    continue
                if module_id == "browser" or module_id.startswith("browser."):
                    continue
                ns = self._module_id_to_cs_namespace(module_id)
                if ns == "":
                    continue
                for ent in self._dict_stmt_list(stmt.get("names")):
                    sym = self.any_to_str(ent.get("name"))
                    asname = self.any_to_str(ent.get("asname"))
                    if sym == "" or sym == "*":
                        continue
                    alias_target = self._module_alias_target(module_id, sym, "symbol")
                    if alias_target != "":
                        alias_name = asname if asname != "" else sym
                        if alias_name in used_names:
                            self._add_unique_using_line(out, seen, "using " + self._safe_name(alias_name) + " = " + alias_target + ";")
                        continue
                    if asname != "" and asname != sym:
                        if asname not in used_names:
                            continue
                        self._add_unique_using_line(out, seen, "using " + self._safe_name(asname) + " = " + ns + "." + sym + ";")
                    elif sym in used_names:
                        self._add_unique_using_line(out, seen, "using " + ns + ";")
        return out

    def _cs_type(self, east_type: str) -> str:
        """EAST 型名を C# 型名へ変換する。"""
        t = self.normalize_type_name(east_type)
        if t == "" or t == "unknown":
            return "object"
        mapped = self.any_dict_get_str(self.type_map, t, "")
        if mapped != "":
            return mapped
        if t.startswith("list[") and t.endswith("]"):
            inner = t[5:-1].strip()
            return "System.Collections.Generic.List<" + self._cs_type(inner) + ">"
        if t.startswith("set[") and t.endswith("]"):
            inner = t[4:-1].strip()
            return "System.Collections.Generic.HashSet<" + self._cs_type(inner) + ">"
        if t.startswith("dict[") and t.endswith("]"):
            parts = self.split_generic(t[5:-1].strip())
            if len(parts) == 2:
                return "System.Collections.Generic.Dictionary<" + self._cs_type(parts[0]) + ", " + self._cs_type(parts[1]) + ">"
        if t.startswith("tuple[") and t.endswith("]"):
            parts = self.split_generic(t[6:-1].strip())
            if not self._is_value_tuple_arity(len(parts)):
                return "System.Collections.Generic.List<object>"
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

    def _render_list_literal_with_elem_type(self, expr_d: dict[str, Any], elem_t: str, elem_hint_east: str = "") -> str:
        if elem_t == "" or elem_t == "unknown":
            elem_t = "object"
        elts = self.any_to_list(expr_d.get("elts"))
        if len(elts) == 0:
            elts = self.any_to_list(expr_d.get("elements"))
        if len(elts) == 0:
            return "new System.Collections.Generic.List<" + elem_t + ">()"
        rendered: list[str] = []
        for elt in elts:
            if elem_hint_east != "":
                rendered.append(self._render_expr_with_type_hint(elt, elem_hint_east))
            else:
                rendered.append(self.render_expr(elt))
        return "new System.Collections.Generic.List<" + elem_t + "> { " + ", ".join(rendered) + " }"

    def _typed_list_literal(self, expr_d: dict[str, Any]) -> str:
        """List リテラルを C# 式へ描画する。"""
        list_t = self.get_expr_type(expr_d)
        elem_t = "object"
        elem_hint_east = ""
        if list_t.startswith("list[") and list_t.endswith("]"):
            elem_hint_east = list_t[5:-1].strip()
            elem_t = self._cs_type(elem_hint_east)
        return self._render_list_literal_with_elem_type(expr_d, elem_t, elem_hint_east)

    def _render_set_literal_with_elem_type(self, expr_d: dict[str, Any], elem_t: str, elem_hint_east: str = "") -> str:
        if elem_t == "" or elem_t == "unknown":
            elem_t = "object"
        elts = self.any_to_list(expr_d.get("elts"))
        if len(elts) == 0:
            elts = self.any_to_list(expr_d.get("elements"))
        if len(elts) == 0:
            return "new System.Collections.Generic.HashSet<" + elem_t + ">()"
        rendered: list[str] = []
        for elt in elts:
            if elem_hint_east != "":
                rendered.append(self._render_expr_with_type_hint(elt, elem_hint_east))
            else:
                rendered.append(self.render_expr(elt))
        return "new System.Collections.Generic.HashSet<" + elem_t + "> { " + ", ".join(rendered) + " }"

    def _typed_set_literal(self, expr_d: dict[str, Any]) -> str:
        set_t = self.get_expr_type(expr_d)
        elem_t = "object"
        elem_hint_east = ""
        if set_t.startswith("set[") and set_t.endswith("]"):
            elem_hint_east = set_t[4:-1].strip()
            elem_t = self._cs_type(elem_hint_east)
        return self._render_set_literal_with_elem_type(expr_d, elem_t, elem_hint_east)

    def _render_dict_literal_with_types(self, expr_d: dict[str, Any], key_t: str, val_t: str) -> str:
        if key_t == "" or key_t == "unknown":
            key_t = "object"
        if val_t == "" or val_t == "unknown":
            val_t = "object"
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
            return "new System.Collections.Generic.Dictionary<" + key_t + ", " + val_t + ">()"
        return "new System.Collections.Generic.Dictionary<" + key_t + ", " + val_t + "> { " + ", ".join(pairs) + " }"

    def _dict_literal_key_value_nodes(self, expr_d: dict[str, Any]) -> tuple[list[Any], list[Any]]:
        key_nodes: list[Any] = []
        value_nodes: list[Any] = []
        entries = self.any_to_list(expr_d.get("entries"))
        if len(entries) > 0:
            for entry in entries:
                ent = self.any_to_dict_or_empty(entry)
                key_nodes.append(ent.get("key"))
                value_nodes.append(ent.get("value"))
            return key_nodes, value_nodes
        keys = self.any_to_list(expr_d.get("keys"))
        vals = self.any_to_list(expr_d.get("values"))
        i = 0
        while i < len(keys) and i < len(vals):
            key_nodes.append(keys[i])
            value_nodes.append(vals[i])
            i += 1
        return key_nodes, value_nodes

    def _node_can_flow_to_cs_type(self, node_obj: Any, cs_t: str) -> bool:
        if cs_t == "" or cs_t == "object":
            return True
        node = self.any_to_dict_or_empty(node_obj)
        east_t = self.normalize_type_name(self.get_expr_type(node))
        if east_t != "" and east_t != "unknown":
            src_cs = self._cs_type(east_t)
            if src_cs == cs_t:
                return True
            if cs_t in {"float", "double"} and src_cs in {
                "byte",
                "sbyte",
                "short",
                "ushort",
                "int",
                "uint",
                "long",
                "ulong",
                "float",
                "double",
            }:
                return True
            if cs_t in {"byte", "sbyte", "short", "ushort", "int", "uint", "long", "ulong"} and src_cs in {
                "byte",
                "sbyte",
                "short",
                "ushort",
                "int",
                "uint",
                "long",
                "ulong",
            }:
                return True
            return False
        if self.any_dict_get_str(node, "kind", "") == "Constant":
            value = node.get("value")
            if value is None:
                return cs_t not in {"bool", "byte", "sbyte", "short", "ushort", "int", "uint", "long", "ulong", "float", "double", "char"}
            if isinstance(value, bool):
                return cs_t == "bool"
            if isinstance(value, str):
                return cs_t == "string"
            if isinstance(value, int):
                return cs_t in {"byte", "sbyte", "short", "ushort", "int", "uint", "long", "ulong", "float", "double"}
            if isinstance(value, float):
                return cs_t in {"float", "double"}
        return False

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
        key_nodes, value_nodes = self._dict_literal_key_value_nodes(expr_d)
        if key_t != "object":
            for key_node in key_nodes:
                if not self._node_can_flow_to_cs_type(key_node, key_t):
                    key_t = "object"
                    break
        if val_t != "object":
            for value_node in value_nodes:
                if not self._node_can_flow_to_cs_type(value_node, val_t):
                    val_t = "object"
                    break
        return self._render_dict_literal_with_types(expr_d, key_t, val_t)

    def _render_expr_with_type_hint(self, value_obj: Any, east_type_hint: str) -> str:
        """型ヒント付きで式を描画し、空 list/dict の要素型を補う。"""
        node = self.any_to_dict_or_empty(value_obj)
        kind = self.any_dict_get_str(node, "kind", "")
        hint = self.normalize_type_name(east_type_hint)
        if kind == "List" and hint.startswith("list[") and hint.endswith("]"):
            elem_hint_east = hint[5:-1].strip()
            elem_t = self._cs_type(elem_hint_east)
            return self._render_list_literal_with_elem_type(node, elem_t, elem_hint_east)
        if kind == "Dict" and hint.startswith("dict[") and hint.endswith("]"):
            parts = self.split_generic(hint[5:-1].strip())
            if len(parts) == 2:
                return self._render_dict_literal_with_types(node, self._cs_type(parts[0]), self._cs_type(parts[1]))
        if kind == "Set" and hint.startswith("set[") and hint.endswith("]"):
            elem_hint_east = hint[4:-1].strip()
            return self._render_set_literal_with_elem_type(node, self._cs_type(elem_hint_east), elem_hint_east)
        if kind == "ListComp" and hint.startswith("list[") and hint.endswith("]"):
            return self._render_list_comp_expr(node, hint[5:-1].strip())
        if kind == "Call":
            fn_node = self.any_to_dict_or_empty(node.get("func"))
            if self.any_dict_get_str(fn_node, "kind", "") == "Name":
                fn_raw = self.any_dict_get_str(fn_node, "id", "")
                arg_nodes = self.any_to_list(node.get("args"))
                rendered_args: list[str] = []
                for arg_node in arg_nodes:
                    rendered_args.append(self.render_expr(arg_node))
                if fn_raw == "set" and hint.startswith("set[") and hint.endswith("]"):
                    elem_cs_t = self._cs_type(hint[4:-1].strip())
                    if elem_cs_t == "":
                        elem_cs_t = "object"
                    if len(rendered_args) == 0:
                        return "new System.Collections.Generic.HashSet<" + elem_cs_t + ">()"
                    return "new System.Collections.Generic.HashSet<" + elem_cs_t + ">(" + rendered_args[0] + ")"
                if fn_raw == "list" and hint.startswith("list[") and hint.endswith("]"):
                    elem_cs_t = self._cs_type(hint[5:-1].strip())
                    if elem_cs_t == "":
                        elem_cs_t = "object"
                    if len(rendered_args) == 0:
                        return "new System.Collections.Generic.List<" + elem_cs_t + ">()"
                    return "new System.Collections.Generic.List<" + elem_cs_t + ">(" + rendered_args[0] + ")"
                if fn_raw == "dict" and hint.startswith("dict[") and hint.endswith("]"):
                    dict_parts = self.split_generic(hint[5:-1].strip())
                    if len(dict_parts) == 2:
                        key_t = self._cs_type(dict_parts[0])
                        val_t = self._cs_type(dict_parts[1])
                        if key_t == "":
                            key_t = "object"
                        if val_t == "":
                            val_t = "object"
                        if len(rendered_args) == 0:
                            return "new System.Collections.Generic.Dictionary<" + key_t + ", " + val_t + ">()"
                        if key_t == "string" and val_t == "object":
                            self.needs_dict_str_object_helper = True
                            return "Program.PytraDictStringObjectFromAny(" + rendered_args[0] + ")"
                        return "new System.Collections.Generic.Dictionary<" + key_t + ", " + val_t + ">(" + rendered_args[0] + ")"
        return self.render_expr(value_obj)

    def _render_list_repeat(self, list_node: dict[str, Any], list_expr: str, count_expr: str) -> str:
        """Python の list 乗算（`[x] * n`）を C# 式へ lower する。"""
        list_t = self.get_expr_type(list_node)
        elem_t = "object"
        if list_t.startswith("list[") and list_t.endswith("]"):
            elem_t = self._cs_type(list_t[5:-1].strip())
        if elem_t == "" or elem_t == "unknown":
            elem_t = "object"
        base_name = self.next_tmp("__base")
        count_name = self.next_tmp("__n")
        out_name = self.next_tmp("__out")
        idx_name = self.next_tmp("__i")
        return (
            "(new System.Func<System.Collections.Generic.List<"
            + elem_t
            + ">>(() => { var "
            + base_name
            + " = "
            + list_expr
            + "; long "
            + count_name
            + " = System.Convert.ToInt64("
            + count_expr
            + "); if ("
            + count_name
            + " < 0) { "
            + count_name
            + " = 0; } var "
            + out_name
            + " = new System.Collections.Generic.List<"
            + elem_t
            + ">(); for (long "
            + idx_name
            + " = 0; "
            + idx_name
            + " < "
            + count_name
            + "; "
            + idx_name
            + " += 1) { "
            + out_name
            + ".AddRange("
            + base_name
            + "); } return "
            + out_name
            + "; }))()"
        )

    def _is_string_expr_node(self, node: dict[str, Any]) -> bool:
        """式ノードが文字列値として扱えるかを返す。"""
        if self.get_expr_type(node) == "str":
            return True
        if self.any_dict_get_str(node, "kind", "") == "Constant":
            return isinstance(node.get("value"), str)
        return False

    def _render_string_repeat(self, text_expr: str, count_expr: str) -> str:
        """Python の文字列乗算（`\"a\" * n`）を C# 式へ lower する。"""
        return "string.Concat(System.Linq.Enumerable.Repeat(" + text_expr + ", System.Convert.ToInt32(" + count_expr + ")))"

    def _render_optional_default_value(self, default_node: Any) -> str:
        """C# optional parameter の既定値リテラルを描画する。"""
        node = self.any_to_dict_or_empty(default_node)
        if self.any_dict_get_str(node, "kind", "") != "Constant":
            return ""
        value = node.get("value")
        if isinstance(value, bool):
            return "true" if self.any_to_bool(value) else "false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            as_float = float(value)
            as_int = int(as_float)
            if float(as_int) == as_float:
                return str(as_int) + ".0"
            return str(as_float)
        if isinstance(value, str):
            return self.quote_string_literal(value)
        if value is None:
            return "null"
        return ""

    def _escape_interpolated_literal_text(self, text: str) -> str:
        """C# 補間文字列で安全に使えるようリテラルをエスケープする。"""
        return (
            text.replace("\\", "\\\\")
            .replace("\"", "\\\"")
            .replace("{", "{{")
            .replace("}", "}}")
        )

    def _tuple_arity_from_type_name(self, east_type: str) -> int:
        """`tuple[...]` 型名から要素数を返す（非 tuple は 0）。"""
        norm = self.normalize_type_name(east_type)
        if not (norm.startswith("tuple[") and norm.endswith("]")):
            return 0
        inner = norm[6:-1].strip()
        if inner == "":
            return 0
        return len(self.split_generic(inner))

    def _is_value_tuple_arity(self, arity: int) -> bool:
        """mcs で安全に扱える C# tuple arity か。"""
        return arity >= 2 and arity <= 7

    def _render_range_expr(self, expr_d: dict[str, Any]) -> str:
        """RangeExpr を C# `List<long>` 生成式へ lower する。"""
        start = self.render_expr(expr_d.get("start"))
        stop = self.render_expr(expr_d.get("stop"))
        step = self.render_expr(expr_d.get("step"))
        out_name = self.next_tmp("__out")
        start_name = self.next_tmp("__start")
        stop_name = self.next_tmp("__stop")
        step_name = self.next_tmp("__step")
        idx_name = self.next_tmp("__i")
        return (
            "(new System.Func<System.Collections.Generic.List<long>>(() => { var "
            + out_name
            + " = new System.Collections.Generic.List<long>(); "
            + "long "
            + start_name
            + " = System.Convert.ToInt64("
            + start
            + "); long "
            + stop_name
            + " = System.Convert.ToInt64("
            + stop
            + "); long "
            + step_name
            + " = System.Convert.ToInt64("
            + step
            + "); if ("
            + step_name
            + " == 0) { return "
            + out_name
            + "; } "
            + "if ("
            + step_name
            + " > 0) { for (long "
            + idx_name
            + " = "
            + start_name
            + "; "
            + idx_name
            + " < "
            + stop_name
            + "; "
            + idx_name
            + " += "
            + step_name
            + ") { "
            + out_name
            + ".Add("
            + idx_name
            + "); } } "
            + "else { for (long "
            + idx_name
            + " = "
            + start_name
            + "; "
            + idx_name
            + " > "
            + stop_name
            + "; "
            + idx_name
            + " += "
            + step_name
            + ") { "
            + out_name
            + ".Add("
            + idx_name
            + "); } } return "
            + out_name
            + "; }))()"
        )

    def _render_comp_target(self, target_node: dict[str, Any]) -> str:
        kind = self.any_dict_get_str(target_node, "kind", "")
        if kind == "Name":
            raw = self.any_dict_get_str(target_node, "id", "_")
            if raw == "_":
                return self.next_tmp("__it")
            return self._safe_name(raw)
        return "_"

    def _render_list_comp_expr(self, expr_d: dict[str, Any], forced_out_type: str = "") -> str:
        """ListComp を C# `List<T>` 構築式へ lower する。"""
        generators = self.any_to_list(expr_d.get("generators"))
        if len(generators) == 0:
            return "new System.Collections.Generic.List<object>()"

        out_t = "object"
        if forced_out_type != "":
            out_t = self._cs_type(forced_out_type)
        else:
            list_t = self.get_expr_type(expr_d)
            if list_t.startswith("list[") and list_t.endswith("]"):
                out_t = self._cs_type(list_t[5:-1].strip())
        if out_t == "" or out_t == "unknown":
            out_t = "object"

        elt_expr = self.render_expr(expr_d.get("elt"))
        out_name = self.next_tmp("__out")
        parts: list[str] = []
        parts.append("(new System.Func<System.Collections.Generic.List<" + out_t + ">>(() => {")
        parts.append("var " + out_name + " = new System.Collections.Generic.List<" + out_t + ">();")

        depth = 0
        for gen in generators:
            gen_d = self.any_to_dict_or_empty(gen)
            target_txt = self._render_comp_target(self.any_to_dict_or_empty(gen_d.get("target")))
            iter_expr = self.render_expr(gen_d.get("iter"))
            parts.append("foreach (var " + target_txt + " in " + iter_expr + ") {")
            depth += 1
            for cond_node in self.any_to_list(gen_d.get("ifs")):
                parts.append("if (!(" + self.render_cond(cond_node) + ")) { continue; }")

        parts.append(out_name + ".Add(" + elt_expr + ");")
        while depth > 0:
            parts.append("}")
            depth -= 1
        parts.append("return " + out_name + ";")
        parts.append("}))()")
        return " ".join(parts)

    def _collect_class_base_map(self, body: list[dict[str, Any]]) -> dict[str, str]:
        """ClassDef から `child -> base` の継承表を抽出する。"""
        out: dict[str, str] = {}
        for stmt in body:
            if self.any_dict_get_str(stmt, "kind", "") != "ClassDef":
                continue
            child = self.any_to_str(stmt.get("name"))
            if child == "":
                continue
            base = self.normalize_type_name(self.any_to_str(stmt.get("base")))
            if base != "":
                out[child] = base
        return out

    def transpile(self) -> str:
        """モジュール全体を C# ソースへ変換する。"""
        self.lines: list[str] = []
        self.scope_stack: list[set[str]] = [set()]
        self.declared_var_types = {}
        self.needs_enumerate_helper = False
        self.needs_dict_str_object_helper = False
        self.in_method_scope = False

        module = self.doc
        body = self._dict_stmt_list(module.get("body"))
        main_guard_body = self._dict_stmt_list(module.get("main_guard_body"))
        meta = self.any_to_dict_or_empty(module.get("meta"))
        self.load_import_bindings_from_meta(meta)
        self.emit_module_leading_trivia()

        used_names = self._collect_used_names(body, main_guard_body)
        using_lines = self._collect_using_lines(body, meta, used_names)
        for line in using_lines:
            self.emit(line)
        if len(using_lines) > 0:
            self.emit("")

        self.class_names = set()
        self.class_base_map = {}
        for stmt in body:
            if self.any_dict_get_str(stmt, "kind", "") == "ClassDef":
                name = self.any_to_str(stmt.get("name"))
                if name != "":
                    self.class_names.add(name)
        self.class_base_map = self._collect_class_base_map(body)

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
        self.top_function_names = set()
        for fn in function_stmts:
            fn_name = self.any_to_str(fn.get("name"))
            if fn_name != "":
                self.top_function_names.add(fn_name)

        for cls in class_stmts:
            self.emit_leading_comments(cls)
            self._emit_class(cls)
            self.emit("")

        self.emit("public static class Program")
        self.emit("{")
        self.indent += 1

        for fn in function_stmts:
            self.emit_leading_comments(fn)
            self._emit_function(fn, None)
            self.emit("")

        main_body = list(top_level_stmts) + main_guard_body
        self.emit("public static void Main(string[] args)")
        self.emit("{")
        self.indent += 1
        self.emit_scoped_stmt_list(main_body, {"args"})
        self.indent -= 1
        self.emit("}")

        if self.needs_enumerate_helper:
            self.emit("")
            self._emit_enumerate_helper()
        if self.needs_dict_str_object_helper:
            self.emit("")
            self._emit_dict_str_object_helper()

        self.indent -= 1
        self.emit("}")

        return "\n".join(self.lines) + ("\n" if len(self.lines) > 0 else "")

    def _emit_enumerate_helper(self) -> None:
        """enumerate() 用の最小 helper を出力する。"""
        self.emit(
            "public static System.Collections.Generic.IEnumerable<(long, T)> "
            + "PytraEnumerate<T>(System.Collections.Generic.IEnumerable<T> source, long start = 0)"
        )
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

    def _emit_dict_str_object_helper(self) -> None:
        """object から `Dictionary<string, object>` へ安全に複製する helper。"""
        self.emit(
            "public static System.Collections.Generic.Dictionary<string, object> "
            + "PytraDictStringObjectFromAny(object source)"
        )
        self.emit("{")
        self.indent += 1
        self.emit("if (source is System.Collections.Generic.Dictionary<string, object> typed)")
        self.emit("{")
        self.indent += 1
        self.emit("return new System.Collections.Generic.Dictionary<string, object>(typed);")
        self.indent -= 1
        self.emit("}")
        self.emit("var outv = new System.Collections.Generic.Dictionary<string, object>();")
        self.emit("var dictRaw = source as System.Collections.IDictionary;")
        self.emit("if (dictRaw == null)")
        self.emit("{")
        self.indent += 1
        self.emit("return outv;")
        self.indent -= 1
        self.emit("}")
        self.emit("foreach (System.Collections.DictionaryEntry ent in dictRaw)")
        self.emit("{")
        self.indent += 1
        self.emit("string key = System.Convert.ToString(ent.Key);")
        self.emit("if (key == null || key == \"\")")
        self.emit("{")
        self.indent += 1
        self.emit("continue;")
        self.indent -= 1
        self.emit("}")
        self.emit("outv[key] = ent.Value;")
        self.indent -= 1
        self.emit("}")
        self.emit("return outv;")
        self.indent -= 1
        self.emit("}")

    def _emit_class(self, stmt: dict[str, Any]) -> None:
        """ClassDef を C# class として出力する。"""
        class_name_raw = self.any_to_str(stmt.get("name"))
        class_name = self._safe_name(class_name_raw)
        prev_class = self.current_class_name
        prev_class_field_types: dict[str, str] = dict(self.current_class_field_types)
        prev_method_scope = self.in_method_scope
        self.current_class_name = class_name_raw

        base_name = self.class_base_map.get(class_name_raw, "")
        base_decl = ""
        if base_name != "":
            base_cs = self._cs_type(base_name)
            if base_cs != "" and base_cs != "object":
                base_decl = " : " + base_cs

        self.emit("public class " + class_name + base_decl)
        self.emit("{")
        self.indent += 1

        base_type_id_expr = self._type_id_expr_for_name(base_name)
        if base_type_id_expr == "":
            base_type_id_expr = "Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT"
        self.emit(
            "public static readonly long PYTRA_TYPE_ID = "
            + "Pytra.CsModule.py_runtime.py_register_class_type("
            + base_type_id_expr
            + ");"
        )

        field_types = self.any_to_dict_or_empty(stmt.get("field_types"))
        self.current_class_field_types = {}
        for field_name_obj, field_t_obj in field_types.items():
            if isinstance(field_name_obj, str):
                self.current_class_field_types[field_name_obj] = self.any_to_str(field_t_obj)
        instance_fields: set[str] = set()
        for field_name, field_t_obj in field_types.items():
            if not isinstance(field_name, str):
                continue
            instance_fields.add(field_name)
            field_t = self._cs_type(self.any_to_str(field_t_obj))
            self.emit("public " + field_t + " " + self._safe_name(field_name) + ";")

        members = self._dict_stmt_list(stmt.get("body"))
        for member in members:
            kind = self.any_dict_get_str(member, "kind", "")
            if kind == "AnnAssign":
                target = self.any_to_dict_or_empty(member.get("target"))
                target_name = self.any_dict_get_str(target, "id", "")
                if target_name in instance_fields:
                    continue
                line = self._render_class_static_annassign(member)
                if line != "":
                    self.emit(line)
            elif kind == "Assign":
                target = self.any_to_dict_or_empty(member.get("target"))
                if len(target) == 0:
                    targets = self._dict_stmt_list(member.get("targets"))
                    if len(targets) > 0:
                        target = targets[0]
                target_name = self.any_dict_get_str(target, "id", "")
                if target_name in instance_fields:
                    continue
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
            self._emit_function(init_fn, class_name_raw)
        elif len(field_types) > 0:
            args: list[str] = []
            for field_name, field_t_obj in field_types.items():
                if not isinstance(field_name, str):
                    continue
                field_cs_t = self._cs_type(self.any_to_str(field_t_obj))
                if field_cs_t == "":
                    field_cs_t = "object"
                safe_name = self._safe_name(field_name)
                args.append(field_cs_t + " " + safe_name)
            self.emit("")
            self.emit("public " + class_name + "(" + ", ".join(args) + ")")
            self.emit("{")
            self.indent += 1
            for field_name, _ in field_types.items():
                if not isinstance(field_name, str):
                    continue
                safe_name = self._safe_name(field_name)
                self.emit("this." + safe_name + " = " + safe_name + ";")
            self.indent -= 1
            self.emit("}")
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
            self._emit_function(member, class_name_raw)

        self.indent -= 1
        self.emit("}")

        self.current_class_name = prev_class
        self.current_class_field_types = prev_class_field_types
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
        prev_declared: dict[str, str] = dict(self.declared_var_types)
        prev_method_scope = self.in_method_scope
        prev_return_type = self.current_return_east_type
        self.in_method_scope = in_class is not None

        fn_name_raw = self.any_to_str(fn.get("name"))
        fn_name = self._safe_name(fn_name_raw)
        arg_order = self.any_to_str_list(fn.get("arg_order"))
        arg_types = self.any_to_dict_or_empty(fn.get("arg_types"))
        arg_defaults = self.any_to_dict_or_empty(fn.get("arg_defaults"))
        decorators = set(self.any_to_str_list(fn.get("decorators")))
        args: list[str] = []
        scope_names: set[str] = set()

        is_constructor = in_class is not None and fn_name_raw == "__init__"
        has_static_decorator = "staticmethod" in decorators or "classmethod" in decorators
        emit_static = in_class is None or has_static_decorator

        if in_class is not None:
            if has_static_decorator:
                if len(arg_order) > 0 and (arg_order[0] == "self" or arg_order[0] == "cls"):
                    arg_order = arg_order[1:]
            else:
                if len(arg_order) > 0 and arg_order[0] == "self":
                    arg_order = arg_order[1:]

        optional_default_texts: dict[str, str] = {}
        optional_allowed: dict[str, bool] = {}
        optional_suffix_ok = True
        i = len(arg_order) - 1
        while i >= 0:
            arg_name_rev = arg_order[i]
            has_default = arg_name_rev in arg_defaults
            default_text_rev = self._render_optional_default_value(arg_defaults.get(arg_name_rev)) if has_default else ""
            optional_default_texts[arg_name_rev] = default_text_rev
            if (not has_default) or default_text_rev == "":
                optional_suffix_ok = False
                optional_allowed[arg_name_rev] = False
            else:
                optional_allowed[arg_name_rev] = optional_suffix_ok
            i -= 1

        for arg_name in arg_order:
            safe = self._safe_name(arg_name)
            arg_east_t = self.any_to_str(arg_types.get(arg_name))
            arg_cs_t = self._cs_type(arg_east_t)
            if arg_cs_t == "":
                arg_cs_t = "object"
            default_text = optional_default_texts.get(arg_name, "")
            if optional_allowed.get(arg_name, False):
                args.append(arg_cs_t + " " + safe + " = " + default_text)
            else:
                args.append(arg_cs_t + " " + safe)
            scope_names.add(arg_name)
            self.declared_var_types[arg_name] = self.normalize_type_name(arg_east_t)

        if is_constructor:
            class_name = self._safe_name(in_class if in_class is not None else "")
            self.current_return_east_type = "None"
            self.emit("public " + class_name + "(" + ", ".join(args) + ")")
        else:
            ret_east = self.normalize_type_name(self.any_to_str(fn.get("return_type")))
            self.current_return_east_type = ret_east
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
        self.current_return_east_type = prev_return_type

    def emit_stmt(self, stmt: dict[str, Any]) -> None:
        """文ノードを C# へ出力する。"""
        self.emit_leading_comments(stmt)
        if self.hook_on_emit_stmt(stmt) is True:
            return
        kind = self.any_dict_get_str(stmt, "kind", "")
        if self.hook_on_emit_stmt_kind(kind, stmt) is True:
            return

        if kind == "Pass":
            self.emit(self.syntax_text("pass_stmt", ";"))
            return
        if kind == "Break":
            self.emit(self.syntax_text("break_stmt", "break;"))
            return
        if kind == "Continue":
            self.emit(self.syntax_text("continue_stmt", "continue;"))
            return
        if kind == "Expr":
            expr_d = self.any_to_dict_or_empty(stmt.get("value"))
            if self.any_dict_get_str(expr_d, "kind", "") == "Constant":
                if isinstance(expr_d.get("value"), str):
                    # Python docstring statement は C# では無意味なので除外する。
                    return
            if self.any_dict_get_str(expr_d, "kind", "") == "Name":
                expr_name = self.any_dict_get_str(expr_d, "id", "")
                if expr_name == "break":
                    self.emit(self.syntax_text("break_stmt", "break;"))
                    return
                if expr_name == "continue":
                    self.emit(self.syntax_text("continue_stmt", "continue;"))
                    return
                if expr_name == "pass":
                    self.emit(self.syntax_text("pass_stmt", ";"))
                    return
            expr_txt = self.render_expr(stmt.get("value"))
            self.emit(self.syntax_line("expr_stmt", "{expr};", {"expr": expr_txt}))
            return
        if kind == "Return":
            if stmt.get("value") is None:
                self.emit(self.syntax_text("return_void", "return;"))
            else:
                value = self._render_expr_with_type_hint(stmt.get("value"), self.current_return_east_type)
                self.emit(self.syntax_line("return_value", "return {value};", {"value": value}))
            return
        if kind == "Raise":
            exc = stmt.get("exc")
            if exc is None:
                self.emit("throw new System.Exception(\"raise\");")
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
        if kind == "ForCore":
            self._emit_for_core(stmt)
            return
        if kind == "Import" or kind == "ImportFrom":
            return

        raise RuntimeError("csharp emitter: unsupported stmt kind: " + kind)

    def _emit_try(self, stmt: dict[str, Any]) -> None:
        """Try/Except/Finally を C# の try/catch/finally へ変換する。"""
        self.emit("try")
        self.emit("{")
        self.emit_scoped_stmt_list(self._dict_stmt_list(stmt.get("body")), set())
        handlers = self._dict_stmt_list(stmt.get("handlers"))
        finalbody = self._dict_stmt_list(stmt.get("finalbody"))
        if len(handlers) > 0:
            base_ex = "ex"
            self.emit("} catch (System.Exception " + base_ex + ") {")
            if len(handlers) == 1:
                first = handlers[0]
                alias_raw = self.any_to_str(first.get("name"))
                alias = self._safe_name(alias_raw) if alias_raw != "" else base_ex
                local_set = {base_ex}
                if alias != base_ex:
                    self.emit("System.Exception " + alias + " = " + base_ex + ";")
                    local_set.add(alias)
                self.emit_scoped_stmt_list(self._dict_stmt_list(first.get("body")), local_set)
            else:
                i = 0
                while i < len(handlers):
                    handler = handlers[i]
                    cond = self._render_except_match_cond(handler.get("type"), base_ex)
                    if i == 0:
                        self.emit("if (" + cond + ") {")
                    else:
                        self.emit("} else if (" + cond + ") {")
                    alias_raw = self.any_to_str(handler.get("name"))
                    alias = self._safe_name(alias_raw) if alias_raw != "" else base_ex
                    local_set = {base_ex}
                    if alias != base_ex:
                        self.emit("System.Exception " + alias + " = " + base_ex + ";")
                        local_set.add(alias)
                    self.emit_scoped_stmt_list(self._dict_stmt_list(handler.get("body")), local_set)
                    i += 1
                self.emit("} else {")
                self.emit("throw;")
                self.emit("}")
        if len(finalbody) > 0:
            self.emit("} finally {")
            self.emit_scoped_stmt_list(finalbody, set())
        self.emit("}")

    def _render_except_match_cond(self, type_node: Any, ex_name: str) -> str:
        """except 型注釈を C# 条件式へ変換する（fail-closed で broad catch）。"""
        t = self.any_to_dict_or_empty(type_node)
        kind = self._node_kind_from_dict(t)
        if kind == "":
            return "true"
        if kind == "Name":
            nm = self.any_dict_get_str(t, "id", "")
            if nm in {"", "Exception", "BaseException", "RuntimeError", "ValueError", "TypeError", "KeyError", "IndexError", "AssertionError"}:
                return "true"
            return ex_name + " is " + self._safe_name(nm)
        if kind == "Tuple":
            elems_any = t.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            parts: list[str] = []
            for elem in elems:
                parts.append(self._render_except_match_cond(elem, ex_name))
            if len(parts) == 0:
                return "true"
            if len(parts) == 1:
                return parts[0]
            return "(" + " || ".join(parts) + ")"
        return "true"

    def _emit_if(self, stmt: dict[str, Any]) -> None:
        cond = self.render_cond(stmt.get("test"))
        self.emit_if_stmt_skeleton(
            cond,
            self._dict_stmt_list(stmt.get("body")),
            self._dict_stmt_list(stmt.get("orelse")),
            "if ({cond}) {",
            "} else {",
        )

    def _emit_while(self, stmt: dict[str, Any]) -> None:
        cond = self.render_cond(stmt.get("test"))
        self.emit_while_stmt_skeleton(
            cond,
            self._dict_stmt_list(stmt.get("body")),
            "while ({cond}) {",
        )

    def _emit_for_range(self, stmt: dict[str, Any]) -> None:
        target_node = self.any_to_dict_or_empty(stmt.get("target"))
        target_name = self.any_dict_get_str(target_node, "id", "_i")
        target = self._safe_name(target_name)
        target_type = self._cs_type(self.any_to_str(stmt.get("target_type")))
        if target_type == "" or target_type == "object":
            target_type = "long"
        start = self.render_expr(stmt.get("start"))
        stop = self.render_expr(stmt.get("stop"))
        step = self.render_expr(stmt.get("step"))
        range_mode = self.any_to_str(stmt.get("range_mode"))
        cond = target + " < " + stop
        if range_mode == "descending":
            cond = target + " > " + stop
        body = self._dict_stmt_list(stmt.get("body"))
        if not self.is_declared(target_name):
            self.declare_in_current_scope(target_name)
            self.declared_var_types[target_name] = self.normalize_type_name(self.any_to_str(stmt.get("target_type")))
            self.emit(target_type + " " + target + " = " + start + ";")
        self.emit_scoped_block("for (" + target + " = " + start + "; " + cond + "; " + target + " += " + step + ") {", body, set())

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
        if iter_type == "str":
            iter_expr = "(" + iter_expr + ").Select(__ch => __ch.ToString())"
        if iter_type in {"", "unknown", "Any", "any", "object"} and not self._iter_is_dict_items(iter_node):
            iter_expr = "((System.Collections.IEnumerable)(" + iter_expr + "))"

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
        self.emit_scoped_block(
            self.syntax_line("for_open", "foreach (var {target} in {iter}) {", {"target": target, "iter": iter_expr}),
            body,
            {target_raw},
        )

    def _legacy_target_from_for_core_plan(self, plan_node: Any) -> dict[str, Any]:
        """ForCore target_plan を既存 For/ForRange target 形へ変換する。"""
        plan = self.any_to_dict_or_empty(plan_node)
        kind = self.any_dict_get_str(plan, "kind", "")
        if kind == "NameTarget":
            return {"kind": "Name", "id": self.any_dict_get_str(plan, "id", "_")}
        if kind == "TupleTarget":
            elements = self.any_to_list(plan.get("elements"))
            legacy_elements: list[dict[str, Any]] = []
            for elem in elements:
                legacy_elements.append(self._legacy_target_from_for_core_plan(elem))
            return {"kind": "Tuple", "elements": legacy_elements}
        if kind == "ExprTarget":
            target_any = plan.get("target")
            if isinstance(target_any, dict):
                return target_any
        return {"kind": "Name", "id": "_"}

    def _emit_for_core(self, stmt: dict[str, Any]) -> None:
        """ForCore を既存 For/ForRange emit へ内部変換して処理する。"""
        iter_plan = self.any_to_dict_or_empty(stmt.get("iter_plan"))
        target_plan = self.any_to_dict_or_empty(stmt.get("target_plan"))
        plan_kind = self.any_dict_get_str(iter_plan, "kind", "")
        target = self._legacy_target_from_for_core_plan(target_plan)
        target_type = self.any_dict_get_str(target_plan, "target_type", "")
        body = self._dict_stmt_list(stmt.get("body"))
        orelse = self._dict_stmt_list(stmt.get("orelse"))
        if plan_kind == "StaticRangeForPlan":
            self._emit_for_range(
                {
                    "kind": "ForRange",
                    "target": target,
                    "target_type": target_type,
                    "start": iter_plan.get("start"),
                    "stop": iter_plan.get("stop"),
                    "step": iter_plan.get("step"),
                    "range_mode": self.any_dict_get_str(iter_plan, "range_mode", "ascending"),
                    "body": body,
                    "orelse": orelse,
                }
            )
            return
        if plan_kind == "RuntimeIterForPlan":
            self._emit_for(
                {
                    "kind": "For",
                    "target": target,
                    "target_type": target_type,
                    "iter_mode": "runtime_protocol",
                    "iter": iter_plan.get("iter_expr"),
                    "body": body,
                    "orelse": orelse,
                }
            )
            return
        raise RuntimeError("csharp emitter: unsupported ForCore iter_plan: " + plan_kind)

    def _emit_annassign(self, stmt: dict[str, Any]) -> None:
        target = self.any_to_dict_or_empty(stmt.get("target"))
        target_kind = self.any_dict_get_str(target, "kind", "")
        ann = self.any_to_str(stmt.get("annotation"))
        decl = self.any_to_str(stmt.get("decl_type"))
        t_hint = ann
        if t_hint == "":
            t_hint = decl
        value_obj = stmt.get("value")
        if target_kind != "Name":
            if target_kind == "Attribute" and self.in_method_scope and t_hint != "":
                owner_node = self.any_to_dict_or_empty(target.get("value"))
                owner_kind = self.any_dict_get_str(owner_node, "kind", "")
                owner_name = self.any_dict_get_str(owner_node, "id", "")
                attr_name = self.any_dict_get_str(target, "attr", "")
                if owner_kind == "Name" and owner_name == "self" and attr_name != "":
                    self.current_class_field_types[attr_name] = self.normalize_type_name(t_hint)
            if value_obj is None:
                return
            t = self.render_expr(target)
            if t_hint != "":
                v = self._render_expr_with_type_hint(value_obj, t_hint)
            else:
                v = self.render_expr(value_obj)
            self.emit(self.syntax_line("annassign_assign", "{target} = {value};", {"target": t, "value": v}))
            return

        name_raw = self.any_dict_get_str(target, "id", "_")
        name = self._safe_name(name_raw)
        t_east = t_hint
        if t_east == "":
            t_east = self.get_expr_type(value_obj)
        t_cs = self._cs_type(t_east)
        use_var_decl = t_cs.startswith("(")
        if self.should_declare_name_binding(stmt, name_raw, True):
            self.declare_in_current_scope(name_raw)
            self.declared_var_types[name_raw] = self.normalize_type_name(t_east)
            if value_obj is None:
                if use_var_decl or t_cs == "" or t_cs == "object":
                    self.emit("object " + name + ";")
                else:
                    self.emit(t_cs + " " + name + ";")
            else:
                value = self._render_expr_with_type_hint(value_obj, t_east)
                if use_var_decl or t_cs == "" or t_cs == "object":
                    if value == "null":
                        self.emit("object " + name + " = null;")
                    else:
                        self.emit("var " + name + " = " + value + ";")
                else:
                    self.emit(t_cs + " " + name + " = " + value + ";")
            return

        if value_obj is not None:
            self.emit(name + " = " + self._render_expr_with_type_hint(value_obj, self.declared_var_types.get(name_raw, t_east)) + ";")

    def _emit_assign(self, stmt: dict[str, Any]) -> None:
        target = self.primary_assign_target(stmt)
        value_obj = stmt.get("value")
        target_kind = self.any_dict_get_str(target, "kind", "")

        if target_kind == "Name":
            name_raw = self.any_dict_get_str(target, "id", "_")
            name = self._safe_name(name_raw)
            if self.should_declare_name_binding(stmt, name_raw, False):
                self.declare_in_current_scope(name_raw)
                t_east = self.get_expr_type(value_obj)
                if t_east != "":
                    self.declared_var_types[name_raw] = t_east
                t_cs = self._cs_type(t_east)
                init_value = self._render_expr_with_type_hint(value_obj, t_east)
                if t_cs.startswith("(") or t_cs == "" or t_cs == "object":
                    if init_value == "null":
                        self.emit("object " + name + " = null;")
                    else:
                        self.emit("var " + name + " = " + init_value + ";")
                else:
                    self.emit(t_cs + " " + name + " = " + init_value + ";")
                return
            assigned_value = self.render_expr(value_obj)
            self.emit(name + " = " + assigned_value + ";")
            return

        if target_kind == "Tuple":
            items = self.tuple_elements(target)
            if len(items) == 0:
                return
            tuple_value = self.render_expr(value_obj)
            tmp_name = self.next_tmp("__tmp")
            self.emit("var " + tmp_name + " = " + tuple_value + ";")
            tuple_arity = self._tuple_arity_from_type_name(self.get_expr_type(value_obj))
            use_indexed_access = len(items) > 7 or tuple_arity == 1 or tuple_arity > 7
            i = 0
            while i < len(items):
                item_node = self.any_to_dict_or_empty(items[i])
                item_kind = self.any_dict_get_str(item_node, "kind", "")
                item_expr = ""
                if use_indexed_access:
                    item_expr = tmp_name + "[" + str(i) + "]"
                else:
                    item_expr = tmp_name + ".Item" + str(i + 1)
                if item_kind == "Name":
                    raw = self.any_dict_get_str(item_node, "id", "")
                    if raw != "":
                        safe = self._safe_name(raw)
                        if not self.is_declared(raw):
                            self.declare_in_current_scope(raw)
                            self.emit("var " + safe + " = " + item_expr + ";")
                        else:
                            self.emit(safe + " = " + item_expr + ";")
                elif item_kind == "Subscript":
                    owner_node = self.any_to_dict_or_empty(item_node.get("value"))
                    owner_type = self.get_expr_type(owner_node)
                    owner_expr = self.render_expr(owner_node)
                    idx_expr = self.render_expr(item_node.get("slice"))
                    if owner_type.startswith("list[") or owner_type in {"bytes", "bytearray"}:
                        self.emit("Pytra.CsModule.py_runtime.py_set(" + owner_expr + ", " + idx_expr + ", " + item_expr + ");")
                    elif owner_type.startswith("dict["):
                        self.emit(owner_expr + "[" + idx_expr + "] = " + item_expr + ";")
                    else:
                        self.emit(owner_expr + "[System.Convert.ToInt32(" + idx_expr + ")] = " + item_expr + ";")
                else:
                    self.emit(self.render_expr(item_node) + " = " + item_expr + ";")
                i += 1
            return

        if target_kind == "Attribute":
            owner_node = self.any_to_dict_or_empty(target.get("value"))
            owner_kind = self.any_dict_get_str(owner_node, "kind", "")
            owner_name = self.any_dict_get_str(owner_node, "id", "")
            attr_name = self.any_dict_get_str(target, "attr", "")
            if owner_kind == "Name" and owner_name == "self" and self.in_method_scope and attr_name != "":
                hint_t = self.current_class_field_types.get(attr_name, "")
                if hint_t != "":
                    hinted_value = self._render_expr_with_type_hint(value_obj, hint_t)
                    self.emit(self.render_expr(target) + " = " + hinted_value + ";")
                    return

        if target_kind == "Subscript":
            owner_node = self.any_to_dict_or_empty(target.get("value"))
            owner_type = self.get_expr_type(owner_node)
            if owner_type.startswith("list[") or owner_type in {"bytes", "bytearray"}:
                owner = self.render_expr(owner_node)
                idx = self.render_expr(target.get("slice"))
                sub_value = self.render_expr(value_obj)
                self.emit("Pytra.CsModule.py_runtime.py_set(" + owner + ", " + idx + ", " + sub_value + ");")
                return

        rhs_value = self.render_expr(value_obj)
        self.emit(self.render_expr(target) + " = " + rhs_value + ";")

    def _emit_augassign(self, stmt: dict[str, Any]) -> None:
        target, value, mapped = self.render_augassign_basic(stmt, self.aug_ops, "+=")
        self.emit(self.syntax_line("augassign_apply", "{target} {op} {value};", {"target": target, "op": mapped, "value": value}))

    def _render_compare(self, expr: dict[str, Any]) -> str:
        left_node = self.any_to_dict_or_empty(expr.get("left"))
        left = self.render_expr(left_node)
        ops = self.any_to_str_list(expr.get("ops"))
        comps = self.any_to_list(expr.get("comparators"))
        pair_count = len(ops)
        if len(comps) < pair_count:
            pair_count = len(comps)
        if pair_count == 0:
            return "false"

        terms: list[str] = []
        cur_left = left
        i = 0
        while i < pair_count:
            op = ops[i]
            right_node = self.any_to_dict_or_empty(comps[i])
            right = self.render_expr(right_node)
            right_t = self.get_expr_type(right_node)
            term = ""
            if op == "In" or op == "NotIn":
                if right_t.startswith("dict["):
                    term = "(" + right + ").ContainsKey(" + cur_left + ")"
                elif right_t.startswith("list[") or right_t.startswith("set[") or right_t in {"bytes", "bytearray", "str"}:
                    term = "(" + right + ").Contains(" + cur_left + ")"
                else:
                    term = "(" + right + ").Contains(" + cur_left + ")"
                if op == "NotIn":
                    term = "!(" + term + ")"
            else:
                mapped = self.cmp_ops.get(op, "==")
                term = cur_left + " " + mapped + " " + right
            terms.append(term)
            cur_left = right
            i += 1

        if len(terms) == 1:
            return terms[0]
        return " && ".join(terms)

    def _render_len_call(self, arg_expr: str, arg_node: Any) -> str:
        """len(x) を C# 式へ変換する。"""
        t = self.get_expr_type(arg_node)
        if t == "str":
            return "(" + arg_expr + ").Length"
        if t.startswith("list[") or t.startswith("dict[") or t.startswith("set[") or t in {"bytes", "bytearray"}:
            return "(" + arg_expr + ").Count"
        return "(" + arg_expr + ").Count()"

    def _render_ifexp_expr(self, expr: dict[str, Any]) -> str:
        """IfExp（三項演算）で test を Python truthy 条件へ寄せる。"""
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
        test_expr = self.render_cond(expr.get("test"))
        return self.render_ifexp_common(test_expr, body, orelse)

    def _type_id_expr_for_name(self, type_name: str) -> str:
        t = self.normalize_type_name(type_name)
        builtin_map = {
            "bool": "Pytra.CsModule.py_runtime.PYTRA_TID_BOOL",
            "int": "Pytra.CsModule.py_runtime.PYTRA_TID_INT",
            "int8": "Pytra.CsModule.py_runtime.PYTRA_TID_INT",
            "uint8": "Pytra.CsModule.py_runtime.PYTRA_TID_INT",
            "int16": "Pytra.CsModule.py_runtime.PYTRA_TID_INT",
            "uint16": "Pytra.CsModule.py_runtime.PYTRA_TID_INT",
            "int32": "Pytra.CsModule.py_runtime.PYTRA_TID_INT",
            "uint32": "Pytra.CsModule.py_runtime.PYTRA_TID_INT",
            "int64": "Pytra.CsModule.py_runtime.PYTRA_TID_INT",
            "uint64": "Pytra.CsModule.py_runtime.PYTRA_TID_INT",
            "float": "Pytra.CsModule.py_runtime.PYTRA_TID_FLOAT",
            "float32": "Pytra.CsModule.py_runtime.PYTRA_TID_FLOAT",
            "float64": "Pytra.CsModule.py_runtime.PYTRA_TID_FLOAT",
            "str": "Pytra.CsModule.py_runtime.PYTRA_TID_STR",
            "list": "Pytra.CsModule.py_runtime.PYTRA_TID_LIST",
            "dict": "Pytra.CsModule.py_runtime.PYTRA_TID_DICT",
            "set": "Pytra.CsModule.py_runtime.PYTRA_TID_SET",
            "object": "Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT",
            "None": "Pytra.CsModule.py_runtime.PYTRA_TID_NONE",
        }
        if t.startswith("list[") or t == "bytes" or t == "bytearray":
            return "Pytra.CsModule.py_runtime.PYTRA_TID_LIST"
        if t.startswith("dict["):
            return "Pytra.CsModule.py_runtime.PYTRA_TID_DICT"
        if t.startswith("set["):
            return "Pytra.CsModule.py_runtime.PYTRA_TID_SET"
        if t in builtin_map:
            return builtin_map[t]
        if t in self.class_names:
            return self._safe_name(t) + ".PYTRA_TYPE_ID"
        return ""

    def _render_isinstance_type_check(self, value_expr: str, type_name: str) -> str:
        """`isinstance(x, T)` の `T` を C# runtime API 判定式へ変換する。"""
        expected_type_id = self._type_id_expr_for_name(type_name)
        if expected_type_id != "":
            return "Pytra.CsModule.py_runtime.py_isinstance(" + value_expr + ", " + expected_type_id + ")"
        return ""

    def _render_isinstance_call(self, rendered_args: list[str], arg_nodes: list[Any]) -> str:
        """`isinstance(...)` 呼び出しを C# へ lower する。"""
        if len(rendered_args) != 2:
            return "false"
        rhs_node = self.any_to_dict_or_empty(arg_nodes[1] if len(arg_nodes) > 1 else None)
        rhs_kind = self.any_dict_get_str(rhs_node, "kind", "")
        if rhs_kind == "Name":
            rhs_name = self.any_dict_get_str(rhs_node, "id", "")
            lowered = self._render_isinstance_type_check(rendered_args[0], rhs_name)
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
                lowered = self._render_isinstance_type_check(rendered_args[0], e_name)
                if lowered != "":
                    checks.append(lowered)
            if len(checks) > 0:
                return " || ".join(checks)
        return "false"

    def _render_type_id_expr(self, expr_node: Any) -> str:
        """type_id 式を C# runtime 互換の識別子へ変換する。"""
        expr_d = self.any_to_dict_or_empty(expr_node)
        if self.any_dict_get_str(expr_d, "kind", "") == "Name":
            name = self.any_dict_get_str(expr_d, "id", "")
            if name.startswith("PYTRA_TID_"):
                return "Pytra.CsModule.py_runtime." + name
            mapped = self._type_id_expr_for_name(name)
            if mapped != "":
                return mapped
        return self.render_expr(expr_node)

    def _render_name_call(self, fn_name_raw: str, rendered_args: list[str], arg_nodes: list[Any]) -> str:
        """組み込み関数呼び出しを C# 式へ変換する。"""
        fn_name = self._safe_name(fn_name_raw)
        if fn_name_raw == "main" and "__pytra_main" in self.top_function_names and "main" not in self.top_function_names:
            fn_name = "__pytra_main"
        if fn_name_raw in self.class_names:
            return "new " + self._safe_name(fn_name_raw) + "(" + ", ".join(rendered_args) + ")"
        if fn_name_raw == "Path":
            if len(rendered_args) == 0:
                return "new Path(\"\")"
            return "new Path(" + ", ".join(rendered_args) + ")"
        if fn_name_raw == "isinstance":
            return self._render_isinstance_call(rendered_args, arg_nodes)
        if fn_name_raw == "perf_counter":
            return "Pytra.CsModule.time.perf_counter()"
        if fn_name_raw == "print":
            if len(rendered_args) == 0:
                return "System.Console.WriteLine()"
            if len(rendered_args) == 1:
                return "System.Console.WriteLine(" + rendered_args[0] + ")"
            return "System.Console.WriteLine(string.Join(\" \", new object[] { " + ", ".join(rendered_args) + " }))"
        if fn_name_raw == "len" and len(rendered_args) == 1:
            return self._render_len_call(rendered_args[0], arg_nodes[0] if len(arg_nodes) > 0 else None)
        if fn_name_raw == "ord" and len(rendered_args) == 1:
            return "Pytra.CsModule.py_runtime.py_ord(" + rendered_args[0] + ")"
        if fn_name_raw == "chr" and len(rendered_args) == 1:
            return "System.Convert.ToString(System.Convert.ToChar(System.Convert.ToInt32(" + rendered_args[0] + ")))"
        if fn_name_raw == "str" and len(rendered_args) == 1:
            return "System.Convert.ToString(" + rendered_args[0] + ")"
        if fn_name_raw == "int" and len(rendered_args) == 1:
            return "Pytra.CsModule.py_runtime.py_int(" + rendered_args[0] + ")"
        if fn_name_raw == "float" and len(rendered_args) == 1:
            return "System.Convert.ToDouble(" + rendered_args[0] + ")"
        if fn_name_raw == "bool" and len(rendered_args) == 1:
            return "Pytra.CsModule.py_runtime.py_bool(" + rendered_args[0] + ")"
        if fn_name_raw == "list":
            if len(rendered_args) == 0:
                return "new System.Collections.Generic.List<object>()"
            return "new System.Collections.Generic.List<object>(" + rendered_args[0] + ")"
        if fn_name_raw == "sorted":
            src = rendered_args[0] if len(rendered_args) > 0 else "new System.Collections.Generic.List<object>()"
            return "System.Linq.Enumerable.OrderBy(" + src + ", __x => System.Convert.ToString(__x)).ToList()"
        if fn_name_raw == "set":
            if len(rendered_args) == 0:
                return "new System.Collections.Generic.HashSet<object>()"
            return "new System.Collections.Generic.HashSet<object>(" + rendered_args[0] + ")"
        if fn_name_raw == "dict":
            if len(rendered_args) == 0:
                return "new System.Collections.Generic.Dictionary<object, object>()"
            self.needs_dict_str_object_helper = True
            return "Program.PytraDictStringObjectFromAny(" + rendered_args[0] + ")"
        if fn_name_raw == "callable" and len(rendered_args) == 1:
            return "(" + rendered_args[0] + " is System.Delegate)"
        if fn_name_raw == "globals" and len(rendered_args) == 0:
            return "new System.Collections.Generic.Dictionary<object, object>()"
        if fn_name_raw == "max" and len(rendered_args) >= 1:
            out_expr = rendered_args[0]
            i = 1
            while i < len(rendered_args):
                out_expr = "System.Math.Max(" + out_expr + ", " + rendered_args[i] + ")"
                i += 1
            return out_expr
        if fn_name_raw == "min" and len(rendered_args) >= 1:
            out_expr = rendered_args[0]
            i = 1
            while i < len(rendered_args):
                out_expr = "System.Math.Min(" + out_expr + ", " + rendered_args[i] + ")"
                i += 1
            return out_expr
        if fn_name_raw == "bytearray":
            if len(rendered_args) == 0:
                return "new System.Collections.Generic.List<byte>()"
            return "Pytra.CsModule.py_runtime.py_bytearray(" + rendered_args[0] + ")"
        if fn_name_raw == "bytes":
            if len(rendered_args) == 0:
                return "new System.Collections.Generic.List<byte>()"
            return "Pytra.CsModule.py_runtime.py_bytes(" + rendered_args[0] + ")"
        if fn_name_raw in {"Exception", "RuntimeError", "ValueError", "TypeError", "KeyError", "IndexError"}:
            if len(rendered_args) >= 1:
                return "new System.Exception(" + rendered_args[0] + ")"
            return "new System.Exception(" + self.quote_string_literal(fn_name_raw) + ")"
        if fn_name_raw == "save_gif":
            return "Pytra.CsModule.gif_helper.save_gif(" + ", ".join(rendered_args) + ")"
        if fn_name_raw == "grayscale_palette":
            return "Pytra.CsModule.gif_helper.grayscale_palette(" + ", ".join(rendered_args) + ")"
        if fn_name_raw == "write_rgb_png":
            return "Pytra.CsModule.png_helper.write_rgb_png(" + ", ".join(rendered_args) + ")"
        if fn_name_raw == "enumerate":
            self.needs_enumerate_helper = True
            src_expr = rendered_args[0] if len(rendered_args) > 0 else "new System.Collections.Generic.List<object>()"
            src_node = arg_nodes[0] if len(arg_nodes) > 0 else None
            if self.get_expr_type(src_node) == "str":
                src_expr = "(" + src_expr + ").Select(__ch => __ch.ToString())"
            if len(rendered_args) == 1:
                return "Program.PytraEnumerate(" + src_expr + ")"
            if len(rendered_args) >= 2:
                return "Program.PytraEnumerate(" + src_expr + ", " + rendered_args[1] + ")"
        return fn_name + "(" + ", ".join(rendered_args) + ")"

    def _render_attr_call(self, owner_node: dict[str, Any], attr_raw: str, rendered_args: list[str]) -> str:
        """属性呼び出しを C# 式へ変換する。"""
        owner_kind = self.any_dict_get_str(owner_node, "kind", "")
        owner_name = ""
        if owner_kind == "Name":
            owner_name = self.any_dict_get_str(owner_node, "id", "")
        if owner_name == "math":
            return "Pytra.CsModule.math." + self._safe_name(attr_raw) + "(" + ", ".join(rendered_args) + ")"
        if owner_name == "png":
            return "Pytra.CsModule.png_helper." + self._safe_name(attr_raw) + "(" + ", ".join(rendered_args) + ")"
        if owner_name == "gif":
            return "Pytra.CsModule.gif_helper." + self._safe_name(attr_raw) + "(" + ", ".join(rendered_args) + ")"
        if owner_name == "time":
            return "Pytra.CsModule.time." + self._safe_name(attr_raw) + "(" + ", ".join(rendered_args) + ")"
        if owner_name == "json":
            if attr_raw == "loads" and len(rendered_args) >= 1:
                return "new System.Collections.Generic.Dictionary<string, object>()"
            if attr_raw == "dumps" and len(rendered_args) >= 1:
                return "\"\""
        if owner_name == "sys" and attr_raw == "exit":
            if len(rendered_args) >= 1:
                return "System.Environment.Exit(System.Convert.ToInt32(" + rendered_args[0] + "))"
            return "System.Environment.Exit(0)"

        owner_expr = self.render_expr(owner_node)
        owner_type = self.get_expr_type(owner_node)

        if owner_type == "str":
            if attr_raw == "join" and len(rendered_args) == 1:
                return "string.Join(" + owner_expr + ", " + rendered_args[0] + ")"
            if attr_raw == "isdigit" and len(rendered_args) == 0:
                return "Pytra.CsModule.py_runtime.py_isdigit(" + owner_expr + ")"
            if attr_raw == "isalpha" and len(rendered_args) == 0:
                return "Pytra.CsModule.py_runtime.py_isalpha(" + owner_expr + ")"
            if attr_raw == "endswith" and len(rendered_args) == 1:
                return owner_expr + ".EndsWith(" + rendered_args[0] + ")"
            if attr_raw == "startswith" and len(rendered_args) == 1:
                return owner_expr + ".StartsWith(" + rendered_args[0] + ")"

        if attr_raw in {"strip", "lstrip", "splitlines", "split", "replace", "find", "rfind"}:
            str_owner = owner_expr
            if owner_type != "str":
                str_owner = "System.Convert.ToString(" + owner_expr + ")"
            if attr_raw == "strip" and len(rendered_args) == 0:
                return str_owner + ".Trim()"
            if attr_raw == "strip" and len(rendered_args) == 1:
                chars = "System.Convert.ToString(" + rendered_args[0] + ")"
                return str_owner + ".Trim(" + chars + ".ToCharArray())"
            if attr_raw == "lstrip" and len(rendered_args) == 0:
                return str_owner + ".TrimStart()"
            if attr_raw == "lstrip" and len(rendered_args) == 1:
                chars = "System.Convert.ToString(" + rendered_args[0] + ")"
                return str_owner + ".TrimStart(" + chars + ".ToCharArray())"
            if attr_raw == "splitlines":
                return (
                    "new System.Collections.Generic.List<string>("
                    + str_owner
                    + ".Split(new string[] { \"\\r\\n\", \"\\n\" }, System.StringSplitOptions.None))"
                )
            if attr_raw == "split" and len(rendered_args) == 0:
                return (
                    "new System.Collections.Generic.List<string>("
                    + str_owner
                    + ".Split((char[])null, System.StringSplitOptions.RemoveEmptyEntries))"
                )
            if attr_raw == "split" and len(rendered_args) >= 1:
                sep = "System.Convert.ToString(" + rendered_args[0] + ")"
                return (
                    "new System.Collections.Generic.List<string>("
                    + str_owner
                    + ".Split(new string[] { "
                    + sep
                    + " }, System.StringSplitOptions.None))"
                )
            if attr_raw == "replace" and len(rendered_args) >= 2:
                return str_owner + ".Replace(" + rendered_args[0] + ", " + rendered_args[1] + ")"
            if attr_raw == "find" and len(rendered_args) == 1:
                return str_owner + ".IndexOf(" + rendered_args[0] + ")"
            if attr_raw == "find" and len(rendered_args) >= 2:
                return str_owner + ".IndexOf(" + rendered_args[0] + ", System.Convert.ToInt32(" + rendered_args[1] + "))"
            if attr_raw == "rfind" and len(rendered_args) == 1:
                return str_owner + ".LastIndexOf(" + rendered_args[0] + ")"
            if attr_raw == "rfind" and len(rendered_args) >= 2:
                return str_owner + ".LastIndexOf(" + rendered_args[0] + ", System.Convert.ToInt32(" + rendered_args[1] + "))"

        if owner_type.startswith("list[") or owner_type in {"bytes", "bytearray"}:
            if attr_raw == "append" and len(rendered_args) == 1:
                if owner_type in {"bytes", "bytearray"}:
                    return "Pytra.CsModule.py_runtime.py_append(" + owner_expr + ", " + rendered_args[0] + ")"
                return owner_expr + ".Add(" + rendered_args[0] + ")"
            if attr_raw == "clear" and len(rendered_args) == 0:
                return owner_expr + ".Clear()"
            if attr_raw == "pop" and len(rendered_args) == 0:
                return "Pytra.CsModule.py_runtime.py_pop(" + owner_expr + ")"
            if attr_raw == "pop" and len(rendered_args) >= 1:
                return "Pytra.CsModule.py_runtime.py_pop(" + owner_expr + ", " + rendered_args[0] + ")"

        if owner_type.startswith("set["):
            if attr_raw == "add" and len(rendered_args) == 1:
                return owner_expr + ".Add(" + rendered_args[0] + ")"
            if attr_raw == "clear" and len(rendered_args) == 0:
                return owner_expr + ".Clear()"

        if owner_type.startswith("dict["):
            if attr_raw == "get":
                key_expr = rendered_args[0] if len(rendered_args) > 0 else "\"\""
                if owner_type.startswith("dict[str"):
                    key_expr = "System.Convert.ToString(" + key_expr + ")"
                if len(rendered_args) == 1:
                    return "(" + owner_expr + ".ContainsKey(" + key_expr + ") ? " + owner_expr + "[" + key_expr + "] : default)"
                if len(rendered_args) >= 2:
                    d = rendered_args[1]
                    return "(" + owner_expr + ".ContainsKey(" + key_expr + ") ? " + owner_expr + "[" + key_expr + "] : " + d + ")"
            if attr_raw == "items" and len(rendered_args) == 0:
                return owner_expr
            if attr_raw == "keys" and len(rendered_args) == 0:
                return owner_expr + ".Keys"
            if attr_raw == "values" and len(rendered_args) == 0:
                return owner_expr + ".Values"

        if owner_type in {"", "unknown", "object"}:
            owner_dict = "((" + "System.Collections.Generic.Dictionary<string, object>)" + owner_expr + ")"
            if attr_raw == "get":
                if len(rendered_args) == 1:
                    k = "System.Convert.ToString(" + rendered_args[0] + ")"
                    return "(" + owner_dict + ".ContainsKey(" + k + ") ? " + owner_dict + "[" + k + "] : default)"
                if len(rendered_args) >= 2:
                    k = "System.Convert.ToString(" + rendered_args[0] + ")"
                    d = rendered_args[1]
                    return "(" + owner_dict + ".ContainsKey(" + k + ") ? " + owner_dict + "[" + k + "] : " + d + ")"
            if attr_raw == "items" and len(rendered_args) == 0:
                return owner_dict
            if attr_raw == "keys" and len(rendered_args) == 0:
                return owner_dict + ".Keys"
            if attr_raw == "values" and len(rendered_args) == 0:
                return owner_dict + ".Values"

        attr = self._safe_name(attr_raw)
        return owner_expr + "." + attr + "(" + ", ".join(rendered_args) + ")"

    def _render_call(self, expr: dict[str, Any]) -> str:
        parts = self.prepare_call_context(expr)
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

        hook_specific = self.hook_on_render_expr_kind_specific(kind, expr_d)
        if hook_specific != "":
            return hook_specific
        hook_leaf = self.hook_on_render_expr_leaf(kind, expr_d)
        if hook_leaf != "":
            return hook_leaf

        if kind == "Name":
            name = self.any_dict_get_str(expr_d, "id", "_")
            if name == "self" and self.in_method_scope:
                return "this"
            if name == "main" and "__pytra_main" in self.top_function_names and "main" not in self.top_function_names:
                return "__pytra_main"
            return self._safe_name(name)

        if kind == "Constant":
            tag, non_str = self.render_constant_non_string_common(expr, expr_d, "null", "null")
            if tag == "1":
                return non_str
            return self.quote_string_literal(self.any_to_str(expr_d.get("value")))

        if kind == "JoinedStr":
            values = self.any_to_list(expr_d.get("values"))
            pieces: list[str] = []
            for part in values:
                p_node = self.any_to_dict_or_empty(part)
                p_kind = self.any_dict_get_str(p_node, "kind", "")
                if p_kind == "Constant":
                    p_val = p_node.get("value")
                    if isinstance(p_val, str):
                        pieces.append(self._escape_interpolated_literal_text(p_val))
                    else:
                        pieces.append("{" + self.render_expr(part) + "}")
                    continue
                if p_kind == "FormattedValue":
                    inner = self.render_expr(p_node.get("value"))
                    pieces.append("{" + inner + "}")
                    continue
                pieces.append("{" + self.render_expr(part) + "}")
            return "$\"" + "".join(pieces) + "\""

        if kind == "Attribute":
            owner_node = self.any_to_dict_or_empty(expr_d.get("value"))
            owner_kind = self.any_dict_get_str(owner_node, "kind", "")
            owner_name = self.any_dict_get_str(owner_node, "id", "")
            attr = self._safe_name(self.any_dict_get_str(expr_d, "attr", ""))
            if owner_kind == "Name" and owner_name == "self" and self.in_method_scope:
                return "this." + attr
            if owner_kind == "Name" and owner_name == "math":
                return "Pytra.CsModule.math." + attr
            if owner_kind == "Name" and owner_name == "png":
                return "Pytra.CsModule.png_helper." + attr
            if owner_kind == "Name" and owner_name == "gif":
                return "Pytra.CsModule.gif_helper." + attr
            if owner_kind == "Name" and owner_name == "time":
                return "Pytra.CsModule.time." + attr
            owner_type = self.get_expr_type(owner_node)
            if owner_type == "Path":
                if attr == "parent":
                    return self.render_expr(owner_node) + ".parent()"
                if attr == "name":
                    return self.render_expr(owner_node) + ".name()"
                if attr == "stem":
                    return self.render_expr(owner_node) + ".stem()"
            return self.render_expr(owner_node) + "." + attr

        if kind == "UnaryOp":
            op = self.any_dict_get_str(expr_d, "op", "")
            operand_node = self.any_to_dict_or_empty(expr_d.get("operand"))
            operand = self.render_expr(operand_node)
            operand_kind = self.any_dict_get_str(operand_node, "kind", "")
            simple_operand = operand_kind in {"Name", "Constant", "Call", "Attribute", "Subscript"}
            if op == "USub":
                if simple_operand:
                    return "-" + operand
                return "-(" + operand + ")"
            if op == "Not":
                if simple_operand:
                    return "!" + operand
                return "!(" + operand + ")"
            return operand

        if kind == "BinOp":
            op = self.any_to_str(expr_d.get("op"))
            left_node = self.any_to_dict_or_empty(expr_d.get("left"))
            right_node = self.any_to_dict_or_empty(expr_d.get("right"))
            left = self._wrap_for_binop_operand(self.render_expr(left_node), left_node, op, False)
            right = self._wrap_for_binop_operand(self.render_expr(right_node), right_node, op, True)
            left_kind = self.any_dict_get_str(left_node, "kind", "")
            right_kind = self.any_dict_get_str(right_node, "kind", "")
            custom = self.hook_on_render_binop(expr_d, left, right)
            if custom != "":
                return custom
            if op == "FloorDiv":
                return "System.Convert.ToInt64(System.Math.Floor(System.Convert.ToDouble(" + left + ") / System.Convert.ToDouble(" + right + ")))"
            if op == "Mult":
                if self._is_string_expr_node(left_node):
                    return self._render_string_repeat(left, right)
                if self._is_string_expr_node(right_node):
                    return self._render_string_repeat(right, left)
                if left_kind == "List" and right_kind != "List":
                    return self._render_list_repeat(left_node, left, right)
                if right_kind == "List" and left_kind != "List":
                    return self._render_list_repeat(right_node, right, left)
            mapped = self.bin_ops.get(op, "+")
            return left + " " + mapped + " " + right

        if kind == "Compare":
            return self._render_compare(expr_d)

        if kind == "BoolOp":
            vals = self.any_to_list(expr_d.get("values"))
            op = self.any_to_str(expr_d.get("op"))
            return self.render_boolop_chain_common(
                vals,
                op,
                "&&",
                "||",
                "false",
                True,
                True,
            )

        if kind == "Call":
            hook = self.hook_on_render_call(expr_d, self.any_to_dict_or_empty(expr_d.get("func")), [], {})
            if hook != "":
                return hook
            return self._render_call(expr_d)

        if kind == "IfExp":
            return self._render_ifexp_expr(expr_d)

        if kind == "ObjBool":
            value = self.render_expr(expr_d.get("value"))
            return "Pytra.CsModule.py_runtime.py_bool(" + value + ")"

        if kind == "ObjLen":
            value_node = expr_d.get("value")
            value = self.render_expr(value_node)
            return self._render_len_call(value, value_node)

        if kind == "ObjStr":
            value = self.render_expr(expr_d.get("value"))
            return "System.Convert.ToString(" + value + ")"

        if kind == "ObjIterInit":
            value = self.render_expr(expr_d.get("value"))
            return "iter(" + value + ")"

        if kind == "ObjIterNext":
            iter_expr = self.render_expr(expr_d.get("iter"))
            return "next(" + iter_expr + ")"

        if kind == "ObjTypeId":
            value = self.render_expr(expr_d.get("value"))
            return "Pytra.CsModule.py_runtime.py_runtime_type_id(" + value + ")"

        if kind == "IsInstance":
            value = self.render_expr(expr_d.get("value"))
            expected = self._render_type_id_expr(expr_d.get("expected_type_id"))
            return "Pytra.CsModule.py_runtime.py_isinstance(" + value + ", " + expected + ")"

        if kind == "IsSubtype" or kind == "IsSubclass":
            actual = self._render_type_id_expr(expr_d.get("actual_type_id"))
            expected = self._render_type_id_expr(expr_d.get("expected_type_id"))
            return "Pytra.CsModule.py_runtime.py_is_subtype(" + actual + ", " + expected + ")"

        if kind == "Box":
            return self.render_expr(expr_d.get("value"))

        if kind == "Unbox":
            value = self.render_expr(expr_d.get("value"))
            target_t = self.normalize_type_name(self.any_to_str(expr_d.get("target")))
            if target_t == "":
                target_t = self.normalize_type_name(self.any_to_str(expr_d.get("resolved_type")))
            if target_t == "bool":
                return "Pytra.CsModule.py_runtime.py_bool(" + value + ")"
            if target_t == "str":
                return "System.Convert.ToString(" + value + ")"
            if target_t == "float" or target_t == "float32" or target_t == "float64":
                return "System.Convert.ToDouble(" + value + ")"
            if target_t == "int" or target_t == "int8" or target_t == "uint8" or target_t == "int16" or target_t == "uint16" or target_t == "int32" or target_t == "uint32" or target_t == "int64" or target_t == "uint64":
                return "System.Convert.ToInt64(" + value + ")"
            if target_t in self.class_names:
                return "((" + self._safe_name(target_t) + ")" + value + ")"
            return value

        if kind == "RangeExpr":
            return self._render_range_expr(expr_d)

        if kind == "ListComp":
            return self._render_list_comp_expr(expr_d)

        if kind == "List":
            return self._typed_list_literal(expr_d)

        if kind == "Set":
            return self._typed_set_literal(expr_d)

        if kind == "Tuple":
            elts = self.tuple_elements(expr_d)
            rendered: list[str] = []
            for elt in elts:
                rendered.append(self.render_expr(elt))
            if self._is_value_tuple_arity(len(rendered)):
                return "(" + ", ".join(rendered) + ")"
            if len(rendered) == 0:
                return "new System.Collections.Generic.List<object>()"
            return "new System.Collections.Generic.List<object> { " + ", ".join(rendered) + " }"

        if kind == "Dict":
            return self._typed_dict_literal(expr_d)

        if kind == "Subscript":
            owner_node = self.any_to_dict_or_empty(expr_d.get("value"))
            owner = self.render_expr(owner_node)
            owner_t = self.get_expr_type(owner_node)
            slice_node = self.any_to_dict_or_empty(expr_d.get("slice"))
            slice_kind = self.any_dict_get_str(slice_node, "kind", "")
            if slice_kind == "Slice":
                lower_node = slice_node.get("lower")
                upper_node = slice_node.get("upper")
                has_lower = lower_node is not None and len(self.any_to_dict_or_empty(lower_node)) > 0
                has_upper = upper_node is not None and len(self.any_to_dict_or_empty(upper_node)) > 0
                lower_expr = "null"
                upper_expr = "null"
                if has_lower:
                    lower_expr = "System.Convert.ToInt64(" + self.render_expr(lower_node) + ")"
                if has_upper:
                    upper_expr = "System.Convert.ToInt64(" + self.render_expr(upper_node) + ")"
                if owner_t.startswith("list[") or owner_t in {"bytes", "bytearray", "str"}:
                    return "Pytra.CsModule.py_runtime.py_slice(" + owner + ", " + lower_expr + ", " + upper_expr + ")"
            idx = self.render_expr(slice_node)
            if owner_t.startswith("list[") or owner_t in {"bytes", "bytearray", "str"}:
                return "Pytra.CsModule.py_runtime.py_get(" + owner + ", " + idx + ")"
            if owner_t.startswith("dict["):
                return owner + "[" + idx + "]"
            return owner + "[System.Convert.ToInt32(" + idx + ")]"

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
        return self.render_truthy_cond_common(
            expr,
            "{expr}.Length != 0",
            "{expr}.Count != 0",
            "{expr} != 0",
        )


def transpile_to_csharp(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを C# コードへ変換する。"""
    emitter = CSharpEmitter(east_doc)
    return emitter.transpile()
