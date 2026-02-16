#!/usr/bin/env python3
# Python -> Rust の変換器。
# native 変換（サブセット）を優先し、未対応構文は embed 方式へフォールバックします。

from __future__ import annotations

import argparse
import ast
from pathlib import Path
import sys

from common.transpile_shared import Scope, TempNameFactory, is_main_guard


class TranspileError(Exception):
    pass


class RustTranspiler:
    INDENT = "    "

    def __init__(self) -> None:
        self.temp_names = TempNameFactory(prefix="__pytra")

    def transpile_module(self, module: ast.Module) -> str:
        function_defs: list[str] = []
        main_stmts: list[ast.stmt] = []
        has_user_main = False

        for stmt in module.body:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                # Rust native モードでは import は無視。必要なら embed 側に倒す。
                continue
            if isinstance(stmt, ast.ClassDef):
                raise TranspileError("class is not supported in native Rust mode")
            if isinstance(stmt, ast.FunctionDef):
                if stmt.name == "main":
                    has_user_main = True
                function_defs.append(self.transpile_function(stmt))
                continue
            if is_main_guard(stmt):
                main_stmts.extend(stmt.body)
                continue
            main_stmts.append(stmt)

        parts: list[str] = []
        parts.extend(
            [
                "// このファイルは自動生成です（native Rust mode）。",
                "use std::time::{SystemTime, UNIX_EPOCH};",
                "",
                "trait PyStringify {",
                f"{self.INDENT}fn py_stringify(&self) -> String;",
                "}",
                "impl PyStringify for bool {",
                f"{self.INDENT}fn py_stringify(&self) -> String {{",
                f"{self.INDENT * 2}if *self {{ \"True\".to_string() }} else {{ \"False\".to_string() }}",
                f"{self.INDENT}}}",
                "}",
                "impl PyStringify for i64 { fn py_stringify(&self) -> String { format!(\"{}\", self) } }",
                "impl PyStringify for i32 { fn py_stringify(&self) -> String { format!(\"{}\", self) } }",
                "impl PyStringify for i16 { fn py_stringify(&self) -> String { format!(\"{}\", self) } }",
                "impl PyStringify for i8 { fn py_stringify(&self) -> String { format!(\"{}\", self) } }",
                "impl PyStringify for u64 { fn py_stringify(&self) -> String { format!(\"{}\", self) } }",
                "impl PyStringify for u32 { fn py_stringify(&self) -> String { format!(\"{}\", self) } }",
                "impl PyStringify for u16 { fn py_stringify(&self) -> String { format!(\"{}\", self) } }",
                "impl PyStringify for u8 { fn py_stringify(&self) -> String { format!(\"{}\", self) } }",
                "impl PyStringify for f64 { fn py_stringify(&self) -> String { format!(\"{}\", self) } }",
                "impl PyStringify for f32 { fn py_stringify(&self) -> String { format!(\"{}\", self) } }",
                "impl PyStringify for String { fn py_stringify(&self) -> String { self.clone() } }",
                "impl PyStringify for &str { fn py_stringify(&self) -> String { (*self).to_string() } }",
                "",
                "fn py_print<T: PyStringify>(v: T) {",
                f"{self.INDENT}println!(\"{{}}\", v.py_stringify());",
                "}",
                "",
                "fn perf_counter() -> f64 {",
                f"{self.INDENT}let d = SystemTime::now().duration_since(UNIX_EPOCH).unwrap();",
                f"{self.INDENT}d.as_secs_f64()",
                "}",
                "",
            ]
        )
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

    def transpile_function(self, fn: ast.FunctionDef) -> str:
        if self._contains_unsupported_native_annotation(fn):
            raise TranspileError(f"function has unsupported annotation in native Rust mode: {fn.name}")
        params: list[str] = []
        declared = set()
        for arg in fn.args.args:
            if arg.annotation is None:
                raise TranspileError(f"function '{fn.name}' arg '{arg.arg}' requires annotation")
            params.append(f"{arg.arg}: {self._map_annotation(arg.annotation)}")
            declared.add(arg.arg)

        ret = "()" if fn.returns is None else self._map_annotation(fn.returns)
        body = self.transpile_statements(fn.body, Scope(declared=declared))
        lines = [f"fn {fn.name}({', '.join(params)}) -> {ret} {{"] + self._indent_block(body) + ["}"]
        return "\n".join(lines)

    def transpile_statements(self, stmts: list[ast.stmt], scope: Scope) -> list[str]:
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
                if not isinstance(stmt.target, ast.Name):
                    raise TranspileError("annotated assignment target must be name")
                name = stmt.target.id
                rty = self._map_annotation(stmt.annotation)
                if rty in {"String", "f64", "f32"}:
                    raise TranspileError(f"{rty} variable is not supported in native Rust mode")
                if stmt.value is None:
                    out.append(f"let mut {name}: {rty};")
                else:
                    out.append(f"let mut {name}: {rty} = {self.transpile_expr(stmt.value)};")
                scope.declared.add(name)
                continue
            if isinstance(stmt, ast.Assign):
                if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
                    raise TranspileError("only simple assignment is supported")
                name = stmt.targets[0].id
                val = self.transpile_expr(stmt.value)
                if name in scope.declared:
                    out.append(f"{name} = {val};")
                else:
                    out.append(f"let mut {name} = {val};")
                    scope.declared.add(name)
                continue
            if isinstance(stmt, ast.AugAssign):
                if not isinstance(stmt.target, ast.Name):
                    raise TranspileError("augassign target must be name")
                op = self._binop(stmt.op)
                out.append(f"{stmt.target.id} = {stmt.target.id} {op} {self.transpile_expr(stmt.value)};")
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
            if isinstance(stmt, ast.Break):
                out.append("break;")
                continue
            if isinstance(stmt, ast.Continue):
                out.append("continue;")
                continue
            raise TranspileError(f"unsupported statement: {type(stmt).__name__}")
        return out

    def _transpile_if(self, stmt: ast.If, scope: Scope) -> list[str]:
        lines: list[str] = [f"if {self.transpile_expr(stmt.test)} {{"]
        lines.extend(self._indent_block(self.transpile_statements(stmt.body, Scope(declared=set(scope.declared)))))
        if stmt.orelse:
            lines.append("} else {")
            lines.extend(self._indent_block(self.transpile_statements(stmt.orelse, Scope(declared=set(scope.declared)))))
        lines.append("}")
        return lines

    def _parse_range(self, expr: ast.expr) -> tuple[str, str, str] | None:
        if not isinstance(expr, ast.Call) or not isinstance(expr.func, ast.Name) or expr.func.id != "range":
            return None
        if expr.keywords:
            raise TranspileError("range with keyword args is not supported")
        argc = len(expr.args)
        if argc == 1:
            return "0", self.transpile_expr(expr.args[0]), "1"
        if argc == 2:
            return self.transpile_expr(expr.args[0]), self.transpile_expr(expr.args[1]), "1"
        if argc == 3:
            return self.transpile_expr(expr.args[0]), self.transpile_expr(expr.args[1]), self.transpile_expr(expr.args[2])
        raise TranspileError("range arg count > 3 is not supported")

    def _transpile_for(self, stmt: ast.For, scope: Scope) -> list[str]:
        if not isinstance(stmt.target, ast.Name):
            raise TranspileError("for target must be name")
        name = stmt.target.id
        rng = self._parse_range(stmt.iter)
        if rng is None:
            raise TranspileError("only for-in-range is supported in native Rust mode")
        start, stop, step = rng
        lines: list[str] = []
        if step == "1":
            lines.append(f"for {name} in ({start})..({stop}) {{")
            body_scope = Scope(declared=set(scope.declared))
            body_scope.declared.add(name)
            lines.extend(self._indent_block(self.transpile_statements(stmt.body, body_scope)))
            lines.append("}")
        else:
            i_name = self.temp_names.new("i")
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

    def transpile_expr(self, expr: ast.expr) -> str:
        if isinstance(expr, ast.Name):
            if expr.id == "True":
                return "true"
            if expr.id == "False":
                return "false"
            return expr.id
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
            if isinstance(expr.op, ast.FloorDiv):
                return f"(({l}) / ({r}))"
            return f"(({l}) {self._binop(expr.op)} ({r}))"
        if isinstance(expr, ast.UnaryOp):
            return f"({self._unaryop(expr.op)}{self.transpile_expr(expr.operand)})"
        if isinstance(expr, ast.BoolOp):
            op = "&&" if isinstance(expr.op, ast.And) else "||"
            return "(" + f" {op} ".join(self.transpile_expr(v) for v in expr.values) + ")"
        if isinstance(expr, ast.Compare):
            if len(expr.ops) != 1 or len(expr.comparators) != 1:
                raise TranspileError("chained comparison is not supported")
            l = self.transpile_expr(expr.left)
            r = self.transpile_expr(expr.comparators[0])
            return f"(({l}) {self._cmpop(expr.ops[0])} ({r}))"
        if isinstance(expr, ast.Call):
            return self._transpile_call(expr)
        if isinstance(expr, ast.IfExp):
            return f"(if {self.transpile_expr(expr.test)} {{ {self.transpile_expr(expr.body)} }} else {{ {self.transpile_expr(expr.orelse)} }})"
        raise TranspileError(f"unsupported expression: {type(expr).__name__}")

    def _transpile_call(self, call: ast.Call) -> str:
        if call.keywords:
            raise TranspileError("keyword args are not supported")
        args = [self.transpile_expr(a) for a in call.args]
        if isinstance(call.func, ast.Name):
            fn = call.func.id
            if fn == "print":
                if len(args) == 0:
                    return 'println!("")'
                if len(args) == 1:
                    return f"py_print({args[0]})"
                # 複数引数は format! で空白区切り表示
                fmt = " ".join(["{}"] * len(args))
                return f'println!("{fmt}", {", ".join(args)})'
            if fn == "len" and len(args) == 1:
                return f"({args[0]}.len() as i64)"
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
        raise TranspileError("only direct calls are supported")

    def _map_annotation(self, ann: ast.expr) -> str:
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
        if isinstance(op, ast.USub):
            return "-"
        if isinstance(op, ast.UAdd):
            return "+"
        if isinstance(op, ast.Not):
            return "!"
        raise TranspileError(f"unsupported unary op: {type(op).__name__}")

    def _contains_unsupported_native_annotation(self, fn: ast.FunctionDef) -> bool:
        unsupported = {"str", "float", "float32"}
        for arg in fn.args.args:
            if isinstance(arg.annotation, ast.Name) and arg.annotation.id in unsupported:
                return True
        if isinstance(fn.returns, ast.Name) and fn.returns.id in unsupported:
            return True
        return False

    def _escape_str(self, value: str) -> str:
        esc = (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )
        return f"\"{esc}\".to_string()"

    def _indent_block(self, lines: list[str]) -> list[str]:
        return [self.INDENT + line if line else "" for line in lines]


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


def transpile_file_embed(input_path: Path, output_path: Path) -> None:
    source = input_path.read_text(encoding="utf-8")
    source_literal = _rust_raw_string_literal(source)
    input_name = input_path.name

    rust = f"""// このファイルは自動生成です。編集しないでください。
// 入力 Python: {input_name}

use std::env;
use std::process::Command;

fn run_with(interpreter: &str, source: &str) -> Option<i32> {{
    let mut cmd = Command::new(interpreter);
    cmd.arg("-c").arg(source);

    // sample/py が `from py_module ...` を使うため `PYTHONPATH=src` を付与する。
    let py_path = match env::var("PYTHONPATH") {{
        Ok(v) if !v.is_empty() => format!("src:{{}}", v),
        _ => "src".to_string(),
    }};
    cmd.env("PYTHONPATH", py_path);

    // 親プロセスの標準入出力をそのまま使う。
    let status = cmd.status().ok()?;
    Some(status.code().unwrap_or(1))
}}

fn main() {{
    let source: &str = {source_literal};

    // python3 を優先し、無ければ python を試す。
    if let Some(code) = run_with("python3", source) {{
        std::process::exit(code);
    }}
    if let Some(code) = run_with("python", source) {{
        std::process::exit(code);
    }}

    eprintln!("error: python interpreter not found (python3/python)");
    std::process::exit(1);
}}
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rust, encoding="utf-8")


def transpile_file_native(input_path: Path, output_path: Path) -> None:
    source = input_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(input_path))
    rust = RustTranspiler().transpile_module(tree)
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
