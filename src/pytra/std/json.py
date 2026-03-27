"""Pure Python JSON utilities for selfhost-friendly transpilation."""

from __future__ import annotations

from pytra.typing import cast
from pytra.types import int64

type JsonVal = None | bool | int | float | str | list[JsonVal] | dict[str, JsonVal]

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


def _json_indent_value(indent: int64 | None) -> int64:
    if indent is None:
        raise ValueError("json indent is required")
    return cast(int64, indent)


def _jv_as_str(raw: JsonVal) -> str | None:
    if not isinstance(raw, str):
        return None
    return cast(str, raw)


def _jv_as_int(raw: JsonVal) -> int | None:
    if not isinstance(raw, int):
        return None
    return cast(int, raw)


def _jv_as_float(raw: JsonVal) -> float | None:
    if not isinstance(raw, float):
        return None
    return cast(float, raw)


def _jv_as_bool(raw: JsonVal) -> bool | None:
    if not isinstance(raw, bool):
        return None
    return cast(bool, raw)


def _jv_obj_require(raw: dict[str, JsonVal], key: str) -> JsonVal:
    for k, value in raw.items():
        if k == key:
            return value
    raise ValueError("json object key not found: " + key)


class JsonObj:
    raw: dict[str, JsonVal]

    def __init__(self, raw: dict[str, JsonVal]) -> None:
        self.raw = raw

    def get(self, key: str) -> JsonValue | None:
        if key not in self.raw:
            return None
        value: JsonValue | None = JsonValue(_jv_obj_require(self.raw, key))
        return value

    def get_obj(self, key: str) -> JsonObj | None:
        if key not in self.raw:
            return None
        value: JsonObj | None = JsonValue(_jv_obj_require(self.raw, key)).as_obj()
        return value

    def get_arr(self, key: str) -> JsonArr | None:
        if key not in self.raw:
            return None
        value: JsonArr | None = JsonValue(_jv_obj_require(self.raw, key)).as_arr()
        return value

    def get_str(self, key: str) -> str | None:
        if key not in self.raw:
            return None
        value: str | None = JsonValue(_jv_obj_require(self.raw, key)).as_str()
        return value

    def get_int(self, key: str) -> int | None:
        if key not in self.raw:
            return None
        value: int | None = JsonValue(_jv_obj_require(self.raw, key)).as_int()
        return value

    def get_float(self, key: str) -> float | None:
        if key not in self.raw:
            return None
        value: float | None = JsonValue(_jv_obj_require(self.raw, key)).as_float()
        return value

    def get_bool(self, key: str) -> bool | None:
        if key not in self.raw:
            return None
        value: bool | None = JsonValue(_jv_obj_require(self.raw, key)).as_bool()
        return value


class JsonArr:
    raw: list[JsonVal]

    def __init__(self, raw: list[JsonVal]) -> None:
        self.raw = raw

    def get(self, index: int) -> JsonValue | None:
        if index < 0 or index >= len(self.raw):
            return None
        value: JsonValue | None = JsonValue(self.raw[index])
        return value

    def get_obj(self, index: int) -> JsonObj | None:
        if index < 0 or index >= len(self.raw):
            return None
        value: JsonObj | None = JsonValue(self.raw[index]).as_obj()
        return value

    def get_arr(self, index: int) -> JsonArr | None:
        if index < 0 or index >= len(self.raw):
            return None
        value: JsonArr | None = JsonValue(self.raw[index]).as_arr()
        return value

    def get_str(self, index: int) -> str | None:
        if index < 0 or index >= len(self.raw):
            return None
        value: str | None = JsonValue(self.raw[index]).as_str()
        return value

    def get_int(self, index: int) -> int | None:
        if index < 0 or index >= len(self.raw):
            return None
        value: int | None = JsonValue(self.raw[index]).as_int()
        return value

    def get_float(self, index: int) -> float | None:
        if index < 0 or index >= len(self.raw):
            return None
        value: float | None = JsonValue(self.raw[index]).as_float()
        return value

    def get_bool(self, index: int) -> bool | None:
        if index < 0 or index >= len(self.raw):
            return None
        value: bool | None = JsonValue(self.raw[index]).as_bool()
        return value


class JsonValue:
    raw: JsonVal

    def __init__(self, raw: JsonVal) -> None:
        self.raw = raw

    def as_obj(self) -> JsonObj | None:
        jv: JsonVal = self.raw
        out: JsonObj | None = None
        if isinstance(jv, dict):
            out = JsonObj(cast(dict[str, JsonVal], jv))
        return out

    def as_arr(self) -> JsonArr | None:
        jv: JsonVal = self.raw
        out: JsonArr | None = None
        if isinstance(jv, list):
            out = JsonArr(cast(list[JsonVal], jv))
        return out

    def as_str(self) -> str | None:
        value: str | None = _jv_as_str(self.raw)
        return value

    def as_int(self) -> int | None:
        value: int | None = _jv_as_int(self.raw)
        return value

    def as_float(self) -> float | None:
        value: float | None = _jv_as_float(self.raw)
        return value

    def as_bool(self) -> bool | None:
        value: bool | None = _jv_as_bool(self.raw)
        return value


class _JsonParser:
    text: str
    n: int64
    i: int64

    def __init__(self, text: str) -> None:
        self.text = text
        self.n = len(text)
        self.i = 0

    def parse(self) -> JsonVal:
        self._skip_ws()
        out: JsonVal = self._parse_value()
        self._skip_ws()
        if self.i != self.n:
            raise ValueError("invalid json: trailing characters")
        return out

    def _skip_ws(self) -> None:
        while self.i < self.n and _is_ws(self.text[self.i]):
            self.i += 1

    def _parse_value(self) -> JsonVal:
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

    def _parse_object(self) -> dict[str, JsonVal]:
        out: dict[str, JsonVal] = {}
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

    def _parse_array(self) -> list[JsonVal]:
        out: list[JsonVal] = []
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
                return _join_strs(out_chars, _EMPTY)
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

    def _parse_number(self) -> JsonVal:
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


def loads(text: str) -> JsonValue:
    return JsonValue(_JsonParser(text).parse())


def loads_obj(text: str) -> JsonObj | None:
    val: JsonVal = _JsonParser(text).parse()
    out: JsonObj | None = None
    if isinstance(val, dict):
        out = JsonObj(cast(dict[str, JsonVal], val))
    return out


def loads_arr(text: str) -> JsonArr | None:
    val: JsonVal = _JsonParser(text).parse()
    out: JsonArr | None = None
    if isinstance(val, list):
        out = JsonArr(cast(list[JsonVal], val))
    return out


def _join_strs(parts: list[str], sep: str) -> str:
    if len(parts) == 0:
        return ""
    out: str = parts[0]
    i = 1
    while i < len(parts):
        out = out + sep + parts[i]
        i += 1
    return out


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
    return _join_strs(out, _EMPTY)


def _dump_json_list(
    values: list[JsonVal],
    ensure_ascii: bool,
    indent: int | None,
    item_sep: str,
    key_sep: str,
    level: int,
) -> str:
    is_empty = True
    for item in values:
        _ = item
        is_empty = False
        break
    if is_empty:
        return "[]"
    if indent is None:
        dumped: list[str] = []
        for x in values:
            dumped_txt: str = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level)
            dumped.append(dumped_txt)
        return "[" + _join_strs(dumped, item_sep) + "]"
    indent_i: int = _json_indent_value(indent)
    inner: list[str] = []
    for x in values:
        prefix: str = " " * (indent_i * (level + 1))
        value_txt: str = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1)
        inner.append(prefix + value_txt)
    return "[\n" + _join_strs(inner, _COMMA_NL) + "\n" + (" " * (indent_i * level)) + "]"


def _dump_json_dict(
    values: dict[str, JsonVal],
    ensure_ascii: bool,
    indent: int | None,
    item_sep: str,
    key_sep: str,
    level: int,
) -> str:
    is_empty = True
    for key in values:
        _ = key
        is_empty = False
        break
    if is_empty:
        return "{}"
    if indent is None:
        parts: list[str] = []
        for k, x in values.items():
            k_txt: str = _escape_str(str(k), ensure_ascii)
            v_txt: str = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level)
            parts.append(k_txt + key_sep + v_txt)
        return "{" + _join_strs(parts, item_sep) + "}"
    indent_i: int = _json_indent_value(indent)
    inner: list[str] = []
    for k, x in values.items():
        prefix: str = " " * (indent_i * (level + 1))
        k_txt: str = _escape_str(str(k), ensure_ascii)
        v_txt: str = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1)
        inner.append(prefix + k_txt + key_sep + v_txt)
    return "{\n" + _join_strs(inner, _COMMA_NL) + "\n" + (" " * (indent_i * level)) + "}"


def _dump_json_value(
    v: JsonVal,
    ensure_ascii: bool,
    indent: int | None,
    item_sep: str,
    key_sep: str,
    level: int,
) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        if str(v) == "True":
            return "true"
        return "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return str(v)
    if isinstance(v, str):
        return _escape_str(str(v), ensure_ascii)
    if isinstance(v, list):
        return _dump_json_list(v, ensure_ascii, indent, item_sep, key_sep, level)
    if isinstance(v, dict):
        return _dump_json_dict(v, ensure_ascii, indent, item_sep, key_sep, level)
    raise TypeError("json.dumps unsupported type")


def dumps(
    obj: JsonVal,
    *,
    ensure_ascii: bool = True,
    indent: int64 | None = None,
    separators: tuple[str, str] | None = None,
) -> str:
    item_sep = ","
    key_sep = ":" if indent is None else ": "
    if separators is not None:
        item_sep, key_sep = separators
    return _dump_json_value(obj, ensure_ascii, indent, item_sep, key_sep, 0)


def dumps_jv(
    jv: JsonVal,
    *,
    ensure_ascii: bool = True,
    indent: int64 | None = None,
    separators: tuple[str, str] | None = None,
) -> str:
    item_sep = ","
    key_sep = ":" if indent is None else ": "
    if separators is not None:
        item_sep, key_sep = separators
    return _dump_json_value(jv, ensure_ascii, indent, item_sep, key_sep, 0)
