# このファイルは `src/py2cs.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

import ast
import argparse
from pathlib import Path
import sys
from typing import List, Set

try:
    from common.base_transpiler import BaseTranspiler, TranspileError
    from common.transpile_shared import Scope
except ModuleNotFoundError:
    from src.common.base_transpiler import BaseTranspiler, TranspileError
    from src.common.transpile_shared import Scope


# Python 基本型名から C# 基本型名への変換テーブル。
CS_PRIMITIVE_TYPES = {
    # Python 標準の int は C# では long として扱う（既存実装方針）。
    "int": "long",
    "int8": "sbyte",
    "uint8": "byte",
    "int16": "short",
    "uint16": "ushort",
    "int32": "int",
    "uint32": "uint",
    "int64": "long",
    "uint64": "ulong",
    "float": "double",
    "float32": "float",
    "str": "string",
    "bool": "bool",
    "None": "void",
    "object": "object",
}


class CSharpTranspiler(BaseTranspiler):
    RESERVED_WORDS = {
        "abstract", "as", "base", "bool", "break", "byte", "case", "catch", "char",
        "checked", "class", "const", "continue", "decimal", "default", "delegate",
        "do", "double", "else", "enum", "event", "explicit", "extern", "false",
        "finally", "fixed", "float", "for", "foreach", "goto", "if", "implicit",
        "in", "int", "interface", "internal", "is", "lock", "long", "namespace",
        "new", "null", "object", "operator", "out", "override", "params", "private",
        "protected", "public", "readonly", "ref", "return", "sbyte", "sealed",
        "short", "sizeof", "stackalloc", "static", "string", "struct", "switch",
        "this", "throw", "true", "try", "typeof", "uint", "ulong", "unchecked",
        "unsafe", "ushort", "using", "virtual", "void", "volatile", "while",
    }

    def __init__(self) -> None:
        super().__init__(temp_prefix="__pytra")
        self.class_names: Set[str] = set()
        self.current_class_name: str | None = None
        self.current_static_fields: Set[str] = set()
        self.typing_aliases: dict[str, str] = {}
        self.wide_int_functions: Set[str] = set()
        self.force_long_int: bool = False
        self.path_like_names: Set[str] = set()

    def _ident(self, name: str) -> str:
        if name in self.RESERVED_WORDS:
            return f"@{name}"
        return name

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
        self.path_like_names = set()
        self.class_names = {
            stmt.name for stmt in module.body if isinstance(stmt, ast.ClassDef)
        }
        module_functions = [
            stmt for stmt in module.body if isinstance(stmt, ast.FunctionDef)
        ]
        self.wide_int_functions = self._compute_wide_int_functions(module_functions)

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
                if alias.name in {"py_module", "pylib", "time", "typing", "dataclasses", "__future__"}:
                    continue
                if alias.name.startswith("py_module.") or alias.name.startswith("pylib."):
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
                if stmt.module in {"py_module", "pylib", "time", "dataclasses", "__future__"}:
                    return lines
                if stmt.module.startswith("py_module.") or stmt.module.startswith("pylib."):
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
                return "long"
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
        if isinstance(expr, ast.Call):
            if isinstance(expr.func, ast.Name) and expr.func.id == "Path":
                return "Pytra.CsModule.py_path"
            if (
                isinstance(expr.func, ast.Attribute)
                and isinstance(expr.func.value, ast.Name)
                and expr.func.value.id == "pathlib"
                and expr.func.attr == "Path"
            ):
                return "Pytra.CsModule.py_path"
        return None

    def transpile_function(self, fn: ast.FunctionDef, in_class: bool = False) -> str:
        # 関数定義を変換する。クラス内の __init__ はC#コンストラクタへ置き換える。
        is_constructor = in_class and fn.name == "__init__"

        prev_force_long_int = self.force_long_int
        self.force_long_int = fn.name in self.wide_int_functions or self._requires_wide_int(fn)
        try:
            return_type = "void" if fn.returns is None else self._map_annotation(fn.returns)
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
                params.append(f"{self._map_annotation(arg.annotation)} {self._ident(arg.arg)}")
                declared.add(arg.arg)

            body_lines = self.transpile_statements(fn.body, Scope(declared=declared))
            if is_constructor:
                if self.current_class_name is None:
                    raise TranspileError("Constructor conversion requires class context")
                if return_type != "void":
                    raise TranspileError("__init__ return type must be None")
                signature = f"public {self._ident(self.current_class_name)}({', '.join(params)})"
            else:
                modifier = "public" if in_class else "public static"
                signature = f"{modifier} {return_type} {self._ident(fn.name)}({', '.join(params)})"

            lines = [signature, "{"]
            lines.extend(self._indent_block(body_lines))
            lines.append("}")
            return "\n".join(lines)
        finally:
            self.force_long_int = prev_force_long_int

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
            line = f"{csharp_type} {self._ident(name)};"
        else:
            if isinstance(stmt.value, ast.List) and csharp_type.startswith("List<"):
                values = ", ".join(self.transpile_expr(e) for e in stmt.value.elts)
                line = f"{csharp_type} {self._ident(name)} = new {csharp_type} {{ {values} }};"
            elif isinstance(stmt.value, ast.Dict) and csharp_type.startswith("Dictionary<"):
                line = f"{csharp_type} {self._ident(name)} = new {csharp_type}();"
            elif isinstance(stmt.value, ast.Set) and csharp_type.startswith("HashSet<"):
                values = ", ".join(self.transpile_expr(e) for e in stmt.value.elts)
                line = f"{csharp_type} {self._ident(name)} = new {csharp_type} {{ {values} }};"
            else:
                line = f"{csharp_type} {self._ident(name)} = {self.transpile_expr(stmt.value)};"
        scope.declared.add(name)
        if csharp_type == "Pytra.CsModule.py_path" or (stmt.value is not None and self._is_path_like_expr(stmt.value)):
            self.path_like_names.add(name)
        return [line]

    def _transpile_assign(self, stmt: ast.Assign, scope: Scope) -> List[str]:
        if len(stmt.targets) != 1:
            return [f"// unsupported assignment: {ast.unparse(stmt)}"]
        if isinstance(stmt.targets[0], ast.Tuple):
            tuple_target = stmt.targets[0]
            if not all(isinstance(elt, ast.Name) for elt in tuple_target.elts):
                return [f"// unsupported tuple assignment: {ast.unparse(stmt)}"]
            tmp_name = self._new_temp("tuple")
            lines = [f"var {tmp_name} = {self.transpile_expr(stmt.value)};"]
            for i, elt in enumerate(tuple_target.elts, start=1):
                name = elt.id
                if name not in scope.declared:
                    scope.declared.add(name)
                    lines.append(f"var {self._ident(name)} = {tmp_name}.Item{i};")
                else:
                    lines.append(f"{self._ident(name)} = {tmp_name}.Item{i};")
            return lines
        if isinstance(stmt.targets[0], ast.Attribute):
            target = self.transpile_expr(stmt.targets[0])
            return [f"{target} = {self.transpile_expr(stmt.value)};"]
        if isinstance(stmt.targets[0], ast.Subscript):
            target = stmt.targets[0]
            if isinstance(target.slice, ast.Slice):
                return [f"// unsupported slice assignment: {ast.unparse(stmt)}"]
            return [
                "Pytra.CsModule.py_runtime.py_set("
                f"{self.transpile_expr(target.value)}, "
                f"{self.transpile_expr(target.slice)}, "
                f"{self.transpile_expr(stmt.value)});"
            ]
        if not isinstance(stmt.targets[0], ast.Name):
            return [f"// unsupported assignment: {ast.unparse(stmt)}"]

        name = stmt.targets[0].id
        if name not in scope.declared:
            scope.declared.add(name)
            inferred_type = self._infer_expr_csharp_type(stmt.value)
            if inferred_type == "Pytra.CsModule.py_path" or self._is_path_like_expr(stmt.value):
                self.path_like_names.add(name)
            if inferred_type is not None:
                return [f"{inferred_type} {self._ident(name)} = {self.transpile_expr(stmt.value)};"]
            return [f"var {self._ident(name)} = {self.transpile_expr(stmt.value)};"]
        if self._is_path_like_expr(stmt.value):
            self.path_like_names.add(name)

        return [f"{self._ident(name)} = {self.transpile_expr(stmt.value)};"]

    def _transpile_aug_assign(self, stmt: ast.AugAssign) -> List[str]:
        target = self.transpile_expr(stmt.target)
        value = self.transpile_expr(stmt.value)
        if isinstance(stmt.op, ast.Pow):
            return [f"{target} = Math.Pow({target}, {value});"]
        if isinstance(stmt.op, ast.FloorDiv):
            return [f"{target} = Pytra.CsModule.py_runtime.py_floordiv({target}, {value});"]
        if isinstance(stmt.op, ast.Mod):
            return [f"{target} = Pytra.CsModule.py_runtime.py_mod({target}, {value});"]
        if isinstance(stmt.op, ast.LShift):
            return [f"{target} = ({target} << (int)({value}));"]
        if isinstance(stmt.op, ast.RShift):
            return [f"{target} = ({target} >> (int)({value}));"]
        return [f"{target} = ({target} {self._binop(stmt.op)} {value});"]

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

        range_args = self._parse_range_args(stmt.iter)
        lines: List[str] = []
        body_scope = Scope(declared=set(scope.declared))

        if range_args is not None and tuple_target is None:
            start_expr, stop_expr, step_expr = range_args
            start_var = self._new_temp("range_start")
            stop_var = self._new_temp("range_stop")
            step_var = self._new_temp("range_step")
            loop_target_name = target_name if target_name != "_" else self._new_temp("unused")
            out_target = self._ident(loop_target_name)
            lines.append(f"var {start_var} = {start_expr};")
            lines.append(f"var {stop_var} = {stop_expr};")
            lines.append(f"var {step_var} = {step_expr};")
            lines.append(f"if ({step_var} == 0) throw new Exception(\"range() arg 3 must not be zero\");")
            if target_name != "_" and target_name in scope.declared:
                init_part = f"{out_target} = {start_var}"
            else:
                init_part = f"var {out_target} = {start_var}"
                body_scope.declared.add(loop_target_name)
            lines.append(
                f"for ({init_part}; "
                f"({step_var} > 0) ? ({out_target} < {stop_var}) : ({out_target} > {stop_var}); "
                f"{out_target} += {step_var})"
            )
            lines.append("{")
        else:
            loop_target_name = target_name if target_name != "_" else self._new_temp("unused")
            out_target = self._ident(loop_target_name)
            lines.extend([f"foreach (var {out_target} in {self.transpile_expr(stmt.iter)})", "{"])
            body_scope.declared.add(loop_target_name)

        if tuple_target is not None:
            for i, elt in enumerate(tuple_target.elts, start=1):
                lines.extend(self._indent_block([f"var {self._ident(elt.id)} = {out_target}.Item{i};"]))
                body_scope.declared.add(elt.id)
        body_lines = self.transpile_statements(stmt.body, body_scope)
        lines.extend(self._indent_block(body_lines))
        lines.append("}")
        if stmt.orelse:
            lines.append("// for-else is not directly supported; else body emitted below")
            lines.extend(self.transpile_statements(stmt.orelse, Scope(declared=set(scope.declared))))
        return lines

    def _transpile_while(self, stmt: ast.While, scope: Scope) -> List[str]:
        if isinstance(stmt.test, ast.Constant) and isinstance(stmt.test.value, bool):
            cond = "true" if stmt.test.value else "false"
            lines = [f"while ({cond})", "{"]
        else:
            lines = [f"while (Pytra.CsModule.py_runtime.py_bool({self.transpile_expr(stmt.test)}))", "{"]
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
        lines = [f"if (Pytra.CsModule.py_runtime.py_bool({self.transpile_expr(stmt.test)}))", "{"]
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
            return self._ident(expr.id)
        if isinstance(expr, ast.Attribute):
            if isinstance(expr.value, ast.Name) and expr.value.id == "math":
                if expr.attr == "pi":
                    return "Math.PI"
                if expr.attr == "e":
                    return "Math.E"
            if self._is_path_like_expr(expr.value):
                base = self.transpile_expr(expr.value)
                if expr.attr == "parent":
                    return f"{base}.parent()"
                if expr.attr == "name":
                    return f"{base}.name()"
                if expr.attr == "stem":
                    return f"{base}.stem()"
            if (
                isinstance(expr.value, ast.Name)
                and expr.value.id == "self"
                and self.current_class_name is not None
                and expr.attr in self.current_static_fields
            ):
                return f"{self._ident(self.current_class_name)}.{self._ident(expr.attr)}"
            return f"{self.transpile_expr(expr.value)}.{self._ident(expr.attr)}"
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
            if isinstance(expr.op, ast.Div):
                if self._is_path_like_expr(expr.left):
                    return f"({left} / {right})"
                return f"((double)({left}) / (double)({right}))"
            if isinstance(expr.op, ast.FloorDiv):
                return f"Pytra.CsModule.py_runtime.py_floordiv({left}, {right})"
            if isinstance(expr.op, ast.Mod):
                return f"Pytra.CsModule.py_runtime.py_mod({left}, {right})"
            if isinstance(expr.op, ast.LShift):
                return f"({left} << (int)({right}))"
            if isinstance(expr.op, ast.RShift):
                return f"({left} >> (int)({right}))"
            return f"({left} {self._binop(expr.op)} {right})"
        if isinstance(expr, ast.UnaryOp):
            return f"({self._unaryop(expr.op)}{self.transpile_expr(expr.operand)})"
        if isinstance(expr, ast.BoolOp):
            op = self._boolop(expr.op)
            return "(" + f" {op} ".join(self.transpile_expr(v) for v in expr.values) + ")"
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
                start_expr = f"(long?)({self.transpile_expr(expr.slice.lower)})"
                stop_expr = f"(long?)({self.transpile_expr(expr.slice.upper)})"
                return (
                    f"Pytra.CsModule.py_runtime.py_slice("
                    f"{self.transpile_expr(expr.value)}, {start_expr}, {stop_expr})"
                )
            return (
                "Pytra.CsModule.py_runtime.py_get("
                f"{self.transpile_expr(expr.value)}, {self.transpile_expr(expr.slice)})"
            )
        if isinstance(expr, ast.IfExp):
            return (
                f"(Pytra.CsModule.py_runtime.py_bool({self.transpile_expr(expr.test)}) ? {self.transpile_expr(expr.body)} : "
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
        if isinstance(call.func, ast.Name) and call.func.id == "len":
            if len(args_list) == 1:
                return f"Pytra.CsModule.py_runtime.py_len({args_list[0]})"
            return "0L"
        if isinstance(call.func, ast.Name) and call.func.id == "perf_counter":
            return "Pytra.CsModule.time.perf_counter()"
        if isinstance(call.func, ast.Name) and call.func.id == "bytearray":
            if len(args_list) == 0:
                return "new List<byte>()"
            if len(args_list) == 1:
                return f"Pytra.CsModule.py_runtime.py_bytearray({args_list[0]})"
            return "new List<byte>()"
        if isinstance(call.func, ast.Name) and call.func.id == "bytes":
            if len(args_list) == 0:
                return "new List<byte>()"
            if len(args_list) == 1:
                return f"Pytra.CsModule.py_runtime.py_bytes({args_list[0]})"
            return "new List<byte>()"
        if isinstance(call.func, ast.Name) and call.func.id == "int":
            if len(args_list) == 1:
                return f"Pytra.CsModule.py_runtime.py_int({args_list[0]})"
            return "0"
        if isinstance(call.func, ast.Name) and call.func.id == "Path":
            if len(args_list) == 1:
                return f"new Pytra.CsModule.py_path(Convert.ToString({args_list[0]}))"
            return "new Pytra.CsModule.py_path(\"\")"
        if isinstance(call.func, ast.Name) and call.func.id == "float":
            if len(args_list) == 1:
                return f"(double)({args_list[0]})"
            return "0.0"
        if isinstance(call.func, ast.Name) and call.func.id == "str":
            if len(args_list) == 1:
                return f"Convert.ToString({args_list[0]})"
            return "\"\""
        if isinstance(call.func, ast.Name) and call.func.id == "ord":
            if len(args_list) == 1:
                return f"Pytra.CsModule.py_runtime.py_ord({args_list[0]})"
            return "0L"
        if isinstance(call.func, ast.Name) and call.func.id == "max":
            if len(args_list) == 2:
                return f"(({args_list[0]}) > ({args_list[1]}) ? ({args_list[0]}) : ({args_list[1]}))"
            return "0"
        if isinstance(call.func, ast.Name) and call.func.id == "min":
            if len(args_list) == 2:
                return f"(({args_list[0]}) < ({args_list[1]}) ? ({args_list[0]}) : ({args_list[1]}))"
            return "0"

        if isinstance(call.func, ast.Name):
            if call.func.id == "save_gif":
                return f"Pytra.CsModule.gif_helper.save_gif({args})"
            if call.func.id == "grayscale_palette":
                return "Pytra.CsModule.gif_helper.grayscale_palette()"
            if call.func.id in self.class_names:
                return f"new {self._ident(call.func.id)}({args})"
            return f"{self._ident(call.func.id)}({args})"
        if isinstance(call.func, ast.Attribute):
            if (
                isinstance(call.func.value, ast.Name)
                and call.func.value.id == "pathlib"
                and call.func.attr == "Path"
            ):
                if len(args_list) == 1:
                    return f"new Pytra.CsModule.py_path(Convert.ToString({args_list[0]}))"
                return "new Pytra.CsModule.py_path(\"\")"
            if isinstance(call.func.value, ast.Name) and call.func.value.id == "math":
                math_map = {
                    "sqrt": "Sqrt",
                    "sin": "Sin",
                    "cos": "Cos",
                    "tan": "Tan",
                    "exp": "Exp",
                    "log": "Log",
                    "log10": "Log10",
                    "floor": "Floor",
                    "ceil": "Ceiling",
                    "fabs": "Abs",
                    "pow": "Pow",
                }
                mapped = math_map.get(call.func.attr, call.func.attr)
                return f"Math.{mapped}({args})"
            if (
                isinstance(call.func.value, ast.Name)
                and call.func.value.id == "png_helper"
                and call.func.attr == "write_rgb_png"
            ):
                return f"Pytra.CsModule.png_helper.write_rgb_png({args})"
            if call.func.attr == "append" and len(args_list) == 1:
                return (
                    "Pytra.CsModule.py_runtime.py_append("
                    f"{self.transpile_expr(call.func.value)}, {args_list[0]})"
                )
            if call.func.attr == "pop":
                if len(args_list) == 0:
                    return f"Pytra.CsModule.py_runtime.py_pop({self.transpile_expr(call.func.value)})"
                if len(args_list) == 1:
                    return (
                        "Pytra.CsModule.py_runtime.py_pop("
                        f"{self.transpile_expr(call.func.value)}, {args_list[0]})"
                    )
            if call.func.attr == "isdigit" and len(args_list) == 0:
                return f"Pytra.CsModule.py_runtime.py_isdigit({self.transpile_expr(call.func.value)})"
            if call.func.attr == "isalpha" and len(args_list) == 0:
                return f"Pytra.CsModule.py_runtime.py_isalpha({self.transpile_expr(call.func.value)})"
            return f"{self.transpile_expr(call.func)}({args})"

        return f"{self.transpile_expr(call.func)}({args})"

    def _is_path_like_expr(self, expr: ast.expr) -> bool:
        if isinstance(expr, ast.Name):
            return expr.id in self.path_like_names
        if isinstance(expr, ast.Call):
            if isinstance(expr.func, ast.Name) and expr.func.id == "Path":
                return True
            if (
                isinstance(expr.func, ast.Attribute)
                and isinstance(expr.func.value, ast.Name)
                and expr.func.value.id == "pathlib"
                and expr.func.attr == "Path"
            ):
                return True
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Div):
            return self._is_path_like_expr(expr.left)
        return False

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
                **CS_PRIMITIVE_TYPES,
                "bytearray": "List<byte>",
                "bytes": "List<byte>",
                "Path": "Pytra.CsModule.py_path",
                "list": "List<object>",
                "set": "HashSet<object>",
                "dict": "Dictionary<object, object>",
                "tuple": "Tuple<object>",
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

    def _constant(self, value: object) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "null"
        if isinstance(value, int):
            return f"{value}L"
        if isinstance(value, str):
            escaped = (
                value.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\t", "\\t")
                .replace("\r", "\\r")
            )
            return f'"{escaped}"'
        return repr(value)

    def _binop(self, op: ast.operator) -> str:
        mapping = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.FloorDiv: "/",
            ast.Mod: "%",
            ast.BitOr: "|",
            ast.BitAnd: "&",
            ast.BitXor: "^",
            ast.LShift: "<<",
            ast.RShift: ">>",
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

    def _transpile_chained_compare(self, expr: ast.Compare) -> str:
        items: List[str] = []
        left_node = expr.left
        for i, op in enumerate(expr.ops):
            right_node = expr.comparators[i]
            items.append(self._transpile_compare(left_node, op, right_node))
            left_node = right_node
        if len(items) == 0:
            return "true"
        return "(" + " && ".join(items) + ")"

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
                parts.append(
                    value.value.replace("\\", "\\\\")
                    .replace('"', '\\"')
                    .replace("\n", "\\n")
                    .replace("\t", "\\t")
                    .replace("\r", "\\r")
                    .replace("{", "{{")
                    .replace("}", "}}")
                )
            elif isinstance(value, ast.FormattedValue):
                parts.append("{" + self.transpile_expr(value.value) + "}")
            else:
                parts.append("{/*unsupported*/}")
        return '$"' + "".join(parts).replace('"', '\\"') + '"'

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
