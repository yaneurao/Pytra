"""Python → EAST1 パーサー。

toolchain/ に依存しない自前実装。
§5.1: Any/object 禁止。
§5.2: Python 標準モジュール直接 import 禁止 (pytra.std.* を使う)。
§5.4: ast モジュール禁止。
§5.5: グローバル可変状態禁止。

行ベース + 正規表現で Python ソースを解析し、EAST1 dataclass ノードを生成する。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union

from pytra.std import re

from toolchain2.parse.py.source_span import SourceSpan, NULL_SPAN, make_span
from toolchain2.parse.py.nodes import (
    JsonVal,
    # Type expressions
    NamedType, GenericType, TypeExpr,
    # Trivia
    TriviaBlank, TriviaComment, TriviaNode,
    # Import
    ImportAlias,
    # Semantic
    Cast, Keyword, Comprehension, DictEntry,
    # Expressions
    ExprBase, Name, Constant, BinOp, UnaryOp, BoolOp, Compare,
    Call, Attribute, Subscript, SliceExpr, IfExp, ListExpr, TupleExpr,
    DictExpr, ListComp, RangeExpr, LambdaExpr, Expr, expr_to_jv,
    # Statements
    Import, ImportFrom, AnnAssign, Assign, AugAssign, ExprStmt, Swap, Return, Raise, Pass, Try, ExceptHandler,
    If, ForRange, For, While, FunctionDef, ClassDef, Stmt,
    # Module
    Module,
)
from toolchain2.parse.py.type_resolver import (
    default_type_aliases,
    resolve_type_annotation,
    annotation_to_type_expr,
)


# ---------------------------------------------------------------------------
# Parse context (関数引数で渡す、グローバル可変状態禁止 §5.5)
# ---------------------------------------------------------------------------

@dataclass
class ParseContext:
    """パーサーの状態。全て関数引数で渡す。"""
    filename: str
    lines: list[str]
    type_aliases: dict[str, str]
    fn_returns: dict[str, str]
    class_method_returns: dict[str, dict[str, str]]
    class_bases: dict[str, Optional[str]]
    import_symbols: dict[str, dict[str, str]]
    import_modules: dict[str, str]
    import_bindings: list[dict[str, JsonVal]]
    qualified_symbol_refs: list[dict[str, JsonVal]]
    implicit_builtin_modules: dict[str, bool]  # set の代替
    class_names: dict[str, bool]  # set の代替: 定義されたクラス名


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _strip_inline_comment(line: str) -> str:
    """行末コメントを除去する（文字列リテラル内は考慮）。"""
    in_single = False
    in_double = False
    escaped = False
    for i in range(len(line)):
        ch = line[i]
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            return line[:i].rstrip()
    return line


def _resolve_type(ann: str, ctx: ParseContext) -> str:
    """型注釈を正規化する。"""
    return resolve_type_annotation(ann, ctx.type_aliases)


def _make_type_expr(ann: str, ctx: ParseContext) -> TypeExpr:
    """型注釈を TypeExpr に変換する。"""
    return annotation_to_type_expr(ann, ctx.type_aliases)


def _is_identifier(s: str) -> bool:
    """文字列が Python 識別子かどうか。"""
    if s == "" or len(s) == 0:
        return False
    ch0 = s[0]
    if not (ch0 == "_" or (ch0 >= "a" and ch0 <= "z") or (ch0 >= "A" and ch0 <= "Z")):
        return False
    for i in range(1, len(s)):
        ch = s[i]
        if not (ch == "_" or (ch >= "a" and ch <= "z") or (ch >= "A" and ch <= "Z") or (ch >= "0" and ch <= "9")):
            return False
    return True



def _parse_from_import(s: str) -> tuple[str, str]:
    """'from MOD import NAMES' をパースして (module, names_text) を返す。失敗時は ("", "")。"""
    m = re.match(r"^from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+import\s+(.+)$", s)
    if m is None:
        return "", ""
    return re.strip_group(m, 1), re.strip_group(m, 2)


def _parse_def_header(s: str) -> tuple[str, str, str]:
    """'def NAME(ARGS) -> RET:' をパース。(name, args, ret)。失敗は ("", "", "")。"""
    m = re.match(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\((.*)\)\s*(?:->\s*(.+)\s*)?:\s*$", s)
    if m is None:
        return "", "", ""
    return re.strip_group(m, 1), re.strip_group(m, 2), re.strip_group(m, 3)


def _parse_def_name(s: str) -> str:
    """'def NAME(...):' からNAMEを抽出。失敗時は ""。"""
    name, _, _ = _parse_def_header(s)
    return name


def _parse_class_name(s: str) -> str:
    """'class NAME:' からNAMEを抽出。"""
    m = re.match(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\(([A-Za-z_][A-Za-z0-9_]*)\))?\s*:\s*$", s)
    if m is None:
        return ""
    return re.strip_group(m, 1)


def _parse_ann_assign(s: str) -> tuple[str, str, str]:
    """'NAME: TYPE = VALUE' をパース。失敗時は ("", "", "")。"""
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^=]+?)\s*=\s*(.+)$", s)
    if m is None:
        return "", "", ""
    return re.strip_group(m, 1), re.strip_group(m, 2), re.strip_group(m, 3)


def _parse_aug_assign(s: str) -> tuple[str, str, str]:
    """augmented assignment をパース。失敗時は ("", "", "")。"""
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*(\+=|-=|\*=|/=|//=|%=|&=|\|=|\^=|<<=|>>=)\s*(.+)$", s)
    if m is None:
        return "", "", ""
    return re.strip_group(m, 1), re.strip_group(m, 2), re.strip_group(m, 3)


def _parse_simple_assign(s: str) -> tuple[str, str]:
    """simple assignment をパース。失敗時は ("", "")。"""
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", s)
    if m is None:
        return "", ""
    return re.strip_group(m, 1), re.strip_group(m, 2)


def _parse_for_header(s: str) -> tuple[str, str]:
    """'for TARGET in ITER:' をパース。(target_name, iter_text)。失敗は ("", "")。"""
    m = re.match(r"^for\s+(.+)\s+in\s+(.+):$", s)
    if m is None:
        return "", ""
    return re.strip_group(m, 1), re.strip_group(m, 2)


def _parse_main_guard(s: str) -> bool:
    """'if __name__ == "__main__":' を検出する。"""
    m = re.match(r"^if\s+__name__\s*==\s*[\"']__main__[\"']\s*:\s*$", s)
    return m is not None


def _extract_element_type(container_type: str) -> str:
    """コンテナ型から要素型を抽出する。list[int64] → int64, dict[str,int64] → str。"""
    if container_type.startswith("list[") and container_type.endswith("]"):
        return container_type[5:-1]
    if container_type.startswith("set[") and container_type.endswith("]"):
        return container_type[4:-1]
    if container_type.startswith("tuple[") and container_type.endswith("]"):
        inner = container_type[6:-1]
        # tuple の最初の要素型
        parts = inner.split(",")
        if len(parts) > 0:
            return parts[0].strip()
    if container_type.startswith("dict[") and container_type.endswith("]"):
        inner = container_type[5:-1]
        parts = inner.split(",")
        if len(parts) >= 2:
            return parts[1].strip()  # value type
        if len(parts) == 1:
            return parts[0].strip()
    if container_type == "str":
        return "str"
    return "unknown"


def _infer_range_mode(step: Expr) -> str:
    """ForRange の range_mode を step から推論する (golden 準拠)。

    Constant(1) → ascending, Constant(-1) → descending, それ以外 → dynamic。
    UnaryOp(USub, Constant(1)) は Constant(-1) ではないので dynamic になる。
    """
    if isinstance(step, Constant) and isinstance(step.value, int):
        if step.value == 1:
            return "ascending"
        if step.value == -1:
            return "descending"
    return "dynamic"


def _parse_range_call(s: str) -> Optional[str]:
    """'range(ARGS)' をパース。ARGS 部分を返す。range でなければ None。"""
    s = s.strip()
    if not s.startswith("range("):
        return None
    if not s.endswith(")"):
        return None
    return s[6:-1]


# ---------------------------------------------------------------------------
# Expression tokenizer
# ---------------------------------------------------------------------------

@dataclass
class Token:
    kind: str   # "INT", "FLOAT", "STR", "NAME", "OP", "EOF"
    value: str
    start: int
    end: int


def _tokenize_expr(text: str) -> list[Token]:
    """式テキストをトークン列に変換する。"""
    tokens: list[Token] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        # Skip whitespace
        if ch == " " or ch == "\t":
            i += 1
            continue

        # Numbers
        if ch >= "0" and ch <= "9":
            start = i
            # hex, bin, oct
            if ch == "0" and i + 1 < n:
                next_ch = text[i + 1]
                if next_ch == "x" or next_ch == "X":
                    i += 2
                    while i < n and ((text[i] >= "0" and text[i] <= "9") or (text[i] >= "a" and text[i] <= "f") or (text[i] >= "A" and text[i] <= "F") or text[i] == "_"):
                        i += 1
                    tokens.append(Token("INT", text[start:i], start, i))
                    continue
                if next_ch == "b" or next_ch == "B":
                    i += 2
                    while i < n and (text[i] == "0" or text[i] == "1" or text[i] == "_"):
                        i += 1
                    tokens.append(Token("INT", text[start:i], start, i))
                    continue
                if next_ch == "o" or next_ch == "O":
                    i += 2
                    while i < n and text[i] >= "0" and text[i] <= "7":
                        i += 1
                    tokens.append(Token("INT", text[start:i], start, i))
                    continue
            while i < n and ((text[i] >= "0" and text[i] <= "9") or text[i] == "_"):
                i += 1
            is_float = False
            if i < n and text[i] == ".":
                # Check it's not .. or method call on int
                if i + 1 < n and text[i + 1] >= "0" and text[i + 1] <= "9":
                    is_float = True
                    i += 1
                    while i < n and ((text[i] >= "0" and text[i] <= "9") or text[i] == "_"):
                        i += 1
            if i < n and (text[i] == "e" or text[i] == "E"):
                is_float = True
                i += 1
                if i < n and (text[i] == "+" or text[i] == "-"):
                    i += 1
                while i < n and (text[i] >= "0" and text[i] <= "9"):
                    i += 1
            kind = "FLOAT" if is_float else "INT"
            tokens.append(Token(kind, text[start:i], start, i))
            continue

        # Strings
        if ch == '"' or ch == "'":
            start = i
            quote = ch
            # Check for triple-quote
            if i + 2 < n and text[i + 1] == quote and text[i + 2] == quote:
                i += 3
                while i < n:
                    if text[i] == "\\" and i + 1 < n:
                        i += 2
                        continue
                    if text[i] == quote and i + 2 < n and text[i + 1] == quote and text[i + 2] == quote:
                        i += 3
                        break
                    i += 1
            else:
                i += 1
                while i < n and text[i] != quote:
                    if text[i] == "\\":
                        i += 1
                    i += 1
                if i < n:
                    i += 1
            tokens.append(Token("STR", text[start:i], start, i))
            continue

        # Identifiers / keywords / string prefixes (r"...", b"...", f"...")
        if ch == "_" or (ch >= "a" and ch <= "z") or (ch >= "A" and ch <= "Z"):
            start = i
            i += 1
            while i < n and (text[i] == "_" or (text[i] >= "a" and text[i] <= "z") or (text[i] >= "A" and text[i] <= "Z") or (text[i] >= "0" and text[i] <= "9")):
                i += 1
            word = text[start:i]
            # Check for string prefix: r"...", b"...", f"...", rb"...", br"..."
            if i < n and (text[i] == '"' or text[i] == "'") and word in ("r", "b", "f", "rb", "br", "rf", "fr", "R", "B", "F"):
                # Parse as string with prefix
                quote = text[i]
                if i + 2 < n and text[i + 1] == quote and text[i + 2] == quote:
                    i += 3
                    while i < n:
                        if text[i] == "\\" and i + 1 < n:
                            i += 2
                            continue
                        if text[i] == quote and i + 2 < n and text[i + 1] == quote and text[i + 2] == quote:
                            i += 3
                            break
                        i += 1
                else:
                    i += 1
                    while i < n and text[i] != quote:
                        if text[i] == "\\":
                            i += 1
                        i += 1
                    if i < n:
                        i += 1
                tokens.append(Token("STR", text[start:i], start, i))
                continue
            tokens.append(Token("NAME", word, start, i))
            continue

        # Two-char operators
        if i + 1 < n:
            two = text[i:i + 2]
            if two == "//" or two == "**" or two == "==" or two == "!=" or two == "<=" or two == ">=" or two == "<<" or two == ">>" or two == "+=" or two == "-=" or two == "*=" or two == "/=" or two == "%=" or two == "->":
                tokens.append(Token("OP", two, i, i + 2))
                i += 2
                continue

        # Single-char operators
        if ch in "+-*/%=<>()[]{},.:|&^~@!":
            tokens.append(Token("OP", ch, i, i + 1))
            i += 1
            continue

        # Skip unknown
        i += 1

    tokens.append(Token("EOF", "", n, n))
    return tokens


# ---------------------------------------------------------------------------
# Expression parser (precedence climbing)
# ---------------------------------------------------------------------------

@dataclass
class ExprParser:
    """式パーサー。トークン列を走査して Expr ノードを生成する。"""
    tokens: list[Token]
    pos: int
    source_line: int
    line_col_offset: int
    source_text: str
    name_types: dict[str, str]
    ctx: ParseContext

    def peek(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token("EOF", "", 0, 0)

    def advance(self) -> Token:
        tok = self.peek()
        if self.pos < len(self.tokens):
            self.pos += 1
        return tok

    def expect(self, kind: str, value: str) -> Token:
        tok = self.advance()
        if tok.kind != kind or tok.value != value:
            raise ValueError("expected " + value + " but got " + tok.value)
        return tok

    def _span(self, local_start: int, local_end: int) -> SourceSpan:
        """ローカル位置 → 絶対位置の SourceSpan を返す。"""
        return make_span(
            self.source_line,
            self.line_col_offset + local_start,
            self.source_line,
            self.line_col_offset + local_end,
        )

    def _base(self, local_start: int, local_end: int, resolved_type: str, borrow_kind: str) -> ExprBase:
        """ExprBase を生成する。start/end は式テキスト内のローカル位置。"""
        return ExprBase(
            source_span=self._span(local_start, local_end),
            resolved_type=resolved_type,
            casts=[],
            borrow_kind=borrow_kind,
            repr_text=self.source_text[local_start:local_end],
        )

    def _to_local(self, abs_col: int) -> int:
        """絶対 col → ローカル位置に逆算する。"""
        return abs_col - self.line_col_offset

    def _child_local_start(self, child: Expr) -> int:
        """子ノードのローカル開始位置。"""
        return self._to_local(_expr_col(child))

    def _child_local_end(self, child: Expr) -> int:
        """子ノードのローカル終了位置。"""
        return self._to_local(_expr_end_col(child))

    # --- Precedence climbing ---

    def parse_expr(self) -> Expr:
        if self.peek().value == "lambda":
            return self._parse_lambda()
        return self._parse_ternary()

    def _parse_lambda(self) -> LambdaExpr:
        """lambda args: body"""
        tok = self.advance()  # consume 'lambda'
        start = tok.start
        # Parse parameter list until ':'
        params: list[str] = []
        arg_types: dict[str, str] = {}
        while self.peek().value != ":" and self.peek().kind != "EOF":
            if self.peek().kind == "NAME":
                pname = self.advance().value
                arg_types[pname] = "unknown"
                params.append(pname)
            elif self.peek().value == ",":
                self.advance()
            elif self.peek().value == "=":
                # default value — skip until , or :
                self.advance()
                # Consume default value expression (stop at , or :)
                depth = 0
                while self.peek().kind != "EOF":
                    if self.peek().value in (",", ":") and depth == 0:
                        break
                    if self.peek().value in ("(", "[", "{"):
                        depth += 1
                    elif self.peek().value in (")", "]", "}"):
                        depth -= 1
                    self.advance()
            else:
                break
        self.expect("OP", ":")
        body = self._parse_ternary()
        end = self._child_local_end(body)
        ret_type = _get_resolved_type(body)
        base = self._base(start, end, "unknown", "value")
        return LambdaExpr(base=base, args=params, arg_types=arg_types, body=body, return_type=ret_type)

    def _parse_ternary(self) -> Expr:
        """a if cond else b"""
        body = self._parse_or()
        if self.peek().value == "if":
            self.advance()
            test = self._parse_or()
            self.expect("NAME", "else")
            orelse = self._parse_ternary()
            # IfExp span: body の開始から orelse の終了まで
            start = self._child_local_start(body)
            end = self._child_local_end(orelse)
            res_type = _get_resolved_type(body)
            base = self._base(start, end, res_type, "value")
            return IfExp(base=base, test=test, body=body, orelse=orelse)
        return body

    def _parse_or(self) -> Expr:
        left = self._parse_and()
        while self.peek().value == "or":
            self.advance()
            right = self._parse_and()
            start = self._child_local_start(left)
            end = self._child_local_end(right)
            base = self._base(start, end, "bool", "value")
            left = BoolOp(base=base, op="Or", values=[left, right])
        return left

    def _parse_and(self) -> Expr:
        left = self._parse_not()
        while self.peek().value == "and":
            self.advance()
            right = self._parse_not()
            start = self._child_local_start(left)
            end = self._child_local_end(right)
            base = self._base(start, end, "bool", "value")
            left = BoolOp(base=base, op="And", values=[left, right])
        return left

    def _parse_not(self) -> Expr:
        if self.peek().value == "not":
            tok = self.advance()
            operand = self._parse_not()
            end = self._child_local_end(operand)
            base = self._base(tok.start, end, "bool", "value")
            return UnaryOp(base=base, op="Not", operand=operand)
        return self._parse_compare()

    def _parse_compare(self) -> Expr:
        left = self._parse_bitor()
        ops: list[str] = []
        comparators: list[Expr] = []
        while True:
            tok = self.peek()
            op_str = ""
            if tok.value == "<":
                op_str = "Lt"
            elif tok.value == ">":
                op_str = "Gt"
            elif tok.value == "<=":
                op_str = "LtE"
            elif tok.value == ">=":
                op_str = "GtE"
            elif tok.value == "==":
                op_str = "Eq"
            elif tok.value == "!=":
                op_str = "NotEq"
            elif tok.value == "in":
                op_str = "In"
            elif tok.value == "not":
                # not in
                self.advance()
                self.expect("NAME", "in")
                op_str = "NotIn"
                ops.append(op_str)
                comparators.append(self._parse_bitor())
                continue
            elif tok.value == "is":
                self.advance()
                if self.peek().value == "not":
                    self.advance()
                    op_str = "IsNot"
                else:
                    op_str = "Is"
                ops.append(op_str)
                comparators.append(self._parse_bitor())
                continue
            else:
                break
            self.advance()
            ops.append(op_str)
            comparators.append(self._parse_bitor())
        if len(ops) > 0:
            start = self._child_local_start(left)
            end = self._child_local_end(comparators[-1])
            base = self._base(start, end, "bool", "value")
            return Compare(base=base, left=left, ops=ops, comparators=comparators)
        return left

    def _parse_bitor(self) -> Expr:
        left = self._parse_bitxor()
        while self.peek().value == "|":
            self.advance()
            right = self._parse_bitxor()
            start = self._child_local_start(left)
            end = self._child_local_end(right)
            base = self._base(start, end, "int64", "value")
            left = BinOp(base=base, left=left, op="BitOr", right=right)
        return left

    def _parse_bitxor(self) -> Expr:
        left = self._parse_bitand()
        while self.peek().value == "^":
            self.advance()
            right = self._parse_bitand()
            start = self._child_local_start(left)
            end = self._child_local_end(right)
            base = self._base(start, end, "int64", "value")
            left = BinOp(base=base, left=left, op="BitXor", right=right)
        return left

    def _parse_bitand(self) -> Expr:
        left = self._parse_shift()
        while self.peek().value == "&":
            self.advance()
            right = self._parse_shift()
            start = self._child_local_start(left)
            end = self._child_local_end(right)
            base = self._base(start, end, "int64", "value")
            left = BinOp(base=base, left=left, op="BitAnd", right=right)
        return left

    def _parse_shift(self) -> Expr:
        left = self._parse_addsub()
        while self.peek().value == "<<" or self.peek().value == ">>":
            op_tok = self.advance()
            right = self._parse_addsub()
            op_name = "LShift" if op_tok.value == "<<" else "RShift"
            start = self._child_local_start(left)
            end = self._child_local_end(right)
            base = self._base(start, end, "int64", "value")
            left = BinOp(base=base, left=left, op=op_name, right=right)
        return left

    def _parse_addsub(self) -> Expr:
        left = self._parse_muldiv()
        while self.peek().value == "+" or self.peek().value == "-":
            op_tok = self.advance()
            right = self._parse_muldiv()
            op_name = "Add" if op_tok.value == "+" else "Sub"
            start = self._child_local_start(left)
            end = self._child_local_end(right)
            left_type = _get_resolved_type(left)
            right_type = _get_resolved_type(right)
            res_type = _binop_result_type(left_type, right_type, op_name)
            base = self._base(start, end, res_type, "value")
            base.casts = _compute_binop_casts(left_type, right_type, op_name)
            left = BinOp(base=base, left=left, op=op_name, right=right)
        return left

    def _parse_muldiv(self) -> Expr:
        left = self._parse_unary()
        while self.peek().value in ("*", "/", "//", "%"):
            op_tok = self.advance()
            right = self._parse_unary()
            op_map: dict[str, str] = {"*": "Mult", "/": "Div", "//": "FloorDiv", "%": "Mod"}
            op_name = op_map.get(op_tok.value, op_tok.value)
            start = self._child_local_start(left)
            end = self._child_local_end(right)
            left_type = _get_resolved_type(left)
            right_type = _get_resolved_type(right)
            res_type = _binop_result_type(left_type, right_type, op_name)
            base = self._base(start, end, res_type, "value")
            # Numeric promotion casts
            casts = _compute_binop_casts(left_type, right_type, op_name)
            base.casts = casts
            left = BinOp(base=base, left=left, op=op_name, right=right)
        return left

    def _parse_unary(self) -> Expr:
        tok = self.peek()
        if tok.value == "-" and tok.kind == "OP":
            self.advance()
            operand = self._parse_unary()
            end = self._child_local_end(operand)
            res_type = _get_resolved_type(operand)
            base = self._base(tok.start, end, res_type, "value")
            return UnaryOp(base=base, op="USub", operand=operand)
        if tok.value == "+" and tok.kind == "OP":
            self.advance()
            operand = self._parse_unary()
            end = self._child_local_end(operand)
            res_type = _get_resolved_type(operand)
            base = self._base(tok.start, end, res_type, "value")
            return UnaryOp(base=base, op="UAdd", operand=operand)
        if tok.value == "~" and tok.kind == "OP":
            self.advance()
            operand = self._parse_unary()
            end = self._child_local_end(operand)
            base = self._base(tok.start, end, "int64", "value")
            return UnaryOp(base=base, op="Invert", operand=operand)
        return self._parse_power()

    def _parse_power(self) -> Expr:
        left = self._parse_postfix()
        if self.peek().value == "**":
            self.advance()
            right = self._parse_unary()  # right-associative
            start = self._child_local_start(left)
            end = self._child_local_end(right)
            base = self._base(start, end, "float64", "value")
            left = BinOp(base=base, left=left, op="Pow", right=right)
        return left

    def _parse_postfix(self) -> Expr:
        """後置演算子: .attr, [index], (call)"""
        expr = self._parse_primary()
        while True:
            tok = self.peek()
            if tok.value == ".":
                self.advance()
                attr_tok = self.advance()
                end = attr_tok.end
                base = self._base(self._child_local_start(expr), end, "unknown", "value")
                expr = Attribute(base=base, value=expr, attr=attr_tok.value)
            elif tok.value == "[":
                self.advance()
                index = self._parse_subscript_index()
                self.expect("OP", "]")
                end_tok = self.tokens[self.pos - 1]
                # Subscript 型推論: container[index] → element type
                container_type = _get_resolved_type(expr)
                sub_type = _extract_element_type(container_type) if not isinstance(index, SliceExpr) else container_type
                base = self._base(self._child_local_start(expr), end_tok.end, sub_type, "value")
                expr = Subscript(base=base, value=expr, slice_expr=index)
            elif tok.value == "(":
                expr = self._parse_call(expr)
            else:
                break
        return expr

    def _parse_call(self, func: Expr) -> Call:
        """関数呼び出し。"""
        self.expect("OP", "(")
        args: list[Expr] = []
        keywords: list[Keyword] = []
        if self.peek().value != ")":
            while True:
                # Check for keyword argument: name=value
                if self.peek().kind == "NAME" and self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].value == "=":
                    kw_name = self.advance().value
                    self.advance()  # skip =
                    kw_value = self.parse_expr()
                    keywords.append(Keyword(arg=kw_name, value_node=kw_value))
                elif self.peek().value == "*":
                    # *args — starred argument, skip * and parse expr
                    self.advance()
                    args.append(self.parse_expr())
                else:
                    arg_expr = self.parse_expr()
                    # Check for generator expression: func(expr for x in iter)
                    if self.peek().value == "for" and len(args) == 0 and len(keywords) == 0:
                        gens: list[Comprehension] = []
                        while self.peek().value == "for":
                            self.advance()
                            target = self._parse_comp_target()
                            self.expect("NAME", "in")
                            iter_expr = self._parse_comp_iter()
                            ifs: list[Expr] = []
                            while self.peek().value == "if":
                                self.advance()
                                ifs.append(self._parse_comp_iter())
                            gens.append(Comprehension(target=target, iter_expr=iter_expr, ifs=ifs, is_async=False))
                        # Wrap as ListComp (generator)
                        gen_base = ExprBase(source_span=arg_expr.base.source_span if hasattr(arg_expr, 'base') else NULL_SPAN,
                                          resolved_type="unknown", casts=[], borrow_kind="value", repr_text="")
                        arg_expr = ListComp(base=gen_base, elt=arg_expr, generators=gens)
                    args.append(arg_expr)
                if self.peek().value != ",":
                    break
                self.advance()  # skip comma
        self.expect("OP", ")")
        end_tok = self.tokens[self.pos - 1]
        start = self._child_local_start(func)
        end = end_tok.end
        # Resolve call type
        func_name = _get_func_name(func)
        res_type = self._resolve_call_type(func_name, args)
        # Method call: owner type から戻り値型を推論
        if isinstance(func, Attribute) and res_type == "unknown":
            owner_type = _get_resolved_type(func.value)
            owner_base = owner_type.split("[")[0] if "[" in owner_type else owner_type
            if func_name == "pop" and owner_base in ("list", "deque"):
                res_type = _extract_element_type(owner_type)
            elif func_name == "get" and owner_base == "dict":
                res_type = _extract_element_type(owner_type)  # value type
        base = self._base(start, end, res_type, "value")
        call = Call(base=base, func=func, args=args, keywords=keywords)
        # Annotate builtin calls
        self._annotate_call(call, func_name)
        return call

    def _resolve_call_type(self, func_name: str, args: list[Expr]) -> str:
        """関数呼び出しの戻り値型を推論する。"""
        if func_name in self.ctx.fn_returns:
            return _resolve_type(self.ctx.fn_returns[func_name], self.ctx)
        if func_name == "int":
            return "int64"
        if func_name == "float":
            return "float64"
        if func_name == "str":
            return "str"
        if func_name == "bool":
            return "bool"
        if func_name == "len":
            return "int64"
        if func_name == "abs":
            if len(args) > 0:
                return _get_resolved_type(args[0])
            return "int64"
        if func_name == "min" or func_name == "max":
            if len(args) > 0:
                return _get_resolved_type(args[0])
            return "unknown"
        if func_name == "range":
            return "range"
        if func_name == "print":
            return "None"
        if func_name == "perf_counter":
            return "float64"
        if func_name == "Path":
            return "Path"
        if func_name == "ord":
            return "int64"
        if func_name == "chr":
            return "str"
        if func_name == "isinstance":
            return "bool"
        if func_name == "enumerate":
            return "unknown"
        if func_name == "reversed":
            return "unknown"
        if func_name == "sorted":
            return "unknown"
        if func_name == "zip":
            return "unknown"
        # Class constructor: ClassName() → ClassName
        if func_name in self.ctx.class_names:
            return func_name
        # Method return types
        if func_name == "append" or func_name == "extend" or func_name == "insert" or func_name == "clear" or func_name == "sort" or func_name == "reverse":
            return "None"
        if func_name == "pop":
            return "unknown"
        if func_name == "get":
            return "unknown"
        if func_name == "keys" or func_name == "values" or func_name == "items":
            return "unknown"
        if func_name == "join":
            return "str"
        if func_name == "split" or func_name == "strip" or func_name == "lstrip" or func_name == "rstrip" or func_name == "lower" or func_name == "upper" or func_name == "replace":
            return "str"
        if func_name == "find" or func_name == "index" or func_name == "count":
            return "int64"
        if func_name == "startswith" or func_name == "endswith":
            return "bool"
        if func_name == "write_text" or func_name == "write_rgb_png" or func_name == "save":
            return "None"
        if func_name == "read_text":
            return "str"
        return "unknown"

    def _annotate_call(self, call: Call, func_name: str) -> None:
        """組み込み関数呼び出しにセマンティック情報を付与する。"""
        # Golden 準拠: print は pytra.built_in.io_ops、他は pytra.core.py_runtime
        # (runtime_call, module_id, runtime_symbol, semantic_tag)
        _DEFAULT_RT_MOD = "pytra.core.py_runtime"
        builtin_map: dict[str, tuple[str, str, str, str]] = {
            "print": ("py_print", "pytra.built_in.io_ops", "py_print", "core.print"),
            "len": ("py_len", _DEFAULT_RT_MOD, "len", "core.len"),
            "abs": ("py_abs", _DEFAULT_RT_MOD, "abs", "core.abs"),
            "min": ("py_min", _DEFAULT_RT_MOD, "min", "core.min"),
            "max": ("py_max", _DEFAULT_RT_MOD, "max", "core.max"),
            "int": ("py_to_string", _DEFAULT_RT_MOD, "int", "cast.int"),
            "float": ("py_to_string", _DEFAULT_RT_MOD, "float", "cast.float"),
            "str": ("py_to_string", _DEFAULT_RT_MOD, "str", "cast.str"),
            "bool": ("py_to_string", _DEFAULT_RT_MOD, "bool", "cast.bool"),
            "ord": ("py_ord", _DEFAULT_RT_MOD, "ord", "core.ord"),
            "chr": ("py_chr", _DEFAULT_RT_MOD, "chr", "core.chr"),
            "isinstance": ("py_isinstance", _DEFAULT_RT_MOD, "isinstance", "core.isinstance"),
            "range": ("py_range", _DEFAULT_RT_MOD, "range", "core.range"),
        }
        if func_name in builtin_map:
            rt_call, rt_mod, rt_sym, sem_tag = builtin_map[func_name]
            call.builtin_name = func_name
            call.lowered_kind = "BuiltinCall"
            call.runtime_call = rt_call
            call.runtime_module_id = rt_mod
            call.runtime_symbol = rt_sym
            call.runtime_call_adapter_kind = "builtin"
            call.semantic_tag = sem_tag
            # Register implicit builtin module from semantic_tag
            _SEM_TAG_TO_BUILTIN: dict[str, str] = {
                "core.print": "pytra.built_in.io_ops",
                "core.len": "pytra.built_in.sequence",
                "core.abs": "pytra.built_in.numeric_ops",
                "core.min": "pytra.built_in.numeric_ops",
                "core.max": "pytra.built_in.numeric_ops",
                "cast.str": "pytra.built_in.scalar_ops",
                "cast.int": "pytra.built_in.scalar_ops",
                "cast.float": "pytra.built_in.scalar_ops",
                "cast.bool": "pytra.built_in.scalar_ops",
                "core.ord": "pytra.built_in.scalar_ops",
                "core.chr": "pytra.built_in.scalar_ops",
                "core.isinstance": "pytra.built_in.predicates",
                "core.range": "pytra.built_in.sequence",
            }
            builtin_mod = _SEM_TAG_TO_BUILTIN.get(sem_tag, "")
            if builtin_mod != "":
                self.ctx.implicit_builtin_modules[builtin_mod] = True
        # Import symbol calls (e.g., perf_counter, Path, py_assert_stdout)
        if func_name in self.ctx.import_symbols and call.builtin_name is None:
            sym_info = self.ctx.import_symbols[func_name]
            mod_id = sym_info.get("module", "")
            if mod_id != "":
                call.runtime_module_id = mod_id
                call.runtime_symbol = func_name
                call.runtime_call_adapter_kind = "extern_delegate"
                call.resolved_runtime_call = func_name
                call.resolved_runtime_source = "import_symbol"
                # Resolve semantic tag for known modules
                if "pytra.std." in mod_id:
                    call.semantic_tag = "stdlib.fn." + func_name
                    call.resolved_runtime_source = mod_id
                elif mod_id == "pathlib":
                    call.semantic_tag = "stdlib.symbol.Path"
        # Method call: obj.method(...) → semantic_tag, runtime_owner
        # 組み込み型 (list, dict, str, set, Path) のメソッドのみアノテーション
        if isinstance(call.func, Attribute):
            attr = call.func
            method_name = attr.attr
            owner_type = _get_resolved_type(attr.value)
            owner_base = owner_type.split("[")[0] if "[" in owner_type else owner_type
            _BUILTIN_OWNER_TYPES = {"list", "dict", "str", "set", "Path", "bytearray", "bytes", "deque"}
            if owner_base in _BUILTIN_OWNER_TYPES:
                call.semantic_tag = "stdlib.method." + method_name
                call.lowered_kind = "BuiltinCall"
                call.builtin_name = method_name
                call.runtime_owner = attr.value
                if owner_base == "list":
                    call.runtime_call = "list." + method_name
                    call.runtime_module_id = "pytra.core.list"
                    call.runtime_symbol = "list." + method_name
                    call.runtime_call_adapter_kind = "builtin"
                    # list.pop は container.list.pop + yields_dynamic
                    if method_name == "pop":
                        call.semantic_tag = "container.list.pop"
                        call.yields_dynamic = True
                elif owner_base == "dict":
                    call.runtime_call = "dict." + method_name
                    call.runtime_module_id = "pytra.core.dict"
                    call.runtime_symbol = "dict." + method_name
                    call.runtime_call_adapter_kind = "builtin"
                    call.semantic_tag = "container.dict." + method_name
                elif owner_base == "str":
                    call.runtime_call = "py_" + method_name
                    call.runtime_module_id = "pytra.built_in.string_ops"
                    call.runtime_symbol = "str." + method_name
                    call.runtime_call_adapter_kind = "builtin"
                elif owner_base == "set":
                    call.runtime_call = "set." + method_name
                    call.runtime_module_id = "pytra.core.set"
                    call.runtime_symbol = "set." + method_name
                    call.runtime_call_adapter_kind = "builtin"

    def _parse_primary(self) -> Expr:
        """基本式: リテラル、名前、括弧、リスト、タプル、辞書。"""
        tok = self.peek()

        # Integer literal
        if tok.kind == "INT":
            self.advance()
            value_str = tok.value.replace("_", "")
            if value_str.startswith("0x") or value_str.startswith("0X"):
                val = int(value_str, 16)
            elif value_str.startswith("0b") or value_str.startswith("0B"):
                val = int(value_str, 2)
            elif value_str.startswith("0o") or value_str.startswith("0O"):
                val = int(value_str, 8)
            else:
                val = int(value_str)
            base = self._base(tok.start, tok.end, "int64", "value")
            return Constant(base=base, value=val)

        # Float literal
        if tok.kind == "FLOAT":
            self.advance()
            val_f = float(tok.value.replace("_", ""))
            base = self._base(tok.start, tok.end, "float64", "value")
            return Constant(base=base, value=val_f)

        # String literal
        if tok.kind == "STR":
            self.advance()
            raw = tok.value
            # Evaluate string value
            if raw.startswith('"""') or raw.startswith("'''"):
                inner = raw[3:-3]
            elif raw.startswith('"'):
                inner = raw[1:-1]
            elif raw.startswith("'"):
                inner = raw[1:-1]
            else:
                inner = raw
            # Basic escape handling
            val_s = _unescape_string(inner)
            base = self._base(tok.start, tok.end, "str", "value")
            return Constant(base=base, value=val_s)

        # Name / keyword literals
        if tok.kind == "NAME":
            if tok.value == "True":
                self.advance()
                base = self._base(tok.start, tok.end, "bool", "value")
                return Constant(base=base, value=True)
            if tok.value == "False":
                self.advance()
                base = self._base(tok.start, tok.end, "bool", "value")
                return Constant(base=base, value=False)
            if tok.value == "None":
                self.advance()
                base = self._base(tok.start, tok.end, "None", "value")
                return Constant(base=base, value=None)  # type: ignore
            self.advance()
            # Look up type from context
            resolved = self.name_types.get(tok.value, "unknown")
            # RHS reference: readonly_ref, no type_expr
            # (LHS targets are created separately via _make_name_expr)
            borrow = "readonly_ref" if resolved != "unknown" else "value"
            base = self._base(tok.start, tok.end, resolved, borrow)
            name = Name(base=base, id=tok.value)
            # RHS names do NOT get type_expr (only LHS declaration targets do)
            return name

        # Parenthesized expression or tuple
        if tok.value == "(":
            self.advance()
            if self.peek().value == ")":
                self.advance()
                # Empty tuple
                base = self._base(tok.start, self.tokens[self.pos - 1].end, "tuple[]", "value")
                return TupleExpr(base=base, elements=[])
            first = self.parse_expr()
            if self.peek().value == "for":
                # Generator expression: (expr for x in iterable)
                # Treat as listcomp for now, wrapped in parens
                gens: list[Comprehension] = []
                while self.peek().value == "for":
                    self.advance()
                    target = self._parse_comp_target()
                    self.expect("NAME", "in")
                    iter_expr = self._parse_comp_iter()
                    ifs: list[Expr] = []
                    while self.peek().value == "if":
                        self.advance()
                        ifs.append(self._parse_comp_iter())
                    gens.append(Comprehension(target=target, iter_expr=iter_expr, ifs=ifs, is_async=False))
                self.expect("OP", ")")
                end_tok = self.tokens[self.pos - 1]
                base = self._base(tok.start, end_tok.end, "unknown", "value")
                return ListComp(base=base, elt=first, generators=gens)
            if self.peek().value == ",":
                # Tuple
                elements: list[Expr] = [first]
                while self.peek().value == ",":
                    self.advance()
                    if self.peek().value == ")":
                        break
                    elements.append(self.parse_expr())
                self.expect("OP", ")")
                end_tok = self.tokens[self.pos - 1]
                # Tuple 型推論: tuple[elem_type1,elem_type2,...]
                elem_types = [_get_resolved_type(e) for e in elements]
                if all(t != "unknown" for t in elem_types):
                    tuple_type = "tuple[" + ", ".join(elem_types) + "]"
                else:
                    tuple_type = "unknown"
                base = self._base(tok.start, end_tok.end, tuple_type, "value")
                return TupleExpr(base=base, elements=elements)
            close_tok = self.expect("OP", ")")
            # 括弧付き式: span を括弧を含めた範囲に拡張
            paren_start = tok.start
            paren_end = close_tok.end
            if isinstance(first, (Name, Constant, BinOp, UnaryOp, BoolOp, Compare, Call, Attribute, Subscript, IfExp, ListExpr, TupleExpr, DictExpr, ListComp, RangeExpr)):
                first.base.source_span = self._span(paren_start, paren_end)
                first.base.repr_text = self.source_text[paren_start:paren_end]
            return first

        # List literal or comprehension
        if tok.value == "[":
            return self._parse_list_or_listcomp()

        # Dict literal
        if tok.value == "{":
            return self._parse_dict_or_set()

        raise ValueError("unexpected token in expression: " + tok.value + " at pos " + str(tok.start))

    def _parse_list_or_listcomp(self) -> Expr:
        open_tok = self.advance()  # [
        if self.peek().value == "]":
            close_tok = self.advance()
            base = self._base(open_tok.start, close_tok.end, "list[unknown]", "value")
            return ListExpr(base=base, elements=[])
        first = self.parse_expr()
        # Check for list comprehension
        if self.peek().value == "for":
            return self._parse_listcomp_tail(open_tok, first)
        # Regular list
        elements: list[Expr] = [first]
        while self.peek().value == ",":
            self.advance()
            if self.peek().value == "]":
                break
            elements.append(self.parse_expr())
        self.expect("OP", "]")
        end_tok = self.tokens[self.pos - 1]
        # Infer list element type from first element
        elem_type = "unknown"
        if len(elements) > 0:
            elem_type = _get_resolved_type(elements[0])
        list_type = "list[" + elem_type + "]" if elem_type != "unknown" else "list[unknown]"
        base = self._base(open_tok.start, end_tok.end, list_type, "value")
        return ListExpr(base=base, elements=elements)

    def _parse_listcomp_tail(self, open_tok: Token, elt: Expr) -> ListComp:
        gens: list[Comprehension] = []
        while self.peek().value == "for":
            self.advance()  # consume 'for'
            # target は単純な Name または Tuple（'in' で止める必要がある）
            target = self._parse_comp_target()
            self.expect("NAME", "in")
            # iter_expr は 'if', 'for', ']' で止める
            iter_expr = self._parse_comp_iter()
            # Comprehension target: golden では型推論しない (unknown/value のまま)
            ifs: list[Expr] = []
            while self.peek().value == "if":
                self.advance()
                ifs.append(self._parse_comp_iter())
            gens.append(Comprehension(target=target, iter_expr=iter_expr, ifs=ifs, is_async=False))
        self.expect("OP", "]")
        end_tok = self.tokens[self.pos - 1]
        # ListComp resolved_type: list[elt_type] (elt が推論済みの場合のみ)
        elt_type = _get_resolved_type(elt)
        comp_type = "list[" + elt_type + "]" if elt_type != "unknown" else "unknown"
        base = self._base(open_tok.start, end_tok.end, comp_type, "value")
        return ListComp(base=base, elt=elt, generators=gens)

    def _parse_comp_target(self) -> Expr:
        """comprehension の target をパース。'in' キーワードで止める。"""
        tok = self.peek()
        if tok.kind == "NAME" and tok.value != "in":
            self.advance()
            base = self._base(tok.start, tok.end, "unknown", "value")
            first = Name(base=base, id=tok.value)
            # Check for tuple target: x, y
            if self.peek().value == ",":
                elements: list[Expr] = [first]
                while self.peek().value == ",":
                    self.advance()
                    if self.peek().value == "in":
                        break
                    next_tok = self.advance()
                    nbase = self._base(next_tok.start, next_tok.end, "unknown", "value")
                    elements.append(Name(base=nbase, id=next_tok.value))
                tbase = self._base(tok.start, self.tokens[self.pos - 1].end, "unknown", "value")
                return TupleExpr(base=tbase, elements=elements)
            return first
        return self.parse_expr()

    def _parse_comp_iter(self) -> Expr:
        """comprehension の iter/if 式をパース。'for', 'if', ']', '}', ')' で止める。"""
        # 通常の式パースを行うが、トップレベルの 'for', 'if' で止める
        # これは _parse_ternary の 'if' と衝突するため、or レベルまでパースする
        return self._parse_or()

    def _parse_subscript_index(self) -> Expr:
        """subscript の index をパース。`:` が来たら SliceExpr を生成。"""
        # Check for initial `:` (e.g., a[:3])
        if self.peek().value == ":":
            return self._parse_slice(None)
        first = self.parse_expr()
        # Check for slice
        if self.peek().value == ":":
            return self._parse_slice(first)
        return first

    def _parse_slice(self, lower: Optional[Expr]) -> SliceExpr:
        """slice 式をパース。`:` を消費した状態で呼ばれる。"""
        self.advance()  # consume ':'
        upper: Optional[Expr] = None
        step: Optional[Expr] = None
        if self.peek().value != "]" and self.peek().value != ":":
            upper = self.parse_expr()
        if self.peek().value == ":":
            self.advance()
            if self.peek().value != "]":
                step = self.parse_expr()
        return SliceExpr(lower=lower, upper=upper, step=step)

    def _parse_dict_or_set(self) -> Expr:
        """dict リテラル、set リテラル、dict/set comprehension をパース。"""
        open_tok = self.advance()  # {
        if self.peek().value == "}":
            close_tok = self.advance()
            base = self._base(open_tok.start, close_tok.end, "dict[unknown, unknown]", "value")
            return DictExpr(base=base, keys=[], dict_values=[])
        first = self.parse_expr()
        # Dict comprehension: {k: v for ...}
        if self.peek().value == ":":
            self.advance()
            first_val = self.parse_expr()
            if self.peek().value == "for":
                # dict comprehension — 簡易実装: 式として扱う
                # TODO: proper DictComp node
                while self.peek().value != "}":
                    self.advance()
                self.expect("OP", "}")
                end_tok = self.tokens[self.pos - 1]
                base = self._base(open_tok.start, end_tok.end, "unknown", "value")
                return DictExpr(base=base, keys=[first], dict_values=[first_val], entries=[DictEntry(key=first, value=first_val)])
            # Regular dict
            keys: list[Expr] = [first]
            values: list[Expr] = [first_val]
            entries: list[DictEntry] = [DictEntry(key=first, value=first_val)]
            while self.peek().value == ",":
                self.advance()
                if self.peek().value == "}":
                    break
                k = self.parse_expr()
                self.expect("OP", ":")
                v = self.parse_expr()
                keys.append(k)
                values.append(v)
                entries.append(DictEntry(key=k, value=v))
            self.expect("OP", "}")
            end_tok = self.tokens[self.pos - 1]
            # Infer dict type from first key/value
            key_type = _get_resolved_type(keys[0]) if len(keys) > 0 else "unknown"
            val_type = _get_resolved_type(values[0]) if len(values) > 0 else "unknown"
            dict_type = "dict[" + key_type + "," + val_type + "]" if key_type != "unknown" and val_type != "unknown" else "unknown"
            base = self._base(open_tok.start, end_tok.end, dict_type, "value")
            return DictExpr(base=base, keys=keys, dict_values=values, entries=entries)
        # Set literal or set comprehension
        if self.peek().value == "for":
            # set comprehension — skip for now
            while self.peek().value != "}":
                self.advance()
            self.expect("OP", "}")
            end_tok = self.tokens[self.pos - 1]
            base = self._base(open_tok.start, end_tok.end, "unknown", "value")
            return ListExpr(base=base, elements=[first])  # TODO: SetExpr
        # Set literal: {a, b, c}
        elements: list[Expr] = [first]
        while self.peek().value == ",":
            self.advance()
            if self.peek().value == "}":
                break
            elements.append(self.parse_expr())
        self.expect("OP", "}")
        end_tok = self.tokens[self.pos - 1]
        base = self._base(open_tok.start, end_tok.end, "unknown", "value")
        return ListExpr(base=base, elements=elements)  # TODO: SetExpr


# ---------------------------------------------------------------------------
# Expression helpers
# ---------------------------------------------------------------------------

def _get_resolved_type(e: Expr) -> str:
    if isinstance(e, (Name, Constant, BinOp, UnaryOp, BoolOp, Compare, Call, Attribute, Subscript, IfExp, ListExpr, TupleExpr, DictExpr, ListComp, RangeExpr)):
        return e.base.resolved_type
    if isinstance(e, SliceExpr):
        return "slice"
    return "unknown"


# ローカル位置追跡: ExprParser 内で _base() に渡す local_start/local_end を
# 子ノードから取得するためのユーティリティ。
# ExprBase.source_span.col = line_col_offset + local_start なので、
# local_start = col - line_col_offset で逆算する。

def _expr_col(e: Expr) -> int:
    """式ノードの source_span.col (絶対位置)。"""
    if isinstance(e, (Name, Constant, BinOp, UnaryOp, BoolOp, Compare, Call, Attribute, Subscript, IfExp, ListExpr, TupleExpr, DictExpr, ListComp, RangeExpr)):
        sp = e.base.source_span
        if sp.col is not None:
            return sp.col
    return 0


def _expr_end_col(e: Expr) -> int:
    """式ノードの source_span.end_col (絶対位置)。"""
    if isinstance(e, (Name, Constant, BinOp, UnaryOp, BoolOp, Compare, Call, Attribute, Subscript, IfExp, ListExpr, TupleExpr, DictExpr, ListComp, RangeExpr)):
        sp = e.base.source_span
        if sp.end_col is not None:
            return sp.end_col
    return 0


def _get_func_name(func: Expr) -> str:
    if isinstance(func, Name):
        return func.id
    if isinstance(func, Attribute):
        return func.attr
    return ""


def _compute_binop_casts(left_type: str, right_type: str, op: str) -> list[Cast]:
    """二項演算の数値プロモーションキャストを計算する。"""
    casts: list[Cast] = []
    # Div: int64/int64 → float64 (両辺をプロモーション)
    if op == "Div":
        if left_type == "int64":
            casts.append(Cast(operand="left", from_type="int64", to_type="float64", reason="numeric_promotion"))
        if right_type == "int64":
            casts.append(Cast(operand="right", from_type="int64", to_type="float64", reason="numeric_promotion"))
    # Pow: int64 → float64
    elif op == "Pow":
        if left_type == "int64":
            casts.append(Cast(operand="left", from_type="int64", to_type="float64", reason="numeric_promotion"))
        if right_type == "int64":
            casts.append(Cast(operand="right", from_type="int64", to_type="float64", reason="numeric_promotion"))
    # Mixed int64/float64: promote int64 side
    elif left_type == "int64" and right_type == "float64":
        casts.append(Cast(operand="left", from_type="int64", to_type="float64", reason="numeric_promotion"))
    elif left_type == "float64" and right_type == "int64":
        casts.append(Cast(operand="right", from_type="int64", to_type="float64", reason="numeric_promotion"))
    return casts


_KNOWN_NUMERIC_TYPES = {"int64", "float64", "bool"}


def _is_known_numeric(t: str) -> bool:
    return t in _KNOWN_NUMERIC_TYPES


def _binop_result_type(left_type: str, right_type: str, op: str) -> str:
    """二項演算の結果型を推論する。"""
    if op == "Div":
        if _is_known_numeric(left_type) and _is_known_numeric(right_type):
            return "float64"
        return "unknown"
    if op == "Pow":
        if _is_known_numeric(left_type) and _is_known_numeric(right_type):
            return "float64"
        return "unknown"
    if op == "Add" and (left_type == "str" or right_type == "str"):
        return "str"
    if left_type == "float64" or right_type == "float64":
        if _is_known_numeric(left_type) and _is_known_numeric(right_type):
            return "float64"
    if left_type == "int64" and _is_known_numeric(right_type):
        return "int64"
    if right_type == "int64" and _is_known_numeric(left_type):
        return "int64"
    if left_type == "unknown" or right_type == "unknown":
        return "unknown"
    # Both same known type
    if left_type == right_type and _is_known_numeric(left_type):
        return left_type
    # Non-standard type → unknown
    if not _is_known_numeric(left_type) or not _is_known_numeric(right_type):
        return "unknown"
    return left_type


def _unescape_string(s: str) -> str:
    """基本的なエスケープシーケンスを処理する。"""
    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        if s[i] == "\\" and i + 1 < n:
            ch = s[i + 1]
            if ch == "n":
                out.append("\n")
            elif ch == "t":
                out.append("\t")
            elif ch == "r":
                out.append("\r")
            elif ch == "\\":
                out.append("\\")
            elif ch == "'":
                out.append("'")
            elif ch == '"':
                out.append('"')
            elif ch == "0":
                out.append("\0")
            else:
                out.append("\\")
                out.append(ch)
            i += 2
        else:
            out.append(s[i])
            i += 1
    result = ""
    for part in out:
        result = result + part
    return result


# ---------------------------------------------------------------------------
# Module-level parser (entry point)
# ---------------------------------------------------------------------------

def parse_python_source(source: str, filename: str) -> Module:
    """Python ソースを EAST1 Module に変換する。"""
    lines = source.splitlines()
    ctx = ParseContext(
        filename=filename,
        lines=lines,
        type_aliases=default_type_aliases(),
        fn_returns={},
        class_method_returns={},
        class_bases={},
        import_symbols={},
        import_modules={},
        import_bindings=[],
        qualified_symbol_refs=[],
        implicit_builtin_modules={},
        class_names={},
    )

    # Phase 1: Pre-scan
    _prescan(ctx, lines)

    # Phase 2: Parse body
    body_items: list[Stmt] = []
    main_guard_body: list[Stmt] = []
    _parse_module_body(ctx, lines, body_items, main_guard_body)

    # Phase 3: Post-processing
    renamed_symbols: dict[str, str] = {}
    _postprocess(ctx, body_items, renamed_symbols)

    # Build meta
    meta = _build_meta(ctx)

    return Module(
        source_path=filename,
        source_span=NULL_SPAN,
        body=body_items,
        main_guard_body=main_guard_body,
        meta=meta,
        renamed_symbols=renamed_symbols,
        east_stage=1,
    )


def _prescan(ctx: ParseContext, lines: list[str]) -> None:
    """Phase 1: 関数の戻り値型やクラス情報を収集する。"""
    for ln_no, ln in enumerate(lines, start=1):
        s = _strip_inline_comment(ln.strip())
        if s == "":
            continue

        # from X import Y
        mod, names_text = _parse_from_import(s)
        if mod != "" and names_text != "":
            # Register import symbols
            for part in names_text.split(","):
                part = part.strip()
                if part == "" or part == "*":
                    continue
                asname = ""
                name = part
                if " as " in part:
                    split = part.split(" as ")
                    name = split[0].strip()
                    asname = split[1].strip()
                local = asname if asname != "" else name
                ctx.import_symbols[local] = {"module": mod, "name": name}
            # Type alias from typing
            if mod == "typing":
                for part in names_text.split(","):
                    name = part.strip()
                    if name == "List":
                        ctx.type_aliases["List"] = "list"
                    elif name == "Dict":
                        ctx.type_aliases["Dict"] = "dict"
                    elif name == "Tuple":
                        ctx.type_aliases["Tuple"] = "tuple"
                    elif name == "Set":
                        ctx.type_aliases["Set"] = "set"
                    elif name == "Optional":
                        ctx.type_aliases["Optional"] = "Optional"
            continue

        # def name(...) -> RetType:
        fn_name, _, ret_ann = _parse_def_header(s)
        if fn_name != "":
            if ret_ann != "":
                ctx.fn_returns[fn_name] = _resolve_type(ret_ann, ctx)
            else:
                # 戻り値注釈なし → None がデフォルト
                ctx.fn_returns[fn_name] = "None"
            continue

        # class Name:
        cls_name = _parse_class_name(s)
        if cls_name != "":
            ctx.class_names[cls_name] = True
            continue


def _parse_module_body(
    ctx: ParseContext,
    lines: list[str],
    body_items: list[Stmt],
    main_guard_body: list[Stmt],
) -> None:
    """Phase 2: モジュール本体をパースする。"""
    ln_no = 0
    total = len(lines)
    pending_trivia: list[TriviaNode] = []
    pending_comments: list[str] = []
    leading_file_trivia_done = False
    pending_dataclass = False
    skip_next_blanks = False  # import/def/class 直後の空行を蓄積しないためのフラグ

    while ln_no < total:
        ln = lines[ln_no]
        s = ln.strip()
        indent = len(ln) - len(ln.lstrip(" ")) if s != "" else 0

        # Blank line
        if s == "":
            # ファイル冒頭コメントが既に蓄積 + import 直後でない場合のみ蓄積
            if (len(pending_comments) > 0 or leading_file_trivia_done) and not skip_next_blanks:
                pending_trivia.append(TriviaBlank(count=1))
            ln_no += 1
            continue

        # Comment line
        if s.startswith("#"):
            text = s[1:].lstrip() if len(s) > 1 else ""
            pending_trivia.append(TriviaComment(text=text))
            pending_comments.append(text)
            ln_no += 1
            continue

        leading_file_trivia_done = True

        # Only process top-level (indent == 0)
        if indent != 0:
            ln_no += 1
            continue

        s_clean = _strip_inline_comment(s)

        # Decorator at module level
        if s_clean.startswith("@"):
            if s_clean == "@dataclass" or s_clean.startswith("@dataclass("):
                pending_dataclass = True
            ln_no += 1
            continue

        # Module-level string literal (docstring)
        if (s_clean.startswith('"""') or s_clean.startswith("'''") or
            (s_clean.startswith('"') and not s_clean.startswith('"""')) or
            (s_clean.startswith("'") and not s_clean.startswith("'''"))):
            # Check if it's a standalone string (expression statement)
            expr = _parse_expr_text(ctx, s_clean, ln_no + 1, indent, {})
            span = make_span(ln_no + 1, indent, ln_no + 1, indent + len(s_clean))
            body_items.append(ExprStmt(source_span=span, value=expr))
            ln_no += 1
            pending_trivia = []
            pending_comments = []
            continue

        # Import: from X import Y
        mod, names_text = _parse_from_import(s_clean)
        if mod != "" and names_text != "":
            aliases: list[ImportAlias] = []
            for part in names_text.split(","):
                part = part.strip()
                if part == "":
                    continue
                asname: Optional[str] = None
                name = part
                if " as " in part:
                    split = part.split(" as ")
                    name = split[0].strip()
                    asname = split[1].strip()
                aliases.append(ImportAlias(name=name, asname=asname))
            # Skip typing / __future__ / dataclasses imports
            if mod == "typing" or mod == "__future__" or mod == "dataclasses":
                ln_no += 1
                skip_next_blanks = True
                continue
            span = make_span(ln_no + 1, 0, ln_no + 1, len(ln.rstrip()))
            stmt = ImportFrom(source_span=span, module=mod, names=aliases, level=0)
            body_items.append(stmt)
            # Build import binding
            for alias in aliases:
                local = alias.asname if alias.asname is not None else alias.name
                binding: dict[str, JsonVal] = {
                    "module_id": mod,
                    "export_name": alias.name,
                    "local_name": local,
                    "binding_kind": "symbol",
                    "source_file": ctx.filename,
                    "source_line": ln_no + 1,
                }
                # host_only for pathlib etc.
                if mod == "pathlib" or mod == "os" or mod == "sys":
                    binding["host_only"] = True
                ctx.import_bindings.append(binding)
                ctx.qualified_symbol_refs.append({
                    "module_id": mod,
                    "symbol": alias.name,
                    "local_name": local,
                })
            ln_no += 1
            # import 後の空行は trivia に蓄積しない
            skip_next_blanks = True
            continue

        # import MOD (not from)
        imp_match = re.match(r"^import\s+(.+)$", s_clean)
        if imp_match is not None:
            imp_names_text = re.strip_group(imp_match, 1)
            imp_aliases: list[ImportAlias] = []
            for part in imp_names_text.split(","):
                part = part.strip()
                if part == "":
                    continue
                asname_i: Optional[str] = None
                name_i = part
                if " as " in part:
                    split_i = part.split(" as ")
                    name_i = split_i[0].strip()
                    asname_i = split_i[1].strip()
                imp_aliases.append(ImportAlias(name=name_i, asname=asname_i))
                # Register module import
                local_i = asname_i if asname_i is not None else name_i
                ctx.import_modules[local_i] = name_i
            span = make_span(ln_no + 1, 0, ln_no + 1, len(ln.rstrip()))
            body_items.append(Import(source_span=span, names=imp_aliases))
            # Build import binding
            for alias in imp_aliases:
                local = alias.asname if alias.asname is not None else alias.name
                binding: dict[str, JsonVal] = {
                    "module_id": alias.name,
                    "export_name": "",
                    "local_name": local,
                    "binding_kind": "module",
                    "source_file": ctx.filename,
                    "source_line": ln_no + 1,
                }
                ctx.import_bindings.append(binding)
            ln_no += 1
            skip_next_blanks = True
            continue

        # 非import文に到達
        skip_next_blanks = False

        # Main guard: if __name__ == "__main__":
        if _parse_main_guard(s_clean):
            ln_no += 1
            guard_lines: list[str] = []
            while ln_no < total:
                gl = lines[ln_no]
                gs = gl.strip()
                gi = len(gl) - len(gl.lstrip(" ")) if gs != "" else 0
                if gs != "" and gi == 0:
                    break
                guard_lines.append(gl)
                ln_no += 1
            # Parse main guard body
            main_guard_body.extend(
                _parse_block_lines(ctx, guard_lines, {}, "main")
            )
            pending_trivia = []
            pending_comments = []
            continue

        # Function def
        fn_name = _parse_def_name(s_clean)
        if fn_name != "":
            fn_stmt, ln_no = _parse_function_def(ctx, lines, ln_no, fn_name, pending_trivia, pending_comments)
            body_items.append(fn_stmt)
            pending_trivia = []
            pending_comments = []
            skip_next_blanks = True
            continue

        # Class def
        cls_name = _parse_class_name(s_clean)
        if cls_name != "":
            cls_stmt, ln_no = _parse_class_def(ctx, lines, ln_no, cls_name, pending_trivia, pending_comments, is_dataclass=pending_dataclass)
            pending_dataclass = False
            body_items.append(cls_stmt)
            pending_trivia = []
            pending_comments = []
            skip_next_blanks = True
            continue

        # Skip other top-level statements for now
        ln_no += 1
        pending_trivia = []
        pending_comments = []


def _collect_block(lines: list[str], start_ln: int, parent_indent: int) -> tuple[list[str], int]:
    """インデントされたブロックの行を収集する。"""
    block_lines: list[str] = []
    ln_no = start_ln
    total = len(lines)
    while ln_no < total:
        ln = lines[ln_no]
        s = ln.strip()
        if s == "" or s.startswith("#"):
            block_lines.append(ln)
            ln_no += 1
            continue
        indent = len(ln) - len(ln.lstrip(" "))
        if indent <= parent_indent:
            break
        block_lines.append(ln)
        ln_no += 1
    return block_lines, ln_no


def _parse_function_def(
    ctx: ParseContext,
    lines: list[str],
    start_ln: int,
    fn_name: str,
    trivia: list[TriviaNode],
    comments: list[str],
    class_name: str = "",
    parent_indent: int = 0,
) -> tuple[FunctionDef, int]:
    """関数定義をパースする。"""
    header_line = lines[start_ln]
    header = _strip_inline_comment(header_line.strip())
    header_indent = len(header_line) - len(header_line.lstrip(" "))

    # Parse signature via pytra.std.re
    _, args_text, return_ann = _parse_def_header(header)
    return_type = _resolve_type(return_ann, ctx) if return_ann != "" else "None"

    # Parse arguments
    arg_order: list[str] = []
    arg_types: dict[str, str] = {}
    arg_defaults: dict[str, JsonVal] = {}
    arg_index: dict[str, int] = {}
    arg_type_exprs: dict[str, dict[str, JsonVal]] = {}

    name_types_empty: dict[str, str] = {}
    if args_text.strip() != "" and (args_text.strip() != "self" or class_name != ""):
        idx = 0
        for param in _split_type_args_outer(args_text):
            param = param.strip()
            if param == "" or param == "*":
                continue
            # self パラメータ: クラスメソッドなら class_name を型として追加
            if param == "self":
                if class_name != "":
                    arg_order.append("self")
                    arg_types["self"] = class_name
                    arg_index["self"] = idx
                    idx += 1
                continue
            # Handle default values
            default_part = ""
            if "=" in param:
                eq_pos = param.find("=")
                default_part = param[eq_pos + 1:].strip()
                param = param[:eq_pos].strip()
            # Handle type annotation
            if ":" in param:
                colon_pos = param.find(":")
                pname = param[:colon_pos].strip()
                ptype_ann = param[colon_pos + 1:].strip()
                ptype = _resolve_type(ptype_ann, ctx)
            else:
                pname = param
                ptype = "unknown"
            arg_order.append(pname)
            arg_types[pname] = ptype
            arg_index[pname] = idx
            # Default value
            if default_part != "":
                default_col = _find_expr_col(ctx, default_part, start_ln + 1, 0)
                default_expr = _parse_expr_text(ctx, default_part, start_ln + 1, default_col, name_types_empty)
                arg_defaults[pname] = expr_to_jv(default_expr)
            if ptype != "unknown":
                arg_type_exprs[pname] = _make_type_expr(ptype, ctx).to_jv()
            idx += 1

    # Collect body
    block_lines, end_ln = _collect_block(lines, start_ln + 1, header_indent)

    # Parse body with arg types in scope
    name_types: dict[str, str] = dict(arg_types)
    body_stmts = _parse_block_lines(ctx, block_lines, name_types, fn_name)

    # Compute arg_usage
    arg_usage = _compute_arg_usage(arg_order, body_stmts)

    # Extract docstring
    docstring = _extract_docstring(block_lines)

    # Compute end span: 最終非空行の絶対行番号と行末位置
    end_lineno = start_ln + 1
    end_col = 0
    if len(block_lines) > 0:
        for bl in reversed(block_lines):
            if bl.strip() != "":
                end_lineno = _find_abs_line(lines, bl, start_ln)
                end_col = len(bl.rstrip())
                break

    span = make_span(start_ln + 1, header_indent, end_lineno, end_col)

    fd = FunctionDef(
        source_span=span,
        name=fn_name,
        original_name=fn_name,
        arg_types=arg_types,
        arg_order=arg_order,
        arg_defaults=arg_defaults,
        arg_index=arg_index,
        return_type=return_type,
        arg_usage=arg_usage,
        renamed_symbols={},
        docstring=docstring,
        body=body_stmts,
        is_generator=0,
        yield_value_type="unknown",
    )

    # Optional fields: クラスメソッドとトップレベル関数で異なる
    if class_name != "":
        # クラスメソッド: decorators のみ出力。arg_type_exprs/return_type_expr/leading は出力しない
        fd.decorators = []
    else:
        # トップレベル関数
        if len(arg_type_exprs) > 0 or len(arg_order) == 0:
            fd.arg_type_exprs = arg_type_exprs
        fd.return_type_expr = _make_type_expr(return_type, ctx)
        fd.leading_comments = list(comments)
        fd.leading_trivia = list(trivia)

    return fd, end_ln


def _parse_class_def(
    ctx: ParseContext,
    lines: list[str],
    start_ln: int,
    cls_name: str,
    trivia: list[TriviaNode],
    comments: list[str],
    is_dataclass: bool = False,
) -> tuple[ClassDef, int]:
    """クラス定義をパースする。"""
    # Check for base class: class Name(Base):
    header = _strip_inline_comment(lines[start_ln].strip())
    base_name: Optional[str] = None
    paren_pos = header.find("(")
    if paren_pos > 0:
        paren_end = header.find(")")
        if paren_end > paren_pos:
            base_name = header[paren_pos + 1:paren_end].strip()
            if base_name == "":
                base_name = None
    block_lines, end_ln = _collect_block(lines, start_ln + 1, 0)
    name_types: dict[str, str] = {}
    body_stmts = _parse_block_lines(ctx, block_lines, name_types, cls_name)

    # Collect field types from annotated assignments
    field_types: dict[str, str] = {}
    for stmt in body_stmts:
        if isinstance(stmt, AnnAssign):
            if isinstance(stmt.target, Name):
                field_types[stmt.target.id] = stmt.annotation

    # ClassDef span: end_lineno = _collect_block が返した end_ln (次のトップレベル行の前)
    span = make_span(start_ln + 1, 0, end_ln, 0)

    cd = ClassDef(
        source_span=span,
        name=cls_name,
        original_name=cls_name,
        base=base_name,
        body=body_stmts,
        dataclass_flag=is_dataclass,
        field_types=field_types,
        class_storage_hint=_infer_class_storage_hint(is_dataclass, base_name, field_types, body_stmts),
    )
    # ClassDef: leading を出力 (空でも最初のクラスは出力)
    cd.leading_comments = list(comments)
    cd.leading_trivia = list(trivia)

    return cd, end_ln


def _parse_try_stmt(
    ctx: ParseContext,
    block_lines: list[str],
    start_i: int,
    parent_indent: int,
    name_types: dict[str, str],
    abs_ln: int,
    indent: int,
) -> tuple[Try, int]:
    """try/except/finally 文をパースする。"""
    # Collect try body
    try_lines, next_i = _collect_sub_block(block_lines, start_i + 1, indent)
    try_body = _parse_block_lines(ctx, try_lines, name_types, "try")

    handlers: list[ExceptHandler] = []
    orelse: list[Stmt] = []
    finalbody: list[Stmt] = []

    # Parse except/else/finally clauses
    while next_i < len(block_lines):
        ln = block_lines[next_i]
        s = ln.strip()
        ln_indent = len(ln) - len(ln.lstrip(" ")) if s != "" else 0
        if s == "" or s.startswith("#"):
            next_i += 1
            continue
        if ln_indent != indent:
            break

        handler_abs_ln = _find_abs_line(ctx.lines, ln, abs_ln)

        if s.startswith("except"):
            # Parse except clause
            m_exc_as = re.match(r"^except\s+(.+?)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$", s)
            m_exc = re.match(r"^except\s+(.+?)\s*:\s*$", s)
            exc_type: Optional[str] = None
            exc_name: Optional[str] = None
            if m_exc_as is not None:
                exc_type = re.strip_group(m_exc_as, 1)
                exc_name = re.strip_group(m_exc_as, 2)
            elif m_exc is not None:
                exc_type = re.strip_group(m_exc, 1)
            elif s == "except:" or s.startswith("except:"):
                pass  # bare except
            handler_lines, next_i = _collect_sub_block(block_lines, next_i + 1, indent)
            handler_body = _parse_block_lines(ctx, handler_lines, name_types, "except")
            span = make_span(handler_abs_ln, indent, handler_abs_ln, indent + len(s))
            handlers.append(ExceptHandler(
                exc_type=exc_type,
                name=exc_name,
                body=handler_body,
                source_span=span,
            ))
            continue

        if s.startswith("else:") or s == "else:":
            else_lines, next_i = _collect_sub_block(block_lines, next_i + 1, indent)
            orelse = _parse_block_lines(ctx, else_lines, name_types, "else")
            continue

        if s.startswith("finally:") or s == "finally:":
            finally_lines, next_i = _collect_sub_block(block_lines, next_i + 1, indent)
            finalbody = _parse_block_lines(ctx, finally_lines, name_types, "finally")
            continue

        break

    # Determine end span
    end_ln = abs_ln
    end_col = indent + 4
    if len(finalbody) > 0:
        last = finalbody[-1]
        if hasattr(last, 'source_span') and last.source_span.end_lineno is not None:
            end_ln = last.source_span.end_lineno
            end_col = last.source_span.end_col if last.source_span.end_col is not None else 0
    elif len(handlers) > 0:
        last_h = handlers[-1]
        if len(last_h.body) > 0:
            last = last_h.body[-1]
            if hasattr(last, 'source_span') and last.source_span.end_lineno is not None:
                end_ln = last.source_span.end_lineno
                end_col = last.source_span.end_col if last.source_span.end_col is not None else 0

    span = make_span(abs_ln, indent, end_ln, end_col)
    return Try(
        source_span=span,
        body=try_body,
        handlers=handlers,
        orelse=orelse,
        finalbody=finalbody,
    ), next_i


def _infer_class_storage_hint(is_dataclass: bool, base: Optional[str], field_types: dict[str, str], body: list[Stmt]) -> str:
    """class_storage_hint を推論する (golden 準拠)。"""
    # base がある → ref
    if base is not None and base != "":
        return "ref"
    # __init__ メソッドがある → ref (instance state がある)
    has_init = False
    has_instance_fields = len(field_types) > 0
    for stmt in body:
        if isinstance(stmt, FunctionDef) and stmt.name == "__init__":
            has_init = True
    if has_init or has_instance_fields:
        return "ref"
    # dataclass with fields → ref (not value, golden shows ref for Point99)
    if is_dataclass:
        return "ref"
    # 空のクラスやメソッドのみ → value
    return "value"


def _merge_logical_lines(lines: list[str]) -> list[str]:
    """未閉じ括弧や行末バックスラッシュで物理行を論理行にマージする。"""
    merged: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        s = ln.rstrip()
        # Count bracket depth
        depth = 0
        in_str = ""
        for ch in s:
            if in_str != "":
                if ch == "\\" and len(in_str) == 1:
                    continue  # skip escaped char (simplified)
                if ch == in_str[0]:
                    in_str = ""
                continue
            if ch == '"' or ch == "'":
                in_str = ch
            elif ch == "(" or ch == "[" or ch == "{":
                depth += 1
            elif ch == ")" or ch == "]" or ch == "}":
                depth -= 1
        explicit_cont = s.endswith("\\")
        if depth > 0 or explicit_cont:
            # Merge with next lines until balanced
            acc = _strip_inline_comment(s).rstrip()
            if explicit_cont and acc.endswith("\\"):
                acc = acc[:-1].rstrip()
            i += 1
            while i < n and (depth > 0 or explicit_cont):
                next_ln = lines[i]
                next_s = next_ln.strip()
                for ch in next_s:
                    if in_str != "":
                        if ch == in_str[0]:
                            in_str = ""
                        continue
                    if ch == '"' or ch == "'":
                        in_str = ch
                    elif ch == "(" or ch == "[" or ch == "{":
                        depth += 1
                    elif ch == ")" or ch == "]" or ch == "}":
                        depth -= 1
                explicit_cont = next_s.rstrip().endswith("\\")
                next_clean = _strip_inline_comment(next_s).strip()
                if explicit_cont and next_clean.endswith("\\"):
                    next_clean = next_clean[:-1].rstrip()
                acc = acc + " " + next_clean
                i += 1
                if depth <= 0 and not explicit_cont:
                    break
            # Preserve original indentation
            indent = len(ln) - len(ln.lstrip(" "))
            merged.append(" " * indent + acc.lstrip())
        else:
            merged.append(ln)
            i += 1
    return merged


def _split_type_args_outer(text: str) -> list[str]:
    """トップレベルのカンマで分割（括弧ネストを考慮）。"""
    args: list[str] = []
    depth = 0
    current = ""
    for ch in text:
        if ch == "(" or ch == "[" or ch == "{":
            depth += 1
            current = current + ch
        elif ch == ")" or ch == "]" or ch == "}":
            depth -= 1
            current = current + ch
        elif ch == "," and depth == 0:
            args.append(current)
            current = ""
        else:
            current = current + ch
    if current.strip() != "":
        args.append(current)
    return args


# ---------------------------------------------------------------------------
# Block-level statement parser
# ---------------------------------------------------------------------------

def _parse_block_lines(
    ctx: ParseContext,
    block_lines: list[str],
    name_types: dict[str, str],
    scope_label: str,
) -> list[Stmt]:
    """インデントされたブロック内の文をパースする。"""
    block_lines = _merge_logical_lines(block_lines)
    stmts: list[Stmt] = []
    i = 0
    total = len(block_lines)
    last_abs_ln = 0  # hint for _find_abs_line
    pending_trivia: list[TriviaNode] = []
    pending_comments: list[str] = []

    # Determine block base indent
    base_indent = 0
    for bl in block_lines:
        s = bl.strip()
        if s != "" and not s.startswith("#"):
            base_indent = len(bl) - len(bl.lstrip(" "))
            break

    while i < total:
        ln = block_lines[i]
        s = ln.strip()
        indent = len(ln) - len(ln.lstrip(" ")) if s != "" else 0

        if s == "":
            pending_trivia.append(TriviaBlank(count=1))
            i += 1
            continue

        if s.startswith("#"):
            text = s[1:].lstrip() if len(s) > 1 else ""
            pending_trivia.append(TriviaComment(text=text))
            pending_comments.append(text)
            i += 1
            continue

        s_clean = _strip_inline_comment(s)

        # Decorator: @name
        if s_clean.startswith("@"):
            # Accumulate decorator, will be attached to next def/class
            # For now just skip (decorator info tracked separately)
            i += 1
            continue

        # Calculate absolute line number
        abs_ln = _find_abs_line(ctx.lines, ln, last_abs_ln)
        last_abs_ln = abs_ln

        # return statement
        if s_clean.startswith("return "):
            expr_text = s_clean[7:].strip()
            expr_col = _find_expr_col(ctx, expr_text, abs_ln, indent + 7)
            expr = _parse_expr_text(ctx, expr_text, abs_ln, expr_col, name_types)
            span = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
            ret_stmt = Return(source_span=span, value=expr)
            if len(pending_trivia) > 0:
                ret_stmt.leading_trivia = list(pending_trivia)
            stmts.append(ret_stmt)
            i += 1
            pending_trivia = []
            pending_comments = []
            continue

        # pass
        if s_clean == "pass":
            span = make_span(abs_ln, 0, abs_ln, indent + 4)
            stmts.append(Pass(source_span=span))
            i += 1
            pending_trivia = []
            pending_comments = []
            continue

        # raise
        if s_clean.startswith("raise "):
            expr_text = s_clean[6:].strip()
            expr = _parse_expr_text(ctx, expr_text, abs_ln, _find_expr_col(ctx, expr_text, abs_ln, indent + 6), name_types)
            span = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
            stmts.append(Raise(source_span=span, exc=expr, cause=None))
            i += 1
            pending_trivia = []
            pending_comments = []
            continue

        # try/except/finally
        if s_clean == "try:" or s_clean.startswith("try:"):
            try_stmt, i = _parse_try_stmt(ctx, block_lines, i, base_indent, name_types, abs_ln, indent)
            stmts.append(try_stmt)
            pending_trivia = []
            pending_comments = []
            continue

        # for ... in range(...)  or  for ... in ...:
        if s_clean.startswith("for "):
            for_stmt, i = _parse_for_stmt(ctx, block_lines, i, base_indent, name_types, pending_trivia, pending_comments)
            stmts.append(for_stmt)
            pending_trivia = []
            pending_comments = []
            continue

        # while ...:
        if s_clean.startswith("while "):
            while_stmt, i = _parse_while_stmt(ctx, block_lines, i, base_indent, name_types, pending_trivia, pending_comments)
            stmts.append(while_stmt)
            pending_trivia = []
            pending_comments = []
            continue

        # def ...: (nested function / class method)
        fn_name_block = _parse_def_name(s_clean)
        if fn_name_block != "":
            # scope_label がクラス名ならクラスメソッドとして self の型を設定
            block_class_name = scope_label if scope_label in ctx.class_names else ""
            fn_stmt, fn_end_ln = _parse_function_def(ctx, ctx.lines, abs_ln - 1, fn_name_block, pending_trivia, pending_comments, class_name=block_class_name, parent_indent=indent)
            stmts.append(fn_stmt)
            # Skip block_lines that were consumed by _parse_function_def
            # fn_end_ln is 0-based file line index. Advance i past those lines.
            i += 1  # skip the def line itself
            while i < total:
                bl_s = block_lines[i].strip()
                if bl_s != "" and not bl_s.startswith("#"):
                    bl_indent = len(block_lines[i]) - len(block_lines[i].lstrip(" "))
                    if bl_indent <= indent:
                        break
                i += 1
            pending_trivia = []
            pending_comments = []
            continue

        # if ...:
        if s_clean.startswith("if "):
            if_stmt, i = _parse_if_stmt(ctx, block_lines, i, base_indent, name_types, pending_trivia, pending_comments)
            stmts.append(if_stmt)
            pending_trivia = []
            pending_comments = []
            continue

        # Annotated assignment: x: Type = value
        var_name, type_ann, value_text = _parse_ann_assign(s_clean)
        if var_name != "":
            resolved = _resolve_type(type_ann, ctx)
            name_types[var_name] = resolved
            target = _make_name_expr(var_name, resolved, abs_ln, indent, ctx)
            value = _parse_expr_text(ctx, value_text, abs_ln, _find_expr_col(ctx, value_text, abs_ln, indent + s_clean.index("=") + 2), name_types)
            type_expr_node = _make_type_expr(resolved, ctx)
            span = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
            ann_stmt = AnnAssign(
                source_span=span,
                target=target,
                annotation=resolved,
                annotation_type_expr=type_expr_node,
                value=value,
                decl_type=resolved,
                decl_type_expr=type_expr_node,
                declare=True,
            )
            if len(pending_trivia) > 0:
                ann_stmt.leading_trivia = list(pending_trivia)
            if len(pending_comments) > 0:
                ann_stmt.leading_comments = list(pending_comments)
            stmts.append(ann_stmt)
            i += 1
            pending_trivia = []
            pending_comments = []
            continue

        # Annotation-only: x: Type (no value)
        ann_only = re.match(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:\s*(.+)$", s_clean)
        if ann_only is not None:
            ann_var = re.strip_group(ann_only, 1)
            ann_type = re.strip_group(ann_only, 2)
            # Ensure it's not a dict/slice by checking no '=' follows
            if "=" not in ann_type:
                resolved = _resolve_type(ann_type, ctx)
                name_types[ann_var] = resolved
                target = _make_name_expr(ann_var, resolved, abs_ln, indent, ctx)
                type_expr_node = _make_type_expr(resolved, ctx)
                span = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
                ann_stmt = AnnAssign(
                    source_span=span,
                    target=target,
                    annotation=resolved,
                    annotation_type_expr=type_expr_node,
                    value=None,
                    decl_type=resolved,
                    decl_type_expr=type_expr_node,
                    declare=True,
                )
                if len(pending_trivia) > 0:
                    ann_stmt.leading_trivia = list(pending_trivia)
                if len(pending_comments) > 0:
                    ann_stmt.leading_comments = list(pending_comments)
                stmts.append(ann_stmt)
                i += 1
                pending_trivia = []
                pending_comments = []
                continue

        # Augmented assignment: x += value
        target_text, op_text, value_text = _parse_aug_assign(s_clean)
        if target_text != "":
            op_map: dict[str, str] = {
                "+=": "Add", "-=": "Sub", "*=": "Mult", "/=": "Div",
                "%=": "Mod", "//=": "FloorDiv", "**=": "Pow",
                "&=": "BitAnd", "|=": "BitOr", "^=": "BitXor",
                "<<=": "LShift", ">>=": "RShift",
            }
            target = _parse_expr_text(ctx, target_text, abs_ln, _find_expr_col(ctx, target_text, abs_ln, indent), name_types)
            value = _parse_expr_text(ctx, value_text, abs_ln, _find_expr_col(ctx, value_text, abs_ln, indent + len(target_text) + len(op_text) + 2), name_types)
            span = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
            aug_stmt = AugAssign(
                source_span=span,
                target=target,
                op=op_map.get(op_text, op_text),
                value=value,
                decl_type=_get_resolved_type(target),
                declare=False,
            )
            stmts.append(aug_stmt)
            i += 1
            pending_trivia = []
            pending_comments = []
            continue

        # Swap pattern: a, b = b, a
        swap_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", s_clean)
        if swap_match is not None:
            swap_left_name = re.strip_group(swap_match, 1)
            swap_right_name = re.strip_group(swap_match, 2)
            swap_rhs = re.strip_group(swap_match, 3)
            # Check if rhs is "b, a" (reverse of lhs)
            rhs_parts = swap_rhs.split(",")
            if len(rhs_parts) == 2:
                rhs_a = rhs_parts[0].strip()
                rhs_b = rhs_parts[1].strip()
                if rhs_a == swap_right_name and rhs_b == swap_left_name:
                    # Swap detected
                    left_type = name_types.get(swap_left_name, "unknown")
                    right_type = name_types.get(swap_right_name, "unknown")
                    left = _make_name_expr(swap_left_name, left_type, abs_ln, indent, ctx)
                    left.base.borrow_kind = "value"
                    left.type_expr = None
                    right = _make_name_expr(swap_right_name, right_type, abs_ln, indent, ctx)
                    right.base.borrow_kind = "value"
                    right.type_expr = None
                    span = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
                    stmts.append(Swap(source_span=span, left=left, right=right))
                    i += 1
                    pending_trivia = []
                    pending_comments = []
                    continue

        # Simple assignment: x = value
        target_text, value_text = _parse_simple_assign(s_clean)
        if target_text != "":
            # Check it's not a comparison or augmented op
            if not target_text.endswith(("!", "<", ">", "+", "-", "*", "/", "%", "&", "|", "^")):
                target = _parse_expr_text(ctx, target_text, abs_ln, _find_expr_col(ctx, target_text, abs_ln, indent), name_types)
                value = _parse_expr_text(ctx, value_text, abs_ln, _find_expr_col(ctx, value_text, abs_ln, indent + len(target_text) + 3), name_types)
                # Infer type from value
                val_type = _get_resolved_type(value)
                # declare: True if this is a simple Name target (not subscript/attr)
                is_declare = isinstance(target, Name)
                if isinstance(target, Name) and val_type != "unknown":
                    name_types[target.id] = val_type
                span = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
                assign_stmt = Assign(
                    source_span=span,
                    target=target,
                    value=value,
                    decl_type=val_type if val_type != "unknown" else None,
                    declare=is_declare,
                    declare_init=True if is_declare else None,
                )
                if len(pending_trivia) > 0:
                    assign_stmt.leading_trivia = list(pending_trivia)
                if len(pending_comments) > 0:
                    assign_stmt.leading_comments = list(pending_comments)
                stmts.append(assign_stmt)
                i += 1
                pending_trivia = []
                pending_comments = []
                continue

        # Expression statement (e.g., function call)
        expr = _parse_expr_text(ctx, s_clean, abs_ln, indent, name_types)
        span = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
        expr_stmt = ExprStmt(source_span=span, value=expr)
        if len(pending_trivia) > 0:
            expr_stmt.leading_trivia = list(pending_trivia)
        if len(pending_comments) > 0:
            expr_stmt.leading_comments = list(pending_comments)
        stmts.append(expr_stmt)
        i += 1
        pending_trivia = []
        pending_comments = []

    return stmts


def _find_abs_line(all_lines: list[str], target_line: str, hint: int) -> int:
    """ブロック行の絶対行番号を探す。hint 以降で最初に一致する行を返す。"""
    stripped = target_line.rstrip()
    # hint 以降を先に探す
    start = max(0, hint)
    for i in range(start, len(all_lines)):
        if all_lines[i].rstrip() == stripped:
            return i + 1
    # hint 以前にフォールバック
    for i in range(0, start):
        if all_lines[i].rstrip() == stripped:
            return i + 1
    return hint + 1


def _find_expr_col(ctx: ParseContext, expr_text: str, abs_ln: int, fallback: int) -> int:
    """元の行テキスト内で式テキストの位置を検索する (golden 準拠)。

    現行パーサーは ln_txt.find(expr_txt) で最初の出現を使う。
    短い式テキスト (1-2文字) は誤マッチしやすいので fallback を優先。
    """
    if expr_text == "" or abs_ln < 1 or abs_ln > len(ctx.lines):
        return fallback
    line_text = ctx.lines[abs_ln - 1]
    pos = line_text.find(expr_text)
    if pos >= 0:
        return pos
    return fallback


def _parse_expr_text(
    ctx: ParseContext,
    text: str,
    line: int,
    col_offset: int,
    name_types: dict[str, str],
) -> Expr:
    """テキストから式をパースする。"""
    tokens = _tokenize_expr(text)
    parser = ExprParser(
        tokens=tokens,
        pos=0,
        source_line=line,
        line_col_offset=col_offset,
        source_text=text,
        name_types=name_types,
        ctx=ctx,
    )
    return parser.parse_expr()


def _make_name_expr(name: str, resolved_type: str, line: int, col: int, ctx: ParseContext) -> Name:
    """Name ノードを生成する。"""
    # golden 準拠: 元の行テキスト内で名前の位置を検索
    actual_col = _find_expr_col(ctx, name, line, col)
    span = make_span(line, actual_col, line, actual_col + len(name))
    base = ExprBase(
        source_span=span,
        resolved_type=resolved_type,
        casts=[],
        borrow_kind="value",
        repr_text=name,
    )
    name_node = Name(base=base, id=name)
    if resolved_type != "unknown":
        name_node.type_expr = _make_type_expr(resolved_type, ctx)
    return name_node


# ---------------------------------------------------------------------------
# Control flow parsers
# ---------------------------------------------------------------------------

def _parse_for_stmt(
    ctx: ParseContext,
    block_lines: list[str],
    start_i: int,
    parent_indent: int,
    name_types: dict[str, str],
    trivia: list[TriviaNode],
    comments: list[str],
) -> tuple[Stmt, int]:
    """for 文をパースする。"""
    ln = block_lines[start_i]
    s = _strip_inline_comment(ln.strip())
    indent = len(ln) - len(ln.lstrip(" "))
    abs_ln = _find_abs_line(ctx.lines, ln, 0)

    # Parse: for TARGET in ITER:
    target_name, iter_text = _parse_for_header(s)
    if target_name == "":
        # Fallback
        span = make_span(abs_ln, indent, abs_ln, indent + len(s))
        dummy = _parse_expr_text(ctx, "None", abs_ln, indent, name_types)
        return ExprStmt(source_span=span, value=dummy), start_i + 1

    # Check if it's range() — must determine BEFORE body parsing to set name_types
    range_args_text = _parse_range_call(iter_text)
    if range_args_text is not None:
        name_types[target_name] = "int64"
    else:
        # Non-range for: infer element type from iterable BEFORE body parsing
        iter_name = iter_text.strip()
        if iter_name in name_types:
            container_type = name_types[iter_name]
            elem = _extract_element_type(container_type)
            if elem != "unknown":
                name_types[target_name] = elem

    # Collect body
    sub_lines, end_i = _collect_sub_block(block_lines, start_i + 1, indent)
    body_stmts = _parse_block_lines(ctx, sub_lines, name_types, "for")

    # Determine end span
    end_ln = abs_ln
    end_col = indent + len(s)
    if len(sub_lines) > 0:
        for bl in reversed(sub_lines):
            if bl.strip() != "":
                end_ln = _find_abs_line(ctx.lines, bl, 0)
                end_col = len(bl.rstrip())
                break

    # ForRange span: col=0 (always), end from body
    span = make_span(abs_ln, 0, end_ln, end_col)

    if range_args_text is not None:
        range_args = _split_type_args_outer(range_args_text)
        # ForRange target: resolved_type="unknown" (型は target_type で別途指定)
        target = _make_name_expr(target_name, "unknown", abs_ln, indent + 4, ctx)
        # target は type_expr を持たない
        target.type_expr = None
        start_expr: Expr
        stop_expr: Expr
        step_expr: Expr
        # range(...) 内の引数位置を計算
        # 行テキスト: "    for y in range(height):"
        # iter_text: "range(height)"
        # range_args_text: "height"
        # range( の開始位置を行内で探す
        line_text = block_lines[start_i] if start_i < len(block_lines) else ""
        range_pos = line_text.find("range(")
        range_inner_col = range_pos + 6 if range_pos >= 0 else indent
        # range のキーワード位置 (暗黙 start=0/step=1 のスパンに使う)
        range_kw_span = make_span(abs_ln, range_pos if range_pos >= 0 else indent, abs_ln, range_inner_col - 1 if range_pos >= 0 else indent + 5)
        if len(range_args) == 1:
            start_expr = Constant(base=ExprBase(source_span=range_kw_span, resolved_type="int64", casts=[], borrow_kind="value", repr_text="0"), value=0)
            stop_expr = _parse_expr_text(ctx, range_args[0].strip(), abs_ln, range_inner_col, name_types)
            step_expr = Constant(base=ExprBase(source_span=range_kw_span, resolved_type="int64", casts=[], borrow_kind="value", repr_text="1"), value=1)
        elif len(range_args) == 2:
            start_expr = _parse_expr_text(ctx, range_args[0].strip(), abs_ln, range_inner_col, name_types)
            comma1 = range_inner_col + len(range_args[0]) + 2  # ", "
            stop_expr = _parse_expr_text(ctx, range_args[1].strip(), abs_ln, comma1, name_types)
            step_expr = Constant(base=ExprBase(source_span=range_kw_span, resolved_type="int64", casts=[], borrow_kind="value", repr_text="1"), value=1)
        else:
            start_expr = _parse_expr_text(ctx, range_args[0].strip(), abs_ln, range_inner_col, name_types)
            comma1 = range_inner_col + len(range_args[0]) + 2
            stop_expr = _parse_expr_text(ctx, range_args[1].strip(), abs_ln, comma1, name_types)
            comma2 = comma1 + len(range_args[1]) + 2
            step_expr = _parse_expr_text(ctx, range_args[2].strip(), abs_ln, comma2, name_types)

        fr = ForRange(
            source_span=span,
            target=target,
            target_type="int64",
            start=start_expr,
            stop=stop_expr,
            step=step_expr,
            body=body_stmts,
            orelse=[],
            range_mode=_infer_range_mode(step_expr),
        )
        if len(trivia) > 0:
            fr.leading_trivia = list(trivia)
        if len(comments) > 0:
            fr.leading_comments = list(comments)
        return fr, end_i

    # General for loop — infer element type from iterable
    iter_expr = _parse_expr_text(ctx, iter_text, abs_ln, _find_expr_col(ctx, iter_text, abs_ln, indent), name_types)
    iter_source_type = _get_resolved_type(iter_expr)
    elem_type = _extract_element_type(iter_source_type)
    if elem_type != "unknown":
        name_types[target_name] = elem_type
    target_type = elem_type
    target = _make_name_expr(target_name, elem_type, abs_ln, indent + 4, ctx)
    # For target には type_expr を付けない (ForRange と同様)
    target.type_expr = None
    # iter Name に iterable 情報を付加
    if isinstance(iter_expr, Name) and iter_source_type != "unknown":
        iter_expr.iterable_trait = "yes"
        iter_expr.iter_protocol = "static_range"
        iter_expr.iter_element_type = elem_type
    for_stmt = For(
        source_span=span,
        target=target,
        target_type=target_type,
        iter_expr=iter_expr,
        iter_element_type=elem_type,
        iter_mode="static_fastpath" if elem_type != "unknown" else "iter",
        iter_source_type=iter_source_type,
        body=body_stmts,
        orelse=[],
    )
    if len(trivia) > 0:
        for_stmt.leading_trivia = list(trivia)
    return for_stmt, end_i


def _parse_while_stmt(
    ctx: ParseContext,
    block_lines: list[str],
    start_i: int,
    parent_indent: int,
    name_types: dict[str, str],
    trivia: list[TriviaNode],
    comments: list[str],
) -> tuple[While, int]:
    """while 文をパースする。"""
    ln = block_lines[start_i]
    s = _strip_inline_comment(ln.strip())
    indent = len(ln) - len(ln.lstrip(" "))
    abs_ln = _find_abs_line(ctx.lines, ln, 0)

    # Parse: while COND:
    cond_text = s[6:].rstrip(":").strip()
    test = _parse_expr_text(ctx, cond_text, abs_ln, _find_expr_col(ctx, cond_text, abs_ln, indent + 6), name_types)

    sub_lines, end_i = _collect_sub_block(block_lines, start_i + 1, indent)
    body_stmts = _parse_block_lines(ctx, sub_lines, name_types, "while")

    end_ln = abs_ln
    end_col = indent + len(s)
    if len(sub_lines) > 0:
        for bl in reversed(sub_lines):
            if bl.strip() != "":
                end_ln = _find_abs_line(ctx.lines, bl, 0)
                end_col = len(bl.rstrip())
                break

    span = make_span(abs_ln, indent, end_ln, end_col)
    return While(source_span=span, test=test, body=body_stmts, orelse=[]), end_i


def _parse_if_stmt(
    ctx: ParseContext,
    block_lines: list[str],
    start_i: int,
    parent_indent: int,
    name_types: dict[str, str],
    trivia: list[TriviaNode],
    comments: list[str],
) -> tuple[If, int]:
    """if/elif/else 文をパースする。"""
    ln = block_lines[start_i]
    s = _strip_inline_comment(ln.strip())
    indent = len(ln) - len(ln.lstrip(" "))
    abs_ln = _find_abs_line(ctx.lines, ln, 0)

    # Parse condition
    cond_text = s[3:].rstrip(":").strip()
    test = _parse_expr_text(ctx, cond_text, abs_ln, _find_expr_col(ctx, cond_text, abs_ln, indent + 3), name_types)

    # Collect then block
    then_lines, next_i = _collect_sub_block(block_lines, start_i + 1, indent)
    then_stmts = _parse_block_lines(ctx, then_lines, name_types, "if")

    # Check for elif / else
    orelse: list[Stmt] = []
    if next_i < len(block_lines):
        next_ln = block_lines[next_i]
        next_s = next_ln.strip()
        next_indent = len(next_ln) - len(next_ln.lstrip(" ")) if next_s != "" else 0
        if next_indent == indent:
            if next_s.startswith("elif "):
                # Convert elif to nested if
                elif_stmt, next_i = _parse_elif_stmt(ctx, block_lines, next_i, indent, name_types)
                orelse = [elif_stmt]
            elif next_s.startswith("else:") or next_s == "else:":
                else_lines, next_i = _collect_sub_block(block_lines, next_i + 1, indent)
                orelse = _parse_block_lines(ctx, else_lines, name_types, "else")

    end_ln = abs_ln
    end_col = indent + len(s)
    if len(orelse) > 0:
        last_stmt = orelse[-1]
        if hasattr(last_stmt, "source_span"):
            sp = last_stmt.source_span
            if sp.end_lineno is not None:
                end_ln = sp.end_lineno
            if sp.end_col is not None:
                end_col = sp.end_col
    elif len(then_lines) > 0:
        for bl in reversed(then_lines):
            if bl.strip() != "":
                end_ln = _find_abs_line(ctx.lines, bl, 0)
                end_col = len(bl.rstrip())
                break

    span = make_span(abs_ln, indent, end_ln, end_col)
    if_stmt = If(source_span=span, test=test, body=then_stmts, orelse=orelse)
    if len(trivia) > 0:
        if_stmt.leading_trivia = list(trivia)
    if len(comments) > 0:
        if_stmt.leading_comments = list(comments)
    return if_stmt, next_i


def _parse_elif_stmt(
    ctx: ParseContext,
    block_lines: list[str],
    start_i: int,
    parent_indent: int,
    name_types: dict[str, str],
) -> tuple[If, int]:
    """elif 節を If ノードとしてパースする。"""
    ln = block_lines[start_i]
    s = _strip_inline_comment(ln.strip())
    indent = len(ln) - len(ln.lstrip(" "))
    abs_ln = _find_abs_line(ctx.lines, ln, 0)

    cond_text = s[5:].rstrip(":").strip()
    test = _parse_expr_text(ctx, cond_text, abs_ln, _find_expr_col(ctx, cond_text, abs_ln, indent + 5), name_types)

    then_lines, next_i = _collect_sub_block(block_lines, start_i + 1, indent)
    then_stmts = _parse_block_lines(ctx, then_lines, name_types, "elif")

    orelse: list[Stmt] = []
    if next_i < len(block_lines):
        next_ln = block_lines[next_i]
        next_s = next_ln.strip()
        next_indent = len(next_ln) - len(next_ln.lstrip(" ")) if next_s != "" else 0
        if next_indent == indent:
            if next_s.startswith("elif "):
                elif_stmt, next_i = _parse_elif_stmt(ctx, block_lines, next_i, indent, name_types)
                orelse = [elif_stmt]
            elif next_s.startswith("else:"):
                else_lines, next_i = _collect_sub_block(block_lines, next_i + 1, indent)
                orelse = _parse_block_lines(ctx, else_lines, name_types, "else")

    end_ln = abs_ln
    end_col = indent + len(s)
    span = make_span(abs_ln, indent, end_ln, end_col)
    return If(source_span=span, test=test, body=then_stmts, orelse=orelse), next_i


def _collect_sub_block(block_lines: list[str], start_i: int, parent_indent: int) -> tuple[list[str], int]:
    """サブブロック（子インデント）を収集する。"""
    result: list[str] = []
    i = start_i
    total = len(block_lines)
    while i < total:
        ln = block_lines[i]
        s = ln.strip()
        if s == "" or s.startswith("#"):
            result.append(ln)
            i += 1
            continue
        indent = len(ln) - len(ln.lstrip(" "))
        if indent <= parent_indent:
            break
        result.append(ln)
        i += 1
    return result, i


# ---------------------------------------------------------------------------
# Arg usage analysis
# ---------------------------------------------------------------------------

def _compute_arg_usage(arg_order: list[str], body: list[Stmt]) -> dict[str, str]:
    """引数の使用状況を解析する。"""
    reassigned: set[str] = set()
    _collect_reassigned(body, reassigned)
    usage: dict[str, str] = {}
    for arg in arg_order:
        if arg in reassigned:
            usage[arg] = "reassigned"
        else:
            usage[arg] = "readonly"
    return usage


def _collect_reassigned(stmts: list[Stmt], out: set[str]) -> None:
    """再代入されている変数名を収集する。"""
    for s in stmts:
        if isinstance(s, Assign):
            if isinstance(s.target, Name):
                out.add(s.target.id)
        elif isinstance(s, AugAssign):
            if isinstance(s.target, Name):
                out.add(s.target.id)
        elif isinstance(s, AnnAssign):
            if isinstance(s.target, Name):
                out.add(s.target.id)
        elif isinstance(s, Swap):
            if isinstance(s.left, Name):
                out.add(s.left.id)
            if isinstance(s.right, Name):
                out.add(s.right.id)
        elif isinstance(s, If):
            _collect_reassigned(s.body, out)
            _collect_reassigned(s.orelse, out)
        elif isinstance(s, ForRange):
            out.add(s.target.id) if isinstance(s.target, Name) else None
            _collect_reassigned(s.body, out)
        elif isinstance(s, For):
            if isinstance(s.target, Name):
                out.add(s.target.id)
            _collect_reassigned(s.body, out)
        elif isinstance(s, While):
            _collect_reassigned(s.body, out)
        elif isinstance(s, Try):
            _collect_reassigned(s.body, out)
            for h in s.handlers:
                _collect_reassigned(h.body, out)
            _collect_reassigned(s.finalbody, out)


# ---------------------------------------------------------------------------
# Postprocessing + meta building
# ---------------------------------------------------------------------------

def _postprocess(ctx: ParseContext, body_items: list[Stmt], renamed_symbols: dict[str, str]) -> None:
    """Phase 3: 後処理（main リネーム、暗黙 builtin import 追加等）。"""
    # Rename main → __pytra_main
    for stmt in body_items:
        if isinstance(stmt, FunctionDef) and stmt.name == "main":
            renamed_symbols["main"] = "__pytra_main"
            stmt.name = "__pytra_main"

    # Add implicit builtin module bindings
    for mod_id in sorted(ctx.implicit_builtin_modules.keys()):
        ctx.import_bindings.append({
            "module_id": mod_id,
            "export_name": "",
            "local_name": mod_id,
            "binding_kind": "implicit_builtin",
            "source_file": ctx.filename,
            "source_line": 0,
        })


def _build_meta(ctx: ParseContext) -> dict[str, JsonVal]:
    """Module.meta を構築する。"""
    # Build import_resolution
    resolution_bindings: list[dict[str, JsonVal]] = []
    for binding in ctx.import_bindings:
        rb: dict[str, JsonVal] = dict(binding)
        # Add resolution fields
        mod_id = str(binding.get("module_id", ""))
        binding_kind = str(binding.get("binding_kind", ""))
        rb["source_module_id"] = mod_id
        # implicit_builtin は source_export_name を持たない
        if binding_kind != "implicit_builtin":
            rb["source_export_name"] = binding.get("export_name", "")
        rb["source_binding_kind"] = binding_kind
        # Resolve runtime module
        if mod_id == "pathlib":
            rb["runtime_module_id"] = "pytra.std.pathlib"
            rb["runtime_group"] = "std"
            rb["resolved_binding_kind"] = "symbol"
            export = str(binding.get("export_name", ""))
            rb["runtime_symbol"] = export
            rb["runtime_symbol_kind"] = "class"
            rb["runtime_symbol_dispatch"] = "ctor"
            rb["runtime_semantic_tag"] = "stdlib.symbol." + export
        elif "pytra.std." in mod_id:
            rb["runtime_module_id"] = mod_id
            rb["runtime_group"] = "std"
            rb["resolved_binding_kind"] = binding.get("binding_kind", "")
            export = str(binding.get("export_name", ""))
            rb["runtime_symbol"] = export
            rb["runtime_symbol_kind"] = "function"
            rb["runtime_symbol_dispatch"] = "function"
            rb["runtime_semantic_tag"] = "stdlib.fn." + export
        elif "pytra.utils." in mod_id:
            rb["runtime_module_id"] = mod_id
            rb["runtime_group"] = "utils"
            rb["resolved_binding_kind"] = binding.get("binding_kind", "")
            export = str(binding.get("export_name", ""))
            rb["runtime_symbol"] = export
            rb["runtime_symbol_kind"] = "function"
            rb["runtime_symbol_dispatch"] = "function"
            rb["runtime_semantic_tag"] = "stdlib.fn." + export
        elif "pytra.built_in." in mod_id:
            rb["runtime_module_id"] = mod_id
            rb["runtime_group"] = "built_in"
        resolution_bindings.append(rb)

    import_resolution: dict[str, JsonVal] = {
        "schema_version": 1,
        "bindings": resolution_bindings,
        "qualified_refs": list(ctx.qualified_symbol_refs),
    }

    # import_symbols as dict
    import_symbols_jv: dict[str, JsonVal] = {}
    for local, info in ctx.import_symbols.items():
        import_symbols_jv[local] = dict(info)

    meta: dict[str, JsonVal] = {
        "parser_backend": "self_hosted",
        "import_resolution": import_resolution,
        "import_bindings": list(ctx.import_bindings),
        "qualified_symbol_refs": list(ctx.qualified_symbol_refs),
        "import_modules": dict(ctx.import_modules),
        "import_symbols": import_symbols_jv,
    }
    return meta


def _extract_docstring(block_lines: list[str]) -> Optional[str]:
    """ブロックの先頭から docstring を抽出する。"""
    for ln in block_lines:
        s = ln.strip()
        if s == "":
            continue
        if s.startswith("#"):
            continue
        if s.startswith('"""') or s.startswith("'''"):
            # Simple single-line docstring
            quote = s[:3]
            if s.endswith(quote) and len(s) > 6:
                return s[3:-3]
        break
    return None
