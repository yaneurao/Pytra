#!/usr/bin/env python3
"""EAST parser core (self-hosted)."""

from __future__ import annotations

from pytra.std import argparse
from pytra.std import json
from pytra.std import re
from pytra.std.dataclasses import dataclass
from pytra.std.typing import Any
from pytra.std.pathlib import Path
from pytra.std import sys


# `BorrowKind` は実体のない型エイリアス用途のみなので、
# selfhost 生成コードでは値として生成しない。
INT_TYPES = {
    "int8",
    "uint8",
    "int16",
    "uint16",
    "int32",
    "uint32",
    "int64",
    "uint64",
}
FLOAT_TYPES = {"float32", "float64"}

# `_sh_parse_expr_lowered` が参照する self-hosted 解析コンテキスト。
_SH_FN_RETURNS: dict[str, str] = {}
_SH_CLASS_METHOD_RETURNS: dict[str, dict[str, str]] = {}
_SH_CLASS_BASE: dict[str, str | None] = {}


def _sh_set_parse_context(
    fn_returns: dict[str, str],
    class_method_returns: dict[str, dict[str, str]],
    class_base: dict[str, str | None],
) -> None:
    """式解析で使う関数戻り値/クラス情報のコンテキストを更新する。"""
    _SH_FN_RETURNS.clear()
    _SH_FN_RETURNS.update(fn_returns)
    _SH_CLASS_METHOD_RETURNS.clear()
    _SH_CLASS_METHOD_RETURNS.update(class_method_returns)
    _SH_CLASS_BASE.clear()
    _SH_CLASS_BASE.update(class_base)


@dataclass
class EastBuildError(Exception):
    kind: str
    message: str
    source_span: dict[str, int | None]
    hint: str

    def to_payload(self) -> dict[str, Any]:
        """例外情報を EAST エラー応答用 dict に整形する。"""
        out: dict[str, Any] = {}
        out["kind"] = self.kind
        out["message"] = self.message
        out["source_span"] = self.source_span
        out["hint"] = self.hint
        return out


def convert_source_to_east(source: str, filename: str) -> dict[str, Any]:
    """後方互換用の入口。self-hosted パーサで EAST を生成する。"""
    return convert_source_to_east_self_hosted(source, filename)

def _sh_span(line: int, col: int, end_col: int) -> dict[str, int]:
    """self-hosted parser 用の source_span を生成する。"""
    return {"lineno": line, "col": col, "end_lineno": line, "end_col": end_col}


def _sh_ann_to_type(ann: str) -> str:
    """型注釈文字列を EAST 正規型へ変換する。"""
    mapping = {
        "int": "int64",
        "float": "float64",
        "byte": "uint8",
        "bool": "bool",
        "str": "str",
        "None": "None",
        "bytes": "bytes",
        "bytearray": "bytearray",
    }
    txt: str = ann.strip()
    if len(txt) >= 2 and ((txt[0] == "'" and txt[-1] == "'") or (txt[0] == '"' and txt[-1] == '"')):
        txt = txt[1:-1].strip()
    if txt in mapping:
        return mapping[txt]
    m: re.Match | None = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\[(.*)\]$", txt)
    if m is None:
        return txt
    head: str = re.group(m, 1)
    inner: str = re.strip_group(m, 2)
    parts: list[str] = []
    depth = 0
    start = 0
    for i, ch in enumerate(inner):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(inner[start:i].strip())
            start = i + 1
    tail = inner[start:].strip()
    if tail != "":
        parts.append(tail)
    norm = [_sh_ann_to_type(p) for p in parts]
    return f"{head}[{', '.join(norm)}]"


def _sh_split_args_with_offsets(arg_text: str) -> list[tuple[str, int]]:
    """引数文字列をトップレベルのカンマで分割し、相対オフセットも返す。"""
    out: list[tuple[str, int]] = []
    depth = 0
    in_str: str | None = None
    esc = False
    start = 0
    i = 0
    while i < len(arg_text):
        ch = arg_text[i]
        if in_str is not None:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in {"'", '"'}:
            in_str = ch
            i += 1
            continue
        if ch in {"(", "[", "{"}:
            depth += 1
        elif ch in {")", "]", "}"}:
            depth -= 1
        elif ch == "," and depth == 0:
            part = arg_text[start:i]
            out.append((part.strip(), start + (len(part) - len(part.lstrip()))))
            start = i + 1
        i += 1
    tail = arg_text[start:]
    if tail.strip() != "":
        out.append((tail.strip(), start + (len(tail) - len(tail.lstrip()))))
    return out


def _sh_scan_string_token(text: str, start: int, quote_pos: int, line_no: int, col_base: int) -> int:
    """文字列リテラルの終端位置を走査して返す。"""
    if quote_pos + 2 < len(text) and text[quote_pos : quote_pos + 3] in {"'''", '"""'}:
        q3 = text[quote_pos : quote_pos + 3]
        j = quote_pos + 3
        while j + 2 < len(text):
            if text[j : j + 3] == q3:
                return j + 3
            j += 1
        raise EastBuildError(
            kind="unsupported_syntax",
            message="unterminated triple-quoted string literal in self_hosted parser",
            source_span=_sh_span(line_no, col_base + start, col_base + len(text)),
            hint="Close triple-quoted string with matching quote.",
        )
    q = text[quote_pos]
    j = quote_pos + 1
    while j < len(text):
        if text[j] == "\\":
            j += 2
            continue
        if text[j] == q:
            return j + 1
        j += 1
    raise EastBuildError(
        kind="unsupported_syntax",
        message="unterminated string literal in self_hosted parser",
        source_span=_sh_span(line_no, col_base + start, col_base + len(text)),
        hint="Close string literal with matching quote.",
    )


def _sh_decode_py_string_body(text: str, raw_mode: bool) -> str:
    """Python 文字列リテラル本体（引用符除去後）を簡易復号する。"""
    if raw_mode:
        return text
    out = ""
    i = 0
    while i < len(text):
        ch = text[i : i + 1]
        if ch != "\\":
            out += ch
            i += 1
            continue
        i += 1
        if i >= len(text):
            out += "\\"
            break
        esc = text[i : i + 1]
        i += 1
        if esc == "n":
            out += "\n"
        elif esc == "r":
            out += "\r"
        elif esc == "t":
            out += "\t"
        elif esc == "b":
            out += "\b"
        elif esc == "f":
            out += "\f"
        elif esc == "v":
            out += "\v"
        elif esc == "a":
            out += "\a"
        elif esc in {'"', "'", "\\"}:
            out += esc
        elif esc == "x" and i + 1 < len(text):
            hex2 = text[i : i + 2]
            try:
                out += chr(int(hex2, 16))
                i += 2
            except ValueError:
                out += "x"
        elif esc == "u" and i + 3 < len(text):
            hex4 = text[i : i + 4]
            try:
                out += chr(int(hex4, 16))
                i += 4
            except ValueError:
                out += "u"
        else:
            out += esc
    return out


def _sh_append_fstring_literal(values: list[dict[str, Any]], segment: str, span: dict[str, int], *, raw_mode: bool = False) -> None:
    """f-string の生文字列片を Constant(str) ノードとして values に追加する。"""
    lit = segment.replace("{{", "{").replace("}}", "}")
    lit = _sh_decode_py_string_body(lit, raw_mode)
    if lit == "":
        return
    node: dict[str, Any] = {}
    node["kind"] = "Constant"
    node["source_span"] = span
    node["resolved_type"] = "str"
    node["borrow_kind"] = "value"
    node["casts"] = []
    node["repr"] = json.dumps(lit)
    node["value"] = lit
    values.append(node)


def _sh_parse_def_sig(
    ln_no: int,
    ln: str,
    *,
    in_class: str = "",
) -> dict[str, Any] | None:
    """`def ...` 行から関数名・引数型・戻り型を抽出する。"""
    ln_norm: str = re.sub(r"\s+", " ", ln.strip())
    m_def: re.Match | None = re.match(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\((.*)\)\s*(?:->\s*(.+)\s*)?:\s*$", ln_norm)
    if m_def is None:
        return None
    arg_types: dict[str, str] = {}
    arg_order: list[str] = []
    arg_defaults: dict[str, str] = {}
    args_raw: str = re.group(m_def, 2)
    if args_raw.strip() != "":
        # Supported:
        # - name: Type
        # - name: Type = default
        # - "*" keyword-only marker
        # Not supported:
        # - "/" positional-only marker
        for p_txt, _off in _sh_split_args_with_offsets(args_raw):
            p: str = p_txt.strip()
            if p == "":
                continue
            if p == "*":
                continue
            if p == "/":
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message="self_hosted parser cannot parse positional-only marker '/' in parameter list",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Remove '/' from signature for now.",
                )
            if p.startswith("**"):
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse variadic kwargs parameter: {p_txt}",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Use explicit parameters instead of **kwargs.",
                )
            if p.startswith("*"):
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse variadic args parameter: {p_txt}",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Use explicit parameters instead of *args.",
                )
            if in_class != "" and p == "self":
                arg_types["self"] = in_class
                arg_order.append("self")
                continue
            m_param: re.Match | None = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^=]+?)(?:\s*=\s*(.+))?$", p)
            if m_param is None:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse parameter: {p_txt}",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Use `name: Type` style parameters.",
                )
            pn: str = re.strip_group(m_param, 1)
            pt: str = re.strip_group(m_param, 2)
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", pn):
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse parameter name: {pn}",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Use valid identifier for parameter name.",
                )
            if pt == "":
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse parameter type: {p_txt}",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Use `name: Type` style parameters.",
                )
            arg_types[pn] = _sh_ann_to_type(pt)
            arg_order.append(pn)
            pdef: str = re.group(m_param, 3)
            if pdef != "":
                default_txt = pdef.strip()
                if default_txt != "":
                    arg_defaults[pn] = default_txt
    ret_group: str = re.group(m_def, 3)
    out_sig: dict[str, Any] = {}
    out_sig["name"] = re.group(m_def, 1)
    out_sig["ret"] = _sh_ann_to_type(ret_group.strip()) if ret_group != "" else "None"
    out_sig["arg_types"] = arg_types
    out_sig["arg_order"] = arg_order
    out_sig["arg_defaults"] = arg_defaults
    return out_sig


def _sh_scan_logical_line_state(
    txt: str,
    depth: int,
    mode: str,
) -> tuple[int, str]:
    """論理行マージ用に括弧深度と文字列モードを更新する。"""
    i = 0
    mode_cur = mode
    while i < len(txt):
        if mode_cur in {"'''", '"""'}:
            close = txt.find(mode_cur, i)
            if close < 0:
                i = len(txt)
                continue
            i = close + 3
            mode_cur = ""
            continue
        ch = txt[i]
        if mode_cur in {"'", '"'}:
            if ch == "\\":
                i += 2
                continue
            if ch == mode_cur:
                mode_cur = ""
            i += 1
            continue
        if i + 2 < len(txt) and txt[i : i + 3] in {"'''", '"""'}:
            mode_cur = txt[i : i + 3]
            i += 3
            continue
        if ch in {"'", '"'}:
            mode_cur = ch
            i += 1
            continue
        if ch == "#":
            break
        if ch in {"(", "[", "{"}:
            depth += 1
        elif ch in {")", "]", "}"}:
            depth -= 1
        i += 1
    return depth, mode_cur


def _sh_merge_logical_lines(raw_lines: list[tuple[int, str]]) -> tuple[list[tuple[int, str]], dict[int, tuple[int, int]]]:
    """物理行を論理行へマージし、開始行ごとの終了行情報も返す。"""
    merged: list[tuple[int, str]] = []
    merged_line_end: dict[int, tuple[int, int]] = {}
    idx = 0
    while idx < len(raw_lines):
        start_no, start_txt = raw_lines[idx]
        acc = start_txt
        depth = 0
        mode = ""
        depth, mode = _sh_scan_logical_line_state(start_txt, depth, mode)
        end_no = start_no
        end_txt = start_txt
        while (depth > 0 or mode in {"'''", '"""'}) and idx + 1 < len(raw_lines):
            idx += 1
            next_no, next_txt = raw_lines[idx]
            if mode in {"'''", '"""'}:
                acc += "\n" + next_txt
            else:
                acc += " " + next_txt.strip()
            depth, mode = _sh_scan_logical_line_state(next_txt, depth, mode)
            end_no = next_no
            end_txt = next_txt
        merged.append((start_no, acc))
        merged_line_end[start_no] = (end_no, len(end_txt))
        idx += 1
    return merged, merged_line_end


def _sh_split_top_commas(txt: str) -> list[str]:
    """文字列/括弧深度を考慮してトップレベルのカンマ分割を行う。"""
    out: list[str] = []
    depth = 0
    in_str: str | None = None
    esc = False
    start = 0
    for i, ch in enumerate(txt):
        if in_str is not None:
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
                continue
            if ch == in_str:
                in_str = None
            continue
        if ch in {"'", '"'}:
            in_str = ch
            continue
        if ch in {"(", "[", "{"}:
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
        if ch == "," and depth == 0:
            out.append(txt[start:i].strip())
            start = i + 1
    tail = txt[start:].strip()
    if tail != "":
        out.append(tail)
    return out


def _sh_split_top_keyword(text: str, kw: str) -> int:
    """トップレベルでキーワード出現位置を探す（未検出なら -1）。"""
    depth = 0
    in_str: str | None = None
    esc = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_str is not None:
            if esc:
                esc = False
                i += 1
                continue
            if ch == "\\":
                esc = True
                i += 1
                continue
            if ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in {"'", '"'}:
            in_str = ch
            i += 1
            continue
        if ch in {"(", "[", "{"}:
            depth += 1
            i += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            i += 1
            continue
        if depth == 0 and text.startswith(kw, i):
            prev_ok = i == 0 or text[i - 1].isspace()
            next_ok = (i + len(kw) >= len(text)) or text[i + len(kw)].isspace()
            if prev_ok and next_ok:
                return i
        i += 1
    return -1


def _sh_split_top_plus(text: str) -> list[str]:
    """トップレベルの `+` で式を分割する。"""
    out: list[str] = []
    depth = 0
    in_str: str | None = None
    esc = False
    start = 0
    for i, ch in enumerate(text):
        if in_str is not None:
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
                continue
            if ch == in_str:
                in_str = None
            continue
        if ch in {"'", '"'}:
            in_str = ch
            continue
        if ch in {"(", "[", "{"}:
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
        if ch == "+" and depth == 0:
            out.append(text[start:i].strip())
            start = i + 1
    tail = text[start:].strip()
    if tail != "":
        out.append(tail)
    return out


def _sh_infer_item_type(node: dict[str, Any]) -> str:
    """dict/list/set/range 由来の反復要素型を簡易推論する。"""
    t = str(node.get("resolved_type", "unknown"))
    if t == "range":
        return "int64"
    if t.startswith("list[") and t.endswith("]"):
        inner = t[5:-1].strip()
        if inner != "":
            return inner
        return "unknown"
    if t.startswith("set[") and t.endswith("]"):
        inner = t[4:-1].strip()
        if inner != "":
            return inner
        return "unknown"
    if t in {"bytes", "bytearray"}:
        return "uint8"
    if t == "str":
        return "str"
    return "unknown"


def _sh_bind_comp_target_types(
    base_types: dict[str, str],
    target_node: dict[str, Any],
    iter_node: dict[str, Any],
) -> dict[str, str]:
    """内包表記 target へ反復要素型を束縛した name_types を返す。"""
    out: dict[str, str] = dict(base_types)
    item_t = _sh_infer_item_type(iter_node)
    if target_node.get("kind") == "Name":
        nm = str(target_node.get("id", ""))
        if nm != "":
            out[nm] = item_t
        return out
    if target_node.get("kind") != "Tuple":
        return out
    elem_nodes = target_node.get("elements", [])
    elem_types: list[str] = []
    if item_t.startswith("tuple[") and item_t.endswith("]"):
        inner = item_t[6:-1].strip()
        if inner != "":
            elem_types = _sh_split_top_commas(inner)
    i = 0
    while i < len(elem_nodes):
        e = elem_nodes[i]
        if isinstance(e, dict) and e.get("kind") == "Name":
            nm = str(e.get("id", ""))
            if nm != "":
                if i < len(elem_types):
                    et = elem_types[i].strip()
                    if et == "":
                        et = "unknown"
                    out[nm] = et
                else:
                    out[nm] = "unknown"
        i += 1
    return out


def _sh_block_end_span(
    body_lines: list[tuple[int, str]],
    start_ln: int,
    start_col: int,
    fallback_end_col: int,
    end_idx_exclusive: int,
) -> dict[str, int]:
    """複数行文の終端まで含む source_span を生成する。"""
    if end_idx_exclusive > 0 and end_idx_exclusive - 1 < len(body_lines):
        end_ln, end_txt = body_lines[end_idx_exclusive - 1]
        return {"lineno": start_ln, "col": start_col, "end_lineno": end_ln, "end_col": len(end_txt)}
    return _sh_span(start_ln, start_col, fallback_end_col)


def _sh_stmt_span(
    merged_line_end: dict[int, tuple[int, int]],
    start_ln: int,
    start_col: int,
    fallback_end_col: int,
) -> dict[str, int]:
    """単文の source_span を論理行終端まで含めて生成する。"""
    end_ln, end_col = merged_line_end.get(start_ln, (start_ln, fallback_end_col))
    return {"lineno": start_ln, "col": start_col, "end_lineno": end_ln, "end_col": end_col}


def _sh_push_stmt_with_trivia(
    stmts: list[dict[str, Any]],
    pending_leading_trivia: list[dict[str, Any]],
    pending_blank_count: int,
    stmt: dict[str, Any],
) -> int:
    """保留中 trivia を付与して文リストへ追加し、更新後 blank 数を返す。"""
    if pending_blank_count > 0:
        blank_item: dict[str, Any] = {}
        blank_item["kind"] = "blank"
        blank_item["count"] = pending_blank_count
        pending_leading_trivia.append(blank_item)
        pending_blank_count = 0
    if len(pending_leading_trivia) > 0:
        stmt["leading_trivia"] = list(pending_leading_trivia)
        comments = [x.get("text") for x in pending_leading_trivia if x.get("kind") == "comment" and isinstance(x.get("text"), str)]
        if len(comments) > 0:
            stmt["leading_comments"] = comments
        pending_leading_trivia.clear()
    stmts.append(stmt)
    return pending_blank_count


def _sh_collect_indented_block(
    body_lines: list[tuple[int, str]],
    start: int,
    parent_indent: int,
) -> tuple[list[tuple[int, str]], int]:
    """指定インデント配下のブロック行を収集する。"""
    out: list[tuple[int, str]] = []
    j = start
    while j < len(body_lines):
        n_no, n_ln = body_lines[j]
        if n_ln.strip() == "":
            t = j + 1
            while t < len(body_lines) and body_lines[t][1].strip() == "":
                t += 1
            if t >= len(body_lines):
                break
            t_ln = body_lines[t][1]
            t_indent = len(t_ln) - len(t_ln.lstrip(" "))
            if t_indent <= parent_indent:
                break
            out.append((n_no, n_ln))
            j += 1
            continue
        n_indent = len(n_ln) - len(n_ln.lstrip(" "))
        if n_indent <= parent_indent:
            break
        out.append((n_no, n_ln))
        j += 1
    return out, j


def _sh_split_top_level_assign(text: str) -> tuple[str, str] | None:
    """トップレベルの `=` を 1 つだけ持つ代入式を分割する。"""
    depth = 0
    in_str: str | None = None
    esc = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_str is not None:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                if i + 2 < len(text) and text[i : i + 3] == in_str * 3:
                    i += 2
                else:
                    in_str = None
            i += 1
            continue
        if i + 2 < len(text) and text[i : i + 3] in {"'''", '"""'}:
            in_str = text[i]
            i += 3
            continue
        if ch in {"'", '"'}:
            in_str = ch
            i += 1
            continue
        if ch == "#":
            break
        if ch in {"(", "[", "{"}:
            depth += 1
            i += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            i += 1
            continue
        if ch == "=" and depth == 0:
            prev = text[i - 1] if i - 1 >= 0 else ""
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if prev in {"!", "<", ">", "="} or nxt == "=":
                i += 1
                continue
            lhs = text[:i].strip()
            rhs = text[i + 1 :].strip()
            if lhs != "" and rhs != "":
                return lhs, rhs
            return None
        i += 1
    return None


def _sh_strip_inline_comment(text: str) -> str:
    """文字列リテラル外の末尾コメントを除去する。"""
    in_str: str | None = None
    esc = False
    for i, ch in enumerate(text):
        if in_str is not None:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in {"'", '"'}:
            in_str = ch
            continue
        if ch == "#":
            return text[:i].rstrip()
    return text


def _sh_split_top_level_from(text: str) -> tuple[str, str] | None:
    """トップレベルの `for ... in ...` を target/iter に分解する。"""
    depth = 0
    in_str: str | None = None
    esc = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_str is not None:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in {"'", '"'}:
            in_str = ch
            i += 1
            continue
        if ch in {"(", "[", "{"}:
            depth += 1
            i += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            i += 1
            continue
        if depth == 0 and text.startswith(" from ", i):
            lhs = text[:i].strip()
            rhs = text[i + 6 :].strip()
            if lhs != "" and rhs != "":
                return lhs, rhs
            return None
        i += 1
    return None


def _sh_parse_if_tail(
    *,
    start_idx: int,
    parent_indent: int,
    body_lines: list[tuple[int, str]],
    name_types: dict[str, str],
    scope_label: str,
) -> tuple[list[dict[str, Any]], int]:
    """if/elif/else 連鎖の後続ブロックを再帰的に解析する。"""
    if start_idx >= len(body_lines):
        return [], start_idx
    t_no, t_ln = body_lines[start_idx]
    t_indent = len(t_ln) - len(t_ln.lstrip(" "))
    t_s = t_ln.strip()
    if t_indent != parent_indent:
        return [], start_idx
    if t_s == "else:":
        else_block, k2 = _sh_collect_indented_block(body_lines, start_idx + 1, parent_indent)
        if len(else_block) == 0:
            raise EastBuildError(
                kind="unsupported_syntax",
                message=f"else body is missing in '{scope_label}'",
                source_span=_sh_span(t_no, 0, len(t_ln)),
                hint="Add indented else-body.",
            )
        return _sh_parse_stmt_block(else_block, name_types=dict(name_types), scope_label=scope_label), k2
    if t_s.startswith("elif ") and t_s.endswith(":"):
        cond_txt2 = t_s[len("elif ") : -1].strip()
        cond_col2 = t_ln.find(cond_txt2)
        cond_expr2 = _sh_parse_expr_lowered(cond_txt2, ln_no=t_no, col=cond_col2, name_types=dict(name_types))
        elif_block, k2 = _sh_collect_indented_block(body_lines, start_idx + 1, parent_indent)
        if len(elif_block) == 0:
            raise EastBuildError(
                kind="unsupported_syntax",
                message=f"elif body is missing in '{scope_label}'",
                source_span=_sh_span(t_no, 0, len(t_ln)),
                hint="Add indented elif-body.",
            )
        nested_orelse, k3 = _sh_parse_if_tail(
            start_idx=k2,
            parent_indent=parent_indent,
            body_lines=body_lines,
            name_types=dict(name_types),
            scope_label=scope_label,
        )
        return [
            {
                "kind": "If",
                "source_span": _sh_block_end_span(body_lines, t_no, t_ln.find("elif "), len(t_ln), k3),
                "test": cond_expr2,
                "body": _sh_parse_stmt_block(elif_block, name_types=dict(name_types), scope_label=scope_label),
                "orelse": nested_orelse,
            }
        ], k3
    return [], start_idx


def _sh_extract_leading_docstring(stmts: list[dict[str, Any]]) -> tuple[str | None, list[dict[str, Any]]]:
    """先頭文が docstring の場合に抽出し、残り文リストを返す。"""
    if len(stmts) == 0:
        return None, stmts
    first = stmts[0]
    if not isinstance(first, dict) or first.get("kind") != "Expr":
        return None, stmts
    val = first.get("value")
    if not isinstance(val, dict) or val.get("kind") != "Constant":
        return None, stmts
    s = val.get("value")
    if not isinstance(s, str):
        return None, stmts
    return s, stmts[1:]


def _sh_append_import_binding(
    *,
    import_bindings: list[dict[str, Any]],
    import_binding_names: set[str],
    module_id: str,
    export_name: str,
    local_name: str,
    binding_kind: str,
    source_file: str,
    source_line: int,
) -> None:
    """import 情報の正本 `ImportBinding` を追加する。"""
    if local_name in import_binding_names:
        raise EastBuildError(
            kind="unsupported_syntax",
            message=f"duplicate import binding: {local_name}",
            source_span=_sh_span(source_line, 0, 0),
            hint="Rename alias to avoid duplicate imported names.",
        )
    import_binding_names.add(local_name)
    import_bindings.append(
        {
            "module_id": module_id,
            "export_name": export_name,
            "local_name": local_name,
            "binding_kind": binding_kind,
            "source_file": source_file,
            "source_line": source_line,
        }
    )


class _ShExprParser:
    def __init__(
        self,
        text: str,
        *,
        line_no: int,
        col_base: int,
        name_types: dict[str, str],
        fn_return_types: dict[str, str],
        class_method_return_types: dict[str, dict[str, str]] | None = None,
        class_base: dict[str, str | None] | None = None,
    ) -> None:
        """式パースに必要な入力と型環境を初期化する。"""
        self.src = text
        self.line_no = line_no
        self.col_base = col_base
        self.name_types = name_types
        self.fn_return_types = fn_return_types
        self.class_method_return_types = class_method_return_types or {}
        self.class_base = class_base or {}
        self.tokens: list[dict[str, Any]] = self._tokenize(text)
        self.pos = 0

    def _tokenize(self, text: str) -> list[dict[str, Any]]:
        """式テキストを self-hosted 用トークン列へ変換する。"""
        out: list[dict[str, Any]] = []
        i = 0
        while i < len(text):
            ch = text[i]
            if ch.isspace():
                i += 1
                continue
            # string literal prefixes: r"...", f"...", b"...", u"...", rf"...", fr"...", ...
            pref_len = 0
            if i + 1 < len(text):
                p1 = text[i]
                if p1 in "rRbBuUfF" and text[i + 1] in {"'", '"'}:
                    pref_len = 1
                elif i + 2 < len(text):
                    p2 = text[i : i + 2]
                    if all(c in "rRbBuUfF" for c in p2) and text[i + 2] in {"'", '"'}:
                        pref_len = 2
            if pref_len > 0:
                end = _sh_scan_string_token(text, i, i + pref_len, self.line_no, self.col_base)
                out.append({"k": "STR", "v": text[i:end], "s": i, "e": end})
                i = end
                continue
            if ch.isdigit():
                if ch == "0" and i + 2 < len(text) and text[i + 1] in {"x", "X"}:
                    j = i + 2
                    while j < len(text) and (text[j].isdigit() or text[j].lower() in {"a", "b", "c", "d", "e", "f"}):
                        j += 1
                    if j > i + 2:
                        out.append({"k": "INT", "v": text[i:j], "s": i, "e": j})
                        i = j
                        continue
                j = i + 1
                while j < len(text) and text[j].isdigit():
                    j += 1
                has_float = False
                if j < len(text) and text[j] == ".":
                    k = j + 1
                    while k < len(text) and text[k].isdigit():
                        k += 1
                    if k > j + 1:
                        j = k
                        has_float = True
                if j < len(text) and text[j] in {"e", "E"}:
                    k = j + 1
                    if k < len(text) and text[k] in {"+", "-"}:
                        k += 1
                    d0 = k
                    while k < len(text) and text[k].isdigit():
                        k += 1
                    if k > d0:
                        j = k
                        has_float = True
                if has_float:
                    out.append({"k": "FLOAT", "v": text[i:j], "s": i, "e": j})
                    i = j
                    continue
                out.append({"k": "INT", "v": text[i:j], "s": i, "e": j})
                i = j
                continue
            if ch.isalpha() or ch == "_":
                j = i + 1
                while j < len(text) and (text[j].isalnum() or text[j] == "_"):
                    j += 1
                out.append({"k": "NAME", "v": text[i:j], "s": i, "e": j})
                i = j
                continue
            if i + 2 < len(text) and text[i : i + 3] in {"'''", '"""'}:
                end = _sh_scan_string_token(text, i, i, self.line_no, self.col_base)
                out.append({"k": "STR", "v": text[i:end], "s": i, "e": end})
                i = end
                continue
            if ch in {"'", '"'}:
                end = _sh_scan_string_token(text, i, i, self.line_no, self.col_base)
                out.append({"k": "STR", "v": text[i:end], "s": i, "e": end})
                i = end
                continue
            if i + 1 < len(text) and text[i : i + 2] in {"<=", ">=", "==", "!=", "//", "<<", ">>"}:
                out.append({"k": text[i : i + 2], "v": text[i : i + 2], "s": i, "e": i + 2})
                i += 2
                continue
            if ch in {"<", ">"}:
                out.append({"k": ch, "v": ch, "s": i, "e": i + 1})
                i += 1
                continue
            if ch in {"+", "-", "*", "/", "%", "&", "|", "^", "(", ")", ",", ".", "[", "]", ":", "=", "{", "}"}:
                out.append({"k": ch, "v": ch, "s": i, "e": i + 1})
                i += 1
                continue
            raise EastBuildError(
                kind="unsupported_syntax",
                message=f"unsupported token '{ch}' in self_hosted parser",
                source_span=_sh_span(self.line_no, self.col_base + i, self.col_base + i + 1),
                hint="Extend tokenizer for this syntax.",
            )
        out.append({"k": "EOF", "v": "", "s": len(text), "e": len(text)})
        return out

    def _cur(self) -> dict[str, Any]:
        """現在トークンを返す。"""
        return self.tokens[self.pos]

    def _eat(self, kind: str | None = None) -> dict[str, Any]:
        """現在トークンを消費して返す。kind 指定時は一致を検証する。"""
        tok = self._cur()
        if kind is not None and tok["k"] != kind:
            raise EastBuildError(
                kind="unsupported_syntax",
                message=f"expected token {kind}, got {tok['k']}",
                source_span=_sh_span(self.line_no, self.col_base + tok["s"], self.col_base + tok["e"]),
                hint="Fix expression syntax for self_hosted parser.",
            )
        self.pos += 1
        return tok

    def _node_span(self, s: int, e: int) -> dict[str, int]:
        """式内相対位置をファイル基準の source_span へ変換する。"""
        return _sh_span(self.line_no, self.col_base + s, self.col_base + e)

    def _src_slice(self, s: int, e: int) -> str:
        """元ソースから該当区間の repr 用文字列を取り出す。"""
        return self.src[s:e].strip()

    def parse(self) -> dict[str, Any]:
        """式を最後まで解析し、EAST 式ノードを返す。"""
        node = self._parse_ifexp()
        self._eat("EOF")
        return node

    def _parse_lambda(self) -> dict[str, Any]:
        """lambda 式を解析する。lambda でなければ次順位へ委譲する。"""
        tok = self._cur()
        if not (tok["k"] == "NAME" and tok["v"] == "lambda"):
            return self._parse_or()
        lam_tok = self._eat("NAME")
        arg_names: list[str] = []
        while self._cur()["k"] != ":":
            if self._cur()["k"] == ",":
                self._eat(",")
                continue
            if self._cur()["k"] == "NAME":
                arg_names.append(str(self._eat("NAME")["v"]))
                continue
            cur = self._cur()
            raise EastBuildError(
                kind="unsupported_syntax",
                message=f"unsupported lambda parameter token: {cur['k']}",
                source_span=self._node_span(cur["s"], cur["e"]),
                hint="Use `lambda x, y: expr` form without annotations/defaults.",
            )
        self._eat(":")
        bak: dict[str, str] = {}
        for nm in arg_names:
            bak[nm] = self.name_types.get(nm, "")
            self.name_types[nm] = "unknown"
        body = self._parse_ifexp()
        for nm in arg_names:
            old = bak.get(nm, "")
            if old == "":
                self.name_types.pop(nm, None)
            else:
                self.name_types[nm] = old
        s = lam_tok["s"]
        e = int(body["source_span"]["end_col"]) - self.col_base
        body_t = str(body.get("resolved_type", "unknown"))
        ret_t = body_t if body_t != "" else "unknown"
        params = ",".join(["unknown" for _ in arg_names])
        callable_t = f"callable[{params}->{ret_t}]"
        return {
            "kind": "Lambda",
            "source_span": self._node_span(s, e),
            "resolved_type": callable_t,
            "borrow_kind": "value",
            "casts": [],
            "repr": self._src_slice(s, e),
            "args": [
                {
                    "kind": "arg",
                    "arg": nm,
                    "annotation": None,
                    "resolved_type": "unknown",
                }
                for nm in arg_names
            ],
            "body": body,
            "return_type": ret_t,
        }

    def _callable_return_type(self, t: str) -> str:
        """`callable[...]` 型文字列から戻り型だけを抽出する。"""
        if not (t.startswith("callable[") and t.endswith("]")):
            return "unknown"
        core = t[len("callable[") : -1]
        p = core.rfind("->")
        if p < 0:
            return "unknown"
        out = core[p + 2 :].strip()
        return out if out != "" else "unknown"

    def _parse_ifexp(self) -> dict[str, Any]:
        """条件式 `a if cond else b` を解析する。"""
        body = self._parse_lambda()
        if self._cur()["k"] == "NAME" and self._cur()["v"] == "if":
            self._eat("NAME")
            test = self._parse_lambda()
            else_tok = self._eat("NAME")
            if else_tok["v"] != "else":
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message="expected 'else' in conditional expression",
                    source_span=self._node_span(else_tok["s"], else_tok["e"]),
                    hint="Use `a if cond else b` syntax.",
                )
            orelse = self._parse_ifexp()
            s = int(body["source_span"]["col"]) - self.col_base
            e = int(orelse["source_span"]["end_col"]) - self.col_base
            rt = str(body.get("resolved_type", "unknown"))
            if rt != str(orelse.get("resolved_type", "unknown")):
                rt = "unknown"
            return {
                "kind": "IfExp",
                "source_span": self._node_span(s, e),
                "resolved_type": rt,
                "borrow_kind": "value",
                "casts": [],
                "repr": self._src_slice(s, e),
                "test": test,
                "body": body,
                "orelse": orelse,
            }
        return body

    def _parse_or(self) -> dict[str, Any]:
        """論理和（or）式を解析する。"""
        node = self._parse_and()
        values = [node]
        while self._cur()["k"] == "NAME" and self._cur()["v"] == "or":
            self._eat("NAME")
            values.append(self._parse_and())
        if len(values) == 1:
            return node
        s = int(values[0]["source_span"]["col"]) - self.col_base
        e = int(values[-1]["source_span"]["end_col"]) - self.col_base
        return {
            "kind": "BoolOp",
            "source_span": self._node_span(s, e),
            "resolved_type": "bool",
            "borrow_kind": "value",
            "casts": [],
            "repr": self._src_slice(s, e),
            "op": "Or",
            "values": values,
        }

    def _parse_and(self) -> dict[str, Any]:
        """論理積（and）式を解析する。"""
        node = self._parse_not()
        values = [node]
        while self._cur()["k"] == "NAME" and self._cur()["v"] == "and":
            self._eat("NAME")
            values.append(self._parse_not())
        if len(values) == 1:
            return node
        s = int(values[0]["source_span"]["col"]) - self.col_base
        e = int(values[-1]["source_span"]["end_col"]) - self.col_base
        return {
            "kind": "BoolOp",
            "source_span": self._node_span(s, e),
            "resolved_type": "bool",
            "borrow_kind": "value",
            "casts": [],
            "repr": self._src_slice(s, e),
            "op": "And",
            "values": values,
        }

    def _parse_not(self) -> dict[str, Any]:
        """単項 not を解析する。"""
        tok = self._cur()
        if tok["k"] == "NAME" and tok["v"] == "not":
            self._eat("NAME")
            operand = self._parse_not()
            s = tok["s"]
            e = int(operand["source_span"]["end_col"]) - self.col_base
            return {
                "kind": "UnaryOp",
                "source_span": self._node_span(s, e),
                "resolved_type": "bool",
                "borrow_kind": "value",
                "casts": [],
                "repr": self._src_slice(s, e),
                "op": "Not",
                "operand": operand,
            }
        return self._parse_compare()

    def _parse_compare(self) -> dict[str, Any]:
        """比較演算（連鎖比較含む）を解析する。"""
        node = self._parse_bitor()
        cmp_map = {"<": "Lt", "<=": "LtE", ">": "Gt", ">=": "GtE", "==": "Eq", "!=": "NotEq"}
        ops: list[str] = []
        comparators: list[dict[str, Any]] = []
        while True:
            if self._cur()["k"] in cmp_map:
                tok = self._eat()
                ops.append(cmp_map[tok["k"]])
                comparators.append(self._parse_bitor())
                continue
            if self._cur()["k"] == "NAME" and self._cur()["v"] == "in":
                self._eat("NAME")
                ops.append("In")
                comparators.append(self._parse_bitor())
                continue
            if self._cur()["k"] == "NAME" and self._cur()["v"] == "is":
                self._eat("NAME")
                if self._cur()["k"] == "NAME" and self._cur()["v"] == "not":
                    self._eat("NAME")
                    ops.append("IsNot")
                    comparators.append(self._parse_bitor())
                else:
                    ops.append("Is")
                    comparators.append(self._parse_bitor())
                continue
            if self._cur()["k"] == "NAME" and self._cur()["v"] == "not":
                pos = self.pos
                self._eat("NAME")
                if self._cur()["k"] == "NAME" and self._cur()["v"] == "in":
                    self._eat("NAME")
                    ops.append("NotIn")
                    comparators.append(self._parse_bitor())
                    continue
                self.pos = pos
            break
        if len(ops) == 0:
            return node
        start_col = int(node["source_span"]["col"]) - self.col_base
        end_col = int(comparators[-1]["source_span"]["end_col"]) - self.col_base
        return {
            "kind": "Compare",
            "source_span": self._node_span(start_col, end_col),
            "resolved_type": "bool",
            "borrow_kind": "value",
            "casts": [],
            "repr": self._src_slice(start_col, end_col),
            "left": node,
            "ops": ops,
            "comparators": comparators,
        }

    def _parse_bitor(self) -> dict[str, Any]:
        """ビット OR を解析する。"""
        node = self._parse_bitxor()
        while self._cur()["k"] == "|":
            op_tok = self._eat()
            right = self._parse_bitxor()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_bitxor(self) -> dict[str, Any]:
        """ビット XOR を解析する。"""
        node = self._parse_bitand()
        while self._cur()["k"] == "^":
            op_tok = self._eat()
            right = self._parse_bitand()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_bitand(self) -> dict[str, Any]:
        """ビット AND を解析する。"""
        node = self._parse_shift()
        while self._cur()["k"] == "&":
            op_tok = self._eat()
            right = self._parse_shift()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_shift(self) -> dict[str, Any]:
        """シフト演算を解析する。"""
        node = self._parse_addsub()
        while self._cur()["k"] in {"<<", ">>"}:
            op_tok = self._eat()
            right = self._parse_addsub()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_addsub(self) -> dict[str, Any]:
        """加減算を解析する。"""
        node = self._parse_muldiv()
        while self._cur()["k"] in {"+", "-"}:
            op_tok = self._eat()
            right = self._parse_muldiv()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_muldiv(self) -> dict[str, Any]:
        """乗除算（`* / // %`）を解析する。"""
        node = self._parse_unary()
        while self._cur()["k"] in {"*", "/", "//", "%"}:
            op_tok = self._eat()
            right = self._parse_unary()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_unary(self) -> dict[str, Any]:
        """単項演算（`+` / `-`）を解析する。"""
        if self._cur()["k"] in {"+", "-"}:
            tok = self._eat()
            operand = self._parse_unary()
            s = tok["s"]
            e = int(operand["source_span"]["end_col"]) - self.col_base
            out_t = str(operand.get("resolved_type", "unknown"))
            return {
                "kind": "UnaryOp",
                "source_span": self._node_span(s, e),
                "resolved_type": out_t if out_t in {"int64", "float64"} else "unknown",
                "borrow_kind": "value",
                "casts": [],
                "repr": self._src_slice(s, e),
                "op": "USub" if tok["k"] == "-" else "UAdd",
                "operand": operand,
            }
        return self._parse_postfix()

    def _lookup_method_return(self, cls_name: str, method: str) -> str:
        """クラス継承を辿ってメソッド戻り型を解決する。"""
        cur: str | None = cls_name
        while cur is not None:
            methods = self.class_method_return_types.get(cur, {})
            if method in methods:
                return methods[method]
            cur = self.class_base.get(cur)
        return "unknown"

    def _split_generic_types(self, s: str) -> list[str]:
        """ジェネリック型引数をトップレベルカンマで分割する。"""
        out: list[str] = []
        depth = 0
        start = 0
        for i, ch in enumerate(s):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            elif ch == "," and depth == 0:
                out.append(s[start:i].strip())
                start = i + 1
        out.append(s[start:].strip())
        return out

    def _split_union_types(self, s: str) -> list[str]:
        """Union 型引数をトップレベル `|` で分割する。"""
        out: list[str] = []
        depth = 0
        start = 0
        for i, ch in enumerate(s):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            elif ch == "|" and depth == 0:
                out.append(s[start:i].strip())
                start = i + 1
        out.append(s[start:].strip())
        return out

    def _is_forbidden_object_receiver_type(self, t: str) -> bool:
        """object レシーバ禁止ルールに該当する型か判定する。"""
        s = t.strip()
        if s in {"object", "Any", "any"}:
            return True
        if "|" in s:
            parts = self._split_union_types(s)
            return any(p in {"object", "Any", "any"} for p in parts if p != "None")
        return False

    def _subscript_result_type(self, container_type: str) -> str:
        """添字アクセスの結果型をコンテナ型から推論する。"""
        if container_type.startswith("list[") and container_type.endswith("]"):
            inner = container_type[5:-1].strip()
            return inner if inner != "" else "unknown"
        if container_type.startswith("dict[") and container_type.endswith("]"):
            inner = self._split_generic_types(container_type[5:-1].strip())
            if len(inner) == 2 and inner[1] != "":
                return inner[1]
            return "unknown"
        if container_type == "str":
            return "str"
        if container_type in {"bytes", "bytearray"}:
            return "uint8"
        return "unknown"

    def _iter_item_type(self, iter_expr: dict[str, Any] | None) -> str:
        """for 反復対象の要素型を推論する。"""
        if not isinstance(iter_expr, dict):
            return "unknown"
        t = str(iter_expr.get("resolved_type", "unknown"))
        if t == "range":
            return "int64"
        if t.startswith("list[") and t.endswith("]"):
            inner = t[5:-1].strip()
            return inner if inner != "" else "unknown"
        if t.startswith("set[") and t.endswith("]"):
            inner = t[4:-1].strip()
            return inner if inner != "" else "unknown"
        if t == "bytearray" or t == "bytes":
            return "uint8"
        if t == "str":
            return "str"
        return "unknown"

    def _parse_postfix(self) -> dict[str, Any]:
        """属性参照・呼び出し・添字・スライスなど後置構文を解析する。"""
        node = self._parse_primary()
        while True:
            tok = self._cur()
            if tok["k"] == ".":
                self._eat(".")
                name_tok = self._eat("NAME")
                s = int(node["source_span"]["col"]) - self.col_base
                e = name_tok["e"]
                attr_name = str(name_tok["v"])
                owner_t = str(node.get("resolved_type", "unknown"))
                if self._is_forbidden_object_receiver_type(owner_t):
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message="object receiver attribute/method access is forbidden by language constraints",
                        source_span=self._node_span(s, e),
                        hint="Cast or assign to a concrete type before attribute/method access.",
                    )
                attr_t = "unknown"
                if isinstance(node, dict) and node.get("kind") == "Name" and node.get("id") == "self":
                    # In method scope, class fields are injected into name_types.
                    maybe_field_t = self.name_types.get(attr_name)
                    if isinstance(maybe_field_t, str) and maybe_field_t != "":
                        attr_t = maybe_field_t
                if owner_t == "Path":
                    if attr_name in {"name", "stem"}:
                        attr_t = "str"
                    elif attr_name == "parent":
                        attr_t = "Path"
                node = {
                    "kind": "Attribute",
                    "source_span": self._node_span(s, e),
                    "resolved_type": attr_t,
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": self._src_slice(s, e),
                    "value": node,
                    "attr": attr_name,
                }
                continue
            if tok["k"] == "(":
                ltok = self._eat("(")
                args: list[dict[str, Any]] = []
                keywords: list[dict[str, Any]] = []
                if self._cur()["k"] != ")":
                    while True:
                        if self._cur()["k"] == "NAME":
                            save_pos = self.pos
                            name_tok = self._eat("NAME")
                            if self._cur()["k"] == "=":
                                self._eat("=")
                                kw_val = self._parse_ifexp()
                                keywords.append({"arg": str(name_tok["v"]), "value": kw_val})
                            else:
                                self.pos = save_pos
                                args.append(self._parse_call_arg_expr())
                        else:
                            args.append(self._parse_call_arg_expr())
                        if self._cur()["k"] == ",":
                            self._eat(",")
                            if self._cur()["k"] == ")":
                                break
                            continue
                        break
                rtok = self._eat(")")
                s = int(node["source_span"]["col"]) - self.col_base
                e = rtok["e"]
                call_ret = "unknown"
                fn_name = ""
                if isinstance(node, dict) and node.get("kind") == "Name":
                    fn_name = str(node.get("id", ""))
                    if fn_name == "print":
                        call_ret = "None"
                    elif fn_name == "Path":
                        call_ret = "Path"
                    elif fn_name == "open":
                        call_ret = "PyFile"
                    elif fn_name == "int":
                        call_ret = "int64"
                    elif fn_name == "float":
                        call_ret = "float64"
                    elif fn_name == "bool":
                        call_ret = "bool"
                    elif fn_name == "str":
                        call_ret = "str"
                    elif fn_name == "len":
                        call_ret = "int64"
                    elif fn_name == "range":
                        call_ret = "range"
                    elif fn_name == "list":
                        call_ret = "list[unknown]"
                    elif fn_name == "set":
                        call_ret = "set[unknown]"
                    elif fn_name == "dict":
                        call_ret = "dict[unknown,unknown]"
                    elif fn_name == "bytes":
                        call_ret = "bytes"
                    elif fn_name == "bytearray":
                        call_ret = "bytearray"
                    elif fn_name in {"Exception", "RuntimeError"}:
                        call_ret = "Exception"
                    elif fn_name in self.fn_return_types:
                        call_ret = self.fn_return_types[fn_name]
                    elif fn_name in self.class_method_return_types:
                        call_ret = fn_name
                    else:
                        call_ret = self._callable_return_type(str(self.name_types.get(fn_name, "unknown")))
                elif isinstance(node, dict) and node.get("kind") == "Attribute":
                    owner = node.get("value")
                    attr = str(node.get("attr", ""))
                    if isinstance(owner, dict) and owner.get("kind") == "Name":
                        owner_t = self.name_types.get(str(owner.get("id", "")), "unknown")
                        if owner_t != "unknown":
                            call_ret = self._lookup_method_return(owner_t, attr)
                        if owner_t == "Path":
                            if attr in {"read_text", "name", "stem"}:
                                call_ret = "str"
                            elif attr in {"exists"}:
                                call_ret = "bool"
                            elif attr in {"mkdir", "write_text"}:
                                call_ret = "None"
                        elif owner_t == "PyFile":
                            if attr in {"close", "write"}:
                                call_ret = "None"
                elif isinstance(node, dict) and node.get("kind") == "Lambda":
                    call_ret = str(node.get("return_type", "unknown"))
                payload: dict[str, Any] = {
                    "kind": "Call",
                    "source_span": self._node_span(s, e),
                    "resolved_type": call_ret,
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": self._src_slice(s, e),
                    "func": node,
                    "args": args,
                    "keywords": keywords,
                }
                if fn_name == "print":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "print"
                    payload["runtime_call"] = "py_print"
                elif fn_name == "len":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "len"
                    payload["runtime_call"] = "py_len"
                elif fn_name == "str":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "str"
                    payload["runtime_call"] = "py_to_string"
                elif fn_name in {"int", "float", "bool"}:
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = fn_name
                    payload["runtime_call"] = "static_cast"
                elif fn_name in {"min", "max"}:
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = fn_name
                    payload["runtime_call"] = "py_min" if fn_name == "min" else "py_max"
                elif fn_name == "perf_counter":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "perf_counter"
                    payload["runtime_call"] = "perf_counter"
                elif fn_name in {"Exception", "RuntimeError"}:
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = fn_name
                    payload["runtime_call"] = "std::runtime_error"
                elif fn_name == "Path":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "Path"
                    payload["runtime_call"] = "Path"
                elif fn_name == "open":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "open"
                    payload["runtime_call"] = "open"
                elif fn_name in {"bytes", "bytearray"}:
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = fn_name
                elif isinstance(node, dict) and node.get("kind") == "Attribute":
                    attr = str(node.get("attr", ""))
                    owner = node.get("value")
                    owner_t = str(owner.get("resolved_type", "unknown")) if isinstance(owner, dict) else "unknown"
                    if owner_t == "str":
                        str_map = {
                            "strip": "py_strip",
                            "rstrip": "py_rstrip",
                            "startswith": "py_startswith",
                            "endswith": "py_endswith",
                            "replace": "py_replace",
                            "join": "py_join",
                            "isdigit": "py_isdigit",
                            "isalpha": "py_isalpha",
                        }
                        rc = str_map.get(attr)
                        if rc is not None:
                            payload["lowered_kind"] = "BuiltinCall"
                            payload["builtin_name"] = attr
                            payload["runtime_call"] = rc
                    elif owner_t == "Path":
                        path_map = {
                            "mkdir": "std::filesystem::create_directories",
                            "exists": "std::filesystem::exists",
                            "write_text": "py_write_text",
                            "read_text": "py_read_text",
                            "parent": "path_parent",
                            "name": "path_name",
                            "stem": "path_stem",
                        }
                        rc = path_map.get(attr)
                        if rc is not None:
                            payload["lowered_kind"] = "BuiltinCall"
                            payload["builtin_name"] = attr
                            payload["runtime_call"] = rc
                    elif owner_t in INT_TYPES | {"int"}:
                        int_map = {
                            "to_bytes": "py_int_to_bytes",
                        }
                        rc = int_map.get(attr)
                        if rc is not None:
                            payload["lowered_kind"] = "BuiltinCall"
                            payload["builtin_name"] = attr
                            payload["runtime_call"] = rc
                    elif owner_t.startswith("list["):
                        list_map = {
                            "append": "list.append",
                            "extend": "list.extend",
                            "pop": "list.pop",
                            "clear": "list.clear",
                            "reverse": "list.reverse",
                            "sort": "list.sort",
                        }
                        rc = list_map.get(attr)
                        if rc is not None:
                            payload["lowered_kind"] = "BuiltinCall"
                            payload["builtin_name"] = attr
                            payload["runtime_call"] = rc
                    elif owner_t.startswith("set["):
                        set_map = {
                            "add": "set.add",
                            "discard": "set.discard",
                            "remove": "set.remove",
                            "clear": "set.clear",
                        }
                        rc = set_map.get(attr)
                        if rc is not None:
                            payload["lowered_kind"] = "BuiltinCall"
                            payload["builtin_name"] = attr
                            payload["runtime_call"] = rc
                    elif owner_t.startswith("dict["):
                        dict_map = {
                            "get": "dict.get",
                            "items": "dict.items",
                            "keys": "dict.keys",
                            "values": "dict.values",
                        }
                        rc = dict_map.get(attr)
                        if rc is not None:
                            payload["lowered_kind"] = "BuiltinCall"
                            payload["builtin_name"] = attr
                            payload["runtime_call"] = rc
                    elif owner_t == "unknown":
                        unknown_map = {
                            "append": "list.append",
                            "extend": "list.extend",
                            "pop": "list.pop",
                            "get": "dict.get",
                            "items": "dict.items",
                            "keys": "dict.keys",
                            "values": "dict.values",
                            "isdigit": "py_isdigit",
                            "isalpha": "py_isalpha",
                        }
                        rc = unknown_map.get(attr)
                        if rc is not None:
                            payload["lowered_kind"] = "BuiltinCall"
                            payload["builtin_name"] = attr
                            payload["runtime_call"] = rc
                node = payload
                continue
            if tok["k"] == "[":
                ltok = self._eat("[")
                if self._cur()["k"] == ":":
                    self._eat(":")
                    up = None
                    if self._cur()["k"] != "]":
                        up = self._parse_addsub()
                    rtok = self._eat("]")
                    s = int(node["source_span"]["col"]) - self.col_base
                    e = rtok["e"]
                    node = {
                        "kind": "Subscript",
                        "source_span": self._node_span(s, e),
                        "resolved_type": node.get("resolved_type", "unknown"),
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": self._src_slice(s, e),
                        "value": node,
                        "slice": {"kind": "Slice", "lower": None, "upper": up, "step": None},
                        "lowered_kind": "SliceExpr",
                        "lower": None,
                        "upper": up,
                    }
                    continue
                first = self._parse_addsub()
                if self._cur()["k"] == ":":
                    self._eat(":")
                    up = None
                    if self._cur()["k"] != "]":
                        up = self._parse_addsub()
                    rtok = self._eat("]")
                    s = int(node["source_span"]["col"]) - self.col_base
                    e = rtok["e"]
                    node = {
                        "kind": "Subscript",
                        "source_span": self._node_span(s, e),
                        "resolved_type": node.get("resolved_type", "unknown"),
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": self._src_slice(s, e),
                        "value": node,
                        "slice": {"kind": "Slice", "lower": first, "upper": up, "step": None},
                        "lowered_kind": "SliceExpr",
                        "lower": first,
                        "upper": up,
                    }
                    continue
                rtok = self._eat("]")
                s = int(node["source_span"]["col"]) - self.col_base
                e = rtok["e"]
                out_t = self._subscript_result_type(str(node.get("resolved_type", "unknown")))
                node = {
                    "kind": "Subscript",
                    "source_span": self._node_span(s, e),
                    "resolved_type": out_t,
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": self._src_slice(s, e),
                    "value": node,
                    "slice": first,
                }
                continue
            return node

    def _parse_comp_target(self) -> dict[str, Any]:
        """内包表現のターゲット（name / tuple）を解析する。"""
        if self._cur()["k"] == "NAME":
            nm = self._eat("NAME")
            t = self.name_types.get(str(nm["v"]), "unknown")
            return {
                "kind": "Name",
                "source_span": self._node_span(nm["s"], nm["e"]),
                "resolved_type": t,
                "borrow_kind": "value",
                "casts": [],
                "repr": str(nm["v"]),
                "id": str(nm["v"]),
            }
        if self._cur()["k"] == "(":
            l = self._eat("(")
            elems: list[dict[str, Any]] = []
            elems.append(self._parse_comp_target())
            while self._cur()["k"] == ",":
                self._eat(",")
                if self._cur()["k"] == ")":
                    break
                elems.append(self._parse_comp_target())
            r = self._eat(")")
            return {
                "kind": "Tuple",
                "source_span": self._node_span(l["s"], r["e"]),
                "resolved_type": "tuple[unknown]",
                "borrow_kind": "value",
                "casts": [],
                "repr": self._src_slice(l["s"], r["e"]),
                "elements": elems,
            }
        tok = self._cur()
        raise EastBuildError(
            kind="unsupported_syntax",
            message="invalid comprehension target in call argument",
            source_span=self._node_span(tok["s"], tok["e"]),
            hint="Use name or tuple target in generator expression.",
        )

    def _parse_call_arg_expr(self) -> dict[str, Any]:
        """呼び出し引数式を解析し、必要なら generator 引数へ lower する。"""
        first = self._parse_ifexp()
        if not (self._cur()["k"] == "NAME" and self._cur()["v"] == "for"):
            return first
        self._eat("NAME")
        target = self._parse_comp_target()
        in_tok = self._eat("NAME")
        if in_tok["v"] != "in":
            raise EastBuildError(
                kind="unsupported_syntax",
                message="expected 'in' in generator expression",
                source_span=self._node_span(in_tok["s"], in_tok["e"]),
                hint="Use `for x in iterable` form.",
            )
        iter_expr = self._parse_ifexp()
        ifs: list[dict[str, Any]] = []
        while self._cur()["k"] == "NAME" and self._cur()["v"] == "if":
            self._eat("NAME")
            ifs.append(self._parse_ifexp())
        s = int(first["source_span"]["col"]) - self.col_base
        end_node = ifs[-1] if len(ifs) > 0 else iter_expr
        e = int(end_node["source_span"]["end_col"]) - self.col_base
        return {
            "kind": "ListComp",
            "source_span": self._node_span(s, e),
            "resolved_type": f"list[{first.get('resolved_type', 'unknown')}]",
            "borrow_kind": "value",
            "casts": [],
            "repr": self._src_slice(s, e),
            "elt": first,
            "generators": [{"target": target, "iter": iter_expr, "ifs": ifs, "is_async": False}],
            "lowered_kind": "GeneratorArg",
        }

    def _make_bin(self, left: dict[str, Any], op_sym: str, right: dict[str, Any]) -> dict[str, Any]:
        """二項演算ノードを構築し、数値昇格 cast も付与する。"""
        op_map = {
            "+": "Add",
            "-": "Sub",
            "*": "Mult",
            "/": "Div",
            "//": "FloorDiv",
            "%": "Mod",
            "&": "BitAnd",
            "|": "BitOr",
            "^": "BitXor",
            "<<": "LShift",
            ">>": "RShift",
        }
        lt = str(left.get("resolved_type", "unknown"))
        rt = str(right.get("resolved_type", "unknown"))
        casts: list[dict[str, Any]] = []
        if op_sym == "/":
            if lt == "Path" and rt in {"str", "Path"}:
                out_t = "Path"
            else:
                out_t = "float64"
                if lt == "int64":
                    casts.append({"on": "left", "from": "int64", "to": "float64", "reason": "numeric_promotion"})
                if rt == "int64":
                    casts.append({"on": "right", "from": "int64", "to": "float64", "reason": "numeric_promotion"})
        elif op_sym == "//":
            out_t = "int64" if lt in {"int64", "unknown"} and rt in {"int64", "unknown"} else "float64"
        elif op_sym == "+" and (
            (lt in {"bytes", "bytearray"} and rt in {"bytes", "bytearray"})
            or (lt == "str" and rt == "str")
        ):
            out_t = "bytes" if (lt in {"bytes", "bytearray"} and rt in {"bytes", "bytearray"}) else "str"
        elif lt == rt and lt in {"int64", "float64"}:
            out_t = lt
        elif lt in {"int64", "float64"} and rt in {"int64", "float64"}:
            out_t = "float64"
            if lt == "int64":
                casts.append({"on": "left", "from": "int64", "to": "float64", "reason": "numeric_promotion"})
            if rt == "int64":
                casts.append({"on": "right", "from": "int64", "to": "float64", "reason": "numeric_promotion"})
        elif op_sym in {"&", "|", "^", "<<", ">>"} and lt == "int64" and rt == "int64":
            out_t = "int64"
        else:
            out_t = "unknown"

        ls = int(left["source_span"]["col"]) - self.col_base
        rs = int(right["source_span"]["end_col"]) - self.col_base
        return {
            "kind": "BinOp",
            "source_span": self._node_span(ls, rs),
            "resolved_type": out_t,
            "borrow_kind": "value",
            "casts": casts,
            "repr": self._src_slice(ls, rs),
            "left": left,
            "op": op_map[op_sym],
            "right": right,
        }

    def _parse_primary(self) -> dict[str, Any]:
        """リテラル・名前・括弧式などの primary 式を解析する。"""
        tok = self._cur()
        if tok["k"] == "INT":
            self._eat("INT")
            return {
                "kind": "Constant",
                "source_span": self._node_span(tok["s"], tok["e"]),
                "resolved_type": "int64",
                "borrow_kind": "value",
                "casts": [],
                "repr": tok["v"],
                "value": int(str(tok["v"]), 0),
            }
        if tok["k"] == "FLOAT":
            self._eat("FLOAT")
            return {
                "kind": "Constant",
                "source_span": self._node_span(tok["s"], tok["e"]),
                "resolved_type": "float64",
                "borrow_kind": "value",
                "casts": [],
                "repr": tok["v"],
                "value": float(tok["v"]),
            }
        if tok["k"] == "STR":
            self._eat("STR")
            raw: str = tok["v"]
            # Support prefixed literals (f/r/b/u/rf/fr...) in expression parser.
            p = 0
            while p < len(raw) and raw[p] in "rRbBuUfF":
                p += 1
            prefix = raw[:p].lower()
            if p >= len(raw):
                p = 0

            is_triple = p + 2 < len(raw) and raw[p : p + 3] in {"'''", '"""'}
            if is_triple:
                body = raw[p + 3 : -3]
            else:
                body = raw[p + 1 : -1]

            if "f" in prefix:
                values: list[dict[str, Any]] = []
                is_raw = "r" in prefix

                i = 0
                while i < len(body):
                    j = body.find("{", i)
                    if j < 0:
                        _sh_append_fstring_literal(values, body[i:], self._node_span(tok["s"], tok["e"]), raw_mode=is_raw)
                        break
                    if j + 1 < len(body) and body[j + 1] == "{":
                        _sh_append_fstring_literal(values, body[i : j + 1], self._node_span(tok["s"], tok["e"]), raw_mode=is_raw)
                        i = j + 2
                        continue
                    if j > i:
                        _sh_append_fstring_literal(values, body[i:j], self._node_span(tok["s"], tok["e"]), raw_mode=is_raw)
                    k = body.find("}", j + 1)
                    if k < 0:
                        raise EastBuildError(
                            kind="unsupported_syntax",
                            message="unterminated f-string placeholder in self_hosted parser",
                            source_span=self._node_span(tok["s"], tok["e"]),
                            hint="Close f-string placeholder with `}`.",
                        )
                    inner_expr = body[j + 1 : k].strip()
                    values.append(
                        {
                            "kind": "FormattedValue",
                            "value": _sh_parse_expr(
                                inner_expr,
                                line_no=self.line_no,
                                col_base=self.col_base + tok["s"],
                                name_types=self.name_types,
                                fn_return_types=self.fn_return_types,
                                class_method_return_types=self.class_method_return_types,
                                class_base=self.class_base,
                            ),
                        }
                    )
                    i = k + 1
                return {
                    "kind": "JoinedStr",
                    "source_span": self._node_span(tok["s"], tok["e"]),
                    "resolved_type": "str",
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": raw,
                    "values": values,
                }
            resolved_type = "str"
            if "b" in prefix and "f" not in prefix:
                resolved_type = "bytes"
            body = _sh_decode_py_string_body(body, "r" in prefix)
            return {
                "kind": "Constant",
                "source_span": self._node_span(tok["s"], tok["e"]),
                "resolved_type": resolved_type,
                "borrow_kind": "value",
                "casts": [],
                "repr": raw,
                "value": body,
            }
        if tok["k"] == "NAME":
            name_tok = self._eat("NAME")
            nm = str(name_tok["v"])
            if nm in {"True", "False"}:
                return {
                    "kind": "Constant",
                    "source_span": self._node_span(name_tok["s"], name_tok["e"]),
                    "resolved_type": "bool",
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": nm,
                    "value": (nm == "True"),
                }
            if nm == "None":
                return {
                    "kind": "Constant",
                    "source_span": self._node_span(name_tok["s"], name_tok["e"]),
                    "resolved_type": "None",
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": nm,
                    "value": None,
                }
            t = self.name_types.get(nm, "unknown")
            return {
                "kind": "Name",
                "source_span": self._node_span(name_tok["s"], name_tok["e"]),
                "resolved_type": t,
                "borrow_kind": "readonly_ref" if t != "unknown" else "value",
                "casts": [],
                "repr": nm,
                "id": nm,
            }
        if tok["k"] == "(":
            l = self._eat("(")
            if self._cur()["k"] == ")":
                r = self._eat(")")
                return {
                    "kind": "Tuple",
                    "source_span": self._node_span(l["s"], r["e"]),
                    "resolved_type": "tuple[]",
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": self._src_slice(l["s"], r["e"]),
                    "elements": [],
                }
            first = self._parse_ifexp()
            if self._cur()["k"] == ",":
                elements = [first]
                while self._cur()["k"] == ",":
                    self._eat(",")
                    if self._cur()["k"] == ")":
                        break
                    elements.append(self._parse_ifexp())
                r = self._eat(")")
                elem_types = [str(e.get("resolved_type", "unknown")) for e in elements]
                return {
                    "kind": "Tuple",
                    "source_span": self._node_span(l["s"], r["e"]),
                    "resolved_type": f"tuple[{','.join(elem_types)}]",
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": self._src_slice(l["s"], r["e"]),
                    "elements": elements,
                }
            r = self._eat(")")
            first["source_span"] = self._node_span(l["s"], r["e"])
            first["repr"] = self._src_slice(l["s"], r["e"])
            return first
        if tok["k"] == "[":
            l = self._eat("[")
            elements: list[dict[str, Any]] = []
            if self._cur()["k"] != "]":
                first = self._parse_ifexp()
                # list comprehension: [elt for x in iter if cond]
                if self._cur()["k"] == "NAME" and self._cur()["v"] == "for":
                    self._eat("NAME")
                    tgt_tok = self._eat("NAME")
                    in_tok = self._eat("NAME")
                    if in_tok["v"] != "in":
                        raise EastBuildError(
                            kind="unsupported_syntax",
                            message="expected 'in' in list comprehension",
                            source_span=self._node_span(in_tok["s"], in_tok["e"]),
                            hint="Use `[x for x in iterable]` syntax.",
                        )
                    iter_expr = self._parse_ifexp()
                    if (
                        isinstance(iter_expr, dict)
                        and iter_expr.get("kind") == "Call"
                        and isinstance(iter_expr.get("func"), dict)
                        and iter_expr.get("func", {}).get("kind") == "Name"
                        and iter_expr.get("func", {}).get("id") == "range"
                    ):
                        rargs = list(iter_expr.get("args", []))
                        if len(rargs) == 1:
                            start_node = {
                                "kind": "Constant",
                                "source_span": self._node_span(tgt_tok["s"], tgt_tok["s"]),
                                "resolved_type": "int64",
                                "borrow_kind": "value",
                                "casts": [],
                                "repr": "0",
                                "value": 0,
                            }
                            stop_node = rargs[0]
                            step_node = {
                                "kind": "Constant",
                                "source_span": self._node_span(tgt_tok["s"], tgt_tok["s"]),
                                "resolved_type": "int64",
                                "borrow_kind": "value",
                                "casts": [],
                                "repr": "1",
                                "value": 1,
                            }
                        elif len(rargs) == 2:
                            start_node = rargs[0]
                            stop_node = rargs[1]
                            step_node = {
                                "kind": "Constant",
                                "source_span": self._node_span(tgt_tok["s"], tgt_tok["s"]),
                                "resolved_type": "int64",
                                "borrow_kind": "value",
                                "casts": [],
                                "repr": "1",
                                "value": 1,
                            }
                        else:
                            start_node = rargs[0]
                            stop_node = rargs[1]
                            step_node = rargs[2]
                        step_const = step_node.get("value") if isinstance(step_node, dict) else None
                        mode = "dynamic"
                        if step_const == 1:
                            mode = "ascending"
                        elif step_const == -1:
                            mode = "descending"
                        iter_expr = {
                            "kind": "RangeExpr",
                            "source_span": iter_expr.get("source_span"),
                            "resolved_type": "range",
                            "borrow_kind": "value",
                            "casts": [],
                            "repr": iter_expr.get("repr", "range(...)"),
                            "start": start_node,
                            "stop": stop_node,
                            "step": step_node,
                            "range_mode": mode,
                        }
                    ifs: list[dict[str, Any]] = []
                    while self._cur()["k"] == "NAME" and self._cur()["v"] == "if":
                        self._eat("NAME")
                        ifs.append(self._parse_ifexp())
                    r = self._eat("]")
                    tgt_name = str(tgt_tok["v"])
                    tgt_ty = self._iter_item_type(iter_expr)
                    first_norm = first
                    ifs_norm = ifs
                    if tgt_ty != "unknown":
                        old_t = self.name_types.get(tgt_name, "")
                        self.name_types[tgt_name] = tgt_ty
                        first_repr = first.get("repr")
                        first_col = int(first.get("source_span", {}).get("col", self.col_base))
                        if isinstance(first_repr, str) and first_repr != "":
                            first_norm = _sh_parse_expr(
                                first_repr,
                                line_no=self.line_no,
                                col_base=first_col,
                                name_types=self.name_types,
                                fn_return_types=self.fn_return_types,
                                class_method_return_types=self.class_method_return_types,
                                class_base=self.class_base,
                            )
                        ifs_norm = []
                        for cond in ifs:
                            cond_repr = cond.get("repr")
                            cond_col = int(cond.get("source_span", {}).get("col", self.col_base))
                            if isinstance(cond_repr, str) and cond_repr != "":
                                ifs_norm.append(
                                    _sh_parse_expr(
                                        cond_repr,
                                        line_no=self.line_no,
                                        col_base=cond_col,
                                        name_types=self.name_types,
                                        fn_return_types=self.fn_return_types,
                                        class_method_return_types=self.class_method_return_types,
                                        class_base=self.class_base,
                                    )
                                )
                            else:
                                ifs_norm.append(cond)
                        if old_t == "":
                            self.name_types.pop(tgt_name, None)
                        else:
                            self.name_types[tgt_name] = old_t
                    return {
                        "kind": "ListComp",
                        "source_span": self._node_span(l["s"], r["e"]),
                        "resolved_type": f"list[{str(first_norm.get('resolved_type', 'unknown'))}]",
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": self._src_slice(l["s"], r["e"]),
                        "elt": first_norm,
                        "generators": [
                            {
                                "target": {
                                    "kind": "Name",
                                    "source_span": self._node_span(tgt_tok["s"], tgt_tok["e"]),
                                    "resolved_type": tgt_ty,
                                    "borrow_kind": "value",
                                    "casts": [],
                                    "repr": tgt_name,
                                    "id": tgt_name,
                                },
                                "iter": iter_expr,
                                "ifs": ifs_norm,
                            }
                        ],
                    }

                elements.append(first)
                while True:
                    if self._cur()["k"] == ",":
                        self._eat(",")
                        if self._cur()["k"] == "]":
                            break
                        elements.append(self._parse_ifexp())
                        continue
                    break
            r = self._eat("]")
            et = "unknown"
            if len(elements) > 0:
                et = str(elements[0].get("resolved_type", "unknown"))
                for e in elements[1:]:
                    if str(e.get("resolved_type", "unknown")) != et:
                        et = "unknown"
                        break
            return {
                "kind": "List",
                "source_span": self._node_span(l["s"], r["e"]),
                "resolved_type": f"list[{et}]",
                "borrow_kind": "value",
                "casts": [],
                "repr": self._src_slice(l["s"], r["e"]),
                "elements": elements,
            }
        if tok["k"] == "{":
            l = self._eat("{")
            if self._cur()["k"] == "}":
                r = self._eat("}")
                return {
                    "kind": "Dict",
                    "source_span": self._node_span(l["s"], r["e"]),
                    "resolved_type": "dict[unknown,unknown]",
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": self._src_slice(l["s"], r["e"]),
                    "keys": [],
                    "values": [],
                }
            first = self._parse_ifexp()
            if self._cur()["k"] == ":":
                keys = [first]
                vals: list[dict[str, Any]] = []
                self._eat(":")
                vals.append(self._parse_ifexp())
                while self._cur()["k"] == ",":
                    self._eat(",")
                    if self._cur()["k"] == "}":
                        break
                    keys.append(self._parse_ifexp())
                    self._eat(":")
                    vals.append(self._parse_ifexp())
                r = self._eat("}")
                kt = str(keys[0].get("resolved_type", "unknown")) if len(keys) > 0 else "unknown"
                vt = str(vals[0].get("resolved_type", "unknown")) if len(vals) > 0 else "unknown"
                return {
                    "kind": "Dict",
                    "source_span": self._node_span(l["s"], r["e"]),
                    "resolved_type": f"dict[{kt},{vt}]",
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": self._src_slice(l["s"], r["e"]),
                    "keys": keys,
                    "values": vals,
                }
            elements = [first]
            while self._cur()["k"] == ",":
                self._eat(",")
                if self._cur()["k"] == "}":
                    break
                elements.append(self._parse_ifexp())
            r = self._eat("}")
            et = str(elements[0].get("resolved_type", "unknown")) if len(elements) > 0 else "unknown"
            return {
                "kind": "Set",
                "source_span": self._node_span(l["s"], r["e"]),
                "resolved_type": f"set[{et}]",
                "borrow_kind": "value",
                "casts": [],
                "repr": self._src_slice(l["s"], r["e"]),
                "elements": elements,
            }
        raise EastBuildError(
            kind="unsupported_syntax",
            message=f"self_hosted parser cannot parse expression token: {tok['k']}",
            source_span=self._node_span(tok["s"], tok["e"]),
            hint="Extend self_hosted expression parser for this syntax.",
        )


def _sh_parse_expr(
    text: str,
    *,
    line_no: int,
    col_base: int,
    name_types: dict[str, str],
    fn_return_types: dict[str, str],
    class_method_return_types: dict[str, dict[str, str]] | None = None,
    class_base: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    """1つの式文字列を self-hosted 方式で EAST 式ノードに変換する。"""
    txt = text.strip()
    if txt == "":
        raise EastBuildError(
            kind="unsupported_syntax",
            message="empty expression in self_hosted backend",
            source_span=_sh_span(line_no, col_base, col_base),
            hint="Provide a non-empty expression.",
        )
    parser = _ShExprParser(
        txt,
        line_no=line_no,
        col_base=col_base + (len(text) - len(text.lstrip())),
        name_types=name_types,
        fn_return_types=fn_return_types,
        class_method_return_types=class_method_return_types,
        class_base=class_base,
    )
    return parser.parse()


def _sh_parse_expr_lowered(expr_txt: str, *, ln_no: int, col: int, name_types: dict[str, str]) -> dict[str, Any]:
    """式文字列を EAST 式ノードへ変換する（簡易 lower を含む）。"""
    raw = expr_txt
    txt = raw.strip()

    # lambda は if-expression より結合が弱いので、
    # ここでの簡易 ifexp 分解を回避して self_hosted 式パーサへ委譲する。
    if txt.startswith("lambda "):
        return _sh_parse_expr(
            txt,
            line_no=ln_no,
            col_base=col,
            name_types=name_types,
            fn_return_types=_SH_FN_RETURNS,
            class_method_return_types=_SH_CLASS_METHOD_RETURNS,
            class_base=_SH_CLASS_BASE,
        )

    # if-expression: a if cond else b
    p_if = _sh_split_top_keyword(txt, "if")
    p_else = _sh_split_top_keyword(txt, "else")
    if p_if >= 0 and p_else > p_if:
        body_txt = txt[:p_if].strip()
        test_txt = txt[p_if + 2 : p_else].strip()
        else_txt = txt[p_else + 4 :].strip()
        body_node = _sh_parse_expr_lowered(body_txt, ln_no=ln_no, col=col + txt.find(body_txt), name_types=dict(name_types))
        test_node = _sh_parse_expr_lowered(test_txt, ln_no=ln_no, col=col + txt.find(test_txt), name_types=dict(name_types))
        else_node = _sh_parse_expr_lowered(else_txt, ln_no=ln_no, col=col + txt.rfind(else_txt), name_types=dict(name_types))
        rt = body_node.get("resolved_type", "unknown")
        if rt != else_node.get("resolved_type", "unknown"):
            rt = "unknown"
        return {
            "kind": "IfExp",
            "source_span": _sh_span(ln_no, col, col + len(raw)),
            "resolved_type": rt,
            "borrow_kind": "value",
            "casts": [],
            "repr": txt,
            "test": test_node,
            "body": body_node,
            "orelse": else_node,
        }

    # Normalize generator-arg any/all into list-comp form for self_hosted parser.
    m_any_all: re.Match | None = re.match(r"^(any|all)\((.+)\)$", txt, flags=re.S)
    if m_any_all is not None:
        fn_name = re.group(m_any_all, 1)
        inner_arg = re.strip_group(m_any_all, 2)
        if _sh_split_top_keyword(inner_arg, "for") > 0 and _sh_split_top_keyword(inner_arg, "in") > 0:
            lc = _sh_parse_expr_lowered(f"[{inner_arg}]", ln_no=ln_no, col=col + txt.find(inner_arg), name_types=dict(name_types))
            return {
                "kind": "Call",
                "source_span": _sh_span(ln_no, col, col + len(raw)),
                "resolved_type": "bool",
                "borrow_kind": "value",
                "casts": [],
                "repr": txt,
                "func": {
                    "kind": "Name",
                    "source_span": _sh_span(ln_no, col, col + len(fn_name)),
                    "resolved_type": "unknown",
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": fn_name,
                    "id": fn_name,
                },
                "args": [lc],
                "keywords": [],
            }

    # Normalize single generator-argument calls into list-comp argument form.
    # Example: ", ".join(f(x) for x in items) -> ", ".join([f(x) for x in items])
    if txt.endswith(")"):
        depth = 0
        in_str: str | None = None
        esc = False
        open_idx = -1
        close_idx = -1
        for idx, ch in enumerate(txt):
            if in_str is not None:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == in_str:
                    in_str = None
                continue
            if ch in {"'", '"'}:
                in_str = ch
                continue
            if ch == "(":
                if depth == 0 and open_idx < 0:
                    open_idx = idx
                depth += 1
                continue
            if ch == ")":
                depth -= 1
                if depth == 0:
                    close_idx = idx
                continue
            if open_idx > 0 and close_idx == len(txt) - 1:
                inner = txt[open_idx + 1 : close_idx].strip()
                if _sh_split_top_commas(inner) == [inner] and _sh_split_top_keyword(inner, "for") > 0 and _sh_split_top_keyword(inner, "in") > 0:
                    rewritten = txt[: open_idx + 1] + "[" + inner + "]" + txt[close_idx:]
                    return _sh_parse_expr_lowered(rewritten, ln_no=ln_no, col=col, name_types=dict(name_types))

    # Handle concatenation chains that include f-strings before generic parsing.
    plus_parts = _sh_split_top_plus(txt)
    if len(plus_parts) >= 2 and any(p.startswith("f\"") or p.startswith("f'") for p in plus_parts):
        nodes = [_sh_parse_expr_lowered(p, ln_no=ln_no, col=col + txt.find(p), name_types=dict(name_types)) for p in plus_parts]
        node = nodes[0]
        for rhs in nodes[1:]:
            node = {
                "kind": "BinOp",
                "source_span": _sh_span(ln_no, col, col + len(raw)),
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
                "repr": txt,
                "left": node,
                "op": "Add",
                "right": rhs,
            }
        return node

    # dict-comp support: {k: v for x in it} / {k: v for a, b in it}
    if txt.startswith("{") and txt.endswith("}") and ":" in txt:
        inner = txt[1:-1].strip()
        p_for = _sh_split_top_keyword(inner, "for")
        if p_for > 0:
            head = inner[:p_for].strip()
            tail = inner[p_for + 3 :].strip()
            p_in = _sh_split_top_keyword(tail, "in")
            if p_in <= 0:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"invalid dict comprehension in self_hosted parser: {txt}",
                    source_span=_sh_span(ln_no, col, col + len(raw)),
                    hint="Use `{key: value for item in iterable}` form.",
                )
            tgt_txt = tail[:p_in].strip()
            iter_and_if_txt = tail[p_in + 2 :].strip()
            p_if = _sh_split_top_keyword(iter_and_if_txt, "if")
            if p_if >= 0:
                iter_txt = iter_and_if_txt[:p_if].strip()
                if_txt = iter_and_if_txt[p_if + 2 :].strip()
            else:
                iter_txt = iter_and_if_txt
                if_txt = ""
            if ":" not in head:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"invalid dict comprehension pair in self_hosted parser: {txt}",
                    source_span=_sh_span(ln_no, col, col + len(raw)),
                    hint="Use `key: value` pair before `for`.",
                )
            ktxt, vtxt = head.split(":", 1)
            ktxt = ktxt.strip()
            vtxt = vtxt.strip()
            target_node = _sh_parse_expr_lowered(tgt_txt, ln_no=ln_no, col=col + txt.find(tgt_txt), name_types=dict(name_types))
            iter_node = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=col + txt.find(iter_txt), name_types=dict(name_types))
            comp_types = _sh_bind_comp_target_types(dict(name_types), target_node, iter_node)
            key_node = _sh_parse_expr_lowered(ktxt, ln_no=ln_no, col=col + txt.find(ktxt), name_types=dict(comp_types))
            val_node = _sh_parse_expr_lowered(vtxt, ln_no=ln_no, col=col + txt.find(vtxt), name_types=dict(comp_types))
            if_nodes: list[dict[str, Any]] = []
            if if_txt != "":
                if_nodes.append(_sh_parse_expr_lowered(if_txt, ln_no=ln_no, col=col + txt.find(if_txt), name_types=dict(comp_types)))
            kt = str(key_node.get("resolved_type", "unknown"))
            vt = str(val_node.get("resolved_type", "unknown"))
            return {
                "kind": "DictComp",
                "source_span": _sh_span(ln_no, col, col + len(raw)),
                "resolved_type": f"dict[{kt},{vt}]",
                "borrow_kind": "value",
                "casts": [],
                "repr": txt,
                "key": key_node,
                "value": val_node,
                "generators": [
                    {
                        "target": target_node,
                        "iter": iter_node,
                        "ifs": if_nodes,
                        "is_async": False,
                    }
                ],
            }

    # set-comp support: {x for x in it} / {x for a, b in it if cond}
    if txt.startswith("{") and txt.endswith("}") and ":" not in txt:
        inner = txt[1:-1].strip()
        p_for = _sh_split_top_keyword(inner, "for")
        if p_for > 0:
            elt_txt = inner[:p_for].strip()
            tail = inner[p_for + 3 :].strip()
            p_in = _sh_split_top_keyword(tail, "in")
            if p_in <= 0:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"invalid set comprehension in self_hosted parser: {txt}",
                    source_span=_sh_span(ln_no, col, col + len(raw)),
                    hint="Use `{elem for item in iterable}` form.",
                )
            tgt_txt = tail[:p_in].strip()
            iter_and_if_txt = tail[p_in + 2 :].strip()
            p_if = _sh_split_top_keyword(iter_and_if_txt, "if")
            if p_if >= 0:
                iter_txt = iter_and_if_txt[:p_if].strip()
                if_txt = iter_and_if_txt[p_if + 2 :].strip()
            else:
                iter_txt = iter_and_if_txt
                if_txt = ""
            iter_node = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=col + txt.find(iter_txt), name_types=dict(name_types))
            target_node = _sh_parse_expr_lowered(tgt_txt, ln_no=ln_no, col=col + txt.find(tgt_txt), name_types=dict(name_types))
            comp_types = _sh_bind_comp_target_types(dict(name_types), target_node, iter_node)
            elt_node = _sh_parse_expr_lowered(elt_txt, ln_no=ln_no, col=col + txt.find(elt_txt), name_types=dict(comp_types))
            if_nodes: list[dict[str, Any]] = []
            if if_txt != "":
                if_nodes.append(_sh_parse_expr_lowered(if_txt, ln_no=ln_no, col=col + txt.find(if_txt), name_types=dict(comp_types)))
            return {
                "kind": "SetComp",
                "source_span": _sh_span(ln_no, col, col + len(raw)),
                "resolved_type": f"set[{elt_node.get('resolved_type', 'unknown')}]",
                "borrow_kind": "value",
                "casts": [],
                "repr": txt,
                "elt": elt_node,
                "generators": [
                    {
                        "target": target_node,
                        "iter": iter_node,
                        "ifs": if_nodes,
                        "is_async": False,
                    }
                ],
            }

    # dict literal: {"a": 1, "b": 2}
    if txt.startswith("{") and txt.endswith("}") and ":" in txt:
        inner = txt[1:-1].strip()
        entries: list[dict[str, Any]] = []
        if inner != "":
            for part in _sh_split_top_commas(inner):
                if ":" not in part:
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message=f"invalid dict entry in self_hosted parser: {part}",
                        source_span=_sh_span(ln_no, col, col + len(raw)),
                        hint="Use `key: value` form in dict literals.",
                    )
                ktxt, vtxt = part.split(":", 1)
                ktxt = ktxt.strip()
                vtxt = vtxt.strip()
                entries.append(
                    {
                        "key": _sh_parse_expr_lowered(ktxt, ln_no=ln_no, col=col + txt.find(ktxt), name_types=dict(name_types)),
                        "value": _sh_parse_expr_lowered(vtxt, ln_no=ln_no, col=col + txt.find(vtxt), name_types=dict(name_types)),
                    }
                )
        kt = "unknown"
        vt = "unknown"
        if len(entries) > 0:
            first_key: dict[str, Any] = entries[0]["key"]
            first_value: dict[str, Any] = entries[0]["value"]
            kt = str(first_key.get("resolved_type", "unknown"))
            vt = str(first_value.get("resolved_type", "unknown"))
        return {
            "kind": "Dict",
            "source_span": _sh_span(ln_no, col, col + len(raw)),
            "resolved_type": f"dict[{kt},{vt}]",
            "borrow_kind": "value",
            "casts": [],
            "repr": txt,
            "entries": entries,
        }

    # list-comp support: [expr for target in iter if cond]
    if txt.startswith("[") and txt.endswith("]"):
        inner = txt[1:-1].strip()
        p_for = _sh_split_top_keyword(inner, "for")
        if p_for > 0:
            elt_txt = inner[:p_for].strip()
            tail = inner[p_for + 3 :].strip()
            p_in = _sh_split_top_keyword(tail, "in")
            if p_in <= 0:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"invalid list comprehension in self_hosted parser: {txt}",
                    source_span=_sh_span(ln_no, col, col + len(raw)),
                    hint="Use `[elem for item in iterable]` form.",
                )
            tgt_txt = tail[:p_in].strip()
            iter_and_if_txt = tail[p_in + 2 :].strip()
            p_if = _sh_split_top_keyword(iter_and_if_txt, "if")
            if p_if >= 0:
                iter_txt = iter_and_if_txt[:p_if].strip()
                if_txt = iter_and_if_txt[p_if + 2 :].strip()
            else:
                iter_txt = iter_and_if_txt
                if_txt = ""
            target_node = _sh_parse_expr_lowered(tgt_txt, ln_no=ln_no, col=col + txt.find(tgt_txt), name_types=dict(name_types))
            iter_node = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=col + txt.find(iter_txt), name_types=dict(name_types))
            if (
                isinstance(iter_node, dict)
                and iter_node.get("kind") == "Call"
                and isinstance(iter_node.get("func"), dict)
                and iter_node.get("func", {}).get("kind") == "Name"
                and iter_node.get("func", {}).get("id") == "range"
            ):
                rargs = list(iter_node.get("args", []))
                if len(rargs) == 1:
                    start_node = {
                        "kind": "Constant",
                        "source_span": _sh_span(ln_no, col, col),
                        "resolved_type": "int64",
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": "0",
                        "value": 0,
                    }
                    stop_node = rargs[0]
                    step_node = {
                        "kind": "Constant",
                        "source_span": _sh_span(ln_no, col, col),
                        "resolved_type": "int64",
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": "1",
                        "value": 1,
                    }
                elif len(rargs) == 2:
                    start_node = rargs[0]
                    stop_node = rargs[1]
                    step_node = {
                        "kind": "Constant",
                        "source_span": _sh_span(ln_no, col, col),
                        "resolved_type": "int64",
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": "1",
                        "value": 1,
                    }
                else:
                    start_node = rargs[0]
                    stop_node = rargs[1]
                    step_node = rargs[2]
                step_const = step_node.get("value") if isinstance(step_node, dict) else None
                mode = "dynamic"
                if step_const == 1:
                    mode = "ascending"
                elif step_const == -1:
                    mode = "descending"
                iter_node = {
                    "kind": "RangeExpr",
                    "source_span": iter_node.get("source_span"),
                    "resolved_type": "range",
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": iter_node.get("repr", "range(...)"),
                    "start": start_node,
                    "stop": stop_node,
                    "step": step_node,
                    "range_mode": mode,
                }

            comp_types = _sh_bind_comp_target_types(dict(name_types), target_node, iter_node)
            elt_node = _sh_parse_expr_lowered(elt_txt, ln_no=ln_no, col=col + txt.find(elt_txt), name_types=dict(comp_types))
            if_nodes: list[dict[str, Any]] = []
            if if_txt != "":
                if_nodes.append(_sh_parse_expr_lowered(if_txt, ln_no=ln_no, col=col + txt.find(if_txt), name_types=dict(comp_types)))
            elem_t = str(elt_node.get("resolved_type", "unknown"))
            return {
                "kind": "ListComp",
                "source_span": _sh_span(ln_no, col, col + len(raw)),
                "resolved_type": f"list[{elem_t}]",
                "borrow_kind": "value",
                "casts": [],
                "repr": txt,
                "elt": elt_node,
                "generators": [
                    {
                        "target": target_node,
                        "iter": iter_node,
                        "ifs": if_nodes,
                        "is_async": False,
                    }
                ],
            }

    # Very simple list-comp support: [x for x in <iter>]
    m_lc: re.Match | None = re.match(r"^\[\s*([A-Za-z_][A-Za-z0-9_]*)\s+for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.+)\]$", txt)
    if m_lc is not None:
        elt_name = re.group(m_lc, 1)
        tgt_name = re.group(m_lc, 2)
        iter_txt = re.strip_group(m_lc, 3)
        iter_node = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=col + txt.find(iter_txt), name_types=dict(name_types))
        it_t = str(iter_node.get("resolved_type", "unknown"))
        elem_t = "unknown"
        if it_t.startswith("list[") and it_t.endswith("]"):
            elem_t = it_t[5:-1]
        elt_node = {
            "kind": "Name",
            "source_span": _sh_span(ln_no, col, col + len(elt_name)),
            "resolved_type": elem_t if elt_name == tgt_name else "unknown",
            "borrow_kind": "value",
            "casts": [],
            "repr": elt_name,
            "id": elt_name,
        }
        return {
            "kind": "ListComp",
            "source_span": _sh_span(ln_no, col, col + len(raw)),
            "resolved_type": f"list[{elem_t}]",
            "borrow_kind": "value",
            "casts": [],
            "repr": txt,
            "elt": elt_node,
            "generators": [
                {
                    "target": {
                        "kind": "Name",
                        "source_span": _sh_span(ln_no, col, col + len(tgt_name)),
                        "resolved_type": "unknown",
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": tgt_name,
                        "id": tgt_name,
                    },
                    "iter": iter_node,
                    "ifs": [],
                }
            ],
            "lowered_kind": "ListCompSimple",
        }

    if len(txt) >= 3 and txt[0] == "f" and txt[1] in {"'", '"'} and txt[-1] == txt[1]:
        quote = txt[1]
        inner = txt[2:-1]
        values: list[dict[str, Any]] = []

        i = 0
        while i < len(inner):
            j = inner.find("{", i)
            if j < 0:
                _sh_append_fstring_literal(values, inner[i:], _sh_span(ln_no, col, col + len(raw)))
                break
            if j + 1 < len(inner) and inner[j + 1] == "{":
                _sh_append_fstring_literal(values, inner[i : j + 1], _sh_span(ln_no, col, col + len(raw)))
                i = j + 2
                continue
            if j > i:
                _sh_append_fstring_literal(values, inner[i:j], _sh_span(ln_no, col, col + len(raw)))
            k = inner.find("}", j + 1)
            if k < 0:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message="unterminated f-string placeholder in self_hosted parser",
                    source_span=_sh_span(ln_no, col, col + len(raw)),
                    hint="Close f-string placeholder with `}`.",
                )
            inner_expr = inner[j + 1 : k].strip()
            values.append({"kind": "FormattedValue", "value": _sh_parse_expr_lowered(inner_expr, ln_no=ln_no, col=col, name_types=dict(name_types))})
            i = k + 1
        return {
            "kind": "JoinedStr",
            "source_span": _sh_span(ln_no, col, col + len(raw)),
            "resolved_type": "str",
            "borrow_kind": "value",
            "casts": [],
            "repr": txt,
            "values": values,
        }

    tuple_parts = _sh_split_top_commas(txt)
    if len(tuple_parts) >= 2:
        elems = [_sh_parse_expr_lowered(p, ln_no=ln_no, col=col + txt.find(p), name_types=dict(name_types)) for p in tuple_parts]
        elem_ts = [str(e.get("resolved_type", "unknown")) for e in elems]
        return {
            "kind": "Tuple",
            "source_span": _sh_span(ln_no, col, col + len(raw)),
            "resolved_type": "tuple[" + ", ".join(elem_ts) + "]",
            "borrow_kind": "value",
            "casts": [],
            "repr": txt,
            "elements": elems,
        }

    return _sh_parse_expr(
        txt,
        line_no=ln_no,
        col_base=col,
        name_types=name_types,
        fn_return_types=_SH_FN_RETURNS,
        class_method_return_types=_SH_CLASS_METHOD_RETURNS,
        class_base=_SH_CLASS_BASE,
    )

def _sh_parse_stmt_block(body_lines: list[tuple[int, str]], *, name_types: dict[str, str], scope_label: str) -> list[dict[str, Any]]:
    """インデントブロックを文単位で解析し、EAST 文リストを返す。"""
    body_lines, merged_line_end = _sh_merge_logical_lines(body_lines)

    stmts: list[dict[str, Any]] = []
    pending_leading_trivia: list[dict[str, Any]] = []
    pending_blank_count = 0

    i = 0
    while i < len(body_lines):
        ln_no, ln_txt = body_lines[i]
        indent = len(ln_txt) - len(ln_txt.lstrip(" "))
        raw_s = ln_txt.strip()
        s = _sh_strip_inline_comment(raw_s)

        if raw_s == "":
            pending_blank_count += 1
            i += 1
            continue
        if raw_s.startswith("#"):
            if pending_blank_count > 0:
                pending_leading_trivia.append({"kind": "blank", "count": pending_blank_count})
                pending_blank_count = 0
            text = raw_s[1:]
            if text.startswith(" "):
                text = text[1:]
            pending_leading_trivia.append({"kind": "comment", "text": text})
            i += 1
            continue
        if s == "":
            i += 1
            continue

        if s.startswith("if ") and s.endswith(":"):
            cond_txt = s[len("if ") : -1].strip()
            cond_col = ln_txt.find(cond_txt)
            cond_expr = _sh_parse_expr_lowered(cond_txt, ln_no=ln_no, col=cond_col, name_types=dict(name_types))
            then_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(then_block) == 0:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"if body is missing in '{scope_label}'",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Add indented if-body.",
                )
            else_stmt_list, j = _sh_parse_if_tail(
                start_idx=j,
                parent_indent=indent,
                body_lines=body_lines,
                name_types=dict(name_types),
                scope_label=scope_label,
            )
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                {
                    "kind": "If",
                    "source_span": _sh_block_end_span(body_lines, ln_no, ln_txt.find("if "), len(ln_txt), j),
                    "test": cond_expr,
                    "body": _sh_parse_stmt_block(then_block, name_types=dict(name_types), scope_label=scope_label),
                    "orelse": else_stmt_list,
                }
            )
            i = j
            continue

        if s.startswith("for ") and s.endswith(":"):
            m_for: re.Match | None = re.match(r"^for\s+(.+)\s+in\s+(.+):$", s, flags=re.S)
            if m_for is None:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse for statement: {s}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `for target in iterable:` form.",
                )
            tgt_txt = re.strip_group(m_for, 1)
            iter_txt = re.strip_group(m_for, 2)
            tgt_col = ln_txt.find(tgt_txt)
            iter_col = ln_txt.find(iter_txt)
            target_expr = _sh_parse_expr_lowered(tgt_txt, ln_no=ln_no, col=tgt_col, name_types=dict(name_types))
            iter_expr = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=iter_col, name_types=dict(name_types))
            body_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(body_block) == 0:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"for body is missing in '{scope_label}'",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Add indented for-body.",
                )
            t_ty = "unknown"
            i_ty = str(iter_expr.get("resolved_type", "unknown"))
            if i_ty.startswith("list[") and i_ty.endswith("]"):
                t_ty = i_ty[5:-1]
            elif i_ty.startswith("tuple[") and i_ty.endswith("]"):
                t_ty = "unknown"
            elif i_ty.startswith("set[") and i_ty.endswith("]"):
                t_ty = i_ty[4:-1]
            elif i_ty == "str":
                t_ty = "str"
            elif i_ty in {"bytes", "bytearray"}:
                t_ty = "uint8"
            target_names: list[str] = []
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                nm = str(target_expr.get("id", ""))
                if nm != "":
                    target_names.append(nm)
            elif isinstance(target_expr, dict) and target_expr.get("kind") == "Tuple":
                for e in target_expr.get("elements", []):
                    if isinstance(e, dict) and e.get("kind") == "Name":
                        nm = str(e.get("id", ""))
                        if nm != "":
                            target_names.append(nm)
            if t_ty != "unknown":
                for nm in target_names:
                    name_types[nm] = t_ty
            if (
                isinstance(target_expr, dict)
                and target_expr.get("kind") == "Name"
                and
                isinstance(iter_expr, dict)
                and iter_expr.get("kind") == "Call"
                and isinstance(iter_expr.get("func"), dict)
                and iter_expr.get("func", {}).get("kind") == "Name"
                and iter_expr.get("func", {}).get("id") == "range"
            ):
                rargs = list(iter_expr.get("args", []))
                start_node: dict[str, Any]
                stop_node: dict[str, Any]
                step_node: dict[str, Any]
                if len(rargs) == 1:
                    start_node = {
                        "kind": "Constant",
                        "source_span": _sh_span(ln_no, ln_txt.find("range"), ln_txt.find("range") + 5),
                        "resolved_type": "int64",
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": "0",
                        "value": 0,
                    }
                    stop_node = rargs[0]
                    step_node = {
                        "kind": "Constant",
                        "source_span": _sh_span(ln_no, ln_txt.find("range"), ln_txt.find("range") + 5),
                        "resolved_type": "int64",
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": "1",
                        "value": 1,
                    }
                elif len(rargs) == 2:
                    start_node = rargs[0]
                    stop_node = rargs[1]
                    step_node = {
                        "kind": "Constant",
                        "source_span": _sh_span(ln_no, ln_txt.find("range"), ln_txt.find("range") + 5),
                        "resolved_type": "int64",
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": "1",
                        "value": 1,
                    }
                else:
                    start_node = rargs[0]
                    stop_node = rargs[1]
                    step_node = rargs[2]
                tgt = str(target_expr.get("id", ""))
                if tgt != "":
                    name_types[tgt] = "int64"
                step_const = step_node.get("value") if isinstance(step_node, dict) else None
                mode = "dynamic"
                if step_const == 1:
                    mode = "ascending"
                elif step_const == -1:
                    mode = "descending"
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                    {
                        "kind": "ForRange",
                        "source_span": _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                        "target": target_expr,
                        "target_type": "int64",
                        "start": start_node,
                        "stop": stop_node,
                        "step": step_node,
                        "range_mode": mode,
                        "body": _sh_parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                        "orelse": [],
                    }
                )
                i = j
                continue
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                {
                    "kind": "For",
                    "source_span": _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                    "target": target_expr,
                    "target_type": t_ty,
                    "iter": iter_expr,
                    "body": _sh_parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                    "orelse": [],
                }
            )
            i = j
            continue

        if s.startswith("with ") and s.endswith(":"):
            m_with: re.Match | None = re.match(r"^with\s+(.+)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$", s, flags=re.S)
            if m_with is None:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse with statement: {s}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `with expr as name:` form.",
                )
            ctx_txt = re.strip_group(m_with, 1)
            as_name = re.strip_group(m_with, 2)
            ctx_col = ln_txt.find(ctx_txt)
            as_col = ln_txt.find(as_name, ctx_col + len(ctx_txt))
            ctx_expr = _sh_parse_expr_lowered(ctx_txt, ln_no=ln_no, col=ctx_col, name_types=dict(name_types))
            name_types[as_name] = str(ctx_expr.get("resolved_type", "unknown"))
            body_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(body_block) == 0:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"with body is missing in '{scope_label}'",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Add indented with-body.",
                )
            assign_stmt = {
                "kind": "Assign",
                "source_span": _sh_stmt_span(merged_line_end, ln_no, as_col, len(ln_txt)),
                "target": {
                    "kind": "Name",
                    "source_span": _sh_span(ln_no, as_col, as_col + len(as_name)),
                    "resolved_type": str(ctx_expr.get("resolved_type", "unknown")),
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": as_name,
                    "id": as_name,
                },
                "value": ctx_expr,
                "declare": True,
                "declare_init": True,
                "decl_type": str(ctx_expr.get("resolved_type", "unknown")),
            }
            close_expr = _sh_parse_expr_lowered(f"{as_name}.close()", ln_no=ln_no, col=as_col, name_types=dict(name_types))
            try_stmt = {
                "kind": "Try",
                "source_span": _sh_block_end_span(body_lines, ln_no, ln_txt.find("with "), len(ln_txt), j),
                "body": _sh_parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                "handlers": [],
                "orelse": [],
                "finalbody": [{"kind": "Expr", "source_span": _sh_stmt_span(merged_line_end, ln_no, as_col, len(ln_txt)), "value": close_expr}],
            }
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, assign_stmt)
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, try_stmt)
            i = j
            continue

        if s.startswith("while ") and s.endswith(":"):
            cond_txt = s[len("while ") : -1].strip()
            cond_col = ln_txt.find(cond_txt)
            cond_expr = _sh_parse_expr_lowered(cond_txt, ln_no=ln_no, col=cond_col, name_types=dict(name_types))
            body_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(body_block) == 0:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"while body is missing in '{scope_label}'",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Add indented while-body.",
                )
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                {
                    "kind": "While",
                    "source_span": _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                    "test": cond_expr,
                    "body": _sh_parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                    "orelse": [],
                }
            )
            i = j
            continue

        if s == "try:":
            try_body, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(try_body) == 0:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"try body is missing in '{scope_label}'",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Add indented try-body.",
                )
            handlers: list[dict[str, Any]] = []
            finalbody: list[dict[str, Any]] = []
            while j < len(body_lines):
                h_no, h_ln = body_lines[j]
                h_s = h_ln.strip()
                h_indent = len(h_ln) - len(h_ln.lstrip(" "))
                if h_indent != indent:
                    break
                m_exc_as: re.Match | None = re.match(r"^except\s+(.+?)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$", h_s, flags=re.S)
                m_exc_plain: re.Match | None = re.match(r"^except\s+(.+?)\s*:\s*$", h_s, flags=re.S)
                if m_exc_as is not None or m_exc_plain is not None:
                    if m_exc_as is not None:
                        ex_type_txt = re.strip_group(m_exc_as, 1)
                        ex_name: str | None = re.group(m_exc_as, 2)
                    else:
                        ex_type_txt = re.strip_group(m_exc_plain, 1) if m_exc_plain is not None else "Exception"
                        ex_name = None
                    ex_type_col = h_ln.find(ex_type_txt)
                    h_body, k = _sh_collect_indented_block(body_lines, j + 1, indent)
                    handlers.append(
                        {
                            "kind": "ExceptHandler",
                            "type": _sh_parse_expr_lowered(ex_type_txt, ln_no=h_no, col=ex_type_col, name_types=dict(name_types)),
                            "name": ex_name,
                            "body": _sh_parse_stmt_block(h_body, name_types=dict(name_types), scope_label=scope_label),
                        }
                    )
                    j = k
                    continue
                if h_s == "finally:":
                    f_body, k = _sh_collect_indented_block(body_lines, j + 1, indent)
                    finalbody = _sh_parse_stmt_block(f_body, name_types=dict(name_types), scope_label=scope_label)
                    j = k
                    continue
                break
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                {
                    "kind": "Try",
                    "source_span": _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                    "body": _sh_parse_stmt_block(try_body, name_types=dict(name_types), scope_label=scope_label),
                    "handlers": handlers,
                    "orelse": [],
                    "finalbody": finalbody,
                }
            )
            i = j
            continue

        if s.startswith("raise "):
            expr_txt = s[len("raise ") :].strip()
            expr_col = ln_txt.find(expr_txt)
            cause_expr = None
            cause_split = _sh_split_top_level_from(expr_txt)
            if cause_split is not None:
                exc_txt, cause_txt = cause_split
                expr_txt = exc_txt
                expr_col = ln_txt.find(expr_txt)
                cause_col = ln_txt.find(cause_txt)
                cause_expr = _sh_parse_expr_lowered(cause_txt, ln_no=ln_no, col=cause_col, name_types=dict(name_types))
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                {
                    "kind": "Raise",
                    "source_span": _sh_stmt_span(merged_line_end, ln_no, ln_txt.find("raise "), len(ln_txt)),
                    "exc": _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types)),
                    "cause": cause_expr,
                }
            )
            i += 1
            continue

        if s == "pass":
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "Pass", "source_span": _sh_stmt_span(merged_line_end, ln_no, indent, indent + 4)})
            i += 1
            continue

        if s == "return":
            rcol = ln_txt.find("return")
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                {
                    "kind": "Return",
                    "source_span": _sh_stmt_span(merged_line_end, ln_no, rcol, len(ln_txt)),
                    "value": None,
                }
            )
            i += 1
            continue

        if s.startswith("return "):
            rcol = ln_txt.find("return ")
            expr_txt = ln_txt[rcol + len("return ") :].strip()
            expr_col = ln_txt.find(expr_txt, rcol + len("return "))
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                {
                    "kind": "Return",
                    "source_span": _sh_stmt_span(merged_line_end, ln_no, rcol, len(ln_txt)),
                    "value": _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types)),
                }
            )
            i += 1
            continue

        m_ann_decl: re.Match | None = re.match(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:\s*(.+)$", s)
        if m_ann_decl is not None and "=" not in s:
            target_txt = re.group(m_ann_decl, 1)
            ann = _sh_ann_to_type(re.group(m_ann_decl, 2))
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                name_types[str(target_expr.get("id", ""))] = ann
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                {
                    "kind": "AnnAssign",
                    "source_span": _sh_stmt_span(merged_line_end, ln_no, target_col, len(ln_txt)),
                    "target": target_expr,
                    "annotation": ann,
                    "value": None,
                    "declare": True,
                    "decl_type": ann,
                }
            )
            i += 1
            continue

        m_ann: re.Match | None = re.match(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:\s*([^=]+?)\s*=\s*(.+)$", s)
        if m_ann is not None:
            target_txt = re.group(m_ann, 1)
            ann = _sh_ann_to_type(re.group(m_ann, 2))
            expr_txt = re.strip_group(m_ann, 3)
            expr_col = ln_txt.find(expr_txt)
            val_expr = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                name_types[str(target_expr.get("id", ""))] = ann
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                {
                    "kind": "AnnAssign",
                    "source_span": _sh_stmt_span(merged_line_end, ln_no, target_col, len(ln_txt)),
                    "target": target_expr,
                    "annotation": ann,
                    "value": val_expr,
                    "declare": True,
                    "decl_type": ann,
                }
            )
            i += 1
            continue

        m_aug: re.Match | None = re.match(
            r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*(\+=|-=|\*=|/=|//=|%=|&=|\|=|\^=|<<=|>>=)\s*(.+)$",
            s,
        )
        if m_aug is not None:
            target_txt = re.group(m_aug, 1)
            op_map = {
                "+=": "Add",
                "-=": "Sub",
                "*=": "Mult",
                "/=": "Div",
                "//=": "FloorDiv",
                "%=": "Mod",
                "&=": "BitAnd",
                "|=": "BitOr",
                "^=": "BitXor",
                "<<=": "LShift",
                ">>=": "RShift",
            }
            expr_txt = re.strip_group(m_aug, 3)
            expr_col = ln_txt.find(expr_txt)
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            val_expr = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            target_ty = "unknown"
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                target_ty = name_types.get(str(target_expr.get("id", "")), "unknown")
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                {
                    "kind": "AugAssign",
                    "source_span": _sh_stmt_span(merged_line_end, ln_no, target_col, len(ln_txt)),
                    "target": target_expr,
                    "op": op_map[re.group(m_aug, 2)],
                    "value": val_expr,
                    "declare": False,
                    "decl_type": target_ty if target_ty != "unknown" else None,
                }
            )
            i += 1
            continue

        m_tasg: re.Match | None = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", s)
        if m_tasg is not None:
            n1 = re.group(m_tasg, 1)
            n2 = re.group(m_tasg, 2)
            expr_txt = re.strip_group(m_tasg, 3)
            expr_col = ln_txt.find(expr_txt)
            rhs = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            c1 = ln_txt.find(n1)
            c2 = ln_txt.find(n2, c1 + len(n1))
            if (
                isinstance(rhs, dict)
                and rhs.get("kind") == "Tuple"
                and len(rhs.get("elements", [])) == 2
                and isinstance(rhs.get("elements")[0], dict)
                and isinstance(rhs.get("elements")[1], dict)
                and rhs.get("elements")[0].get("kind") == "Name"
                and rhs.get("elements")[1].get("kind") == "Name"
                and str(rhs.get("elements")[0].get("id", "")) == n2
                and str(rhs.get("elements")[1].get("id", "")) == n1
            ):
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                    {
                        "kind": "Swap",
                        "source_span": _sh_stmt_span(merged_line_end, ln_no, c1, len(ln_txt)),
                        "left": {
                            "kind": "Name",
                            "source_span": _sh_span(ln_no, c1, c1 + len(n1)),
                            "resolved_type": name_types.get(n1, "unknown"),
                            "borrow_kind": "value",
                            "casts": [],
                            "repr": n1,
                            "id": n1,
                        },
                        "right": {
                            "kind": "Name",
                            "source_span": _sh_span(ln_no, c2, c2 + len(n2)),
                            "resolved_type": name_types.get(n2, "unknown"),
                            "borrow_kind": "value",
                            "casts": [],
                            "repr": n2,
                            "id": n2,
                        },
                    }
                )
                i += 1
                continue
            target_expr = {
                "kind": "Tuple",
                "source_span": _sh_span(ln_no, c1, c2 + len(n2)),
                "resolved_type": "unknown",
                "borrow_kind": "value",
                "casts": [],
                "repr": f"{n1}, {n2}",
                "elements": [
                    {
                        "kind": "Name",
                        "source_span": _sh_span(ln_no, c1, c1 + len(n1)),
                        "resolved_type": name_types.get(n1, "unknown"),
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": n1,
                        "id": n1,
                    },
                    {
                        "kind": "Name",
                        "source_span": _sh_span(ln_no, c2, c2 + len(n2)),
                        "resolved_type": name_types.get(n2, "unknown"),
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": n2,
                        "id": n2,
                    },
                ],
            }
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                {
                    "kind": "Assign",
                    "source_span": _sh_stmt_span(merged_line_end, ln_no, c1, len(ln_txt)),
                    "target": target_expr,
                    "value": rhs,
                    "declare": False,
                    "decl_type": None,
                }
            )
            i += 1
            continue

        asg_split = _sh_split_top_level_assign(s)
        if asg_split is not None:
            target_txt, expr_txt = asg_split
            expr_col = ln_txt.find(expr_txt)
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            val_expr = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            decl_type = val_expr.get("resolved_type", "unknown")
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                nm = str(target_expr.get("id", ""))
                if nm != "":
                    name_types[nm] = str(decl_type)
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                {
                    "kind": "Assign",
                    "source_span": _sh_stmt_span(merged_line_end, ln_no, target_col, len(ln_txt)),
                    "target": target_expr,
                    "value": val_expr,
                    "declare": True,
                    "declare_init": True,
                    "decl_type": decl_type,
                }
            )
            i += 1
            continue

        expr_col = len(ln_txt) - len(ln_txt.lstrip(" "))
        expr_stmt = _sh_parse_expr_lowered(s, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
        pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "Expr", "source_span": _sh_stmt_span(merged_line_end, ln_no, expr_col, len(ln_txt)), "value": expr_stmt})
        i += 1
    return stmts


def convert_source_to_east_self_hosted(source: str, filename: str) -> dict[str, Any]:
    """Python ソースを self-hosted パーサで EAST Module に変換する。"""
    lines = source.splitlines()
    leading_file_comments: list[str] = []
    leading_file_trivia: list[dict[str, Any]] = []
    for ln in lines:
        s = ln.strip()
        if s == "":
            if len(leading_file_comments) > 0:
                leading_file_trivia.append({"kind": "blank", "count": 1})
            continue
        if s.startswith("#"):
            text = s[1:].lstrip()
            leading_file_comments.append(text)
            leading_file_trivia.append({"kind": "comment", "text": text})
            continue
        break

    class_method_return_types: dict[str, dict[str, str]] = {}
    class_base: dict[str, str | None] = {}
    fn_returns: dict[str, str] = {}

    cur_cls: str | None = None
    cur_cls_indent = 0
    for ln_no, ln in enumerate(lines, start=1):
        s = ln.strip()
        if s == "":
            continue
        indent = len(ln) - len(ln.lstrip(" "))
        if cur_cls is not None and indent <= cur_cls_indent and not s.startswith("#"):
            cur_cls = None
        m_cls: re.Match | None = re.match(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\(([A-Za-z_][A-Za-z0-9_]*)\))?\s*:\s*$", ln)
        if m_cls is not None:
            cur_cls = re.group(m_cls, 1)
            cur_cls_indent = indent
            class_base[cur_cls] = re.group(m_cls, 2)
            class_method_return_types.setdefault(cur_cls, {})
            continue
        if cur_cls is None:
            sig = _sh_parse_def_sig(ln_no, ln)
            if sig is not None:
                fn_returns[str(sig["name"])] = str(sig["ret"])
            continue
        sig = _sh_parse_def_sig(ln_no, ln, in_class=cur_cls)
        if sig is not None:
            class_method_return_types[cur_cls][str(sig["name"])] = str(sig["ret"])

    _sh_set_parse_context(fn_returns, class_method_return_types, class_base)
    parse_expr = _sh_parse_expr_lowered

    parse_stmt_block = _sh_parse_stmt_block

    body_items: list[dict[str, Any]] = []
    main_stmts: list[dict[str, Any]] = []
    import_module_bindings: dict[str, str] = {}
    import_symbol_bindings: dict[str, dict[str, str]] = {}
    import_bindings: list[dict[str, Any]] = []
    import_binding_names: set[str] = set()
    first_item_attached = False
    pending_dataclass = False

    top_lines = list(enumerate(lines, start=1))
    top_merged_lines, top_merged_end = _sh_merge_logical_lines(top_lines)
    top_merged_map = {ln_no: txt for ln_no, txt in top_merged_lines}
    i = 1
    while i <= len(lines):
        ln = top_merged_map.get(i, lines[i - 1])
        logical_end = top_merged_end.get(i, (i, len(lines[i - 1])))[0]
        s = ln.strip()
        if s == "" or s.startswith("#"):
            i += 1
            continue
        if ln.startswith(" "):
            i += 1
            continue

        m_main: re.Match | None = re.match(r"^if\s+__name__\s*==\s*[\"']__main__[\"']\s*:\s*$", ln)
        if m_main is not None:
            block: list[tuple[int, str]] = []
            j = i + 1
            while j <= len(lines):
                bl = lines[j - 1]
                if bl.strip() == "":
                    block.append((j, bl))
                    j += 1
                    continue
                if not bl.startswith(" "):
                    break
                block.append((j, bl))
                j += 1
            main_name_types: dict[str, str] = {}
            main_stmts = parse_stmt_block(block, name_types=main_name_types, scope_label="__main__")
            i = j
            continue
        sig_line = ln
        sig_end_line = logical_end
        sig = _sh_parse_def_sig(i, sig_line)
        if sig is not None:
            fn_name = str(sig["name"])
            fn_ret = str(sig["ret"])
            arg_types = dict(sig["arg_types"])
            arg_order = list(sig.get("arg_order", list(arg_types.keys())))
            arg_defaults_raw_obj = sig.get("arg_defaults")
            arg_defaults_raw = arg_defaults_raw_obj if isinstance(arg_defaults_raw_obj, dict) else {}
            block: list[tuple[int, str]] = []
            j = sig_end_line + 1
            while j <= len(lines):
                bl = lines[j - 1]
                if bl.strip() == "":
                    block.append((j, bl))
                    j += 1
                    continue
                if not bl.startswith(" "):
                    break
                block.append((j, bl))
                j += 1
            if len(block) == 0:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser requires non-empty function body '{fn_name}'",
                    source_span=_sh_span(i, 0, len(sig_line)),
                    hint="Add return or assignment statements in function body.",
                )
            stmts = parse_stmt_block(block, name_types=dict(arg_types), scope_label=fn_name)
            docstring, stmts = _sh_extract_leading_docstring(stmts)
            arg_defaults: dict[str, Any] = {}
            for arg_name in arg_order:
                if arg_name in arg_defaults_raw:
                    default_txt = str(arg_defaults_raw[arg_name]).strip()
                    if default_txt != "":
                        default_col = sig_line.find(default_txt)
                        if default_col < 0:
                            default_col = 0
                        arg_defaults[arg_name] = parse_expr(
                            default_txt,
                            ln_no=i,
                            col=default_col,
                            name_types=dict(arg_types),
                        )
            item = {
                "kind": "FunctionDef",
                "name": fn_name,
                "original_name": fn_name,
                "source_span": {"lineno": i, "col": 0, "end_lineno": block[-1][0], "end_col": len(block[-1][1])},
                "arg_types": arg_types,
                "arg_order": arg_order,
                "arg_defaults": arg_defaults,
                "arg_index": {n: i for i, n in enumerate(arg_order)},
                "return_type": fn_ret,
                "arg_usage": {n: "readonly" for n in arg_types.keys()},
                "renamed_symbols": {},
                "leading_comments": [],
                "leading_trivia": [],
                "docstring": docstring,
                "body": stmts,
            }
            if not first_item_attached:
                item["leading_comments"] = list(leading_file_comments)
                item["leading_trivia"] = list(leading_file_trivia)
                first_item_attached = True
            body_items.append(item)
            i = j
            continue

        if s == "@dataclass":
            pending_dataclass = True
            i += 1
            continue
        m_import: re.Match | None = re.match(r"^import\s+(.+)$", s, flags=re.S)
        if m_import is not None:
            names_txt = re.strip_group(m_import, 1)
            raw_parts = [p.strip() for p in names_txt.split(",") if p.strip() != ""]
            if len(raw_parts) == 0:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message="import statement has no module names",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Use `import module` or `import module as alias`.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                m_alias: re.Match | None = re.match(r"^([A-Za-z_][A-Za-z0-9_\.]*)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?$", part)
                if m_alias is None:
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message=f"unsupported import clause: {part}",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `import module` or `import module as alias` form.",
                    )
                mod_name = re.group(m_alias, 1)
                as_name = re.group(m_alias, 2)
                bind_name = as_name if isinstance(as_name, str) and as_name != "" else mod_name.split(".")[0]
                _sh_append_import_binding(
                    import_bindings=import_bindings,
                    import_binding_names=import_binding_names,
                    module_id=mod_name,
                    export_name="",
                    local_name=bind_name,
                    binding_kind="module",
                    source_file=filename,
                    source_line=i,
                )
                aliases.append({"name": mod_name, "asname": as_name})
            body_items.append(
                {
                    "kind": "Import",
                    "source_span": _sh_span(i, 0, len(ln)),
                    "names": aliases,
                }
            )
            i = logical_end + 1
            continue
        if s.startswith("from "):
            marker = " import "
            pos = s.find(marker)
            if pos >= 0:
                mod_txt = s[5:pos].strip()
                if mod_txt.startswith("."):
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message="relative import is not supported",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use absolute import form: `from module import name`.",
                    )
        m_import_from: re.Match | None = re.match(r"^from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+import\s+(.+)$", s, flags=re.S)
        if m_import_from is not None:
            mod_name = re.strip_group(m_import_from, 1)
            names_txt = re.strip_group(m_import_from, 2)
            if names_txt == "*":
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message="from-import wildcard is not supported",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Import explicit symbol names instead of '*'.",
                )
            raw_parts = [p.strip() for p in names_txt.split(",") if p.strip() != ""]
            if len(raw_parts) == 0:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message="from-import statement has no symbol names",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Use `from module import name` form.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                m_alias: re.Match | None = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?$", part)
                if m_alias is None:
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message=f"unsupported from-import clause: {part}",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `from module import name` or `... as alias`.",
                    )
                sym_name = re.group(m_alias, 1)
                as_name = re.group(m_alias, 2)
                bind_name = as_name if isinstance(as_name, str) and as_name != "" else sym_name
                _sh_append_import_binding(
                    import_bindings=import_bindings,
                    import_binding_names=import_binding_names,
                    module_id=mod_name,
                    export_name=sym_name,
                    local_name=bind_name,
                    binding_kind="symbol",
                    source_file=filename,
                    source_line=i,
                )
                aliases.append({"name": sym_name, "asname": as_name})
            body_items.append(
                {
                    "kind": "ImportFrom",
                    "source_span": _sh_span(i, 0, len(ln)),
                    "module": mod_name,
                    "names": aliases,
                    "level": 0,
                }
            )
            i = logical_end + 1
            continue
        if s.startswith("@"):
            i += 1
            continue

        m_cls: re.Match | None = re.match(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\(([A-Za-z_][A-Za-z0-9_]*)\))?\s*:\s*$", ln)
        if m_cls is not None:
            cls_name = re.group(m_cls, 1)
            base = re.group(m_cls, 2)
            is_enum_base = base in {"Enum", "IntEnum", "IntFlag"}
            cls_indent = len(ln) - len(ln.lstrip(" "))
            block: list[tuple[int, str]] = []
            j = i + 1
            while j <= len(lines):
                bl = lines[j - 1]
                if bl.strip() == "":
                    block.append((j, bl))
                    j += 1
                    continue
                bind = len(bl) - len(bl.lstrip(" "))
                if bind <= cls_indent:
                    break
                block.append((j, bl))
                j += 1
            if len(block) == 0:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser requires non-empty class body '{cls_name}'",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Add field or method definitions.",
                )
            class_block, _class_line_end = _sh_merge_logical_lines(block)

            field_types: dict[str, str] = {}
            class_body: list[dict[str, Any]] = []
            pending_method_decorators: list[str] = []
            class_storage_hint_override = ""
            k = 0
            while k < len(class_block):
                ln_no, ln_txt = class_block[k]
                s2 = re.sub(r"\s+#.*$", "", ln_txt).strip()
                bind = len(ln_txt) - len(ln_txt.lstrip(" "))
                if s2 == "":
                    k += 1
                    continue
                if bind == cls_indent + 4 and s2.startswith("@"):
                    dec_name = s2[1:].strip()
                    if dec_name != "":
                        pending_method_decorators.append(dec_name)
                    k += 1
                    continue
                if bind == cls_indent + 4 and (s2.startswith('"""') or s2.startswith("'''")):
                    q = s2[:3]
                    if s2.count(q) >= 2 and len(s2) > 3:
                        k += 1
                        continue
                    k += 1
                    while k < len(class_block):
                        _doc_no, doc_txt = class_block[k]
                        if q in doc_txt:
                            k += 1
                            break
                        k += 1
                    continue
                if bind == cls_indent + 4:
                    if s2.startswith("__pytra_class_storage_hint__") or s2.startswith("__pytra_storage_hint__"):
                        parts = s2.split("=", 1)
                        if len(parts) == 2:
                            rhs = parts[1].strip()
                            if rhs in {'"value"', "'value'"}:
                                class_storage_hint_override = "value"
                                k += 1
                                continue
                            if rhs in {'"ref"', "'ref'"}:
                                class_storage_hint_override = "ref"
                                k += 1
                                continue
                    m_field: re.Match | None = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^=]+?)(?:\s*=\s*(.+))?$", s2)
                    if m_field is not None:
                        fname = re.group(m_field, 1)
                        fty = _sh_ann_to_type(re.group(m_field, 2))
                        field_types[fname] = fty
                        val_node = None
                        if re.group(m_field, 3) != "":
                            fexpr_txt = re.strip_group(m_field, 3)
                            fexpr_col = ln_txt.find(fexpr_txt)
                            val_node = parse_expr(fexpr_txt, ln_no=ln_no, col=fexpr_col, name_types={})
                        class_body.append(
                            {
                                "kind": "AnnAssign",
                                "source_span": _sh_span(ln_no, ln_txt.find(fname), len(ln_txt)),
                                "target": {
                                    "kind": "Name",
                                    "source_span": _sh_span(ln_no, ln_txt.find(fname), ln_txt.find(fname) + len(fname)),
                                    "resolved_type": fty,
                                    "borrow_kind": "value",
                                    "casts": [],
                                    "repr": fname,
                                    "id": fname,
                                },
                                "annotation": fty,
                                "value": val_node,
                                "declare": True,
                                "decl_type": fty,
                            }
                        )
                        k += 1
                        continue
                    if is_enum_base:
                        m_enum_assign: re.Match | None = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", s2)
                        if m_enum_assign is not None:
                            fname = re.group(m_enum_assign, 1)
                            fexpr_txt = re.strip_group(m_enum_assign, 2)
                            name_col = ln_txt.find(fname)
                            expr_col = ln_txt.find(fexpr_txt, name_col + len(fname))
                            val_node = parse_expr(fexpr_txt, ln_no=ln_no, col=expr_col, name_types={})
                            class_body.append(
                                {
                                    "kind": "Assign",
                                    "source_span": _sh_span(ln_no, name_col, len(ln_txt)),
                                    "target": {
                                        "kind": "Name",
                                        "source_span": _sh_span(ln_no, name_col, name_col + len(fname)),
                                        "resolved_type": str(val_node.get("resolved_type", "unknown")),
                                        "borrow_kind": "value",
                                        "casts": [],
                                        "repr": fname,
                                        "id": fname,
                                    },
                                    "value": val_node,
                                    "declare": True,
                                    "declare_init": True,
                                    "decl_type": str(val_node.get("resolved_type", "unknown")),
                                }
                            )
                            k += 1
                            continue
                    sig = _sh_parse_def_sig(ln_no, ln_txt, in_class=cls_name)
                    if sig is not None:
                        mname = str(sig["name"])
                        marg_types = dict(sig["arg_types"])
                        marg_order = list(sig.get("arg_order", list(marg_types.keys())))
                        marg_defaults_raw_obj = sig.get("arg_defaults")
                        marg_defaults_raw = marg_defaults_raw_obj if isinstance(marg_defaults_raw_obj, dict) else {}
                        mret = str(sig["ret"])
                        method_block: list[tuple[int, str]] = []
                        m = k + 1
                        while m < len(class_block):
                            n_no, n_txt = class_block[m]
                            if n_txt.strip() == "":
                                t = m + 1
                                while t < len(class_block) and class_block[t][1].strip() == "":
                                    t += 1
                                if t >= len(class_block):
                                    break
                                t_txt = class_block[t][1]
                                t_indent = len(t_txt) - len(t_txt.lstrip(" "))
                                if t_indent <= bind:
                                    break
                                method_block.append((n_no, n_txt))
                                m += 1
                                continue
                            n_indent = len(n_txt) - len(n_txt.lstrip(" "))
                            if n_indent <= bind:
                                break
                            method_block.append((n_no, n_txt))
                            m += 1
                        if len(method_block) == 0:
                            raise EastBuildError(
                                kind="unsupported_syntax",
                                message=f"self_hosted parser requires non-empty method body '{cls_name}.{mname}'",
                                source_span=_sh_span(ln_no, 0, len(ln_txt)),
                                hint="Add method statements.",
                            )
                        local_types = dict(marg_types)
                        for fnm, fty in field_types.items():
                            local_types[fnm] = fty
                        stmts = parse_stmt_block(method_block, name_types=local_types, scope_label=f"{cls_name}.{mname}")
                        docstring, stmts = _sh_extract_leading_docstring(stmts)
                        marg_defaults: dict[str, Any] = {}
                        for arg_name in marg_order:
                            if arg_name in marg_defaults_raw:
                                default_txt = str(marg_defaults_raw[arg_name]).strip()
                                if default_txt != "":
                                    default_col = ln_txt.find(default_txt)
                                    if default_col < 0:
                                        default_col = bind
                                    marg_defaults[arg_name] = parse_expr(
                                        default_txt,
                                        ln_no=ln_no,
                                        col=default_col,
                                        name_types=local_types,
                                    )
                        if mname == "__init__":
                            for st in stmts:
                                if st.get("kind") == "Assign":
                                    tgt = st.get("target")
                                    tgt_value = tgt.get("value") if isinstance(tgt, dict) else None
                                    if (
                                        isinstance(tgt, dict)
                                        and tgt.get("kind") == "Attribute"
                                        and isinstance(tgt_value, dict)
                                        and tgt_value.get("kind") == "Name"
                                        and tgt_value.get("id") == "self"
                                    ):
                                        fname = str(tgt.get("attr", ""))
                                        if fname != "":
                                            st_value = st.get("value")
                                            st_value_rt = st_value.get("resolved_type") if isinstance(st_value, dict) else None
                                            t = st.get("decl_type") or st_value_rt
                                            if isinstance(t, str) and t != "":
                                                field_types[fname] = t
                                if st.get("kind") == "AnnAssign":
                                    tgt = st.get("target")
                                    tgt_value = tgt.get("value") if isinstance(tgt, dict) else None
                                    if (
                                        isinstance(tgt, dict)
                                        and tgt.get("kind") == "Attribute"
                                        and isinstance(tgt_value, dict)
                                        and tgt_value.get("kind") == "Name"
                                        and tgt_value.get("id") == "self"
                                    ):
                                        fname = str(tgt.get("attr", ""))
                                        ann = st.get("annotation")
                                        if fname != "" and isinstance(ann, str) and ann != "":
                                            field_types[fname] = ann
                        arg_index_map: dict[str, int] = {}
                        arg_pos = 0
                        while arg_pos < len(marg_order):
                            arg_name = marg_order[arg_pos]
                            arg_index_map[arg_name] = arg_pos
                            arg_pos += 1
                        arg_usage_map: dict[str, str] = {}
                        for arg_name in marg_types.keys():
                            arg_usage_map[arg_name] = "readonly"
                        class_body.append(
                            {
                                "kind": "FunctionDef",
                                "name": mname,
                                "original_name": mname,
                                "source_span": {
                                    "lineno": ln_no,
                                    "col": bind,
                                    "end_lineno": method_block[-1][0],
                                    "end_col": len(method_block[-1][1]),
                                },
                                "arg_types": marg_types,
                                "arg_order": marg_order,
                                "arg_defaults": marg_defaults,
                                "arg_index": arg_index_map,
                                "return_type": mret,
                                "arg_usage": arg_usage_map,
                                "renamed_symbols": {},
                                "decorators": list(pending_method_decorators),
                                "docstring": docstring,
                                "body": stmts,
                            }
                        )
                        pending_method_decorators = []
                        k = m
                        continue
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse class statement: {s2}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use field annotation or method definitions in class body.",
                )

            storage_hint_override = class_storage_hint_override

            cls_item = {
                "kind": "ClassDef",
                "name": cls_name,
                "original_name": cls_name,
                "source_span": {"lineno": i, "col": 0, "end_lineno": block[-1][0], "end_col": len(block[-1][1])},
                "base": base,
                "dataclass": pending_dataclass,
                "field_types": field_types,
                "body": class_body,
            }
            static_field_names: set[str] = set()
            if not pending_dataclass:
                for st in class_body:
                    if st.get("kind") == "AnnAssign":
                        tgt = st.get("target")
                        if isinstance(tgt, dict) and tgt.get("kind") == "Name":
                            fname = str(tgt.get("id", ""))
                            if fname != "":
                                static_field_names.add(fname)
            has_del = any(
                isinstance(st, dict) and st.get("kind") == "FunctionDef" and st.get("name") == "__del__"
                for st in class_body
            )
            instance_field_names = {k for k in field_types.keys() if k not in static_field_names}
            # conservative hint:
            # - classes with instance state / __del__ / inheritance should keep reference semantics
            # - stateless, non-inherited classes can be value candidates
            if storage_hint_override != "":
                cls_item["class_storage_hint"] = storage_hint_override
            elif base in {"Enum", "IntEnum", "IntFlag"}:
                cls_item["class_storage_hint"] = "value"
            elif len(instance_field_names) == 0 and not has_del and not isinstance(base, str):
                cls_item["class_storage_hint"] = "value"
            else:
                cls_item["class_storage_hint"] = "ref"
            pending_dataclass = False
            if not first_item_attached:
                cls_item["leading_comments"] = list(leading_file_comments)
                cls_item["leading_trivia"] = list(leading_file_trivia)
                first_item_attached = True
            body_items.append(cls_item)
            i = j
            continue

        m_ann_top: re.Match | None = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^=]+?)\s*=\s*(.+)$", s, flags=re.S)
        if m_ann_top is not None:
            name = re.group(m_ann_top, 1)
            ann = _sh_ann_to_type(re.group(m_ann_top, 2))
            expr_txt = re.strip_group(m_ann_top, 3)
            expr_col = ln.find(expr_txt)
            body_items.append(
                {
                    "kind": "AnnAssign",
                    "source_span": _sh_span(i, ln.find(name), len(ln)),
                    "target": {
                        "kind": "Name",
                        "source_span": _sh_span(i, ln.find(name), ln.find(name) + len(name)),
                        "resolved_type": ann,
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": name,
                        "id": name,
                    },
                    "annotation": ann,
                    "value": parse_expr(expr_txt, ln_no=i, col=expr_col, name_types={}),
                    "declare": True,
                    "decl_type": ann,
                }
            )
            i = logical_end + 1
            continue

        asg_top: re.Match | None = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", s, flags=re.S)
        if asg_top is not None:
            name = re.group(asg_top, 1)
            expr_txt = re.strip_group(asg_top, 2)
            expr_col = ln.find(expr_txt)
            if expr_col < 0:
                expr_col = 0
            val_node = parse_expr(expr_txt, ln_no=i, col=expr_col, name_types={})
            decl_type = str(val_node.get("resolved_type", "unknown"))
            body_items.append(
                {
                    "kind": "Assign",
                    "source_span": _sh_span(i, ln.find(name), len(ln)),
                    "target": {
                        "kind": "Name",
                        "source_span": _sh_span(i, ln.find(name), ln.find(name) + len(name)),
                        "resolved_type": decl_type,
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": name,
                        "id": name,
                    },
                    "value": val_node,
                    "declare": True,
                    "declare_init": True,
                    "decl_type": decl_type,
                }
            )
            i = logical_end + 1
            continue

        if (s.startswith('"""') and s.endswith('"""')) or (s.startswith("'''") and s.endswith("'''")):
            # Module-level docstring / standalone string expression.
            body_items.append(
                {
                    "kind": "Expr",
                    "source_span": _sh_span(i, 0, len(ln)),
                    "value": parse_expr(s, ln_no=i, col=0, name_types={}),
                }
            )
            i = logical_end + 1
            continue

        raise EastBuildError(
            kind="unsupported_syntax",
            message=f"self_hosted parser cannot parse top-level statement: {s}",
            source_span=_sh_span(i, 0, len(ln)),
            hint="Use def/class/top-level typed assignment/main guard.",
        )

    renamed_symbols: dict[str, str] = {}
    for item in body_items:
        if item.get("kind") == "FunctionDef" and item.get("name") == "main":
            renamed_symbols["main"] = "__pytra_main"
            item["name"] = "__pytra_main"

    # 互換メタデータは ImportBinding 正本から導出する。
    import_module_bindings = {}
    import_symbol_bindings = {}
    qualified_symbol_refs: list[dict[str, str]] = []
    for binding in import_bindings:
        module_id_obj = binding.get("module_id")
        local_name_obj = binding.get("local_name")
        export_name_obj = binding.get("export_name")
        binding_kind_obj = binding.get("binding_kind")
        module_id = module_id_obj if isinstance(module_id_obj, str) else ""
        local_name = local_name_obj if isinstance(local_name_obj, str) else ""
        export_name = export_name_obj if isinstance(export_name_obj, str) else ""
        binding_kind = binding_kind_obj if isinstance(binding_kind_obj, str) else ""
        if module_id == "" or local_name == "":
            continue
        if binding_kind == "module":
            import_module_bindings[local_name] = module_id
            continue
        if binding_kind == "symbol" and export_name != "":
            import_symbol_bindings[local_name] = {"module": module_id, "name": export_name}
            qualified_symbol_refs.append(
                {
                    "module_id": module_id,
                    "symbol": export_name,
                    "local_name": local_name,
                }
            )

    return {
        "kind": "Module",
        "source_path": filename,
        "source_span": {"lineno": None, "col": None, "end_lineno": None, "end_col": None},
        "body": body_items,
        "main_guard_body": main_stmts,
        "renamed_symbols": renamed_symbols,
        "meta": {
            "parser_backend": "self_hosted",
            "import_bindings": import_bindings,
            "qualified_symbol_refs": qualified_symbol_refs,
            "import_modules": import_module_bindings,
            "import_symbols": import_symbol_bindings,
        },
    }


def convert_source_to_east_with_backend(source: str, filename: str, parser_backend: str = "self_hosted") -> dict[str, Any]:
    """指定バックエンドでソースを EAST へ変換する統一入口。"""
    if parser_backend != "self_hosted":
        raise EastBuildError(
            kind="unsupported_syntax",
            message=f"unknown parser backend: {parser_backend}",
            source_span={"lineno": None, "col": None, "end_lineno": None, "end_col": None},
            hint="Use parser_backend=self_hosted.",
        )
    return convert_source_to_east_self_hosted(source, filename)


def convert_path(input_path: Path, parser_backend: str = "self_hosted") -> dict[str, Any]:
    """Python ファイルを読み込み、EAST ドキュメントへ変換する。"""
    source = input_path.read_text(encoding="utf-8")
    return convert_source_to_east_with_backend(source, str(input_path), parser_backend=parser_backend)
