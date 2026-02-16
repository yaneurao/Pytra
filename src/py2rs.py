#!/usr/bin/env python3
# Python -> Rust の変換器。
# native 変換（サブセット）を優先し、未対応構文は embed 方式へフォールバックします。

from __future__ import annotations

import argparse
import ast
import os
from pathlib import Path
import sys

try:
    from common.base_transpiler import BaseTranspiler, TranspileError
    from common.transpile_shared import Scope
except ModuleNotFoundError:
    from src.common.base_transpiler import BaseTranspiler, TranspileError
    from src.common.transpile_shared import Scope


class RustTranspiler(BaseTranspiler):
    """Python AST を Rust コードへ変換するトランスパイラ本体。"""

    RUST_RESERVED_WORDS = {
        "as", "break", "const", "continue", "crate", "else", "enum", "extern", "false", "fn",
        "for", "if", "impl", "in", "let", "loop", "match", "mod", "move", "mut", "pub", "ref",
        "return", "self", "Self", "static", "struct", "super", "trait", "true", "type", "unsafe",
        "use", "where", "while", "async", "await", "dyn",
    }

    def __init__(self) -> None:
        """変換器の内部状態を初期化する。"""
        super().__init__(temp_prefix="__pytra")
        # 関数スコープごとの簡易型環境（Name -> Rust型）を保持する。
        self.type_env_stack: list[dict[str, str]] = []
        # モジュール内クラス名集合。コンストラクタ呼び出し判定に使う。
        self.class_names: set[str] = set()
        # モジュール内クラス定義。継承時のメソッド解決に使う。
        self.class_defs: dict[str, ast.ClassDef] = {}
        # クラス変換中のコンテキスト名。
        self.current_class_name: str | None = None
        # self 参照をどの変数名へ展開するか（メソッド: self / コンストラクタ生成中: self_obj）。
        self.self_alias_stack: list[str] = ["self"]
        # クラスごとのフィールド型情報。
        self.class_field_types: dict[str, dict[str, str]] = {}
        # 関数名 -> 引数型リスト（注釈から取得）。
        self.function_param_types: dict[str, list[str]] = {}
        # 関数名 -> 引数借用モード（"value" | "ref" | "ref_mut"）。
        self.function_param_modes: dict[str, list[str]] = {}
        # 現在変換中の関数における引数借用モード（Name -> mode）。
        self.param_borrow_mode_stack: list[dict[str, str]] = []

    def _ident(self, name: str) -> str:
        """Rust 予約語と衝突する識別子を raw identifier 化する。"""
        if name in self.RUST_RESERVED_WORDS:
            return f"r#{name}"
        return name

    def transpile_module(self, module: ast.Module) -> str:
        """モジュール全体を Rust ソースへ変換する。"""
        function_defs: list[str] = []
        class_defs: list[str] = []
        main_stmts: list[ast.stmt] = []
        has_user_main = False

        self.class_names = {stmt.name for stmt in module.body if isinstance(stmt, ast.ClassDef)}
        self.class_defs = {stmt.name: stmt for stmt in module.body if isinstance(stmt, ast.ClassDef)}
        self._collect_function_signatures(module)

        for stmt in module.body:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                # Rust native モードでは import は無視。必要なら embed 側に倒す。
                continue
            if isinstance(stmt, ast.ClassDef):
                class_defs.append(self.transpile_class(stmt))
                continue
            if isinstance(stmt, ast.FunctionDef):
                if stmt.name == "main":
                    has_user_main = True
                function_defs.append(self.transpile_function(stmt))
                continue
            if self._is_main_guard(stmt):
                main_stmts.extend(stmt.body)
                continue
            main_stmts.append(stmt)

        parts: list[str] = []
        parts.extend(
            [
                "// このファイルは自動生成です（native Rust mode）。",
                "",
            ]
        )
        for cls in class_defs:
            parts.append(cls)
            parts.append("")
        for fn in function_defs:
            parts.append(fn)
            parts.append("")

        if not has_user_main:
            main_lines = self.transpile_statements(main_stmts, Scope(declared=set()))
            parts.append("fn main() {")
            parts.extend(self._indent_block(main_lines))
            parts.append("}")
            parts.append("")
        return "\n".join(parts)

    def _collect_function_signatures(self, module: ast.Module) -> None:
        """モジュール内関数の引数型と借用モードを事前収集する。"""
        self.function_param_types = {}
        self.function_param_modes = {}
        for stmt in module.body:
            if not isinstance(stmt, ast.FunctionDef):
                continue
            types: list[str] = []
            for arg in stmt.args.args:
                if arg.annotation is None:
                    raise TranspileError(f"function '{stmt.name}' arg '{arg.arg}' requires annotation")
                types.append(self._map_annotation(arg.annotation))
            self.function_param_types[stmt.name] = types
            self.function_param_modes[stmt.name] = self._infer_function_param_modes(stmt, types)

    def _infer_function_param_modes(self, fn: ast.FunctionDef, param_types: list[str]) -> list[str]:
        """関数引数ごとの借用モードを推論する。"""
        param_names = [arg.arg for arg in fn.args.args]
        rebound_names: set[str] = set()
        container_mut_names: set[str] = set()

        def mark_rebound_target(target: ast.expr) -> None:
            if isinstance(target, ast.Name) and target.id in param_names:
                rebound_names.add(target.id)
                return
            if isinstance(target, ast.Tuple):
                for elt in target.elts:
                    mark_rebound_target(elt)

        def mark_container_mut_target(target: ast.expr) -> None:
            if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id in param_names:
                container_mut_names.add(target.value.id)
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id in param_names:
                container_mut_names.add(target.value.id)

        for node in ast.walk(fn):
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    mark_rebound_target(tgt)
                    mark_container_mut_target(tgt)
            elif isinstance(node, ast.AnnAssign):
                mark_rebound_target(node.target)
                mark_container_mut_target(node.target)
            elif isinstance(node, ast.AugAssign):
                mark_rebound_target(node.target)
                mark_container_mut_target(node.target)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    base_name = node.func.value.id
                    if base_name in param_names and node.func.attr in {
                        "append", "pop", "insert", "clear", "remove", "update", "extend", "sort", "reverse",
                        "add", "discard", "setdefault",
                    }:
                        container_mut_names.add(base_name)

        modes: list[str] = []
        for i, name in enumerate(param_names):
            ty = param_types[i]
            if not self._is_heap_like_type(ty):
                modes.append("value")
                continue
            if name in rebound_names:
                modes.append("value")
                continue
            if name in container_mut_names:
                modes.append("ref_mut")
                continue
            modes.append("ref")
        return modes

    def _is_heap_like_type(self, rust_type: str) -> bool:
        """所有権コストの高い型かを判定する。"""
        return (
            rust_type == "String"
            or rust_type.startswith("Vec<")
            or rust_type.startswith("std::collections::HashMap<")
            or rust_type.startswith("std::collections::HashSet<")
        )

    def transpile_class(self, cls: ast.ClassDef) -> str:
        """Python class を Rust の `struct + impl` へ変換する。"""
        base_methods: list[ast.FunctionDef] = []
        if len(cls.bases) > 1:
            raise TranspileError("multiple inheritance is not supported")
        if len(cls.bases) == 1:
            if not isinstance(cls.bases[0], ast.Name):
                raise TranspileError("base class must be a simple name")
            base_name = cls.bases[0].id
            if base_name not in self.class_defs:
                raise TranspileError(f"base class '{base_name}' is not found in module")
            base_cls = self.class_defs[base_name]
            for node in base_cls.body:
                if isinstance(node, ast.FunctionDef) and node.name != "__init__":
                    base_methods.append(node)

        field_types: dict[str, str] = {}
        field_defaults: dict[str, str] = {}
        methods: list[ast.FunctionDef] = []
        init_method: ast.FunctionDef | None = None
        is_dataclass = any(
            (isinstance(d, ast.Name) and d.id == "dataclass")
            or (isinstance(d, ast.Attribute) and d.attr == "dataclass")
            for d in cls.decorator_list
        )

        for stmt in cls.body:
            if isinstance(stmt, ast.FunctionDef):
                if stmt.name == "__init__":
                    init_method = stmt
                else:
                    methods.append(stmt)
            elif isinstance(stmt, ast.AnnAssign):
                if not isinstance(stmt.target, ast.Name):
                    raise TranspileError("class field declaration target must be name")
                name = stmt.target.id
                field_types[name] = self._map_annotation(stmt.annotation)
                if stmt.value is not None:
                    field_defaults[name] = self.transpile_expr(stmt.value)
            elif isinstance(stmt, ast.Assign):
                if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
                    raise TranspileError("class static assignment must be a simple name assignment")
                name = stmt.targets[0].id
                if name not in field_types:
                    inferred = self._expr_type(stmt.value)
                    field_types[name] = inferred if inferred is not None else "i64"
                field_defaults[name] = self.transpile_expr(stmt.value)
            elif isinstance(stmt, ast.Pass):
                continue
            else:
                raise TranspileError(f"unsupported class member: {type(stmt).__name__}")

        if init_method is not None:
            for stmt in init_method.body:
                if isinstance(stmt, ast.Assign):
                    if len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Attribute):
                        attr = stmt.targets[0]
                        if isinstance(attr.value, ast.Name) and attr.value.id == "self":
                            name = attr.attr
                            if name not in field_types:
                                inferred = self._expr_type(stmt.value)
                                field_types[name] = inferred if inferred is not None else "i64"
                if isinstance(stmt, ast.AnnAssign):
                    if isinstance(stmt.target, ast.Attribute):
                        attr = stmt.target
                        if isinstance(attr.value, ast.Name) and attr.value.id == "self":
                            field_types[attr.attr] = self._map_annotation(stmt.annotation)

        for name, ty in list(field_types.items()):
            if name not in field_defaults:
                field_defaults[name] = self._default_value_for_type(ty)
        self.class_field_types[cls.name] = dict(field_types)

        struct_lines = [f"#[derive(Clone)]", f"struct {cls.name} {{"] + [f"    {name}: {field_types[name]}," for name in field_types] + ["}"]

        impl_lines: list[str] = [f"impl {cls.name} {{"]
        ctor_lines = self._transpile_class_constructor(cls.name, field_types, field_defaults, init_method, is_dataclass)
        impl_lines.extend(self._indent_block(ctor_lines))
        own_method_names = {m.name for m in methods}
        inherited_methods = [m for m in base_methods if m.name not in own_method_names]
        prev_class = self.current_class_name
        self.current_class_name = cls.name
        try:
            for method in methods + inherited_methods:
                impl_lines.append("")
                impl_lines.extend(self._indent_block(self._transpile_method(method).splitlines()))
        finally:
            self.current_class_name = prev_class
        impl_lines.append("}")
        return "\n".join(struct_lines + [""] + impl_lines)

    def _transpile_class_constructor(
        self,
        class_name: str,
        field_types: dict[str, str],
        field_defaults: dict[str, str],
        init_method: ast.FunctionDef | None,
        is_dataclass: bool,
    ) -> list[str]:
        """クラス用コンストラクタ `new(...)` を生成する。"""
        params: list[str] = []
        init_lines: list[str] = []
        declared = set()
        type_env: dict[str, str] = {}
        if init_method is not None:
            for arg in init_method.args.args[1:]:
                if arg.annotation is None:
                    raise TranspileError(f"constructor arg '{arg.arg}' requires annotation")
                ty = self._map_annotation(arg.annotation)
                params.append(f"{self._ident(arg.arg)}: {ty}")
                declared.add(arg.arg)
                type_env[arg.arg] = ty
        elif is_dataclass:
            # dataclass はデフォルト値なしフィールドのみ引数化する。
            for name, ty in field_types.items():
                has_default = name in field_defaults and field_defaults[name] != self._default_value_for_type(ty)
                if has_default:
                    continue
                params.append(f"{self._ident(name)}: {ty}")
                declared.add(name)
                type_env[name] = ty

        init_lines.append("let mut self_obj = Self {")
        for name in field_types:
            init_lines.append(f"    {name}: {field_defaults[name]},")
        init_lines.append("};")

        self.type_env_stack.append(type_env)
        prev_class = self.current_class_name
        self.current_class_name = class_name
        self.self_alias_stack.append("self_obj")
        try:
            if init_method is not None:
                init_lines.extend(self.transpile_statements(init_method.body, Scope(declared=set(declared))))
            elif is_dataclass:
                for name in field_types:
                    if name in declared:
                        init_lines.append(f"self_obj.{name} = {self._ident(name)};")
            init_lines.append("self_obj")
        finally:
            self.current_class_name = prev_class
            self.type_env_stack.pop()
            self.self_alias_stack.pop()
        return [f"fn new({', '.join(params)}) -> Self {{"] + self._indent_block(init_lines) + ["}"]

    def _transpile_method(self, fn: ast.FunctionDef) -> str:
        """クラスメソッドを Rust `impl` メソッドへ変換する。"""
        if len(fn.args.args) == 0 or fn.args.args[0].arg != "self":
            raise TranspileError("method must have self as first argument")
        self_param = "&mut self"
        params: list[str] = [self_param]
        declared = {"self"}
        type_env: dict[str, str] = {}
        for arg in fn.args.args[1:]:
            if arg.annotation is None:
                raise TranspileError(f"method '{fn.name}' arg '{arg.arg}' requires annotation")
            ty = self._map_annotation(arg.annotation)
            params.append(f"mut {self._ident(arg.arg)}: {ty}")
            declared.add(arg.arg)
            type_env[arg.arg] = ty
        ret = "()" if fn.returns is None else self._map_annotation(fn.returns)
        self.type_env_stack.append(type_env)
        self.self_alias_stack.append("self")
        try:
            body = self.transpile_statements(fn.body, Scope(declared=declared))
        finally:
            self.self_alias_stack.pop()
            self.type_env_stack.pop()
        lines = [f"fn {self._ident(fn.name)}({', '.join(params)}) -> {ret} {{"] + self._indent_block(body) + ["}"]
        return "\n".join(lines)

    def _method_mutates_self(self, fn: ast.FunctionDef) -> bool:
        """メソッドが `self.<field>` を更新するかを判定する。"""
        for node in ast.walk(fn):
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name) and tgt.value.id == "self":
                        return True
            if isinstance(node, ast.AnnAssign):
                tgt = node.target
                if isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name) and tgt.value.id == "self":
                    return True
            if isinstance(node, ast.AugAssign):
                tgt = node.target
                if isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name) and tgt.value.id == "self":
                    return True
        return False

    def transpile_function(self, fn: ast.FunctionDef) -> str:
        """関数定義を Rust の `fn` へ変換する。"""
        params: list[str] = []
        declared = set()
        type_env: dict[str, str] = {}
        param_modes = self.function_param_modes.get(fn.name, [])
        borrow_mode_env: dict[str, str] = {}
        for i, arg in enumerate(fn.args.args):
            if arg.annotation is None:
                raise TranspileError(f"function '{fn.name}' arg '{arg.arg}' requires annotation")
            rust_type = self._map_annotation(arg.annotation)
            mode = param_modes[i] if i < len(param_modes) else "value"
            borrow_mode_env[arg.arg] = mode
            if mode == "ref":
                params.append(f"{self._ident(arg.arg)}: &{rust_type}")
            elif mode == "ref_mut":
                params.append(f"{self._ident(arg.arg)}: &mut {rust_type}")
            else:
                params.append(f"mut {self._ident(arg.arg)}: {rust_type}")
            declared.add(arg.arg)
            type_env[arg.arg] = rust_type

        ret = "()" if fn.returns is None else self._map_annotation(fn.returns)
        self.type_env_stack.append(type_env)
        self.param_borrow_mode_stack.append(borrow_mode_env)
        try:
            body = self.transpile_statements(fn.body, Scope(declared=declared))
            lines = [f"fn {self._ident(fn.name)}({', '.join(params)}) -> {ret} {{"] + self._indent_block(body) + ["}"]
            return "\n".join(lines)
        finally:
            self.param_borrow_mode_stack.pop()
            self.type_env_stack.pop()

    def transpile_statements(self, stmts: list[ast.stmt], scope: Scope) -> list[str]:
        """文ノード列を Rust 文列へ変換する。"""
        out: list[str] = []
        for stmt in stmts:
            if isinstance(stmt, ast.Pass):
                continue
            if isinstance(stmt, ast.Return):
                if stmt.value is None:
                    out.append("return;")
                else:
                    out.append(f"return {self.transpile_expr(stmt.value)};")
                continue
            if isinstance(stmt, ast.Expr):
                if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                    continue
                out.append(f"{self.transpile_expr(stmt.value)};")
                continue
            if isinstance(stmt, ast.AnnAssign):
                if isinstance(stmt.target, ast.Attribute):
                    attr = stmt.target
                    if not (isinstance(attr.value, ast.Name) and attr.value.id == "self"):
                        raise TranspileError("annotated assignment target must be name or self attribute")
                    value = self._default_value_for_type(self._map_annotation(stmt.annotation)) if stmt.value is None else self.transpile_expr(stmt.value)
                    self_alias = self.self_alias_stack[-1]
                    if self._field_type_of_current_class(attr.attr) == "Vec<u8>":
                        out.append(f"{self_alias}.{attr.attr} = ({value}) as u8;")
                    else:
                        out.append(f"{self_alias}.{attr.attr} = {value};")
                else:
                    if not isinstance(stmt.target, ast.Name):
                        raise TranspileError("annotated assignment target must be name")
                    name = stmt.target.id
                    name_id = self._ident(name)
                    rty = self._map_annotation(stmt.annotation)
                    if stmt.value is None:
                        out.append(f"let mut {name_id}: {rty};")
                    else:
                        out.append(f"let mut {name_id}: {rty} = {self.transpile_expr(stmt.value)};")
                    scope.declared.add(name)
                    if len(self.type_env_stack) > 0:
                        self.type_env_stack[-1][name] = rty
                continue
            if isinstance(stmt, ast.Assign):
                if len(stmt.targets) != 1:
                    raise TranspileError("only single assignment target is supported")
                target = stmt.targets[0]
                if isinstance(target, ast.Tuple):
                    temp_values: list[str] = []
                    if isinstance(stmt.value, ast.Tuple):
                        if len(target.elts) != len(stmt.value.elts):
                            raise TranspileError("tuple assignment requires tuple value with same arity")
                        for i, src in enumerate(stmt.value.elts):
                            temp_name = self._new_temp(f"tuple_{i}")
                            temp_values.append(temp_name)
                            out.append(f"let {temp_name} = {self.transpile_expr(src)};")
                    else:
                        tuple_temp = self._new_temp("tuple_rhs")
                        out.append(f"let {tuple_temp} = {self.transpile_expr(stmt.value)};")
                        for i in range(len(target.elts)):
                            temp_values.append(f"{tuple_temp}.{i}")
                    for i, dst in enumerate(target.elts):
                        if not isinstance(dst, ast.Name):
                            raise TranspileError("tuple assignment target must contain only names")
                        name = dst.id
                        name_id = self._ident(name)
                        val = temp_values[i]
                        if name in scope.declared:
                            out.append(f"{name_id} = {val};")
                        else:
                            out.append(f"let mut {name_id} = {val};")
                            scope.declared.add(name)
                    continue
                if not isinstance(target, ast.Name):
                    if isinstance(target, ast.Attribute):
                        if isinstance(target.value, ast.Name) and target.value.id == "self":
                            self_alias = self.self_alias_stack[-1]
                            rhs = self.transpile_expr(stmt.value)
                            if self._field_type_of_current_class(target.attr) == "Vec<u8>":
                                out.append(f"{self_alias}.{target.attr} = ({rhs}) as u8;")
                            else:
                                out.append(f"{self_alias}.{target.attr} = {rhs};")
                            continue
                        out.append(f"{self.transpile_expr(target)} = {self.transpile_expr(stmt.value)};")
                        continue
                    if isinstance(target, ast.Subscript):
                        rhs = self.transpile_expr(stmt.value)
                        if self._is_hashmap_subscript_target(target):
                            base_expr = self.transpile_expr(target.value)
                            key_expr = self.transpile_expr(target.slice)
                            temp_rhs = self._new_temp("insert_val")
                            out.append(f"let {temp_rhs} = {rhs};")
                            out.append(f"{base_expr}.insert({key_expr}, {temp_rhs});")
                        elif self._is_u8_subscript_target(target):
                            target_expr = self._transpile_subscript_lvalue(target)
                            out.append(f"{target_expr} = ({rhs}) as u8;")
                        else:
                            target_expr = self._transpile_subscript_lvalue(target)
                            out.append(f"{target_expr} = {rhs};")
                        continue
                    raise TranspileError("only simple assignment is supported")
                name = target.id
                name_id = self._ident(name)
                val = self.transpile_expr(stmt.value)
                if name in scope.declared:
                    out.append(f"{name_id} = {val};")
                else:
                    out.append(f"let mut {name_id} = {val};")
                    scope.declared.add(name)
                    inferred = self._expr_type(stmt.value)
                    if inferred is not None and len(self.type_env_stack) > 0:
                        self.type_env_stack[-1][name] = inferred
                continue
            if isinstance(stmt, ast.AugAssign):
                op = self._binop(stmt.op)
                if isinstance(stmt.target, ast.Name):
                    name_id = self._ident(stmt.target.id)
                    out.append(f"{name_id} = {name_id} {op} {self.transpile_expr(stmt.value)};")
                    continue
                if isinstance(stmt.target, ast.Attribute):
                    target_expr = self.transpile_expr(stmt.target)
                    out.append(f"{target_expr} = {target_expr} {op} {self.transpile_expr(stmt.value)};")
                    continue
                if isinstance(stmt.target, ast.Subscript):
                    target_expr = self._transpile_subscript_lvalue(stmt.target)
                    rhs = self.transpile_expr(stmt.value)
                    if self._is_u8_subscript_target(stmt.target):
                        out.append(f"{target_expr} = ({target_expr} {op} {rhs}) as u8;")
                    else:
                        out.append(f"{target_expr} = {target_expr} {op} {rhs};")
                    continue
                raise TranspileError("augassign target must be name, attribute or subscript")
                continue
            if isinstance(stmt, ast.If):
                out.extend(self._transpile_if(stmt, scope))
                continue
            if isinstance(stmt, ast.While):
                out.append(f"while py_bool(&({self.transpile_expr(stmt.test)})) {{")
                out.extend(self._indent_block(self.transpile_statements(stmt.body, Scope(declared=set(scope.declared)))))
                out.append("}")
                if stmt.orelse:
                    raise TranspileError("while-else is not supported")
                continue
            if isinstance(stmt, ast.For):
                out.extend(self._transpile_for(stmt, scope))
                continue
            if isinstance(stmt, ast.Try):
                out.extend(self._transpile_try(stmt, scope))
                continue
            if isinstance(stmt, ast.Raise):
                if stmt.exc is None:
                    out.append('panic!("raise");')
                else:
                    out.append(f'panic!("{{}}", {self.transpile_expr(stmt.exc)});')
                continue
            if isinstance(stmt, ast.Break):
                out.append("break;")
                continue
            if isinstance(stmt, ast.Continue):
                out.append("continue;")
                continue
            raise TranspileError(f"unsupported statement: {type(stmt).__name__}")
        return out

    def _transpile_if(self, stmt: ast.If, scope: Scope) -> list[str]:
        """if/else 文を Rust の `if` 構文へ変換する。"""
        lines: list[str] = [f"if {self.transpile_expr(stmt.test)} {{"]
        lines[0] = f"if py_bool(&({self.transpile_expr(stmt.test)})) {{"
        lines.extend(self._indent_block(self.transpile_statements(stmt.body, Scope(declared=set(scope.declared)))))
        if stmt.orelse:
            lines.append("} else {")
            lines.extend(self._indent_block(self.transpile_statements(stmt.orelse, Scope(declared=set(scope.declared)))))
        lines.append("}")
        return lines

    def _transpile_for(self, stmt: ast.For, scope: Scope) -> list[str]:
        """for 文を `range` または iterable ループへ変換する。"""
        if not isinstance(stmt.target, ast.Name):
            raise TranspileError("for target must be name")
        name = stmt.target.id
        name_id = self._ident(name)
        rng = self._parse_range_args(stmt.iter, argc_error="range arg count > 3 is not supported")
        if rng is None:
            lines = [f"for {name_id} in ({self.transpile_expr(stmt.iter)}).clone() {{"]
            body_scope = Scope(declared=set(scope.declared))
            body_scope.declared.add(name)
            prev_type = None
            has_env = len(self.type_env_stack) > 0
            if has_env:
                env = self.type_env_stack[-1]
                prev_type = env.get(name)
                iter_ty = self._expr_type(stmt.iter)
                if iter_ty is not None and iter_ty.startswith("Vec<") and iter_ty.endswith(">"):
                    env[name] = iter_ty[4:-1]
            lines.extend(self._indent_block(self.transpile_statements(stmt.body, body_scope)))
            if has_env:
                env = self.type_env_stack[-1]
                if prev_type is None:
                    env.pop(name, None)
                else:
                    env[name] = prev_type
            lines.append("}")
            if stmt.orelse:
                raise TranspileError("for-else is not supported")
            return lines
        start, stop, step = rng
        lines: list[str] = []
        if step == "1":
            lines.append(f"for {name_id} in ({start})..({stop}) {{")
            body_scope = Scope(declared=set(scope.declared))
            body_scope.declared.add(name)
            prev_type = None
            has_env = len(self.type_env_stack) > 0
            if has_env:
                env = self.type_env_stack[-1]
                prev_type = env.get(name)
                env[name] = "i64"
            lines.extend(self._indent_block(self.transpile_statements(stmt.body, body_scope)))
            if has_env:
                env = self.type_env_stack[-1]
                if prev_type is None:
                    env.pop(name, None)
                else:
                    env[name] = prev_type
            lines.append("}")
        else:
            i_name = self._new_temp("i")
            lines.append(f"let mut {i_name} = {start};")
            lines.append(f"while (({step}) > 0 && {i_name} < ({stop})) || (({step}) < 0 && {i_name} > ({stop})) {{")
            lines.append(f"{self.INDENT}let {name_id} = {i_name};")
            body_scope = Scope(declared=set(scope.declared))
            body_scope.declared.add(name)
            prev_type = None
            has_env = len(self.type_env_stack) > 0
            if has_env:
                env = self.type_env_stack[-1]
                prev_type = env.get(name)
                env[name] = "i64"
            lines.extend(self._indent_block(self.transpile_statements(stmt.body, body_scope)))
            if has_env:
                env = self.type_env_stack[-1]
                if prev_type is None:
                    env.pop(name, None)
                else:
                    env[name] = prev_type
            lines.append(f"{self.INDENT}{i_name} += ({step});")
            lines.append("}")
        if stmt.orelse:
            raise TranspileError("for-else is not supported")
        return lines

    def _transpile_try(self, stmt: ast.Try, scope: Scope) -> list[str]:
        """限定パターンの try/except/finally を Rust 条件分岐へ変換する。"""
        # 現状は case19 相当の典型パターンを native 対応する。
        # try:
        #   if cond: raise Exception(...)
        #   return ok
        # except Exception as ex:
        #   return ng
        # finally: pass
        if len(stmt.handlers) != 1:
            raise TranspileError("only single except handler is supported")
        if stmt.orelse:
            raise TranspileError("try-else is not supported")
        if any(not isinstance(s, ast.Pass) for s in stmt.finalbody):
            raise TranspileError("finally with statements is not supported")

        handler = stmt.handlers[0]
        if handler.type is not None and not (
            isinstance(handler.type, ast.Name) and handler.type.id == "Exception"
        ):
            raise TranspileError("only except Exception is supported")

        if len(stmt.body) != 2:
            raise TranspileError("unsupported try body pattern")
        first, second = stmt.body[0], stmt.body[1]
        if not isinstance(first, ast.If):
            raise TranspileError("unsupported try body pattern")
        if first.orelse:
            raise TranspileError("unsupported try-if else block")
        if len(first.body) != 1 or not isinstance(first.body[0], ast.Raise):
            raise TranspileError("unsupported raise pattern")
        if not isinstance(second, ast.Return) or second.value is None:
            raise TranspileError("try success path must end with return value")
        if len(handler.body) != 1 or not isinstance(handler.body[0], ast.Return) or handler.body[0].value is None:
            raise TranspileError("except path must end with return value")

        cond = self.transpile_expr(first.test)
        ok_expr = self.transpile_expr(second.value)
        ng_expr = self.transpile_expr(handler.body[0].value)
        return [f"if py_bool(&({cond})) {{", f"{self.INDENT}return {ng_expr};", "} else {", f"{self.INDENT}return {ok_expr};", "}"]

    def transpile_expr(self, expr: ast.expr) -> str:
        """式ノードを Rust 式文字列へ変換する。"""
        if isinstance(expr, ast.Name):
            if expr.id == "True":
                return "true"
            if expr.id == "False":
                return "false"
            return self._ident(expr.id)
        if isinstance(expr, ast.Attribute):
            if isinstance(expr.value, ast.Name) and expr.value.id == "self":
                self_alias = self.self_alias_stack[-1]
                return f"{self_alias}.{expr.attr}"
            if isinstance(expr.value, ast.Name) and expr.value.id == "math":
                if expr.attr == "pi":
                    return "std::f64::consts::PI"
                return f"math_{expr.attr}"
            return f"{self.transpile_expr(expr.value)}.{expr.attr}"
        if isinstance(expr, ast.Constant):
            if isinstance(expr.value, bool):
                return "true" if expr.value else "false"
            if isinstance(expr.value, int):
                return str(expr.value)
            if isinstance(expr.value, float):
                return repr(expr.value)
            if isinstance(expr.value, str):
                return self._escape_str(expr.value)
            if expr.value is None:
                return "()"
            raise TranspileError(f"unsupported constant: {expr.value!r}")
        if isinstance(expr, ast.BinOp):
            l = self.transpile_expr(expr.left)
            r = self.transpile_expr(expr.right)
            lt = self._expr_type(expr.left)
            rt = self._expr_type(expr.right)
            if isinstance(expr.op, ast.Add):
                if lt == "String" or rt == "String":
                    return f"format!(\"{{}}{{}}\", {l}, {r})"
            if isinstance(expr.op, ast.FloorDiv):
                return f"(({l}) / ({r}))"
            if isinstance(expr.op, ast.Div):
                return f"((( {l} ) as f64) / (( {r} ) as f64))"
            if (lt in {"f64", "f32"} and rt in {"i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8"}) or (
                rt in {"f64", "f32"} and lt in {"i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8"}
            ):
                return f"(((( {l} ) as f64) {self._binop(expr.op)} (( {r} ) as f64)))"
            return f"(({l}) {self._binop(expr.op)} ({r}))"
        if isinstance(expr, ast.UnaryOp):
            return f"({self._unaryop(expr.op)}{self.transpile_expr(expr.operand)})"
        if isinstance(expr, ast.BoolOp):
            op = "&&" if isinstance(expr.op, ast.And) else "||"
            return "(" + f" {op} ".join(self.transpile_expr(v) for v in expr.values) + ")"
        if isinstance(expr, ast.Compare):
            return self._transpile_compare(expr)
        if isinstance(expr, ast.Call):
            return self._transpile_call(expr)
        if isinstance(expr, ast.IfExp):
            return f"(if py_bool(&({self.transpile_expr(expr.test)})) {{ {self.transpile_expr(expr.body)} }} else {{ {self.transpile_expr(expr.orelse)} }})"
        if isinstance(expr, ast.JoinedStr):
            return self._transpile_joined_str(expr)
        if isinstance(expr, ast.List):
            values = ", ".join(self.transpile_expr(v) for v in expr.elts)
            return f"vec![{values}]"
        if isinstance(expr, ast.Tuple):
            values = ", ".join(self.transpile_expr(v) for v in expr.elts)
            if len(expr.elts) == 1:
                return f"({values},)"
            return f"({values})"
        if isinstance(expr, ast.Dict):
            if any(k is None for k in expr.keys):
                raise TranspileError("dict unpacking is not supported")
            pairs: list[str] = []
            for k, v in zip(expr.keys, expr.values):
                key_expr = self.transpile_expr(k)  # type: ignore[arg-type]
                val_expr = self.transpile_expr(v)
                pairs.append(f"({key_expr}, {val_expr})")
            return f"std::collections::HashMap::from([{', '.join(pairs)}])"
        if isinstance(expr, ast.Subscript):
            value_expr = self.transpile_expr(expr.value)
            if isinstance(expr.slice, ast.Slice):
                start_expr = "None" if expr.slice.lower is None else f"Some({self.transpile_expr(expr.slice.lower)})"
                end_expr = "None" if expr.slice.upper is None else f"Some({self.transpile_expr(expr.slice.upper)})"
                return f"py_slice(&({value_expr}), {start_expr}, {end_expr})"
            index_expr = self.transpile_expr(expr.slice)
            base_ty = self._expr_type(expr.value)
            if base_ty is not None and base_ty.startswith("std::collections::HashMap<"):
                read_expr = f"({value_expr})[&({index_expr})]"
                val_ty = self._expr_type(expr)
                if (
                    isinstance(expr.ctx, ast.Load)
                    and val_ty is not None
                    and not self._is_copy_type(val_ty)
                    and not self._is_borrow_friendly_container_type(val_ty)
                ):
                    return f"({read_expr}).clone()"
                return read_expr
            read_expr = f"({value_expr})[{index_expr} as usize]"
            val_ty = self._expr_type(expr)
            if (
                isinstance(expr.ctx, ast.Load)
                and val_ty is not None
                and not self._is_copy_type(val_ty)
                and not self._is_borrow_friendly_container_type(val_ty)
            ):
                return f"({read_expr}).clone()"
            return read_expr
        if isinstance(expr, ast.ListComp):
            return self._transpile_list_comp(expr)
        raise TranspileError(f"unsupported expression: {type(expr).__name__}")

    def _transpile_call(self, call: ast.Call) -> str:
        """関数呼び出し式を Rust へ変換する。"""
        if any(kw.arg is None for kw in call.keywords):
            raise TranspileError("**kwargs is not supported")
        arg_nodes = list(call.args) + [kw.value for kw in call.keywords]
        args = [self.transpile_expr(a) for a in arg_nodes]
        if isinstance(call.func, ast.Name):
            fn = call.func.id
            if fn in self.class_names:
                call_args = [self._prepare_call_arg(node, arg) for node, arg in zip(arg_nodes, args)]
                return f"{fn}::new({', '.join(call_args)})"
            if fn == "bytearray":
                if len(args) == 0:
                    return "Vec::<u8>::new()"
                if len(args) == 1:
                    return f"vec![0u8; ({args[0]}) as usize]"
                raise TranspileError("bytearray() supports at most one argument")
            if fn == "bytes":
                if len(args) == 1:
                    return f"({args[0]}).clone()"
                raise TranspileError("bytes() supports one argument")
            if fn == "print":
                if len(args) == 0:
                    return 'println!("")'
                if len(args) == 1:
                    return f"py_print({args[0]})"
                # 複数引数は format! で空白区切り表示
                fmt = " ".join(["{}"] * len(args))
                return f'println!("{fmt}", {", ".join(args)})'
            if fn == "len" and len(args) == 1:
                return f"(py_len({self._borrow_shared_expr(arg_nodes[0], args[0])}) as i64)"
            if fn == "int" and len(args) == 1:
                return f"(({args[0]}) as i64)"
            if fn == "float" and len(args) == 1:
                return f"(({args[0]}) as f64)"
            if fn == "str" and len(args) == 1:
                return f"format!(\"{{}}\", {args[0]})"
            if fn == "RuntimeError" and len(args) == 1:
                return args[0]
            if fn == "ord" and len(args) == 1:
                return f"(({args[0]}).chars().next().unwrap() as i64)"
            if fn == "max" and len(args) == 2:
                return f"(if ({args[0]}) > ({args[1]}) {{ {args[0]} }} else {{ {args[1]} }})"
            if fn == "min" and len(args) == 2:
                return f"(if ({args[0]}) < ({args[1]}) {{ {args[0]} }} else {{ {args[1]} }})"
            if fn == "save_gif":
                if len(args) != 7:
                    raise TranspileError("save_gif requires 7 arguments")
                return f"py_save_gif(&({args[0]}), {args[1]}, {args[2]}, &({args[3]}), &({args[4]}), {args[5]}, {args[6]})"
            if fn == "grayscale_palette" and len(args) == 0:
                return "py_grayscale_palette()"
            if fn == "perf_counter" and len(args) == 0:
                return "perf_counter()"
            if fn == "range":
                raise TranspileError("range() should be used only in for")
            if fn in self.function_param_modes:
                modes = self.function_param_modes.get(fn, [])
                call_args = [
                    self._prepare_user_function_call_arg(node, arg, modes[i] if i < len(modes) else "value")
                    for i, (node, arg) in enumerate(zip(arg_nodes, args))
                ]
            else:
                call_args = [self._prepare_call_arg(node, arg) for node, arg in zip(arg_nodes, args)]
            return f"{self._ident(fn)}({', '.join(call_args)})"
        if isinstance(call.func, ast.Attribute):
            if isinstance(call.func.value, ast.Name) and call.func.value.id == "math":
                casted = [f"(({a}) as f64)" for a in args]
                args_joined = ", ".join(casted)
                return f"math_{call.func.attr}({args_joined})"
            if isinstance(call.func.value, ast.Name) and call.func.value.id == "png_helper":
                if call.func.attr == "write_rgb_png":
                    if len(args) != 4:
                        raise TranspileError("write_rgb_png requires 4 arguments")
                    return f"py_write_rgb_png(&({args[0]}), {args[1]}, {args[2]}, &({args[3]}))"
            if isinstance(call.func.value, ast.Name) and call.func.value.id == "self":
                obj = self.self_alias_stack[-1]
            else:
                obj = self.transpile_expr(call.func.value)
            method = call.func.attr
            if method == "append" and len(args) == 1:
                val = args[0]
                obj_type = self._expr_type(call.func.value)
                if obj_type == "Vec<u8>":
                    return f"{obj}.push(({val}) as u8)"
                return f"{obj}.push({val})"
            if method == "pop" and len(args) == 0:
                return f"{obj}.pop().unwrap()"
            if method == "isdigit" and len(args) == 0:
                return f"py_isdigit(&({obj}))"
            if method == "isalpha" and len(args) == 0:
                return f"py_isalpha(&({obj}))"
            return f"{obj}.{self._ident(method)}({', '.join(args)})"
        raise TranspileError("only direct calls are supported")

    def _prepare_call_arg(self, node: ast.expr, rendered: str) -> str:
        """関数引数でムーブを避けるため、必要時のみ clone した式を返す。"""
        ty = self._expr_type(node)
        if ty is None:
            return rendered
        if self._is_heap_like_type(ty):
            return f"({rendered}).clone()"
        return rendered

    def _current_param_borrow_mode(self, name: str) -> str | None:
        """現在の関数コンテキストで、引数名の借用モードを返す。"""
        if len(self.param_borrow_mode_stack) == 0:
            return None
        return self.param_borrow_mode_stack[-1].get(name)

    def _borrow_shared_expr(self, node: ast.expr, rendered: str) -> str:
        """読み取り用途の参照式を作る（既に参照なら二重参照を避ける）。"""
        if isinstance(node, ast.Name):
            mode = self._current_param_borrow_mode(node.id)
            if mode == "ref" or mode == "ref_mut":
                return self._ident(node.id)
        return f"&({rendered})"

    def _prepare_user_function_call_arg(self, node: ast.expr, rendered: str, mode: str) -> str:
        """ユーザー関数呼び出し向けに、推論済み借用モードへ引数式を整形する。"""
        if mode == "value":
            return self._prepare_call_arg(node, rendered)

        if mode == "ref":
            if isinstance(node, ast.Name):
                current_mode = self._current_param_borrow_mode(node.id)
                if current_mode == "ref":
                    return self._ident(node.id)
                if current_mode == "ref_mut":
                    return f"&*{self._ident(node.id)}"
                return f"&({self._ident(node.id)})"
            return f"&({rendered})"

        if mode == "ref_mut":
            if isinstance(node, ast.Name):
                current_mode = self._current_param_borrow_mode(node.id)
                if current_mode == "ref_mut":
                    return f"&mut *{self._ident(node.id)}"
                if current_mode == "value" or current_mode is None:
                    return f"&mut {self._ident(node.id)}"
                raise TranspileError(f"cannot pass shared reference '{node.id}' as mutable reference")
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id == "self":
                    self_alias = self.self_alias_stack[-1]
                    return f"&mut {self_alias}.{node.attr}"
                return f"&mut ({self.transpile_expr(node)})"
            if isinstance(node, ast.Subscript):
                return f"&mut {self._transpile_subscript_lvalue(node)}"
            raise TranspileError("mutable reference argument must be a mutable lvalue")

        raise TranspileError(f"unknown argument borrow mode: {mode}")

    def _map_annotation(self, ann: ast.expr) -> str:
        """Python 型注釈を Rust 型へ変換する。"""
        if isinstance(ann, ast.Name):
            mapping = {
                "int": "i64",
                "int8": "i8",
                "uint8": "u8",
                "int16": "i16",
                "uint16": "u16",
                "int32": "i32",
                "uint32": "u32",
                "int64": "i64",
                "uint64": "u64",
                "float": "f64",
                "float32": "f32",
                "str": "String",
                "bytes": "Vec<u8>",
                "bytearray": "Vec<u8>",
                "bool": "bool",
                "None": "()",
            }
            if ann.id in mapping:
                return mapping[ann.id]
            return ann.id
        if isinstance(ann, ast.Subscript):
            if isinstance(ann.value, ast.Name):
                base = ann.value.id
            else:
                raise TranspileError(f"unsupported annotation: {ast.dump(ann)}")
            if base in {"list", "List"}:
                return f"Vec<{self._map_annotation(ann.slice)}>"
            if base in {"set", "Set"}:
                return f"std::collections::HashSet<{self._map_annotation(ann.slice)}>"
            if base in {"dict", "Dict"}:
                if not isinstance(ann.slice, ast.Tuple) or len(ann.slice.elts) != 2:
                    raise TranspileError("dict annotation requires two type parameters")
                kt = self._map_annotation(ann.slice.elts[0])
                vt = self._map_annotation(ann.slice.elts[1])
                return f"std::collections::HashMap<{kt}, {vt}>"
            if base in {"tuple", "Tuple"}:
                if isinstance(ann.slice, ast.Tuple):
                    items = [self._map_annotation(e) for e in ann.slice.elts]
                    if len(items) == 1:
                        return f"({items[0]},)"
                    return f"({', '.join(items)})"
                item = self._map_annotation(ann.slice)
                return f"({item},)"
            raise TranspileError(f"unsupported generic annotation base: {base}")
        if isinstance(ann, ast.Constant) and ann.value is None:
            return "()"
        raise TranspileError(f"unsupported annotation: {ast.dump(ann)}")

    def _binop(self, op: ast.operator) -> str:
        mapping = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.Mod: "%",
            ast.Pow: "^",
            ast.BitOr: "|",
            ast.BitAnd: "&",
            ast.BitXor: "^",
            ast.LShift: "<<",
            ast.RShift: ">>",
        }
        for k, v in mapping.items():
            if isinstance(op, k):
                return v
        raise TranspileError(f"unsupported binop: {type(op).__name__}")

    def _cmpop(self, op: ast.cmpop) -> str:
        mapping = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
        }
        for k, v in mapping.items():
            if isinstance(op, k):
                return v
        raise TranspileError(f"unsupported compare op: {type(op).__name__}")

    def _unaryop(self, op: ast.unaryop) -> str:
        """単項演算子ノードを Rust 演算子へ変換する。"""
        if isinstance(op, ast.USub):
            return "-"
        if isinstance(op, ast.UAdd):
            return "+"
        if isinstance(op, ast.Not):
            return "!"
        raise TranspileError(f"unsupported unary op: {type(op).__name__}")

    def _escape_str(self, value: str) -> str:
        """Python 文字列リテラルを Rust 文字列式へエスケープして変換する。"""
        esc = (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )
        return f"\"{esc}\".to_string()"

    def _transpile_joined_str(self, expr: ast.JoinedStr) -> str:
        """f-string を Rust の format! 呼び出しへ変換する。"""
        format_parts: list[str] = []
        arg_parts: list[str] = []
        for value in expr.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                format_parts.append(value.value.replace("{", "{{").replace("}", "}}"))
                continue
            if isinstance(value, ast.FormattedValue):
                format_parts.append("{}")
                arg_parts.append(self.transpile_expr(value.value))
                continue
            raise TranspileError("unsupported f-string part")
        fmt = "".join(format_parts).replace('"', '\\"')
        if len(arg_parts) == 0:
            return f"\"{fmt}\".to_string()"
        return f"format!(\"{fmt}\", {', '.join(arg_parts)})"

    def _transpile_compare(self, expr: ast.Compare) -> str:
        """比較式を Rust 式へ変換する。"""
        if len(expr.ops) != 1 or len(expr.comparators) != 1:
            raise TranspileError("chained comparison is not supported")
        l = self.transpile_expr(expr.left)
        r = self.transpile_expr(expr.comparators[0])
        lt = self._expr_type(expr.left)
        rt = self._expr_type(expr.comparators[0])
        op = expr.ops[0]
        if isinstance(op, ast.In):
            return f"py_in({self._borrow_shared_expr(expr.comparators[0], r)}, {self._borrow_shared_expr(expr.left, l)})"
        if isinstance(op, ast.NotIn):
            return f"!py_in({self._borrow_shared_expr(expr.comparators[0], r)}, {self._borrow_shared_expr(expr.left, l)})"
        numeric = {"i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8", "f64", "f32"}
        if lt in numeric and rt in numeric and lt != rt:
            return f"(((( {l} ) as f64) {self._cmpop(op)} (( {r} ) as f64)))"
        return f"(({l}) {self._cmpop(op)} ({r}))"

    def _transpile_list_comp(self, expr: ast.ListComp) -> str:
        """単純な list comprehension を Rust ブロック式へ変換する。"""
        if len(expr.generators) != 1:
            raise TranspileError("only single-generator list comprehension is supported")
        gen = expr.generators[0]
        if gen.is_async:
            raise TranspileError("async comprehension is not supported")
        if not isinstance(gen.target, ast.Name):
            raise TranspileError("list comprehension target must be name")
        loop_name = gen.target.id
        iter_expr = self.transpile_expr(gen.iter)
        out_name = self._new_temp("listcomp")
        lines: list[str] = [f"let mut {out_name} = Vec::new();", f"for {loop_name} in ({iter_expr}).clone() {{"]
        for cond in gen.ifs:
            lines.append(f"{self.INDENT}if !({self.transpile_expr(cond)}) {{ continue; }}")
        lines.append(f"{self.INDENT}{out_name}.push({self.transpile_expr(expr.elt)});")
        lines.append("}")
        lines.append(out_name)
        return "{ " + " ".join(lines) + " }"

    def _expr_type(self, expr: ast.expr) -> str | None:
        """式の推定 Rust 型を返す（不明なら None）。"""
        if isinstance(expr, ast.Constant):
            if isinstance(expr.value, str):
                return "String"
            if isinstance(expr.value, bool):
                return "bool"
            if isinstance(expr.value, int):
                return "i64"
            if isinstance(expr.value, float):
                return "f64"
        if isinstance(expr, ast.Name):
            if len(self.type_env_stack) == 0:
                return None
            return self.type_env_stack[-1].get(expr.id)
        if isinstance(expr, ast.Attribute):
            if isinstance(expr.value, ast.Name) and expr.value.id == "self":
                return self._field_type_of_current_class(expr.attr)
            if isinstance(expr.value, ast.Name) and len(self.type_env_stack) > 0:
                base_ty = self.type_env_stack[-1].get(expr.value.id)
                if base_ty is not None:
                    return self.class_field_types.get(base_ty, {}).get(expr.attr)
            return None
        if isinstance(expr, ast.Subscript):
            base_ty = self._expr_type(expr.value)
            if base_ty is None:
                return None
            if base_ty.startswith("Vec<") and base_ty.endswith(">"):
                return base_ty[4:-1]
            if base_ty.startswith("std::collections::HashMap<") and base_ty.endswith(">"):
                inside = base_ty[len("std::collections::HashMap<") : -1]
                parts = inside.split(", ")
                if len(parts) == 2:
                    return parts[1]
            return None
        if isinstance(expr, ast.JoinedStr):
            return "String"
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
            lt = self._expr_type(expr.left)
            rt = self._expr_type(expr.right)
            if lt == "String" or rt == "String":
                return "String"
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Div):
            return "f64"
        if isinstance(expr, ast.BinOp):
            lt = self._expr_type(expr.left)
            rt = self._expr_type(expr.right)
            if lt in {"f64", "f32"} or rt in {"f64", "f32"}:
                return "f64"
            ints = {"i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8"}
            if lt in ints and rt in ints:
                return "i64"
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
            if expr.func.id in self.class_names:
                return expr.func.id
            if expr.func.id == "str":
                return "String"
            if expr.func.id == "float":
                return "f64"
            if expr.func.id == "int":
                return "i64"
            if expr.func.id in {"bytearray", "bytes", "grayscale_palette"}:
                return "Vec<u8>"
        return None

    def _default_value_for_type(self, rust_type: str) -> str:
        """Rust 型名からデフォルト値式を返す。"""
        if rust_type == "String":
            return "String::new()"
        if rust_type.startswith("Vec<"):
            return "Vec::new()"
        if rust_type.startswith("std::collections::HashMap<"):
            return "std::collections::HashMap::new()"
        if rust_type.startswith("std::collections::HashSet<"):
            return "std::collections::HashSet::new()"
        if rust_type == "bool":
            return "false"
        if rust_type in {"f64", "f32"}:
            return "0.0"
        if rust_type == "()":
            return "()"
        if rust_type.startswith("i") or rust_type.startswith("u"):
            return "0"
        if rust_type in self.class_names:
            return f"{rust_type}::new()"
        return "Default::default()"

    def _field_type_of_current_class(self, field_name: str) -> str | None:
        """現在変換中クラスのフィールド型を返す。"""
        if self.current_class_name is None:
            return None
        return self.class_field_types.get(self.current_class_name, {}).get(field_name)

    def _is_u8_subscript_target(self, sub: ast.Subscript) -> bool:
        """添字代入先が Vec<u8> かを推定する。"""
        base = sub.value
        while isinstance(base, ast.Subscript):
            base = base.value
        ty = self._expr_type(base)
        return ty == "Vec<u8>"

    def _is_hashmap_subscript_target(self, sub: ast.Subscript) -> bool:
        """添字代入先が HashMap かを推定する。"""
        base = sub.value
        while isinstance(base, ast.Subscript):
            base = base.value
        ty = self._expr_type(base)
        return ty is not None and ty.startswith("std::collections::HashMap<")

    def _is_copy_type(self, rust_type: str) -> bool:
        """Rust の Copy 扱いにできるプリミティブ型かを返す。"""
        return rust_type in {"bool", "i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8", "f64", "f32", "()"}

    def _is_borrow_friendly_container_type(self, rust_type: str) -> bool:
        """添字アクセスで clone せず借用を維持してよいコンテナ型かを返す。"""
        return (
            rust_type.startswith("Vec<")
            or rust_type.startswith("std::collections::HashMap<")
            or rust_type.startswith("std::collections::HashSet<")
        )

    def _transpile_subscript_lvalue(self, sub: ast.Subscript) -> str:
        """添字代入左辺を clone なしで Rust の可変参照式へ変換する。"""
        if isinstance(sub.slice, ast.Slice):
            raise TranspileError("slice assignment is not supported")
        index_expr = self.transpile_expr(sub.slice)
        if isinstance(sub.value, ast.Subscript):
            value_expr = self._transpile_subscript_lvalue(sub.value)
        else:
            value_expr = self.transpile_expr(sub.value)
        base_ty = self._expr_type(sub.value)
        if base_ty is not None and base_ty.startswith("std::collections::HashMap<"):
            return f"({value_expr})[&({index_expr})]"
        return f"({value_expr})[{index_expr} as usize]"

def _rust_raw_string_literal(text: str) -> str:
    """任意テキストを Rust の raw string literal へ変換する。"""
    for n in range(1, 32):
        fence = "#" * n
        end_seq = f'"{fence}'
        if end_seq not in text:
            return f'r{fence}"{text}"{fence}'
    # ほぼ起こらない保険。通常文字列へエスケープする。
    escaped = (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def _runtime_path_literal(output_path: Path) -> str:
    runtime_path = (Path(__file__).resolve().parent / "rs_module" / "py_runtime.rs").resolve()
    rel = os.path.relpath(runtime_path, output_path.parent.resolve())
    return rel.replace("\\", "/")


def transpile_file_embed(input_path: Path, output_path: Path) -> None:
    source = input_path.read_text(encoding="utf-8")
    source_literal = _rust_raw_string_literal(source)
    input_name = input_path.name
    runtime_rel = _runtime_path_literal(output_path)

    rust = f"""// このファイルは自動生成です。編集しないでください。
// 入力 Python: {input_name}

#[path = "{runtime_rel}"]
mod py_runtime;

fn main() {{
    let source: &str = {source_literal};
    std::process::exit(py_runtime::run_embedded_python(source));
}}
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rust, encoding="utf-8")


def transpile_file_native(input_path: Path, output_path: Path) -> None:
    source = input_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(input_path))
    runtime_rel = _runtime_path_literal(output_path)
    rust_body = RustTranspiler().transpile_module(tree)
    rust = (
        f'#[path = "{runtime_rel}"]\n'
        "mod py_runtime;\n"
        "use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};\n\n"
        + rust_body
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rust, encoding="utf-8")


def transpile_file_auto(input_path: Path, output_path: Path) -> None:
    try:
        transpile_file_native(input_path, output_path)
    except TranspileError as exc:
        # native 未対応構文は embed 方式で実行可能性を維持する。
        transpile_file_embed(input_path, output_path)
        # 先頭へフォールバック理由を追記。
        original = output_path.read_text(encoding="utf-8")
        output_path.write_text(f"// fallback: {exc}\n{original}", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Transpile Python to Rust")
    parser.add_argument("input", help="input Python file")
    parser.add_argument("output", help="output Rust file")
    parser.add_argument(
        "--mode",
        choices=["auto", "native", "embed"],
        default="auto",
        help="transpile mode: auto(native then fallback), native(raise on unsupported), embed(always)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        if args.mode == "native":
            transpile_file_native(input_path, output_path)
        elif args.mode == "embed":
            transpile_file_embed(input_path, output_path)
        else:
            transpile_file_auto(input_path, output_path)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
