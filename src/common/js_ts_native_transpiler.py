"""Python AST を JavaScript / TypeScript へ変換する共通トランスパイラ。"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from .base_transpiler import BaseTranspiler, TranspileError
from .transpile_shared import Scope


@dataclass
class JsTsConfig:
    """JS/TS 生成設定。"""

    language_name: str
    file_header: str
    runtime_ext: str


class JsTsNativeTranspiler(BaseTranspiler):
    """Python サブセットを JS/TS へ変換する共通実装。"""

    def __init__(self, config: JsTsConfig) -> None:
        super().__init__(temp_prefix="__pytra")
        self.config = config
        self.class_names: set[str] = set()
        self.class_static_fields: dict[str, set[str]] = {}
        self.current_class: str | None = None
        self.scope_stack: list[Scope] = []
        self._import_lines: list[str] = []
        self.path_like_names: set[str] = set()

    def transpile_path(self, input_path: Path) -> str:
        module = ast.parse(input_path.read_text(encoding="utf-8"), filename=str(input_path))
        return self.transpile_module(module)

    def transpile_module(self, module: ast.Module) -> str:
        self.class_names = {stmt.name for stmt in module.body if isinstance(stmt, ast.ClassDef)}
        self._import_lines = self._build_runtime_imports()
        self.path_like_names = set()

        body_lines: list[str] = []
        for stmt in module.body:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                self._import_lines.extend(self._transpile_import(stmt))
                continue
            if self._is_main_guard(stmt):
                body_lines.extend(self.transpile_statements(stmt.body, Scope(declared=set())))
                continue
            body_lines.extend(self.transpile_statements([stmt], Scope(declared=set())))

        out: list[str] = [self.config.file_header, ""]
        out.extend(self._import_lines)
        out.append("")
        out.extend(body_lines)
        out.append("")
        return "\n".join(out)

    def _build_runtime_imports(self) -> list[str]:
        ext = self.config.runtime_ext
        lines = [
            "const __pytra_root = process.cwd();",
            f"const py_runtime = require(__pytra_root + '/src/{'js_module' if ext == 'js' else 'ts_module'}/py_runtime.{ext}');",
            f"const py_math = require(__pytra_root + '/src/{'js_module' if ext == 'js' else 'ts_module'}/math.{ext}');",
            f"const py_time = require(__pytra_root + '/src/{'js_module' if ext == 'js' else 'ts_module'}/time.{ext}');",
            f"const pathlib = require(__pytra_root + '/src/{'js_module' if ext == 'js' else 'ts_module'}/pathlib.{ext}');",
            "const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;",
            "const { perfCounter } = py_time;",
        ]
        return lines

    def _transpile_import(self, stmt: ast.stmt) -> list[str]:
        ext = self.config.runtime_ext
        module_dir = "js_module" if ext == "js" else "ts_module"
        if isinstance(stmt, ast.Import):
            lines: list[str] = []
            for alias in stmt.names:
                name = alias.asname or alias.name
                if alias.name == "math":
                    lines.append(f"const {name} = require(__pytra_root + '/src/{module_dir}/math.{ext}');")
                elif alias.name == "time":
                    lines.append(f"const {name} = require(__pytra_root + '/src/{module_dir}/time.{ext}');")
                elif alias.name == "pathlib":
                    lines.append(f"const {name} = require(__pytra_root + '/src/{module_dir}/pathlib.{ext}');")
                elif alias.name in {"py_module", "pylib"}:
                    continue
                else:
                    # __future__ 等は無視
                    if alias.name != "__future__":
                        raise TranspileError(f"unsupported import: {alias.name}")
            return lines
        assert isinstance(stmt, ast.ImportFrom)
        mod = stmt.module or ""
        if mod == "time":
            mapped: list[str] = []
            for alias in stmt.names:
                if alias.name == "perf_counter":
                    asname = alias.asname or alias.name
                    mapped.append(f"const {asname} = perfCounter;")
                else:
                    raise TranspileError(f"unsupported from time import {alias.name}")
            return mapped
        if mod == "dataclasses":
            return []
        if mod == "pathlib":
            mapped: list[str] = []
            for alias in stmt.names:
                if alias.name == "Path":
                    asname = alias.asname or alias.name
                    mapped.append(f"const {asname} = pathlib.Path;")
                else:
                    raise TranspileError(f"unsupported from pathlib import {alias.name}")
            return mapped
        if mod in {"py_module", "pylib"}:
            lines: list[str] = []
            for alias in stmt.names:
                if alias.name in {"png_helper", "png"}:
                    asname = alias.asname or alias.name
                    lines.append(f"const {asname} = require(__pytra_root + '/src/{module_dir}/png_helper.{ext}');")
                else:
                    raise TranspileError(f"unsupported from {mod} import {alias.name}")
            return lines
        if mod in {"py_module.gif_helper", "pylib.gif_helper", "pylib.gif"}:
            names = []
            for alias in stmt.names:
                asname = alias.asname or alias.name
                names.append(f"{alias.name}: {asname}" if asname != alias.name else alias.name)
            joined = ", ".join(names)
            return [f"const {{ {joined} }} = require(__pytra_root + '/src/{module_dir}/gif_helper.{ext}');"]
        if mod == "__future__":
            return []
        raise TranspileError(f"unsupported import-from: {mod}")

    def transpile_statements(self, stmts: list[ast.stmt], scope: Scope) -> list[str]:
        self.scope_stack.append(scope)
        out: list[str] = []
        for stmt in stmts:
            if isinstance(stmt, ast.Pass):
                continue
            if isinstance(stmt, ast.Return):
                out.append("return;" if stmt.value is None else f"return {self.transpile_expr(stmt.value)};")
                continue
            if isinstance(stmt, ast.Expr):
                if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                    continue
                out.append(f"{self.transpile_expr(stmt.value)};")
                continue
            if isinstance(stmt, ast.FunctionDef):
                out.append(self.transpile_function(stmt))
                continue
            if isinstance(stmt, ast.ClassDef):
                out.append(self.transpile_class(stmt))
                continue
            if isinstance(stmt, ast.AnnAssign):
                out.extend(self._transpile_assign_like(stmt.target, stmt.value, scope, declared_by_ann=True))
                continue
            if isinstance(stmt, ast.Assign):
                if len(stmt.targets) != 1:
                    raise TranspileError("multiple assignment targets are not supported")
                out.extend(self._transpile_assign_like(stmt.targets[0], stmt.value, scope, declared_by_ann=False))
                continue
            if isinstance(stmt, ast.AugAssign):
                target = self._transpile_lvalue(stmt.target)
                out.append(f"{target} = {target} {self._binop(stmt.op)} {self.transpile_expr(stmt.value)};")
                continue
            if isinstance(stmt, ast.If):
                out.extend(self._transpile_if(stmt, scope))
                continue
            if isinstance(stmt, ast.While):
                out.append(f"while (pyBool({self.transpile_expr(stmt.test)})) {{")
                out.extend(self._indent_block(self.transpile_statements(stmt.body, Scope(declared=set(scope.declared)))))
                out.append("}")
                continue
            if isinstance(stmt, ast.For):
                out.extend(self._transpile_for(stmt, scope))
                continue
            if isinstance(stmt, ast.Try):
                out.extend(self._transpile_try(stmt, scope))
                continue
            if isinstance(stmt, ast.Raise):
                if stmt.exc is None:
                    out.append("throw new Error('raise');")
                else:
                    out.append(f"throw {self.transpile_expr(stmt.exc)};")
                continue
            if isinstance(stmt, ast.Break):
                out.append("break;")
                continue
            if isinstance(stmt, ast.Continue):
                out.append("continue;")
                continue
            raise TranspileError(f"unsupported statement: {type(stmt).__name__}")
        self.scope_stack.pop()
        return out

    def _transpile_assign_like(self, target: ast.expr, value: ast.expr | None, scope: Scope, *, declared_by_ann: bool) -> list[str]:
        rhs = "null" if value is None else self.transpile_expr(value)
        out: list[str] = []
        is_path_rhs = value is not None and self._is_path_like_expr(value)
        if isinstance(target, ast.Tuple):
            if value is None:
                raise TranspileError("tuple assignment requires value")
            tmp = self._new_temp("tuple")
            out.append(f"const {tmp} = {rhs};")
            for i, elt in enumerate(target.elts):
                if not isinstance(elt, ast.Name):
                    raise TranspileError("tuple assignment target must be names")
                name = elt.id
                if name in scope.declared:
                    out.append(f"{name} = {tmp}[{i}];")
                else:
                    scope.declared.add(name)
                    out.append(f"let {name} = {tmp}[{i}];")
            return out
        if isinstance(target, ast.Name):
            name = target.id
            if name in scope.declared:
                out.append(f"{name} = {rhs};")
            else:
                scope.declared.add(name)
                # Python の変数は再代入可能なので、型注釈のみ宣言でも let で保持する。
                out.append(f"let {name} = {rhs};")
            if is_path_rhs:
                self.path_like_names.add(name)
            return out
        lvalue = self._transpile_lvalue(target)
        out.append(f"{lvalue} = {rhs};")
        return out

    def transpile_function(self, fn: ast.FunctionDef) -> str:
        args = [a.arg for a in fn.args.args]
        scope = Scope(declared=set(args))
        body = self.transpile_statements(fn.body, scope)
        lines = [f"function {fn.name}({', '.join(args)}) {{"]
        lines.extend(self._indent_block(body))
        lines.append("}")
        return "\n".join(lines)

    def transpile_class(self, cls: ast.ClassDef) -> str:
        is_dataclass = any(
            (isinstance(d, ast.Name) and d.id == "dataclass")
            or (isinstance(d, ast.Attribute) and d.attr == "dataclass")
            for d in cls.decorator_list
        )
        base = ""
        if len(cls.bases) > 1:
            raise TranspileError("multiple inheritance is not supported")
        if len(cls.bases) == 1:
            if not isinstance(cls.bases[0], ast.Name):
                raise TranspileError("class base must be name")
            base = f" extends {cls.bases[0].id}"

        static_fields: list[tuple[str, str]] = []
        methods: list[ast.FunctionDef] = []
        init_fn: ast.FunctionDef | None = None
        dataclass_fields: list[str] = []
        dataclass_defaults: dict[str, str] = {}

        for stmt in cls.body:
            if isinstance(stmt, ast.FunctionDef):
                if stmt.name == "__init__":
                    init_fn = stmt
                else:
                    methods.append(stmt)
                continue
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                if is_dataclass:
                    dataclass_fields.append(stmt.target.id)
                    if stmt.value is not None:
                        dataclass_defaults[stmt.target.id] = self.transpile_expr(stmt.value)
                else:
                    static_fields.append((stmt.target.id, "null" if stmt.value is None else self.transpile_expr(stmt.value)))
                continue
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                if is_dataclass:
                    dataclass_fields.append(stmt.targets[0].id)
                    dataclass_defaults[stmt.targets[0].id] = self.transpile_expr(stmt.value)
                else:
                    static_fields.append((stmt.targets[0].id, self.transpile_expr(stmt.value)))
                continue
            if isinstance(stmt, ast.Pass):
                continue
            raise TranspileError(f"unsupported class member: {type(stmt).__name__}")

        self.class_static_fields[cls.name] = {name for name, _ in static_fields}

        lines = [f"class {cls.name}{base} {{"]
        if init_fn is not None:
            args = [a.arg for a in init_fn.args.args[1:]]
            scope = Scope(declared=set(args) | {"self"})
            prev = self.current_class
            self.current_class = cls.name
            body = self.transpile_statements(init_fn.body, scope)
            self.current_class = prev
            lines.append(f"{self.INDENT}constructor({', '.join(args)}) {{")
            if base:
                lines.append(f"{self.INDENT * 2}super();")
            lines.extend([f"{self.INDENT}{line}" for line in self._indent_block(body)])
            lines.append(f"{self.INDENT}}}")
        elif is_dataclass:
            args: list[str] = []
            for name in dataclass_fields:
                if name in dataclass_defaults:
                    args.append(f"{name} = {dataclass_defaults[name]}")
                else:
                    args.append(name)
            lines.append(f"{self.INDENT}constructor({', '.join(args)}) {{")
            if base:
                lines.append(f"{self.INDENT * 2}super();")
            for name in dataclass_fields:
                lines.append(f"{self.INDENT * 2}this.{name} = {name};")
            lines.append(f"{self.INDENT}}}")
        else:
            if base:
                lines.append(f"{self.INDENT}constructor() {{")
                lines.append(f"{self.INDENT * 2}super();")
                lines.append(f"{self.INDENT}}}")
            else:
                lines.append(f"{self.INDENT}constructor() {{}}")

        prev = self.current_class
        self.current_class = cls.name
        for m in methods:
            lines.append("")
            args = [a.arg for a in m.args.args[1:]] if m.args.args and m.args.args[0].arg == "self" else [a.arg for a in m.args.args]
            scope = Scope(declared=set(args) | {"self"})
            body = self.transpile_statements(m.body, scope)
            lines.append(f"{self.INDENT}{m.name}({', '.join(args)}) {{")
            lines.extend([f"{self.INDENT}{line}" for line in self._indent_block(body)])
            lines.append(f"{self.INDENT}}}")
        self.current_class = prev

        lines.append("}")
        for name, expr in static_fields:
            lines.append(f"{cls.name}.{name} = {expr};")
        return "\n".join(lines)

    def _transpile_if(self, stmt: ast.If, scope: Scope) -> list[str]:
        lines = [f"if (pyBool({self.transpile_expr(stmt.test)})) {{"]
        lines.extend(self._indent_block(self.transpile_statements(stmt.body, Scope(declared=set(scope.declared)))))
        if stmt.orelse:
            lines.append("} else {")
            lines.extend(self._indent_block(self.transpile_statements(stmt.orelse, Scope(declared=set(scope.declared)))))
        lines.append("}")
        return lines

    def _transpile_for(self, stmt: ast.For, scope: Scope) -> list[str]:
        if not isinstance(stmt.target, ast.Name):
            raise TranspileError("for target must be name")
        target = stmt.target.id
        rng = self._parse_range_args(stmt.iter)
        lines: list[str] = []
        body_scope = Scope(declared=set(scope.declared) | {target})
        if target not in scope.declared:
            scope.declared.add(target)
            lines.append(f"let {target};")
        if rng is not None:
            start, stop, step = rng
            i_name = self._new_temp("i")
            if step == "1":
                lines.append(f"for (let {i_name} = {start}; {i_name} < {stop}; {i_name} += 1) {{")
            else:
                lines.append(
                    f"for (let {i_name} = {start}; ({step} > 0 ? {i_name} < {stop} : {i_name} > {stop}); {i_name} += {step}) {{"
                )
            lines.append(f"{self.INDENT}{target} = {i_name};")
            lines.extend(self._indent_block(self.transpile_statements(stmt.body, body_scope)))
            lines.append("}")
            return lines

        iter_expr = self.transpile_expr(stmt.iter)
        it_name = self._new_temp("it")
        lines.append(f"for (const {it_name} of {iter_expr}) {{")
        lines.append(f"{self.INDENT}{target} = {it_name};")
        lines.extend(self._indent_block(self.transpile_statements(stmt.body, body_scope)))
        lines.append("}")
        return lines

    def _transpile_try(self, stmt: ast.Try, scope: Scope) -> list[str]:
        lines = ["try {"]
        lines.extend(self._indent_block(self.transpile_statements(stmt.body, Scope(declared=set(scope.declared)))))
        lines.append("}")
        if stmt.handlers:
            if len(stmt.handlers) != 1:
                raise TranspileError("only single except is supported")
            h = stmt.handlers[0]
            ex_name = h.name or "ex"
            lines.append(f"catch ({ex_name}) {{")
            lines.extend(self._indent_block(self.transpile_statements(h.body, Scope(declared=set(scope.declared) | {ex_name})) ))
            lines.append("}")
        if stmt.finalbody:
            lines.append("finally {")
            lines.extend(self._indent_block(self.transpile_statements(stmt.finalbody, Scope(declared=set(scope.declared)))))
            lines.append("}")
        return lines

    def _transpile_lvalue(self, expr: ast.expr) -> str:
        if isinstance(expr, ast.Name):
            return expr.id
        if isinstance(expr, ast.Attribute):
            return self.transpile_expr(expr)
        if isinstance(expr, ast.Subscript):
            if isinstance(expr.slice, ast.Slice):
                raise TranspileError("slice assignment is not supported")
            return f"{self.transpile_expr(expr.value)}[{self.transpile_expr(expr.slice)}]"
        raise TranspileError("unsupported assignment target")

    def transpile_expr(self, expr: ast.expr) -> str:
        if isinstance(expr, ast.Name):
            if expr.id == "self":
                return "this"
            if expr.id == "True":
                return "true"
            if expr.id == "False":
                return "false"
            if expr.id == "None":
                return "null"
            return expr.id
        if isinstance(expr, ast.Constant):
            if isinstance(expr.value, str):
                return self._string_literal(expr.value)
            if expr.value is None:
                return "null"
            if isinstance(expr.value, bool):
                return "true" if expr.value else "false"
            return repr(expr.value)
        if isinstance(expr, ast.Attribute):
            if isinstance(expr.value, ast.Name) and expr.value.id == "self":
                if (
                    self.current_class is not None
                    and expr.attr in self.class_static_fields.get(self.current_class, set())
                ):
                    return f"{self.current_class}.{expr.attr}"
                return f"this.{expr.attr}"
            if self._is_path_like_expr(expr.value):
                base = self.transpile_expr(expr.value)
                if expr.attr == "parent":
                    return f"{base}.parent()"
                if expr.attr == "name":
                    return f"{base}.name()"
                if expr.attr == "stem":
                    return f"{base}.stem()"
            return f"{self.transpile_expr(expr.value)}.{expr.attr}"
        if isinstance(expr, ast.BinOp):
            l = self.transpile_expr(expr.left)
            r = self.transpile_expr(expr.right)
            if isinstance(expr.op, ast.Div) and self._is_path_like_expr(expr.left):
                return f"pathlib.pathJoin({l}, {r})"
            if isinstance(expr.op, ast.FloorDiv):
                return f"pyFloorDiv({l}, {r})"
            if isinstance(expr.op, ast.Mod):
                return f"pyMod({l}, {r})"
            return f"(({l}) {self._binop(expr.op)} ({r}))"
        if isinstance(expr, ast.UnaryOp):
            if isinstance(expr.op, ast.Not):
                return f"(!pyBool({self.transpile_expr(expr.operand)}))"
            if isinstance(expr.op, ast.USub):
                return f"(-({self.transpile_expr(expr.operand)}))"
            raise TranspileError("unsupported unary op")
        if isinstance(expr, ast.BoolOp):
            op = "&&" if isinstance(expr.op, ast.And) else "||"
            return "(" + f" {op} ".join(self.transpile_expr(v) for v in expr.values) + ")"
        if isinstance(expr, ast.Compare):
            if len(expr.ops) != 1 or len(expr.comparators) != 1:
                raise TranspileError("chained compare is not supported")
            l = self.transpile_expr(expr.left)
            r = self.transpile_expr(expr.comparators[0])
            op = expr.ops[0]
            if isinstance(op, ast.In):
                return f"pyIn({l}, {r})"
            if isinstance(op, ast.NotIn):
                return f"(!pyIn({l}, {r}))"
            return f"(({l}) {self._cmpop(op)} ({r}))"
        if isinstance(expr, ast.Call):
            return self._transpile_call(expr)
        if isinstance(expr, ast.IfExp):
            return f"(pyBool({self.transpile_expr(expr.test)}) ? {self.transpile_expr(expr.body)} : {self.transpile_expr(expr.orelse)})"
        if isinstance(expr, ast.List):
            return "[" + ", ".join(self.transpile_expr(e) for e in expr.elts) + "]"
        if isinstance(expr, ast.Tuple):
            return "[" + ", ".join(self.transpile_expr(e) for e in expr.elts) + "]"
        if isinstance(expr, ast.Dict):
            if any(k is None for k in expr.keys):
                raise TranspileError("dict unpacking is not supported")
            items = []
            for k, v in zip(expr.keys, expr.values):
                items.append(f"[{self.transpile_expr(k)}, {self.transpile_expr(v)}]")
            return "Object.fromEntries([" + ", ".join(items) + "])"
        if isinstance(expr, ast.Subscript):
            if isinstance(expr.slice, ast.Slice):
                start = "null" if expr.slice.lower is None else self.transpile_expr(expr.slice.lower)
                end = "null" if expr.slice.upper is None else self.transpile_expr(expr.slice.upper)
                return f"pySlice({self.transpile_expr(expr.value)}, {start}, {end})"
            return f"{self.transpile_expr(expr.value)}[{self.transpile_expr(expr.slice)}]"
        if isinstance(expr, ast.JoinedStr):
            return self._transpile_fstring(expr)
        if isinstance(expr, ast.ListComp):
            return self._transpile_list_comp(expr)
        raise TranspileError(f"unsupported expression: {type(expr).__name__}")

    def _transpile_call(self, expr: ast.Call) -> str:
        if any(kw.arg is None for kw in expr.keywords):
            raise TranspileError("**kwargs is not supported")
        args = [self.transpile_expr(a) for a in list(expr.args) + [kw.value for kw in expr.keywords]]
        if isinstance(expr.func, ast.Name):
            fn = expr.func.id
            if fn in self.class_names:
                return f"new {fn}({', '.join(args)})"
            if fn == "Path":
                if len(args) != 1:
                    raise TranspileError("Path() requires one argument")
                return f"new pathlib.Path({args[0]})"
            if fn == "print":
                return f"pyPrint({', '.join(args)})"
            if fn == "len":
                return f"pyLen({args[0]})"
            if fn == "range":
                if len(args) == 1:
                    return f"pyRange(0, {args[0]}, 1)"
                if len(args) == 2:
                    return f"pyRange({args[0]}, {args[1]}, 1)"
                if len(args) == 3:
                    return f"pyRange({args[0]}, {args[1]}, {args[2]})"
                raise TranspileError("range() argument count")
            if fn == "int":
                return f"Math.trunc(Number({args[0]}))"
            if fn == "float":
                return f"Number({args[0]})"
            if fn == "str":
                return f"String({args[0]})"
            if fn == "ord":
                return f"pyOrd({args[0]})"
            if fn == "chr":
                return f"pyChr({args[0]})"
            if fn == "bytearray":
                if len(args) == 0:
                    return "pyBytearray()"
                if len(args) == 1:
                    return f"pyBytearray({args[0]})"
                raise TranspileError("bytearray arg count")
            if fn == "bytes":
                if len(args) == 1:
                    return f"pyBytes({args[0]})"
                raise TranspileError("bytes arg count")
            if fn == "min":
                return f"Math.min({', '.join(args)})"
            if fn == "max":
                return f"Math.max({', '.join(args)})"
            if fn == "RuntimeError":
                return f"new Error({args[0] if args else self._string_literal('RuntimeError')})"
            return f"{fn}({', '.join(args)})"

        if isinstance(expr.func, ast.Attribute):
            obj = self.transpile_expr(expr.func.value)
            m = expr.func.attr
            if isinstance(expr.func.value, ast.Name) and expr.func.value.id == "pathlib" and m == "Path":
                if len(args) != 1:
                    raise TranspileError("pathlib.Path() requires one argument")
                return f"new pathlib.Path({args[0]})"
            if isinstance(expr.func.value, ast.Name) and expr.func.value.id == "math":
                if m == "pi":
                    return "math.pi"
                return f"math.{m}({', '.join(args)})"
            if m == "append":
                return f"{obj}.push({args[0]})"
            if m == "pop":
                return f"{obj}.pop()" if len(args) == 0 else f"{obj}.splice({args[0]}, 1)[0]"
            if m == "isdigit":
                return f"pyIsDigit({obj})"
            if m == "isalpha":
                return f"pyIsAlpha({obj})"
            return f"{obj}.{m}({', '.join(args)})"
        raise TranspileError("unsupported call target")

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
            if (
                isinstance(expr.func, ast.Attribute)
                and expr.func.attr in {"resolve", "parent"}
                and self._is_path_like_expr(expr.func.value)
            ):
                return True
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Div):
            return self._is_path_like_expr(expr.left)
        if isinstance(expr, ast.Attribute):
            if expr.attr == "parent":
                return self._is_path_like_expr(expr.value)
        return False

    def _transpile_fstring(self, expr: ast.JoinedStr) -> str:
        parts: list[str] = []
        for v in expr.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                parts.append(v.value.replace('`', '\\`').replace('${', '\\${'))
            elif isinstance(v, ast.FormattedValue):
                parts.append("${" + self.transpile_expr(v.value) + "}")
            else:
                raise TranspileError("unsupported f-string part")
        return "`" + "".join(parts) + "`"

    def _transpile_list_comp(self, expr: ast.ListComp) -> str:
        if len(expr.generators) != 1:
            raise TranspileError("only single list comprehension is supported")
        gen = expr.generators[0]
        if not isinstance(gen.target, ast.Name):
            raise TranspileError("list comprehension target must be name")
        out = self._new_temp("listcomp")
        var = gen.target.id
        iter_expr = self.transpile_expr(gen.iter)
        lines = [f"(() => {{", f"{self.INDENT}const {out} = [];", f"{self.INDENT}for (const {var} of {iter_expr}) {{"]
        for cond in gen.ifs:
            lines.append(f"{self.INDENT * 2}if (!pyBool({self.transpile_expr(cond)})) continue;")
        lines.append(f"{self.INDENT * 2}{out}.push({self.transpile_expr(expr.elt)});")
        lines.append(f"{self.INDENT}}}")
        lines.append(f"{self.INDENT}return {out};")
        lines.append("})()")
        return "\n".join(lines)

    def _binop(self, op: ast.operator) -> str:
        mapping = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.BitAnd: "&",
            ast.LShift: "<<",
            ast.RShift: ">>",
            ast.Mod: "%",
        }
        for k, v in mapping.items():
            if isinstance(op, k):
                return v
        raise TranspileError(f"unsupported binop: {type(op).__name__}")

    def _cmpop(self, op: ast.cmpop) -> str:
        mapping = {
            ast.Eq: "===",
            ast.NotEq: "!==",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
        }
        for k, v in mapping.items():
            if isinstance(op, k):
                return v
        raise TranspileError(f"unsupported compare op: {type(op).__name__}")

    def _string_literal(self, text: str) -> str:
        esc = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        return f"'{esc}'"
