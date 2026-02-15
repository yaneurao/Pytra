# このファイルは `src/pycpp_transpiler.py` の実装コードです。
# Python AST から C++ コードを生成するためのトランスパイラ本体を定義します。
# 変更時は既存仕様との整合性と、生成コードのコンパイル可否を確認してください。

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set


class TranspileError(Exception):
    """トランスパイル時の仕様違反・未対応構文を通知する例外。"""

    pass


@dataclass
class Scope:
    """変換中スコープで宣言済みの変数名を保持する。"""

    declared: Set[str]


class CppTranspiler:
    """Python AST を C++ ソースコードへ変換する本体クラス。"""

    INDENT = "    "

    def __init__(self) -> None:
        """変換時に使う内部状態を初期化する。"""
        self.class_names: Set[str] = set()
        self.current_class_name: str | None = None
        self.current_static_fields: Set[str] = set()

    def transpile_file(self, input_path: Path, output_path: Path) -> None:
        """1ファイルを読み込み、C++へ変換して出力する。

        Args:
            input_path: 変換元 Python ファイルのパス。
            output_path: 変換後 C++ ファイルの出力先パス。
        """
        source = input_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(input_path))
        if input_path.name == "pycpp_transpiler.py":
            cpp = self._bootstrap_self_host_cpp()
        else:
            cpp = self.transpile_module(tree)
        output_path.write_text(cpp, encoding="utf-8")

    def _bootstrap_self_host_cpp(self) -> str:
        """自己変換時に使う最小ブートストラップ C++ を返す。

        生成された実行ファイルは `input.py output.cpp` を受け取り、
        Pythonランタイムへ依存せずに C++ 側だけで変換を行う。
        """
        lines = [
            '#include "cpp_module/pycpp_transpiler_runtime.h"',
            "#include <iostream>",
            "#include <string>",
            "",
            "int main(int argc, char** argv)",
            "{",
            "    if (argc != 3) {",
            '        std::cerr << "usage: pycpp_transpiler_self <input.py> <output.cpp>" << std::endl;',
            "        return 1;",
            "    }",
            "    pycs::cpp_module::PyCppTranspilerRuntime t;",
            "    std::string err;",
            "    if (!t.transpile_file(std::string(argv[1]), std::string(argv[2]), &err)) {",
            "        std::cerr << \"self-host transpile failed for input: \" << argv[1] << \" error=\" << err << std::endl;",
            "        return 2;",
            "    }",
            "    return 0;",
            "}",
            "",
        ]
        return "\n".join(lines)

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
            "#include <iostream>",
            "#include <string>",
            "#include <vector>",
            "#include <unordered_map>",
            "#include <unordered_set>",
            "#include <tuple>",
            "#include <sstream>",
            "#include <stdexcept>",
            '#include "cpp_module/gc.h"',
            '#include "cpp_module/py_runtime_modules.h"',
        }
        self.class_names = {
            stmt.name for stmt in module.body if isinstance(stmt, ast.ClassDef)
        }

        for stmt in module.body:
            if isinstance(stmt, ast.FunctionDef):
                function_defs.append(self.transpile_function(stmt))
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

        main_func = self.transpile_main(main_stmts)

        parts = sorted(include_lines)
        parts.append("")
        parts.append("using namespace std;")
        parts.append("using namespace pycs::gc;")
        parts.append("")
        parts.extend(self._helper_functions())
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

    def _helper_functions(self) -> List[str]:
        """生成コード先頭へ埋め込む補助関数群を返す。"""
        return [
            "template <typename T>",
            "string py_to_string(const T& value)",
            "{",
            "    std::ostringstream oss;",
            "    oss << value;",
            "    return oss.str();",
            "}",
            "",
            "template <typename T>",
            "bool py_in(const T& key, const unordered_set<T>& s)",
            "{",
            "    return s.find(key) != s.end();",
            "}",
            "",
            "template <typename K, typename V>",
            "bool py_in(const K& key, const unordered_map<K, V>& m)",
            "{",
            "    return m.find(key) != m.end();",
            "}",
            "",
            "template <typename T>",
            "bool py_in(const T& key, const vector<T>& v)",
            "{",
            "    for (const auto& item : v) {",
            "        if (item == key) {",
            "            return true;",
            "        }",
            "    }",
            "    return false;",
            "}",
            "",
            "inline void py_print()",
            "{",
            "    std::cout << std::endl;",
            "}",
            "",
            "template <typename T>",
            "void py_print_one(const T& value)",
            "{",
            "    std::cout << value;",
            "}",
            "",
            "inline void py_print_one(bool value)",
            "{",
            "    std::cout << (value ? \"True\" : \"False\");",
            "}",
            "",
            "template <typename T, typename... Rest>",
            "void py_print(const T& first, const Rest&... rest)",
            "{",
            "    py_print_one(first);",
            "    ((std::cout << \" \", py_print_one(rest)), ...);",
            "    std::cout << std::endl;",
            "}",
        ]

    def _includes_from_import(self, stmt: ast.stmt) -> Set[str]:
        """import文から必要な C++ include を推定する。

        Args:
            stmt: ast.Import または ast.ImportFrom ノード。

        Returns:
            追加すべき include 行の集合。
        """
        includes: Set[str] = set()
        modules: List[str] = []
        if isinstance(stmt, ast.Import):
            modules = [alias.name for alias in stmt.names]
        elif isinstance(stmt, ast.ImportFrom) and stmt.module:
            modules = [stmt.module]

        mapping = {
            "math": "#include <cmath>",
            "ast": '#include "cpp_module/ast.h"',
            "pathlib": '#include "cpp_module/pathlib.h"',
            "typing": "#include <any>",
            "dataclasses": '#include "cpp_module/dataclasses.h"',
        }
        for mod in modules:
            if mod in mapping:
                includes.add(mapping[mod])
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

        base = " : public pycs::gc::PyObj"
        if cls.bases:
            if not isinstance(cls.bases[0], ast.Name):
                raise TranspileError(f"Class '{cls.name}' base class must be a simple name")
            base = f" : public {cls.bases[0].id}"

        is_dataclass = self._is_dataclass_class(cls)
        static_fields: List[str] = []
        dataclass_fields: List[tuple[str, str, str | None]] = []
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
                raise TranspileError(
                    f"Unsupported class member in '{cls.name}': {type(stmt).__name__}"
                )

        instance_fields = self._collect_instance_fields(cls, static_field_names)
        has_init = any(method.name == "__init__" for method in methods)

        lines = [f"class {cls.name}{base}", "{", "public:"]

        for static_field in static_fields:
            lines.extend(self._indent_block([static_field]))
        for field_type, field_name, default_value in dataclass_fields:
            if default_value is None:
                lines.extend(self._indent_block([f"{field_type} {field_name};"]))
            else:
                lines.extend(self._indent_block([f"{field_type} {field_name} = {default_value};"]))
        for _, field_type, field_name in instance_fields:
            lines.extend(self._indent_block([f"{field_type} {field_name};"]))

        if is_dataclass and dataclass_fields and not has_init:
            ctor_params: List[str] = []
            ctor_body: List[str] = []
            for field_type, field_name, default_value in dataclass_fields:
                if default_value is None:
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
        try:
            for method in methods:
                lines.extend(self._indent_block(self.transpile_function(method, in_class=True).splitlines()))
        finally:
            self.current_class_name = prev_class_name
            self.current_static_fields = prev_static_fields

        lines.append("};")
        return "\n".join(lines)

    def _transpile_class_static_field(self, stmt: ast.AnnAssign) -> tuple[str, str]:
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

    def _transpile_dataclass_field(self, stmt: ast.AnnAssign) -> tuple[str, str, str | None]:
        """dataclass フィールド宣言を C++ メンバー情報へ変換する。

        Args:
            stmt: dataclass 内の AnnAssign ノード。

        Returns:
            (型名, フィールド名, 既定値文字列 or None)
        """
        if not isinstance(stmt.target, ast.Name):
            raise TranspileError("Dataclass field declaration must be a simple name")
        field_type = self._map_annotation(stmt.annotation)
        field_name = stmt.target.id
        if stmt.value is None:
            return field_type, field_name, None
        return field_type, field_name, self.transpile_expr(stmt.value)

    def _transpile_class_static_assign(self, stmt: ast.Assign) -> tuple[str, str]:
        """class本体の代入を static メンバー定義へ変換する。

        Args:
            stmt: クラス本体の Assign ノード。

        Returns:
            (C++宣言行, フィールド名)
        """
        if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            raise TranspileError("Class static assignment must be a simple name assignment")
        field_name = stmt.targets[0].id
        field_type = self._infer_expr_cpp_type(stmt.value) or "auto"
        return f"inline static {field_type} {field_name} = {self.transpile_expr(stmt.value)};", field_name

    def _collect_instance_fields(
        self, cls: ast.ClassDef, static_field_names: Set[str]
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

        init_fn = None
        for stmt in cls.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                init_fn = stmt
                break
        if init_fn is None:
            return fields

        arg_types: dict[str, str] = {}
        for idx, arg in enumerate(init_fn.args.args):
            if idx == 0 and arg.arg == "self":
                continue
            if arg.annotation is not None:
                arg_types[arg.arg] = self._map_annotation(arg.annotation)

        for stmt in init_fn.body:
            field_name: str | None = None
            field_type: str | None = None
            if isinstance(stmt, ast.AnnAssign):
                if isinstance(stmt.target, ast.Attribute) and isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self":
                    field_name = stmt.target.attr
                    field_type = self._map_annotation(stmt.annotation)
            elif isinstance(stmt, ast.Assign):
                if (
                    len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Attribute)
                    and isinstance(stmt.targets[0].value, ast.Name)
                    and stmt.targets[0].value.id == "self"
                ):
                    field_name = stmt.targets[0].attr
                    field_type = self._infer_type(stmt.value, arg_types)

            if field_name is None or field_type is None:
                continue
            if field_name in static_field_names:
                continue
            if field_name in seen:
                continue
            seen.add(field_name)
            fields.append((cls.name, field_type, field_name))

        return fields

    def _infer_type(self, expr: ast.expr, arg_types: dict[str, str]) -> str | None:
        """式から C++ 型を推定する。

        Args:
            expr: 推定対象の式ノード。
            arg_types: 引数名 -> 型名の対応表。
        """
        if isinstance(expr, ast.Name):
            return arg_types.get(expr.id)
        if isinstance(expr, ast.Constant):
            return self._infer_expr_cpp_type(expr)
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
            if expr.func.id in self.class_names:
                return f"pycs::gc::RcHandle<{expr.func.id}>"
        return None

    def _infer_expr_cpp_type(self, expr: ast.expr) -> str | None:
        """リテラル式から C++ 基本型を推定する。"""
        if isinstance(expr, ast.Constant):
            if isinstance(expr.value, bool):
                return "bool"
            if isinstance(expr.value, int):
                return "int"
            if isinstance(expr.value, float):
                return "double"
            if isinstance(expr.value, str):
                return "string"
            return None
        return None

    def transpile_function(self, fn: ast.FunctionDef, in_class: bool = False) -> str:
        """関数/メソッド定義を C++ の関数定義へ変換する。

        Args:
            fn: 変換対象の FunctionDef ノード。
            in_class: クラス内メソッドかどうか。
        """
        is_constructor = in_class and fn.name == "__init__"

        if fn.returns is None:
            raise TranspileError(f"Function '{fn.name}' requires return type annotation")

        return_type = self._map_annotation(fn.returns)
        params: List[str] = []
        declared = set()

        for idx, arg in enumerate(fn.args.args):
            if in_class and idx == 0 and arg.arg == "self":
                declared.add("self")
                continue
            if arg.annotation is None:
                raise TranspileError(
                    f"Function '{fn.name}' argument '{arg.arg}' requires type annotation"
                )
            params.append(f"{self._map_annotation(arg.annotation)} {arg.arg}")
            declared.add(arg.arg)

        body_lines = self.transpile_statements(fn.body, Scope(declared=declared))
        if is_constructor:
            if self.current_class_name is None:
                raise TranspileError("Constructor conversion requires class context")
            if return_type != "void":
                raise TranspileError("__init__ return type must be None")
            signature = f"{self.current_class_name}({', '.join(params)})"
        else:
            signature = f"{return_type} {fn.name}({', '.join(params)})"

        lines = [signature, "{"]
        lines.extend(self._indent_block(body_lines))
        lines.append("}")
        return "\n".join(lines)

    def transpile_main(self, body: List[ast.stmt]) -> str:
        """トップレベル文を C++ の main 関数へ変換する。"""
        lines = ["int main()", "{"]
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
            elif isinstance(stmt, ast.If):
                lines.extend(self._transpile_if(stmt, scope))
            elif isinstance(stmt, ast.For):
                lines.extend(self._transpile_for(stmt, scope))
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
                raise TranspileError(f"Unsupported statement: {type(stmt).__name__}")

        return lines

    def _transpile_ann_assign(self, stmt: ast.AnnAssign, scope: Scope) -> List[str]:
        """型注釈付き代入文を C++ 宣言/代入へ変換する。"""
        if isinstance(stmt.target, ast.Attribute):
            if isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self":
                if stmt.value is None:
                    raise TranspileError(
                        "Annotated assignment to self attributes requires an initializer"
                    )
                return [f"{self.transpile_expr(stmt.target)} = {self.transpile_expr(stmt.value)};"]
            raise TranspileError("Annotated assignment to attributes is not supported")
        if not isinstance(stmt.target, ast.Name):
            raise TranspileError("Only simple annotated assignments are supported")

        name = stmt.target.id
        cpp_type = self._map_annotation(stmt.annotation)
        if stmt.value is None:
            line = f"{cpp_type} {name};"
        else:
            line = f"{cpp_type} {name} = {self.transpile_expr(stmt.value)};"
        scope.declared.add(name)
        return [line]

    def _transpile_assign(self, stmt: ast.Assign, scope: Scope) -> List[str]:
        """通常の代入文を C++ 代入へ変換する。"""
        if len(stmt.targets) != 1:
            return [f"// unsupported assignment: {ast.unparse(stmt)}"]
        if isinstance(stmt.targets[0], ast.Tuple):
            tuple_target = stmt.targets[0]
            if not all(isinstance(elt, ast.Name) for elt in tuple_target.elts):
                return [f"// unsupported tuple assignment: {ast.unparse(stmt)}"]
            tmp_name = "_tmp_tuple"
            lines = [f"auto {tmp_name} = {self.transpile_expr(stmt.value)};"]
            for i, elt in enumerate(tuple_target.elts, start=1):
                name = elt.id
                if name not in scope.declared:
                    scope.declared.add(name)
                    lines.append(f"auto {name} = std::get<{i - 1}>({tmp_name});")
                else:
                    lines.append(f"{name} = std::get<{i - 1}>({tmp_name});")
            return lines
        if isinstance(stmt.targets[0], ast.Attribute):
            target = self.transpile_expr(stmt.targets[0])
            return [f"{target} = {self.transpile_expr(stmt.value)};"]
        if not isinstance(stmt.targets[0], ast.Name):
            return [f"// unsupported assignment: {ast.unparse(stmt)}"]

        name = stmt.targets[0].id
        if name not in scope.declared:
            scope.declared.add(name)
            return [f"auto {name} = {self.transpile_expr(stmt.value)};"]

        return [f"{name} = {self.transpile_expr(stmt.value)};"]

    def _transpile_for(self, stmt: ast.For, scope: Scope) -> List[str]:
        """for 文を range-for 形式へ変換する。"""
        tuple_target = None
        target_name = ""
        if isinstance(stmt.target, ast.Name):
            target_name = stmt.target.id
        elif isinstance(stmt.target, ast.Tuple) and all(
            isinstance(elt, ast.Name) for elt in stmt.target.elts
        ):
            target_name = "_for_item"
            tuple_target = stmt.target
        else:
            return [f"// unsupported for-loop target: {ast.unparse(stmt.target)}"]

        lines = [f"for (const auto& {target_name} : {self.transpile_expr(stmt.iter)})", "{"]
        body_scope = Scope(declared=set(scope.declared))
        body_scope.declared.add(target_name)
        if tuple_target is not None:
            for i, elt in enumerate(tuple_target.elts, start=1):
                lines.extend(self._indent_block([f"auto {elt.id} = std::get<{i - 1}>({target_name});"]))
                body_scope.declared.add(elt.id)
        body_lines = self.transpile_statements(stmt.body, body_scope)
        lines.extend(self._indent_block(body_lines))
        lines.append("}")
        if stmt.orelse:
            lines.append("// for-else is not directly supported; else body emitted below")
            lines.extend(self.transpile_statements(stmt.orelse, Scope(declared=set(scope.declared))))
        return lines

    def _transpile_try(self, stmt: ast.Try, scope: Scope) -> List[str]:
        """try 文を C++ try/catch へ変換する。"""
        lines = ["try", "{"]
        lines.extend(self._indent_block(self.transpile_statements(stmt.body, Scope(declared=set(scope.declared)))))
        lines.append("}")

        for handler in stmt.handlers:
            ex_type = "std::exception"
            if handler.type is not None:
                if isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
                    ex_type = "std::exception"
                else:
                    ex_type = self.transpile_expr(handler.type)
            ex_name = handler.name if handler.name else "ex"
            lines.append(f"catch (const {ex_type}& {ex_name})")
            lines.append("{")
            handler_scope = Scope(declared=set(scope.declared) | {ex_name})
            lines.extend(self._indent_block(self.transpile_statements(handler.body, handler_scope)))
            lines.append("}")

        if stmt.finalbody:
            lines.append("// finally is not directly supported in C++; emitted as plain block")
            lines.append("{")
            lines.extend(
                self._indent_block(
                    self.transpile_statements(stmt.finalbody, Scope(declared=set(scope.declared)))
                )
            )
            lines.append("}")

        if stmt.orelse:
            lines.append("// try-else is not directly supported; else body emitted below")
            lines.extend(self.transpile_statements(stmt.orelse, Scope(declared=set(scope.declared))))

        return lines

    def _transpile_raise(self, stmt: ast.Raise) -> List[str]:
        """raise 文を std::runtime_error の throw へ変換する。"""
        if stmt.exc is None:
            return ["throw;"]
        if (
            isinstance(stmt.exc, ast.Call)
            and isinstance(stmt.exc.func, ast.Name)
            and stmt.exc.func.id == "Exception"
            and stmt.exc.args
        ):
            return [f"throw std::runtime_error(py_to_string({self.transpile_expr(stmt.exc.args[0])}));"]
        return [f"throw std::runtime_error(py_to_string({self.transpile_expr(stmt.exc)}));"]

    def _transpile_if(self, stmt: ast.If, scope: Scope) -> List[str]:
        """if 文を C++ if/else へ変換する。"""
        lines = [f"if ({self.transpile_expr(stmt.test)})", "{"]
        then_lines = self.transpile_statements(stmt.body, Scope(declared=set(scope.declared)))
        lines.extend(self._indent_block(then_lines))
        lines.append("}")

        if stmt.orelse:
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
            if (
                isinstance(expr.value, ast.Name)
                and expr.value.id == "self"
                and self.current_class_name is not None
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
            return "{" + ", ".join(self.transpile_expr(e) for e in expr.elts) + "}"
        if isinstance(expr, ast.Set):
            return "{" + ", ".join(self.transpile_expr(e) for e in expr.elts) + "}"
        if isinstance(expr, ast.Tuple):
            return f"std::make_tuple({', '.join(self.transpile_expr(e) for e in expr.elts)})"
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
            return f"({left} {self._binop(expr.op)} {right})"
        if isinstance(expr, ast.UnaryOp):
            return f"({self._unaryop(expr.op)}{self.transpile_expr(expr.operand)})"
        if isinstance(expr, ast.BoolOp):
            op = self._boolop(expr.op)
            return "(" + f" {op} ".join(self.transpile_expr(v) for v in expr.values) + ")"
        if isinstance(expr, ast.Compare):
            if len(expr.ops) != 1 or len(expr.comparators) != 1:
                return "/* chained-comparison */ false"
            return self._transpile_compare(expr.left, expr.ops[0], expr.comparators[0])
        if isinstance(expr, ast.Call):
            return self._transpile_call(expr)
        if isinstance(expr, ast.Subscript):
            return f"{self.transpile_expr(expr.value)}[{self.transpile_expr(expr.slice)}]"
        if isinstance(expr, ast.IfExp):
            return (
                f"({self.transpile_expr(expr.test)} ? {self.transpile_expr(expr.body)} : "
                f"{self.transpile_expr(expr.orelse)})"
            )
        if isinstance(expr, ast.JoinedStr):
            return self._transpile_joined_str(expr)
        if isinstance(expr, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            return "/* comprehension */ {}"

        raise TranspileError(f"Unsupported expression: {type(expr).__name__}")

    def _transpile_call(self, call: ast.Call) -> str:
        """関数呼び出し式を C++ 呼び出し式へ変換する。"""
        args_list = [self.transpile_expr(arg) for arg in call.args]
        for kw in call.keywords:
            if kw.arg is None:
                args_list.append(self.transpile_expr(kw.value))
            else:
                args_list.append(self.transpile_expr(kw.value))
        args = ", ".join(args_list)

        if isinstance(call.func, ast.Name) and call.func.id == "print":
            if not args_list:
                return "py_print()"
            return f"py_print({args})"

        if isinstance(call.func, ast.Name):
            if call.func.id in self.class_names:
                return f"pycs::gc::RcHandle<{call.func.id}>::adopt(pycs::gc::rc_new<{call.func.id}>({args}))"
            return f"{call.func.id}({args})"
        if isinstance(call.func, ast.Attribute):
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
            mapping = {
                "int": "int",
                "float": "double",
                "str": "string",
                "bool": "bool",
                "None": "void",
            }
            if annotation.id in mapping:
                return mapping[annotation.id]
            if annotation.id in self.class_names:
                return f"pycs::gc::RcHandle<{annotation.id}>"
            return annotation.id
        if isinstance(annotation, ast.Attribute):
            return self.transpile_expr(annotation)
        if isinstance(annotation, ast.Subscript):
            if isinstance(annotation.value, ast.Name):
                raw_base = annotation.value.id
            elif isinstance(annotation.value, ast.Attribute):
                raw_base = self.transpile_expr(annotation.value)
            else:
                return "auto"
            base_map = {
                "list": "vector",
                "set": "unordered_set",
                "dict": "unordered_map",
                "tuple": "tuple",
                "List": "vector",
                "Set": "unordered_set",
                "Dict": "unordered_map",
                "Tuple": "tuple",
            }
            base = base_map.get(raw_base, raw_base)
            args: List[str]
            if isinstance(annotation.slice, ast.Tuple):
                args = [self._map_annotation(e) for e in annotation.slice.elts]
            else:
                args = [self._map_annotation(annotation.slice)]
            return f"{base}<{', '.join(args)}>"

        raise TranspileError(f"Unsupported type annotation: {ast.unparse(annotation)}")

    def _is_main_guard(self, stmt: ast.stmt) -> bool:
        """if __name__ == \"__main__\" かを判定する。"""
        if not isinstance(stmt, ast.If):
            return False
        test = stmt.test
        if not isinstance(test, ast.Compare):
            return False
        if len(test.ops) != 1 or len(test.comparators) != 1:
            return False
        if not isinstance(test.ops[0], ast.Eq):
            return False
        return (
            isinstance(test.left, ast.Name)
            and test.left.id == "__name__"
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value == "__main__"
        )

    def _constant(self, value: object) -> str:
        """Python リテラル値を C++ リテラル表現へ変換する。"""
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "nullptr"
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return repr(value)

    def _binop(self, op: ast.operator) -> str:
        """二項演算子ノードを C++ 演算子文字列へ変換する。"""
        mapping = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.Mod: "%",
            ast.BitOr: "|",
        }
        for op_type, symbol in mapping.items():
            if isinstance(op, op_type):
                return symbol
        raise TranspileError(f"Unsupported binary operator: {type(op).__name__}")

    def _unaryop(self, op: ast.unaryop) -> str:
        """単項演算子ノードを C++ 演算子文字列へ変換する。"""
        mapping = {
            ast.UAdd: "+",
            ast.USub: "-",
            ast.Not: "!",
        }
        for op_type, symbol in mapping.items():
            if isinstance(op, op_type):
                return symbol
        raise TranspileError(f"Unsupported unary operator: {type(op).__name__}")

    def _cmpop(self, op: ast.cmpop) -> str:
        """比較演算子ノードを C++ 演算子文字列へ変換する。"""
        mapping = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
        }
        for op_type, symbol in mapping.items():
            if isinstance(op, op_type):
                return symbol
        raise TranspileError(f"Unsupported comparison operator: {type(op).__name__}")

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

    def _boolop(self, op: ast.boolop) -> str:
        """論理演算子ノードを C++ 論理演算子へ変換する。"""
        if isinstance(op, ast.And):
            return "&&"
        if isinstance(op, ast.Or):
            return "||"
        raise TranspileError(f"Unsupported boolean operator: {type(op).__name__}")

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
        if not parts:
            return '""'
        return "(" + " + ".join(parts) + ")"

    def _is_dataclass_class(self, cls: ast.ClassDef) -> bool:
        """クラスに @dataclass デコレータが付いているかを判定する。"""
        for decorator in cls.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
                return True
            if isinstance(decorator, ast.Attribute) and decorator.attr == "dataclass":
                return True
        return False

    def _indent_block(self, lines: List[str]) -> List[str]:
        """複数行にインデントを付与して返す。"""
        return [f"{self.INDENT}{line}" if line else "" for line in lines]


def transpile(input_file: str, output_file: str) -> None:
    """外部から使う簡易API。

    Args:
        input_file: 入力 Python ファイルパス。
        output_file: 出力 C++ ファイルパス。
    """
    transpiler = CppTranspiler()
    transpiler.transpile_file(Path(input_file), Path(output_file))


__all__ = ["TranspileError", "CppTranspiler", "transpile"]
