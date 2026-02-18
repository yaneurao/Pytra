"""Pure Python JSON utilities for selfhost-friendly transpilation."""

from __future__ import annotations

from typing import Any


class _JsonParser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.n = len(text)
        self.i = 0

    def parse(self) -> Any:
        self._skip_ws()
        out = self._parse_value()
        self._skip_ws()
        if self.i != self.n:
            raise ValueError("invalid json: trailing characters")
        return out

    def _skip_ws(self) -> None:
        while self.i < self.n and self.text[self.i] in " \t\r\n":
            self.i += 1

    def _parse_value(self) -> Any:
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

    def _parse_object(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
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

    def _parse_array(self) -> list[Any]:
        out: list[Any] = []
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
                return "".join(out_chars)
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
                    try:
                        out_chars.append(chr(int(hx, 16)))
                    except ValueError as exc:
                        raise ValueError("invalid json unicode escape") from exc
                else:
                    raise ValueError("invalid json escape")
            else:
                out_chars.append(ch)
        raise ValueError("unterminated json string")

    def _parse_number(self) -> int | float:
        start = self.i
        if self.text[self.i] == "-":
            self.i += 1
        if self.i >= self.n:
            raise ValueError("invalid json number")
        if self.text[self.i] == "0":
            self.i += 1
        else:
            if not self.text[self.i].isdigit():
                raise ValueError("invalid json number")
            while self.i < self.n and self.text[self.i].isdigit():
                self.i += 1
        is_float = False
        if self.i < self.n and self.text[self.i] == ".":
            is_float = True
            self.i += 1
            if self.i >= self.n or not self.text[self.i].isdigit():
                raise ValueError("invalid json number")
            while self.i < self.n and self.text[self.i].isdigit():
                self.i += 1
        if self.i < self.n and self.text[self.i] in {"e", "E"}:
            is_float = True
            self.i += 1
            if self.i < self.n and self.text[self.i] in {"+", "-"}:
                self.i += 1
            if self.i >= self.n or not self.text[self.i].isdigit():
                raise ValueError("invalid json exponent")
            while self.i < self.n and self.text[self.i].isdigit():
                self.i += 1
        token = self.text[start : self.i]
        return float(token) if is_float else int(token)


def loads(text: str) -> Any:
    return _JsonParser(text).parse()


def _escape_str(s: str, ensure_ascii: bool) -> str:
    out: list[str] = ['"']
    for ch in s:
        code = ord(ch)
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
            out.append("\\u" + format(code & 0xFFFF, "04x"))
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def dumps(
    obj: Any,
    *,
    ensure_ascii: bool = True,
    indent: int | None = None,
    separators: tuple[str, str] | None = None,
) -> str:
    if separators is None:
        if indent is None:
            item_sep = ","
            key_sep = ":"
        else:
            item_sep = ","
            key_sep = ": "
    else:
        item_sep, key_sep = separators

    def _dump(v: Any, level: int) -> str:
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        if isinstance(v, str):
            return _escape_str(v, ensure_ascii)
        if isinstance(v, list):
            if len(v) == 0:
                return "[]"
            if indent is None:
                return "[" + item_sep.join(_dump(x, level) for x in v) + "]"
            inner = []
            for x in v:
                inner.append(" " * (indent * (level + 1)) + _dump(x, level + 1))
            return "[\n" + ",\n".join(inner) + "\n" + (" " * (indent * level)) + "]"
        if isinstance(v, dict):
            if len(v) == 0:
                return "{}"
            if indent is None:
                parts: list[str] = []
                for k, x in v.items():
                    parts.append(_escape_str(str(k), ensure_ascii) + key_sep + _dump(x, level))
                return "{" + item_sep.join(parts) + "}"
            inner = []
            for k, x in v.items():
                inner.append(
                    " " * (indent * (level + 1))
                    + _escape_str(str(k), ensure_ascii)
                    + key_sep
                    + _dump(x, level + 1)
                )
            return "{\n" + ",\n".join(inner) + "\n" + (" " * (indent * level)) + "}"
        raise TypeError(f"json.dumps unsupported type: {type(v).__name__}")

    return _dump(obj, 0)

