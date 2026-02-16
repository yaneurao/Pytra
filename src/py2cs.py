# このファイルは `src/py2cs.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

import ast
import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import List, Set


class TranspileError(Exception):
    pass


@dataclass
class Scope:
    declared: Set[str]


class CSharpTranspiler:
    INDENT = "    "

    def __init__(self) -> None:
        self.class_names: Set[str] = set()
        self.current_class_name: str | None = None
        self.current_static_fields: Set[str] = set()
        self.typing_aliases: dict[str, str] = {}

    def transpile_file(self, input_path: Path, output_path: Path) -> None:
        # 1ファイル単位の変換入口。AST化してからC#文字列へ変換する。
        source = input_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(input_path))
        csharp = self.transpile_module(tree)
        output_path.write_text(csharp, encoding="utf-8")

    def transpile_module(self, module: ast.Module) -> str:
        # モジュール直下を「using / 関数 / クラス / メイン処理」に分離して出力する。
        function_defs: List[str] = []
        class_defs: List[str] = []
        top_level_body: List[ast.stmt] = []
        using_lines: Set[str] = {"using System;", "using System.Collections.Generic;", "using System.IO;"}
        self.typing_aliases = {}
        self.class_names = {
            stmt.name for stmt in module.body if isinstance(stmt, ast.ClassDef)
        }

        for stmt in module.body:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                using_lines = using_lines.union(self._using_lines_from_import(stmt))
            elif isinstance(stmt, ast.FunctionDef):
                function_defs.append(self.transpile_function(stmt))
            elif isinstance(stmt, ast.ClassDef):
                class_defs.append(self.transpile_class(stmt))
            else:
                top_level_body.append(stmt)

        main_stmts: List[ast.stmt] = []
        for stmt in top_level_body:
            if self._is_main_guard(stmt):
                main_stmts.extend(stmt.body)
            else:
                main_stmts.append(stmt)

        main_method = self.transpile_main(main_stmts)

        parts = sorted(using_lines)
        parts.extend(["", "public static class Program", "{"])

        for fn in function_defs:
            parts.extend(self._indent_block(fn.splitlines()))
            parts.append("")

        for cls in class_defs:
            parts.extend(self._indent_block(cls.splitlines()))
            parts.append("")

        parts.extend(self._indent_block(main_method.splitlines()))
        parts.append("}")
        parts.append("")
        return "\n".join(parts)

    def _using_lines_from_import(self, stmt: ast.stmt) -> Set[str]:
        lines: Set[str] = set()
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                if alias.name in {"py_module", "time", "typing", "dataclasses"}:
                    continue
                module_name = self._map_python_module(alias.name)
                if alias.asname:
                    lines.add(f"using {alias.asname} = {module_name};")
                else:
                    lines.add(f"using {module_name};")
            return lines

        if isinstance(stmt, ast.ImportFrom):
            if stmt.level != 0:
                return lines
            if stmt.module:
                if stmt.module in {"py_module", "time", "dataclasses"}:
                    return lines
                if stmt.module == "typing":
                    for alias in stmt.names:
                        if alias.name == "*":
                            continue
                        alias_name = alias.asname if alias.asname else alias.name
                        self.typing_aliases[alias_name] = self._typing_name_to_builtin(alias.name)
                    return lines
                module_name = self._map_python_module(stmt.module)
                lines.add(f"using {module_name};")
                for alias in stmt.names:
                    if alias.name == "*":
                        continue
                    full_name = f"{module_name}.{alias.name}"
                    if alias.asname:
                        lines.add(f"using {alias.asname} = {full_name};")
            return lines

        return lines

    def _map_python_module(self, module_name: str) -> str:
        mapping = {
            "math": "System",
            "time": "System",
            "pathlib": "System.IO",
            "typing": "System.Collections.Generic",
            "collections": "System.Collections.Generic",
            "itertools": "System.Linq",
        }
        return mapping.get(module_name, module_name)

    def _typing_name_to_builtin(self, typing_name: str) -> str:
        mapping = {
            "List": "list",
            "Dict": "dict",
            "Set": "set",
            "Tuple": "tuple",
            "Optional": "optional",
        }
        return mapping.get(typing_name, typing_name)

    def transpile_class(self, cls: ast.ClassDef) -> str:
        # class定義をC#のclassに変換する。
        # dataclassの場合は、型注釈フィールドをインスタンスフィールドとして扱う。
        if len(cls.bases) > 1:
            raise TranspileError(f"Class '{cls.name}' multiple inheritance is not supported")

        base = ""
        if cls.bases:
            if not isinstance(cls.bases[0], ast.Name):
                raise TranspileError(f"Class '{cls.name}' base class must be a simple name")
            base = f" : {cls.bases[0].id}"

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
            elif isinstance(stmt, ast.Pass):
                continue
            else:
                raise TranspileError(
                    f"Unsupported class member in '{cls.name}': {type(stmt).__name__}"
                )

        instance_fields = self._collect_instance_fields(cls, static_field_names)
        has_init = any(method.name == "__init__" for method in methods)

        lines = [f"public class {cls.name}{base}", "{"]
        for static_field in static_fields:
            lines.extend(self._indent_block([static_field]))
        for field_type, field_name, default_value in dataclass_fields:
            if default_value is None:
                lines.extend(self._indent_block([f"public {field_type} {field_name};"]))
            else:
                lines.extend(self._indent_block([f"public {field_type} {field_name} = {default_value};"]))
        for _, field_type, field_name in instance_fields:
            lines.extend(self._indent_block([f"public {field_type} {field_name};"]))
        if is_dataclass and dataclass_fields and not has_init:
            ctor_params: List[str] = []
            ctor_body: List[str] = []
            for field_type, field_name, default_value in dataclass_fields:
                if default_value is None:
                    ctor_params.append(f"{field_type} {field_name}")
                else:
                    ctor_params.append(f"{field_type} {field_name} = {default_value}")
                ctor_body.append(f"this.{field_name} = {field_name};")
            lines.extend(self._indent_block([f"public {cls.name}({', '.join(ctor_params)})"]))
            lines.extend(self._indent_block(["{"]))
            lines.extend(self._indent_block(self._indent_block(ctor_body)))
            lines.extend(self._indent_block(["}"]))
        if static_fields or dataclass_fields or instance_fields:
            lines.extend(self._indent_block([""]))

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

        lines.append("}")
        return "\n".join(lines)

    def _transpile_class_static_field(self, stmt: ast.AnnAssign) -> tuple[str, str]:
        if not isinstance(stmt.target, ast.Name):
            raise TranspileError("Class field declaration must be a simple name")

        field_type = self._map_annotation(stmt.annotation)
        field_name = stmt.target.id
        if stmt.value is None:
            return f"public static {field_type} {field_name};", field_name
        return f"public static {field_type} {field_name} = {self.transpile_expr(stmt.value)};", field_name

    def _transpile_dataclass_field(self, stmt: ast.AnnAssign) -> tuple[str, str, str | None]:
        if not isinstance(stmt.target, ast.Name):
            raise TranspileError("Dataclass field declaration must be a simple name")
        field_type = self._map_annotation(stmt.annotation)
        field_name = stmt.target.id
        if stmt.value is None:
            return field_type, field_name, None
        return field_type, field_name, self.transpile_expr(stmt.value)

    def _transpile_class_static_assign(self, stmt: ast.Assign) -> tuple[str, str]:
        if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            raise TranspileError("Class static assignment must be a simple name assignment")
        field_name = stmt.targets[0].id
        field_type = self._infer_expr_csharp_type(stmt.value) or "object"
        return f"public static {field_type} {field_name} = {self.transpile_expr(stmt.value)};", field_name

    def _collect_instance_fields(
        self, cls: ast.ClassDef, static_field_names: Set[str]
    ) -> List[tuple[str, str, str]]:
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
        if isinstance(expr, ast.Name):
            return arg_types.get(expr.id)
        if isinstance(expr, ast.Constant):
            return self._infer_expr_csharp_type(expr)
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
            if expr.func.id in self.class_names:
                return expr.func.id
        return None

    def _infer_expr_csharp_type(self, expr: ast.expr) -> str | None:
        def merge_types(types: List[str]) -> str:
            if not types:
                return "object"
            first = types[0]
            if all(t == first for t in types):
                return first
            if all(t in {"int", "double"} for t in types):
                return "double"
            return "object"

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
        if isinstance(expr, ast.List):
            item_types: List[str] = []
            for elt in expr.elts:
                elt_type = self._infer_expr_csharp_type(elt)
                item_types.append(elt_type if elt_type is not None else "object")
            return f"List<{merge_types(item_types)}>"
        if isinstance(expr, ast.Set):
            item_types: List[str] = []
            for elt in expr.elts:
                elt_type = self._infer_expr_csharp_type(elt)
                item_types.append(elt_type if elt_type is not None else "object")
            return f"HashSet<{merge_types(item_types)}>"
        if isinstance(expr, ast.Dict):
            key_types: List[str] = []
            val_types: List[str] = []
            for key, val in zip(expr.keys, expr.values):
                if key is None:
                    continue
                key_type = self._infer_expr_csharp_type(key)
                val_type = self._infer_expr_csharp_type(val)
                key_types.append(key_type if key_type is not None else "object")
                val_types.append(val_type if val_type is not None else "object")
            return f"Dictionary<{merge_types(key_types)}, {merge_types(val_types)}>"
        return None

    def transpile_function(self, fn: ast.FunctionDef, in_class: bool = False) -> str:
        # 関数定義を変換する。クラス内の __init__ はC#コンストラクタへ置き換える。
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
            signature = f"public {self.current_class_name}({', '.join(params)})"
        else:
            modifier = "public" if in_class else "public static"
            signature = f"{modifier} {return_type} {fn.name}({', '.join(params)})"

        lines = [signature, "{"]
        lines.extend(self._indent_block(body_lines))
        lines.append("}")
        return "\n".join(lines)

    def transpile_main(self, body: List[ast.stmt]) -> str:
        lines = ["public static void Main(string[] args)", "{"]
        body_lines = self.transpile_statements(body, Scope(declared={"args"}))
        lines.extend(self._indent_block(body_lines))
        lines.append("}")
        return "\n".join(lines)

    def transpile_statements(self, stmts: List[ast.stmt], scope: Scope) -> List[str]:
        # 文単位の変換ディスパッチ。未対応ノードは明示的に例外化する。
        lines: List[str] = []

        for stmt in stmts:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                lines.append(f"// {ast.unparse(stmt)}")
                continue
            if isinstance(stmt, ast.Return):
                if stmt.value is None:
                    lines.append("return;")
                else:
                    lines.append(f"return {self.transpile_expr(stmt.value)};")
            elif isinstance(stmt, ast.Expr):
                if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                    continue
                lines.append(f"{self.transpile_expr(stmt.value)};")
            elif isinstance(stmt, ast.AnnAssign):
                lines.extend(self._transpile_ann_assign(stmt, scope))
            elif isinstance(stmt, ast.Assign):
                lines.extend(self._transpile_assign(stmt, scope))
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
                raise TranspileError(f"Unsupported statement: {type(stmt).__name__}")

        return lines

    def _transpile_ann_assign(self, stmt: ast.AnnAssign, scope: Scope) -> List[str]:
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
        csharp_type = self._map_annotation(stmt.annotation)
        if stmt.value is None:
            line = f"{csharp_type} {name};"
        else:
            line = f"{csharp_type} {name} = {self.transpile_expr(stmt.value)};"
        scope.declared.add(name)
        return [line]

    def _transpile_assign(self, stmt: ast.Assign, scope: Scope) -> List[str]:
        if len(stmt.targets) != 1:
            return [f"// unsupported assignment: {ast.unparse(stmt)}"]
        if isinstance(stmt.targets[0], ast.Tuple):
            tuple_target = stmt.targets[0]
            if not all(isinstance(elt, ast.Name) for elt in tuple_target.elts):
                return [f"// unsupported tuple assignment: {ast.unparse(stmt)}"]
            tmp_name = "_tmp_tuple"
            lines = [f"var {tmp_name} = {self.transpile_expr(stmt.value)};"]
            for i, elt in enumerate(tuple_target.elts, start=1):
                name = elt.id
                if name not in scope.declared:
                    scope.declared.add(name)
                    lines.append(f"var {name} = {tmp_name}.Item{i};")
                else:
                    lines.append(f"{name} = {tmp_name}.Item{i};")
            return lines
        if isinstance(stmt.targets[0], ast.Attribute):
            target = self.transpile_expr(stmt.targets[0])
            return [f"{target} = {self.transpile_expr(stmt.value)};"]
        if not isinstance(stmt.targets[0], ast.Name):
            return [f"// unsupported assignment: {ast.unparse(stmt)}"]

        name = stmt.targets[0].id
        if name not in scope.declared:
            scope.declared.add(name)
            return [f"var {name} = {self.transpile_expr(stmt.value)};"]

        return [f"{name} = {self.transpile_expr(stmt.value)};"]

    def _transpile_for(self, stmt: ast.For, scope: Scope) -> List[str]:
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

        lines = [f"foreach (var {target_name} in {self.transpile_expr(stmt.iter)})", "{"]
        body_scope = Scope(declared=set(scope.declared))
        body_scope.declared.add(target_name)
        if tuple_target is not None:
            for i, elt in enumerate(tuple_target.elts, start=1):
                lines.extend(self._indent_block([f"var {elt.id} = {target_name}.Item{i};"]))
                body_scope.declared.add(elt.id)
        body_lines = self.transpile_statements(stmt.body, body_scope)
        lines.extend(self._indent_block(body_lines))
        lines.append("}")
        if stmt.orelse:
            lines.append("// for-else is not directly supported; else body emitted below")
            lines.extend(self.transpile_statements(stmt.orelse, Scope(declared=set(scope.declared))))
        return lines

    def _transpile_while(self, stmt: ast.While, scope: Scope) -> List[str]:
        lines = [f"while ({self.transpile_expr(stmt.test)})", "{"]
        body_lines = self.transpile_statements(stmt.body, Scope(declared=set(scope.declared)))
        lines.extend(self._indent_block(body_lines))
        lines.append("}")
        if stmt.orelse:
            lines.append("// while-else is not directly supported; else body emitted below")
            lines.extend(self.transpile_statements(stmt.orelse, Scope(declared=set(scope.declared))))
        return lines

    def _transpile_try(self, stmt: ast.Try, scope: Scope) -> List[str]:
        lines = ["try", "{"]
        lines.extend(self._indent_block(self.transpile_statements(stmt.body, Scope(declared=set(scope.declared)))))
        lines.append("}")

        for handler in stmt.handlers:
            ex_type = "Exception"
            if handler.type is not None:
                ex_type = self.transpile_expr(handler.type)
            ex_name = handler.name if handler.name else "ex"
            lines.append(f"catch ({ex_type} {ex_name})")
            lines.append("{")
            handler_scope = Scope(declared=set(scope.declared) | {ex_name})
            lines.extend(self._indent_block(self.transpile_statements(handler.body, handler_scope)))
            lines.append("}")

        if stmt.finalbody:
            lines.append("finally")
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
        if stmt.exc is None:
            return ["throw;"]
        if isinstance(stmt.exc, ast.Call):
            if isinstance(stmt.exc.func, ast.Name):
                ex_type = stmt.exc.func.id
            elif isinstance(stmt.exc.func, ast.Attribute):
                ex_type = stmt.exc.func.attr
            else:
                ex_type = "Exception"
            args = ", ".join(self.transpile_expr(arg) for arg in stmt.exc.args)
            if ex_type in {"Exception", "ValueError", "RuntimeError"}:
                return [f"throw new Exception({args});"]
            return [f"throw new {ex_type}({args});"]
        if isinstance(stmt.exc, ast.Name):
            ex_type = stmt.exc.id
            if ex_type in {"Exception", "ValueError", "RuntimeError"}:
                return ["throw new Exception();"]
            return [f"throw new {ex_type}();"]
        return [f"throw new Exception({self.transpile_expr(stmt.exc)});"]

    def _transpile_if(self, stmt: ast.If, scope: Scope) -> List[str]:
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
        # 式ノードをC#式へ変換する。
        if isinstance(expr, ast.Name):
            if expr.id == "self":
                return "this"
            return expr.id
        if isinstance(expr, ast.Attribute):
            if (
                isinstance(expr.value, ast.Name)
                and expr.value.id == "self"
                and self.current_class_name is not None
                and expr.attr in self.current_static_fields
            ):
                return f"{self.current_class_name}.{expr.attr}"
            return f"{self.transpile_expr(expr.value)}.{expr.attr}"
        if isinstance(expr, ast.Constant):
            return self._constant(expr.value)
        if isinstance(expr, ast.List):
            inferred_type = self._infer_expr_csharp_type(expr)
            list_type = inferred_type if inferred_type and inferred_type.startswith("List<") else "List<object>"
            return f"new {list_type} {{ {', '.join(self.transpile_expr(e) for e in expr.elts)} }}"
        if isinstance(expr, ast.Set):
            inferred_type = self._infer_expr_csharp_type(expr)
            set_type = inferred_type if inferred_type and inferred_type.startswith("HashSet<") else "HashSet<object>"
            return f"new {set_type} {{ {', '.join(self.transpile_expr(e) for e in expr.elts)} }}"
        if isinstance(expr, ast.Tuple):
            return f"Tuple.Create({', '.join(self.transpile_expr(e) for e in expr.elts)})"
        if isinstance(expr, ast.Dict):
            entries: List[str] = []
            for k, v in zip(expr.keys, expr.values):
                if k is None:
                    continue
                entries.append(f"{{ {self.transpile_expr(k)}, {self.transpile_expr(v)} }}")
            inferred_type = self._infer_expr_csharp_type(expr)
            dict_type = inferred_type if inferred_type and inferred_type.startswith("Dictionary<") else "Dictionary<object, object>"
            return f"new {dict_type} {{ {', '.join(entries)} }}"
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
            return "/* comprehension */ null"

        raise TranspileError(f"Unsupported expression: {type(expr).__name__}")

    def _transpile_call(self, call: ast.Call) -> str:
        args_list = [self.transpile_expr(arg) for arg in call.args]
        for kw in call.keywords:
            if kw.arg is None:
                args_list.append(self.transpile_expr(kw.value))
            else:
                args_list.append(f"{kw.arg}: {self.transpile_expr(kw.value)}")
        args = ", ".join(args_list)

        if isinstance(call.func, ast.Name) and call.func.id == "print":
            return f"Pytra.CsModule.py_runtime.print({args})"
        if isinstance(call.func, ast.Name) and call.func.id == "perf_counter":
            return "Pytra.CsModule.time.perf_counter()"
        if isinstance(call.func, ast.Name) and call.func.id == "bytearray":
            return "new List<byte>()"
        if isinstance(call.func, ast.Name) and call.func.id == "int":
            if len(args_list) == 1:
                return f"(int)({args_list[0]})"
            return "0"
        if isinstance(call.func, ast.Name) and call.func.id == "float":
            if len(args_list) == 1:
                return f"(double)({args_list[0]})"
            return "0.0"
        if isinstance(call.func, ast.Name) and call.func.id == "str":
            if len(args_list) == 1:
                return f"Convert.ToString({args_list[0]})"
            return "\"\""

        if isinstance(call.func, ast.Name):
            if call.func.id in self.class_names:
                return f"new {call.func.id}({args})"
            return f"{call.func.id}({args})"
        if isinstance(call.func, ast.Attribute):
            if (
                isinstance(call.func.value, ast.Name)
                and call.func.value.id == "png_helper"
                and call.func.attr == "write_rgb_png"
            ):
                return f"Pytra.CsModule.png_helper.write_rgb_png({args})"
            if call.func.attr == "append" and len(args_list) == 1:
                return f"{self.transpile_expr(call.func.value)}.Add((byte)({args_list[0]}))"
            return f"{self.transpile_expr(call.func)}({args})"

        raise TranspileError("Only direct function calls are supported")

    def _map_annotation(self, annotation: ast.expr) -> str:
        # Python側型注釈をC#の型名にマッピングする。
        if isinstance(annotation, ast.Constant) and annotation.value is None:
            return "void"
        if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
            left = self._map_annotation(annotation.left)
            right = self._map_annotation(annotation.right)
            if left == "void":
                return right
            if right == "void":
                return left
            return "object"
        if isinstance(annotation, ast.Name):
            mapped_name = self.typing_aliases.get(annotation.id, annotation.id)
            mapping = {
                "int": "int",
                "float": "double",
                "str": "string",
                "bytearray": "List<byte>",
                "bytes": "List<byte>",
                "bool": "bool",
                "None": "void",
                "list": "List<object>",
                "set": "HashSet<object>",
                "dict": "Dictionary<object, object>",
                "tuple": "Tuple<object>",
                "object": "object",
            }
            if mapped_name in mapping:
                return mapping[mapped_name]
            return mapped_name
        if isinstance(annotation, ast.Attribute):
            return self.transpile_expr(annotation)
        if isinstance(annotation, ast.Subscript):
            if isinstance(annotation.value, ast.Name):
                raw_base = self.typing_aliases.get(annotation.value.id, annotation.value.id)
            elif isinstance(annotation.value, ast.Attribute):
                raw_base = self.transpile_expr(annotation.value)
            else:
                return "object"
            base_map = {
                "list": "List",
                "set": "HashSet",
                "dict": "Dictionary",
                "tuple": "Tuple",
            }
            base = base_map.get(raw_base, raw_base)
            args: List[str]
            if isinstance(annotation.slice, ast.Tuple):
                args = [self._map_annotation(e) for e in annotation.slice.elts]
            else:
                args = [self._map_annotation(annotation.slice)]
            return f"{base}<{', '.join(args)}>"

        raise TranspileError(f"Unsupported type annotation: {ast.unparse(annotation)}")

    def _is_dataclass_class(self, cls: ast.ClassDef) -> bool:
        for decorator in cls.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
                return True
            if isinstance(decorator, ast.Attribute) and decorator.attr == "dataclass":
                return True
        return False

    def _is_main_guard(self, stmt: ast.stmt) -> bool:
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
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "null"
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return repr(value)

    def _binop(self, op: ast.operator) -> str:
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
        left = self.transpile_expr(left_expr)
        right = self.transpile_expr(right_expr)
        if isinstance(op, ast.In):
            return f"Pytra.CsModule.py_runtime.py_in({left}, {right})"
        if isinstance(op, ast.NotIn):
            return f"!Pytra.CsModule.py_runtime.py_in({left}, {right})"
        if isinstance(op, ast.Is):
            return f"object.ReferenceEquals({left}, {right})"
        if isinstance(op, ast.IsNot):
            return f"!object.ReferenceEquals({left}, {right})"
        return f"({left} {self._cmpop(op)} {right})"

    def _boolop(self, op: ast.boolop) -> str:
        if isinstance(op, ast.And):
            return "&&"
        if isinstance(op, ast.Or):
            return "||"
        raise TranspileError(f"Unsupported boolean operator: {type(op).__name__}")

    def _transpile_joined_str(self, expr: ast.JoinedStr) -> str:
        parts: List[str] = []
        for value in expr.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value.replace("{", "{{").replace("}", "}}"))
            elif isinstance(value, ast.FormattedValue):
                parts.append("{" + self.transpile_expr(value.value) + "}")
            else:
                parts.append("{/*unsupported*/}")
        return '$"' + "".join(parts).replace('"', '\\"') + '"'

    def _indent_block(self, lines: List[str]) -> List[str]:
        return [f"{self.INDENT}{line}" if line else "" for line in lines]


def transpile(input_file: str, output_file: str) -> None:
    transpiler = CSharpTranspiler()
    transpiler.transpile_file(Path(input_file), Path(output_file))


def main() -> int:
    # C#向けトランスパイラのCLIエントリポイント。
    parser = argparse.ArgumentParser(description="Transpile typed Python code to C#")
    parser.add_argument("input", help="Path to input Python file")
    parser.add_argument("output", help="Path to output C# file")
    args = parser.parse_args()

    try:
        transpile(args.input, args.output)
    except (OSError, SyntaxError, TranspileError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


__all__ = ["TranspileError", "CSharpTranspiler", "transpile"]


if __name__ == "__main__":
    raise SystemExit(main())
