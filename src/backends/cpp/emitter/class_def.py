from __future__ import annotations

from typing import Any
from toolchain.compiler.transpile_cli import join_str_list, sort_str_list_copy


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

    def _dataclass_field_v1_meta(self, stmt: dict[str, Any]) -> dict[str, Any]:
        meta = self.any_to_dict_or_empty(stmt.get("meta"))
        field_meta = self.any_to_dict_or_empty(meta.get("dataclass_field_v1"))
        if self.any_dict_get_int(field_meta, "schema_version", 0) != 1:
            return {}
        return field_meta

    def _dataclass_field_init_enabled(self, stmt: dict[str, Any]) -> bool:
        field_meta = self._dataclass_field_v1_meta(stmt)
        if "init" not in field_meta:
            return True
        return bool(field_meta.get("init"))

    def _dataclass_field_default_expr_node(self, stmt: dict[str, Any]) -> dict[str, Any]:
        field_meta = self._dataclass_field_v1_meta(stmt)
        default_expr = self.any_to_dict_or_empty(field_meta.get("default_expr"))
        if self._expr_node_has_payload(default_expr):
            return default_expr
        return self.any_to_dict_or_empty(stmt.get("value"))

    def _dataclass_field_default_factory_expr_node(self, stmt: dict[str, Any]) -> dict[str, Any]:
        field_meta = self._dataclass_field_v1_meta(stmt)
        return self.any_to_dict_or_empty(field_meta.get("default_factory_expr"))

    def _coerce_dataclass_field_default_value(self, field_type: str, value_node: Any, rendered_expr: str) -> str:
        if rendered_expr == "":
            return ""
        target_t = self.normalize_type_name(field_type)
        coerced = self._rewrite_nullopt_default_for_typed_target(rendered_expr, target_t)
        coerced = self._rewrite_empty_collection_literal_for_typed_target(coerced, value_node, target_t)
        if self._is_pyobj_ref_first_list_type(target_t):
            return self._render_pyobj_alias_list_value(coerced, value_node, target_t)
        if not self.is_any_like_type(target_t):
            return coerced
        if coerced in {"object{}", "object()"} or self.is_boxed_object_expr(coerced):
            return coerced
        return f"make_object({coerced})"

    def _render_dataclass_field_default_factory(self, field_type: str, factory_expr: dict[str, Any]) -> str:
        if not self._expr_node_has_payload(factory_expr):
            return ""
        kind = self._node_kind_from_dict(factory_expr)
        if kind == "Call":
            rendered = self.render_expr(factory_expr)
            return self._coerce_dataclass_field_default_value(field_type, factory_expr, rendered)
        if kind == "Lambda":
            if len(self._dict_stmt_list(factory_expr.get("args"))) == 0:
                body_node = factory_expr.get("body")
                rendered = self.render_expr(body_node)
                return self._coerce_dataclass_field_default_value(field_type, body_node, rendered)
        if kind == "Name":
            factory_name = self.any_dict_get_str(factory_expr, "id", "")
            if self.cpp_signature_type(field_type).startswith("rc<") and factory_name in self.ref_classes:
                return f"::rc_new<{factory_name}>()"
            if factory_name in {"list", "dict", "set", "tuple", "str", "bytes", "bytearray", "deque"}:
                if self._is_pyobj_ref_first_list_type(field_type) and factory_name == "list":
                    value_expr = self._cpp_list_value_model_type_text(field_type) + "{}"
                    return self._coerce_dataclass_field_default_value(
                        field_type,
                        {"kind": "List", "elements": [], "resolved_type": field_type},
                        value_expr,
                    )
                return self.cpp_signature_type(field_type) + "{}"
        if kind == "Attribute":
            factory_name = self.any_dict_get_str(factory_expr, "attr", "")
            if factory_name in {"list", "dict", "set", "tuple", "str", "bytes", "bytearray", "deque"}:
                if self._is_pyobj_ref_first_list_type(field_type) and factory_name == "list":
                    value_expr = self._cpp_list_value_model_type_text(field_type) + "{}"
                    return self._coerce_dataclass_field_default_value(
                        field_type,
                        {"kind": "List", "elements": [], "resolved_type": field_type},
                        value_expr,
                    )
                return self.cpp_signature_type(field_type) + "{}"
        rendered = self.render_expr(factory_expr)
        if rendered == "":
            return ""
        return self._coerce_dataclass_field_default_value(field_type, factory_expr, rendered + "()")

    def emit_class(self, stmt: dict[str, Any]) -> None:
        """クラス定義ノードを C++ クラス/struct として出力する。"""
        name = self.any_dict_get_str(stmt, "name", "Class")
        is_dataclass = self.any_dict_get_int(stmt, "dataclass", 0) != 0
        base = self.any_to_str(stmt.get("base"))
        if base in {
            "Exception",
            "BaseException",
            "RuntimeError",
            "NotImplementedError",
            "ValueError",
            "TypeError",
            "IndexError",
            "KeyError",
        }:
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
        base_cpp = base
        if base != "" and not is_enum_base:
            base_cpp = self._resolve_local_class_base_cpp_name(base)
            if base_cpp == "" or base_cpp == base:
                base_cpp = self._strip_rc_wrapper(self._cpp_type_text(base))
                if base_cpp == "":
                    base_cpp = base
        bases: list[str] = []
        if base != "" and not is_enum_base:
            bases.append(f"public {base_cpp}")
        base_is_gc = self._type_is_ref_class(base)
        if gc_managed and not base_is_gc:
            bases.append("public RcObject")
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
        self.current_class_base_name = base_cpp if isinstance(base_cpp, str) else ""
        self.current_class_fields.clear()
        for fk, fv in self.any_to_dict_or_empty(stmt.get("field_types")).items():
            if isinstance(fk, str):
                self.current_class_fields[fk] = self.any_to_str(fv)
        class_body = self._dict_stmt_list(stmt.get("body"))
        static_field_types: dict[str, str] = {}
        static_field_defaults: dict[str, str] = {}
        instance_field_defaults: dict[str, str] = {}
        instance_field_default_factories: dict[str, str] = {}
        dataclass_init_disabled_fields: set[str] = set()
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
                            if not self._dataclass_field_init_enabled(s):
                                dataclass_init_disabled_fields.add(fname)
                            else:
                                dataclass_init_disabled_fields.discard(fname)
                            default_expr_node = self._dataclass_field_default_expr_node(s)
                            if self._expr_node_has_payload(default_expr_node):
                                instance_field_defaults[fname] = self.render_expr(default_expr_node)
                            else:
                                instance_field_defaults.pop(fname, None)
                            default_factory_expr_node = self._dataclass_field_default_factory_expr_node(s)
                            default_factory_expr = self._render_dataclass_field_default_factory(ann, default_factory_expr_node)
                            if default_factory_expr != "":
                                instance_field_default_factories[fname] = default_factory_expr
                            else:
                                instance_field_default_factories.pop(fname, None)
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
            emitted_fname = self.rename_if_reserved(fname, self.reserved_words, self.rename_prefix, self.renamed_symbols)
            if fname in static_field_defaults:
                self.emit(f"inline static {self._cpp_type_text(fty)} {emitted_fname} = {static_field_defaults[fname]};")
            else:
                self.emit(f"inline static {self._cpp_type_text(fty)} {emitted_fname};")
        for fname, fty in instance_fields_ordered:
            emitted_fname = self.rename_if_reserved(fname, self.reserved_words, self.rename_prefix, self.renamed_symbols)
            self.emit(f"{self.cpp_signature_type(fty)} {emitted_fname};")
        if gc_managed:
            base_type_id_expr = f"{base_cpp}::PYTRA_TYPE_ID" if base_is_gc else "PYTRA_TID_OBJECT"
            self.emit(f"PYTRA_DECLARE_CLASS_TYPE({base_type_id_expr});")

        if len(static_emit_names) > 0 or len(instance_fields_ordered) > 0 or gc_managed:
            self.emit("")
        if (len(instance_fields_ordered) > 0 or gc_managed) and not has_init:
            params: list[str] = []
            for fname, fty in instance_fields_ordered:
                if fname in dataclass_init_disabled_fields:
                    continue
                emitted_fname = self.rename_if_reserved(fname, self.reserved_words, self.rename_prefix, self.renamed_symbols)
                p = f"{self.cpp_signature_type(fty)} {emitted_fname}"
                default_expr = instance_field_defaults.get(fname, "")
                if default_expr == "":
                    default_expr = instance_field_default_factories.get(fname, "")
                if default_expr != "":
                    if not self._expr_is_none_marker(default_expr):
                        p += f" = {default_expr}"
                params.append(p)
            init_items: list[str] = []
            for fname, _ in instance_fields_ordered:
                emitted_fname = self.rename_if_reserved(fname, self.reserved_words, self.rename_prefix, self.renamed_symbols)
                if fname in dataclass_init_disabled_fields:
                    init_expr = instance_field_defaults.get(fname, "")
                    if init_expr == "" or self._expr_is_none_marker(init_expr):
                        init_expr = instance_field_default_factories.get(fname, "")
                    if init_expr != "":
                        init_items.append(f"{emitted_fname}({init_expr})")
                    continue
                init_items.append(f"{emitted_fname}({emitted_fname})")
            init_txt = join_str_list(", ", init_items)
            if init_txt != "":
                self.emit(f"{name}({join_str_list(', ', params)}) : {init_txt} {{")
            else:
                self.emit(f"{name}({join_str_list(', ', params)}) {{")
            self.emit("}")
            self.emit("")
        for s in class_body:
            if self._node_kind_from_dict(s) == "AnnAssign":
                t = self.cpp_type(s.get("annotation"))
                target_node = self.any_to_dict_or_empty(s.get("target"))
                target_name = self.any_dict_get_str(target_node, "id", "")
                target = self.render_expr(s.get("target"))
                if self.is_plain_name_expr(s.get("target")) and target_name in self.current_class_fields:
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
