"""Pure Python JSON utilities for selfhost-friendly transpilation."""

from __future__ import annotations

from pytra.std.typing import Any


_EMPTY: str = ""
_COMMA_NL: str = ",\n"
_HEX_DIGITS: str = "0123456789abcdef"


def _is_ws(ch: str) -> bool:
    return ch == " " or ch == "\t" or ch == "\r" or ch == "\n"


def _is_digit(ch: str) -> bool:
    return ch >= "0" and ch <= "9"


def _hex_value(ch: str) -> int:
    if ch >= "0" and ch <= "9":
        return int(ch)
    if ch == "a" or ch == "A":
        return 10
    if ch == "b" or ch == "B":
        return 11
    if ch == "c" or ch == "C":
        return 12
    if ch == "d" or ch == "D":
        return 13
    if ch == "e" or ch == "E":
        return 14
    if ch == "f" or ch == "F":
        return 15
    raise ValueError("invalid json unicode escape")


def _int_from_hex4(hx: str) -> int:
    if len(hx) != 4:
        raise ValueError("invalid json unicode escape")
    v0 = _hex_value(hx[0:1])
    v1 = _hex_value(hx[1:2])
    v2 = _hex_value(hx[2:3])
    v3 = _hex_value(hx[3:4])
    return (v0 * 4096) + (v1 * 256) + (v2 * 16) + v3


def _hex4(code: int) -> str:
    v = code % 65536
    d3 = v % 16
    v = v // 16
    d2 = v % 16
    v = v // 16
    d1 = v % 16
    v = v // 16
    d0 = v % 16
    p0: str = _HEX_DIGITS[d0 : d0 + 1]
    p1: str = _HEX_DIGITS[d1 : d1 + 1]
    p2: str = _HEX_DIGITS[d2 : d2 + 1]
    p3: str = _HEX_DIGITS[d3 : d3 + 1]
    return p0 + p1 + p2 + p3


class _JsonParser:
    text: str
    n: int64
    i: int64

    def __init__(self, text: str) -> None:
        self.text = text
        self.n = len(text)
        self.i = 0

    def parse(self) -> object:
        self._skip_ws()
        out = self._parse_value()
        self._skip_ws()
        if self.i != self.n:
            raise ValueError("invalid json: trailing characters")
        return out

    def _skip_ws(self) -> None:
        while self.i < self.n and _is_ws(self.text[self.i]):
            self.i += 1

    def _parse_value(self) -> object:
        if self.i >= self.n:
            raise ValueError("invalid json: unexpected end")
        ch = self.text[self.i]
        if ch == "{":
            return self._parse_object()
        if ch == "[":
            return self._parse_array()
        if ch == '"':
            return self._parse_string()
        if ch == "t" and self.text[self.i : self.i + 4] == "true":
            self.i += 4
            return True
        if ch == "f" and self.text[self.i : self.i + 5] == "false":
            self.i += 5
            return False
        if ch == "n" and self.text[self.i : self.i + 4] == "null":
            self.i += 4
            return None
        return self._parse_number()

    def _parse_object(self) -> dict[str, object]:
        out: dict[str, object] = {}
        self.i += 1
        self._skip_ws()
        if self.i < self.n and self.text[self.i] == "}":
            self.i += 1
            return out
        while True:
            self._skip_ws()
            if self.i >= self.n or self.text[self.i] != '"':
                raise ValueError("invalid json object key")
            key = self._parse_string()
            self._skip_ws()
            if self.i >= self.n or self.text[self.i] != ":":
                raise ValueError("invalid json object: missing ':'")
            self.i += 1
            self._skip_ws()
            out[key] = self._parse_value()
            self._skip_ws()
            if self.i >= self.n:
                raise ValueError("invalid json object: unexpected end")
            ch = self.text[self.i]
            self.i += 1
            if ch == "}":
                return out
            if ch != ",":
                raise ValueError("invalid json object separator")

    def _parse_array(self) -> list[object]:
        out: list[object] = []
        self.i += 1
        self._skip_ws()
        if self.i < self.n and self.text[self.i] == "]":
            self.i += 1
            return out
        while True:
            self._skip_ws()
            out.append(self._parse_value())
            self._skip_ws()
            if self.i >= self.n:
                raise ValueError("invalid json array: unexpected end")
            ch = self.text[self.i]
            self.i += 1
            if ch == "]":
                return out
            if ch != ",":
                raise ValueError("invalid json array separator")

    def _parse_string(self) -> str:
        if self.text[self.i] != '"':
            raise ValueError("invalid json string")
        self.i += 1
        out_chars: list[str] = []
        while self.i < self.n:
            ch = self.text[self.i]
            self.i += 1
            if ch == '"':
                return _EMPTY.join(out_chars)
            if ch == "\\":
                if self.i >= self.n:
                    raise ValueError("invalid json string escape")
                esc = self.text[self.i]
                self.i += 1
                if esc == '"':
                    out_chars.append('"')
                elif esc == "\\":
                    out_chars.append("\\")
                elif esc == "/":
                    out_chars.append("/")
                elif esc == "b":
                    out_chars.append("\b")
                elif esc == "f":
                    out_chars.append("\f")
                elif esc == "n":
                    out_chars.append("\n")
                elif esc == "r":
                    out_chars.append("\r")
                elif esc == "t":
                    out_chars.append("\t")
                elif esc == "u":
                    if self.i + 4 > self.n:
                        raise ValueError("invalid json unicode escape")
                    hx = self.text[self.i : self.i + 4]
                    self.i += 4
                    out_chars.append(chr(_int_from_hex4(hx)))
                else:
                    raise ValueError("invalid json escape")
            else:
                out_chars.append(ch)
        raise ValueError("unterminated json string")

    def _parse_number(self) -> object:
        start = self.i
        if self.text[self.i] == "-":
            self.i += 1
        if self.i >= self.n:
            raise ValueError("invalid json number")
        if self.text[self.i] == "0":
            self.i += 1
        else:
            if not _is_digit(self.text[self.i]):
                raise ValueError("invalid json number")
            while self.i < self.n and _is_digit(self.text[self.i]):
                self.i += 1
        is_float = False
        if self.i < self.n and self.text[self.i] == ".":
            is_float = True
            self.i += 1
            if self.i >= self.n or not _is_digit(self.text[self.i]):
                raise ValueError("invalid json number")
            while self.i < self.n and _is_digit(self.text[self.i]):
                self.i += 1
        if self.i < self.n:
            exp_ch = self.text[self.i]
            if exp_ch == "e" or exp_ch == "E":
                is_float = True
                self.i += 1
                if self.i < self.n:
                    sign = self.text[self.i]
                    if sign == "+" or sign == "-":
                        self.i += 1
                if self.i >= self.n or not _is_digit(self.text[self.i]):
                    raise ValueError("invalid json exponent")
                while self.i < self.n and _is_digit(self.text[self.i]):
                    self.i += 1
        token = self.text[start : self.i]
        if is_float:
            num_f: float = float(token)
            return num_f
        num_i: int = int(token)
        return num_i


def loads(text: str) -> object:
    return _JsonParser(text).parse()


def _escape_str(s: str, ensure_ascii: bool) -> str:
    out: list[str] = ['"']
    for ch in s:
        code: int = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\b":
            out.append("\\b")
        elif ch == "\f":
            out.append("\\f")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif ensure_ascii and code > 0x7F:
            out.append("\\u" + _hex4(code))
        else:
            out.append(ch)
    out.append('"')
    return _EMPTY.join(out)


def _dump_json_list(
    values: list[object],
    ensure_ascii: bool,
    indent: int | None,
    item_sep: str,
    key_sep: str,
    level: int,
) -> str:
    if len(values) == 0:
        return "[]"
    if indent is None:
        dumped: list[str] = []
        for x in values:
            dumped_txt: str = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level)
            dumped.append(dumped_txt)
        return "[" + item_sep.join(dumped) + "]"
    indent_i: int = int(indent)
    inner: list[str] = []
    for x in values:
        prefix: str = " " * (indent_i * (level + 1))
        value_txt: str = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1)
        inner.append(prefix + value_txt)
    return "[\n" + _COMMA_NL.join(inner) + "\n" + (" " * (indent_i * level)) + "]"


def _dump_json_dict(
    values: dict[str, object],
    ensure_ascii: bool,
    indent: int | None,
    item_sep: str,
    key_sep: str,
    level: int,
) -> str:
    if len(values) == 0:
        return "{}"
    if indent is None:
        parts: list[str] = []
        for k, x in values.items():
            k_txt: str = _escape_str(str(k), ensure_ascii)
            v_txt: str = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level)
            parts.append(k_txt + key_sep + v_txt)
        return "{" + item_sep.join(parts) + "}"
    indent_i: int = int(indent)
    inner: list[str] = []
    for k, x in values.items():
        prefix: str = " " * (indent_i * (level + 1))
        k_txt: str = _escape_str(str(k), ensure_ascii)
        v_txt: str = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1)
        inner.append(prefix + k_txt + key_sep + v_txt)
    return "{\n" + _COMMA_NL.join(inner) + "\n" + (" " * (indent_i * level)) + "}"


def _dump_json_value(
    v: object,
    ensure_ascii: bool,
    indent: int | None,
    item_sep: str,
    key_sep: str,
    level: int,
) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return str(v)
    if isinstance(v, str):
        return _escape_str(v, ensure_ascii)
    if isinstance(v, list):
        as_list: list[object] = list(v)
        return _dump_json_list(as_list, ensure_ascii, indent, item_sep, key_sep, level)
    if isinstance(v, dict):
        as_dict: dict[str, object] = dict(v)
        return _dump_json_dict(as_dict, ensure_ascii, indent, item_sep, key_sep, level)
    raise TypeError("json.dumps unsupported type")


def dumps(
    obj: Any,
    *,
    ensure_ascii: bool = True,
    indent: int | None = None,
    separators: tuple[str, str] | None = None,
) -> str:
    item_sep = ","
    key_sep = ":" if indent is None else ": "
    if separators is not None:
        item_sep, key_sep = separators
    return _dump_json_value(obj, ensure_ascii, indent, item_sep, key_sep, 0)
