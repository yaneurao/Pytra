"""Python AST を Go / Java ネイティブコードへ変換する共通トランスパイラ。"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from .base_transpiler import BaseTranspiler, TranspileError


@dataclass
class GoJavaConfig:
    """Go / Java ネイティブ変換設定。"""

    language_name: str
    target: str  # "go" or "java"
    file_header: str
    runtime_template_path: Path


@dataclass
class Scope:
    """文ブロック単位の宣言状態と型ヒント。"""

    declared: set[str]
    class_types: dict[str, str]
    value_types: dict[str, str]


class GoJavaNativeTranspiler(BaseTranspiler):
    """Python サブセットを Go / Java へ変換する共通実装。"""

    def __init__(self, config: GoJavaConfig) -> None:
        super().__init__(temp_prefix="__pytra")
        self.config = config
        self.class_names: set[str] = set()
        self.class_bases: dict[str, str | None] = {}
        self.class_methods: dict[str, set[str]] = {}
        self.class_static_fields: dict[str, set[str]] = {}
        self.class_instance_fields: dict[str, set[str]] = {}
        self.class_is_dataclass: dict[str, bool] = {}
        self.class_dataclass_fields: dict[str, list[tuple[str, str | None]]] = {}
        self.function_arg_types: dict[str, list[str | None]] = {}
        self.current_class: str | None = None
        self.scope_stack: list[Scope] = []
        self.function_renames: dict[str, str] = {}

    @property
    def is_go(self) -> bool:
        return self.config.target == "go"

    def transpile_path(self, input_path: Path, output_path: Path) -> str:
        source = input_path.read_text(encoding="utf-8")
        module = ast.parse(source, filename=str(input_path))
        runtime = self.config.runtime_template_path.read_text(encoding="utf-8").rstrip()
        body = self.transpile_module(module, output_path)
        return f"{self.config.file_header}\n\n{runtime}\n\n{body}\n"

    def transpile_module(self, module: ast.Module, output_path: Path) -> str:
        self._collect_class_info(module)
        self._collect_function_info(module)
        lines: list[str] = []
        defs: list[str] = []

        # Go は package/import を先頭に置く必要があるため、ランタイム側で宣言済み。
        # Java はランタイム側に import と PyRuntime がある前提。

        # クラス関連関数を先に生成する。
        for stmt in module.body:
            if isinstance(stmt, ast.ClassDef):
                defs.extend(self._transpile_class(stmt))
                defs.append("")

        # 関数を生成。
        self.function_renames = {}
        if self.is_go and any(isinstance(stmt, ast.FunctionDef) and stmt.name == "main" for stmt in module.body):
            self.function_renames["main"] = "py_main"
        for stmt in module.body:
            if isinstance(stmt, ast.FunctionDef):
                defs.extend(self._transpile_function(stmt))
                defs.append("")

        # トップレベル文（main guard 外）と main guard 本体を main に集約。
        main_stmts: list[ast.stmt] = []
        for stmt in module.body:
            if isinstance(stmt, (ast.ClassDef, ast.FunctionDef, ast.Import, ast.ImportFrom)):
                continue
            if self._is_main_guard(stmt):
                main_stmts.extend(stmt.body)
            else:
                main_stmts.append(stmt)

        if self.is_go:
            lines.extend(defs)
            lines.extend(self._transpile_main_go(main_stmts))
            return "\n".join(lines).rstrip()

        class_name = self._java_class_name_from_output(output_path)
        lines.append(f"class {class_name} {{")
        if defs:
            lines.extend(self._indent_block([ln for ln in defs if ln != ""]))
            lines.append("")
        lines.extend(self._indent_block(self._transpile_main_java(main_stmts)))
        lines.append("}")
        return "\n".join(lines).rstrip()

    def _collect_class_info(self, module: ast.Module) -> None:
        self.class_names = {stmt.name for stmt in module.body if isinstance(stmt, ast.ClassDef)}
        self.class_bases = {}
        self.class_methods = {}
        self.class_static_fields = {}
        self.class_instance_fields = {}
        self.class_is_dataclass = {}
        self.class_dataclass_fields = {}

        for stmt in module.body:
            if not isinstance(stmt, ast.ClassDef):
                continue
            base: str | None = None
            if stmt.bases:
                if len(stmt.bases) != 1 or not isinstance(stmt.bases[0], ast.Name):
                    raise TranspileError("only single-name inheritance is supported")
                base = stmt.bases[0].id
            self.class_bases[stmt.name] = base
            is_dataclass = any(
                (isinstance(d, ast.Name) and d.id == "dataclass")
                or (isinstance(d, ast.Attribute) and d.attr == "dataclass")
                for d in stmt.decorator_list
            )
            self.class_is_dataclass[stmt.name] = is_dataclass
            methods: set[str] = set()
            static_fields: set[str] = set()
            instance_fields: set[str] = set()
            dataclass_fields: list[tuple[str, str | None]] = []

            for node in stmt.body:
                if isinstance(node, ast.FunctionDef):
                    methods.add(node.name)
                    if node.name == "__init__":
                        for st in node.body:
                            if isinstance(st, ast.Assign):
                                for t in st.targets:
                                    if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                                        instance_fields.add(t.attr)
                            if isinstance(st, ast.AnnAssign):
                                t = st.target
                                if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                                    instance_fields.add(t.attr)
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    if is_dataclass:
                        dataclass_fields.append((node.target.id, self.transpile_expr(node.value) if node.value is not None else None))
                        instance_fields.add(node.target.id)
                    else:
                        static_fields.add(node.target.id)
                elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    static_fields.add(node.targets[0].id)

            self.class_methods[stmt.name] = methods
            self.class_static_fields[stmt.name] = static_fields
            self.class_instance_fields[stmt.name] = instance_fields
            self.class_dataclass_fields[stmt.name] = dataclass_fields

    def _collect_function_info(self, module: ast.Module) -> None:
        self.function_arg_types = {}
        for stmt in module.body:
            if isinstance(stmt, ast.FunctionDef):
                types: list[str | None] = []
                for a in stmt.args.args:
                    types.append(self._annotation_tag(a.annotation))
                self.function_arg_types[stmt.name] = types

    def _resolve_method_owner(self, class_name: str, method: str) -> str | None:
        cur: str | None = class_name
        while cur is not None:
            if method in self.class_methods.get(cur, set()):
                return cur
            cur = self.class_bases.get(cur)
        return None

    def _transpile_class(self, cls: ast.ClassDef) -> list[str]:
        lines: list[str] = []
        class_name = cls.name
        base = self.class_bases.get(class_name)

        # 静的メンバー保持マップ。
        static_init_items: list[tuple[str, str]] = []
        for node in cls.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if self.class_is_dataclass.get(class_name, False):
                    continue
                value = "null" if (not self.is_go and node.value is None) else ("nil" if self.is_go and node.value is None else self.transpile_expr(node.value))
                static_init_items.append((node.target.id, value))
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                static_init_items.append((node.targets[0].id, self.transpile_expr(node.value)))

        static_expr = self._dict_literal_from_items(static_init_items)
        if self.is_go:
            lines.append(f"var __cls_{class_name} = {static_expr}")
        else:
            lines.append(f"static Map<Object, Object> __cls_{class_name} = {static_expr};")

        # コンストラクタ関数。
        init_fn = None
        for node in cls.body:
            if isinstance(node, ast.FunctionDef) and node.name == "__init__":
                init_fn = node
                break

        ctor_args = []
        if init_fn is not None:
            ctor_args = [a.arg for a in init_fn.args.args[1:]]
        elif self.class_is_dataclass.get(class_name, False):
            ctor_args = [name for name, _ in self.class_dataclass_fields.get(class_name, [])]

        lines.extend(self._emit_ctor(class_name, base, ctor_args, init_fn))

        # メソッド関数。
        for node in cls.body:
            if isinstance(node, ast.FunctionDef) and node.name != "__init__":
                lines.extend(self._emit_method(class_name, node))

        return lines

    def _emit_ctor(self, class_name: str, base: str | None, args: list[str], init_fn: ast.FunctionDef | None) -> list[str]:
        lines: list[str] = []
        is_dc = self.class_is_dataclass.get(class_name, False)
        arg_types: dict[str, str] = {}
        if self.is_go and init_fn is not None:
            raw_args = init_fn.args.args[1:] if init_fn.args.args and init_fn.args.args[0].arg == "self" else init_fn.args.args
            for a in raw_args:
                t = self._annotation_tag(a.annotation)
                if t is not None:
                    arg_types[a.arg] = t
        arg_decl = self._args_decl(args, arg_types=arg_types)
        if is_dc:
            arg_decl = "__args ...any" if self.is_go else "Object... __args"
        if self.is_go:
            lines.append(f"func New{class_name}({arg_decl}) map[any]any {{")
            if base is not None:
                base_args = ", ".join("nil" for _ in args)
                lines.append(f"{self.INDENT}self := New{base}({base_args})")
                lines.append(f"{self.INDENT}self[\"__class\"] = \"{class_name}\"")
            else:
                lines.append(f"{self.INDENT}self := map[any]any{{\"__class\": \"{class_name}\"}}")
            scope = Scope(declared=set(args) | {"self"}, class_types={}, value_types=dict(arg_types))
            if init_fn is not None:
                prev = self.current_class
                self.current_class = class_name
                body = self.transpile_statements(init_fn.body, scope)
                self.current_class = prev
                for line in body:
                    lines.append(f"{self.INDENT}{line}")
            elif is_dc:
                for i, (name, default) in enumerate(self.class_dataclass_fields.get(class_name, [])):
                    if default is None:
                        lines.append(f"{self.INDENT}var {name} any = nil")
                    else:
                        lines.append(f"{self.INDENT}var {name} any = {default}")
                    lines.append(f"{self.INDENT}if len(__args) > {i} {{ {name} = __args[{i}] }}")
                    lines.append(f"{self.INDENT}self[{self._string_literal(name)}] = {name}")
            lines.append(f"{self.INDENT}return self")
            lines.append("}")
        else:
            lines.append(f"static Map<Object, Object> New{class_name}({arg_decl}) {{")
            if base is not None:
                base_args = ", ".join("null" for _ in args)
                lines.append(f"{self.INDENT}Map<Object, Object> self = New{base}({base_args});")
                lines.append(f"{self.INDENT}self.put(\"__class\", \"{class_name}\");")
            else:
                lines.append(f"{self.INDENT}Map<Object, Object> self = PyRuntime.pyDict(\"__class\", \"{class_name}\");")
            scope = Scope(declared=set(args) | {"self"}, class_types={}, value_types={})
            if init_fn is not None:
                prev = self.current_class
                self.current_class = class_name
                body = self.transpile_statements(init_fn.body, scope)
                self.current_class = prev
                for line in body:
                    lines.append(f"{self.INDENT}{line}")
            elif is_dc:
                for i, (name, default) in enumerate(self.class_dataclass_fields.get(class_name, [])):
                    if default is None:
                        lines.append(f"{self.INDENT}Object {name} = null;")
                    else:
                        lines.append(f"{self.INDENT}Object {name} = {default};")
                    lines.append(f"{self.INDENT}if (__args.length > {i}) {{ {name} = __args[{i}]; }}")
                    lines.append(f"{self.INDENT}self.put({self._string_literal(name)}, {name});")
            lines.append(f"{self.INDENT}return self;")
            lines.append("}")
        return lines

    def _emit_method(self, class_name: str, fn: ast.FunctionDef) -> list[str]:
        args = [a.arg for a in fn.args.args[1:]] if fn.args.args and fn.args.args[0].arg == "self" else [a.arg for a in fn.args.args]
        lines: list[str] = []
        arg_types: dict[str, str] = {}
        if self.is_go:
            raw_args = fn.args.args[1:] if fn.args.args and fn.args.args[0].arg == "self" else fn.args.args
            for a in raw_args:
                t = self._annotation_tag(a.annotation)
                if t is not None:
                    arg_types[a.arg] = t
        arg_decl = self._args_decl(["self"] + args, self_map_first=True, arg_types=arg_types)
        if self.is_go:
            lines.append(f"func {class_name}_{fn.name}({arg_decl}) any {{")
        else:
            lines.append(f"static Object {class_name}_{fn.name}({arg_decl}) {{")
        scope = Scope(declared=set(["self"] + args), class_types={}, value_types=dict(arg_types))
        prev = self.current_class
        self.current_class = class_name
        body = self.transpile_statements(fn.body, scope)
        self.current_class = prev
        for line in body:
            lines.append(f"{self.INDENT}{line}")
        if not self._stmt_guarantees_return(fn.body):
            if self.is_go:
                lines.append(f"{self.INDENT}return nil")
            else:
                lines.append(f"{self.INDENT}return null;")
        lines.append("}")
        return lines

    def _transpile_function(self, fn: ast.FunctionDef) -> list[str]:
        args = [a.arg for a in fn.args.args]
        arg_types: dict[str, str] = {}
        if self.is_go:
            for a in fn.args.args:
                t = self._annotation_tag(a.annotation)
                if t is not None:
                    arg_types[a.arg] = t
        arg_decl = self._args_decl(args, arg_types=arg_types)
        lines: list[str] = []
        fn_name = self.function_renames.get(fn.name, fn.name)
        if self.is_go:
            lines.append(f"func {fn_name}({arg_decl}) any {{")
        else:
            lines.append(f"static Object {fn_name}({arg_decl}) {{")
        scope = Scope(declared=set(args), class_types={}, value_types=dict(arg_types))
        body = self.transpile_statements(fn.body, scope)
        for line in body:
            lines.append(f"{self.INDENT}{line}")
        if not self._stmt_guarantees_return(fn.body):
            if self.is_go:
                lines.append(f"{self.INDENT}return nil")
            else:
                lines.append(f"{self.INDENT}return null;")
        lines.append("}")
        return lines

    def _transpile_main_go(self, stmts: list[ast.stmt]) -> list[str]:
        scope = Scope(declared=set(), class_types={}, value_types={})
        body = self.transpile_statements(stmts, scope)
        lines: list[str] = []
        lines.append("func main() {")
        for line in body:
            lines.append(f"{self.INDENT}{line}")
        lines.append("}")
        return lines

    def _transpile_main_java(self, stmts: list[ast.stmt]) -> list[str]:
        scope = Scope(declared=set(), class_types={}, value_types={})
        body = self.transpile_statements(stmts, scope)
        lines = ["public static void main(String[] args) {"]
        lines.extend(self._indent_block(body))
        lines.append("}")
        return lines

    def transpile_statements(self, stmts: list[ast.stmt], scope: Scope) -> list[str]:
        self.scope_stack.append(scope)
        out: list[str] = []
        for stmt in stmts:
            if isinstance(stmt, ast.Return):
                value = self.transpile_expr(stmt.value) if stmt.value is not None else ("nil" if self.is_go else "null")
                out.append(self._stmt(f"return {value}"))
                continue
            if isinstance(stmt, ast.Pass):
                continue
            if isinstance(stmt, ast.Break):
                out.append(self._stmt("break"))
                continue
            if isinstance(stmt, ast.Continue):
                out.append(self._stmt("continue"))
                continue
            if isinstance(stmt, ast.Expr):
                # Python の docstring（先頭文字列式）は実行文として出力しない。
                if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                    continue
                out.append(self._stmt(self.transpile_expr(stmt.value)))
                continue
            if isinstance(stmt, ast.FunctionDef):
                continue
            if isinstance(stmt, ast.ClassDef):
                continue
            if isinstance(stmt, ast.AnnAssign):
                if isinstance(stmt.target, ast.Name):
                    ann = self._annotation_tag(stmt.annotation)
                    if ann is not None:
                        scope.value_types[self._safe_name(stmt.target.id)] = ann
                out.extend(self._transpile_assign_like(stmt.target, stmt.value, scope))
                if isinstance(stmt.target, ast.Name) and isinstance(stmt.annotation, ast.Name):
                    if stmt.annotation.id in self.class_names:
                        scope.class_types[stmt.target.id] = stmt.annotation.id
                continue
            if isinstance(stmt, ast.Assign):
                if len(stmt.targets) != 1:
                    raise TranspileError("only single-target assign is supported")
                out.extend(self._transpile_assign_like(stmt.targets[0], stmt.value, scope))
                continue
            if isinstance(stmt, ast.AugAssign):
                out.extend(self._transpile_augassign(stmt, scope))
                continue
            if isinstance(stmt, ast.If):
                out.extend(self._transpile_if(stmt, scope))
                continue
            if isinstance(stmt, ast.While):
                out.extend(self._transpile_while(stmt, scope))
                continue
            if isinstance(stmt, ast.For):
                out.extend(self._transpile_for(stmt, scope))
                continue
            if isinstance(stmt, ast.Raise):
                exc = self.transpile_expr(stmt.exc) if stmt.exc is not None else self._string_literal("RuntimeError")
                if self.is_go:
                    out.append(self._stmt(f"panic({exc})"))
                else:
                    out.append(self._stmt(f"throw new RuntimeException(PyRuntime.pyToString({exc}))"))
                continue
            if isinstance(stmt, ast.Try):
                out.extend(self._transpile_try(stmt, scope))
                continue
            raise TranspileError(f"unsupported statement: {type(stmt).__name__}")
        self.scope_stack.pop()
        return out

    def _transpile_assign_like(self, target: ast.expr, value: ast.expr | None, scope: Scope) -> list[str]:
        rhs = ("nil" if self.is_go else "null") if value is None else self.transpile_expr(value)
        rhs_go_type = self._expr_go_type(value) if (self.is_go and value is not None) else None
        out: list[str] = []

        if isinstance(target, ast.Tuple):
            tmp = self._new_temp("tuple")
            out.extend(self._declare_or_assign(tmp, rhs, scope, rhs_go_type=rhs_go_type))
            for i, elt in enumerate(target.elts):
                if not isinstance(elt, ast.Name):
                    raise TranspileError("tuple assignment target must be names")
                out.extend(self._declare_or_assign(elt.id, f"PyRuntime.pyGet({tmp}, {i})" if not self.is_go else f"pyGet({tmp}, {i})", scope))
            return out

        if isinstance(target, ast.Name):
            out.extend(self._declare_or_assign(target.id, rhs, scope, rhs_go_type=rhs_go_type))
            if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id in self.class_names:
                scope.class_types[target.id] = value.func.id
            return out

        if isinstance(target, ast.Attribute):
            out.append(self._stmt(f"{self._set_attr(target, rhs)}"))
            return out

        if isinstance(target, ast.Subscript):
            if isinstance(target.slice, ast.Slice):
                raise TranspileError("slice assignment is not supported")
            base = self.transpile_expr(target.value)
            key = self.transpile_expr(target.slice)
            call = f"pySet({base}, {key}, {rhs})" if self.is_go else f"PyRuntime.pySet({base}, {key}, {rhs})"
            out.append(self._stmt(call))
            return out

        raise TranspileError("unsupported assignment target")

    def _transpile_augassign(self, stmt: ast.AugAssign, scope: Scope) -> list[str]:
        op = self._binop_helper(stmt.op)
        rhs = self.transpile_expr(stmt.value)
        out: list[str] = []
        if isinstance(stmt.target, ast.Name):
            name = stmt.target.id
            if self.is_go:
                safe = self._safe_name(name)
                lhs_t = scope.value_types.get(safe)
                rhs_t = self._expr_go_type(stmt.value)
                if lhs_t == "int":
                    if isinstance(stmt.op, ast.Add):
                        out.extend(self._declare_or_assign(name, f"({safe} + {self._as_go_int(stmt.value, rhs_t)})", scope, force_assign=True, rhs_go_type="int"))
                        return out
                    if isinstance(stmt.op, ast.Sub):
                        out.extend(self._declare_or_assign(name, f"({safe} - {self._as_go_int(stmt.value, rhs_t)})", scope, force_assign=True, rhs_go_type="int"))
                        return out
                    if isinstance(stmt.op, ast.Mult):
                        out.extend(self._declare_or_assign(name, f"({safe} * {self._as_go_int(stmt.value, rhs_t)})", scope, force_assign=True, rhs_go_type="int"))
                        return out
                    if isinstance(stmt.op, ast.FloorDiv):
                        out.extend(self._declare_or_assign(name, f"({safe} / {self._as_go_int(stmt.value, rhs_t)})", scope, force_assign=True, rhs_go_type="int"))
                        return out
                if lhs_t == "float64":
                    if isinstance(stmt.op, ast.Add):
                        out.extend(self._declare_or_assign(name, f"({safe} + {self._as_go_float(stmt.value, rhs_t)})", scope, force_assign=True, rhs_go_type="float64"))
                        return out
                    if isinstance(stmt.op, ast.Sub):
                        out.extend(self._declare_or_assign(name, f"({safe} - {self._as_go_float(stmt.value, rhs_t)})", scope, force_assign=True, rhs_go_type="float64"))
                        return out
                    if isinstance(stmt.op, ast.Mult):
                        out.extend(self._declare_or_assign(name, f"({safe} * {self._as_go_float(stmt.value, rhs_t)})", scope, force_assign=True, rhs_go_type="float64"))
                        return out
                    if isinstance(stmt.op, ast.Div):
                        out.extend(self._declare_or_assign(name, f"({safe} / {self._as_go_float(stmt.value, rhs_t)})", scope, force_assign=True, rhs_go_type="float64"))
                        return out
            out.extend(self._declare_or_assign(name, f"{op}({name}, {rhs})", scope, force_assign=True))
            return out
        if isinstance(stmt.target, ast.Attribute):
            cur = self.transpile_expr(stmt.target)
            out.append(self._stmt(self._set_attr(stmt.target, f"{op}({cur}, {rhs})")))
            return out
        if isinstance(stmt.target, ast.Subscript):
            if isinstance(stmt.target.slice, ast.Slice):
                raise TranspileError("slice augassign unsupported")
            base = self.transpile_expr(stmt.target.value)
            key = self.transpile_expr(stmt.target.slice)
            get = f"pyGet({base}, {key})" if self.is_go else f"PyRuntime.pyGet({base}, {key})"
            set_call = f"pySet({base}, {key}, {op}({get}, {rhs}))" if self.is_go else f"PyRuntime.pySet({base}, {key}, {op}({get}, {rhs}))"
            out.append(self._stmt(set_call))
            return out
        raise TranspileError("unsupported augassign target")

    def _transpile_if(self, stmt: ast.If, scope: Scope) -> list[str]:
        cond = self._py_bool(self.transpile_expr(stmt.test))
        lines = [f"if ({cond}) {{"]
        lines.extend(self._indent_block(self.transpile_statements(stmt.body, Scope(set(scope.declared), dict(scope.class_types), dict(scope.value_types)))))
        if stmt.orelse:
            lines.append("} else {")
            lines.extend(self._indent_block(self.transpile_statements(stmt.orelse, Scope(set(scope.declared), dict(scope.class_types), dict(scope.value_types)))))
        lines.append("}")
        return lines

    def _transpile_while(self, stmt: ast.While, scope: Scope) -> list[str]:
        cond = self._py_bool(self.transpile_expr(stmt.test))
        lines = [f"for {cond} {{" if self.is_go else f"while ({cond}) {{"]
        lines.extend(self._indent_block(self.transpile_statements(stmt.body, Scope(set(scope.declared), dict(scope.class_types), dict(scope.value_types)))))
        lines.append("}")
        return lines

    def _transpile_for(self, stmt: ast.For, scope: Scope) -> list[str]:
        if not isinstance(stmt.target, ast.Name):
            raise TranspileError("for target must be name")
        target = stmt.target.id
        target_safe = self._safe_name(target)

        rng = self._parse_range_args(stmt.iter)
        if rng is not None:
            start, stop, step = rng
            s0 = self._new_temp("range_start")
            s1 = self._new_temp("range_stop")
            s2 = self._new_temp("range_step")
            i0 = self._new_temp("i")
            lines: list[str] = []
            if self.is_go:
                lines.append(self._stmt(f"{s0} := pyToInt({start})"))
                lines.append(self._stmt(f"{s1} := pyToInt({stop})"))
                lines.append(self._stmt(f"{s2} := pyToInt({step})"))
                lines.append(f"if {s2} == 0 {{ panic(\"range() step must not be zero\") }}")
                if target_safe not in scope.declared:
                    lines.extend(self._declare_or_assign(target, "0", scope, rhs_go_type="int"))
                lines.append(f"for {i0} := {s0}; ({s2} > 0 && {i0} < {s1}) || ({s2} < 0 && {i0} > {s1}); {i0} += {s2} {{")
                lines.extend(self._indent_block([self._stmt(f"{target_safe} = {i0}")]))
            else:
                lines.append(self._stmt(f"int {s0} = PyRuntime.pyToInt({start})"))
                lines.append(self._stmt(f"int {s1} = PyRuntime.pyToInt({stop})"))
                lines.append(self._stmt(f"int {s2} = PyRuntime.pyToInt({step})"))
                lines.append(f"if ({s2} == 0) {{ throw new RuntimeException(\"range() step must not be zero\"); }}")
                if target_safe not in scope.declared:
                    lines.extend(self._declare_or_assign(target, "null", scope))
                lines.append(f"for (int {i0} = {s0}; ({s2} > 0 && {i0} < {s1}) || ({s2} < 0 && {i0} > {s1}); {i0} += {s2}) {{")
                lines.extend(self._indent_block([self._stmt(f"{target_safe} = {i0}")]))
            lines.extend(self._indent_block(self.transpile_statements(stmt.body, Scope(set(scope.declared), dict(scope.class_types), dict(scope.value_types)))))
            lines.append("}")
            return lines

        src = self.transpile_expr(stmt.iter)
        iter_expr = f"pyIter({src})" if self.is_go else f"PyRuntime.pyIter({src})"
        it = self._new_temp("it")
        lines: list[str] = []
        if self.is_go:
            if target_safe not in scope.declared:
                lines.extend(self._declare_or_assign(target, "nil", scope))
            lines.append(f"for _, {it} := range {iter_expr} {{")
            lines.extend(self._indent_block([self._stmt(f"{target_safe} = {it}")]))
        else:
            if target_safe not in scope.declared:
                lines.extend(self._declare_or_assign(target, "null", scope))
            lines.append(f"for (Object {it} : {iter_expr}) {{")
            lines.extend(self._indent_block([self._stmt(f"{target_safe} = {it}")]))
        lines.extend(self._indent_block(self.transpile_statements(stmt.body, Scope(set(scope.declared), dict(scope.class_types), dict(scope.value_types)))))
        lines.append("}")
        return lines

    def _transpile_try(self, stmt: ast.Try, scope: Scope) -> list[str]:
        if len(stmt.handlers) > 1:
            raise TranspileError("only single except is supported")
        if self.is_go:
            has_ret = self._stmt_guarantees_return(stmt.body) or any(self._stmt_guarantees_return(h.body) for h in stmt.handlers)
            tmp = self._new_temp("tryret")
            lines = [f"var {tmp} any = pyTryCatch(func() any {{"]
            lines.extend([f"{self.INDENT}{l}" for l in self.transpile_statements(stmt.body, Scope(set(scope.declared), dict(scope.class_types), dict(scope.value_types)))])
            lines.append(f"{self.INDENT}return nil")
            lines.append("}, func(ex any) any {")
            if stmt.handlers:
                h = stmt.handlers[0]
                ex_name = h.name or "ex"
                if ex_name != "ex":
                    lines.extend([f"{self.INDENT}{l}" for l in self._declare_or_assign(ex_name, "ex", Scope(set(scope.declared), dict(scope.class_types), dict(scope.value_types)))])
                lines.extend([f"{self.INDENT}{l}" for l in self.transpile_statements(h.body, Scope(set(scope.declared) | {ex_name}, dict(scope.class_types), dict(scope.value_types)))])
            lines.append(f"{self.INDENT}return nil")
            lines.append("}, func() {")
            lines.extend([f"{self.INDENT}{l}" for l in self.transpile_statements(stmt.finalbody, Scope(set(scope.declared), dict(scope.class_types), dict(scope.value_types)))])
            lines.append("})")
            if has_ret:
                lines.append(self._stmt(f"return {tmp}"))
            return lines

        lines = ["try {"]
        lines.extend(self._indent_block(self.transpile_statements(stmt.body, Scope(set(scope.declared), dict(scope.class_types), dict(scope.value_types)))))
        lines.append("}")
        if stmt.handlers:
            h = stmt.handlers[0]
            ex_name = h.name or "ex"
            lines.append(f"catch (RuntimeException {ex_name}) {{")
            lines.extend(self._indent_block(self.transpile_statements(h.body, Scope(set(scope.declared)|{ex_name}, dict(scope.class_types), dict(scope.value_types)))))
            lines.append("}")
        if stmt.finalbody:
            lines.append("finally {")
            lines.extend(self._indent_block(self.transpile_statements(stmt.finalbody, Scope(set(scope.declared), dict(scope.class_types), dict(scope.value_types)))))
            lines.append("}")
        return lines

    def transpile_expr(self, expr: ast.expr) -> str:
        if isinstance(expr, ast.Name):
            if expr.id == "True":
                return "true"
            if expr.id == "False":
                return "false"
            if expr.id == "None":
                return "nil" if self.is_go else "null"
            if expr.id == "self":
                return "self"
            return self._safe_name(expr.id)

        if isinstance(expr, ast.Constant):
            if isinstance(expr.value, str):
                return self._string_literal(expr.value)
            if expr.value is None:
                return "nil" if self.is_go else "null"
            if isinstance(expr.value, bool):
                return "true" if expr.value else "false"
            if expr.value is Ellipsis:
                return '"..."'
            if isinstance(expr.value, int) and (not self.is_go):
                if expr.value > 2147483647 or expr.value < -2147483648:
                    return f"{expr.value}L"
            return repr(expr.value)

        if isinstance(expr, ast.Attribute):
            if isinstance(expr.value, ast.Name) and expr.value.id == "math" and expr.attr == "pi":
                return "pyMathPi()" if self.is_go else "PyRuntime.pyMathPi()"
            if isinstance(expr.value, ast.Name) and expr.value.id == "self" and self.current_class is not None:
                if expr.attr in self.class_static_fields.get(self.current_class, set()) and expr.attr not in self.class_instance_fields.get(self.current_class, set()):
                    holder = f"__cls_{self.current_class}"
                    return f"pyGet({holder}, {self._string_literal(expr.attr)})" if self.is_go else f"PyRuntime.pyGet({holder}, {self._string_literal(expr.attr)})"
                return f"pyGet(self, {self._string_literal(expr.attr)})" if self.is_go else f"PyRuntime.pyGet(self, {self._string_literal(expr.attr)})"
            base = self.transpile_expr(expr.value)
            return f"pyGet({base}, {self._string_literal(expr.attr)})" if self.is_go else f"PyRuntime.pyGet({base}, {self._string_literal(expr.attr)})"

        if isinstance(expr, ast.BinOp):
            if self.is_go:
                t = self._expr_go_type(expr)
                if t in {"int", "float64"}:
                    lt = self._expr_go_type(expr.left)
                    rt = self._expr_go_type(expr.right)
                    if t == "float64":
                        l = self._as_go_float(expr.left, lt)
                        r = self._as_go_float(expr.right, rt)
                    else:
                        l = self._as_go_int(expr.left, lt)
                        r = self._as_go_int(expr.right, rt)
                    if isinstance(expr.op, ast.Add):
                        return f"({l} + {r})"
                    if isinstance(expr.op, ast.Sub):
                        return f"({l} - {r})"
                    if isinstance(expr.op, ast.Mult):
                        return f"({l} * {r})"
                    if isinstance(expr.op, ast.Div):
                        return f"({l} / {r})"
                    if isinstance(expr.op, ast.Mod):
                        return f"({l} % {r})"
                    if isinstance(expr.op, ast.FloorDiv):
                        if t == "int":
                            return f"({l} / {r})"
                        return f"math.Floor({l} / {r})"
                    if isinstance(expr.op, ast.LShift):
                        return f"({l} << uint({r}))"
                    if isinstance(expr.op, ast.RShift):
                        return f"({l} >> uint({r}))"
                    if isinstance(expr.op, ast.BitAnd):
                        return f"({l} & {r})"
                    if isinstance(expr.op, ast.BitOr):
                        return f"({l} | {r})"
                    if isinstance(expr.op, ast.BitXor):
                        return f"({l} ^ {r})"
            l = self.transpile_expr(expr.left)
            r = self.transpile_expr(expr.right)
            return f"{self._binop_helper(expr.op)}({l}, {r})"

        if isinstance(expr, ast.UnaryOp):
            if isinstance(expr.op, ast.Not):
                return f"(!{self._py_bool(self.transpile_expr(expr.operand))})"
            if isinstance(expr.op, ast.USub):
                if self.is_go:
                    ot = self._expr_go_type(expr.operand)
                    if ot == "int":
                        return f"(-{self._as_go_int(expr.operand, ot)})"
                    if ot == "float64":
                        return f"(-{self._as_go_float(expr.operand, ot)})"
                f = "pyNeg" if self.is_go else "PyRuntime.pyNeg"
                return f"{f}({self.transpile_expr(expr.operand)})"
            raise TranspileError("unsupported unary op")

        if isinstance(expr, ast.BoolOp):
            op = "&&" if isinstance(expr.op, ast.And) else "||"
            items = [self._py_bool(self.transpile_expr(v)) for v in expr.values]
            return "(" + f" {op} ".join(items) + ")"

        if isinstance(expr, ast.Compare):
            if len(expr.ops) != 1 or len(expr.comparators) != 1:
                raise TranspileError("chained compare unsupported")
            if self.is_go:
                lt = self._expr_go_type(expr.left)
                rt = self._expr_go_type(expr.comparators[0])
                if lt in {"int", "float64"} and rt in {"int", "float64"}:
                    l = self._as_go_float(expr.left, lt) if ("float64" in {lt, rt}) else self._as_go_int(expr.left, lt)
                    r = self._as_go_float(expr.comparators[0], rt) if ("float64" in {lt, rt}) else self._as_go_int(expr.comparators[0], rt)
                    op = expr.ops[0]
                    if isinstance(op, ast.Eq):
                        return f"({l} == {r})"
                    if isinstance(op, ast.NotEq):
                        return f"({l} != {r})"
                    if isinstance(op, ast.Lt):
                        return f"({l} < {r})"
                    if isinstance(op, ast.LtE):
                        return f"({l} <= {r})"
                    if isinstance(op, ast.Gt):
                        return f"({l} > {r})"
                    if isinstance(op, ast.GtE):
                        return f"({l} >= {r})"
            l = self.transpile_expr(expr.left)
            r = self.transpile_expr(expr.comparators[0])
            op = expr.ops[0]
            if isinstance(op, ast.In):
                return f"{'pyIn' if self.is_go else 'PyRuntime.pyIn'}({l}, {r})"
            if isinstance(op, ast.NotIn):
                return f"(!{'pyIn' if self.is_go else 'PyRuntime.pyIn'}({l}, {r}))"
            return f"{self._cmpop_helper(op)}({l}, {r})"

        if isinstance(expr, ast.Call):
            return self._transpile_call(expr)

        if isinstance(expr, ast.IfExp):
            f = "pyTernary" if self.is_go else "PyRuntime.pyTernary"
            return f"{f}({self._py_bool(self.transpile_expr(expr.test))}, {self.transpile_expr(expr.body)}, {self.transpile_expr(expr.orelse)})"

        if isinstance(expr, ast.List):
            if self.is_go:
                return "[]any{" + ", ".join(self.transpile_expr(e) for e in expr.elts) + "}"
            return "PyRuntime.pyList(" + ", ".join(self.transpile_expr(e) for e in expr.elts) + ")"

        if isinstance(expr, ast.Tuple):
            if self.is_go:
                return "[]any{" + ", ".join(self.transpile_expr(e) for e in expr.elts) + "}"
            return "PyRuntime.pyList(" + ", ".join(self.transpile_expr(e) for e in expr.elts) + ")"

        if isinstance(expr, ast.Dict):
            if self.is_go:
                pairs = [f"{self.transpile_expr(k)}: {self.transpile_expr(v)}" for k, v in zip(expr.keys, expr.values)]
                return "map[any]any{" + ", ".join(pairs) + "}"
            items: list[str] = []
            for k, v in zip(expr.keys, expr.values):
                items.append(self.transpile_expr(k))
                items.append(self.transpile_expr(v))
            return "PyRuntime.pyDict(" + ", ".join(items) + ")"

        if isinstance(expr, ast.Subscript):
            if isinstance(expr.slice, ast.Slice):
                start = ("nil" if self.is_go else "null") if expr.slice.lower is None else self.transpile_expr(expr.slice.lower)
                end = ("nil" if self.is_go else "null") if expr.slice.upper is None else self.transpile_expr(expr.slice.upper)
                f = "pySlice" if self.is_go else "PyRuntime.pySlice"
                return f"{f}({self.transpile_expr(expr.value)}, {start}, {end})"
            f = "pyGet" if self.is_go else "PyRuntime.pyGet"
            return f"{f}({self.transpile_expr(expr.value)}, {self.transpile_expr(expr.slice)})"

        if isinstance(expr, ast.JoinedStr):
            parts: list[str] = []
            for v in expr.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    parts.append(self._string_literal(v.value))
                elif isinstance(v, ast.FormattedValue):
                    parts.append(f"{'pyToString' if self.is_go else 'PyRuntime.pyToString'}({self.transpile_expr(v.value)})")
                else:
                    raise TranspileError("unsupported fstring part")
            if not parts:
                return self._string_literal("")
            out = parts[0]
            for p in parts[1:]:
                out = f"pyAdd({out}, {p})" if self.is_go else f"PyRuntime.pyAdd({out}, {p})"
            return out

        if isinstance(expr, ast.ListComp):
            # 単純な [x for x in iter] だけ対応。
            if len(expr.generators) != 1:
                raise TranspileError("only single-generator list comprehension is supported")
            g = expr.generators[0]
            if g.ifs:
                raise TranspileError("list comprehension if is not supported")
            if not isinstance(g.target, ast.Name):
                raise TranspileError("list comprehension target must be name")
            if not isinstance(expr.elt, ast.Name) or expr.elt.id != g.target.id:
                raise TranspileError("only identity list comprehension is supported")
            f = "pyListFromIter" if self.is_go else "PyRuntime.pyListFromIter"
            return f"{f}({self.transpile_expr(g.iter)})"

        raise TranspileError(f"unsupported expression: {type(expr).__name__}")

    def _transpile_call(self, expr: ast.Call) -> str:
        if any(kw.arg is None for kw in expr.keywords):
            raise TranspileError("**kwargs is not supported")
        arg_nodes = list(expr.args) + [kw.value for kw in expr.keywords]
        args = [self.transpile_expr(a) for a in arg_nodes]

        if isinstance(expr.func, ast.Name):
            fn = expr.func.id
            if fn in self.class_names:
                return f"New{fn}({', '.join(args)})"
            builtin = {
                "print": "pyPrint" if self.is_go else "PyRuntime.pyPrint",
                "len": "pyLen" if self.is_go else "PyRuntime.pyLen",
                "int": "pyToInt" if self.is_go else "PyRuntime.pyToInt",
                "float": "pyToFloat" if self.is_go else "PyRuntime.pyToFloat",
                "str": "pyToString" if self.is_go else "PyRuntime.pyToString",
                "min": "pyMin" if self.is_go else "PyRuntime.pyMin",
                "max": "pyMax" if self.is_go else "PyRuntime.pyMax",
                "ord": "pyOrd" if self.is_go else "PyRuntime.pyOrd",
                "chr": "pyChr" if self.is_go else "PyRuntime.pyChr",
                "bytearray": "pyBytearray" if self.is_go else "PyRuntime.pyBytearray",
                "bytes": "pyBytes" if self.is_go else "PyRuntime.pyBytes",
                "perf_counter": "pyPerfCounter" if self.is_go else "PyRuntime.pyPerfCounter",
                "save_gif": "pySaveGIF" if self.is_go else "PyRuntime.pySaveGif",
                "grayscale_palette": "pyGrayscalePalette" if self.is_go else "PyRuntime.pyGrayscalePalette",
                "write_rgb_png": "pyWriteRGBPNG" if self.is_go else "PyRuntime.pyWriteRGBPNG",
            }
            if fn == "range":
                if len(args) == 1:
                    return f"{'pyRange' if self.is_go else 'PyRuntime.pyRange'}(0, {'pyToInt' if self.is_go else 'PyRuntime.pyToInt'}({args[0]}), 1)"
                if len(args) == 2:
                    return f"{'pyRange' if self.is_go else 'PyRuntime.pyRange'}({'pyToInt' if self.is_go else 'PyRuntime.pyToInt'}({args[0]}), {'pyToInt' if self.is_go else 'PyRuntime.pyToInt'}({args[1]}), 1)"
                if len(args) == 3:
                    return f"{'pyRange' if self.is_go else 'PyRuntime.pyRange'}({'pyToInt' if self.is_go else 'PyRuntime.pyToInt'}({args[0]}), {'pyToInt' if self.is_go else 'PyRuntime.pyToInt'}({args[1]}), {'pyToInt' if self.is_go else 'PyRuntime.pyToInt'}({args[2]}))"
                raise TranspileError("range() arg count")
            if fn in builtin:
                if fn == "bytearray" and not args:
                    return f"{builtin[fn]}({'nil' if self.is_go else 'null'})"
                return f"{builtin[fn]}({', '.join(args)})"
            if fn == "RuntimeError" or fn == "Exception":
                arg = args[0] if args else self._string_literal("RuntimeError")
                return arg
            fn_name = self.function_renames.get(fn, fn)
            if self.is_go:
                arg_types = self.function_arg_types.get(fn)
                if arg_types:
                    coerced: list[str] = []
                    for i, a in enumerate(args):
                        dst_t = arg_types[i] if i < len(arg_types) else None
                        src_t = self._expr_go_type(arg_nodes[i]) if i < len(arg_nodes) else None
                        coerced.append(self._coerce_go_arg(a, src_t, dst_t))
                    args = coerced
            return f"{fn_name}({', '.join(args)})"

        if isinstance(expr.func, ast.Attribute):
            # self.method(...) はクラスメソッド関数へ展開。
            if isinstance(expr.func.value, ast.Name) and expr.func.value.id == "self" and self.current_class is not None:
                owner = self._resolve_method_owner(self.current_class, expr.func.attr)
                if owner is not None:
                    return f"{owner}_{expr.func.attr}(self{', ' if args else ''}{', '.join(args)})"

            # obj.method(...) は型ヒントがあればクラスメソッド関数へ展開。
            if isinstance(expr.func.value, ast.Name):
                obj_name = expr.func.value.id
                obj_ref = self._safe_name(obj_name)
                for sc in reversed(self.scope_stack):
                    cls_name = sc.class_types.get(obj_name)
                    if cls_name is not None:
                        owner = self._resolve_method_owner(cls_name, expr.func.attr)
                        if owner is not None:
                            if self.is_go:
                                return f"{owner}_{expr.func.attr}({obj_ref}.(map[any]any){', ' if args else ''}{', '.join(args)})"
                            return f"{owner}_{expr.func.attr}((Map<Object, Object>){obj_ref}{', ' if args else ''}{', '.join(args)})"
                        break

            obj = self.transpile_expr(expr.func.value)
            method = expr.func.attr
            if isinstance(expr.func.value, ast.Name):
                mod = expr.func.value.id
                if mod == "math":
                    if method == "sqrt":
                        return f"math.Sqrt(pyToFloat({args[0]}))" if self.is_go else f"PyRuntime.pyMathSqrt({', '.join(args)})"
                    if method == "sin":
                        return f"math.Sin(pyToFloat({args[0]}))" if self.is_go else f"PyRuntime.pyMathSin({', '.join(args)})"
                    if method == "cos":
                        return f"math.Cos(pyToFloat({args[0]}))" if self.is_go else f"PyRuntime.pyMathCos({', '.join(args)})"
                    if method == "tan":
                        return f"math.Tan(pyToFloat({args[0]}))" if self.is_go else f"PyRuntime.pyMathTan({', '.join(args)})"
                    if method == "exp":
                        return f"math.Exp(pyToFloat({args[0]}))" if self.is_go else f"PyRuntime.pyMathExp({', '.join(args)})"
                    if method == "log":
                        return f"math.Log(pyToFloat({args[0]}))" if self.is_go else f"PyRuntime.pyMathLog({', '.join(args)})"
                    if method == "log10":
                        return f"math.Log10(pyToFloat({args[0]}))" if self.is_go else f"PyRuntime.pyMathLog10({', '.join(args)})"
                    if method == "fabs":
                        return f"math.Abs(pyToFloat({args[0]}))" if self.is_go else f"PyRuntime.pyMathFabs({', '.join(args)})"
                    if method == "floor":
                        return f"math.Floor(pyToFloat({args[0]}))" if self.is_go else f"PyRuntime.pyMathFloor({', '.join(args)})"
                    if method == "ceil":
                        return f"math.Ceil(pyToFloat({args[0]}))" if self.is_go else f"PyRuntime.pyMathCeil({', '.join(args)})"
                    if method == "pow":
                        return f"math.Pow(pyToFloat({args[0]}), pyToFloat({args[1]}))" if self.is_go else f"PyRuntime.pyMathPow({', '.join(args)})"
                if mod == "png_helper" and method == "write_rgb_png":
                    return f"{'pyWriteRGBPNG' if self.is_go else 'PyRuntime.pyWriteRGBPNG'}({', '.join(args)})"
                if mod == "gif_helper":
                    if method == "save_gif":
                        return f"{'pySaveGIF' if self.is_go else 'PyRuntime.pySaveGif'}({', '.join(args)})"
                    if method == "grayscale_palette":
                        return f"{'pyGrayscalePalette' if self.is_go else 'PyRuntime.pyGrayscalePalette'}()"
            if method == "append":
                if self.is_go:
                    if isinstance(expr.func.value, ast.Attribute):
                        owner = self.transpile_expr(expr.func.value.value)
                        key = self._string_literal(expr.func.value.attr)
                        cur = f"pyGet({owner}, {key})"
                        return f"pySet({owner}, {key}, pyAppend({cur}, {args[0]}))"
                    if isinstance(expr.func.value, ast.Subscript) and not isinstance(expr.func.value.slice, ast.Slice):
                        owner = self.transpile_expr(expr.func.value.value)
                        key = self.transpile_expr(expr.func.value.slice)
                        cur = f"pyGet({owner}, {key})"
                        return f"pySet({owner}, {key}, pyAppend({cur}, {args[0]}))"
                    return f"{obj} = pyAppend({obj}, {args[0]})"
                return f"((java.util.List<Object>){obj}).add({args[0]})"
            if method == "pop":
                idx = args[0] if args else ("nil" if self.is_go else "null")
                if self.is_go:
                    if isinstance(expr.func.value, ast.Attribute):
                        owner = self.transpile_expr(expr.func.value.value)
                        key = self._string_literal(expr.func.value.attr)
                        return f"pyPopAt({owner}, {key}, {idx})"
                    if isinstance(expr.func.value, ast.Subscript) and not isinstance(expr.func.value.slice, ast.Slice):
                        owner = self.transpile_expr(expr.func.value.value)
                        key = self.transpile_expr(expr.func.value.slice)
                        return f"pyPopAt({owner}, {key}, {idx})"
                    return f"pyPop(&{obj}, {idx})"
                return f"PyRuntime.pyPop({obj}, {idx})"
            if method == "isdigit":
                return f"{'pyIsDigit' if self.is_go else 'PyRuntime.pyIsDigit'}({obj})"
            if method == "isalpha":
                return f"{'pyIsAlpha' if self.is_go else 'PyRuntime.pyIsAlpha'}({obj})"

            # クラス型メソッド呼び出し推論（名前変数のみ）。
            if isinstance(expr.func.value, ast.Name):
                obj_name = expr.func.value.id
                # 型は式文字列からは分からないので、呼び出し時点では一般呼び出しへフォールバック。
                if self.current_class is not None and obj_name == "self":
                    owner = self._resolve_method_owner(self.current_class, method)
                    if owner is not None:
                        return f"{owner}_{method}(self{', ' if args else ''}{', '.join(args)})"

            raise TranspileError(f"cannot resolve method call: {method}")

        raise TranspileError("unsupported call target")

    def _set_attr(self, target: ast.Attribute, rhs: str) -> str:
        if isinstance(target.value, ast.Name) and target.value.id == "self" and self.current_class is not None:
            if target.attr in self.class_static_fields.get(self.current_class, set()) and target.attr not in self.class_instance_fields.get(self.current_class, set()):
                holder = f"__cls_{self.current_class}"
                return f"pySet({holder}, {self._string_literal(target.attr)}, {rhs})" if self.is_go else f"PyRuntime.pySet({holder}, {self._string_literal(target.attr)}, {rhs})"
            return f"pySet(self, {self._string_literal(target.attr)}, {rhs})" if self.is_go else f"PyRuntime.pySet(self, {self._string_literal(target.attr)}, {rhs})"
        base = self.transpile_expr(target.value)
        return f"pySet({base}, {self._string_literal(target.attr)}, {rhs})" if self.is_go else f"PyRuntime.pySet({base}, {self._string_literal(target.attr)}, {rhs})"

    def _declare_or_assign(self, name: str, rhs: str, scope: Scope, force_assign: bool = False, rhs_go_type: str | None = None) -> list[str]:
        safe = self._safe_name(name)
        go_t = scope.value_types.get(safe) if self.is_go else None
        if self.is_go and go_t is None and rhs_go_type in {"int", "float64", "bool", "string"} and (not force_assign) and safe not in scope.declared:
            go_t = rhs_go_type
            scope.value_types[safe] = go_t
        rhs_go = rhs
        if self.is_go and go_t is not None:
            rhs_go = self._coerce_go_value(rhs, go_t, rhs_go_type)
        if force_assign or safe in scope.declared:
            return [self._stmt(f"{safe} = {rhs_go}")]
        scope.declared.add(safe)
        if self.is_go:
            if go_t is not None:
                return [self._stmt(f"var {safe} {go_t} = {rhs_go}"), self._stmt(f"_ = {safe}")]
            return [self._stmt(f"var {safe} any = {rhs}"), self._stmt(f"_ = {safe}")]
        return [self._stmt(f"Object {safe} = {rhs}")]

    def _args_decl(self, args: list[str], self_map_first: bool = False, arg_types: dict[str, str] | None = None) -> str:
        decls: list[str] = []
        arg_types = arg_types or {}
        for i, a in enumerate(args):
            an = self._safe_name(a)
            if self_map_first and i == 0:
                if self.is_go:
                    decls.append(f"{an} map[any]any")
                else:
                    decls.append(f"Map<Object, Object> {an}")
            else:
                if self.is_go:
                    decls.append(f"{an} {arg_types.get(a, 'any')}")
                else:
                    decls.append(f"Object {an}")
        return ", ".join(decls)

    def _dict_literal_from_items(self, items: list[tuple[str, str]]) -> str:
        if self.is_go:
            return "map[any]any{" + ", ".join(f"{self._string_literal(k)}: {v}" for k, v in items) + "}"
        if not items:
            return "PyRuntime.pyDict()"
        flattened: list[str] = []
        for k, v in items:
            flattened.extend([self._string_literal(k), v])
        return "PyRuntime.pyDict(" + ", ".join(flattened) + ")"

    def _py_bool(self, expr: str) -> str:
        return f"pyBool({expr})" if self.is_go else f"PyRuntime.pyBool({expr})"

    def _binop_helper(self, op: ast.operator) -> str:
        if isinstance(op, ast.Add):
            return "pyAdd" if self.is_go else "PyRuntime.pyAdd"
        if isinstance(op, ast.Sub):
            return "pySub" if self.is_go else "PyRuntime.pySub"
        if isinstance(op, ast.Mult):
            return "pyMul" if self.is_go else "PyRuntime.pyMul"
        if isinstance(op, ast.Div):
            return "pyDiv" if self.is_go else "PyRuntime.pyDiv"
        if isinstance(op, ast.FloorDiv):
            return "pyFloorDiv" if self.is_go else "PyRuntime.pyFloorDiv"
        if isinstance(op, ast.Mod):
            return "pyMod" if self.is_go else "PyRuntime.pyMod"
        if isinstance(op, ast.LShift):
            return "pyLShift" if self.is_go else "PyRuntime.pyLShift"
        if isinstance(op, ast.RShift):
            return "pyRShift" if self.is_go else "PyRuntime.pyRShift"
        if isinstance(op, ast.BitAnd):
            return "pyBitAnd" if self.is_go else "PyRuntime.pyBitAnd"
        if isinstance(op, ast.BitOr):
            return "pyBitOr" if self.is_go else "PyRuntime.pyBitOr"
        if isinstance(op, ast.BitXor):
            return "pyBitXor" if self.is_go else "PyRuntime.pyBitXor"
        raise TranspileError(f"unsupported binop: {type(op).__name__}")

    def _cmpop_helper(self, op: ast.cmpop) -> str:
        if isinstance(op, ast.Eq):
            return "pyEq" if self.is_go else "PyRuntime.pyEq"
        if isinstance(op, ast.NotEq):
            return "pyNe" if self.is_go else "PyRuntime.pyNe"
        if isinstance(op, ast.Lt):
            return "pyLt" if self.is_go else "PyRuntime.pyLt"
        if isinstance(op, ast.LtE):
            return "pyLe" if self.is_go else "PyRuntime.pyLe"
        if isinstance(op, ast.Gt):
            return "pyGt" if self.is_go else "PyRuntime.pyGt"
        if isinstance(op, ast.GtE):
            return "pyGe" if self.is_go else "PyRuntime.pyGe"
        raise TranspileError(f"unsupported compare op: {type(op).__name__}")

    def _stmt(self, code: str) -> str:
        return code if self.is_go and code.endswith("}") else (code + ("" if self.is_go and code.endswith(";") else ("" if self.is_go else ";")))

    def _string_literal(self, text: str) -> str:
        escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'

    def _java_class_name_from_output(self, output_path: Path) -> str:
        stem = output_path.stem
        out = "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in stem)
        if not out:
            out = "pytra_generated"
        if out[0].isdigit():
            out = f"pytra_{out}"
        return out

    def _safe_name(self, name: str) -> str:
        if name == "_":
            return "__pytra_discard"
        return name

    def _annotation_tag(self, ann: ast.expr | None) -> str | None:
        if ann is None:
            return None
        if isinstance(ann, ast.Name):
            if ann.id == "int":
                return "int"
            if ann.id == "float":
                return "float64"
            if ann.id == "bool":
                return "bool"
            if ann.id == "str":
                return "string"
        return None

    def _coerce_go_value(self, rhs: str, go_type: str, rhs_go_type: str | None = None) -> str:
        if rhs_go_type == go_type:
            return rhs
        if rhs == "nil":
            if go_type == "int":
                return "0"
            if go_type == "float64":
                return "0.0"
            if go_type == "bool":
                return "false"
            if go_type == "string":
                return '""'
        if go_type == "int":
            return f"pyToInt({rhs})"
        if go_type == "float64":
            return f"pyToFloat({rhs})"
        if go_type == "bool":
            return f"pyBool({rhs})"
        if go_type == "string":
            return f"pyToString({rhs})"
        return rhs

    def _coerce_go_arg(self, code: str, src_t: str | None, dst_t: str | None) -> str:
        if dst_t is None:
            return code
        if src_t == dst_t:
            return code
        if dst_t == "int":
            return f"pyToInt({code})"
        if dst_t == "float64":
            if src_t == "int":
                return f"float64({code})"
            return f"pyToFloat({code})"
        if dst_t == "bool":
            return f"pyBool({code})"
        if dst_t == "string":
            return f"pyToString({code})"
        return code

    def _expr_go_type(self, expr: ast.expr | None) -> str | None:
        if expr is None:
            return None
        if isinstance(expr, ast.Constant):
            if isinstance(expr.value, bool):
                return "bool"
            if isinstance(expr.value, int):
                return "int"
            if isinstance(expr.value, float):
                return "float64"
            if isinstance(expr.value, str):
                return "string"
            return None
        if isinstance(expr, ast.Name):
            nm = self._safe_name(expr.id)
            for sc in reversed(self.scope_stack):
                t = sc.value_types.get(nm)
                if t is not None:
                    return t
            return None
        if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.USub):
            return self._expr_go_type(expr.operand)
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
            if expr.func.id == "int":
                return "int"
            if expr.func.id == "float":
                return "float64"
            if expr.func.id == "str":
                return "string"
            if expr.func.id == "bool":
                return "bool"
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute):
            if isinstance(expr.func.value, ast.Name):
                if expr.func.value.id == "math" and expr.func.attr in {"sqrt", "sin", "cos", "exp", "floor"}:
                    return "float64"
                if expr.func.value.id == "time" and expr.func.attr == "perf_counter":
                    return "float64"
        if isinstance(expr, ast.BinOp):
            lt = self._expr_go_type(expr.left)
            rt = self._expr_go_type(expr.right)
            if lt not in {"int", "float64"} or rt not in {"int", "float64"}:
                return None
            if isinstance(expr.op, ast.Div):
                return "float64"
            if isinstance(expr.op, ast.FloorDiv):
                return "int" if lt == "int" and rt == "int" else "float64"
            if isinstance(expr.op, (ast.Mod, ast.LShift, ast.RShift, ast.BitAnd, ast.BitOr, ast.BitXor)):
                return "int" if lt == "int" and rt == "int" else None
            if isinstance(expr.op, (ast.Add, ast.Sub, ast.Mult)):
                return "float64" if "float64" in {lt, rt} else "int"
        return None

    def _as_go_int(self, expr: ast.expr, expr_t: str | None) -> str:
        code = self.transpile_expr(expr)
        if expr_t == "int":
            return code
        return f"pyToInt({code})"

    def _as_go_float(self, expr: ast.expr, expr_t: str | None) -> str:
        code = self.transpile_expr(expr)
        if expr_t == "float64":
            return code
        if expr_t == "int":
            return f"float64({code})"
        return f"pyToFloat({code})"

    def _stmt_guarantees_return(self, body: list[ast.stmt]) -> bool:
        """ブロックが必ず return するかを簡易判定する。"""
        for stmt in reversed(body):
            if isinstance(stmt, ast.Pass):
                continue
            if isinstance(stmt, ast.Return):
                return True
            if isinstance(stmt, ast.Raise):
                return True
            if isinstance(stmt, ast.If):
                return self._stmt_guarantees_return(stmt.body) and self._stmt_guarantees_return(stmt.orelse)
            if isinstance(stmt, ast.Try):
                if not stmt.handlers:
                    return False
                return self._stmt_guarantees_return(stmt.body) and all(
                    self._stmt_guarantees_return(h.body) for h in stmt.handlers
                )
            return False
        return False
