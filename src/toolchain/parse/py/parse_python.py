"""Python frontend: .py → .py.east1

自前パーサーで Python ソースを EAST1 (east_stage=1) に変換する。
toolchain/ には依存しない。
"""

from __future__ import annotations

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain.parse.py.nodes import Module
from toolchain.parse.py.parser import parse_python_source


def _find_from(text: str, needle: str, start: int) -> int:
    if start <= 0:
        return text.find(needle)
    suffix: str = text[start:]
    pos: int = suffix.find(needle)
    if pos < 0:
        return -1
    return start + pos


def _bracket_depth_str_aware(text: str) -> int:
    """Count net bracket depth, ignoring strings and comments."""
    depth: int = 0
    in_str: str = ""
    i: int = 0
    n: int = len(text)
    while i < n:
        ch: str = text[i]
        if in_str != "":
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == in_str:
                in_str = ""
            i += 1
            continue
        if ch == "#":
            break
        if ch == '"' or ch == "'":
            if i + 2 < n and text[i + 1] == ch and text[i + 2] == ch:
                close: str = ch + ch + ch
                end: int = _find_from(text, close, i + 3)
                i = end + 3 if end >= 0 else n
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


def _unclosed_triple_quote(line: str) -> str:
    """Return the triple-quote delimiter if line opens but doesn't close one, else ""."""
    in_single: bool = False
    in_double: bool = False
    i: int = 0
    n: int = len(line)
    while i < n:
        ch: str = line[i]
        if in_single:
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == "'":
                in_single = False
            i += 1
            continue
        if in_double:
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == '"':
                in_double = False
            i += 1
            continue
        if ch == "#":
            break
        if ch == "'" or ch == '"':
            if i + 2 < n and line[i + 1] == ch and line[i + 2] == ch:
                tq: str = ch + ch + ch
                end: int = _find_from(line, tq, i + 3)
                if end < 0:
                    return tq
                i = end + 3
                continue
            if ch == "'":
                in_single = True
            else:
                in_double = True
        i += 1
    return ""


def _join_continuation_lines(source: str) -> str:
    """Join lines with unclosed brackets into single logical lines.

    Python's implicit line continuation inside (), [], {}.
    Blank placeholder lines are inserted to keep line numbers consistent.
    """
    lines: list[str] = source.split("\n")
    result: list[str] = []
    i: int = 0
    n: int = len(lines)
    while i < n:
        line: str = lines[i]

        # Check for unclosed triple-quote string
        tq: str = _unclosed_triple_quote(line)
        if tq != "":
            parts: list[str] = [line.rstrip()]
            i += 1
            while i < n:
                nxt: str = lines[i]
                parts.append(nxt.rstrip())
                i += 1
                if tq in nxt:
                    break
            escaped_parts: list[str] = []
            for part in parts:
                escaped_parts.append(part.replace("\\", "\\\\"))
            joined_tq: str = "\\n".join(escaped_parts)
            result.append(joined_tq)
            skipped_tq: int = len(parts) - 1
            for _ in range(skipped_tq):
                result.append("")
            continue

        depth: int = _bracket_depth_str_aware(line)
        if depth <= 0:
            result.append(line)
            i += 1
            continue
        # Unclosed bracket: join subsequent lines, preserve first line indent
        parts2: list[str] = [line.rstrip()]
        i += 1
        while i < n and depth > 0:
            nxt2: str = lines[i]
            parts2.append(nxt2.strip())
            depth += _bracket_depth_str_aware(nxt2)
            i += 1
        joined2: str = " ".join(parts2)
        result.append(joined2)
        skipped: int = len(parts2) - 1
        for _ in range(skipped):
            result.append("")
    return "\n".join(result)


def parse_python_file_to_module(input_path: str) -> Module:
    """ファイルを読み込み、EAST1 Module ノードを返す。"""
    source: str = Path(input_path).read_text(encoding="utf-8")
    source = _join_continuation_lines(source)
    return parse_python_source(source, input_path)


def parse_python_file(input_path: str) -> dict[str, JsonVal]:
    """ファイルを読み込み、EAST1 ドキュメント (dict) を返す。"""
    module: Module = parse_python_file_to_module(input_path)
    doc: dict[str, JsonVal] = module.to_jv()
    return doc
