"""Pure Python JSON utilities for selfhost-friendly transpilation."""

from __future__ import annotations

from pytra.std import abi


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


@abi(ret="value")
def _json_array_items(raw: object) -> list[object]:
    return list(raw)


@abi(ret="value")
def _json_new_array() -> list[object]:
    return list()


def _json_obj_require(raw: dict[str, object], key: str) -> object:
    for k, value in raw.items():
        if k == key:
            return value
    raise ValueError("json object key not found: " + key)


def _json_indent_value(indent: int | None) -> int:
    if indent is None:
        raise ValueError("json indent is required")
    indent_i: int = indent
    return indent_i


class JsonObj:
    raw: dict[str, object]

    def __init__(self, raw: dict[str, object]) -> None:
        self.raw = raw

    def get(self, key: str) -> JsonValue | None:
        if key not in self.raw:
            return None
        value = _json_obj_require(self.raw, key)
        return JsonValue(value)

    def get_obj(self, key: str) -> JsonObj | None:
        if key not in self.raw:
            return None
        value = _json_obj_require(self.raw, key)
        return JsonValue(value).as_obj()

    def get_arr(self, key: str) -> JsonArr | None:
        if key not in self.raw:
            return None
        value = _json_obj_require(self.raw, key)
        return JsonValue(value).as_arr()

    def get_str(self, key: str) -> str | None:
        if key not in self.raw:
            return None
        value = _json_obj_require(self.raw, key)
        return JsonValue(value).as_str()

    def get_int(self, key: str) -> int | None:
        if key not in self.raw:
            return None
        value = _json_obj_require(self.raw, key)
        return JsonValue(value).as_int()

    def get_float(self, key: str) -> float | None:
        if key not in self.raw:
            return None
        value = _json_obj_require(self.raw, key)
        return JsonValue(value).as_float()

    def get_bool(self, key: str) -> bool | None:
        if key not in self.raw:
            return None
        value = _json_obj_require(self.raw, key)
        return JsonValue(value).as_bool()


class JsonArr:
    raw: list[object]

    def __init__(self, raw: list[object]) -> None:
        self.raw = raw

    def get(self, index: int) -> JsonValue | None:
        if index < 0 or index >= len(_json_array_items(self.raw)):
            return None
        return JsonValue(_json_array_items(self.raw)[index])

    def get_obj(self, index: int) -> JsonObj | None:
        if index < 0 or index >= len(_json_array_items(self.raw)):
            return None
        return JsonValue(_json_array_items(self.raw)[index]).as_obj()

    def get_arr(self, index: int) -> JsonArr | None:
        if index < 0 or index >= len(_json_array_items(self.raw)):
            return None
        return JsonValue(_json_array_items(self.raw)[index]).as_arr()

    def get_str(self, index: int) -> str | None:
        if index < 0 or index >= len(_json_array_items(self.raw)):
            return None
        return JsonValue(_json_array_items(self.raw)[index]).as_str()

    def get_int(self, index: int) -> int | None:
        if index < 0 or index >= len(_json_array_items(self.raw)):
            return None
        return JsonValue(_json_array_items(self.raw)[index]).as_int()

    def get_float(self, index: int) -> float | None:
        if index < 0 or index >= len(_json_array_items(self.raw)):
            return None
        return JsonValue(_json_array_items(self.raw)[index]).as_float()

    def get_bool(self, index: int) -> bool | None:
        if index < 0 or index >= len(_json_array_items(self.raw)):
            return None
        return JsonValue(_json_array_items(self.raw)[index]).as_bool()


class JsonValue:
    raw: object

    def __init__(self, raw: object) -> None:
        self.raw = raw

    def as_obj(self) -> JsonObj | None:
        raw = self.raw
        if isinstance(raw, dict):
            raw_obj: dict[str, object] = dict(raw)
            return JsonObj(raw_obj)
        return None

    def as_arr(self) -> JsonArr | None:
        raw = self.raw
        if isinstance(raw, list):
            raw_arr: list[object] = list(raw)
            return JsonArr(raw_arr)
        return None

    def as_str(self) -> str | None:
        raw = self.raw
        if isinstance(raw, str):
            return raw
        return None

    def as_int(self) -> int | None:
        raw = self.raw
        if isinstance(raw, bool):
            return None
        if isinstance(raw, int):
            raw_i: int = int(raw)
            return raw_i
        return None

    def as_float(self) -> float | None:
        raw = self.raw
        if isinstance(raw, float):
            raw_f: float = float(raw)
            return raw_f
        return None

    def as_bool(self) -> bool | None:
        raw = self.raw
        if isinstance(raw, bool):
            raw_b: bool = bool(raw)
            return raw_b
        return None


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
        out = _json_new_array()
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


def loads_obj(text: str) -> JsonObj | None:
    value = _JsonParser(text).parse()
    if isinstance(value, dict):
        raw_obj: dict[str, object] = dict(value)
        return JsonObj(raw_obj)
    return None


def loads_arr(text: str) -> JsonArr | None:
    value = _JsonParser(text).parse()
    if isinstance(value, list):
        raw_arr: list[object] = list(value)
        return JsonArr(raw_arr)
    return None


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
        return "[" + _join_strs(dumped, item_sep) + "]"
    indent_i: int = _json_indent_value(indent)
    inner: list[str] = []
    for x in values:
        prefix: str = " " * (indent_i * (level + 1))
        value_txt: str = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1)
        inner.append(prefix + value_txt)
    return "[\n" + _join_strs(inner, _COMMA_NL) + "\n" + (" " * (indent_i * level)) + "]"


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
        raw_b: bool = bool(v)
        return "true" if raw_b else "false"
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
    obj: object,
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
