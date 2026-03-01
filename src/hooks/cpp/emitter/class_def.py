from __future__ import annotations

from pytra.std.typing import Any
from pytra.compiler.transpile_cli import join_str_list, sort_str_list_copy


class CppClassEmitter:
    """Class emission helpers extracted from CppEmitter."""

    def _class_has_base_method(self, class_name: str, method: str) -> bool:
        """指定クラスの継承祖先に同名メソッドが存在するか判定する。"""
        base = self.class_base.get(class_name, "")
        while base != "":
            methods = self.class_method_names.get(base, set())
            if method in methods:
                return True
            base = self.class_base.get(base, "")
        return False

    def emit_class(self, stmt: dict[str, Any]) -> None:
        """クラス定義ノードを C++ クラス/struct として出力する。"""
        name = self.any_dict_get_str(stmt, "name", "Class")
        is_dataclass = self.any_dict_get_int(stmt, "dataclass", 0) != 0
        base = self.any_to_str(stmt.get("base"))
        if base in {"Exception", "BaseException", "RuntimeError", "ValueError", "TypeError", "IndexError", "KeyError"}:
            # Python 例外継承は runtime 側の C++ 例外階層と1対1対応しないため、
            # クラス本体（フィールド/メソッド）を優先して継承は省略する。
            base = ""
        is_enum_base = base in {"Enum", "IntEnum", "IntFlag"}
        if is_enum_base:
            cls_name = str(name)
            enum_members: list[str] = []
            enum_values: list[str] = []
            class_body = self._dict_stmt_list(stmt.get("body"))
            for s in class_body:
                sk = self._node_kind_from_dict(s)
                if sk == "Assign":
                    texpr = self.any_to_dict_or_empty(s.get("target"))
                    if self.is_name(s.get("target"), None):
                        member = self.any_to_str(texpr.get("id"))
                        if member != "":
                            enum_members.append(member)
                            enum_values.append(self.render_expr(s.get("value")))
                elif sk == "AnnAssign":
                    texpr = self.any_to_dict_or_empty(s.get("target"))
                    if self.is_name(s.get("target"), None):
                        member = self.any_to_str(texpr.get("id"))
                        if member != "":
                            val = "0"
                            if s.get("value") is not None:
                                val = self.render_expr(s.get("value"))
                            enum_members.append(member)
                            enum_values.append(val)
            self.emit(f"enum class {cls_name} : int64 {{")
            self.indent += 1
            for i, member in enumerate(enum_members):
                value_txt = enum_values[i]
                sep = "," if i + 1 < len(enum_members) else ""
                self.emit(f"{member} = {value_txt}{sep}")
            self.indent -= 1
            self.emit("};")
            self.emit("")
            if base in {"IntEnum", "IntFlag"}:
                self.emit(f"static inline int64 py_to_int64({cls_name} v) {{ return static_cast<int64>(v); }}")
                self.emit(f"static inline bool operator==({cls_name} lhs, int64 rhs) {{ return static_cast<int64>(lhs) == rhs; }}")
                self.emit(f"static inline bool operator==(int64 lhs, {cls_name} rhs) {{ return lhs == static_cast<int64>(rhs); }}")
                self.emit(f"static inline bool operator!=({cls_name} lhs, int64 rhs) {{ return !(lhs == rhs); }}")
                self.emit(f"static inline bool operator!=(int64 lhs, {cls_name} rhs) {{ return !(lhs == rhs); }}")
                if base == "IntFlag":
                    self.emit(f"static inline {cls_name} operator|({cls_name} lhs, {cls_name} rhs) {{")
                    self.indent += 1
                    self.emit(f"return static_cast<{cls_name}>(static_cast<int64>(lhs) | static_cast<int64>(rhs));")
                    self.indent -= 1
                    self.emit("}")
                    self.emit(f"static inline {cls_name} operator&({cls_name} lhs, {cls_name} rhs) {{")
                    self.indent += 1
                    self.emit(f"return static_cast<{cls_name}>(static_cast<int64>(lhs) & static_cast<int64>(rhs));")
                    self.indent -= 1
                    self.emit("}")
                    self.emit(f"static inline {cls_name} operator^({cls_name} lhs, {cls_name} rhs) {{")
                    self.indent += 1
                    self.emit(f"return static_cast<{cls_name}>(static_cast<int64>(lhs) ^ static_cast<int64>(rhs));")
                    self.indent -= 1
                    self.emit("}")
                    self.emit(f"static inline {cls_name} operator~({cls_name} v) {{")
                    self.indent += 1
                    self.emit(f"return static_cast<{cls_name}>(~static_cast<int64>(v));")
                    self.indent -= 1
                    self.emit("}")
            self.emit("")
            return
        cls_name = str(name)
        gc_managed = cls_name in self.ref_classes
        bases: list[str] = []
        if base != "" and not is_enum_base:
            bases.append(f"public {base}")
        base_is_gc = base in self.ref_classes
        if gc_managed and not base_is_gc:
            bases.append("public PyObj")
        base_txt: str = ""
        if len(bases) > 0:
            sep = ", "
            base_txt = " : " + sep.join(bases)
        self.emit_class_open(str(name), base_txt)
        self.indent += 1
        prev_class = self.current_class_name
        prev_class_base = self.current_class_base_name
        prev_fields = self.current_class_fields
        prev_static_fields = self.current_class_static_fields
        self.current_class_name = str(name)
        self.current_class_base_name = str(base) if isinstance(base, str) else ""
        self.current_class_fields.clear()
        for fk, fv in self.any_to_dict_or_empty(stmt.get("field_types")).items():
            if isinstance(fk, str):
                self.current_class_fields[fk] = self.any_to_str(fv)
        class_body = self._dict_stmt_list(stmt.get("body"))
        static_field_types: dict[str, str] = {}
        static_field_defaults: dict[str, str] = {}
        instance_field_defaults: dict[str, str] = {}
        field_decl_order: list[str] = []
        static_field_order: list[str] = []
        consumed_assign_fields: set[str] = set()
        for s in class_body:
            if self._node_kind_from_dict(s) == "AnnAssign":
                texpr = self.any_to_dict_or_empty(s.get("target"))
                if self.is_plain_name_expr(s.get("target")):
                    fname = self.any_dict_get_str(texpr, "id", "")
                    ann = self.any_to_str(s.get("annotation"))
                    if ann != "":
                        if fname != "" and fname not in field_decl_order:
                            field_decl_order.append(fname)
                        if fname != "":
                            cur_t = self.current_class_fields.get(fname, "")
                            if not isinstance(cur_t, str) or cur_t == "" or cur_t == "unknown":
                                self.current_class_fields[fname] = ann
                        if is_dataclass:
                            if self._expr_node_has_payload(s.get("value")):
                                instance_field_defaults[fname] = self.render_expr(s.get("value"))
                            else:
                                instance_field_defaults.pop(fname, None)
                        else:
                            # クラス直下 `AnnAssign` は、値ありのみ static 扱い。
                            # 値なしはインスタンスフィールド宣言（型ヒント）として扱う。
                            if self._expr_node_has_payload(s.get("value")):
                                static_field_types[fname] = ann
                                if fname not in static_field_order:
                                    static_field_order.append(fname)
                                static_field_defaults[fname] = self.render_expr(s.get("value"))
            elif is_enum_base and self._node_kind_from_dict(s) == "Assign":
                texpr = self.any_to_dict_or_empty(s.get("target"))
                if self.is_name(s.get("target"), None):
                    fname = self.any_to_str(texpr.get("id"))
                    if fname != "":
                        inferred = self.get_expr_type(s.get("value"))
                        ann = inferred if isinstance(inferred, str) else ""
                        if ann == "" or ann == "unknown":
                            ann = "int64" if base in {"IntEnum", "IntFlag"} else "int64"
                        static_field_types[fname] = ann
                        if fname not in static_field_order:
                            static_field_order.append(fname)
                        if self._expr_node_has_payload(s.get("value")):
                            static_field_defaults[fname] = self.render_expr(s.get("value"))
                        consumed_assign_fields.add(fname)
        self.current_class_static_fields.clear()
        for k, _ in static_field_types.items():
            if isinstance(k, str) and k != "":
                self.current_class_static_fields.add(k)
        instance_fields_ordered: list[tuple[str, str]] = []
        seen_instance_fields: set[str] = set()
        for fname in field_decl_order:
            if fname in self.current_class_static_fields:
                continue
            fty_any = self.current_class_fields.get(fname, "")
            if not isinstance(fty_any, str):
                continue
            if fname in seen_instance_fields:
                continue
            instance_fields_ordered.append((fname, fty_any))
            seen_instance_fields.add(fname)
        remaining_instance_keys: list[str] = []
        for k, v in self.current_class_fields.items():
            if (
                isinstance(k, str)
                and isinstance(v, str)
                and k not in self.current_class_static_fields
                and k not in seen_instance_fields
            ):
                remaining_instance_keys.append(k)
        remaining_instance_keys = sort_str_list_copy(remaining_instance_keys)
        for fname in remaining_instance_keys:
            fty_fallback = self.current_class_fields.get(fname, "")
            if isinstance(fty_fallback, str):
                instance_fields_ordered.append((fname, fty_fallback))
                seen_instance_fields.add(fname)
        has_init = False
        for s in class_body:
            if self._node_kind_from_dict(s) == "FunctionDef" and s.get("name") == "__init__":
                has_init = True
                break
        static_emit_names: list[str] = []
        for fname in static_field_order:
            if fname in static_field_types and fname not in static_emit_names:
                static_emit_names.append(fname)
        extra_static_names: list[str] = []
        for fname, _ in static_field_types.items():
            if fname not in static_emit_names:
                extra_static_names.append(fname)
        extra_static_names = sort_str_list_copy(extra_static_names)
        for fname in extra_static_names:
            static_emit_names.append(fname)
        for fname in static_emit_names:
            fty = static_field_types.get(fname, "")
            if not isinstance(fty, str) or fty == "":
                continue
            if fname in static_field_defaults:
                self.emit(f"inline static {self._cpp_type_text(fty)} {fname} = {static_field_defaults[fname]};")
            else:
                self.emit(f"inline static {self._cpp_type_text(fty)} {fname};")
        for fname, fty in instance_fields_ordered:
            self.emit(f"{self._cpp_type_text(fty)} {fname};")
        if gc_managed:
            base_type_id_expr = f"{base}::PYTRA_TYPE_ID" if base_is_gc else "PYTRA_TID_OBJECT"
            self.emit(f"PYTRA_DECLARE_CLASS_TYPE({base_type_id_expr});")

        if len(static_emit_names) > 0 or len(instance_fields_ordered) > 0 or gc_managed:
            self.emit("")
        if (len(instance_fields_ordered) > 0 or gc_managed) and not has_init:
            params: list[str] = []
            for fname, fty in instance_fields_ordered:
                p = f"{self._cpp_type_text(fty)} {fname}"
                if fname in instance_field_defaults and instance_field_defaults[fname] != "":
                    default_expr = instance_field_defaults[fname]
                    if not self._expr_is_none_marker(default_expr):
                        p += f" = {default_expr}"
                params.append(p)
            self.emit(f"{name}({join_str_list(', ', params)}) {{")
            self.indent += 1
            self.scope_stack.append(set())
            for fname, _ in instance_fields_ordered:
                self.emit(f"this->{fname} = {fname};")
            self.scope_stack.pop()
            self.indent -= 1
            self.emit_block_close()
            self.emit("")
        for s in class_body:
            if self._node_kind_from_dict(s) == "AnnAssign":
                t = self.cpp_type(s.get("annotation"))
                target = self.render_expr(s.get("target"))
                if self.is_plain_name_expr(s.get("target")) and target in self.current_class_fields:
                    pass
                elif not self._expr_node_has_payload(s.get("value")):
                    self.emit(f"{t} {target};")
                else:
                    self.emit(f"{t} {target} = {self.render_expr(s.get('value'))};")
            elif is_enum_base and self._node_kind_from_dict(s) == "Assign":
                texpr = self.any_to_dict_or_empty(s.get("target"))
                skip_stmt = False
                if self.is_name(s.get("target"), None):
                    fname = self.any_to_str(texpr.get("id"))
                    if fname in consumed_assign_fields:
                        skip_stmt = True
                if not skip_stmt:
                    self.emit_stmt(s)
            else:
                self.emit_stmt(s)
        self.current_class_name = prev_class
        self.current_class_base_name = prev_class_base
        self.current_class_fields = prev_fields
        self.current_class_static_fields = prev_static_fields
        self.indent -= 1
        self.emit_class_close()
