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

from pytra.std import re, json

from toolchain.parse.py.source_span import SourceSpan, NULL_SPAN, make_span
from toolchain.parse.py.nodes import (
    JsonVal,
    # Trivia
    TriviaBlank, TriviaComment, JsonVal,
    # Import
    ImportAlias,
    # Semantic
    Keyword, Comprehension, DictEntry,
    # Expressions
    ExprBase, Name, Constant, BinOp, UnaryOp, BoolOp, Compare,
    Call, Attribute, Subscript, SliceExpr, IfExp, ListExpr, TupleExpr,
    SetExpr, DictExpr, ListComp, SetComp, DictComp, JoinedStr, FStringText, FormattedValue,
    LambdaExpr, LambdaArg, Starred, JsonVal, expr_to_jv, stmt_to_jv,
    # Statements
    Import, ImportFrom, AnnAssign, Assign, AugAssign, ExprStmt, Swap, Return, Yield, Raise, Pass, Try, ExceptHandler,
    If, For, While, With, FunctionDef, ClassDef, TypeAlias, JsonVal,
    # Module
    Module,
)
from toolchain.parse.py.type_resolver import default_type_aliases
# type_resolver は EAST1 では不要 (型正規化は resolve の責務)


# ---------------------------------------------------------------------------
# Parse context (関数引数で渡す、グローバル可変状態禁止 §5.5)
# ---------------------------------------------------------------------------

@dataclass
class ParseContext:
    """パーサーの状態。全て関数引数で渡す。"""
    filename: str
    lines: list[str]
    fn_returns: dict[str, str]  # 関数名 → 戻り値型注釈 (ソースのまま)
    class_names: dict[str, bool]  # 定義されたクラス名
    import_symbols: dict[str, dict[str, str]]
    import_modules: dict[str, str]
    import_bindings: list[dict[str, JsonVal]]
    qualified_refs: list[dict[str, JsonVal]]
    type_aliases: dict[str, str] = field(default_factory=default_type_aliases)


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



def _parse_extern_kwargs(text: str) -> Optional[dict[str, str]]:
    """extern_fn/extern_var/extern_class のキーワード引数を抽出する。
    例: 'module="pytra.core", symbol="len", tag="core.len"'
    → {"module": "pytra.core", "symbol": "len", "tag": "core.len"}
    """
    result: dict[str, str] = {}
    for raw_part in text.split(","):
        part = raw_part.strip()
        if "=" not in part:
            continue
        eq = part.index("=")
        key = part[:eq].strip()
        val = part[eq + 1:].strip()
        # Strip quotes
        if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
            val = val[1:-1]
        elif len(val) >= 2 and val[0] == "'" and val[-1] == "'":
            val = val[1:-1]
        result[key] = val
    if "module" in result and "symbol" in result and "tag" in result:
        return result
    return None


def _parse_extern_v2_decorator(s: str) -> Optional[dict[str, str]]:
    """@extern(...)/@extern_fn(...)/@extern_class(...) からキーワード引数を抽出。"""
    for prefix in ["@extern(", "@extern_fn(", "@extern_class("]:
        if s.startswith(prefix) and s.endswith(")"):
            inner = s[len(prefix):-1]
            return _parse_extern_kwargs(inner)
    return None


def _parse_runtime_decorator(s: str) -> tuple[str, str, str]:
    """@runtime("runtime_ns") または @runtime("runtime_ns", symbol="...", tag="...") をパース。
    成功時は (runtime_ns, symbol_override, tag_override)。失敗時は ("", "", "")。
    """
    if not s.startswith("@runtime(") or not s.endswith(")"):
        return "", "", ""
    inner = s[len("@runtime("):-1].strip()
    # First arg must be a quoted runtime_ns string
    if not inner:
        return "", "", ""
    quote = inner[0]
    if quote != '"' and quote != "'":
        return "", "", ""
    end_quote = -1
    qi = 1
    while qi < len(inner):
        if inner[qi] == quote:
            end_quote = qi
            break
        qi += 1
    if end_quote < 0:
        return "", "", ""
    runtime_ns = inner[1:end_quote]
    if runtime_ns == "":
        return "", "", ""
    rest = inner[end_quote + 1:].strip()
    symbol_override = ""
    tag_override = ""
    if rest.startswith(","):
        for raw_part in rest[1:].split(","):
            part = raw_part.strip()
            if "=" not in part:
                continue
            eq = part.index("=")
            key = part[:eq].strip()
            val = part[eq + 1:].strip()
            if len(val) >= 2 and val[0] in ('"', "'") and val[-1] == val[0]:
                val = val[1:-1]
            if key == "symbol":
                symbol_override = val
            elif key == "tag":
                tag_override = val
    return runtime_ns, symbol_override, tag_override


def _runtime_fn_extern_v2(runtime_ns: str, fn_name: str, symbol_override: str, tag_override: str) -> dict[str, str]:
    symbol = symbol_override if symbol_override != "" else fn_name
    tag = tag_override if tag_override != "" else "stdlib.fn." + fn_name
    return {"module": runtime_ns, "symbol": symbol, "tag": tag}


def _runtime_class_extern_v2(runtime_ns: str, class_name: str) -> dict[str, str]:
    return {"module": runtime_ns + "." + class_name, "symbol": class_name, "tag": "container." + class_name}


def _runtime_method_tag(method_name: str) -> str:
    if method_name.startswith("__") and method_name.endswith("__") and len(method_name) > 4:
        return "dunder." + method_name[2:-2]
    return "stdlib.method." + method_name


def _runtime_method_extern_v2(runtime_ns: str, class_name: str, method_name: str) -> dict[str, str]:
    return {"module": runtime_ns + "." + class_name, "symbol": class_name + "." + method_name, "tag": _runtime_method_tag(method_name), "kind": "method"}


def _parse_extern_var_call(value_text: str, var_name: str = "") -> Optional[dict[str, str]]:
    """extern_var(module=..., symbol=..., tag=...) または runtime_var("runtime_ns") を解析。"""
    vt = value_text.strip()
    if vt.startswith("extern_var(") and vt.endswith(")"):
        inner = vt[len("extern_var("):-1]
        return _parse_extern_kwargs(inner)
    if vt.startswith("runtime_var(") and vt.endswith(")"):
        inner = vt[len("runtime_var("):-1].strip()
        if len(inner) >= 2 and inner[0] in ('"', "'") and inner[-1] == inner[0]:
            runtime_ns = inner[1:-1]
            if runtime_ns != "" and var_name != "":
                return {"module": runtime_ns, "symbol": var_name, "tag": "stdlib.symbol." + var_name}
    return None


def _decorator_text(s: str) -> str:
    text = s.strip()
    if text.startswith("@"):
        return text[1:].strip()
    return text


def _parse_from_import(s: str) -> tuple[str, str]:
    """'from MOD import NAMES' をパースして (module, names_text) を返す。失敗時は ("", "")。"""
    m = re.match(r"^from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+import\s+(.+)$", s)
    if m is None:
        return "", ""
    names_text = re.strip_group(m, 2)
    while names_text.startswith("(") and names_text.endswith(")"):
        names_text = names_text[1:-1].strip()
    if names_text.endswith(","):
        names_text = names_text[:-1].strip()
    return re.strip_group(m, 1), names_text


def _parse_def_header(s: str) -> tuple[str, str, str]:
    """'def NAME(ARGS) -> RET:' をパース。(name, args, ret)。失敗は ("", "", "")。
    ワンライナー 'def NAME(ARGS) -> RET: ...' にも対応。"""
    # Strip inline body (e.g., ": ..." or ": pass")
    clean = s
    if ": ..." in clean:
        clean = clean[:clean.index(": ...") + 1]
    elif ": pass" in clean:
        clean = clean[:clean.index(": pass") + 1]
    m = re.match(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\((.*)\)\s*(?:->\s*(.+)\s*)?:\s*$", clean)
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
    """'NAME: TYPE = VALUE' or 'self.attr: TYPE = VALUE' をパース。失敗時は ("", "", "")。"""
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_.]*)\s*:\s*([^=]+?)\s*=\s*(.+)$", s)
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
    """simple assignment をパース。失敗時は ("", "")。
    self.attr = value や name[idx] = value も対応。"""
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_.]*(?:\[[^\]]*\])?)\s*=\s*(.+)$", s)
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


def _parse_range_call(s: str) -> Optional[str]:
    """'range(ARGS)' をパース。ARGS 部分を返す。range でなければ None。"""
    s = s.strip()
    if not s.startswith("range("):
        return None
    if not s.endswith(")"):
        return None
    return s[6:-1]


def _split_header_inline_suite(s: str) -> tuple[str, str]:
    """Split `if cond: stmt` style headers into (`if cond:`, `stmt`).

    Only the first top-level colon counts; colons inside strings or nested
    delimiters are ignored.
    """
    depth = 0
    in_single = False
    in_double = False
    escaped = False
    for idx in range(len(s)):
        ch = s[idx]
        if escaped:
            escaped = False
            continue
        if ch == "\\" and (in_single or in_double):
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single or in_double:
            continue
        if ch in "([{":
            depth += 1
            continue
        if ch in ")]}":
            if depth > 0:
                depth -= 1
            continue
        if ch == ":" and depth == 0:
            return s[: idx + 1].strip(), s[idx + 1 :].strip()
    return s.strip(), ""


def _parse_inline_suite(
    ctx: ParseContext,
    inline_text: str,
    abs_ln: int,
    indent: int,
    name_types: dict[str, str],
    scope_label: str,
) -> list[JsonVal]:
    if inline_text == "":
        return []
    synthetic_line = (" " * indent) + inline_text
    synthetic_lines: list[str] = [synthetic_line]
    copied_name_types: dict[str, str] = dict(name_types)
    return _parse_block_lines(ctx, synthetic_lines, copied_name_types, scope_label, start_hint=abs_ln - 1)


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
    """式パーサー。トークン列を走査して JsonVal ノードを生成する。"""
    tokens: list[Token]
    pos: int
    source_line: int
    line_col_offset: int
    source_text: str
    source_line_text: str  # 元の行テキスト全体 (span 計算の基準)
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

    def _abs_col(self, local_pos: int) -> int:
        """ローカル位置 → 絶対 col。source_line_text 内でトークンテキストを検索。"""
        return self.line_col_offset + local_pos

    def _span(self, local_start: int, local_end: int) -> SourceSpan:
        """ローカル位置 → 絶対位置の SourceSpan を返す。"""
        repr_text = self.source_text[local_start:local_end]
        abs_start = self._abs_col(local_start)
        abs_end = self._abs_col(local_end)
        # span 補正は行わない (line_col_offset + local_start をそのまま使用)
        return make_span(self.source_line, abs_start, self.source_line, abs_end)

    def _base(self, local_start: int, local_end: int) -> ExprBase:
        """ExprBase を生成する。start/end は式テキスト内のローカル位置。"""
        return ExprBase(source_span=self._span(local_start, local_end), repr_text=self.source_text[local_start:local_end])

    def _to_local(self, abs_col: int) -> int:
        """絶対 col → ローカル位置に逆算する。"""
        return abs_col - self.line_col_offset

    def _child_local_start(self, child: JsonVal) -> int:
        """子ノードのローカル開始位置。"""
        return self._to_local(_expr_col(child))

    def _child_local_end(self, child: JsonVal) -> int:
        """子ノードのローカル終了位置。"""
        return self._to_local(_expr_end_col(child))

    # --- Precedence climbing ---

    def parse_expr(self) -> JsonVal:
        if self.peek().value == "lambda":
            return self._parse_lambda()
        return self._parse_ternary()

    def _parse_lambda(self) -> LambdaExpr:
        """lambda args: body"""
        tok = self.advance()  # consume 'lambda'
        start = tok.start
        # Parse parameter list until ':'
        lambda_args: list[LambdaArg] = []
        while self.peek().value != ":" and self.peek().kind != "EOF":
            if self.peek().kind == "NAME":
                pname = self.advance().value
                default_expr: JsonVal = None
                if self.peek().value == "=":
                    self.advance()
                    # Parse default value (stop at , or :)
                    default_expr = self._parse_comp_iter()
                lambda_args.append(LambdaArg(name=pname, default_expr=default_expr))
            elif self.peek().value == ",":
                self.advance()
            else:
                break
        self.expect("OP", ":")
        body = self._parse_ternary()
        end = self._child_local_end(body)
        base = self._base(start, end)
        return LambdaExpr(base=base, args=lambda_args, body=body, return_type="unknown")

    def _parse_ternary(self) -> JsonVal:
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
            base = self._base(start, end)
            return IfExp(base=base, test=test, body=body, orelse=orelse)
        return body

    def _parse_or(self) -> JsonVal:
        left = self._parse_and()
        if self.peek().value != "or":
            return left
        values: list[JsonVal] = [left]
        while self.peek().value == "or":
            self.advance()
            values.append(self._parse_and())
        start = self._child_local_start(values[0])
        end = self._child_local_end(values[-1])
        base = self._base(start, end)
        return BoolOp(base=base, op="Or", values=values)

    def _parse_and(self) -> JsonVal:
        left = self._parse_not()
        if self.peek().value != "and":
            return left
        values: list[JsonVal] = [left]
        while self.peek().value == "and":
            self.advance()
            values.append(self._parse_not())
        start = self._child_local_start(values[0])
        end = self._child_local_end(values[-1])
        base = self._base(start, end)
        return BoolOp(base=base, op="And", values=values)

    def _parse_not(self) -> JsonVal:
        if self.peek().value == "not":
            tok = self.advance()
            operand = self._parse_not()
            end = self._child_local_end(operand)
            base = self._base(tok.start, end)
            return UnaryOp(base=base, op="Not", operand=operand)
        return self._parse_compare()

    def _parse_compare(self) -> JsonVal:
        left = self._parse_bitor()
        ops: list[str] = []
        comparators: list[JsonVal] = []
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
            base = self._base(start, end)
            return Compare(base=base, left=left, ops=ops, comparators=comparators)
        return left

    def _parse_bitor(self) -> JsonVal:
        left = self._parse_bitxor()
        while self.peek().value == "|":
            self.advance()
            right = self._parse_bitxor()
            start = self._child_local_start(left)
            end = self._child_local_end(right)
            base = self._base(start, end)
            left = BinOp(base=base, left=left, op="BitOr", right=right)
        return left

    def _parse_bitxor(self) -> JsonVal:
        left = self._parse_bitand()
        while self.peek().value == "^":
            self.advance()
            right = self._parse_bitand()
            start = self._child_local_start(left)
            end = self._child_local_end(right)
            base = self._base(start, end)
            left = BinOp(base=base, left=left, op="BitXor", right=right)
        return left

    def _parse_bitand(self) -> JsonVal:
        left = self._parse_shift()
        while self.peek().value == "&":
            self.advance()
            right = self._parse_shift()
            start = self._child_local_start(left)
            end = self._child_local_end(right)
            base = self._base(start, end)
            left = BinOp(base=base, left=left, op="BitAnd", right=right)
        return left

    def _parse_shift(self) -> JsonVal:
        left = self._parse_addsub()
        while self.peek().value == "<<" or self.peek().value == ">>":
            op_tok = self.advance()
            right = self._parse_addsub()
            op_name = "LShift" if op_tok.value == "<<" else "RShift"
            start = self._child_local_start(left)
            end = self._child_local_end(right)
            base = self._base(start, end)
            left = BinOp(base=base, left=left, op=op_name, right=right)
        return left

    def _parse_addsub(self) -> JsonVal:
        left = self._parse_muldiv()
        while self.peek().value == "+" or self.peek().value == "-":
            op_tok = self.advance()
            right = self._parse_muldiv()
            op_name = "Add" if op_tok.value == "+" else "Sub"
            start = self._child_local_start(left)
            end = self._child_local_end(right)
            base = self._base(start, end)
            left = BinOp(base=base, left=left, op=op_name, right=right)
        return left

    def _parse_muldiv(self) -> JsonVal:
        left = self._parse_unary()
        while self.peek().value in ("*", "/", "//", "%"):
            op_tok = self.advance()
            right = self._parse_unary()
            op_map: dict[str, str] = {"*": "Mult", "/": "Div", "//": "FloorDiv", "%": "Mod"}
            op_name = op_map.get(op_tok.value, op_tok.value)
            start = self._child_local_start(left)
            end = self._child_local_end(right)
            base = self._base(start, end)
            # Numeric promotion casts
            left = BinOp(base=base, left=left, op=op_name, right=right)
        return left

    def _parse_unary(self) -> JsonVal:
        tok = self.peek()
        if tok.value == "-" and tok.kind == "OP":
            self.advance()
            operand = self._parse_unary()
            end = self._child_local_end(operand)
            base = self._base(tok.start, end)
            return UnaryOp(base=base, op="USub", operand=operand)
        if tok.value == "+" and tok.kind == "OP":
            self.advance()
            operand = self._parse_unary()
            end = self._child_local_end(operand)
            base = self._base(tok.start, end)
            return UnaryOp(base=base, op="UAdd", operand=operand)
        if tok.value == "~" and tok.kind == "OP":
            self.advance()
            operand = self._parse_unary()
            end = self._child_local_end(operand)
            base = self._base(tok.start, end)
            return UnaryOp(base=base, op="Invert", operand=operand)
        return self._parse_power()

    def _parse_power(self) -> JsonVal:
        left = self._parse_postfix()
        if self.peek().value == "**":
            self.advance()
            right = self._parse_unary()  # right-associative
            start = self._child_local_start(left)
            end = self._child_local_end(right)
            base = self._base(start, end)
            left = BinOp(base=base, left=left, op="Pow", right=right)
        return left

    def _parse_postfix(self) -> JsonVal:
        """後置演算子: .attr, [index], (call)"""
        expr = self._parse_primary()
        while True:
            tok = self.peek()
            if tok.value == ".":
                self.advance()
                attr_tok = self.advance()
                end = attr_tok.end
                base = self._base(self._child_local_start(expr), end)
                expr = Attribute(base=base, value=expr, attr=attr_tok.value)
            elif tok.value == "[":
                self.advance()
                index = self._parse_subscript_index()
                self.expect("OP", "]")
                end_tok = self.tokens[self.pos - 1]
                base = self._base(self._child_local_start(expr), end_tok.end)
                sub = Subscript(base=base, value=expr, slice_expr=index)
                # Slice の場合、lower/upper を Subscript に直接設定 (lowered_kind は resolve の責務)
                index_node = expr_to_jv(index)
                if str(index_node.get("kind", "")) == "Slice":
                    sub.is_slice = True
                    sub.lower = index_node.get("lower", None)
                    sub.upper = index_node.get("upper", None)
                expr = sub
            elif tok.value == "(":
                expr = self._parse_call(expr)
            else:
                break
        return expr

    def _parse_call(self, func: JsonVal) -> Call:
        """関数呼び出し。"""
        self.expect("OP", "(")
        args: list[JsonVal] = []
        keywords: list[Keyword] = []
        if self.peek().value != ")":
            while True:
                # Check for keyword argument: name=value
                if self.peek().kind == "NAME" and self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].value == "=":
                    kw_name = self.advance().value
                    self.advance()  # skip =
                    kw_value = self.parse_expr()
                    keywords.append(Keyword(arg=kw_name, value_node=kw_value))
                elif self.peek().value == "**":
                    self.advance()
                    kw_value = self.parse_expr()
                    keywords.append(Keyword(arg=None, value_node=kw_value))
                elif self.peek().value == "*":
                    # *args — starred argument
                    star_tok = self.advance()
                    inner_expr = self.parse_expr()
                    inner_start = self._child_local_start(inner_expr)
                    inner_end = self._child_local_end(inner_expr)
                    star_repr = "*" + self.source_text[inner_start:inner_end]
                    star_base = self._base(star_tok.start, inner_end)
                    star_base.repr_text = star_repr
                    args.append(Starred(base=star_base, value=inner_expr))
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
                            ifs: list[JsonVal] = []
                            while self.peek().value == "if":
                                self.advance()
                                ifs.append(self._parse_comp_iter())
                            gens.append(Comprehension(target=target, iter_expr=iter_expr, ifs=ifs, is_async=False))
                        # Wrap as ListComp (generator)
                        gen_start = self._child_local_start(arg_expr)
                        gen_end = self.tokens[self.pos - 1].end
                        gen_repr = self.source_text[gen_start:gen_end]
                        gen_base = self._base(gen_start, gen_end)
                        gen_base.repr_text = gen_repr
                        arg_expr = ListComp(base=gen_base, elt=arg_expr, generators=gens)
                    args.append(arg_expr)
                if self.peek().value != ",":
                    break
                self.advance()  # skip comma
                if self.peek().value == ")":
                    break  # trailing comma
        self.expect("OP", ")")
        end_tok = self.tokens[self.pos - 1]
        start = self._child_local_start(func)
        end = end_tok.end
        # Resolve call type
        func_name = _get_func_name(func)
        # Attribute call (Class.method / obj.method): fn_returns を使わない
        base = self._base(start, end)
        call = Call(base=base, func=func, args=args, keywords=keywords)
        return call

    def _parse_primary(self) -> JsonVal:
        """基本式: リテラル、名前、括弧、リスト、タプル、辞書。"""
        tok = self.peek()

        # Integer literal
        if tok.kind == "INT":
            self.advance()
            value_str = tok.value.replace("_", "")
            if value_str.startswith("0x") or value_str.startswith("0X"):
                val = _parse_int_base(value_str[2:], 16)
            elif value_str.startswith("0b") or value_str.startswith("0B"):
                val = _parse_int_base(value_str[2:], 2)
            elif value_str.startswith("0o") or value_str.startswith("0O"):
                val = _parse_int_base(value_str[2:], 8)
            else:
                val = _parse_int_base(value_str, 10)
            base = self._base(tok.start, tok.end)
            return Constant(base=base, value=val)

        # Float literal
        if tok.kind == "FLOAT":
            self.advance()
            val_f = float(tok.value.replace("_", ""))
            base = self._base(tok.start, tok.end)
            return Constant(base=base, value=val_f)

        # String literal
        if tok.kind == "STR":
            self.advance()
            raw = tok.value
            # Strip string prefix (r, b, f, rb, br, rf, fr)
            is_raw = False
            is_fstring = False
            prefix_end = 0
            while prefix_end < len(raw) and raw[prefix_end] in "rRbBfF":
                if raw[prefix_end] in "rR":
                    is_raw = True
                if raw[prefix_end] in "fF":
                    is_fstring = True
                prefix_end += 1
            stripped = raw[prefix_end:]
            # Evaluate string value
            if stripped.startswith('"""') or stripped.startswith("'''"):
                inner = stripped[3:-3]
            elif stripped.startswith('"'):
                inner = stripped[1:-1]
            elif stripped.startswith("'"):
                inner = stripped[1:-1]
            else:
                inner = stripped
            # Escape handling (raw strings don't process escapes)
            if is_raw:
                val_s = inner
            else:
                val_s = _unescape_string(inner)
            base = self._base(tok.start, tok.end)
            # f-string → JoinedStr
            if is_fstring:
                fstr_span: SourceSpan = self._span(tok.start, tok.end)
                values = _parse_fstring_parts(inner, self.source_line, self.line_col_offset + tok.start, self.ctx, fstr_span)
                return JoinedStr(base=base, values=values)
            return Constant(base=base, value=val_s)

        # Name / keyword literals
        if tok.kind == "NAME":
            if tok.value == "True":
                self.advance()
                base = self._base(tok.start, tok.end)
                return Constant(base=base, value=True)
            if tok.value == "False":
                self.advance()
                base = self._base(tok.start, tok.end)
                return Constant(base=base, value=False)
            if tok.value == "None":
                self.advance()
                base = self._base(tok.start, tok.end)
                return Constant(base=base, value=None)  # type: ignore
            self.advance()
            # Look up type from context
            resolved = self.name_types.get(tok.value, "unknown")
            # RHS reference: readonly_ref, no type_expr
            # (LHS targets are created separately via _make_name_expr)
            borrow = "readonly_ref" if resolved != "unknown" else "value"
            base = self._base(tok.start, tok.end)
            name = Name(base=base, id=tok.value)
            # RHS names do NOT get type_expr (only LHS declaration targets do)
            return name

        # Parenthesized expression or tuple
        if tok.value == "(":
            self.advance()
            if self.peek().value == ")":
                self.advance()
                # Empty tuple
                base = self._base(tok.start, self.tokens[self.pos - 1].end)
                empty_elements: list[JsonVal] = []
                return TupleExpr(base=base, elements=empty_elements)
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
                    ifs: list[JsonVal] = []
                    while self.peek().value == "if":
                        self.advance()
                        ifs.append(self._parse_comp_iter())
                    gens.append(Comprehension(target=target, iter_expr=iter_expr, ifs=ifs, is_async=False))
                self.expect("OP", ")")
                end_tok = self.tokens[self.pos - 1]
                base = self._base(tok.start, end_tok.end)
                return ListComp(base=base, elt=first, generators=gens)
            if self.peek().value == ",":
                # Tuple
                elements: list[JsonVal] = [first]
                while self.peek().value == ",":
                    self.advance()
                    if self.peek().value == ")":
                        break
                    elements.append(self.parse_expr())
                self.expect("OP", ")")
                end_tok = self.tokens[self.pos - 1]
                # Tuple 型推論: tuple[elem_type1,elem_type2,...]
                base = self._base(tok.start, end_tok.end)
                return TupleExpr(base=base, elements=elements)
            self.expect("OP", ")")
            return first

        # List literal or comprehension
        if tok.value == "[":
            return self._parse_list_or_listcomp()

        # Dict literal
        if tok.value == "{":
            return self._parse_dict_or_set()

        # Ellipsis literal: ...
        if tok.value == "." and self.pos + 2 < len(self.tokens) and self.tokens[self.pos + 1].value == "." and self.tokens[self.pos + 2].value == ".":
            self.advance()  # first .
            self.advance()  # second .
            self.advance()  # third .
            base = self._base(tok.start, self.tokens[self.pos - 1].end)
            return Constant(base=base, value=True)  # Ellipsis → placeholder constant

        raise ValueError("unexpected token in expression: " + tok.value + " at pos " + str(tok.start))

    def _parse_list_or_listcomp(self) -> JsonVal:
        open_tok = self.advance()  # [
        if self.peek().value == "]":
            close_tok = self.advance()
            base = self._base(open_tok.start, close_tok.end)
            empty_elements: list[JsonVal] = []
            return ListExpr(base=base, elements=empty_elements)
        first = self.parse_expr()
        # Check for list comprehension
        if self.peek().value == "for":
            return self._parse_listcomp_tail(open_tok, first)
        # Regular list
        elements: list[JsonVal] = [first]
        while self.peek().value == ",":
            self.advance()
            if self.peek().value == "]":
                break
            elements.append(self.parse_expr())
        self.expect("OP", "]")
        end_tok = self.tokens[self.pos - 1]
        base = self._base(open_tok.start, end_tok.end)
        return ListExpr(base=base, elements=elements)

    def _parse_listcomp_tail(self, open_tok: Token, elt: JsonVal) -> ListComp:
        gens: list[Comprehension] = []
        while self.peek().value == "for":
            self.advance()  # consume 'for'
            # target は単純な Name または Tuple（'in' で止める必要がある）
            target = self._parse_comp_target()
            self.expect("NAME", "in")
            # iter_expr は 'if', 'for', ']' で止める
            iter_expr = self._parse_comp_iter()
            # EAST1: 型推論しない
            ifs: list[JsonVal] = []
            while self.peek().value == "if":
                self.advance()
                ifs.append(self._parse_comp_iter())
            gens.append(Comprehension(target=target, iter_expr=iter_expr, ifs=ifs, is_async=False))
        self.expect("OP", "]")
        end_tok = self.tokens[self.pos - 1]
        base = self._base(open_tok.start, end_tok.end)
        return ListComp(base=base, elt=elt, generators=gens)

    def _parse_comp_target(self) -> JsonVal:
        """comprehension の target をパース。'in' キーワードで止める。"""
        tok = self.peek()
        if tok.kind == "NAME" and tok.value != "in":
            self.advance()
            base = self._base(tok.start, tok.end)
            first = Name(base=base, id=tok.value)
            # Check for tuple target: x, y
            if self.peek().value == ",":
                elements: list[JsonVal] = [first]
                while self.peek().value == ",":
                    self.advance()
                    if self.peek().value == "in":
                        break
                    next_tok = self.advance()
                    nbase = self._base(next_tok.start, next_tok.end)
                    elements.append(Name(base=nbase, id=next_tok.value))
                tbase = self._base(tok.start, self.tokens[self.pos - 1].end)
                return TupleExpr(base=tbase, elements=elements)
            return first
        return self.parse_expr()

    def _parse_comp_iter(self) -> JsonVal:
        """comprehension の iter/if 式をパース。'for', 'if', ']', '}', ')' で止める。"""
        # 通常の式パースを行うが、トップレベルの 'for', 'if' で止める
        # これは _parse_ternary の 'if' と衝突するため、or レベルまでパースする
        return self._parse_or()

    def _parse_comprehension_generators(self) -> list[Comprehension]:
        """comprehension の generator 部分をパース (for ... in ... if ...)。"""
        gens: list[Comprehension] = []
        while self.peek().value == "for":
            self.advance()
            target = self._parse_comp_target()
            self.expect("NAME", "in")
            iter_expr = self._parse_comp_iter()
            ifs: list[JsonVal] = []
            while self.peek().value == "if":
                self.advance()
                ifs.append(self._parse_comp_iter())
            gens.append(Comprehension(target=target, iter_expr=iter_expr, ifs=ifs, is_async=False))
        return gens

    def _parse_subscript_index(self) -> JsonVal:
        """subscript の index をパース。`:` が来たら SliceExpr を生成。"""
        # Check for initial `:` (e.g., a[:3])
        if self.peek().value == ":":
            return self._parse_slice(None)
        first = self.parse_expr()
        if self.peek().value == ",":
            elements: list[JsonVal] = [first]
            while self.peek().value == ",":
                self.advance()
                if self.peek().value == "]":
                    break
                elements.append(self.parse_expr())
            if len(elements) > 1:
                start = self._child_local_start(elements[0])
                end = self._child_local_end(elements[-1])
                return TupleExpr(base=self._base(start, end), elements=elements)
        # Check for slice
        if self.peek().value == ":":
            return self._parse_slice(first)
        return first

    def _parse_slice(self, lower: JsonVal) -> SliceExpr:
        """slice 式をパース。`:` を消費した状態で呼ばれる。"""
        self.advance()  # consume ':'
        upper: JsonVal = None
        step: JsonVal = None
        if self.peek().value != "]" and self.peek().value != ":":
            upper = self.parse_expr()
        if self.peek().value == ":":
            self.advance()
            if self.peek().value != "]":
                step = self.parse_expr()
        return SliceExpr(lower=lower, upper=upper, step=step)

    def _parse_dict_or_set(self) -> JsonVal:
        """dict リテラル、set リテラル、dict/set comprehension をパース。"""
        open_tok = self.advance()
        if self.peek().value == "}":
            close_tok = self.advance()
            base = self._base(open_tok.start, close_tok.end)
            empty_keys: list[JsonVal] = []
            empty_values: list[JsonVal] = []
            return DictExpr(base=base, keys=empty_keys, dict_values=empty_values)
        first = self.parse_expr()
        # Dict comprehension: {k: v for ...}
        if self.peek().value == ":":
            self.advance()
            first_val = self.parse_expr()
            if self.peek().value == "for":
                gens = self._parse_comprehension_generators()
                self.expect("OP", "}")
                end_tok = self.tokens[self.pos - 1]
                base = self._base(open_tok.start, end_tok.end)
                return DictComp(base=base, key=first, value=first_val, generators=gens)
            # Regular dict
            keys: list[JsonVal] = [first]
            values: list[JsonVal] = [first_val]
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
            base = self._base(open_tok.start, end_tok.end)
            return DictExpr(base=base, keys=keys, dict_values=values, entries=entries)
        # Set literal or set comprehension
        if self.peek().value == "for":
            gens = self._parse_comprehension_generators()
            self.expect("OP", "}")
            end_tok = self.tokens[self.pos - 1]
            base = self._base(open_tok.start, end_tok.end)
            return SetComp(base=base, elt=first, generators=gens)
        # Set literal: {a, b, c}
        elements: list[JsonVal] = [first]
        while self.peek().value == ",":
            self.advance()
            if self.peek().value == "}":
                break
            elements.append(self.parse_expr())
        self.expect("OP", "}")
        end_tok = self.tokens[self.pos - 1]
        base = self._base(open_tok.start, end_tok.end)
        return SetExpr(base=base, elements=elements)


# ---------------------------------------------------------------------------
# Expression helpers
# ---------------------------------------------------------------------------

# ローカル位置追跡: ExprParser 内で _base() に渡す local_start/local_end を
# 子ノードから取得するためのユーティリティ。
# ExprBase.source_span.col = line_col_offset + local_start なので、
# local_start = col - line_col_offset で逆算する。

def _expr_col(e: JsonVal) -> int:
    """式ノードの source_span.col (絶対位置)。"""
    node = expr_to_jv(e)
    base_obj = json.JsonValue(node.get("base")).as_obj()
    if base_obj is None:
        return 0
    span_obj = json.JsonValue(base_obj.raw.get("source_span")).as_obj()
    if span_obj is None:
        return 0
    col = json.JsonValue(span_obj.raw.get("col")).as_int()
    if col is None:
        return 0
    return col


def _expr_end_col(e: JsonVal) -> int:
    """式ノードの source_span.end_col (絶対位置)。"""
    node = expr_to_jv(e)
    base_obj = json.JsonValue(node.get("base")).as_obj()
    if base_obj is None:
        return 0
    span_obj = json.JsonValue(base_obj.raw.get("source_span")).as_obj()
    if span_obj is None:
        return 0
    end_col = json.JsonValue(span_obj.raw.get("end_col")).as_int()
    if end_col is None:
        return 0
    return end_col


def _get_func_name(func: JsonVal) -> str:
    node = expr_to_jv(func)
    kind = str(node.get("kind", ""))
    if kind == "Name":
        return str(node.get("id", ""))
    if kind == "Attribute":
        return str(node.get("attr", ""))
    return ""


_KNOWN_NUMERIC_TYPES = {"int64", "float64", "bool"}
_TYPE_ONLY_IMPORT_MODULES = {"__future__", "typing", "dataclasses", "pytra.typing", "pytra.dataclasses", "pytra.enum"}
_TYPE_MODULE_VALUE_EXPORTS = {"cast"}


def _digit_value(ch: str) -> int:
    if ch >= "0" and ch <= "9":
        return ord(ch) - ord("0")
    if ch >= "a" and ch <= "f":
        return 10 + ord(ch) - ord("a")
    if ch >= "A" and ch <= "F":
        return 10 + ord(ch) - ord("A")
    return -1


def _parse_int_base(text: str, base: int) -> int:
    value = 0
    sign = 1
    i = 0
    if text.startswith("-"):
        sign = -1
        i = 1
    while i < len(text):
        digit = _digit_value(text[i])
        if digit < 0 or digit >= base:
            raise ValueError("invalid integer literal")
        value = value * base + digit
        i += 1
    return value * sign


def _leading_space_count(text: str) -> int:
    i = 0
    while i < len(text) and text[i] == " ":
        i += 1
    return i


def _alias_local(alias: ImportAlias) -> str:
    if alias.asname != "":
        return "" + alias.asname
    return "" + alias.name


def _json_obj_str(obj: dict[str, JsonVal], key: str) -> str:
    if key not in obj:
        return ""
    value = json.JsonValue(obj[key]).as_str()
    if value is None:
        return ""
    return "" + value


def _json_obj_int(obj: dict[str, JsonVal], key: str) -> int:
    if key not in obj:
        return 0
    value = json.JsonValue(obj[key]).as_int()
    if value is None:
        return 0
    return value


def _stmt_end_lineno(stmt: JsonVal) -> int:
    stmt_obj = json.JsonValue(stmt).as_obj()
    if stmt_obj is None:
        return 0
    span_obj = stmt_obj.get_obj("source_span")
    if span_obj is None:
        return 0
    return _json_obj_int(span_obj.raw, "end_lineno")


def _stmt_end_col(stmt: JsonVal) -> int:
    stmt_obj = json.JsonValue(stmt).as_obj()
    if stmt_obj is None:
        return 0
    span_obj = stmt_obj.get_obj("source_span")
    if span_obj is None:
        return 0
    return _json_obj_int(span_obj.raw, "end_col")


def _endswith_assignment_operator_prefix(text: str) -> bool:
    return (
        text.endswith("!") or text.endswith("<") or text.endswith(">") or
        text.endswith("+") or text.endswith("-") or text.endswith("*") or
        text.endswith("/") or text.endswith("%") or text.endswith("&") or
        text.endswith("|") or text.endswith("^")
    )


def _starts_with_compound_stmt_keyword(text: str) -> bool:
    return (
        text.startswith("if ") or text.startswith("elif ") or text.startswith("while ") or
        text.startswith("for ") or text.startswith("def ") or text.startswith("class ") or
        text.startswith("with ") or text.startswith("try:") or text.startswith("except ") or
        text.startswith("return ") or text.startswith("raise ")
    )


def _find_substr_from(text: str, needle: str, start: int) -> int:
    if needle == "":
        return start
    i = start
    limit = len(text) - len(needle)
    while i <= limit:
        if text[i:i + len(needle)] == needle:
            return i
        i += 1
    return -1


def _rstrip_one_char(text: str, ch: str) -> str:
    end = len(text)
    while end > 0 and text[end - 1] == ch:
        end -= 1
    return text[:end]


def _split_last_as(text: str) -> tuple[str, str]:
    marker = " as "
    marker_len = len(marker)
    last = -1
    i = 0
    while i <= len(text) - marker_len:
        if text[i:i + marker_len] == marker:
            last = i
        i += 1
    if last < 0:
        return text, ""
    return text[:last], text[last + marker_len:]


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
    # Strip BOM
    if source.startswith("\ufeff"):
        source = source[1:]
    raw_lines = source.splitlines()
    lines: list[str] = []
    for raw_line in raw_lines:
        lines.append(raw_line)
    fn_returns: dict[str, str] = {}
    class_names: dict[str, bool] = {}
    import_symbols: dict[str, dict[str, str]] = {}
    import_modules: dict[str, str] = {}
    import_bindings: list[dict[str, JsonVal]] = []
    qualified_refs: list[dict[str, JsonVal]] = []
    ctx = ParseContext(
        filename=filename,
        lines=lines,
        fn_returns=fn_returns,
        class_names=class_names,
        import_symbols=import_symbols,
        import_modules=import_modules,
        import_bindings=import_bindings,
        qualified_refs=qualified_refs,
    )

    # Phase 1: Pre-scan
    _prescan(ctx, lines)

    # Phase 2: Parse body
    body_items: list[JsonVal] = []
    main_guard_body: list[JsonVal] = []
    _parse_module_body(ctx, lines, body_items, main_guard_body)

    # Phase 3: Post-processing
    renamed_symbols: dict[str, str] = {}
    _postprocess(ctx, body_items, renamed_symbols)

    # Build meta
    meta = _build_meta(ctx, ctx.qualified_refs)

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
    for line_index in range(len(lines)):
        ln_no = line_index + 1
        ln = lines[line_index]
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
                allow_value_symbol = mod in ("typing", "pytra.typing") and name in _TYPE_MODULE_VALUE_EXPORTS
                # __future__, typing, dataclasses (+ pytra.typing, pytra.dataclasses) は
                # 通常は import_symbols に登録しないが、cast のような値レベル helper は残す。
                if mod not in _TYPE_ONLY_IMPORT_MODULES or allow_value_symbol:
                    ctx.import_symbols[local] = {"module": mod, "name": name}
            # Type alias from typing (prescan 用)
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
                ctx.fn_returns[fn_name] = ret_ann
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
    body_items: list[JsonVal],
    main_guard_body: list[JsonVal],
) -> None:
    """Phase 2: モジュール本体をパースする。"""
    ln_no = 0
    total = len(lines)
    pending_trivia: list[JsonVal] = []
    pending_comments: list[str] = []
    pending_decorators: list[str] = []
    leading_file_trivia_done = False
    pending_dataclass = False
    pending_extern_v2: dict[str, str] = {}
    pending_runtime_ns = ""
    pending_runtime_symbol = ""
    pending_runtime_tag = ""
    skip_next_blanks = False  # import/def/class 直後の空行を蓄積しないためのフラグ
    first_nonimport_done = False  # 最初の non-import body item かどうか

    while ln_no < total:
        ln = lines[ln_no]
        s = ln.strip()
        indent = _leading_space_count(ln) if s != "" else 0

        # Blank line
        if s == "":
            # ファイル冒頭コメントが既に蓄積 + import 直後でない場合のみ蓄積
            if (len(pending_comments) > 0 or leading_file_trivia_done) and not skip_next_blanks:
                pending_trivia.append(TriviaBlank(count=1).to_jv())
            ln_no += 1
            continue

        # Comment line
        if s.startswith("#"):
            text = s[1:].lstrip() if len(s) > 1 else ""
            pending_trivia.append(TriviaComment(text=text).to_jv())
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
            if s_clean.startswith("@extern_method("):
                raise RuntimeError("extern_method is removed; use @runtime(...) or @extern(...)")
            if s_clean.startswith("@abi(") or s_clean == "@abi":
                raise RuntimeError("abi decorator is removed")
            pending_decorators.append(_decorator_text(s_clean))
            if s_clean == "@dataclass" or s_clean.startswith("@dataclass("):
                pending_dataclass = True
            # v2 extern decorators
            extern_v2 = _parse_extern_v2_decorator(s_clean)
            if extern_v2 is not None:
                pending_extern_v2 = extern_v2
            rt_ns, rt_sym, rt_tag = _parse_runtime_decorator(s_clean)
            if rt_ns != "":
                pending_runtime_ns = rt_ns
                pending_runtime_symbol = rt_sym
                pending_runtime_tag = rt_tag
            ln_no += 1
            continue

        # Module-level string literal (docstring)
        if (s_clean.startswith('"""') or s_clean.startswith("'''") or
            (s_clean.startswith('"') and not s_clean.startswith('"""')) or
            (s_clean.startswith("'") and not s_clean.startswith("'''"))):
            # Check if it's a standalone string (expression statement)
            expr = _parse_expr_text(ctx, s_clean, ln_no + 1, indent, {})
            span: SourceSpan = make_span(ln_no + 1, indent, ln_no + 1, indent + len(s_clean))
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
                asname = ""
                name = part
                if " as " in part:
                    split = part.split(" as ")
                    name = split[0].strip()
                    asname = split[1].strip()
                aliases.append(ImportAlias(name=name, asname=asname))
            # Skip typing / __future__ / dataclasses imports (+ pytra.typing, pytra.dataclasses)
            # ただし cast のような値レベル helper は resolve 用 metadata だけ残す。
            if mod in _TYPE_ONLY_IMPORT_MODULES:
                if mod in ("typing", "pytra.typing"):
                    for alias in aliases:
                        alias_name: str = "" + alias.name
                        if alias_name not in _TYPE_MODULE_VALUE_EXPORTS:
                            continue
                        local: str = _alias_local(alias)
                        symbol_info: dict[str, str] = {}
                        symbol_info["module"] = mod
                        symbol_info["name"] = alias_name
                        ctx.import_symbols[local] = symbol_info
                        ctx.import_bindings.append(
                            {
                                "module_id": mod,
                                "export_name": alias_name,
                                "local_name": local,
                                "binding_kind": "symbol",
                                "source_file": ctx.filename,
                                "source_line": ln_no + 1,
                            }
                        )
                        ctx.qualified_refs.append(
                            {
                                "module_id": mod,
                                "symbol": alias_name,
                                "local_name": local,
                            }
                        )
                ln_no += 1
                skip_next_blanks = True
                continue
            span: SourceSpan = make_span(ln_no + 1, 0, ln_no + 1, len(ln.rstrip()))
            stmt: ImportFrom = ImportFrom(source_span=span, module=mod, names=aliases, level=0)
            body_items.append(stmt)
            # Build import binding
            for alias in aliases:
                alias_name: str = "" + alias.name
                local: str = _alias_local(alias)
                binding: dict[str, JsonVal] = {}
                binding["module_id"] = mod
                binding["export_name"] = alias_name
                binding["local_name"] = local
                binding["binding_kind"] = "symbol"
                binding["source_file"] = ctx.filename
                binding["source_line"] = ln_no + 1
                ctx.import_bindings.append(binding)
                ctx.qualified_refs.append({
                    "module_id": mod,
                    "symbol": alias_name,
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
                asname_i = ""
                name_i = part
                if " as " in part:
                    split_i = part.split(" as ")
                    name_i = split_i[0].strip()
                    asname_i = split_i[1].strip()
                imp_aliases.append(ImportAlias(name=name_i, asname=asname_i))
                # Register module import
                local_i: str = asname_i if asname_i != "" else name_i
                ctx.import_modules[local_i] = name_i
            span: SourceSpan = make_span(ln_no + 1, 0, ln_no + 1, len(ln.rstrip()))
            body_items.append(Import(source_span=span, names=imp_aliases))
            # Build import binding
            for alias in imp_aliases:
                alias_name: str = "" + alias.name
                local: str = _alias_local(alias)
                binding: dict[str, JsonVal] = {}
                binding["module_id"] = alias_name
                binding["export_name"] = ""
                binding["local_name"] = local
                binding["binding_kind"] = "module"
                binding["source_file"] = ctx.filename
                binding["source_line"] = ln_no + 1
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
                gi = _leading_space_count(gl) if gs != "" else 0
                if gs != "" and gi == 0:
                    break
                guard_lines.append(gl)
                ln_no += 1
            # Parse main guard body
            main_guard_name_types: dict[str, str] = {}
            main_guard_body.extend(
                _parse_block_lines(ctx, guard_lines, main_guard_name_types, "main")
            )
            pending_trivia = []
            pending_comments = []
            continue

        # Function def (including multi-line signatures)
        fn_name = _parse_def_name(s_clean)
        if fn_name == "" and s_clean.startswith("def "):
            # Multi-line def: merge lines until we get a complete header
            merged = s_clean
            merge_ln = ln_no + 1
            while merge_ln < total:
                next_s = lines[merge_ln].strip()
                merged = merged.rstrip() + " " + next_s
                merge_ln += 1
                if next_s.endswith(":"):
                    break
            fn_name = _parse_def_name(merged)
        if fn_name != "":
            fn_stmt, ln_no = _parse_function_def(ctx, lines, ln_no, fn_name, pending_trivia, pending_comments)
            if len(pending_decorators) > 0:
                fn_stmt.decorators = list(pending_decorators)
                pending_decorators = []
            if len(pending_extern_v2) > 0:
                ev2_meta: dict[str, JsonVal] = {}
                for ev2_key, ev2_value in pending_extern_v2.items():
                    ev2_meta[ev2_key] = ev2_value
                fn_meta: dict[str, JsonVal] = {}
                fn_meta["extern_v2"] = ev2_meta
                fn_stmt.node_meta = fn_meta
                pending_extern_v2 = {}
            elif pending_runtime_ns != "":
                runtime_ev2 = _runtime_fn_extern_v2(
                    pending_runtime_ns, fn_name, pending_runtime_symbol, pending_runtime_tag)
                runtime_ev2_meta: dict[str, JsonVal] = {}
                for ev2_key2, ev2_value2 in runtime_ev2.items():
                    runtime_ev2_meta[ev2_key2] = ev2_value2
                fn_meta2: dict[str, JsonVal] = {}
                fn_meta2["extern_v2"] = runtime_ev2_meta
                fn_stmt.node_meta = fn_meta2
                pending_runtime_ns = ""
                pending_runtime_symbol = ""
                pending_runtime_tag = ""
            body_items.append(fn_stmt)
            first_nonimport_done = True
            pending_trivia = []
            pending_comments = []
            skip_next_blanks = True
            continue

        # Class def
        cls_name = _parse_class_name(s_clean)
        if cls_name != "":
            force_cls_leading = not first_nonimport_done
            cls_stmt, ln_no = _parse_class_def(
                ctx,
                lines,
                ln_no,
                cls_name,
                pending_trivia,
                pending_comments,
                decorators=pending_decorators,
                is_dataclass=pending_dataclass,
                force_leading=force_cls_leading,
            )
            pending_decorators = []
            cls_meta: dict[str, JsonVal] = {}
            if len(pending_extern_v2) > 0:
                cls_ev2_meta: dict[str, JsonVal] = {}
                for cls_ev2_key, cls_ev2_value in pending_extern_v2.items():
                    cls_ev2_meta[cls_ev2_key] = cls_ev2_value
                cls_meta["extern_v2"] = cls_ev2_meta
                pending_extern_v2 = {}
            if pending_runtime_ns != "":
                runtime_v1: dict[str, JsonVal] = {}
                runtime_v1["schema_version"] = 1
                runtime_v1["runtime_ns"] = pending_runtime_ns
                cls_meta["runtime_v1"] = runtime_v1
                cls_runtime_ev2 = _runtime_class_extern_v2(pending_runtime_ns, cls_name)
                cls_runtime_ev2_meta: dict[str, JsonVal] = {}
                for cls_ev2_key2, cls_ev2_value2 in cls_runtime_ev2.items():
                    cls_runtime_ev2_meta[cls_ev2_key2] = cls_ev2_value2
                cls_meta["extern_v2"] = cls_runtime_ev2_meta
                pending_runtime_ns = ""
                pending_runtime_symbol = ""
                pending_runtime_tag = ""
            if len(cls_meta) > 0:
                cls_stmt.node_meta = cls_meta
            first_nonimport_done = True
            pending_dataclass = False
            body_items.append(cls_stmt)
            pending_trivia = []
            pending_comments = []
            skip_next_blanks = True
            continue

        # type alias: type Name = ...
        type_alias_m = re.match(r"^type\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", s_clean)
        if type_alias_m is not None:
            ta_name = re.strip_group(type_alias_m, 1)
            ta_value = re.strip_group(type_alias_m, 2)
            span: SourceSpan = make_span(ln_no + 1, 0, ln_no + 1, len(ln.rstrip()))
            body_items.append(TypeAlias(source_span=span, name=ta_name, value=ta_value))
            ln_no += 1
            pending_trivia = []
            pending_comments = []
            continue

        # Top-level annotated assignment: x: Type = value
        tl_var, tl_type, tl_value = _parse_ann_assign(s_clean)
        if tl_var != "":
            target = _make_attr_or_name_expr(tl_var, ln_no + 1, 0, ctx)
            val_expr = _parse_expr_text(ctx, tl_value, ln_no + 1, _find_expr_col(ctx, tl_value, ln_no + 1, 0), {})
            span: SourceSpan = make_span(ln_no + 1, 0, ln_no + 1, len(ln.rstrip()))
            ann_stmt = AnnAssign(source_span=span, target=target, annotation=tl_type, value=val_expr, declare=True)
            # Check for extern_var(...) / runtime_var(...) in value
            ev2 = _parse_extern_var_call(tl_value, tl_var)
            if ev2 is not None:
                ev2_meta: dict[str, JsonVal] = {}
                for ev2_key, ev2_value in ev2.items():
                    ev2_meta[ev2_key] = ev2_value
                ann_meta: dict[str, JsonVal] = {}
                ann_meta["extern_v2"] = ev2_meta
                ann_stmt.node_meta = ann_meta
            if len(pending_trivia) > 0:
                ann_stmt.leading_trivia = list(pending_trivia)
            if len(pending_comments) > 0:
                ann_stmt.leading_comments = list(pending_comments)
            body_items.append(ann_stmt)
            ln_no += 1
            first_nonimport_done = True
            pending_trivia = []
            pending_comments = []
            continue

        # Top-level simple assignment: x = value
        tl_target, tl_val_text = _parse_simple_assign(s_clean)
        if tl_target != "":
            target = _parse_expr_text(ctx, tl_target, ln_no + 1, 0, {})
            val_expr = _parse_expr_text(ctx, tl_val_text, ln_no + 1, _find_expr_col(ctx, tl_val_text, ln_no + 1, 0), {})
            span: SourceSpan = make_span(ln_no + 1, 0, ln_no + 1, len(ln.rstrip()))
            is_declare = str(expr_to_jv(target).get("kind", "")) == "Name"
            assign_stmt = Assign(source_span=span, target=target, value=val_expr, declare=is_declare)
            if len(pending_trivia) > 0:
                assign_stmt.leading_trivia = list(pending_trivia)
            if len(pending_comments) > 0:
                assign_stmt.leading_comments = list(pending_comments)
            body_items.append(assign_stmt)
            ln_no += 1
            first_nonimport_done = True
            pending_trivia = []
            pending_comments = []
            continue

        # Skip unhandled top-level statements
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
        indent = _leading_space_count(ln)
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
    trivia: list[JsonVal],
    comments: list[str],
    class_name: str = "",
    parent_indent: int = 0,
) -> tuple[FunctionDef, int]:
    """関数定義をパースする。"""
    header_line = lines[start_ln]
    header = _strip_inline_comment(header_line.strip())
    header_indent = _leading_space_count(header_line)

    # Multi-line header: merge continuation lines
    merge_ln = start_ln
    while _parse_def_header(header)[0] == "" and header.startswith("def ") and merge_ln + 1 < len(lines):
        merge_ln += 1
        header = header.rstrip() + " " + lines[merge_ln].strip()

    # Parse signature via pytra.std.re
    _, args_text, return_ann = _parse_def_header(header)
    return_type = return_ann if return_ann != "" else "None"

    # Parse arguments
    arg_order: list[str] = []
    arg_types: dict[str, str] = {}
    arg_defaults: dict[str, JsonVal] = {}
    arg_index: dict[str, int] = {}
    arg_type_exprs: dict[str, dict[str, JsonVal]] = {}
    vararg_name_val: Optional[str] = None
    vararg_type_val: Optional[str] = None

    name_types_empty: dict[str, str] = {}
    if args_text.strip() != "" and (args_text.strip() != "self" or class_name != ""):
        idx = 0
        for raw_param in _split_type_args_outer(args_text):
            param = raw_param.strip()
            if param == "" or param == "*":
                continue
            # *args: capture vararg info, skip from regular args
            if param.startswith("**"):
                continue
            if param.startswith("*"):
                vararg_param = param[1:].strip()
                if ":" in vararg_param:
                    colon_pos = vararg_param.find(":")
                    vararg_name_val = vararg_param[:colon_pos].strip()
                    vararg_type_val = vararg_param[colon_pos + 1:].strip()
                else:
                    vararg_name_val = vararg_param
                    vararg_type_val = "unknown"
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
                ptype = ptype_ann
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
            idx += 1

    # Check for one-liner: def name(args) -> ret: ...
    is_stub = header.rstrip().endswith(": ...") or header.rstrip().endswith(": pass")

    # Collect body
    if is_stub:
        block_lines: list[str] = []
        end_ln = merge_ln + 1
    else:
        block_lines, end_ln = _collect_block(lines, merge_ln + 1, header_indent)

    # Parse body with arg types in scope
    name_types: dict[str, str] = dict(arg_types)
    body_stmts: list[JsonVal] = []
    if len(block_lines) > 0:
        body_stmts = _parse_block_lines(ctx, block_lines, name_types, fn_name, start_hint=start_ln)

    # Extract docstring and remove from body
    docstring = _extract_docstring(block_lines)
    if docstring is not None and len(body_stmts) > 0:
        first_stmt = stmt_to_jv(body_stmts[0])
        if str(first_stmt.get("kind", "")) == "Expr":
            first_value = expr_to_jv(first_stmt.get("value"))
            if str(first_value.get("kind", "")) == "Constant" and json.JsonValue(first_value.get("value")).as_str() is not None:
                body_stmts = body_stmts[1:]

    # Compute end span: 最終非空行の絶対行番号と行末位置
    end_lineno = start_ln + 1
    end_col = 0
    if len(block_lines) > 0:
        for bl in reversed(block_lines):
            if bl.strip() != "":
                end_lineno = _find_abs_line(lines, bl, start_ln)
                end_col = len(bl.rstrip())
                break

    span: SourceSpan = make_span(start_ln + 1, header_indent, end_lineno, end_col)

    # Detect generator (yield in body)
    gen_flag = 0
    gen_yield_type = "unknown"
    if _has_yield(body_stmts):
        gen_flag = 1
        # yield_value_type from return annotation: e.g., "int" for "def gen() -> int"
        gen_yield_type = return_type if return_type != "None" else "unknown"
        # return_type for generators becomes list[yield_type]
        if gen_yield_type != "unknown":
            return_type = "list[" + gen_yield_type + "]"

    renamed_symbols: dict[str, str] = {}
    fd = FunctionDef(
        source_span=span,
        name=fn_name,
        original_name=fn_name,
        arg_types=arg_types,
        arg_order=arg_order,
        arg_defaults=arg_defaults,
        arg_index=arg_index,
        return_type=return_type,
        renamed_symbols=renamed_symbols,
        docstring=docstring,
        body=body_stmts,
        is_generator=gen_flag,
        yield_value_type=gen_yield_type,
    )
    if vararg_name_val is not None:
        fd.vararg_name = vararg_name_val
        fd.vararg_type = vararg_type_val

    # Optional fields: クラスメソッドとトップレベル関数で異なる
    if class_name != "":
        # クラスメソッド: decorators のみ出力。arg_type_exprs/return_type_expr/leading は出力しない
        empty_decorators: list[str] = []
        fd.decorators = empty_decorators
    else:
        # トップレベル関数
        fd.leading_comments = list(comments)
        fd.leading_trivia = list(trivia)

    return fd, end_ln


def _has_yield(stmts: list[JsonVal]) -> bool:
    """ステートメントリストに yield が含まれるか再帰的にチェック。"""
    for stmt in stmts:
        s = stmt_to_jv(stmt)
        kind = str(s.get("kind", ""))
        if kind == "Yield":
            return True
        if kind == "If":
            body = json.JsonValue(s.get("body")).as_arr()
            orelse = json.JsonValue(s.get("orelse")).as_arr()
            if body is not None and _has_yield(body.raw):
                return True
            if orelse is not None and _has_yield(orelse.raw):
                return True
        if kind == "For" or kind == "While":
            body = json.JsonValue(s.get("body")).as_arr()
            if body is not None and _has_yield(body.raw):
                return True
        if kind == "Try":
            body = json.JsonValue(s.get("body")).as_arr()
            finalbody = json.JsonValue(s.get("finalbody")).as_arr()
            if body is not None and _has_yield(body.raw):
                return True
            if finalbody is not None and _has_yield(finalbody.raw):
                return True
            handlers = json.JsonValue(s.get("handlers")).as_arr()
            if handlers is not None:
                for handler in handlers.raw:
                    handler_obj = json.JsonValue(handler).as_obj()
                    if handler_obj is not None:
                        handler_body = json.JsonValue(handler_obj.raw.get("body")).as_arr()
                        if handler_body is not None and _has_yield(handler_body.raw):
                            return True
    return False


def _parse_class_def(
    ctx: ParseContext,
    lines: list[str],
    start_ln: int,
    cls_name: str,
    trivia: list[JsonVal],
    comments: list[str],
    decorators: Optional[list[str]] = None,
    is_dataclass: bool = False,
    force_leading: bool = True,
) -> tuple[ClassDef, int]:
    """クラス定義をパースする。"""
    # Check for base class: class Name(Base):
    header = _strip_inline_comment(lines[start_ln].strip())
    base_name: Optional[str] = None
    paren_pos = header.find("(")
    if paren_pos > 0:
        paren_end = header.find(")")
        if paren_end > paren_pos:
            parsed_base: str = header[paren_pos + 1:paren_end].strip()
            if parsed_base != "":
                base_name = parsed_base
    block_lines, end_ln = _collect_block(lines, start_ln + 1, 0)
    name_types: dict[str, str] = {}
    body_stmts = _parse_block_lines(ctx, block_lines, name_types, cls_name, start_hint=start_ln)
    runtime_ns = ""
    if decorators is not None:
        for deco in decorators:
            _rt_ns, _rt_sym, _rt_tag = _parse_runtime_decorator("@" + deco)
            if _rt_ns != "":
                runtime_ns = _rt_ns
                break
    if runtime_ns != "":
        for stmt in body_stmts:
            stmt_obj = json.JsonValue(stmt).as_obj()
            if stmt_obj is None:
                continue
            if _json_obj_str(stmt_obj.raw, "kind") != "FunctionDef":
                continue
            method_name = _json_obj_str(stmt_obj.raw, "name")
            if method_name == "":
                continue
            meta_obj = stmt_obj.get_obj("meta")
            meta_raw: dict[str, JsonVal] = {}
            if meta_obj is not None:
                meta_raw = meta_obj.raw
            if "extern_v2" in meta_raw:
                continue
            method_ev2 = _runtime_method_extern_v2(runtime_ns, cls_name, method_name)
            method_ev2_meta: dict[str, JsonVal] = {}
            for method_ev2_key, method_ev2_value in method_ev2.items():
                method_ev2_meta[method_ev2_key] = method_ev2_value
            meta_raw["extern_v2"] = method_ev2_meta
            stmt_obj.raw["meta"] = meta_raw

    # Collect field types from annotated assignments and __init__ self.attr assignments
    field_types: dict[str, str] = {}
    for stmt in body_stmts:
        stmt_obj2 = json.JsonValue(stmt).as_obj()
        if stmt_obj2 is None:
            continue
        stmt_kind2 = _json_obj_str(stmt_obj2.raw, "kind")
        if stmt_kind2 == "AnnAssign":
            target_obj = stmt_obj2.get_obj("target")
            ann = _json_obj_str(stmt_obj2.raw, "annotation")
            if target_obj is not None and ann != "" and _json_obj_str(target_obj.raw, "kind") == "Name":
                target_id = _json_obj_str(target_obj.raw, "id")
                if target_id != "":
                    field_types[target_id] = ann
        # Scan __init__ for self.attr assignments
        if stmt_kind2 == "FunctionDef" and _json_obj_str(stmt_obj2.raw, "original_name") == "__init__":
            init_body = stmt_obj2.get_arr("body")
            arg_types_obj = stmt_obj2.get_obj("arg_types")
            if init_body is None:
                continue
            for init_stmt in init_body.raw:
                init_obj = json.JsonValue(init_stmt).as_obj()
                if init_obj is None:
                    continue
                init_kind = _json_obj_str(init_obj.raw, "kind")
                init_target = init_obj.get_obj("target")
                if init_target is None or _json_obj_str(init_target.raw, "kind") != "Attribute":
                    continue
                target_value = init_target.get_obj("value")
                if target_value is None or _json_obj_str(target_value.raw, "kind") != "Name" or _json_obj_str(target_value.raw, "id") != "self":
                    continue
                attr_name = _json_obj_str(init_target.raw, "attr")
                if attr_name == "":
                    continue
                if init_kind == "AnnAssign":
                    init_ann = _json_obj_str(init_obj.raw, "annotation")
                    if init_ann != "":
                        field_types[attr_name] = init_ann
                if init_kind == "Assign":
                    # Infer type from arg_types: try attr name, then RHS value name.
                    ft = "unknown"
                    if arg_types_obj is not None and attr_name in arg_types_obj.raw:
                        attr_ft = json.JsonValue(arg_types_obj.raw[attr_name]).as_str()
                        if attr_ft is not None:
                            ft = attr_ft
                    init_value = init_obj.get_obj("value")
                    if ft == "unknown" and init_value is not None and _json_obj_str(init_value.raw, "kind") == "Name" and arg_types_obj is not None:
                        value_id = _json_obj_str(init_value.raw, "id")
                        if value_id != "" and value_id in arg_types_obj.raw:
                            value_ft = json.JsonValue(arg_types_obj.raw[value_id]).as_str()
                            if value_ft is not None:
                                ft = value_ft
                    field_types[attr_name] = ft

    # ClassDef span: end_lineno = _collect_block が返した end_ln (次のトップレベル行の前)
    span: SourceSpan = make_span(start_ln + 1, 0, end_ln, 0)

    class_decorators: list[str] = []
    if decorators is not None:
        for class_deco in decorators:
            class_decorators.append(class_deco)
    cd = ClassDef(
        source_span=span,
        name=cls_name,
        original_name=cls_name,
        base=base_name,
        body=body_stmts,
        dataclass_flag=is_dataclass,
        field_types=field_types,
        decorators=class_decorators,
    )
    # ClassDef: 最初の body item は常に出力、2番目以降は trivia がある場合のみ
    if force_leading or len(comments) > 0 or len(trivia) > 0:
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
) -> tuple[JsonVal, int]:
    """try/except/finally 文をパースする。"""
    # Collect try body
    try_lines, next_i = _collect_sub_block(block_lines, start_i + 1, indent)
    try_body = _parse_block_lines(ctx, try_lines, name_types, "try")

    handlers: list[ExceptHandler] = []
    orelse: list[JsonVal] = []
    finalbody: list[JsonVal] = []

    # Parse except/else/finally clauses
    while next_i < len(block_lines):
        ln = block_lines[next_i]
        s = ln.strip()
        ln_indent = _leading_space_count(ln) if s != "" else 0
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
            exc_type_str = ""
            exc_name: Optional[str] = None
            if m_exc_as is not None:
                exc_type_str = re.strip_group(m_exc_as, 1)
                exc_name = re.strip_group(m_exc_as, 2)
            elif m_exc is not None:
                exc_type_str = re.strip_group(m_exc, 1)
            elif s == "except:" or s.startswith("except:"):
                pass  # bare except
            exc_type_expr: JsonVal = None
            if exc_type_str != "":
                exc_type_expr = _make_name_expr(exc_type_str, handler_abs_ln, indent + 7, ctx)
            handler_lines, next_i = _collect_sub_block(block_lines, next_i + 1, indent)
            handler_body = _parse_block_lines(ctx, handler_lines, name_types, "except")
            span: SourceSpan = make_span(handler_abs_ln, indent, handler_abs_ln, indent + len(s))
            handlers.append(ExceptHandler(
                exc_type_expr=exc_type_expr,
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
        last_end_ln = _stmt_end_lineno(finalbody[-1])
        if last_end_ln > 0:
            end_ln = last_end_ln
            end_col = _stmt_end_col(finalbody[-1])
    elif len(handlers) > 0:
        last_h = handlers[-1]
        if len(last_h.body) > 0:
            last_h_end_ln = _stmt_end_lineno(last_h.body[-1])
            if last_h_end_ln > 0:
                end_ln = last_h_end_ln
                end_col = _stmt_end_col(last_h.body[-1])

    span: SourceSpan = make_span(abs_ln, indent, end_ln, end_col)
    try_node = Try(
        source_span=span,
        body=try_body,
        handlers=handlers,
        orelse=orelse,
        finalbody=finalbody,
    )
    return try_node.to_jv(), next_i


def _merge_logical_lines(lines: list[str]) -> list[str]:
    """未閉じ括弧や行末バックスラッシュで物理行を論理行にマージする。"""
    merged: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        s = ln.rstrip()
        depth = _bracket_depth(s)
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
                depth += _bracket_depth(next_s)
                explicit_cont = next_s.rstrip().endswith("\\")
                next_clean = _strip_inline_comment(next_s).strip()
                if explicit_cont and next_clean.endswith("\\"):
                    next_clean = next_clean[:-1].rstrip()
                acc = acc + " " + next_clean
                i += 1
                if depth <= 0 and not explicit_cont:
                    break
            # Preserve original indentation
            indent = _leading_space_count(ln)
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


def _split_raise_from_outer(text: str) -> tuple[str, str]:
    depth = 0
    quote = ""
    i = 0
    marker = " from "
    marker_len = len(marker)
    while i < len(text):
        ch = text[i]
        if quote != "":
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch == "'" or ch == '"':
            quote = ch
            i += 1
            continue
        if ch == "(" or ch == "[" or ch == "{":
            depth += 1
            i += 1
            continue
        if ch == ")" or ch == "]" or ch == "}":
            if depth > 0:
                depth -= 1
            i += 1
            continue
        if depth == 0 and text[i:i + marker_len] == marker:
            return text[:i], text[i + marker_len:]
        i += 1
    return text, ""


# ---------------------------------------------------------------------------
# Block-level statement parser
# ---------------------------------------------------------------------------

def _parse_block_lines(
    ctx: ParseContext,
    block_lines: list[str],
    name_types: dict[str, str],
    scope_label: str,
    start_hint: int = 0,
) -> list[JsonVal]:
    """インデントされたブロック内の文をパースする。"""
    block_lines = _merge_logical_lines(block_lines)
    stmts: list[JsonVal] = []
    i = 0
    total = len(block_lines)
    last_abs_ln = start_hint  # hint for _find_abs_line
    pending_trivia: list[JsonVal] = []
    pending_comments: list[str] = []
    pending_decorators: list[str] = []
    pending_block_extern_v2: dict[str, str] = {}

    # Determine block base indent
    base_indent = 0
    for bl in block_lines:
        s = bl.strip()
        if s != "" and not s.startswith("#"):
            base_indent = _leading_space_count(bl)
            break

    while i < total:
        ln = block_lines[i]
        s = ln.strip()
        indent = _leading_space_count(ln) if s != "" else 0

        if s == "":
            pending_trivia.append(TriviaBlank(count=1).to_jv())
            i += 1
            continue

        if s.startswith("#"):
            text = s[1:].lstrip() if len(s) > 1 else ""
            pending_trivia.append(TriviaComment(text=text).to_jv())
            pending_comments.append(text)
            i += 1
            continue

        s_clean = _strip_inline_comment(s)

        # Decorator: @name — accumulate for next def
        if s_clean.startswith("@"):
            if s_clean.startswith("@extern_method("):
                raise RuntimeError("extern_method is removed; use @runtime(...) or @extern(...)")
            if s_clean.startswith("@abi(") or s_clean == "@abi":
                raise RuntimeError("abi decorator is removed")
            deco_name = _decorator_text(s_clean)
            # Check for v2 extern decorator
            block_extern_v2 = _parse_extern_v2_decorator(s_clean)
            if block_extern_v2 is not None:
                pending_block_extern_v2 = block_extern_v2
            pending_decorators.append(deco_name)
            i += 1
            continue

        # Calculate absolute line number
        abs_ln = _find_abs_line(ctx.lines, ln, last_abs_ln)
        last_abs_ln = abs_ln

        # Standalone string literal (function/class docstring or expression statement)
        if (s_clean.startswith('"""') or s_clean.startswith("'''") or
            (s_clean.startswith('"') and not s_clean.startswith('"""')) or
            (s_clean.startswith("'") and not s_clean.startswith("'''"))):
            expr = _parse_expr_text(ctx, s_clean, abs_ln, indent, name_types)
            span: SourceSpan = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
            expr_stmt: ExprStmt = ExprStmt(source_span=span, value=expr)
            if len(pending_trivia) > 0:
                expr_stmt.leading_trivia = list(pending_trivia)
            if len(pending_comments) > 0:
                expr_stmt.leading_comments = list(pending_comments)
            stmts.append(expr_stmt)
            i += 1
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
                asname = ""
                name = part
                if " as " in part:
                    split = part.split(" as ")
                    name = split[0].strip()
                    asname = split[1].strip()
                aliases.append(ImportAlias(name=name, asname=asname))
            if mod in _TYPE_ONLY_IMPORT_MODULES:
                if mod in ("typing", "pytra.typing"):
                    for alias in aliases:
                        alias_name: str = "" + alias.name
                        if alias_name not in _TYPE_MODULE_VALUE_EXPORTS:
                            continue
                        local: str = _alias_local(alias)
                        symbol_info: dict[str, str] = {}
                        symbol_info["module"] = mod
                        symbol_info["name"] = alias_name
                        ctx.import_symbols[local] = symbol_info
                        ctx.import_bindings.append(
                            {
                                "module_id": mod,
                                "export_name": alias_name,
                                "local_name": local,
                                "binding_kind": "symbol",
                                "source_file": ctx.filename,
                                "source_line": abs_ln,
                            }
                        )
                        ctx.qualified_refs.append(
                            {
                                "module_id": mod,
                                "symbol": alias_name,
                                "local_name": local,
                            }
                        )
                i += 1
                pending_trivia = []
                pending_comments = []
                continue
            span: SourceSpan = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
            import_from_stmt: ImportFrom = ImportFrom(source_span=span, module=mod, names=aliases, level=0)
            stmts.append(import_from_stmt)
            for alias in aliases:
                alias_name: str = "" + alias.name
                local: str = _alias_local(alias)
                binding: dict[str, JsonVal] = {}
                binding["module_id"] = mod
                binding["export_name"] = alias_name
                binding["local_name"] = local
                binding["binding_kind"] = "symbol"
                binding["source_file"] = ctx.filename
                binding["source_line"] = abs_ln
                ctx.import_bindings.append(binding)
                qref: dict[str, JsonVal] = {}
                qref["module_id"] = mod
                qref["symbol"] = alias_name
                qref["local_name"] = local
                ctx.qualified_refs.append(qref)
            i += 1
            pending_trivia = []
            pending_comments = []
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
                asname_i = ""
                name_i = part
                if " as " in part:
                    split_i = part.split(" as ")
                    name_i = split_i[0].strip()
                    asname_i = split_i[1].strip()
                imp_aliases.append(ImportAlias(name=name_i, asname=asname_i))
                local_i: str = asname_i if asname_i != "" else name_i
                ctx.import_modules[local_i] = name_i
            span: SourceSpan = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
            import_stmt: Import = Import(source_span=span, names=imp_aliases)
            stmts.append(import_stmt)
            for alias in imp_aliases:
                alias_name: str = "" + alias.name
                local: str = _alias_local(alias)
                binding: dict[str, JsonVal] = {}
                binding["module_id"] = alias_name
                binding["export_name"] = ""
                binding["local_name"] = local
                binding["binding_kind"] = "module"
                binding["source_file"] = ctx.filename
                binding["source_line"] = abs_ln
                ctx.import_bindings.append(binding)
            i += 1
            pending_trivia = []
            pending_comments = []
            continue

        # return statement
        if s_clean == "return":
            span: SourceSpan = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
            return_none_stmt: Return = Return(source_span=span, value=None)
            if len(pending_comments) > 0:
                return_none_stmt.leading_comments = list(pending_comments)
            if len(pending_trivia) > 0:
                return_none_stmt.leading_trivia = list(pending_trivia)
            stmts.append(return_none_stmt)
            i += 1
            pending_trivia = []
            pending_comments = []
            continue
        if s_clean.startswith("return "):
            expr_text = s_clean[7:].strip()
            expr_col = _find_expr_col(ctx, expr_text, abs_ln, indent + 7)
            expr = _parse_tuple_or_expr(ctx, expr_text, abs_ln, expr_col, name_types)
            span: SourceSpan = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
            return_value_stmt: Return = Return(source_span=span, value=expr)
            if len(pending_comments) > 0:
                return_value_stmt.leading_comments = list(pending_comments)
            if len(pending_trivia) > 0:
                return_value_stmt.leading_trivia = list(pending_trivia)
            stmts.append(return_value_stmt)
            i += 1
            pending_trivia = []
            pending_comments = []
            continue

        # pass
        if s_clean == "pass":
            span: SourceSpan = make_span(abs_ln, 0, abs_ln, indent + 4)
            stmts.append(Pass(source_span=span))
            i += 1
            pending_trivia = []
            pending_comments = []
            continue

        # global / nonlocal
        if s_clean.startswith("global ") or s_clean.startswith("nonlocal "):
            i += 1
            pending_trivia = []
            pending_comments = []
            continue

        # yield statement
        if s_clean.startswith("yield "):
            expr_text = s_clean[6:].strip()
            expr = _parse_expr_text(ctx, expr_text, abs_ln, _find_expr_col(ctx, expr_text, abs_ln, indent + 6), name_types)
            span: SourceSpan = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
            stmts.append(Yield(source_span=span, value=expr))
            i += 1
            pending_trivia = []
            pending_comments = []
            continue

        # raise
        if s_clean == "raise":
            span: SourceSpan = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
            stmts.append(Raise(source_span=span, exc=None, cause=None))
            i += 1
            pending_trivia = []
            pending_comments = []
            continue
        if s_clean.startswith("raise "):
            expr_text = s_clean[6:].strip()
            cause_expr: JsonVal = None
            exc_text = expr_text
            exc_text, cause_text = _split_raise_from_outer(expr_text)
            if cause_text != "":
                exc_text = exc_text.strip()
                cause_text = cause_text.strip()
                if cause_text != "":
                    cause_expr = _parse_expr_text(
                        ctx,
                        cause_text,
                        abs_ln,
                        _find_expr_col(ctx, cause_text, abs_ln, indent + 6),
                        name_types,
                    )
            expr = _parse_expr_text(ctx, exc_text, abs_ln, _find_expr_col(ctx, exc_text, abs_ln, indent + 6), name_types)
            span: SourceSpan = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
            stmts.append(Raise(source_span=span, exc=expr, cause=cause_expr))
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
            for_stmt, i = _parse_for_stmt(ctx, block_lines, i, base_indent, name_types, pending_trivia, pending_comments, abs_ln)
            stmts.append(for_stmt)
            pending_trivia = []
            pending_comments = []
            continue

        # while ...:
        if s_clean.startswith("while "):
            while_stmt, i = _parse_while_stmt(ctx, block_lines, i, base_indent, name_types, pending_trivia, pending_comments, abs_ln)
            stmts.append(while_stmt)
            pending_trivia = []
            pending_comments = []
            continue

        # with ...:
        if s_clean.startswith("with "):
            with_stmt, i = _parse_with_stmt(ctx, block_lines, i, base_indent, name_types, pending_trivia, pending_comments, abs_ln)
            stmts.append(with_stmt)
            pending_trivia = []
            pending_comments = []
            continue

        # def ...: (nested function / class method)
        fn_name_block = _parse_def_name(s_clean)
        if fn_name_block != "":
            # scope_label がクラス名ならクラスメソッドとして self の型を設定
            block_class_name = scope_label if scope_label in ctx.class_names else ""
            fn_stmt, fn_end_ln = _parse_function_def(ctx, ctx.lines, abs_ln - 1, fn_name_block, pending_trivia, pending_comments, class_name=block_class_name, parent_indent=indent)
            # Attach decorators
            if len(pending_decorators) > 0:
                fn_stmt.decorators = list(pending_decorators)
                pending_decorators = []
            # Attach v2 extern metadata
            if len(pending_block_extern_v2) > 0:
                ev2 = dict(pending_block_extern_v2)
                ev2["kind"] = "method"
                ev2_meta: dict[str, JsonVal] = {}
                for ev2_key, ev2_value in ev2.items():
                    ev2_meta[ev2_key] = ev2_value
                fn_meta: dict[str, JsonVal] = {}
                fn_meta["extern_v2"] = ev2_meta
                fn_stmt.node_meta = fn_meta
                pending_block_extern_v2 = {}
            stmts.append(fn_stmt)
            # Skip block_lines that were consumed by _parse_function_def
            # fn_end_ln is 0-based file line index. Advance i past those lines.
            i += 1  # skip the def line itself
            while i < total:
                bl_s = block_lines[i].strip()
                if bl_s != "" and not bl_s.startswith("#"):
                    bl_indent = _leading_space_count(block_lines[i])
                    if bl_indent <= indent:
                        break
                i += 1
            pending_trivia = []
            pending_comments = []
            continue

        # if ...:
        if s_clean.startswith("if "):
            if_stmt, i = _parse_if_stmt(ctx, block_lines, i, base_indent, name_types, pending_trivia, pending_comments, abs_ln)
            stmts.append(if_stmt)
            pending_trivia = []
            pending_comments = []
            continue

        # Annotated assignment: x: Type = value or self.x: Type = value
        var_name, type_ann, value_text = _parse_ann_assign(s_clean)
        if var_name != "":
            resolved = type_ann
            name_types[var_name] = resolved
            target: JsonVal = _make_attr_or_name_expr(var_name, abs_ln, indent, ctx)
            value = _parse_expr_text(ctx, value_text, abs_ln, _find_expr_col(ctx, value_text, abs_ln, indent + s_clean.index("=") + 2), name_types)
            span: SourceSpan = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
            ann_value_stmt: AnnAssign = AnnAssign(
                source_span=span,
                target=target,
                annotation=resolved,
                value=value,
                declare=True,
            )
            if len(pending_trivia) > 0:
                ann_value_stmt.leading_trivia = list(pending_trivia)
            if len(pending_comments) > 0:
                ann_value_stmt.leading_comments = list(pending_comments)
            stmts.append(ann_value_stmt)
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
                resolved = ann_type
                name_types[ann_var] = resolved
                target = _make_attr_or_name_expr(ann_var, abs_ln, indent, ctx)
                span: SourceSpan = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
                ann_only_stmt: AnnAssign = AnnAssign(
                    source_span=span,
                    target=target,
                    annotation=resolved,
                    value=None,
                    declare=True,
                )
                if len(pending_trivia) > 0:
                    ann_only_stmt.leading_trivia = list(pending_trivia)
                if len(pending_comments) > 0:
                    ann_only_stmt.leading_comments = list(pending_comments)
                stmts.append(ann_only_stmt)
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
            span: SourceSpan = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
            aug_stmt = AugAssign(
                source_span=span,
                target=target,
                op=op_map.get(op_text, op_text),
                value=value,
                
                declare=False,
            )
            stmts.append(aug_stmt)
            i += 1
            pending_trivia = []
            pending_comments = []
            continue

        # Tuple unpacking or swap: a, b = ... OR a[i], a[j] = ...
        tuple_lhs_text, tuple_rhs_text = _try_parse_tuple_assign(s_clean)
        if tuple_lhs_text != "":
            lhs_text = tuple_lhs_text
            rhs_text = tuple_rhs_text
            lhs_parts = [n.strip() for n in _split_tuple_targets(lhs_text) if n.strip() != ""]
            if len(lhs_parts) >= 2:
                # Check for swap pattern: a[i], a[j] = a[j], a[i]
                rhs_parts = [p.strip() for p in _split_tuple_targets(rhs_text) if p.strip() != ""]
                is_swap = len(lhs_parts) == 2 and len(rhs_parts) == 2 and rhs_parts[0] == lhs_parts[1] and rhs_parts[1] == lhs_parts[0]
                if is_swap:
                    left = _parse_expr_text(ctx, lhs_parts[0], abs_ln, _find_expr_col(ctx, lhs_parts[0], abs_ln, indent), name_types)
                    right = _parse_expr_text(ctx, lhs_parts[1], abs_ln, _find_expr_col(ctx, lhs_parts[1], abs_ln, indent), name_types)
                    span: SourceSpan = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
                    stmts.append(Swap(source_span=span, left=left, right=right))
                    i += 1
                    pending_trivia = []
                    pending_comments = []
                    continue
                # Tuple unpacking: a, b = expr
                elements = [_parse_expr_text(ctx, p, abs_ln, _find_expr_col(ctx, p, abs_ln, indent), name_types) for p in lhs_parts]
                target_col = _find_expr_col(ctx, lhs_text, abs_ln, indent)
                target_span: SourceSpan = make_span(abs_ln, target_col, abs_ln, target_col + len(lhs_text))
                tuple_target = TupleExpr(base=ExprBase(source_span=target_span, repr_text=lhs_text), elements=elements)
                rhs_parts = [p.strip() for p in _split_top_level_csv(rhs_text) if p.strip() != ""]
                if len(rhs_parts) >= 2:
                    rhs_elements = [
                        _parse_expr_text(ctx, p, abs_ln, _find_expr_col(ctx, p, abs_ln, indent + len(lhs_text) + 3), name_types)
                        for p in rhs_parts
                    ]
                    value_col = _find_expr_col(ctx, rhs_text, abs_ln, indent + len(lhs_text) + 3)
                    value_span: SourceSpan = make_span(abs_ln, value_col, abs_ln, value_col + len(rhs_text))
                    value = TupleExpr(base=ExprBase(source_span=value_span, repr_text=rhs_text), elements=rhs_elements)
                else:
                    value = _parse_expr_text(ctx, rhs_text, abs_ln, _find_expr_col(ctx, rhs_text, abs_ln, indent + len(lhs_text) + 3), name_types)
                span: SourceSpan = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
                tuple_assign_stmt: Assign = Assign(source_span=span, target=tuple_target, value=value, declare=False)
                if len(pending_trivia) > 0:
                    tuple_assign_stmt.leading_trivia = list(pending_trivia)
                if len(pending_comments) > 0:
                    tuple_assign_stmt.leading_comments = list(pending_comments)
                stmts.append(tuple_assign_stmt)
                i += 1
                pending_trivia = []
                pending_comments = []
                continue

        # Simple assignment: x = value
        target_text, value_text = _parse_simple_assign(s_clean)
        if target_text != "":
            # Check it's not a comparison or augmented op
            if not _endswith_assignment_operator_prefix(target_text):
                target = _parse_expr_text(ctx, target_text, abs_ln, _find_expr_col(ctx, target_text, abs_ln, indent), name_types)
                value = _parse_assign_value(ctx, value_text, abs_ln, indent + len(target_text) + 3, name_types)
                # EAST1: declare is always True for simple assignments
                is_declare = True
                
                span: SourceSpan = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
                simple_assign_stmt: Assign = Assign(
                    source_span=span,
                    target=target,
                    value=value,
                    declare=is_declare,
                )
                if len(pending_trivia) > 0:
                    simple_assign_stmt.leading_trivia = list(pending_trivia)
                if len(pending_comments) > 0:
                    simple_assign_stmt.leading_comments = list(pending_comments)
                stmts.append(simple_assign_stmt)
                i += 1
                pending_trivia = []
                pending_comments = []
                continue

        # Expression statement (e.g., function call)
        expr = _parse_expr_text(ctx, s_clean, abs_ln, indent, name_types)
        span: SourceSpan = make_span(abs_ln, indent, abs_ln, indent + len(s_clean))
        expr_stmt: ExprStmt = ExprStmt(source_span=span, value=expr)
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


def _parse_fstring_parts(inner: str, line: int, col_base: int, ctx: ParseContext, fstr_span: SourceSpan) -> list[JsonVal]:
    """f-string の内部を FStringText と FormattedValue に分解する。

    {{/}} はリテラル {/} に変換。{expr} は FormattedValue に。
    """
    parts: list[JsonVal] = []
    i = 0
    n = len(inner)
    text_buf: list[str] = []

    def flush_text() -> None:
        if len(text_buf) > 0:
            t = "".join(text_buf)
            parts.append(FStringText(source_span=fstr_span, repr_text=t, value=t).to_jv())
            text_buf.clear()

    while i < n:
        ch = inner[i]
        if ch == "{":
            if i + 1 < n and inner[i + 1] == "{":
                # Escaped brace: {{ → literal {. Create separate text part.
                flush_text()
                parts.append(FStringText(source_span=fstr_span, repr_text="{", value="{").to_jv())
                i += 2
                continue
            # Expression: {expr} or {expr:fmt}
            flush_text()
            depth = 1
            j = i + 1
            format_spec: Optional[str] = None
            in_str = ""
            while j < n and depth > 0:
                c = inner[j]
                if in_str != "":
                    if c == in_str:
                        in_str = ""
                    j += 1
                    continue
                if c == "'" or c == '"':
                    in_str = c
                elif c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                elif c == ":" and depth == 1:
                    expr_text = inner[i + 1:j]
                    k = j + 1
                    while k < n and inner[k] != "}":
                        k += 1
                    format_spec = inner[j + 1:k]
                    j = k
                    depth = 0
                    break
                j += 1
            if format_spec is None:
                expr_text = inner[i + 1:j - 1] if depth == 0 else inner[i + 1:]
            expr_node = _parse_expr_text(ctx, expr_text.strip(), line, col_base + i + 1, {})
            parts.append(FormattedValue(value=expr_node, format_spec=format_spec).to_jv())
            if format_spec is not None:
                i = j + 1
            else:
                i = j
        elif ch == "}" and i + 1 < n and inner[i + 1] == "}":
            # Escaped brace: }} → literal }
            text_buf.append("}")
            i += 2
        else:
            text_buf.append(ch)
            i += 1

    flush_text()
    return parts


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
) -> JsonVal:
    """テキストから式をパースする。"""
    tokens = _tokenize_expr(text)
    # 元の行テキストを取得 (span 計算の基準)
    source_line_text = ""
    if line >= 1 and line <= len(ctx.lines):
        source_line_text = ctx.lines[line - 1]
    parser = ExprParser(
        tokens=tokens,
        pos=0,
        source_line=line,
        line_col_offset=col_offset,
        source_text=text,
        source_line_text=source_line_text,
        name_types=name_types,
        ctx=ctx,
    )
    return parser.parse_expr()


def _try_parse_tuple_assign(s: str) -> tuple[str, str]:
    """Try to parse 'target1, target2 = value' where targets can be name or name[expr].

    Returns (lhs_text, rhs_text) or ("", "") if not a tuple assign.
    """
    stripped = s.lstrip()
    if _starts_with_compound_stmt_keyword(stripped):
        return ("", "")
    # Find the top-level '=' that is not '==' and not inside brackets
    depth: int = 0
    eq_pos: int = -1
    i: int = 0
    while i < len(s):
        ch = s[i]
        if ch == "[" or ch == "(":
            depth += 1
        elif ch == "]" or ch == ")":
            depth -= 1
        elif ch == "=" and depth == 0:
            # Check not ==
            if i + 1 < len(s) and s[i + 1] == "=":
                i += 2
                continue
            # Check not !=, <=, >=
            if i > 0 and s[i - 1] in ("!", "<", ">", "+", "-", "*", "/", "%"):
                i += 1
                continue
            eq_pos = i
            break
        i += 1
    if eq_pos <= 0:
        return ("", "")
    lhs = s[:eq_pos].rstrip()
    rhs = s[eq_pos + 1:].lstrip()
    depth = 0
    for ch in lhs:
        if ch == "[" or ch == "(" or ch == "{":
            depth += 1
        elif ch == "]" or ch == ")" or ch == "}":
            depth -= 1
        elif ch == ":" and depth == 0:
            return ("", "")
    stripped_lhs = _strip_outer_tuple_target_wrapper(lhs)
    lhs_parts = [p.strip() for p in _split_tuple_targets(stripped_lhs) if p.strip() != ""]
    if len(lhs_parts) < 2:
        return ("", "")
    return (stripped_lhs, rhs)


def _bracket_depth(text: str) -> int:
    """Count net bracket depth, ignoring characters inside string literals and comments."""
    depth: int = 0
    in_str: str = ""  # "" or quote char
    i: int = 0
    n: int = len(text)
    while i < n:
        ch = text[i]
        if in_str != "":
            if ch == "\\" and i + 1 < n:
                i += 2  # skip escaped char
                continue
            if ch == in_str:
                in_str = ""
            i += 1
            continue
        if ch == "#":
            break  # rest is comment
        if ch == '"' or ch == "'":
            # Check for triple quote
            if i + 2 < n and text[i+1] == ch and text[i+2] == ch:
                # Triple-quoted string: skip to closing triple
                close = ch * 3
                end = _find_substr_from(text, close, i + 3)
                if end >= 0:
                    i = end + 3
                else:
                    i = n  # unclosed triple in this line
                continue
            in_str = ch
            i += 1
            continue
        if ch in ("(", "[", "{"):
            depth += 1
        elif ch in (")", "]", "}"):
            depth -= 1
        i += 1
    return depth


def _join_continuation(lines: list[str], start: int, total: int) -> tuple[str, int]:
    """Join lines when brackets are unclosed.

    Returns (joined_line, next_index).
    """
    line = lines[start]
    depth = _bracket_depth(line)
    if depth <= 0:
        # Backslash continuation
        stripped = line.rstrip()
        if stripped.endswith("\\"):
            idx = start + 1
            parts = [stripped[:-1]]
            while idx < total:
                nxt = lines[idx]
                idx += 1
                ns = nxt.rstrip()
                if ns.endswith("\\"):
                    parts.append(ns[:-1])
                else:
                    parts.append(ns)
                    break
            return " ".join(parts), idx
        return line, start + 1
    # Unclosed brackets: join until balanced
    idx = start + 1
    parts = [line.rstrip()]
    while idx < total and depth > 0:
        nxt = lines[idx]
        parts.append(nxt.rstrip())
        depth += _bracket_depth(nxt)
        idx += 1
    return " ".join(parts), idx


def _split_tuple_targets(text: str) -> list[str]:
    """Split tuple target text by comma, respecting brackets.

    'a[i], a[j]' → ['a[i]', 'a[j]']
    'a, b' → ['a', 'b']
    """
    text = _strip_outer_tuple_target_wrapper(text.strip())
    parts: list[str] = []
    depth: int = 0
    current: list[str] = []
    for ch in text:
        if ch == "[" or ch == "(":
            depth += 1
            current.append(ch)
        elif ch == "]" or ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    tail = "".join(current).strip()
    if tail != "":
        parts.append(tail)
    return parts


def _split_top_level_csv(text: str) -> list[str]:
    parts: list[str] = []
    depth: int = 0
    current: list[str] = []
    for ch in text:
        if ch in ("[", "(", "{"):
            depth += 1
            current.append(ch)
        elif ch in ("]", ")", "}"):
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    tail = "".join(current).strip()
    if tail != "":
        parts.append(tail)
    return parts


def _strip_outer_tuple_target_wrapper(text: str) -> str:
    stripped = text.strip()
    while True:
        if _is_wrapped_by_pair(stripped, "(", ")") or _is_wrapped_by_pair(stripped, "[", "]"):
            stripped = stripped[1:-1].strip()
            continue
        return stripped


def _is_wrapped_by_pair(text: str, open_ch: str, close_ch: str) -> bool:
    if len(text) < 2 or text[0] != open_ch or text[-1] != close_ch:
        return False
    depth = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0 and i != len(text) - 1:
                return False
        i += 1
    return depth == 0


def _make_name_expr(name: str, line: int, col: int, ctx: ParseContext) -> Name:
    """Name ノードを生成する。"""
    # golden 準拠: 元の行テキスト内で名前の位置を検索
    actual_col = _find_expr_col(ctx, name, line, col)
    span: SourceSpan = make_span(line, actual_col, line, actual_col + len(name))
    base = ExprBase(source_span=span, repr_text=name)
    name_node = Name(base=base, id=name)
    return name_node


def _parse_tuple_or_expr(ctx: ParseContext, text: str, line: int, col: int, name_types: dict[str, str]) -> JsonVal:
    """カンマ区切りの式をパース。複数要素ならタプル、単一ならそのまま。"""
    tokens = _tokenize_expr(text)
    source_line_text = ""
    if line >= 1 and line <= len(ctx.lines):
        source_line_text = ctx.lines[line - 1]
    parser = ExprParser(
        tokens=tokens, pos=0, source_line=line, line_col_offset=col,
        source_text=text, source_line_text=source_line_text,
        name_types=name_types, ctx=ctx,
    )
    first = parser.parse_expr()
    if parser.peek().value == ",":
        elements: list[JsonVal] = [first]
        while parser.peek().value == ",":
            parser.advance()
            if parser.peek().kind == "EOF":
                break
            elements.append(parser.parse_expr())
        if len(elements) > 1:
            span: SourceSpan = make_span(line, col, line, col + len(text))
            return TupleExpr(base=ExprBase(source_span=span, repr_text=text), elements=elements)
    return first


def _parse_assign_value(ctx: ParseContext, value_text: str, line: int, col_hint: int, name_types: dict[str, str]) -> JsonVal:
    """代入右辺をパース。末尾カンマはタプルとして扱う。"""
    vt = value_text.rstrip()
    col = _find_expr_col(ctx, value_text, line, col_hint)
    if vt.endswith(","):
        # Trailing comma = tuple: parse comma-separated elements
        parts = [p.strip() for p in _split_type_args_outer(_rstrip_one_char(vt, ",")) if p.strip() != ""]
        elements = [_parse_expr_text(ctx, p, line, _find_expr_col(ctx, p, line, col), name_types) for p in parts]
        repr_text = _rstrip_one_char(vt, ",") + ","
        span: SourceSpan = make_span(line, col, line, col + len(repr_text))
        return TupleExpr(base=ExprBase(source_span=span, repr_text=repr_text), elements=elements)
    return _parse_expr_text(ctx, vt, line, col, name_types)


def _make_attr_or_name_expr(text: str, line: int, col: int, ctx: ParseContext) -> JsonVal:
    """self.attr のような属性アクセスを Attribute ノードに、単純名を Name ノードに変換。"""
    if "." in text:
        parts = text.split(".", 1)
        obj_name = parts[0]
        attr_name = parts[1]
        obj = _make_name_expr(obj_name, line, col, ctx)
        actual_col = _find_expr_col(ctx, text, line, col)
        span: SourceSpan = make_span(line, actual_col, line, actual_col + len(text))
        return Attribute(base=ExprBase(source_span=span, repr_text=text), value=obj, attr=attr_name)
    return _make_name_expr(text, line, col, ctx)


# ---------------------------------------------------------------------------
# Control flow parsers
# ---------------------------------------------------------------------------

def _parse_for_stmt(
    ctx: ParseContext,
    block_lines: list[str],
    start_i: int,
    parent_indent: int,
    name_types: dict[str, str],
    trivia: list[JsonVal],
    comments: list[str],
    abs_ln: int,
) -> tuple[JsonVal, int]:
    """for 文をパースする。"""
    ln = block_lines[start_i]
    s = _strip_inline_comment(ln.strip())
    header, inline_suite = _split_header_inline_suite(s)
    indent = _leading_space_count(ln)
    # Parse: for TARGET in ITER:
    target_name, iter_text = _parse_for_header(header)
    if target_name == "":
        # Fallback
        span: SourceSpan = make_span(abs_ln, indent, abs_ln, indent + len(s))
        dummy = _parse_expr_text(ctx, "None", abs_ln, indent, name_types)
        return ExprStmt(source_span=span, value=dummy), start_i + 1

    # Collect body
    sub_lines: list[str] = []
    end_i = start_i + 1
    if inline_suite != "":
        body_stmts = _parse_inline_suite(ctx, inline_suite, abs_ln, indent + 4, name_types, "for")
    else:
        sub_lines, end_i = _collect_sub_block(block_lines, start_i + 1, indent)
        body_stmts = _parse_block_lines(ctx, sub_lines, name_types, "for")

    # Determine end span
    end_ln = abs_ln
    end_col = indent + len(s)
    if len(sub_lines) > 0:
        for bl in reversed(sub_lines):
            if bl.strip() != "":
                end_ln = _find_abs_line(ctx.lines, bl, abs_ln - 1)
                end_col = len(bl.rstrip())
                break

    span: SourceSpan = make_span(abs_ln, 0, end_ln, end_col)

    # EAST1: range() は変換しない。全て For ノード。
    iter_expr = _parse_expr_text(ctx, iter_text, abs_ln, _find_expr_col(ctx, iter_text, abs_ln, indent), name_types)
    # Tuple unpacking target: for i, x in ...
    target: JsonVal
    target_col = _find_expr_col(ctx, target_name, abs_ln, indent + 4)
    if "," in target_name:
        target = _parse_tuple_or_expr(ctx, target_name, abs_ln, target_col, name_types)
    else:
        target = _make_name_expr(target_name, abs_ln, indent + 4, ctx)
    empty_orelse: list[JsonVal] = []
    for_stmt = For(
        source_span=span,
        target=target,
        iter_expr=iter_expr,
        body=body_stmts,
        orelse=empty_orelse,
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
    trivia: list[JsonVal],
    comments: list[str],
    abs_ln: int,
) -> tuple[JsonVal, int]:
    """while 文をパースする。"""
    ln = block_lines[start_i]
    s = _strip_inline_comment(ln.strip())
    header, inline_suite = _split_header_inline_suite(s)
    indent = _leading_space_count(ln)
    # Parse: while COND:
    cond_text = _rstrip_one_char(header[6:], ":").strip()
    test = _parse_expr_text(ctx, cond_text, abs_ln, _find_expr_col(ctx, cond_text, abs_ln, indent + 6), name_types)

    sub_lines: list[str] = []
    end_i = start_i + 1
    if inline_suite != "":
        body_stmts = _parse_inline_suite(ctx, inline_suite, abs_ln, indent + 4, name_types, "while")
    else:
        sub_lines, end_i = _collect_sub_block(block_lines, start_i + 1, indent)
        body_stmts = _parse_block_lines(ctx, sub_lines, name_types, "while")

    end_ln = abs_ln
    end_col = indent + len(s)
    if len(sub_lines) > 0:
        for bl in reversed(sub_lines):
            if bl.strip() != "":
                end_ln = _find_abs_line(ctx.lines, bl, abs_ln - 1)
                end_col = len(bl.rstrip())
                break

    span: SourceSpan = make_span(abs_ln, indent, end_ln, end_col)
    empty_while_orelse: list[JsonVal] = []
    while_node = While(source_span=span, test=test, body=body_stmts, orelse=empty_while_orelse)
    return while_node.to_jv(), end_i


def _parse_with_stmt(
    ctx: ParseContext,
    block_lines: list[str],
    start_i: int,
    parent_indent: int,
    name_types: dict[str, str],
    trivia: list[JsonVal],
    comments: list[str],
    abs_ln: int,
) -> tuple[JsonVal, int]:
    """with 文をパースする。with EXPR as VAR:"""
    ln = block_lines[start_i]
    s = _strip_inline_comment(ln.strip())
    header, inline_suite = _split_header_inline_suite(s)
    indent = _leading_space_count(ln)
    # Parse: with EXPR as VAR:
    inner = _rstrip_one_char(header[5:], ":").strip()  # strip "with " prefix and trailing ":"
    var_name: str = ""
    ctx_text: str = inner
    if " as " in inner:
        as_split = _split_last_as(inner)
        ctx_text = as_split[0].strip()
        var_name = as_split[1].strip()

    context_expr = _parse_expr_text(ctx, ctx_text, abs_ln, _find_expr_col(ctx, ctx_text, abs_ln, indent + 5), name_types)

    sub_lines: list[str] = []
    end_i = start_i + 1
    if inline_suite != "":
        body_stmts = _parse_inline_suite(ctx, inline_suite, abs_ln, indent + 4, name_types, "with")
    else:
        sub_lines, end_i = _collect_sub_block(block_lines, start_i + 1, indent)
        body_stmts = _parse_block_lines(ctx, sub_lines, name_types, "with")

    end_ln = abs_ln
    end_col = indent + len(s)
    if len(sub_lines) > 0:
        for bl in reversed(sub_lines):
            if bl.strip() != "":
                end_ln = _find_abs_line(ctx.lines, bl, abs_ln - 1)
                end_col = len(bl.rstrip())
                break

    span: SourceSpan = make_span(abs_ln, indent, end_ln, end_col)
    with_node = With(source_span=span, context_expr=context_expr, var_name=var_name, body=body_stmts)
    return with_node.to_jv(), end_i


def _parse_if_stmt(
    ctx: ParseContext,
    block_lines: list[str],
    start_i: int,
    parent_indent: int,
    name_types: dict[str, str],
    trivia: list[JsonVal],
    comments: list[str],
    abs_ln: int,
) -> tuple[JsonVal, int]:
    """if/elif/else 文をパースする。"""
    ln = block_lines[start_i]
    s = _strip_inline_comment(ln.strip())
    header_suite = _split_header_inline_suite(s)
    header = header_suite[0]
    inline_suite = header_suite[1]
    indent = _leading_space_count(ln)
    # Parse condition
    cond_text = _rstrip_one_char(header[3:], ":").strip()
    test = _parse_expr_text(ctx, cond_text, abs_ln, _find_expr_col(ctx, cond_text, abs_ln, indent + 3), name_types)

    # Collect then block
    then_lines: list[str] = []
    next_i = start_i + 1
    if inline_suite != "":
        then_stmts = _parse_inline_suite(ctx, inline_suite, abs_ln, indent + 4, name_types, "if")
    else:
        then_collect = _collect_sub_block(block_lines, start_i + 1, indent)
        then_lines = then_collect[0]
        next_i = then_collect[1]
        then_stmts = _parse_block_lines(ctx, then_lines, name_types, "if")

    # Check for elif / else
    orelse: list[JsonVal] = []
    if next_i < len(block_lines):
        next_ln = block_lines[next_i]
        next_s = next_ln.strip()
        next_indent = _leading_space_count(next_ln) if next_s != "" else 0
        if next_indent == indent:
            if next_s.startswith("elif "):
                # Convert elif to nested if
                elif_result = _parse_elif_stmt(ctx, block_lines, next_i, indent, name_types, abs_ln)
                elif_stmt = elif_result[0]
                next_i = elif_result[1]
                orelse = [elif_stmt]
            elif next_s.startswith("else:") or next_s == "else:":
                else_header_suite = _split_header_inline_suite(_strip_inline_comment(next_s))
                else_header = else_header_suite[0]
                else_inline_suite = else_header_suite[1]
                if else_inline_suite != "":
                    orelse = _parse_inline_suite(
                        ctx, else_inline_suite, _find_abs_line(ctx.lines, next_ln, abs_ln - 1), indent + 4, name_types, "else"
                    )
                    next_i += 1
                else:
                    else_collect = _collect_sub_block(block_lines, next_i + 1, indent)
                    else_lines = else_collect[0]
                    next_i = else_collect[1]
                    orelse = _parse_block_lines(ctx, else_lines, name_types, "else")

    end_ln = abs_ln
    end_col = indent + len(s)
    if len(orelse) > 0:
        last_stmt = orelse[-1]
        last_stmt_end_ln = _stmt_end_lineno(last_stmt)
        if last_stmt_end_ln > 0:
            end_ln = last_stmt_end_ln
            end_col = _stmt_end_col(last_stmt)
    elif len(then_lines) > 0:
        for bl in reversed(then_lines):
            if bl.strip() != "":
                end_ln = _find_abs_line(ctx.lines, bl, abs_ln - 1)
                end_col = len(bl.rstrip())
                break

    span: SourceSpan = make_span(abs_ln, indent, end_ln, end_col)
    if_stmt = If(source_span=span, test=test, body=then_stmts, orelse=orelse)
    if len(trivia) > 0:
        if_stmt.leading_trivia = list(trivia)
    if len(comments) > 0:
        if_stmt.leading_comments = list(comments)
    return if_stmt.to_jv(), next_i


def _parse_elif_stmt(
    ctx: ParseContext,
    block_lines: list[str],
    start_i: int,
    parent_indent: int,
    name_types: dict[str, str],
    line_hint: int,
) -> tuple[JsonVal, int]:
    """elif 節を If ノードとしてパースする。"""
    ln = block_lines[start_i]
    s = _strip_inline_comment(ln.strip())
    header_suite = _split_header_inline_suite(s)
    header = header_suite[0]
    inline_suite = header_suite[1]
    indent = _leading_space_count(ln)
    abs_ln = _find_abs_line(ctx.lines, ln, line_hint - 1)

    cond_text = _rstrip_one_char(header[5:], ":").strip()
    test = _parse_expr_text(ctx, cond_text, abs_ln, _find_expr_col(ctx, cond_text, abs_ln, indent + 5), name_types)

    then_lines: list[str] = []
    next_i = start_i + 1
    if inline_suite != "":
        then_stmts = _parse_inline_suite(ctx, inline_suite, abs_ln, indent + 4, name_types, "elif")
    else:
        then_collect = _collect_sub_block(block_lines, start_i + 1, indent)
        then_lines = then_collect[0]
        next_i = then_collect[1]
        then_stmts = _parse_block_lines(ctx, then_lines, name_types, "elif")

    orelse: list[JsonVal] = []
    if next_i < len(block_lines):
        next_ln = block_lines[next_i]
        next_s = next_ln.strip()
        next_indent = _leading_space_count(next_ln) if next_s != "" else 0
        if next_indent == indent:
            if next_s.startswith("elif "):
                elif_result = _parse_elif_stmt(ctx, block_lines, next_i, indent, name_types, abs_ln)
                elif_stmt = elif_result[0]
                next_i = elif_result[1]
                orelse = [elif_stmt]
            elif next_s.startswith("else:"):
                else_header_suite = _split_header_inline_suite(_strip_inline_comment(next_s))
                else_header = else_header_suite[0]
                else_inline_suite = else_header_suite[1]
                if else_inline_suite != "":
                    orelse = _parse_inline_suite(
                        ctx, else_inline_suite, _find_abs_line(ctx.lines, next_ln, abs_ln - 1), indent + 4, name_types, "else"
                    )
                    next_i += 1
                else:
                    else_collect = _collect_sub_block(block_lines, next_i + 1, indent)
                    else_lines = else_collect[0]
                    next_i = else_collect[1]
                    orelse = _parse_block_lines(ctx, else_lines, name_types, "else")

    end_ln = abs_ln
    end_col = indent + len(s)
    if len(orelse) > 0:
        last_stmt = orelse[-1]
        last_stmt_end_ln = _stmt_end_lineno(last_stmt)
        if last_stmt_end_ln > 0:
            end_ln = last_stmt_end_ln
            end_col = _stmt_end_col(last_stmt)
    elif len(then_lines) > 0:
        for bl in reversed(then_lines):
            if bl.strip() != "":
                end_ln = _find_abs_line(ctx.lines, bl, abs_ln - 1)
                end_col = len(bl.rstrip())
                break
    span: SourceSpan = make_span(abs_ln, indent, end_ln, end_col)
    elif_node = If(source_span=span, test=test, body=then_stmts, orelse=orelse)
    return elif_node.to_jv(), next_i


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
        indent = _leading_space_count(ln)
        if indent <= parent_indent:
            break
        result.append(ln)
        i += 1
    return result, i


# ---------------------------------------------------------------------------
# Arg usage analysis
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Postprocessing + meta building
# ---------------------------------------------------------------------------

def _postprocess(ctx: ParseContext, body_items: list[JsonVal], renamed_symbols: dict[str, str]) -> None:
    """Phase 3: 後処理（main リネーム）。"""
    # Rename main → __pytra_main
    for stmt in body_items:
        stmt_obj = json.JsonValue(stmt).as_obj()
        if stmt_obj is None:
            continue
        if _json_obj_str(stmt_obj.raw, "kind") == "FunctionDef" and _json_obj_str(stmt_obj.raw, "name") == "main":
            renamed_symbols["main"] = "__pytra_main"
            stmt_obj.raw["name"] = "__pytra_main"


def _build_meta(ctx: ParseContext, qualified_refs: list[dict[str, JsonVal]]) -> dict[str, JsonVal]:
    """Module.meta を構築する (EAST1: 構文情報のみ、runtime 解決なし)。"""
    import_symbols_jv: dict[str, JsonVal] = {}
    for local, info in ctx.import_symbols.items():
        info_jv: dict[str, JsonVal] = {}
        for info_key, info_value in info.items():
            info_jv[info_key] = info_value
        import_symbols_jv[local] = info_jv

    import_resolution: dict[str, JsonVal] = {
        "bindings": list(ctx.import_bindings),
        "qualified_refs": list(qualified_refs),
    }

    import_modules_jv: dict[str, JsonVal] = {}
    for module_key, module_value in ctx.import_modules.items():
        import_modules_jv[module_key] = module_value

    meta: dict[str, JsonVal] = {
        "import_resolution": import_resolution,
        "import_bindings": list(ctx.import_bindings),
        "qualified_symbol_refs": list(qualified_refs),
        "import_modules": import_modules_jv,
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
                return _unescape_string(s[3:-3])
        break
    return None
