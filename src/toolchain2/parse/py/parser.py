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
    DictExpr, ListComp, RangeExpr, Expr, expr_to_jv,
    # Statements
    ImportFrom, AnnAssign, Assign, AugAssign, ExprStmt, Return, Raise, Pass,
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


def _is_word_char(ch: str) -> bool:
    return ch == "_" or (ch >= "a" and ch <= "z") or (ch >= "A" and ch <= "Z") or (ch >= "0" and ch <= "9")


def _skip_ws(s: str, i: int) -> int:
    while i < len(s) and (s[i] == " " or s[i] == "\t"):
        i += 1
    return i


def _parse_from_import(s: str) -> tuple[str, str]:
    """'from MOD import NAMES' をパースして (module, names_text) を返す。失敗時は ("", "")。"""
    if not s.startswith("from "):
        return "", ""
    rest = s[5:].lstrip()
    # module name (non-space)
    end = 0
    while end < len(rest) and rest[end] != " " and rest[end] != "\t":
        end += 1
    if end == 0:
        return "", ""
    mod = rest[:end]
    rest = rest[end:].lstrip()
    if not rest.startswith("import "):
        return "", ""
    names = rest[7:].strip()
    if names == "":
        return "", ""
    return mod, names


def _parse_def_name(s: str) -> str:
    """'def NAME(' からNAMEを抽出。失敗時は ""。"""
    if not s.startswith("def "):
        return ""
    rest = s[4:].lstrip()
    end = 0
    while end < len(rest) and _is_word_char(rest[end]):
        end += 1
    if end == 0:
        return ""
    name = rest[:end]
    # Check '(' follows
    after = rest[end:].lstrip()
    if after == "" or after[0] != "(":
        return ""
    return name


def _parse_class_name(s: str) -> str:
    """'class NAME' からNAMEを抽出。"""
    if not s.startswith("class "):
        return ""
    rest = s[6:].lstrip()
    end = 0
    while end < len(rest) and _is_word_char(rest[end]):
        end += 1
    if end == 0:
        return ""
    return rest[:end]


def _parse_ann_assign(s: str) -> tuple[str, str, str]:
    """'NAME: TYPE = VALUE' をパース。失敗時は ("", "", "")。"""
    # Find identifier
    end = 0
    while end < len(s) and _is_word_char(s[end]):
        end += 1
    if end == 0:
        return "", "", ""
    var_name = s[:end]
    rest = s[end:].lstrip()
    if rest == "" or rest[0] != ":":
        return "", "", ""
    rest = rest[1:].lstrip()
    # Find '=' (top-level, outside brackets)
    eq_pos = _find_top_level_eq(rest)
    if eq_pos < 0:
        return "", "", ""
    type_ann = rest[:eq_pos].rstrip()
    value_text = rest[eq_pos + 1:].lstrip()
    if type_ann == "" or value_text == "":
        return "", "", ""
    return var_name, type_ann, value_text


def _find_top_level_eq(s: str) -> int:
    """ブラケットの外側にある最初の '=' の位置を返す。'==' は無視。"""
    depth = 0
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == "(" or ch == "[" or ch == "{":
            depth += 1
        elif ch == ")" or ch == "]" or ch == "}":
            depth -= 1
        elif ch == "=" and depth == 0:
            # Ensure not ==
            if i + 1 < n and s[i + 1] == "=":
                i += 2
                continue
            # Ensure not !=, <=, >=
            if i > 0 and s[i - 1] in "!<>":
                i += 1
                continue
            return i
        i += 1
    return -1


def _parse_aug_assign(s: str) -> tuple[str, str, str]:
    """augmented assignment をパース。失敗時は ("", "", "")。"""
    ops = ["//=", "**=", "<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^="]
    for op in ops:
        pos = s.find(op)
        if pos > 0:
            target = s[:pos].rstrip()
            value = s[pos + len(op):].lstrip()
            if target != "" and value != "":
                return target, op, value
    return "", "", ""


def _parse_simple_assign(s: str) -> tuple[str, str]:
    """simple assignment をパース。失敗時は ("", "")。'==' を除外。"""
    eq_pos = _find_top_level_eq(s)
    if eq_pos < 0:
        return "", ""
    target = s[:eq_pos].rstrip()
    value = s[eq_pos + 1:].lstrip()
    if target == "" or value == "":
        return "", ""
    # Exclude if target ends with augmented operator
    if target.endswith(("!", "+", "-", "*", "/", "%", "&", "|", "^", "<", ">")):
        return "", ""
    return target, value


def _parse_for_header(s: str) -> tuple[str, str]:
    """'for TARGET in ITER:' をパース。(target_name, iter_text)。失敗は ("", "")。"""
    if not s.startswith("for "):
        return "", ""
    rest = s[4:].lstrip()
    # Find ' in '
    in_pos = rest.find(" in ")
    if in_pos < 0:
        return "", ""
    target_name = rest[:in_pos].strip()
    iter_text = rest[in_pos + 4:].rstrip(":")
    iter_text = iter_text.strip()
    return target_name, iter_text


def _parse_range_call(s: str) -> Optional[str]:
    """'range(ARGS)' をパース。ARGS 部分を返す。range でなければ None。"""
    if not s.startswith("range("):
        stripped = s.lstrip()
        if not stripped.startswith("range("):
            return None
        s = stripped
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

        # Identifiers / keywords
        if ch == "_" or (ch >= "a" and ch <= "z") or (ch >= "A" and ch <= "Z"):
            start = i
            i += 1
            while i < n and (text[i] == "_" or (text[i] >= "a" and text[i] <= "z") or (text[i] >= "A" and text[i] <= "Z") or (text[i] >= "0" and text[i] <= "9")):
                i += 1
            tokens.append(Token("NAME", text[start:i], start, i))
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

    def _span(self, start: int, end: int) -> SourceSpan:
        return make_span(
            self.source_line,
            self.line_col_offset + start,
            self.source_line,
            self.line_col_offset + end,
        )

    def _span_multi(self, start_line: int, start_col: int, end_line: int, end_col: int) -> SourceSpan:
        return make_span(start_line, start_col, end_line, end_col)

    def _repr(self, start: int, end: int) -> str:
        return self.source_text[start:end]

    def _base(self, start: int, end: int, resolved_type: str, borrow_kind: str) -> ExprBase:
        return ExprBase(
            source_span=self._span(start, end),
            resolved_type=resolved_type,
            casts=[],
            borrow_kind=borrow_kind,
            repr_text=self._repr(start, end),
        )

    # --- Precedence climbing ---

    def parse_expr(self) -> Expr:
        return self._parse_ternary()

    def _parse_ternary(self) -> Expr:
        """a if cond else b"""
        body = self._parse_or()
        if self.peek().value == "if":
            self.advance()
            test = self._parse_or()
            self.expect("NAME", "else")
            orelse = self._parse_ternary()
            # IfExp
            start = 0
            end = len(self.source_text)
            base = self._base(start, end, body.base.resolved_type if isinstance(body, (Name, Constant, BinOp, UnaryOp, Call, Attribute, Subscript)) else "unknown", "value")
            return IfExp(base=base, test=test, body=body, orelse=orelse)
        return body

    def _parse_or(self) -> Expr:
        left = self._parse_and()
        while self.peek().value == "or":
            self.advance()
            right = self._parse_and()
            start = _expr_start(left)
            end = _expr_end(right)
            base = self._base(start, end, "bool", "value")
            left = BoolOp(base=base, op="Or", values=[left, right])
        return left

    def _parse_and(self) -> Expr:
        left = self._parse_not()
        while self.peek().value == "and":
            self.advance()
            right = self._parse_not()
            start = _expr_start(left)
            end = _expr_end(right)
            base = self._base(start, end, "bool", "value")
            left = BoolOp(base=base, op="And", values=[left, right])
        return left

    def _parse_not(self) -> Expr:
        if self.peek().value == "not":
            tok = self.advance()
            operand = self._parse_not()
            end = _expr_end(operand)
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
            start = _expr_start(left)
            end = _expr_end(comparators[-1])
            base = self._base(start, end, "bool", "value")
            return Compare(base=base, left=left, ops=ops, comparators=comparators)
        return left

    def _parse_bitor(self) -> Expr:
        left = self._parse_bitxor()
        while self.peek().value == "|":
            self.advance()
            right = self._parse_bitxor()
            start = _expr_start(left)
            end = _expr_end(right)
            base = self._base(start, end, "int64", "value")
            left = BinOp(base=base, left=left, op="BitOr", right=right)
        return left

    def _parse_bitxor(self) -> Expr:
        left = self._parse_bitand()
        while self.peek().value == "^":
            self.advance()
            right = self._parse_bitand()
            start = _expr_start(left)
            end = _expr_end(right)
            base = self._base(start, end, "int64", "value")
            left = BinOp(base=base, left=left, op="BitXor", right=right)
        return left

    def _parse_bitand(self) -> Expr:
        left = self._parse_shift()
        while self.peek().value == "&":
            self.advance()
            right = self._parse_shift()
            start = _expr_start(left)
            end = _expr_end(right)
            base = self._base(start, end, "int64", "value")
            left = BinOp(base=base, left=left, op="BitAnd", right=right)
        return left

    def _parse_shift(self) -> Expr:
        left = self._parse_addsub()
        while self.peek().value == "<<" or self.peek().value == ">>":
            op_tok = self.advance()
            right = self._parse_addsub()
            op_name = "LShift" if op_tok.value == "<<" else "RShift"
            start = _expr_start(left)
            end = _expr_end(right)
            base = self._base(start, end, "int64", "value")
            left = BinOp(base=base, left=left, op=op_name, right=right)
        return left

    def _parse_addsub(self) -> Expr:
        left = self._parse_muldiv()
        while self.peek().value == "+" or self.peek().value == "-":
            op_tok = self.advance()
            right = self._parse_muldiv()
            op_name = "Add" if op_tok.value == "+" else "Sub"
            start = _expr_start(left)
            end = _expr_end(right)
            res_type = _binop_result_type(_get_resolved_type(left), _get_resolved_type(right), op_name)
            base = self._base(start, end, res_type, "value")
            left = BinOp(base=base, left=left, op=op_name, right=right)
        return left

    def _parse_muldiv(self) -> Expr:
        left = self._parse_unary()
        while self.peek().value in ("*", "/", "//", "%"):
            op_tok = self.advance()
            right = self._parse_unary()
            op_map: dict[str, str] = {"*": "Mult", "/": "Div", "//": "FloorDiv", "%": "Mod"}
            op_name = op_map.get(op_tok.value, op_tok.value)
            start = _expr_start(left)
            end = _expr_end(right)
            res_type = _binop_result_type(_get_resolved_type(left), _get_resolved_type(right), op_name)
            base = self._base(start, end, res_type, "value")
            left = BinOp(base=base, left=left, op=op_name, right=right)
        return left

    def _parse_unary(self) -> Expr:
        tok = self.peek()
        if tok.value == "-" and tok.kind == "OP":
            self.advance()
            operand = self._parse_unary()
            end = _expr_end(operand)
            res_type = _get_resolved_type(operand)
            base = self._base(tok.start, end, res_type, "value")
            return UnaryOp(base=base, op="USub", operand=operand)
        if tok.value == "+" and tok.kind == "OP":
            self.advance()
            operand = self._parse_unary()
            end = _expr_end(operand)
            res_type = _get_resolved_type(operand)
            base = self._base(tok.start, end, res_type, "value")
            return UnaryOp(base=base, op="UAdd", operand=operand)
        if tok.value == "~" and tok.kind == "OP":
            self.advance()
            operand = self._parse_unary()
            end = _expr_end(operand)
            base = self._base(tok.start, end, "int64", "value")
            return UnaryOp(base=base, op="Invert", operand=operand)
        return self._parse_power()

    def _parse_power(self) -> Expr:
        left = self._parse_postfix()
        if self.peek().value == "**":
            self.advance()
            right = self._parse_unary()  # right-associative
            start = _expr_start(left)
            end = _expr_end(right)
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
                base = self._base(_expr_start(expr), end, "unknown", "value")
                expr = Attribute(base=base, value=expr, attr=attr_tok.value)
            elif tok.value == "[":
                self.advance()
                index = self.parse_expr()
                self.expect("OP", "]")
                end_tok = self.tokens[self.pos - 1]
                base = self._base(_expr_start(expr), end_tok.end, "unknown", "value")
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
                else:
                    args.append(self.parse_expr())
                if self.peek().value != ",":
                    break
                self.advance()  # skip comma
        self.expect("OP", ")")
        end_tok = self.tokens[self.pos - 1]
        start = _expr_start(func)
        end = end_tok.end
        # Resolve call type
        func_name = _get_func_name(func)
        res_type = self._resolve_call_type(func_name, args)
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
        return "unknown"

    def _annotate_call(self, call: Call, func_name: str) -> None:
        """組み込み関数呼び出しにセマンティック情報を付与する。"""
        builtin_map: dict[str, tuple[str, str, str, str]] = {
            "print": ("py_print", "pytra.built_in.io_ops", "py_print", "core.print"),
            "len": ("py_len", "pytra.built_in.sequence", "py_len", "core.len"),
            "abs": ("py_abs", "pytra.built_in.numeric_ops", "py_abs", "core.abs"),
            "min": ("py_min", "pytra.built_in.numeric_ops", "py_min", "core.min"),
            "max": ("py_max", "pytra.built_in.numeric_ops", "py_max", "core.max"),
            "int": ("py_int", "pytra.built_in.scalar_ops", "py_int", "core.int"),
            "float": ("py_float", "pytra.built_in.scalar_ops", "py_float", "core.float"),
            "str": ("py_str", "pytra.built_in.scalar_ops", "py_str", "core.str"),
            "bool": ("py_bool", "pytra.built_in.scalar_ops", "py_bool", "core.bool"),
            "ord": ("py_ord", "pytra.built_in.scalar_ops", "py_ord", "core.ord"),
            "chr": ("py_chr", "pytra.built_in.scalar_ops", "py_chr", "core.chr"),
            "isinstance": ("py_isinstance", "pytra.built_in.predicates", "py_isinstance", "core.isinstance"),
            "range": ("py_range", "pytra.built_in.iter_ops", "py_range", "core.range"),
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
            # Register implicit builtin module
            self.ctx.implicit_builtin_modules[rt_mod] = True
        # Import symbol calls (e.g., perf_counter, Path)
        if func_name in self.ctx.import_symbols:
            sym_info = self.ctx.import_symbols[func_name]
            mod_id = sym_info.get("module", "")
            if mod_id != "":
                call.runtime_module_id = mod_id
                call.runtime_symbol = func_name
                call.runtime_call_adapter_kind = "import_symbol"
                # Resolve semantic tag
                if "pytra.std." in mod_id:
                    call.semantic_tag = "stdlib.fn." + func_name
                    call.resolved_runtime_call = func_name
                    call.resolved_runtime_source = mod_id
                elif mod_id == "pathlib":
                    call.semantic_tag = "stdlib.symbol.Path"
                    call.runtime_call_adapter_kind = "import_symbol"

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
            borrow = "readonly_ref" if resolved != "unknown" else "value"
            # For declared variables that are being targeted (lhs), borrow_kind is "value"
            base = self._base(tok.start, tok.end, resolved, borrow)
            name = Name(base=base, id=tok.value)
            if resolved != "unknown":
                name.type_expr = _make_type_expr(resolved, self.ctx)
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
                base = self._base(tok.start, end_tok.end, "unknown", "value")
                return TupleExpr(base=base, elements=elements)
            self.expect("OP", ")")
            return first

        # List literal or comprehension
        if tok.value == "[":
            return self._parse_list_or_listcomp()

        # Dict literal
        if tok.value == "{":
            return self._parse_dict()

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
        base = self._base(open_tok.start, end_tok.end, "unknown", "value")
        return ListExpr(base=base, elements=elements)

    def _parse_listcomp_tail(self, open_tok: Token, elt: Expr) -> ListComp:
        gens: list[Comprehension] = []
        while self.peek().value == "for":
            self.advance()
            target = self.parse_expr()
            self.expect("NAME", "in")
            iter_expr = self.parse_expr()
            ifs: list[Expr] = []
            while self.peek().value == "if":
                self.advance()
                ifs.append(self.parse_expr())
            gens.append(Comprehension(target=target, iter_expr=iter_expr, ifs=ifs, is_async=False))
        self.expect("OP", "]")
        end_tok = self.tokens[self.pos - 1]
        base = self._base(open_tok.start, end_tok.end, "unknown", "value")
        return ListComp(base=base, elt=elt, generators=gens)

    def _parse_dict(self) -> DictExpr:
        open_tok = self.advance()  # {
        if self.peek().value == "}":
            close_tok = self.advance()
            base = self._base(open_tok.start, close_tok.end, "dict[unknown, unknown]", "value")
            return DictExpr(base=base, keys=[], dict_values=[])
        keys: list[Expr] = []
        values: list[Expr] = []
        entries: list[DictEntry] = []
        while True:
            k = self.parse_expr()
            self.expect("OP", ":")
            v = self.parse_expr()
            keys.append(k)
            values.append(v)
            entries.append(DictEntry(key=k, value=v))
            if self.peek().value != ",":
                break
            self.advance()
            if self.peek().value == "}":
                break
        self.expect("OP", "}")
        end_tok = self.tokens[self.pos - 1]
        base = self._base(open_tok.start, end_tok.end, "unknown", "value")
        return DictExpr(base=base, keys=keys, dict_values=values, entries=entries)


# ---------------------------------------------------------------------------
# Expression helpers
# ---------------------------------------------------------------------------

def _get_resolved_type(e: Expr) -> str:
    if isinstance(e, (Name, Constant, BinOp, UnaryOp, BoolOp, Compare, Call, Attribute, Subscript, IfExp, ListExpr, TupleExpr, DictExpr, ListComp, RangeExpr)):
        return e.base.resolved_type
    if isinstance(e, SliceExpr):
        return "slice"
    return "unknown"


def _expr_start(e: Expr) -> int:
    if isinstance(e, (Name, Constant, BinOp, UnaryOp, BoolOp, Compare, Call, Attribute, Subscript, IfExp, ListExpr, TupleExpr, DictExpr, ListComp, RangeExpr)):
        sp = e.base.source_span
        if sp.col is not None:
            return sp.col
    return 0


def _expr_end(e: Expr) -> int:
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


def _binop_result_type(left_type: str, right_type: str, op: str) -> str:
    """二項演算の結果型を推論する。"""
    if op == "Div":
        return "float64"
    if op == "Pow":
        return "float64"
    if op == "Add" and (left_type == "str" or right_type == "str"):
        return "str"
    if left_type == "float64" or right_type == "float64":
        return "float64"
    if left_type == "int64" or right_type == "int64":
        return "int64"
    if left_type == "unknown" or right_type == "unknown":
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
    )

    # Phase 1: Pre-scan
    _prescan(ctx, lines)

    # Phase 2: Parse body
    body_items: list[Stmt] = []
    main_guard_body: list[Stmt] = []
    _parse_module_body(ctx, lines, body_items, main_guard_body)

    # Phase 3: Post-processing
    _postprocess(ctx, body_items)

    # Build meta
    meta = _build_meta(ctx)

    return Module(
        source_path=filename,
        source_span=NULL_SPAN,
        body=body_items,
        main_guard_body=main_guard_body,
        meta=meta,
        renamed_symbols={},
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
        fn_name = _parse_def_name(s)
        if fn_name != "":
            arrow_pos = s.rfind("->")
            if arrow_pos >= 0:
                ret_ann = s[arrow_pos + 2:].rstrip(":").strip()
                ctx.fn_returns[fn_name] = _resolve_type(ret_ann, ctx)
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

    while ln_no < total:
        ln = lines[ln_no]
        s = ln.strip()
        indent = len(ln) - len(ln.lstrip(" ")) if s != "" else 0

        # Blank line
        if s == "":
            if leading_file_trivia_done:
                pending_trivia.append(TriviaBlank(count=1))
            ln_no += 1
            continue

        # Comment line
        if s.startswith("#"):
            text = s[1:].lstrip() if len(s) > 1 else ""
            if not leading_file_trivia_done:
                pending_trivia.append(TriviaComment(text=text))
                pending_comments.append(text)
            else:
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
                pending_trivia = []
                pending_comments = []
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
            pending_trivia = []
            pending_comments = []
            continue

        # Main guard: if __name__ == "__main__":
        if s_clean.startswith("if __name__") and "__main__" in s_clean:
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
            continue

        # Class def
        cls_name = _parse_class_name(s_clean)
        if cls_name != "":
            cls_stmt, ln_no = _parse_class_def(ctx, lines, ln_no, cls_name, pending_trivia, pending_comments)
            body_items.append(cls_stmt)
            pending_trivia = []
            pending_comments = []
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
) -> tuple[FunctionDef, int]:
    """関数定義をパースする。"""
    header_line = lines[start_ln]
    header = _strip_inline_comment(header_line.strip())

    # Parse signature: def name(args) -> ret:
    paren_start = header.find("(")
    paren_end = header.rfind(")")
    args_text = header[paren_start + 1:paren_end] if paren_start >= 0 and paren_end > paren_start else ""

    # Parse return type
    arrow_pos = header.rfind("->")
    return_ann = ""
    if arrow_pos >= 0:
        return_ann = header[arrow_pos + 2:].rstrip(":").strip()
    return_type = _resolve_type(return_ann, ctx) if return_ann != "" else "None"

    # Parse arguments
    arg_order: list[str] = []
    arg_types: dict[str, str] = {}
    arg_defaults: dict[str, JsonVal] = {}
    arg_index: dict[str, int] = {}
    arg_type_exprs: dict[str, dict[str, JsonVal]] = {}

    if args_text.strip() != "" and args_text.strip() != "self":
        idx = 0
        for param in _split_type_args_outer(args_text):
            param = param.strip()
            if param == "" or param == "self":
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
            if ptype != "unknown":
                arg_type_exprs[pname] = _make_type_expr(ptype, ctx).to_jv()
            idx += 1

    # Collect body
    block_lines, end_ln = _collect_block(lines, start_ln + 1, 0)

    # Parse body with arg types in scope
    name_types: dict[str, str] = dict(arg_types)
    body_stmts = _parse_block_lines(ctx, block_lines, name_types, fn_name)

    # Compute arg_usage
    arg_usage = _compute_arg_usage(arg_order, body_stmts)

    # Extract docstring
    docstring = _extract_docstring(block_lines)

    # Compute end span
    end_lineno = end_ln
    end_col = 0
    if len(block_lines) > 0:
        last_non_empty = ""
        for bl in reversed(block_lines):
            if bl.strip() != "":
                last_non_empty = bl
                break
        end_col = len(last_non_empty.rstrip())
        end_lineno = start_ln + len(block_lines)

    span = make_span(start_ln + 1, 0, end_lineno, end_col)

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

    # Optional fields
    if len(arg_type_exprs) > 0 or len(arg_order) == 0:
        fd.arg_type_exprs = arg_type_exprs
    if return_ann != "":
        fd.return_type_expr = _make_type_expr(return_type, ctx)
    if len(trivia) > 0 or len(comments) > 0:
        fd.leading_trivia = list(trivia) if len(trivia) > 0 else []
        fd.leading_comments = list(comments) if len(comments) > 0 else []

    return fd, end_ln


def _parse_class_def(
    ctx: ParseContext,
    lines: list[str],
    start_ln: int,
    cls_name: str,
    trivia: list[TriviaNode],
    comments: list[str],
) -> tuple[ClassDef, int]:
    """クラス定義をパースする。"""
    block_lines, end_ln = _collect_block(lines, start_ln + 1, 0)
    name_types: dict[str, str] = {}
    body_stmts = _parse_block_lines(ctx, block_lines, name_types, cls_name)

    # Collect field types from annotated assignments
    field_types: dict[str, str] = {}
    for stmt in body_stmts:
        if isinstance(stmt, AnnAssign):
            if isinstance(stmt.target, Name):
                field_types[stmt.target.id] = stmt.annotation

    end_lineno = end_ln
    end_col = 0
    if len(block_lines) > 0:
        for bl in reversed(block_lines):
            if bl.strip() != "":
                end_col = len(bl.rstrip())
                break
        end_lineno = start_ln + len(block_lines)

    span = make_span(start_ln + 1, 0, end_lineno, end_col)

    cd = ClassDef(
        source_span=span,
        name=cls_name,
        original_name=cls_name,
        base=None,
        body=body_stmts,
        dataclass_flag=False,
        field_types=field_types,
        class_storage_hint="value",
    )
    if len(trivia) > 0 or len(comments) > 0:
        cd.leading_trivia = list(trivia) if len(trivia) > 0 else []
        cd.leading_comments = list(comments) if len(comments) > 0 else []

    return cd, end_ln


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
    stmts: list[Stmt] = []
    i = 0
    total = len(block_lines)
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
        # Calculate absolute line number
        # We need to figure out what line this is in the original file
        # For now, use a heuristic based on source_span from parent context
        abs_ln = _find_abs_line(ctx.lines, ln, 0)

        # return statement
        if s_clean.startswith("return "):
            expr_text = s_clean[7:].strip()
            expr = _parse_expr_text(ctx, expr_text, abs_ln, indent + 7, name_types)
            span = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
            stmt: Stmt = Return(source_span=span, value=expr)
            stmts.append(stmt)
            i += 1
            pending_trivia = []
            pending_comments = []
            continue

        # pass
        if s_clean == "pass":
            span = make_span(abs_ln, indent, abs_ln, indent + 4)
            stmts.append(Pass(source_span=span))
            i += 1
            pending_trivia = []
            pending_comments = []
            continue

        # raise
        if s_clean.startswith("raise "):
            expr_text = s_clean[6:].strip()
            expr = _parse_expr_text(ctx, expr_text, abs_ln, indent + 6, name_types)
            span = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
            stmts.append(Raise(source_span=span, exc=expr, cause=None))
            i += 1
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
            value = _parse_expr_text(ctx, value_text, abs_ln, indent + s_clean.index("=") + 2, name_types)
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

        # Augmented assignment: x += value
        target_text, op_text, value_text = _parse_aug_assign(s_clean)
        if target_text != "":
            op_map: dict[str, str] = {
                "+=": "Add", "-=": "Sub", "*=": "Mult", "/=": "Div",
                "%=": "Mod", "//=": "FloorDiv", "**=": "Pow",
                "&=": "BitAnd", "|=": "BitOr", "^=": "BitXor",
                "<<=": "LShift", ">>=": "RShift",
            }
            target = _parse_expr_text(ctx, target_text, abs_ln, indent, name_types)
            value = _parse_expr_text(ctx, value_text, abs_ln, indent + len(target_text) + len(op_text) + 2, name_types)
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

        # Simple assignment: x = value
        target_text, value_text = _parse_simple_assign(s_clean)
        if target_text != "":
            # Check it's not a comparison or augmented op
            if not target_text.endswith(("!", "<", ">", "+", "-", "*", "/", "%", "&", "|", "^")):
                target = _parse_expr_text(ctx, target_text, abs_ln, indent, name_types)
                value = _parse_expr_text(ctx, value_text, abs_ln, indent + len(target_text) + 3, name_types)
                # Infer type from value
                val_type = _get_resolved_type(value)
                is_declare = isinstance(target, Name) and target.id not in name_types
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
    """ブロック行の絶対行番号を探す。"""
    stripped = target_line.rstrip()
    for i in range(len(all_lines)):
        if all_lines[i].rstrip() == stripped:
            return i + 1
    return hint + 1


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
    span = make_span(line, col, line, col + len(name))
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

    span = make_span(abs_ln, indent, end_ln, end_col)

    # Check if it's range()
    range_args_text = _parse_range_call(iter_text)
    if range_args_text is not None:
        range_args = _split_type_args_outer(range_args_text)
        name_types[target_name] = "int64"
        target = _make_name_expr(target_name, "int64", abs_ln, indent + 4, ctx)
        start_expr: Expr
        stop_expr: Expr
        step_expr: Expr
        if len(range_args) == 1:
            start_expr = Constant(base=ExprBase(source_span=NULL_SPAN, resolved_type="int64", casts=[], borrow_kind="value", repr_text="0"), value=0)
            stop_expr = _parse_expr_text(ctx, range_args[0].strip(), abs_ln, indent, name_types)
            step_expr = Constant(base=ExprBase(source_span=NULL_SPAN, resolved_type="int64", casts=[], borrow_kind="value", repr_text="1"), value=1)
        elif len(range_args) == 2:
            start_expr = _parse_expr_text(ctx, range_args[0].strip(), abs_ln, indent, name_types)
            stop_expr = _parse_expr_text(ctx, range_args[1].strip(), abs_ln, indent, name_types)
            step_expr = Constant(base=ExprBase(source_span=NULL_SPAN, resolved_type="int64", casts=[], borrow_kind="value", repr_text="1"), value=1)
        else:
            start_expr = _parse_expr_text(ctx, range_args[0].strip(), abs_ln, indent, name_types)
            stop_expr = _parse_expr_text(ctx, range_args[1].strip(), abs_ln, indent, name_types)
            step_expr = _parse_expr_text(ctx, range_args[2].strip(), abs_ln, indent, name_types)

        fr = ForRange(
            source_span=span,
            target=target,
            target_type="int64",
            start=start_expr,
            stop=stop_expr,
            step=step_expr,
            body=body_stmts,
            orelse=[],
            range_mode="half_open",
        )
        if len(trivia) > 0:
            fr.leading_trivia = list(trivia)
        if len(comments) > 0:
            fr.leading_comments = list(comments)
        return fr, end_i

    # General for loop
    iter_expr = _parse_expr_text(ctx, iter_text, abs_ln, indent, name_types)
    target = _make_name_expr(target_name, "unknown", abs_ln, indent + 4, ctx)
    for_stmt = For(
        source_span=span,
        target=target,
        target_type="unknown",
        iter_expr=iter_expr,
        iter_element_type="unknown",
        iter_mode="iter",
        iter_source_type="unknown",
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
    test = _parse_expr_text(ctx, cond_text, abs_ln, indent + 6, name_types)

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
    test = _parse_expr_text(ctx, cond_text, abs_ln, indent + 3, name_types)

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
    test = _parse_expr_text(ctx, cond_text, abs_ln, indent + 5, name_types)

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


# ---------------------------------------------------------------------------
# Postprocessing + meta building
# ---------------------------------------------------------------------------

def _postprocess(ctx: ParseContext, body_items: list[Stmt]) -> None:
    """Phase 3: 後処理（暗黙 builtin import 追加等）。"""
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
        rb["source_module_id"] = mod_id
        rb["source_export_name"] = binding.get("export_name", "")
        rb["source_binding_kind"] = binding.get("binding_kind", "")
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
