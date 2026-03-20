#!/usr/bin/env python3
"""Shared statement/header text helper semantics for self-hosted EAST parsing."""

from __future__ import annotations

from typing import Any

from toolchain.compile.core_text_semantics import _sh_is_identifier
from toolchain.compile.core_text_semantics import _sh_split_top_level_as


def _sh_split_def_header_and_inline_stmt(text: str) -> tuple[str, str]:
    """`def f(...): stmt` を `def ...:` と inline stmt に分割する。"""
    txt = text.strip()
    split = _sh_split_top_level_colon(txt)
    if split is None:
        return txt, ""
    head, tail = split
    inline_stmt = tail.strip()
    if not head.startswith("def ") or inline_stmt == "":
        return txt, ""
    return head + ":", inline_stmt


def _sh_scan_logical_line_state(
    txt: str,
    depth: int,
    mode: str,
) -> tuple[int, str]:
    """論理行マージ用に括弧深度と文字列モードを更新する。"""
    mode_cur = mode
    skip = 0
    for i, ch in enumerate(txt):
        if skip > 0:
            skip -= 1
            continue
        if mode_cur in {"'''", '"""'}:
            close = txt.find(mode_cur, i)
            if close < 0:
                break
            skip = close + 3 - i - 1
            mode_cur = ""
            continue
        if mode_cur in {"'", '"'}:
            if ch == "\\":
                skip = 1
                continue
            if ch == mode_cur:
                mode_cur = ""
            continue
        if i + 2 < len(txt) and txt[i : i + 3] in {"'''", '"""'}:
            mode_cur = txt[i : i + 3]
            skip = 2
            continue
        if ch in {"'", '"'}:
            mode_cur = ch
            continue
        if ch == "#":
            break
        if ch in {"(", "[", "{"}:
            depth += 1
        elif ch in {")", "]", "}"}:
            depth -= 1
    return depth, mode_cur


def _sh_has_explicit_line_continuation(txt: str) -> bool:
    """行末 `\\` による明示継続かを返す（文字列/コメント外のみ）。"""
    body = _sh_strip_inline_comment(txt).rstrip()
    if body == "":
        return False
    backslashes = 0
    for i in range(len(body) - 1, -1, -1):
        if body[i] == "\\":
            backslashes += 1
        else:
            break
    return (backslashes % 2) == 1


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
        explicit_cont = _sh_has_explicit_line_continuation(start_txt)
        end_no = start_no
        end_txt = start_txt
        while (depth > 0 or mode in {"'''", '"""'} or explicit_cont) and idx + 1 < len(raw_lines):
            idx += 1
            next_no, next_txt = raw_lines[idx]
            if mode in {"'''", '"""'}:
                acc += "\n" + next_txt
            else:
                # Merge continuation lines after stripping per-line inline comments.
                # (Stripping only after full merge loses code that appears after
                # comment-bearing continuation lines.)
                left_txt = _sh_strip_inline_comment(acc).rstrip()
                if explicit_cont:
                    bs_count = 0
                    j = len(left_txt) - 1
                    while j >= 0 and left_txt[j] == "\\":
                        bs_count += 1
                        j -= 1
                    if (bs_count % 2) == 1:
                        left_txt = left_txt[:-1].rstrip()
                right_txt = _sh_strip_inline_comment(next_txt).strip()
                acc = left_txt + " " + right_txt
            depth, mode = _sh_scan_logical_line_state(next_txt, depth, mode)
            explicit_cont = _sh_has_explicit_line_continuation(next_txt)
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


def _sh_find_top_char(text: str, needle: str) -> int:
    """文字列/括弧深度を考慮してトップレベルの1文字を探す（未検出なら -1）。"""
    depth = 0
    in_str: str | None = None
    esc = False
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
        if ch == needle and depth == 0:
            return i
    return -1


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
    for idx, e in enumerate(elem_nodes):
        if isinstance(e, dict) and e.get("kind") == "Name":
            nm = str(e.get("id", ""))
            if nm != "":
                if idx < len(elem_types):
                    et = elem_types[idx].strip()
                    if et == "":
                        et = "unknown"
                    out[nm] = et
                else:
                    out[nm] = "unknown"
    return out


def _sh_split_top_level_assign(text: str) -> tuple[str, str] | None:
    """トップレベルの `=` を 1 つだけ持つ代入式を分割する。"""
    depth = 0
    in_str = ""
    in_str_len = 0
    esc = False
    skip = 0
    for i, ch in enumerate(text):
        if skip > 0:
            skip -= 1
            continue
        if in_str != "":
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                if in_str_len == 3 and i + 2 < len(text) and text[i : i + 3] == (in_str + in_str + in_str):
                    skip = 2
                else:
                    in_str = ""
                    in_str_len = 0
            continue
        if i + 2 < len(text) and text[i : i + 3] in {"'''", '"""'}:
            in_str = text[i]
            in_str_len = 3
            skip = 2
            continue
        if ch in {"'", '"'}:
            in_str = ch
            in_str_len = 1
            continue
        if ch == "#":
            break
        if ch in {"(", "[", "{"}:
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
        if ch == "=" and depth == 0:
            prev = text[i - 1] if i - 1 >= 0 else ""
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if prev in {"!", "<", ">", "="} or nxt == "=":
                continue
            lhs = text[:i].strip()
            rhs = text[i + 1 :].strip()
            if lhs != "" and rhs != "":
                return lhs, rhs
            return None
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


def _sh_raise_if_trailing_stmt_terminator(
    text: str,
    *,
    line_no: int,
    line_text: str,
    make_east_build_error: Any,
    make_span: Any,
) -> None:
    """文末 `;` を検出したらエラーにする。"""
    out = text.rstrip()
    if out.endswith(";"):
        raise make_east_build_error(
            kind="input_invalid",
            message="self_hosted parser does not accept statement terminator ';'",
            source_span=make_span(line_no, 0, len(line_text)),
            hint="Remove trailing ';' from the statement.",
        )


def _sh_split_top_level_from(text: str) -> tuple[str, str] | None:
    """トップレベルの `for ... from ...` を lhs/rhs に分解する。"""
    depth = 0
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
        if ch in {"(", "[", "{"}:
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
        if depth == 0 and text[i:].startswith(" from "):
            lhs = text[:i].strip()
            rhs = text[i + 6 :].strip()
            if lhs != "" and rhs != "":
                return lhs, rhs
            return None
    return None


def _sh_split_top_level_in(text: str) -> tuple[str, str] | None:
    """トップレベルの `target in iter` を target/iter に分割する。"""
    depth = 0
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
        if ch in {"(", "[", "{"}:
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
        if depth == 0 and text[i:].startswith(" in "):
            lhs = text[:i].strip()
            rhs = text[i + 4 :].strip()
            if lhs != "" and rhs != "":
                return lhs, rhs
            return None
    return None


def _sh_split_top_level_colon(text: str) -> tuple[str, str] | None:
    """トップレベルの `head: tail` を 1 箇所分割する。"""
    depth = 0
    in_str: str | None = None
    esc = False
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
        if ch == ":" and depth == 0:
            lhs = text[:i].strip()
            rhs = text[i + 1 :].strip()
            if lhs != "" and rhs != "":
                return lhs, rhs
            return None
    return None


def _sh_parse_except_clause(header_text: str) -> tuple[str, str | None] | None:
    """`except <Type> [as <name>]:` を手書きパースする。"""
    raw = header_text.strip()
    if not raw.startswith("except") or not raw.endswith(":"):
        return None
    inner = raw[len("except") : -1].strip()
    if inner == "":
        return "Exception", None
    as_split = _sh_split_top_level_as(inner)
    if as_split is None:
        return inner, None
    ex_type_txt, ex_name_txt = as_split
    if ex_type_txt.strip() == "":
        return None
    if not _sh_is_identifier(ex_name_txt.strip()):
        return None
    return ex_type_txt.strip(), ex_name_txt.strip()


def _sh_parse_class_header_base_list(
    ln: str,
    *,
    split_top_commas: Any,
) -> tuple[str, list[str]] | None:
    """`class Name(...):` から class 名と基底リスト（0..n）を抽出する。"""
    s = ln.strip()
    if not s.startswith("class ") or not s.endswith(":"):
        return None
    head = s[len("class ") : -1].strip()
    if head == "":
        return None
    lp = head.find("(")
    if lp < 0:
        if not _sh_is_identifier(head):
            return None
        return head, []
    rp = head.rfind(")")
    if rp < 0 or rp < lp:
        return None
    if head[rp + 1 :].strip() != "":
        return None
    cls_name = head[:lp].strip()
    if not _sh_is_identifier(cls_name):
        return None
    base_expr = head[lp + 1 : rp].strip()
    bases = split_top_commas(base_expr)
    return cls_name, bases


def _sh_parse_class_header(
    ln: str,
    *,
    split_top_commas: Any,
) -> tuple[str, str] | None:
    """`class Name:` / `class Name(Base):` を簡易解析する。"""
    parsed = _sh_parse_class_header_base_list(ln, split_top_commas=split_top_commas)
    if parsed is None:
        return None
    cls_name, bases = parsed
    if len(bases) == 0:
        return cls_name, ""
    # Use the first base as the primary base (for single-inheritance compatibility).
    # Multiple bases are handled by mixin expansion at a later stage.
    base_name = bases[0]
    if not _sh_is_identifier(base_name):
        return None
    return cls_name, base_name


def _sh_collect_indented_block(
    body_lines: list[tuple[int, str]],
    start: int,
    parent_indent: int,
) -> tuple[list[tuple[int, str]], int]:
    """指定インデント配下のブロック行を収集する。"""
    out: list[tuple[int, str]] = []

    depth = 0
    mode = ""
    if 0 <= start - 1 < len(body_lines):
        prev_txt = body_lines[start - 1][1]
        depth, mode = _sh_scan_logical_line_state(prev_txt, 0, "")

    j = start
    while j < len(body_lines):
        n_no, n_ln = body_lines[j]
        if n_ln.strip() == "":
            if mode in {"'''", '"""'} or depth > 0:
                out.append((n_no, n_ln))
                depth, mode = _sh_scan_logical_line_state(n_ln, depth, mode)
                j += 1
                continue
            t = j + 1
            while t < len(body_lines) and body_lines[t][1].strip() == "":
                t += 1
            if t >= len(body_lines):
                break
            t_ln = body_lines[t][1]
            t_indent = len(t_ln) - len(t_ln.lstrip(" "))
            if t_indent <= parent_indent:
                # Blank lines right before dedent/elif/else should not pin j on
                # the blank line; advance to the next logical statement.
                j = t
                break
            out.append((n_no, n_ln))
            j += 1
            continue
        n_indent = len(n_ln) - len(n_ln.lstrip(" "))
        if n_indent <= parent_indent and not (mode in {"'''", '"""'} or depth > 0):
            break
        out.append((n_no, n_ln))
        depth, mode = _sh_scan_logical_line_state(n_ln, depth, mode)
        j += 1
    return out, j
