# このファイルは `src/py2cpp.py` の実装コードです。
# Python AST から C++ コードを生成するためのトランスパイラ本体を定義します。
# 変更時は既存仕様との整合性と、生成コードのコンパイル可否を確認してください。

from __future__ import annotations

import argparse
import ast
from pathlib import Path
import sys
from typing import List, Set

try:
    from common.base_transpiler import BaseTranspiler, TranspileError
    from common.transpile_shared import INT32_MAX, INT32_MIN, Scope
    from cpp_type_mappings import CPP_PRIMITIVE_TYPES
except ModuleNotFoundError:
    from src.common.base_transpiler import BaseTranspiler, TranspileError
    from src.common.transpile_shared import INT32_MAX, INT32_MIN, Scope
    from src.cpp_type_mappings import CPP_PRIMITIVE_TYPES


class CppTranspiler(BaseTranspiler):
    """Python AST を C++ ソースコードへ変換する本体クラス。"""

    def __init__(self) -> None:
        """変換時に使う内部状態を初期化する。"""
        super().__init__(temp_prefix="__pytra")
        self.class_names: Set[str] = set()
        self.exception_class_names: Set[str] = set()
        self.current_class_name: str = ""
        self.current_static_fields: Set[str] = set()
        self.global_function_renames: dict[str, str] = {}
        self.wide_int_functions: Set[str] = set()
        self.force_long_int: bool = False

    def transpile_file(self, input_path: Path, output_path: Path) -> None:
        """1ファイルを読み込み、C++へ変換して出力する。

        Args:
            input_path: 変換元 Python ファイルのパス。
            output_path: 変換後 C++ ファイルの出力先パス。
        """
        source = input_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(input_path))
        cpp = self.transpile_module(tree)
        output_path.write_text(cpp, encoding="utf-8")

    def transpile_module(self, module: ast.Module) -> str:
        """モジュールASTをC++コード文字列へ変換する。

        Args:
            module: Python AST の Module ノード。

        Returns:
            変換後の C++ ソースコード全文。
        """
        function_defs: List[str] = []
        class_defs: List[str] = []
        top_level_body: List[ast.stmt] = []
        include_lines: Set[str] = {
            "#include <algorithm>",
            "#include <any>",
            "#include <cstdint>",
            "#include <fstream>",
            "#include <ios>",
            "#include <iostream>",
            "#include <string>",
            "#include <vector>",
            "#include <unordered_map>",
            "#include <unordered_set>",
            "#include <tuple>",
            "#include <sstream>",
            "#include <stdexcept>",
            "#include <type_traits>",
            '#include "cpp_module/gc.h"',
            '#include "cpp_module/py_runtime.h"',
        }
        self.class_names = set()
        self.exception_class_names = set()
        for stmt in module.body:
            if isinstance(stmt, ast.ClassDef):
                self.class_names.add(stmt.name)
                if len(stmt.bases) > 0 and isinstance(stmt.bases[0], ast.Name) and stmt.bases[0].id == "Exception":
                    self.exception_class_names.add(stmt.name)

        self.global_function_renames = {}
        has_top_level_main = any(
            isinstance(stmt, ast.FunctionDef) and stmt.name == "main" for stmt in module.body
        )
        if has_top_level_main:
            self.global_function_renames["main"] = "py_main"
        module_functions = [
            stmt for stmt in module.body if isinstance(stmt, ast.FunctionDef)
        ]
        self.wide_int_functions = self._compute_wide_int_functions(module_functions)

        for stmt in module.body:
            if isinstance(stmt, ast.FunctionDef):
                function_defs.append(self.transpile_function(stmt, False))
            elif isinstance(stmt, ast.ClassDef):
                class_defs.append(self.transpile_class(stmt))
            elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
                include_lines = include_lines.union(self._includes_from_import(stmt))
            else:
                top_level_body.append(stmt)

        main_stmts: List[ast.stmt] = []
        for stmt in top_level_body:
            if self._is_main_guard(stmt):
                main_stmts.extend(stmt.body)
            else:
                main_stmts.append(stmt)

        main_func = self.transpile_main(main_stmts, "main")

        parts = sorted(include_lines)
        parts.append("")
        parts.append("using namespace std;")
        parts.append("using namespace pycs::gc;")
        parts.append("")

        for cls in class_defs:
            parts.extend(cls.splitlines())
            parts.append("")

        for fn in function_defs:
            parts.extend(fn.splitlines())
            parts.append("")

        parts.extend(main_func.splitlines())
        parts.append("")
        return "\n".join(parts)

    def _includes_from_import(self, stmt: ast.stmt) -> Set[str]:
        """import文から必要な C++ include を推定する。

        Args:
            stmt: ast.Import または ast.ImportFrom ノード。

        Returns:
            追加すべき include 行の集合。
        """
        includes: Set[str] = set()
        modules: List[str] = []
        from_import_names: List[str] = []
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                modules.append(alias.name)
        elif isinstance(stmt, ast.ImportFrom):
            if stmt.module:
                modules.append(stmt.module)
            for alias in stmt.names:
                from_import_names.append(alias.name)

        for mod in modules:
            if mod == "math":
                includes.add('#include "cpp_module/math.h"')
            elif mod == "ast":
                includes.add('#include "cpp_module/ast.h"')
            elif mod == "time":
                includes.add('#include "cpp_module/time.h"')
            elif mod == "pathlib":
                includes.add('#include "cpp_module/pathlib.h"')
            elif mod == "png_helper":
                includes.add('#include "cpp_module/png.h"')
            elif mod == "py_module":
                if "png_helper" in from_import_names:
                    includes.add('#include "cpp_module/png.h"')
            elif mod == "py_module.gif_helper":
                includes.add('#include "cpp_module/gif.h"')
            elif mod == "typing":
                includes.add("#include <any>")
            elif mod == "dataclasses":
                includes.add('#include "cpp_module/dataclasses.h"')
        return includes

    def transpile_class(self, cls: ast.ClassDef) -> str:
        """Python class を C++ class 定義へ変換する。

        Args:
            cls: 変換対象の ClassDef ノード。

        Returns:
            C++ class 定義文字列。
        """
        if len(cls.bases) > 1:
            raise TranspileError(f"Class '{cls.name}' multiple inheritance is not supported")

        base: str = " : public pycs::gc::PyObj"
        if len(cls.bases) > 0:
            if not isinstance(cls.bases[0], ast.Name):
                raise TranspileError(f"Class '{cls.name}' base class must be a simple name")
            if cls.bases[0].id == "Exception":
                base = " : public std::exception"
            else:
                base = f" : public {cls.bases[0].id}"

        is_dataclass = self._is_dataclass_class(cls)
        static_fields: List[str] = []
        dataclass_fields: List[tuple[str, str, bool, str]] = []
        static_field_names: Set[str] = set()
        methods: List[ast.FunctionDef] = []

        for stmt in cls.body:
            if isinstance(stmt, ast.FunctionDef):
                methods.append(stmt)
            elif isinstance(stmt, ast.AnnAssign):
                if is_dataclass:
                    dataclass_fields.append(self._transpile_dataclass_field(stmt))
                else:
                    field_line, field_name = self._transpile_class_static_field(stmt)
                    static_fields.append(field_line)
                    static_field_names.add(field_name)
            elif isinstance(stmt, ast.Assign):
                field_line, field_name = self._transpile_class_static_assign(stmt)
                static_fields.append(field_line)
                static_field_names.add(field_name)
            elif (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str)
            ):
                # class docstring
                continue
            elif isinstance(stmt, ast.Pass):
                continue
            else:
                raise TranspileError(f"Unsupported class member in '{cls.name}'")

        instance_fields = self._collect_instance_fields(cls, static_field_names)
        has_init = False
        for method in methods:
            if method.name == "__init__":
                has_init = True
                break

        lines: List[str] = [f"class {cls.name}{base}", "{", "public:"]

        for static_field in static_fields:
            lines.extend(self._indent_block([static_field]))
        for field_type, field_name, has_default, default_value in dataclass_fields:
            if not has_default:
                lines.extend(self._indent_block([f"{field_type} {field_name};"]))
            else:
                lines.extend(self._indent_block([f"{field_type} {field_name} = {default_value};"]))
        for _, field_type, field_name in instance_fields:
            lines.extend(self._indent_block([f"{field_type} {field_name};"]))

        if is_dataclass and len(dataclass_fields) > 0 and not has_init:
            ctor_params: List[str] = []
            ctor_body: List[str] = []
            for field_type, field_name, has_default, default_value in dataclass_fields:
                if not has_default:
                    ctor_params.append(f"{field_type} {field_name}")
                else:
                    ctor_params.append(f"{field_type} {field_name} = {default_value}")
                ctor_body.append(f"this->{field_name} = {field_name};")
            lines.extend(self._indent_block([f"{cls.name}({', '.join(ctor_params)})"]))
            lines.extend(self._indent_block(["{"]))
            lines.extend(self._indent_block(self._indent_block(ctor_body)))
            lines.extend(self._indent_block(["}"]))

        prev_class_name = self.current_class_name
        prev_static_fields = self.current_static_fields
        self.current_class_name = cls.name
        self.current_static_fields = static_field_names
        for method in methods:
            lines.extend(self._indent_block(self.transpile_function(method, True).splitlines()))
        self.current_class_name = prev_class_name
        self.current_static_fields = prev_static_fields

        lines.append("};")
        return "\n".join(lines)

    def _transpile_class_static_field(self, stmt: ast.stmt) -> tuple[str, str]:
        """class本体の型付きメンバー宣言を static メンバーへ変換する。

        Args:
            stmt: クラス本体の AnnAssign ノード。

        Returns:
            (C++宣言行, フィールド名)
        """
        if not isinstance(stmt.target, ast.Name):
            raise TranspileError("Class field declaration must be a simple name")

        field_type = self._map_annotation(stmt.annotation)
        field_name = stmt.target.id
        if stmt.value is None:
            return f"inline static {field_type} {field_name};", field_name
        return f"inline static {field_type} {field_name} = {self.transpile_expr(stmt.value)};", field_name

    def _transpile_dataclass_field(self, stmt: ast.stmt) -> tuple[str, str, bool, str]:
        """dataclass フィールド宣言を C++ メンバー情報へ変換する。

        Args:
            stmt: dataclass 内の AnnAssign ノード。

        Returns:
            (型名, フィールド名, 既定値有無, 既定値文字列)
        """
        if not isinstance(stmt.target, ast.Name):
            raise TranspileError("Dataclass field declaration must be a simple name")
        field_type = self._map_annotation(stmt.annotation)
        field_name = stmt.target.id
        if stmt.value is None:
            return field_type, field_name, False, ""
        return field_type, field_name, True, self.transpile_expr(stmt.value)

    def _transpile_class_static_assign(self, stmt: ast.stmt) -> tuple[str, str]:
        """class本体の代入を static メンバー定義へ変換する。

        Args:
            stmt: クラス本体の Assign ノード。

        Returns:
            (C++宣言行, フィールド名)
        """
        if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            raise TranspileError("Class static assignment must be a simple name assignment")
        field_name = stmt.targets[0].id
        field_type = self._infer_expr_cpp_type(stmt.value)
        if field_type == "":
            field_type = "auto"
        return f"inline static {field_type} {field_name} = {self.transpile_expr(stmt.value)};", field_name

    def _collect_instance_fields(
        self, cls: ast.stmt, static_field_names: Set[str]
    ) -> List[tuple[str, str, str]]:
        """__init__ からインスタンスフィールド候補を抽出する。

        Args:
            cls: 解析対象クラス。
            static_field_names: static 扱い済みフィールド名の集合。

        Returns:
            (クラス名, 型名, フィールド名) の一覧。
        """
        fields: List[tuple[str, str, str]] = []
        seen: Set[str] = set()

        for stmt in cls.body:
            if isinstance(stmt, ast.FunctionDef):
                init_fn = stmt
                if init_fn.name != "__init__":
                    continue
                arg_types: dict[str, str] = {}
                idx = 0
                for arg in init_fn.args.args:
                    if idx == 0 and arg.arg == "self":
                        idx = idx + 1
                        continue
                    if arg.annotation is not None:
                        arg_types[arg.arg] = self._map_annotation(arg.annotation)
                    idx = idx + 1

                for init_stmt in init_fn.body:
                    field_name: str = ""
                    field_type: str = ""
                    if isinstance(init_stmt, ast.AnnAssign):
                        target_expr = init_stmt.target
                        if isinstance(target_expr, ast.Attribute):
                            attr_target = target_expr
                            if isinstance(attr_target.value, ast.Name) and attr_target.value.id == "self":
                                field_name = attr_target.attr
                                field_type = self._map_annotation(init_stmt.annotation)
                    elif isinstance(init_stmt, ast.Assign):
                        if len(init_stmt.targets) == 1:
                            target_expr = init_stmt.targets[0]
                            if not isinstance(target_expr, ast.Attribute):
                                continue
                            attr_target = target_expr
                            if isinstance(attr_target.value, ast.Name) and attr_target.value.id == "self":
                                field_name = attr_target.attr
                                field_type = self._infer_type(init_stmt.value, arg_types)

                    if field_name == "" or field_type == "":
                        continue
                    if field_name in static_field_names:
                        continue
                    if field_name in seen:
                        continue
                    seen.add(field_name)
                    fields.append((cls.name, field_type, field_name))
                return fields

        return fields

    def _infer_type(self, expr: ast.expr, arg_types: dict[str, str]) -> str:
        """式から C++ 型を推定する。

        Args:
            expr: 推定対象の式ノード。
            arg_types: 引数名 -> 型名の対応表。
        """
        if isinstance(expr, ast.Name):
            if expr.id in arg_types:
                return arg_types[expr.id]
            return ""
        if isinstance(expr, ast.Constant):
            return self._infer_expr_cpp_type(expr)
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
            if expr.func.id in self.class_names:
                return f"pycs::gc::RcHandle<{expr.func.id}>"
        return ""

    def _infer_expr_cpp_type(self, expr: ast.expr) -> str:
        """リテラル式から C++ 基本型を推定する。"""
        def merge_types(types: List[str], fallback: str = "auto") -> str:
            if len(types) == 0:
                return fallback
            first = types[0]
            if all(t == first for t in types):
                return first
            number_types = {"int", "long long", "double"}
            if all(t in number_types for t in types):
                return "double"
            return fallback

        if isinstance(expr, ast.Constant):
            if isinstance(expr.value, bool):
                return "bool"
            if isinstance(expr.value, int):
                return "long long"
            if isinstance(expr.value, float):
                return "double"
            if isinstance(expr.value, str):
                return "string"
            return ""
        if isinstance(expr, ast.List):
            item_types: List[str] = []
            for item in expr.elts:
                t = self._infer_expr_cpp_type(item)
                if t != "":
                    item_types.append(t)
            inner = merge_types(item_types, "long long")
            return f"vector<{inner}>"
        if isinstance(expr, ast.Set):
            item_types = []
            for item in expr.elts:
                t = self._infer_expr_cpp_type(item)
                if t != "":
                    item_types.append(t)
            inner = merge_types(item_types, "long long")
            return f"unordered_set<{inner}>"
        if isinstance(expr, ast.Dict):
            key_types: List[str] = []
            value_types: List[str] = []
            for key, value in zip(expr.keys, expr.values):
                if key is None:
                    continue
                kt = self._infer_expr_cpp_type(key)
                vt = self._infer_expr_cpp_type(value)
                if kt != "":
                    key_types.append(kt)
                if vt != "":
                    value_types.append(vt)
            key_type = merge_types(key_types, "string")
            val_type = merge_types(value_types, "long long")
            return f"unordered_map<{key_type}, {val_type}>"
        if isinstance(expr, ast.BinOp):
            if isinstance(expr.op, (ast.Div, ast.Pow)):
                return "double"
            lt = self._infer_expr_cpp_type(expr.left)
            rt = self._infer_expr_cpp_type(expr.right)
            return merge_types([t for t in (lt, rt) if t != ""], "auto")
        if isinstance(expr, ast.UnaryOp):
            return self._infer_expr_cpp_type(expr.operand)
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
            if expr.func.id in {"len"}:
                return "size_t"
            if expr.func.id in {"int"}:
                return "long long"
            if expr.func.id in {"float"}:
                return "double"
            if expr.func.id in {"str"}:
                return "string"
            if expr.func.id in {"bytearray", "bytes"}:
                return "vector<uint8_t>"
        return ""

    def transpile_function(self, fn: ast.FunctionDef, in_class: bool = False) -> str:
        """関数/メソッド定義を C++ の関数定義へ変換する。

        Args:
            fn: 変換対象の FunctionDef ノード。
            in_class: クラス内メソッドかどうか。
        """
        is_constructor = in_class and fn.name == "__init__"
        prev_force_long_int = self.force_long_int
        self.force_long_int = fn.name in self.wide_int_functions or self._requires_wide_int(fn)
        try:
            return_type = self._map_annotation(fn.returns)
            params: List[str] = []
            declared: Set[str] = set()

            idx = 0
            for arg in fn.args.args:
                if in_class and idx == 0 and arg.arg == "self":
                    declared.add("self")
                    idx = idx + 1
                    continue
                mapped = self._map_annotation(arg.annotation)
                if self._should_pass_by_const_ref(mapped) and not self._is_param_mutated(fn, arg.arg):
                    params.append(f"const {mapped}& {arg.arg}")
                else:
                    params.append(f"{mapped} {arg.arg}")
                declared.add(arg.arg)
                idx = idx + 1

            body_lines = self.transpile_statements(fn.body, Scope(declared=declared))
            if is_constructor:
                if self.current_class_name == "":
                    raise TranspileError("Constructor conversion requires class context")
                if return_type != "void":
                    raise TranspileError("__init__ return type must be None")
                lines: List[str] = [f"{self.current_class_name}({', '.join(params)})", "{"]
                lines.extend(self._indent_block(body_lines))
                lines.append("}")
                return "\n".join(lines)

            fn_name = fn.name
            if not in_class and fn_name in self.global_function_renames:
                fn_name = self.global_function_renames[fn_name]
            lines: List[str] = [f"{return_type} {fn_name}({', '.join(params)})", "{"]
            lines.extend(self._indent_block(body_lines))
            lines.append("}")
            return "\n".join(lines)
        finally:
            self.force_long_int = prev_force_long_int

    def _should_pass_by_const_ref(self, cpp_type: str) -> bool:
        """コピーコストが高い型を const 参照渡しにするか判定する。"""
        if cpp_type == "string":
            return True
        heavy_prefixes = ("vector<", "unordered_set<", "unordered_map<", "tuple<")
        for prefix in heavy_prefixes:
            if cpp_type.startswith(prefix):
                return True
        return False

    def _is_param_mutated(self, fn: ast.FunctionDef, param_name: str) -> bool:
        """関数内で引数が直接変更されるかを判定する。"""
        mutating_methods = {
            "append",
            "extend",
            "clear",
            "insert",
            "pop",
            "remove",
            "sort",
            "reverse",
            "update",
            "add",
            "discard",
            "setdefault",
        }

        for node in ast.walk(fn):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if self._is_write_target_of_param(t, param_name):
                        return True
            elif isinstance(node, ast.AnnAssign):
                if self._is_write_target_of_param(node.target, param_name):
                    return True
            elif isinstance(node, ast.AugAssign):
                if self._is_write_target_of_param(node.target, param_name):
                    return True
            elif isinstance(node, ast.Delete):
                for t in node.targets:
                    if self._is_write_target_of_param(t, param_name):
                        return True
            elif isinstance(node, ast.For):
                if self._contains_name(node.target, param_name):
                    return True
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == param_name:
                    if node.func.attr in mutating_methods:
                        return True
        return False

    def _is_write_target_of_param(self, target: ast.expr, param_name: str) -> bool:
        """代入先が引数自身またはその要素/属性かを判定する。"""
        if isinstance(target, ast.Name):
            return target.id == param_name
        if isinstance(target, ast.Attribute):
            return self._root_name(target) == param_name
        if isinstance(target, ast.Subscript):
            return self._root_name(target.value) == param_name
        if isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                if self._is_write_target_of_param(elt, param_name):
                    return True
        return False

    def _root_name(self, expr: ast.expr) -> str:
        """属性/添字式の最も根の Name を返す。"""
        cur = expr
        while True:
            if isinstance(cur, ast.Name):
                return cur.id
            if isinstance(cur, ast.Attribute):
                cur = cur.value
                continue
            if isinstance(cur, ast.Subscript):
                cur = cur.value
                continue
            return ""

    def _contains_name(self, expr: ast.expr, name: str) -> bool:
        """式に指定名が含まれるかを判定する。"""
        for node in ast.walk(expr):
            if isinstance(node, ast.Name) and node.id == name:
                return True
        return False

    def transpile_main(self, body: List[ast.stmt], entry_name: str = "main") -> str:
        """トップレベル文を C++ の main 関数へ変換する。"""
        lines: List[str] = [f"int {entry_name}()", "{"]
        body_lines = self.transpile_statements(body, Scope(declared=set()))
        lines.extend(self._indent_block(body_lines))
        lines.extend(self._indent_block(["return 0;"]))
        lines.append("}")
        return "\n".join(lines)

    def transpile_statements(self, stmts: List[ast.stmt], scope: Scope) -> List[str]:
        """文ノード列を C++ 文へ変換するディスパッチャ。"""
        lines: List[str] = []

        for stmt in stmts:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                continue
            if (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str)
            ):
                # docstring を実行文としては出力しない
                continue
            if isinstance(stmt, ast.Return):
                if stmt.value is None:
                    lines.append("return;")
                else:
                    lines.append(f"return {self.transpile_expr(stmt.value)};")
            elif isinstance(stmt, ast.Expr):
                expr = self.transpile_expr(stmt.value)
                lines.append(f"{expr};")
            elif isinstance(stmt, ast.AnnAssign):
                lines.extend(self._transpile_ann_assign(stmt, scope))
            elif isinstance(stmt, ast.Assign):
                lines.extend(self._transpile_assign(stmt, scope))
            elif isinstance(stmt, ast.AugAssign):
                lines.extend(self._transpile_aug_assign(stmt))
            elif isinstance(stmt, ast.If):
                lines.extend(self._transpile_if(stmt, scope))
            elif isinstance(stmt, ast.For):
                lines.extend(self._transpile_for(stmt, scope))
            elif isinstance(stmt, ast.While):
                lines.extend(self._transpile_while(stmt, scope))
            elif isinstance(stmt, ast.Try):
                lines.extend(self._transpile_try(stmt, scope))
            elif isinstance(stmt, ast.Raise):
                lines.extend(self._transpile_raise(stmt))
            elif isinstance(stmt, ast.Break):
                lines.append("break;")
            elif isinstance(stmt, ast.Continue):
                lines.append("continue;")
            elif isinstance(stmt, ast.Pass):
                continue
            else:
                raise TranspileError("Unsupported statement")

        return lines

    def _transpile_ann_assign(self, stmt: ast.stmt, scope: Scope) -> List[str]:
        """型注釈付き代入文を C++ 宣言/代入へ変換する。"""
        target_expr = stmt.target
        if isinstance(target_expr, ast.Attribute):
            attr_target = target_expr
            if isinstance(attr_target.value, ast.Name) and attr_target.value.id == "self":
                if stmt.value is None:
                    raise TranspileError(
                        "Annotated assignment to self attributes requires an initializer"
                    )
                return [f"{self.transpile_expr(attr_target)} = {self.transpile_expr(stmt.value)};"]
            raise TranspileError("Annotated assignment to attributes is not supported")
        if not isinstance(stmt.target, ast.Name):
            raise TranspileError("Only simple annotated assignments are supported")

        name = stmt.target.id
        cpp_type = self._map_annotation(stmt.annotation)
        if stmt.value is None:
            scope.declared.add(name)
            return [f"{cpp_type} {name};"]
        scope.declared.add(name)
        return [f"{cpp_type} {name} = {self.transpile_expr(stmt.value)};"]

    def _transpile_assign(self, stmt: ast.stmt, scope: Scope) -> List[str]:
        """通常の代入文を C++ 代入へ変換する。"""
        if len(stmt.targets) != 1:
            return ["// unsupported assignment"]
        if isinstance(stmt.targets[0], ast.Tuple):
            tuple_target = stmt.targets[0]
            for elt in tuple_target.elts:
                if not isinstance(elt, ast.Name):
                    return ["// unsupported tuple assignment"]
            tmp_name = self._new_temp("tuple")
            lines: List[str] = [f"auto {tmp_name} = {self.transpile_expr(stmt.value)};"]
            i = 0
            for elt in tuple_target.elts:
                name = elt.id
                if name not in scope.declared:
                    scope.declared.add(name)
                    lines.append(f"auto {name} = std::get<{i}>({tmp_name});")
                else:
                    lines.append(f"{name} = std::get<{i}>({tmp_name});")
                i = i + 1
            return lines
        if isinstance(stmt.targets[0], ast.Attribute):
            target = self.transpile_expr(stmt.targets[0])
            return [f"{target} = {self.transpile_expr(stmt.value)};"]
        if isinstance(stmt.targets[0], ast.Subscript):
            target = self.transpile_expr(stmt.targets[0])
            return [f"{target} = {self.transpile_expr(stmt.value)};"]
        if not isinstance(stmt.targets[0], ast.Name):
            return ["// unsupported assignment"]

        name = stmt.targets[0].id
        if name not in scope.declared:
            scope.declared.add(name)
            inferred = self._infer_expr_cpp_type(stmt.value)
            if inferred != "" and inferred != "auto":
                return [f"{inferred} {name} = {self.transpile_expr(stmt.value)};"]
            return [f"auto {name} = {self.transpile_expr(stmt.value)};"]

        return [f"{name} = {self.transpile_expr(stmt.value)};"]

    def _transpile_aug_assign(self, stmt: ast.AugAssign) -> List[str]:
        """拡張代入文を C++ の通常代入へ展開する。"""
        target = self.transpile_expr(stmt.target)
        value = self.transpile_expr(stmt.value)
        if isinstance(stmt.op, ast.Pow):
            return [f"{target} = py_pow({target}, {value});"]
        if isinstance(stmt.op, ast.Div):
            return [f"{target} = py_div({target}, {value});"]
        if isinstance(stmt.op, ast.FloorDiv):
            return [f"{target} = py_floordiv({target}, {value});"]
        op = self._binop(stmt.op)
        return [f"{target} = ({target} {op} {value});"]

    def _transpile_for(self, stmt: ast.For, scope: Scope) -> List[str]:
        """for 文を range-for 形式へ変換する。"""
        tuple_names: List[str] = []
        target_name: str = ""
        if isinstance(stmt.target, ast.Name):
            target_name = stmt.target.id
        elif isinstance(stmt.target, ast.Tuple):
            only_names = True
            for elt in stmt.target.elts:
                if not isinstance(elt, ast.Name):
                    only_names = False
                    break
            if only_names:
                target_name = "_for_item"
                for elt in stmt.target.elts:
                    tuple_names.append(elt.id)
            else:
                return ["// unsupported for-loop target"]
        else:
            return ["// unsupported for-loop target"]

        lines: List[str] = []
        body_scope = Scope(declared=set(scope.declared))
        range_args = self._parse_range_args(stmt.iter)
        if range_args is not None and len(tuple_names) == 0:
            start_expr, stop_expr, step_expr = range_args
            start_var = self._new_temp("range_start")
            stop_var = self._new_temp("range_stop")
            step_var = self._new_temp("range_step")
            lines.append(f"auto {start_var} = {start_expr};")
            lines.append(f"auto {stop_var} = {stop_expr};")
            lines.append(f"auto {step_var} = {step_expr};")
            lines.append(f"if ({step_var} == 0) throw std::runtime_error(\"range() arg 3 must not be zero\");")
            if target_name != "_" and target_name in scope.declared:
                init_part = f"{target_name} = {start_var}"
            else:
                init_part = f"auto {target_name} = {start_var}"
                body_scope.declared.add(target_name)
            lines.append(
                f"for ({init_part}; "
                f"({step_var} > 0) ? ({target_name} < {stop_var}) : ({target_name} > {stop_var}); "
                f"{target_name} += {step_var})"
            )
            lines.append("{")
        else:
            lines.extend([f"for (const auto& {target_name} : {self.transpile_expr(stmt.iter)})", "{"])
            body_scope.declared.add(target_name)

        if len(tuple_names) > 0:
            i = 0
            for elt_name in tuple_names:
                lines.extend(self._indent_block([f"auto {elt_name} = std::get<{i}>({target_name});"]))
                body_scope.declared.add(elt_name)
                i = i + 1
        body_lines = self.transpile_statements(stmt.body, body_scope)
        lines.extend(self._indent_block(body_lines))
        lines.append("}")
        if len(stmt.orelse) > 0:
            lines.append("// for-else is not directly supported; else body emitted below")
            lines.extend(self.transpile_statements(stmt.orelse, Scope(declared=set(scope.declared))))
        return lines

    def _transpile_while(self, stmt: ast.While, scope: Scope) -> List[str]:
        """while 文を C++ while 文へ変換する。"""
        lines: List[str] = [f"while ({self.transpile_expr(stmt.test)})", "{"]
        body_lines = self.transpile_statements(stmt.body, Scope(declared=set(scope.declared)))
        lines.extend(self._indent_block(body_lines))
        lines.append("}")
        if len(stmt.orelse) > 0:
            lines.append("// while-else is not directly supported; else body emitted below")
            lines.extend(self.transpile_statements(stmt.orelse, Scope(declared=set(scope.declared))))
        return lines

    def _transpile_try(self, stmt: ast.Try, scope: Scope) -> List[str]:
        """try 文を C++ try/catch へ変換する。"""
        lines: List[str] = ["try", "{"]
        lines.extend(self._indent_block(self.transpile_statements(stmt.body, Scope(declared=set(scope.declared)))))
        lines.append("}")

        for handler in stmt.handlers:
            ex_type: str = "std::exception"
            if handler.type is not None:
                if isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
                    ex_type = "std::exception"
                else:
                    ex_type = self.transpile_expr(handler.type)
            ex_name: str = "ex"
            if handler.name != "":
                ex_name = handler.name
            lines.append(f"catch (const {ex_type}& {ex_name})")
            lines.append("{")
            handler_declared = set(scope.declared)
            handler_declared.add(ex_name)
            handler_scope = Scope(declared=handler_declared)
            lines.extend(self._indent_block(self.transpile_statements(handler.body, handler_scope)))
            lines.append("}")

        if len(stmt.finalbody) > 0:
            lines.append("// finally is not directly supported in C++; emitted as plain block")
            lines.append("{")
            lines.extend(
                self._indent_block(
                    self.transpile_statements(stmt.finalbody, Scope(declared=set(scope.declared)))
                )
            )
            lines.append("}")

        if len(stmt.orelse) > 0:
            lines.append("// try-else is not directly supported; else body emitted below")
            lines.extend(self.transpile_statements(stmt.orelse, Scope(declared=set(scope.declared))))

        return lines

    def _transpile_raise(self, stmt: ast.Raise) -> List[str]:
        """raise 文を std::runtime_error の throw へ変換する。"""
        if stmt.exc is None:
            return ["throw;"]
        if isinstance(stmt.exc, ast.Call) and len(stmt.exc.args) > 0:
            return [f"throw std::runtime_error(py_to_string({self.transpile_expr(stmt.exc.args[0])}));"]
        return [f"throw std::runtime_error(py_to_string({self.transpile_expr(stmt.exc)}));"]

    def _transpile_if(self, stmt: ast.If, scope: Scope) -> List[str]:
        """if 文を C++ if/else へ変換する。"""
        cast_var: str = ""
        cast_type: str = ""
        if (
            isinstance(stmt.test, ast.Call)
            and isinstance(stmt.test.func, ast.Name)
            and stmt.test.func.id == "isinstance"
            and len(stmt.test.args) == 2
            and isinstance(stmt.test.args[0], ast.Name)
            and len(stmt.test.keywords) == 0
        ):
            cast_var = stmt.test.args[0].id
            type_arg = stmt.test.args[1]
            if isinstance(type_arg, ast.Attribute) and isinstance(type_arg.value, ast.Name):
                cast_type = self.transpile_expr(type_arg)
            elif isinstance(type_arg, ast.Name):
                if type_arg.id in self.class_names:
                    cast_type = type_arg.id

        lines: List[str] = []
        if cast_var != "" and cast_type != "":
            lines.append(f"if (auto __cast_{cast_var} = py_cast<{cast_type}>({cast_var}))")
            lines.append("{")
        else:
            lines.append(f"if ({self.transpile_expr(stmt.test)})")
            lines.append("{")
        then_lines: List[str] = self.transpile_statements(stmt.body, Scope(declared=set(scope.declared)))
        if cast_var != "" and cast_type != "":
            prefixed_then_lines: List[str] = [f"auto {cast_var} = __cast_{cast_var};"]
            prefixed_then_lines.extend(then_lines)
            then_lines = prefixed_then_lines
        lines.extend(self._indent_block(then_lines))
        lines.append("}")

        if len(stmt.orelse) > 0:
            lines.append("else")
            lines.append("{")
            else_lines = self.transpile_statements(stmt.orelse, Scope(declared=set(scope.declared)))
            lines.extend(self._indent_block(else_lines))
            lines.append("}")

        return lines

    def transpile_expr(self, expr: ast.expr) -> str:
        """式ノードを C++ 式文字列へ変換する。"""
        if isinstance(expr, ast.Name):
            if expr.id == "self":
                return "this"
            if expr.id == "True":
                return "true"
            if expr.id == "False":
                return "false"
            return expr.id
        if isinstance(expr, ast.Attribute):
            if isinstance(expr.value, ast.Name) and expr.value.id == "ast":
                return f"pycs::cpp_module::ast::{expr.attr}"
            if isinstance(expr.value, ast.Name) and expr.value.id == "math":
                return f"pycs::cpp_module::math::{expr.attr}"
            if isinstance(expr.value, ast.Name) and expr.value.id == "time":
                return f"pycs::cpp_module::{expr.attr}"
            if isinstance(expr.value, ast.Name) and expr.value.id == "png_helper":
                return f"pycs::cpp_module::png::{expr.attr}"
            if (
                isinstance(expr.value, ast.Name)
                and expr.value.id == "self"
                and self.current_class_name != ""
                and expr.attr in self.current_static_fields
            ):
                return f"{self.current_class_name}::{expr.attr}"
            if isinstance(expr.value, ast.Name) and expr.value.id == "self":
                return f"this->{expr.attr}"
            if isinstance(expr.value, ast.Name) and expr.value.id in self.class_names:
                return f"{expr.value.id}::{expr.attr}"
            return f"{self.transpile_expr(expr.value)}->{expr.attr}"
        if isinstance(expr, ast.Constant):
            return self._constant(expr.value)
        if isinstance(expr, ast.List):
            items: List[str] = []
            for e in expr.elts:
                items.append(self.transpile_expr(e))
            return "{" + ", ".join(items) + "}"
        if isinstance(expr, ast.Set):
            items: List[str] = []
            for e in expr.elts:
                items.append(self.transpile_expr(e))
            return "{" + ", ".join(items) + "}"
        if isinstance(expr, ast.Tuple):
            items: List[str] = []
            for e in expr.elts:
                items.append(self.transpile_expr(e))
            return f"std::make_tuple({', '.join(items)})"
        if isinstance(expr, ast.Dict):
            entries: List[str] = []
            for k, v in zip(expr.keys, expr.values):
                if k is None:
                    continue
                entries.append(f"{{ {self.transpile_expr(k)}, {self.transpile_expr(v)} }}")
            return "{" + ", ".join(entries) + "}"
        if isinstance(expr, ast.BinOp):
            left = self.transpile_expr(expr.left)
            right = self.transpile_expr(expr.right)
            if isinstance(expr.op, ast.Pow):
                return f"py_pow({left}, {right})"
            if isinstance(expr.op, ast.Div):
                return f"py_div({left}, {right})"
            if isinstance(expr.op, ast.FloorDiv):
                return f"py_floordiv({left}, {right})"
            return f"({left} {self._binop(expr.op)} {right})"
        if isinstance(expr, ast.UnaryOp):
            return f"({self._unaryop(expr.op)}{self.transpile_expr(expr.operand)})"
        if isinstance(expr, ast.BoolOp):
            op = self._boolop(expr.op)
            values: List[str] = []
            for v in expr.values:
                values.append(self.transpile_expr(v))
            return "(" + f" {op} ".join(values) + ")"
        if isinstance(expr, ast.Compare):
            if len(expr.ops) == 1 and len(expr.comparators) == 1:
                return self._transpile_compare(expr.left, expr.ops[0], expr.comparators[0])
            return self._transpile_chained_compare(expr)
        if isinstance(expr, ast.Call):
            return self._transpile_call(expr)
        if isinstance(expr, ast.Subscript):
            if isinstance(expr.slice, ast.Slice):
                if expr.slice.step is not None:
                    raise TranspileError("Slice step is not supported yet")
                if expr.slice.lower is None or expr.slice.upper is None:
                    raise TranspileError("Only slice form a[b:c] is supported")
                has_start = "true"
                start_expr = self.transpile_expr(expr.slice.lower)
                has_stop = "true"
                stop_expr = self.transpile_expr(expr.slice.upper)
                return (
                    f"py_slice({self.transpile_expr(expr.value)}, "
                    f"{has_start}, {start_expr}, {has_stop}, {stop_expr})"
                )
            return f"{self.transpile_expr(expr.value)}[{self.transpile_expr(expr.slice)}]"
        if isinstance(expr, ast.IfExp):
            return (
                f"({self.transpile_expr(expr.test)} ? {self.transpile_expr(expr.body)} : "
                f"{self.transpile_expr(expr.orelse)})"
            )
        if isinstance(expr, ast.JoinedStr):
            return self._transpile_joined_str(expr)
        if isinstance(expr, ast.ListComp):
            return self._transpile_list_comp(expr)
        if isinstance(expr, ast.SetComp):
            return self._transpile_set_comp(expr)
        if isinstance(expr, ast.GeneratorExp):
            return self._transpile_gen_comp(expr)
        try:
            return self._raw_expr_to_cpp(expr.as_text())
        except Exception:
            pass

        raise TranspileError("Unsupported expression")

    def _transpile_call(self, call: ast.expr) -> str:
        """関数呼び出し式を C++ 呼び出し式へ変換する。"""
        args_list: List[str] = []
        for arg in call.args:
            args_list.append(self.transpile_expr(arg))
        for kw in call.keywords:
            args_list.append(self.transpile_expr(kw.value))
        args = ", ".join(args_list)

        if isinstance(call.func, ast.Name) and call.func.id == "print":
            if len(args_list) == 0:
                return "py_print()"
            return f"py_print({args})"
        if isinstance(call.func, ast.Name) and call.func.id == "len":
            return f"py_len({args})"
        if isinstance(call.func, ast.Name) and call.func.id == "sorted":
            return f"py_sorted({args})"
        if isinstance(call.func, ast.Name) and call.func.id == "zip":
            if len(args_list) == 2:
                return f"py_zip({args_list[0]}, {args_list[1]})"
            return "vector<tuple<int, int>>{}"
        if isinstance(call.func, ast.Name) and call.func.id == "set":
            if len(args_list) == 0:
                return "unordered_set<string>{}"
            return (
                "unordered_set<std::remove_cvref_t<decltype(*"
                + f"{args_list[0]}.begin())>>({args_list[0]}.begin(), {args_list[0]}.end())"
            )
        if isinstance(call.func, ast.Name) and call.func.id == "str":
            if len(call.args) == 1:
                return f"py_to_string({args_list[0]})"
            return "\"\""
        if isinstance(call.func, ast.Name) and call.func.id == "int":
            if len(call.args) == 1:
                return f"static_cast<long long>({args_list[0]})"
            return "0"
        if isinstance(call.func, ast.Name) and call.func.id == "float":
            if len(call.args) == 1:
                return f"static_cast<double>({args_list[0]})"
            return "0.0"
        if isinstance(call.func, ast.Name) and call.func.id == "pow":
            if len(args_list) == 2:
                return f"py_pow({args_list[0]}, {args_list[1]})"
            return "0.0"
        if isinstance(call.func, ast.Name) and call.func.id == "open":
            if len(args_list) >= 2:
                if isinstance(call.args[1], ast.Constant) and isinstance(call.args[1].value, str):
                    mode = call.args[1].value
                    if "b" in mode:
                        return f"std::make_shared<std::ofstream>({args_list[0]}, std::ios::binary)"
                return f"std::make_shared<std::ofstream>({args_list[0]})"
            return "std::make_shared<std::ofstream>()"
        if isinstance(call.func, ast.Name) and call.func.id == "bytearray":
            if len(args_list) == 0:
                return "py_bytearray()"
            if len(args_list) == 1:
                return f"py_bytearray({args_list[0]})"
            return "py_bytearray()"
        if isinstance(call.func, ast.Name) and call.func.id == "bytes":
            if len(args_list) == 1:
                return f"py_bytes({args_list[0]})"
            return "py_bytes()"
        if isinstance(call.func, ast.Name) and call.func.id == "save_gif":
            return f"pycs::cpp_module::gif::save_gif({args})"
        if isinstance(call.func, ast.Name) and call.func.id == "grayscale_palette":
            return f"pycs::cpp_module::gif::grayscale_palette({args})"
        if isinstance(call.func, ast.Name) and call.func.id == "chr":
            if len(args_list) == 1:
                return f"string(1, static_cast<char>({args_list[0]}))"
            return '""'
        if isinstance(call.func, ast.Name) and call.func.id == "ord":
            if len(args_list) == 1:
                return f"py_ord({args_list[0]})"
            return "0"
        if isinstance(call.func, ast.Name) and call.func.id == "isinstance":
            if len(call.args) == 2:
                obj = self.transpile_expr(call.args[0])
                type_arg = call.args[1]
                if isinstance(type_arg, ast.Tuple):
                    types: List[str] = []
                    for elt in type_arg.elts:
                        if isinstance(elt, ast.Attribute) and isinstance(elt.value, ast.Name) and elt.value.id == "ast":
                            types.append(f"pycs::cpp_module::ast::{elt.attr}")
                        elif isinstance(elt, ast.Name):
                            types.append(elt.id)
                    if len(types) > 0:
                        return f"py_isinstance_any<decltype({obj}), {', '.join(types)}>({obj})"
                if isinstance(type_arg, ast.Attribute) and isinstance(type_arg.value, ast.Name) and type_arg.value.id == "ast":
                    return f"py_isinstance<pycs::cpp_module::ast::{type_arg.attr}>({obj})"
                if isinstance(type_arg, ast.Name):
                    if type_arg.id == "str":
                        return f"py_isinstance<string>({obj})"
                    return f"py_isinstance<{type_arg.id}>({obj})"
            return "false"

        if isinstance(call.func, ast.Name):
            if call.func.id in self.global_function_renames:
                mapped_name = self.global_function_renames[call.func.id]
                return f"{mapped_name}({args})"
            if call.func.id in self.class_names and call.func.id not in self.exception_class_names:
                return f"pycs::gc::RcHandle<{call.func.id}>::adopt(pycs::gc::rc_new<{call.func.id}>({args}))"
            return f"{call.func.id}({args})"
        if isinstance(call.func, ast.Attribute):
            obj = self.transpile_expr(call.func.value)
            method = call.func.attr
            if method == "append" and len(args_list) == 1:
                return f"{obj}.push_back({args_list[0]})"
            if method == "pop" and len(args_list) == 0:
                return f"py_pop({obj})"
            if method == "pop" and len(args_list) == 1:
                return f"py_pop({obj}, {args_list[0]})"
            if method == "extend" and len(args_list) == 1:
                return f"py_extend({obj}, {args_list[0]})"
            if method == "add" and len(args_list) == 1:
                return f"{obj}.insert({args_list[0]})"
            if method == "union" and len(args_list) == 1:
                return f"py_set_union({obj}, {args_list[0]})"
            if method == "splitlines":
                return f"py_splitlines({obj})"
            if method == "join" and len(args_list) == 1:
                return f"py_join({obj}, {args_list[0]})"
            if method == "replace" and len(args_list) == 2:
                return f"py_replace({obj}, {args_list[0]}, {args_list[1]})"
            if method == "isdigit" and len(args_list) == 0:
                return f"py_isdigit({obj})"
            if method == "isalpha" and len(args_list) == 0:
                return f"py_isalpha({obj})"
            if method == "write" and len(args_list) == 1:
                return f"py_write(*{obj}, {args_list[0]})"
            if method == "close" and len(args_list) == 0:
                return f"{obj}->close()"
            if method == "encode":
                return obj
            return f"{self.transpile_expr(call.func)}({args})"

        raise TranspileError("Only direct function calls are supported")

    def _map_annotation(self, annotation: ast.expr) -> str:
        """Python 型注釈を C++ 型名へ変換する。"""
        if isinstance(annotation, ast.Constant) and annotation.value is None:
            return "void"
        if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
            left = self._map_annotation(annotation.left)
            right = self._map_annotation(annotation.right)
            if left == "void":
                return right
            if right == "void":
                return left
            return "auto"
        if isinstance(annotation, ast.Name):
            if annotation.id in CPP_PRIMITIVE_TYPES:
                return CPP_PRIMITIVE_TYPES[annotation.id]
            if annotation.id == "bytearray":
                return "vector<uint8_t>"
            if annotation.id == "bytes":
                return "vector<uint8_t>"
            if annotation.id in self.class_names:
                return f"pycs::gc::RcHandle<{annotation.id}>"
            return "auto"
        if isinstance(annotation, ast.Attribute):
            if isinstance(annotation.value, ast.Name) and annotation.value.id == "ast":
                if annotation.attr == "Module":
                    return "pycs::cpp_module::ast::ModulePtr"
                if annotation.attr == "stmt":
                    return "pycs::cpp_module::ast::StmtPtr"
                if annotation.attr == "expr":
                    return "pycs::cpp_module::ast::ExprPtr"
                if annotation.attr == "FunctionDef":
                    return "std::shared_ptr<pycs::cpp_module::ast::FunctionDef>"
                if annotation.attr == "ClassDef":
                    return "std::shared_ptr<pycs::cpp_module::ast::ClassDef>"
                if annotation.attr == "Assign":
                    return "std::shared_ptr<pycs::cpp_module::ast::Assign>"
                if annotation.attr == "AnnAssign":
                    return "std::shared_ptr<pycs::cpp_module::ast::AnnAssign>"
                if annotation.attr == "For":
                    return "std::shared_ptr<pycs::cpp_module::ast::For>"
                if annotation.attr == "If":
                    return "std::shared_ptr<pycs::cpp_module::ast::If>"
                if annotation.attr == "Try":
                    return "std::shared_ptr<pycs::cpp_module::ast::Try>"
                if annotation.attr == "Raise":
                    return "std::shared_ptr<pycs::cpp_module::ast::Raise>"
                if annotation.attr == "Call":
                    return "std::shared_ptr<pycs::cpp_module::ast::Call>"
                if annotation.attr == "JoinedStr":
                    return "std::shared_ptr<pycs::cpp_module::ast::JoinedStr>"
                if annotation.attr == "boolop":
                    return "std::shared_ptr<pycs::cpp_module::ast::boolop>"
                if annotation.attr == "cmpop":
                    return "std::shared_ptr<pycs::cpp_module::ast::cmpop>"
                if annotation.attr == "unaryop":
                    return "std::shared_ptr<pycs::cpp_module::ast::unaryop>"
                if annotation.attr == "operator":
                    return "std::shared_ptr<pycs::cpp_module::ast::operator_>"
                return "auto"
            return "auto"
        if isinstance(annotation, ast.Subscript):
            raw_base: str = ""
            if isinstance(annotation.value, ast.Name):
                raw_base = annotation.value.id
            elif isinstance(annotation.value, ast.Attribute):
                raw_base = self.transpile_expr(annotation.value)
            else:
                return "auto"
            base: str = ""
            if raw_base == "list" or raw_base == "List":
                base = "vector"
            elif raw_base == "set" or raw_base == "Set":
                base = "unordered_set"
            elif raw_base == "dict" or raw_base == "Dict":
                base = "unordered_map"
            elif raw_base == "tuple" or raw_base == "Tuple":
                base = "tuple"
            else:
                base = raw_base
            args: List[str]
            if isinstance(annotation.slice, ast.Tuple):
                args = []
                for e in annotation.slice.elts:
                    args.append(self._map_annotation(e))
            else:
                args = [self._map_annotation(annotation.slice)]
            return f"{base}<{', '.join(args)}>"

        return "auto"

    def _is_main_guard(self, stmt: ast.stmt) -> bool:
        """if __name__ == \"__main__\" かを判定する。"""
        if super()._is_main_guard(stmt):
            return True
        if not isinstance(stmt, ast.If):
            return False
        test = stmt.test
        if not isinstance(test, ast.Compare):
            try:
                return test.as_text() == '__name__ == "__main__"'
            except Exception:
                return False
        return False

    def _raw_expr_to_cpp(self, text: str) -> str:
        """RawExpr の文字列を最小限 C++ 表記に正規化する。"""
        if text == "True":
            return "true"
        if text == "False":
            return "false"
        if text == "None":
            return "nullptr"
        return (
            text.replace("(True)", "(true)")
            .replace("(False)", "(false)")
            .replace("(None)", "(nullptr)")
            .replace(" True", " true")
            .replace(" False", " false")
            .replace(" None", " nullptr")
        )

    def _constant(self, value: object) -> str:
        """Python リテラル値を C++ リテラル表現へ変換する。"""
        if isinstance(value, str):
            text = str(value)
            escaped = (
                text.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\t", "\\t")
                .replace("\r", "\\r")
            )
            return f'"{escaped}"'
        text = str(value)
        if text == "True":
            return "true"
        if text == "False":
            return "false"
        if text == "None":
            return "nullptr"
        if isinstance(value, int):
            if self.force_long_int or value < INT32_MIN or value > INT32_MAX:
                return f"{value}LL"
        return text

    def _binop(self, op: ast.operator) -> str:
        """二項演算子ノードを C++ 演算子文字列へ変換する。"""
        if isinstance(op, ast.Add):
            return "+"
        if isinstance(op, ast.Sub):
            return "-"
        if isinstance(op, ast.Mult):
            return "*"
        if isinstance(op, ast.Div):
            return "/"
        if isinstance(op, ast.FloorDiv):
            return "/"
        if isinstance(op, ast.Mod):
            return "%"
        if isinstance(op, ast.Pow):
            return "**"
        if isinstance(op, ast.BitOr):
            return "|"
        if isinstance(op, ast.BitAnd):
            return "&"
        if isinstance(op, ast.BitXor):
            return "^"
        if isinstance(op, ast.LShift):
            return "<<"
        if isinstance(op, ast.RShift):
            return ">>"
        raise TranspileError("Unsupported binary operator")

    def _unaryop(self, op: ast.unaryop) -> str:
        """単項演算子ノードを C++ 演算子文字列へ変換する。"""
        if isinstance(op, ast.UAdd):
            return "+"
        if isinstance(op, ast.USub):
            return "-"
        if isinstance(op, ast.Not):
            return "!"
        raise TranspileError("Unsupported unary operator")

    def _cmpop(self, op: ast.cmpop) -> str:
        """比較演算子ノードを C++ 演算子文字列へ変換する。"""
        if isinstance(op, ast.Eq):
            return "=="
        if isinstance(op, ast.NotEq):
            return "!="
        if isinstance(op, ast.Lt):
            return "<"
        if isinstance(op, ast.LtE):
            return "<="
        if isinstance(op, ast.Gt):
            return ">"
        if isinstance(op, ast.GtE):
            return ">="
        raise TranspileError("Unsupported comparison operator")

    def _transpile_compare(self, left_expr: ast.expr, op: ast.cmpop, right_expr: ast.expr) -> str:
        """比較式ノードを C++ 比較式へ変換する。"""
        left = self.transpile_expr(left_expr)
        right = self.transpile_expr(right_expr)
        if isinstance(op, ast.In):
            return f"py_in({left}, {right})"
        if isinstance(op, ast.NotIn):
            return f"(!py_in({left}, {right}))"
        if isinstance(op, ast.Is):
            return f"({left} == {right})"
        if isinstance(op, ast.IsNot):
            return f"({left} != {right})"
        return f"({left} {self._cmpop(op)} {right})"

    def _transpile_chained_compare(self, expr: ast.Compare) -> str:
        """連鎖比較を pairwise 比較の AND に展開する。"""
        items: List[str] = []
        left_node = expr.left
        for i, op in enumerate(expr.ops):
            right_node = expr.comparators[i]
            items.append(self._transpile_compare(left_node, op, right_node))
            left_node = right_node
        if len(items) == 0:
            return "true"
        return "(" + " && ".join(items) + ")"

    def _transpile_comprehension_body(
        self,
        generators: List[ast.comprehension],
        body_line: str,
        index: int = 0,
        temp_idx: int = 0,
    ) -> List[str]:
        """comprehension の for/if を入れ子の C++ for/if へ変換する。"""
        if index >= len(generators):
            return [body_line]

        gen = generators[index]
        iter_expr = self.transpile_expr(gen.iter)
        lines: List[str] = []
        loop_var = f"__pytra_item_{temp_idx}"
        target_lines: List[str] = []

        if isinstance(gen.target, ast.Name):
            loop_var = gen.target.id
        elif isinstance(gen.target, ast.Tuple):
            tuple_names: List[str] = []
            only_name_targets = True
            for elt in gen.target.elts:
                if isinstance(elt, ast.Name):
                    tuple_names.append(elt.id)
                else:
                    only_name_targets = False
                    break
            if not only_name_targets:
                raise TranspileError("Unsupported comprehension target")
            for i, name in enumerate(tuple_names):
                target_lines.append(f"auto {name} = std::get<{i}>({loop_var});")
        else:
            raise TranspileError("Unsupported comprehension target")

        lines.append(f"for (const auto& {loop_var} : {iter_expr})")
        lines.append("{")
        body: List[str] = []
        body.extend(target_lines)
        for if_cond in gen.ifs:
            body.append(f"if (!({self.transpile_expr(if_cond)})) continue;")
        body.extend(self._transpile_comprehension_body(generators, body_line, index + 1, temp_idx + 1))
        lines.extend(self._indent_block(body))
        lines.append("}")
        return lines

    def _transpile_list_comp(self, expr: ast.ListComp) -> str:
        """list comprehension を即時ラムダで vector 生成へ変換する。"""
        elt_expr = self.transpile_expr(expr.elt)
        elt_type = self._infer_expr_cpp_type(expr.elt)
        if elt_type == "":
            elt_type = "auto"
        out_type = f"vector<{elt_type}>" if elt_type != "auto" else "vector<int>"

        lines: List[str] = [f"{out_type} __pytra_out;"]
        lines.extend(self._transpile_comprehension_body(expr.generators, f"__pytra_out.push_back({elt_expr});"))
        lines.append("return __pytra_out;")
        return "([&]() { " + " ".join(lines) + " })()"

    def _transpile_set_comp(self, expr: ast.SetComp) -> str:
        """set comprehension を即時ラムダで unordered_set 生成へ変換する。"""
        elt_expr = self.transpile_expr(expr.elt)
        elt_type = self._infer_expr_cpp_type(expr.elt)
        if elt_type == "":
            elt_type = "int"
        lines: List[str] = [f"unordered_set<{elt_type}> __pytra_out;"]
        lines.extend(self._transpile_comprehension_body(expr.generators, f"__pytra_out.insert({elt_expr});"))
        lines.append("return __pytra_out;")
        return "([&]() { " + " ".join(lines) + " })()"

    def _transpile_gen_comp(self, expr: ast.GeneratorExp) -> str:
        """generator expression は list として展開して返す。"""
        pseudo_list = ast.ListComp(elt=expr.elt, generators=expr.generators)
        return self._transpile_list_comp(pseudo_list)

    def _boolop(self, op: ast.boolop) -> str:
        """論理演算子ノードを C++ 論理演算子へ変換する。"""
        if isinstance(op, ast.And):
            return "&&"
        if isinstance(op, ast.Or):
            return "||"
        raise TranspileError("Unsupported boolean operator")

    def _transpile_joined_str(self, expr: ast.JoinedStr) -> str:
        """f-string を文字列連結式へ変換する。"""
        parts: List[str] = []
        for value in expr.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(self._constant(value.value))
            elif isinstance(value, ast.FormattedValue):
                parts.append(f"py_to_string({self.transpile_expr(value.value)})")
            else:
                parts.append('""')
        if len(parts) == 0:
            return '""'
        return "(" + " + ".join(parts) + ")"

    def _is_dataclass_class(self, cls: ast.stmt) -> bool:
        """クラスに @dataclass デコレータが付いているかを判定する。"""
        for decorator in cls.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
                return True
            if isinstance(decorator, ast.Attribute) and decorator.attr == "dataclass":
                return True
        return False

def transpile(input_file: str, output_file: str) -> None:
    """外部から使う簡易API。

    Args:
        input_file: 入力 Python ファイルパス。
        output_file: 出力 C++ ファイルパス。
    """
    transpiler = CppTranspiler()
    transpiler.transpile_file(Path(input_file), Path(output_file))


__all__ = ["TranspileError", "CppTranspiler", "transpile"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Transpile typed Python code to C++")
    parser.add_argument("input", help="Path to input Python file")
    parser.add_argument("output", help="Path to output C++ file")
    args = parser.parse_args()
    try:
        transpile(args.input, args.output)
    except (OSError, SyntaxError, TranspileError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
