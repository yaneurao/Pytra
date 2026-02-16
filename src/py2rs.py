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

    def transpile_module(self, module: ast.Module) -> str:
        """モジュール全体を Rust ソースへ変換する。"""
        function_defs: list[str] = []
        class_defs: list[str] = []
        main_stmts: list[ast.stmt] = []
        has_user_main = False

        self.class_names = {stmt.name for stmt in module.body if isinstance(stmt, ast.ClassDef)}
        self.class_defs = {stmt.name: stmt for stmt in module.body if isinstance(stmt, ast.ClassDef)}

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

        struct_lines = [f"struct {cls.name} {{"] + [f"    {name}: {field_types[name]}," for name in field_types] + ["}"]

        impl_lines: list[str] = [f"impl {cls.name} {{"]
        ctor_lines = self._transpile_class_constructor(cls.name, field_types, field_defaults, init_method, is_dataclass)
        impl_lines.extend(self._indent_block(ctor_lines))
        own_method_names = {m.name for m in methods}
        inherited_methods = [m for m in base_methods if m.name not in own_method_names]
        for method in methods + inherited_methods:
            impl_lines.append("")
            impl_lines.extend(self._indent_block(self._transpile_method(method).splitlines()))
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
                params.append(f"{arg.arg}: {ty}")
                declared.add(arg.arg)
                type_env[arg.arg] = ty
        elif is_dataclass:
            # dataclass はデフォルト値なしフィールドのみ引数化する。
            for name, ty in field_types.items():
                has_default = name in field_defaults and field_defaults[name] != self._default_value_for_type(ty)
                if has_default:
                    continue
                params.append(f"{name}: {ty}")
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
                        init_lines.append(f"self_obj.{name} = {name};")
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
        mutates_self = self._method_mutates_self(fn)
        self_param = "&mut self" if mutates_self else "&self"
        params: list[str] = [self_param]
        declared = {"self"}
        type_env: dict[str, str] = {}
        for arg in fn.args.args[1:]:
            if arg.annotation is None:
                raise TranspileError(f"method '{fn.name}' arg '{arg.arg}' requires annotation")
            ty = self._map_annotation(arg.annotation)
            params.append(f"{arg.arg}: {ty}")
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
        lines = [f"fn {fn.name}({', '.join(params)}) -> {ret} {{"] + self._indent_block(body) + ["}"]
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
        for arg in fn.args.args:
            if arg.annotation is None:
                raise TranspileError(f"function '{fn.name}' arg '{arg.arg}' requires annotation")
            rust_type = self._map_annotation(arg.annotation)
            params.append(f"{arg.arg}: {rust_type}")
            declared.add(arg.arg)
            type_env[arg.arg] = rust_type

        ret = "()" if fn.returns is None else self._map_annotation(fn.returns)
        self.type_env_stack.append(type_env)
        try:
            body = self.transpile_statements(fn.body, Scope(declared=declared))
            lines = [f"fn {fn.name}({', '.join(params)}) -> {ret} {{"] + self._indent_block(body) + ["}"]
            return "\n".join(lines)
        finally:
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
                    out.append(f"{self_alias}.{attr.attr} = {value};")
                else:
                    if not isinstance(stmt.target, ast.Name):
                        raise TranspileError("annotated assignment target must be name")
                    name = stmt.target.id
                    rty = self._map_annotation(stmt.annotation)
                    if stmt.value is None:
                        out.append(f"let mut {name}: {rty};")
                    else:
                        out.append(f"let mut {name}: {rty} = {self.transpile_expr(stmt.value)};")
                    scope.declared.add(name)
                    if len(self.type_env_stack) > 0:
                        self.type_env_stack[-1][name] = rty
                continue
            if isinstance(stmt, ast.Assign):
                if len(stmt.targets) != 1:
                    raise TranspileError("only single assignment target is supported")
                target = stmt.targets[0]
                if isinstance(target, ast.Tuple):
                    if not isinstance(stmt.value, ast.Tuple) or len(target.elts) != len(stmt.value.elts):
                        raise TranspileError("tuple assignment requires tuple value with same arity")
                    temp_names: list[str] = []
                    for i, src in enumerate(stmt.value.elts):
                        temp_name = self._new_temp(f"tuple_{i}")
                        temp_names.append(temp_name)
                        out.append(f"let {temp_name} = {self.transpile_expr(src)};")
                    for i, dst in enumerate(target.elts):
                        if not isinstance(dst, ast.Name):
                            raise TranspileError("tuple assignment target must contain only names")
                        name = dst.id
                        val = temp_names[i]
                        if name in scope.declared:
                            out.append(f"{name} = {val};")
                        else:
                            out.append(f"let mut {name} = {val};")
                            scope.declared.add(name)
                    continue
                if not isinstance(target, ast.Name):
                    if isinstance(target, ast.Attribute):
                        if isinstance(target.value, ast.Name) and target.value.id == "self":
                            self_alias = self.self_alias_stack[-1]
                            out.append(f"{self_alias}.{target.attr} = {self.transpile_expr(stmt.value)};")
                            continue
                        out.append(f"{self.transpile_expr(target)} = {self.transpile_expr(stmt.value)};")
                        continue
                    raise TranspileError("only simple assignment is supported")
                name = target.id
                val = self.transpile_expr(stmt.value)
                if name in scope.declared:
                    out.append(f"{name} = {val};")
                else:
                    out.append(f"let mut {name} = {val};")
                    scope.declared.add(name)
                continue
            if isinstance(stmt, ast.AugAssign):
                op = self._binop(stmt.op)
                if isinstance(stmt.target, ast.Name):
                    out.append(f"{stmt.target.id} = {stmt.target.id} {op} {self.transpile_expr(stmt.value)};")
                    continue
                if isinstance(stmt.target, ast.Attribute):
                    target_expr = self.transpile_expr(stmt.target)
                    out.append(f"{target_expr} = {target_expr} {op} {self.transpile_expr(stmt.value)};")
                    continue
                raise TranspileError("augassign target must be name or attribute")
                continue
            if isinstance(stmt, ast.If):
                out.extend(self._transpile_if(stmt, scope))
                continue
            if isinstance(stmt, ast.While):
                out.append(f"while {self.transpile_expr(stmt.test)} {{")
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
        rng = self._parse_range_args(stmt.iter, argc_error="range arg count > 3 is not supported")
        if rng is None:
            lines = [f"for {name} in ({self.transpile_expr(stmt.iter)}).clone() {{"]
            body_scope = Scope(declared=set(scope.declared))
            body_scope.declared.add(name)
            lines.extend(self._indent_block(self.transpile_statements(stmt.body, body_scope)))
            lines.append("}")
            if stmt.orelse:
                raise TranspileError("for-else is not supported")
            return lines
        start, stop, step = rng
        lines: list[str] = []
        if step == "1":
            lines.append(f"for {name} in ({start})..({stop}) {{")
            body_scope = Scope(declared=set(scope.declared))
            body_scope.declared.add(name)
            lines.extend(self._indent_block(self.transpile_statements(stmt.body, body_scope)))
            lines.append("}")
        else:
            i_name = self._new_temp("i")
            lines.append(f"let mut {i_name} = {start};")
            lines.append(f"while (({step}) > 0 && {i_name} < ({stop})) || (({step}) < 0 && {i_name} > ({stop})) {{")
            lines.append(f"{self.INDENT}let {name} = {i_name};")
            body_scope = Scope(declared=set(scope.declared))
            body_scope.declared.add(name)
            lines.extend(self._indent_block(self.transpile_statements(stmt.body, body_scope)))
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
        return [f"if {cond} {{", f"{self.INDENT}return {ng_expr};", "} else {", f"{self.INDENT}return {ok_expr};", "}"]

    def transpile_expr(self, expr: ast.expr) -> str:
        """式ノードを Rust 式文字列へ変換する。"""
        if isinstance(expr, ast.Name):
            if expr.id == "True":
                return "true"
            if expr.id == "False":
                return "false"
            return expr.id
        if isinstance(expr, ast.Attribute):
            if isinstance(expr.value, ast.Name) and expr.value.id == "self":
                self_alias = self.self_alias_stack[-1]
                return f"{self_alias}.{expr.attr}"
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
            if isinstance(expr.op, ast.Add):
                lt = self._expr_type(expr.left)
                rt = self._expr_type(expr.right)
                if lt == "String" or rt == "String":
                    return f"format!(\"{{}}{{}}\", {l}, {r})"
            if isinstance(expr.op, ast.FloorDiv):
                return f"(({l}) / ({r}))"
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
            return f"(if {self.transpile_expr(expr.test)} {{ {self.transpile_expr(expr.body)} }} else {{ {self.transpile_expr(expr.orelse)} }})"
        if isinstance(expr, ast.JoinedStr):
            return self._transpile_joined_str(expr)
        if isinstance(expr, ast.List):
            values = ", ".join(self.transpile_expr(v) for v in expr.elts)
            return f"vec![{values}]"
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
            return f"({value_expr})[{index_expr} as usize]"
        if isinstance(expr, ast.ListComp):
            return self._transpile_list_comp(expr)
        raise TranspileError(f"unsupported expression: {type(expr).__name__}")

    def _transpile_call(self, call: ast.Call) -> str:
        """関数呼び出し式を Rust へ変換する。"""
        if call.keywords:
            raise TranspileError("keyword args are not supported")
        args = [self.transpile_expr(a) for a in call.args]
        if isinstance(call.func, ast.Name):
            fn = call.func.id
            if fn in self.class_names:
                return f"{fn}::new({', '.join(args)})"
            if fn == "print":
                if len(args) == 0:
                    return 'println!("")'
                if len(args) == 1:
                    return f"py_print({args[0]})"
                # 複数引数は format! で空白区切り表示
                fmt = " ".join(["{}"] * len(args))
                return f'println!("{fmt}", {", ".join(args)})'
            if fn == "len" and len(args) == 1:
                return f"(py_len(&{args[0]}) as i64)"
            if fn == "int" and len(args) == 1:
                return f"(({args[0]}) as i64)"
            if fn == "float" and len(args) == 1:
                return f"(({args[0]}) as f64)"
            if fn == "str" and len(args) == 1:
                return f"format!(\"{{}}\", {args[0]})"
            if fn == "perf_counter" and len(args) == 0:
                return "perf_counter()"
            if fn == "range":
                raise TranspileError("range() should be used only in for")
            return f"{fn}({', '.join(args)})"
        if isinstance(call.func, ast.Attribute):
            obj = self.transpile_expr(call.func.value)
            method = call.func.attr
            return f"{obj}.{method}({', '.join(args)})"
        raise TranspileError("only direct calls are supported")

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
        op = expr.ops[0]
        if isinstance(op, ast.In):
            return f"py_in(&({r}), &({l}))"
        if isinstance(op, ast.NotIn):
            return f"!py_in(&({r}), &({l}))"
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
            return None
        if isinstance(expr, ast.JoinedStr):
            return "String"
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
            lt = self._expr_type(expr.left)
            rt = self._expr_type(expr.right)
            if lt == "String" or rt == "String":
                return "String"
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
            if expr.func.id in self.class_names:
                return expr.func.id
            if expr.func.id == "str":
                return "String"
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
        "use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};\n\n"
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
