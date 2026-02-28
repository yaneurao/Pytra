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
from pytra.compiler.stdlib.signature_registry import lookup_stdlib_attribute_type
from pytra.compiler.stdlib.signature_registry import lookup_stdlib_function_return_type
from pytra.compiler.stdlib.signature_registry import lookup_stdlib_function_runtime_call
from pytra.compiler.stdlib.signature_registry import lookup_stdlib_method_runtime_call


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
_SH_STR_PREFIX_CHARS = {"r", "R", "b", "B", "u", "U", "f", "F"}

# `_sh_parse_expr_lowered` が参照する self-hosted 解析コンテキスト。
_SH_FN_RETURNS: dict[str, str] = {}
_SH_CLASS_METHOD_RETURNS: dict[str, dict[str, str]] = {}
_SH_CLASS_BASE: dict[str, str | None] = {}
_SH_TYPE_ALIASES: dict[str, str] = {
    "List": "list",
    "Dict": "dict",
    "Tuple": "tuple",
    "Set": "set",
}
_SH_EMPTY_SPAN: dict[str, Any] = {}


def _sh_default_type_aliases() -> dict[str, str]:
    """型解決用の初期別名テーブルを作成する。"""
    return {
        "List": "list",
        "Dict": "dict",
        "Tuple": "tuple",
        "Set": "set",
        "Any": "Any",
        "None": "None",
        "str": "str",
        "int": "int64",
        "float": "float64",
        "bool": "bool",
    }


def _sh_set_parse_context(
    fn_returns: dict[str, str],
    class_method_returns: dict[str, dict[str, str]],
    class_base: dict[str, str | None],
    type_aliases: dict[str, str] | None = None,
) -> None:
    """式解析で使う関数戻り値/クラス情報のコンテキストを更新する。"""
    _SH_FN_RETURNS.clear()
    _SH_FN_RETURNS.update(fn_returns)
    _SH_CLASS_METHOD_RETURNS.clear()
    _SH_CLASS_METHOD_RETURNS.update(class_method_returns)
    _SH_CLASS_BASE.clear()
    _SH_CLASS_BASE.update(class_base)
    _SH_TYPE_ALIASES.clear()
    if type_aliases is None:
        _SH_TYPE_ALIASES.update(_sh_default_type_aliases())
    else:
        _SH_TYPE_ALIASES.update(type_aliases)


def _sh_is_type_expr_text(txt: str) -> bool:
    """型注釈として妥当そうな文字列かを軽量判定する。"""
    raw: str = txt.strip()
    if raw == "":
        return False
    for ch in raw:
        if ch.isspace():
            continue
        if ch.isalnum() or ch in {"[", "]", ",", "|", ":", ".", "_"}:
            continue
        return False
    return True


def _sh_typing_alias_to_type_name(sym: str) -> str:
    """`from typing` で import される代表的シンボルを EAST 型名へ正規化する。"""
    key = sym.strip()
    mapping = {
        "List": "list",
        "Dict": "dict",
        "Tuple": "tuple",
        "Set": "set",
        "Any": "Any",
        "None": "None",
        "bool": "bool",
        "float": "float64",
        "int": "int64",
        "str": "str",
        "bytes": "bytes",
        "bytearray": "bytearray",
    }
    return mapping.get(key, "")


def _sh_register_type_alias(type_aliases: dict[str, str], alias_name: str, rhs_txt: str) -> None:
    """型っぽい代入式からトップレベルの型エイリアス定義を登録する。"""
    name = alias_name.strip()
    rhs = rhs_txt.strip()
    if not _sh_is_identifier(name):
        return
    if rhs == "":
        return
    if not _sh_is_type_expr_text(rhs):
        return
    normalized = _sh_typing_alias_to_type_name(rhs)
    ann_type = _sh_ann_to_type(rhs, type_aliases=type_aliases)
    if normalized != "":
        type_aliases[name] = normalized
    elif ann_type == "Any":
        type_aliases[name] = ann_type
    elif ann_type != "unknown" and ann_type != rhs:
        type_aliases[name] = ann_type


class EastBuildError(Exception):
    kind: str
    message: str
    source_span: dict[str, Any]
    hint: str

    def __init__(
        self,
        kind: str,
        message: str,
        source_span: dict[str, Any],
        hint: str,
    ) -> None:
        self.kind = kind
        self.message = message
        self.source_span = dict(source_span)
        self.hint = hint

    def to_payload(self) -> dict[str, Any]:
        """例外情報を EAST エラー応答用 dict に整形する。"""
        out: dict[str, Any] = {}
        out["kind"] = self.kind
        out["message"] = self.message
        out["source_span"] = self.source_span
        out["hint"] = self.hint
        return out


def _make_east_build_error(kind: str, message: str, source_span: dict[str, Any], hint: str) -> RuntimeError:
    """self-hosted 生成で投げる例外を std::exception 互換（RuntimeError）に統一する。"""
    src_line = int(source_span.get("lineno", 0))
    src_col = int(source_span.get("col", 0))
    return RuntimeError(f"{kind}: {message} at {src_line}:{src_col} hint={hint}")


def convert_source_to_east(source: str, filename: str) -> dict[str, Any]:
    """後方互換用の入口。self-hosted パーサで EAST を生成する。"""
    return convert_source_to_east_self_hosted(source, filename)

def _sh_span(line: int, col: int, end_col: int) -> dict[str, int]:
    """self-hosted parser 用の source_span を生成する。"""
    return {"lineno": line, "col": col, "end_lineno": line, "end_col": end_col}


def _sh_ann_to_type(ann: str, *, type_aliases: dict[str, str] | None = None) -> str:
    """型注釈文字列を EAST 正規型へ変換する。"""
    aliases: dict[str, str] = type_aliases if type_aliases is not None else _SH_TYPE_ALIASES
    mapping = {
        "int": "int64",
        "float": "float64",
        "byte": "uint8",
        "bool": "bool",
        "str": "str",
        "None": "None",
        "bytes": "bytes",
        "bytearray": "bytearray",
        "Any": "Any",
    }
    txt: str = ann.strip()
    if len(txt) >= 2 and ((txt[0] == "'" and txt[-1] == "'") or (txt[0] == '"' and txt[-1] == '"')):
        txt = txt[1:-1].strip()
    if txt in mapping:
        return mapping[txt]
    if txt in aliases:
        return aliases[txt]
    lb = txt.find("[")
    if lb <= 0 or not txt.endswith("]"):
        return txt
    head: str = txt[:lb].strip()
    if head in aliases:
        head = aliases[head]
    if not _sh_is_identifier(head):
        return txt
    inner: str = txt[lb + 1 : -1].strip()
    if inner == "":
        return txt
    parts: list[str] = []
    depth = 0
    start = 0
    for i, ch in enumerate(inner):
        if ch == "[":
            depth += 1
        elif ch == "]":
            if depth > 0:
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
    for i, ch in enumerate(arg_text):
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
        if ch == "," and depth == 0:
            part = arg_text[start:i]
            out.append((part.strip(), start + (len(part) - len(part.lstrip()))))
            start = i + 1
    tail = arg_text[start:]
    if tail.strip() != "":
        out.append((tail.strip(), start + (len(tail) - len(tail.lstrip()))))
    return out


def _sh_parse_typed_binding(text: str, *, allow_dotted_name: bool = False) -> tuple[str, str, str] | None:
    """`name: Type` / `name: Type = expr` を手書きパースし、(name, type, default) を返す。"""
    raw = text.strip()
    if raw == "":
        return None
    colon = raw.find(":")
    if colon <= 0:
        return None
    name_txt = raw[:colon].strip()
    ann_txt = raw[colon + 1 :].strip()
    if ann_txt == "":
        return None
    if allow_dotted_name:
        name_parts = name_txt.split(".")
        if len(name_parts) == 0:
            return None
        norm_parts: list[str] = []
        for seg in name_parts:
            seg_norm = seg.strip()
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", seg_norm) is None:
                return None
            norm_parts.append(seg_norm)
        name_txt = ".".join(norm_parts)
    else:
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name_txt) is None:
            return None
    default_txt = ""
    split_ann = _sh_split_top_level_assign(ann_txt)
    if split_ann is not None:
        ann_lhs, ann_rhs = split_ann
        ann_txt = ann_lhs.strip()
        default_txt = ann_rhs.strip()
    if ann_txt == "":
        return None
    return name_txt, ann_txt, default_txt


def _sh_is_identifier(text: str) -> bool:
    """ASCII 識別子（先頭英字/`_`）かを返す。"""
    if text == "":
        return False
    c0 = text[0:1]
    is_head = ("A" <= c0 <= "Z") or ("a" <= c0 <= "z") or c0 == "_"
    if not is_head:
        return False
    for ch in text[1:]:
        is_body = ("A" <= ch <= "Z") or ("a" <= ch <= "z") or ("0" <= ch <= "9") or ch == "_"
        if not is_body:
            return False
    return True


def _sh_strip_utf8_bom(source: str) -> str:
    """UTF-8 BOM を先頭から除去する。"""
    if source.startswith("\ufeff"):
        return source[1:]
    return source


def _sh_is_dotted_identifier(text: str) -> bool:
    """`a.b.c` 形式の識別子列かを返す。"""
    if text.strip() == "":
        return False
    parts = text.split(".")
    if len(parts) == 0:
        return False
    for seg in parts:
        if not _sh_is_identifier(seg):
            return False
    return True


def _sh_parse_import_alias(text: str, *, allow_dotted_name: bool) -> tuple[str, str] | None:
    """`name` / `name as alias` を手書きパースして (name, alias_or_empty) を返す。"""
    raw = text.strip()
    if raw == "":
        return None
    name_txt = raw
    alias_txt = ""
    as_split = _sh_split_top_level_as(raw)
    if as_split is not None:
        name_txt, alias_txt = as_split
        name_txt = name_txt.strip()
        alias_txt = alias_txt.strip()
    if name_txt == "":
        return None
    if allow_dotted_name:
        if not _sh_is_dotted_identifier(name_txt):
            return None
    else:
        if not _sh_is_identifier(name_txt):
            return None
    if alias_txt != "" and not _sh_is_identifier(alias_txt):
        return None
    return name_txt, alias_txt


def _sh_parse_augassign(text: str) -> tuple[str, str, str] | None:
    """`target <op>= expr` をトップレベルで分解して返す。"""
    raw = text.strip()
    if raw == "":
        return None
    ops = ["<<=", ">>=", "//=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^="]
    depth = 0
    in_str: str | None = None
    esc = False
    for i, ch in enumerate(raw):
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
        if depth == 0:
            for op in ops:
                if raw[i : i + len(op)] == op:
                    left = raw[:i].strip()
                    right = raw[i + len(op) :].strip()
                    if left == "" or right == "":
                        return None
                    # allow Name / Attribute / Subscript lvalues, e.g. "a[i] += 1"
                    if left.count("=") > 0:
                        return None
                    return left, op, right
    return None


def _sh_scan_string_token(text: str, start: int, quote_pos: int, line_no: int, col_base: int) -> int:
    """文字列リテラルの終端位置を走査して返す。"""
    if quote_pos + 2 < len(text) and text[quote_pos : quote_pos + 3] in {"'''", '"""'}:
        q3 = text[quote_pos : quote_pos + 3]
        j = quote_pos + 3
        while j + 2 < len(text):
            if text[j : j + 3] == q3:
                return j + 3
            j += 1
        raise _make_east_build_error(
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
    raise _make_east_build_error(
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
    skip = 0
    for i, ch in enumerate(text):
        if skip > 0:
            skip -= 1
            continue
        if ch != "\\":
            out += ch
            continue
        if i + 1 >= len(text):
            out += "\\"
            break
        esc = text[i + 1 : i + 2]
        skip = 1
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
        elif esc == "x" and i + 2 < len(text):
            hex2 = text[i + 1 : i + 3]
            try:
                out += chr(int(hex2, 16))
                skip = 3
            except ValueError:
                out += "x"
        elif esc == "u" and i + 4 < len(text):
            hex4 = text[i + 1 : i + 5]
            try:
                out += chr(int(hex4, 16))
                skip = 4
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
    if not ln_norm.startswith("def ") or not ln_norm.endswith(":"):
        return None
    head = ln_norm[4:-1].strip()
    lp = head.find("(")
    rp = head.rfind(")")
    if lp <= 0 or rp < lp:
        return None
    fn_name = ""
    args_raw: str = ""
    ret_group: str = ""
    fn_name = head[:lp].strip()
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", fn_name) is None:
        return None
    args_raw = head[lp + 1 : rp]
    tail = head[rp + 1 :].strip()
    if tail == "":
        ret_group = ""
    elif tail.startswith("->"):
        ret_group = tail[2:].strip()
        if ret_group == "":
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message="self_hosted parser cannot parse return annotation in function signature",
                source_span=_sh_span(ln_no, 0, len(ln_norm)),
                hint="Use `def name(args) -> Type:` style signature.",
            )
    else:
        return None
    arg_types: dict[str, str] = {}
    arg_order: list[str] = []
    arg_defaults: dict[str, str] = {}
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
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="self_hosted parser cannot parse positional-only marker '/' in parameter list",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Remove '/' from signature for now.",
                )
            if p.startswith("**"):
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse variadic kwargs parameter: {p_txt}",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Use explicit parameters instead of **kwargs.",
                )
            if p.startswith("*"):
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse variadic args parameter: {p_txt}",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Use explicit parameters instead of *args.",
                )
            if in_class != "" and p == "self":
                arg_types["self"] = in_class
                arg_order.append("self")
                continue
            if ":" not in p:
                p_name = p
                p_default = ""
                p_assign = _sh_split_top_level_assign(p)
                if p_assign is not None:
                    p_name = p_assign[0].strip()
                    p_default = p_assign[1].strip()
                if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", p_name):
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse parameter name: {p_txt}",
                        source_span=_sh_span(ln_no, 0, len(ln_norm)),
                        hint="Use valid identifier for parameter name.",
                    )
                if in_class != "" and p_name == "self":
                    arg_types["self"] = in_class
                    arg_order.append("self")
                    if p_default != "":
                        arg_defaults["self"] = p_default
                    continue
                arg_types[p_name] = "unknown"
                arg_order.append(p_name)
                if p_default != "":
                    arg_defaults[p_name] = p_default
                continue
            parsed_param = _sh_parse_typed_binding(p, allow_dotted_name=False)
            if parsed_param is None:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse parameter: {p_txt}",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Use `name: Type` style parameters.",
                )
            pn, pt, pdef = parsed_param
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", pn):
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse parameter name: {pn}",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Use valid identifier for parameter name.",
                )
            if pt == "":
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse parameter type: {p_txt}",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Use `name: Type` style parameters.",
                )
            arg_types[pn] = _sh_ann_to_type(pt)
            arg_order.append(pn)
            if pdef != "":
                default_txt = pdef.strip()
                if default_txt != "":
                    arg_defaults[pn] = default_txt
    out_sig: dict[str, Any] = {}
    out_sig["name"] = fn_name
    out_sig["ret"] = _sh_ann_to_type(ret_group.strip()) if ret_group != "" else "None"
    out_sig["arg_types"] = arg_types
    out_sig["arg_order"] = arg_order
    out_sig["arg_defaults"] = arg_defaults
    return out_sig


def _sh_split_def_header_and_inline_stmt(text: str) -> tuple[str, str]:
    """`def ...:` と同一行本文（`def ...: stmt`）を分割する。"""
    txt = text.strip()
    if not txt.startswith("def "):
        return txt, ""
    if txt.endswith(":"):
        return txt, ""
    split = _sh_split_top_level_colon(txt)
    if split is None:
        return txt, ""
    head, inline_stmt = split
    head = head.strip()
    inline_stmt = inline_stmt.strip()
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


def _sh_split_top_keyword(text: str, kw: str) -> int:
    """トップレベルでキーワード出現位置を探す（未検出なら -1）。"""
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
        if depth == 0 and text[i:].startswith(kw):
            prev_ok = i == 0 or text[i - 1].isspace()
            next_ok = (i + len(kw) >= len(text)) or text[i + len(kw)].isspace()
            if prev_ok and next_ok:
                return i
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


def _sh_extract_adjacent_string_parts(
    text: str,
    line_no: int,
    col_base: int,
    name_types: dict[str, str],
) -> list[tuple[str, int]] | None:
    """トップレベルで `STR STR ...` のみで構成される式を、文字列トークン分割して返す。

    タプルを構成する `("a", "b")` のようなケースは除外し、括弧付きでも
    外側が1組の `()` で全体を包む形式に対応する。
    """
    parser = _ShExprParser(
        text,
        line_no,
        col_base,
        dict(name_types),
        _SH_FN_RETURNS,
        _SH_CLASS_METHOD_RETURNS,
        _SH_CLASS_BASE,
    )
    toks = parser._tokenize(text)
    if len(toks) <= 1:
        return None
    if toks[-1].get("k") != "EOF":
        return None
    end = len(toks) - 1
    start = 0
    if end > 1 and toks[0].get("k") == "(" and toks[end - 1].get("k") == ")":
        start = 1
        end -= 1
    inner = toks[start:end]
    if len(inner) == 0:
        return None
    for tok in inner:
        if tok.get("k") != "STR":
            return None
    if len(inner) < 2:
        return None
    return [(str(tok.get("v", "")), int(tok.get("s", 0)) + col_base) for tok in inner]


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
    end_pair: tuple[int, int] = merged_line_end.get(start_ln, (start_ln, fallback_end_col))
    end_ln: int = int(end_pair[0])
    end_col: int = int(end_pair[1])
    return {"lineno": start_ln, "col": start_col, "end_lineno": end_ln, "end_col": end_col}


def _sh_push_stmt_with_trivia(
    stmts: list[dict[str, Any]],
    pending_leading_trivia: list[dict[str, Any]],
    pending_blank_count: int,
    stmt: dict[str, Any],
) -> int:
    """保留中 trivia を付与して文リストへ追加し、更新後 blank 数を返す。"""
    stmt_copy: dict[str, Any] = dict(stmt)
    if pending_blank_count > 0:
        blank_item: dict[str, Any] = {}
        blank_item["kind"] = "blank"
        blank_item["count"] = pending_blank_count
        pending_leading_trivia.append(blank_item)
        pending_blank_count = 0
    if len(pending_leading_trivia) > 0:
        stmt_copy["leading_trivia"] = list(pending_leading_trivia)
        comments = [x.get("text") for x in pending_leading_trivia if x.get("kind") == "comment" and isinstance(x.get("text"), str)]
        if len(comments) > 0:
            stmt_copy["leading_comments"] = comments
        pending_leading_trivia.clear()
    stmts.append(stmt_copy)
    return pending_blank_count


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


def _sh_raise_if_trailing_stmt_terminator(text: str, *, line_no: int, line_text: str) -> None:
    """文末 `;` を検出したらエラーにする。"""
    out = text.rstrip()
    if out.endswith(";"):
        raise _make_east_build_error(
            kind="input_invalid",
            message="self_hosted parser does not accept statement terminator ';'",
            source_span=_sh_span(line_no, 0, len(line_text)),
            hint="Remove trailing ';' from the statement.",
        )


def _sh_split_top_level_from(text: str) -> tuple[str, str] | None:
    """トップレベルの `for ... in ...` を target/iter に分解する。"""
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


def _sh_split_top_level_as(text: str) -> tuple[str, str] | None:
    """トップレベルの `lhs as rhs` を分割する。"""
    pos = _sh_split_top_keyword(text, "as")
    if pos < 0:
        return None
    lhs = text[:pos].strip()
    rhs = text[pos + 2 :].strip()
    if lhs == "" or rhs == "":
        return None
    return lhs, rhs


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


def _sh_parse_class_header_base_list(ln: str) -> tuple[str, list[str]] | None:
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
    bases = _sh_split_top_commas(base_expr)
    return cls_name, bases


def _sh_parse_class_header(ln: str) -> tuple[str, str] | None:
    """`class Name:` / `class Name(Base):` を簡易解析する。"""
    parsed = _sh_parse_class_header_base_list(ln)
    if parsed is None:
        return None
    cls_name, bases = parsed
    if len(bases) == 0:
        return cls_name, ""
    if len(bases) != 1:
        return None
    base_name = bases[0]
    if not _sh_is_identifier(base_name):
        return None
    return cls_name, base_name


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
    idx = start_idx
    while idx < len(body_lines):
        t_no, t_ln = body_lines[idx]
        t_indent = len(t_ln) - len(t_ln.lstrip(" "))
        if t_indent != parent_indent:
            return [], idx
        t_s = _sh_strip_inline_comment(t_ln.strip())
        _sh_raise_if_trailing_stmt_terminator(t_s, line_no=t_no, line_text=t_ln)
        if t_s == "":
            idx += 1
            continue
        break
    if idx >= len(body_lines):
        return [], idx
    t_no, t_ln = body_lines[idx]
    t_indent = len(t_ln) - len(t_ln.lstrip(" "))
    t_s = _sh_strip_inline_comment(t_ln.strip())
    if t_indent != parent_indent:
        return [], idx
    if t_s == "else:":
        else_block, k2 = _sh_collect_indented_block(body_lines, idx + 1, parent_indent)
        if len(else_block) == 0:
            raise _make_east_build_error(
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
        elif_block, k2 = _sh_collect_indented_block(body_lines, idx + 1, parent_indent)
        if len(elif_block) == 0:
            raise _make_east_build_error(
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
        elif_items: list[dict[str, Any]] = []
        elif_item: dict[str, Any] = {
            "kind": "If",
            "source_span": _sh_block_end_span(body_lines, t_no, t_ln.find("elif "), len(t_ln), k3),
            "test": cond_expr2,
            "body": _sh_parse_stmt_block(elif_block, name_types=dict(name_types), scope_label=scope_label),
            "orelse": nested_orelse,
        }
        elif_items.append(elif_item)
        return elif_items, k3
    return [], idx


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


def _sh_collect_yield_value_types(stmts: list[dict[str, Any]]) -> list[str]:
    """文リストから yield 値型を再帰収集する（入れ子関数/クラスは除外）。"""
    out: list[str] = []
    for st in stmts:
        if not isinstance(st, dict):
            continue
        kind = str(st.get("kind", ""))
        if kind == "Yield":
            val = st.get("value")
            if isinstance(val, dict):
                t_val = val.get("resolved_type", "unknown")
                if isinstance(t_val, str) and t_val != "":
                    out.append(t_val)
                else:
                    out.append("unknown")
            else:
                out.append("None")
            continue
        if kind in {"FunctionDef", "ClassDef"}:
            continue
        if kind in {"If", "While", "For", "ForRange"}:
            body_obj: Any = st.get("body")
            body_list: list[dict[str, Any]] = body_obj if isinstance(body_obj, list) else []
            out.extend(_sh_collect_yield_value_types(body_list))
            orelse_obj: Any = st.get("orelse")
            orelse_list: list[dict[str, Any]] = orelse_obj if isinstance(orelse_obj, list) else []
            out.extend(_sh_collect_yield_value_types(orelse_list))
            continue
        if kind == "Try":
            body_obj = st.get("body")
            body_list = body_obj if isinstance(body_obj, list) else []
            out.extend(_sh_collect_yield_value_types(body_list))
            orelse_obj = st.get("orelse")
            orelse_list = orelse_obj if isinstance(orelse_obj, list) else []
            out.extend(_sh_collect_yield_value_types(orelse_list))
            final_obj = st.get("finalbody")
            final_list = final_obj if isinstance(final_obj, list) else []
            out.extend(_sh_collect_yield_value_types(final_list))
            handlers_obj: Any = st.get("handlers")
            handlers: list[dict[str, Any]] = handlers_obj if isinstance(handlers_obj, list) else []
            for h in handlers:
                if not isinstance(h, dict):
                    continue
                h_body_obj: Any = h.get("body")
                h_body: list[dict[str, Any]] = h_body_obj if isinstance(h_body_obj, list) else []
                out.extend(_sh_collect_yield_value_types(h_body))
    return out


def _sh_collect_return_value_types(stmts: list[dict[str, Any]]) -> list[str]:
    """文リストから `return <expr>` の戻り値型を再帰収集する（入れ子関数/クラスは除外）。"""
    out: list[str] = []
    for st in stmts:
        if not isinstance(st, dict):
            continue
        kind = str(st.get("kind", ""))
        if kind == "Return":
            val = st.get("value")
            if not isinstance(val, dict):
                continue
            t_val_obj: Any = val.get("resolved_type")
            t_val = str(t_val_obj) if isinstance(t_val_obj, str) else "unknown"
            out.append(t_val if t_val != "" else "unknown")
            continue
        if kind in {"FunctionDef", "ClassDef"}:
            continue
        if kind in {"If", "While", "For", "ForRange"}:
            body_obj: Any = st.get("body")
            body_list: list[dict[str, Any]] = body_obj if isinstance(body_obj, list) else []
            out.extend(_sh_collect_return_value_types(body_list))
            orelse_obj: Any = st.get("orelse")
            orelse_list: list[dict[str, Any]] = orelse_obj if isinstance(orelse_obj, list) else []
            out.extend(_sh_collect_return_value_types(orelse_list))
            continue
        if kind == "Try":
            body_obj = st.get("body")
            body_list = body_obj if isinstance(body_obj, list) else []
            out.extend(_sh_collect_return_value_types(body_list))
            orelse_obj = st.get("orelse")
            orelse_list = orelse_obj if isinstance(orelse_obj, list) else []
            out.extend(_sh_collect_return_value_types(orelse_list))
            final_obj = st.get("finalbody")
            final_list = final_obj if isinstance(final_obj, list) else []
            out.extend(_sh_collect_return_value_types(final_list))
            handlers_obj: Any = st.get("handlers")
            handlers: list[dict[str, Any]] = handlers_obj if isinstance(handlers_obj, list) else []
            for h in handlers:
                if not isinstance(h, dict):
                    continue
                h_body_obj: Any = h.get("body")
                h_body: list[dict[str, Any]] = h_body_obj if isinstance(h_body_obj, list) else []
                out.extend(_sh_collect_return_value_types(h_body))
    return out


def _sh_infer_return_type_for_untyped_def(declared_ret: str, stmts: list[dict[str, Any]]) -> str:
    """戻り注釈なし（`None`）関数に対し `return <expr>` から戻り型を推定する。"""
    if declared_ret != "None":
        return declared_ret
    ret_types = _sh_collect_return_value_types(stmts)
    if len(ret_types) == 0:
        return declared_ret
    picked = ""
    for rt in ret_types:
        t = rt if rt != "" else "unknown"
        if t == "None":
            continue
        if picked == "":
            picked = t
            continue
        if picked == t:
            continue
        if picked == "unknown" or t == "unknown":
            picked = "unknown"
            continue
        picked = "Any"
        break
    if picked == "":
        return declared_ret
    return picked


def _sh_collect_store_name_ids(target: Any, out: set[str]) -> None:
    """代入ターゲットから Name 識別子を再帰収集する。"""
    if isinstance(target, dict):
        kind = str(target.get("kind", ""))
        if kind == "Name":
            name = target.get("id")
            if isinstance(name, str) and name != "":
                out.add(name)
            return
        if kind == "Starred":
            _sh_collect_store_name_ids(target.get("value"), out)
            return
        if kind in {"Tuple", "List"}:
            elems_obj: Any = target.get("elements")
            elems: list[Any] = elems_obj if isinstance(elems_obj, list) else []
            for elem in elems:
                _sh_collect_store_name_ids(elem, out)
            return
        return
    if isinstance(target, list):
        for item in target:
            _sh_collect_store_name_ids(item, out)


def _sh_collect_reassigned_names(stmts: list[dict[str, Any]]) -> set[str]:
    """文リストから再代入（再束縛）されたローカル名を収集する。"""
    out: set[str] = set()
    for st in stmts:
        if not isinstance(st, dict):
            continue
        kind = str(st.get("kind", ""))
        if kind in {"FunctionDef", "ClassDef"}:
            # 入れ子スコープ内の代入は外側関数引数の再代入に含めない。
            continue
        if kind in {"Assign", "AnnAssign", "AugAssign"}:
            _sh_collect_store_name_ids(st.get("target"), out)
            continue
        if kind == "Swap":
            _sh_collect_store_name_ids(st.get("left"), out)
            _sh_collect_store_name_ids(st.get("right"), out)
            continue
        if kind in {"For", "ForRange"}:
            _sh_collect_store_name_ids(st.get("target"), out)
            body_obj: Any = st.get("body")
            body: list[dict[str, Any]] = body_obj if isinstance(body_obj, list) else []
            out.update(_sh_collect_reassigned_names(body))
            orelse_obj: Any = st.get("orelse")
            orelse: list[dict[str, Any]] = orelse_obj if isinstance(orelse_obj, list) else []
            out.update(_sh_collect_reassigned_names(orelse))
            continue
        if kind in {"If", "While"}:
            body_obj = st.get("body")
            body = body_obj if isinstance(body_obj, list) else []
            out.update(_sh_collect_reassigned_names(body))
            orelse_obj = st.get("orelse")
            orelse = orelse_obj if isinstance(orelse_obj, list) else []
            out.update(_sh_collect_reassigned_names(orelse))
            continue
        if kind == "Try":
            body_obj = st.get("body")
            body = body_obj if isinstance(body_obj, list) else []
            out.update(_sh_collect_reassigned_names(body))
            orelse_obj = st.get("orelse")
            orelse = orelse_obj if isinstance(orelse_obj, list) else []
            out.update(_sh_collect_reassigned_names(orelse))
            final_obj = st.get("finalbody")
            finalbody = final_obj if isinstance(final_obj, list) else []
            out.update(_sh_collect_reassigned_names(finalbody))
            handlers_obj: Any = st.get("handlers")
            handlers: list[dict[str, Any]] = handlers_obj if isinstance(handlers_obj, list) else []
            for handler in handlers:
                if not isinstance(handler, dict):
                    continue
                h_name = handler.get("name")
                if isinstance(h_name, str) and h_name != "":
                    out.add(h_name)
                h_body_obj: Any = handler.get("body")
                h_body: list[dict[str, Any]] = h_body_obj if isinstance(h_body_obj, list) else []
                out.update(_sh_collect_reassigned_names(h_body))
    return out


def _sh_build_arg_usage_map(
    arg_order: list[str],
    arg_types: dict[str, str],
    fn_stmts: list[dict[str, Any]],
) -> dict[str, str]:
    """関数本文の代入状況から `arg_usage` を構築する。"""
    usage: dict[str, str] = {}
    for arg_name in arg_types.keys():
        usage[arg_name] = "readonly"
    for arg_name in arg_order:
        usage[arg_name] = "readonly"

    reassigned = _sh_collect_reassigned_names(fn_stmts)
    for arg_name in arg_types.keys():
        if arg_name in reassigned:
            usage[arg_name] = "reassigned"
    for arg_name in arg_order:
        if arg_name in reassigned:
            usage[arg_name] = "reassigned"
    return usage


def _sh_make_generator_return_type(declared_ret: str, yield_types: list[str]) -> tuple[str, str]:
    """yield 検出時の関数戻り型（list[...]）と要素型を決定する。"""
    elem = "unknown"
    if declared_ret != "" and declared_ret != "None":
        elem = declared_ret
    for yt in yield_types:
        if yt in {"", "unknown", "None"}:
            continue
        if elem == "unknown":
            elem = yt
            continue
        if elem != yt:
            elem = "Any"
            break
    return "list[" + elem + "]", elem


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
        raise _make_east_build_error(
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
    src: str
    line_no: int
    col_base: int
    name_types: dict[str, str]
    fn_return_types: dict[str, str]
    class_method_return_types: dict[str, dict[str, str]]
    class_base: dict[str, str | None]
    tokens: list[dict[str, Any]]
    pos: int

    def __init__(
        self,
        text: str,
        line_no: int,
        col_base: int,
        name_types: dict[str, str],
        fn_return_types: dict[str, str],
        class_method_return_types: dict[str, dict[str, str]] = {},
        class_base: dict[str, str | None] = {},
    ) -> None:
        """式パースに必要な入力と型環境を初期化する。"""
        self.src = text
        self.line_no = line_no
        self.col_base = col_base
        self.name_types = name_types
        self.fn_return_types = fn_return_types
        self.class_method_return_types = class_method_return_types
        self.class_base = class_base
        self.tokens: list[dict[str, Any]] = self._tokenize(text)
        self.pos = 0

    def _tokenize(self, text: str) -> list[dict[str, Any]]:
        """式テキストを self-hosted 用トークン列へ変換する。"""
        out: list[dict[str, Any]] = []
        skip = 0
        text_len = len(text)
        for i, ch in enumerate(text):
            if skip > 0:
                skip -= 1
                continue
            if ch.isspace():
                continue
            # string literal prefixes: r"...", f"...", b"...", u"...", rf"...", fr"...", ...
            pref_len = 0
            if i + 1 < text_len:
                p1 = text[i]
                if p1 in _SH_STR_PREFIX_CHARS and text[i + 1] in {"'", '"'}:
                    pref_len = 1
                elif i + 2 < text_len:
                    p2 = text[i : i + 2]
                    if all(c in _SH_STR_PREFIX_CHARS for c in p2) and text[i + 2] in {"'", '"'}:
                        pref_len = 2
            if pref_len > 0:
                end = _sh_scan_string_token(text, i, i + pref_len, self.line_no, self.col_base)
                out.append({"k": "STR", "v": text[i:end], "s": i, "e": end})
                skip = end - i - 1
                continue
            if ch.isdigit():
                if ch == "0" and i + 2 < text_len and text[i + 1] in {"x", "X"}:
                    j = i + 2
                    while j < text_len and (text[j].isdigit() or text[j].lower() in {"a", "b", "c", "d", "e", "f"}):
                        j += 1
                    if j > i + 2:
                        out.append({"k": "INT", "v": text[i:j], "s": i, "e": j})
                        skip = j - i - 1
                        continue
                j = i + 1
                while j < text_len and text[j].isdigit():
                    j += 1
                has_float = False
                if j < text_len and text[j] == ".":
                    k = j + 1
                    while k < text_len and text[k].isdigit():
                        k += 1
                    if k > j + 1:
                        j = k
                        has_float = True
                if j < text_len and text[j] in {"e", "E"}:
                    k = j + 1
                    if k < text_len and text[k] in {"+", "-"}:
                        k += 1
                    d0 = k
                    while k < text_len and text[k].isdigit():
                        k += 1
                    if k > d0:
                        j = k
                        has_float = True
                if has_float:
                    out.append({"k": "FLOAT", "v": text[i:j], "s": i, "e": j})
                    skip = j - i - 1
                    continue
                out.append({"k": "INT", "v": text[i:j], "s": i, "e": j})
                skip = j - i - 1
                continue
            if ch.isalpha() or ch == "_":
                j = i + 1
                while j < text_len and (text[j].isalnum() or text[j] == "_"):
                    j += 1
                out.append({"k": "NAME", "v": text[i:j], "s": i, "e": j})
                skip = j - i - 1
                continue
            if i + 2 < text_len and text[i : i + 3] in {"'''", '"""'}:
                end = _sh_scan_string_token(text, i, i, self.line_no, self.col_base)
                out.append({"k": "STR", "v": text[i:end], "s": i, "e": end})
                skip = end - i - 1
                continue
            if ch in {"'", '"'}:
                end = _sh_scan_string_token(text, i, i, self.line_no, self.col_base)
                out.append({"k": "STR", "v": text[i:end], "s": i, "e": end})
                skip = end - i - 1
                continue
            if i + 1 < text_len and text[i : i + 2] in {"<=", ">=", "==", "!=", "//", "<<", ">>", "**"}:
                out.append({"k": text[i : i + 2], "v": text[i : i + 2], "s": i, "e": i + 2})
                skip = 1
                continue
            if ch in {"<", ">"}:
                out.append({"k": ch, "v": ch, "s": i, "e": i + 1})
                continue
            if ch in {"+", "-", "*", "/", "%", "&", "|", "^", "(", ")", ",", ".", "[", "]", ":", "=", "{", "}"}:
                out.append({"k": ch, "v": ch, "s": i, "e": i + 1})
                continue
            raise _make_east_build_error(
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
            raise _make_east_build_error(
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
        arg_entries: list[dict[str, Any]] = []
        seen_default = False
        while self._cur()["k"] != ":":
            if self._cur()["k"] == ",":
                self._eat(",")
                continue
            if self._cur()["k"] == "NAME":
                nm = str(self._eat("NAME")["v"])
                default_expr: dict[str, Any] | None = None
                if self._cur()["k"] == "=":
                    self._eat("=")
                    default_expr = self._parse_ifexp()
                    seen_default = True
                elif seen_default:
                    cur = self._cur()
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="lambda non-default parameter follows default parameter",
                        source_span=self._node_span(cur["s"], cur["e"]),
                        hint="Reorder lambda parameters so defaulted ones come last.",
                    )
                param_t = "unknown"
                if isinstance(default_expr, dict):
                    default_t = str(default_expr.get("resolved_type", "unknown"))
                    if default_t != "":
                        param_t = default_t
                arg_entries.append({"name": nm, "default": default_expr, "resolved_type": param_t})
                continue
            cur = self._cur()
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"unsupported lambda parameter token: {cur['k']}",
                source_span=self._node_span(cur["s"], cur["e"]),
                hint="Use `lambda x, y=default: expr` form (annotations are not supported).",
            )
        self._eat(":")
        bak: dict[str, str] = {}
        for ent in arg_entries:
            nm = str(ent.get("name", ""))
            if nm == "":
                continue
            bak[nm] = self.name_types.get(nm, "")
            param_t = str(ent.get("resolved_type", "unknown"))
            if param_t == "":
                param_t = "unknown"
            self.name_types[nm] = param_t
        body = self._parse_ifexp()
        for ent in arg_entries:
            nm = str(ent.get("name", ""))
            if nm == "":
                continue
            old = bak.get(nm, "")
            if old == "":
                self.name_types.pop(nm, None)
            else:
                self.name_types[nm] = old
        s = lam_tok["s"]
        e = int(body["source_span"]["end_col"]) - self.col_base
        body_t = str(body.get("resolved_type", "unknown"))
        ret_t = body_t if body_t != "" else "unknown"
        param_types: list[str] = []
        for ent in arg_entries:
            param_t = str(ent.get("resolved_type", "unknown"))
            if param_t == "":
                param_t = "unknown"
            param_types.append(param_t)
        params = ",".join(param_types)
        callable_t = f"callable[{params}->{ret_t}]"
        args: list[dict[str, Any]] = []
        for ent in arg_entries:
            nm = str(ent.get("name", ""))
            default_expr = ent.get("default")
            param_t = str(ent.get("resolved_type", "unknown"))
            if param_t == "":
                param_t = "unknown"
            arg_ent: dict[str, Any] = {
                "kind": "arg",
                "arg": nm,
                "annotation": None,
                "resolved_type": param_t,
            }
            if isinstance(default_expr, dict):
                arg_ent["default"] = default_expr
            args.append(arg_ent)
        return {
            "kind": "Lambda",
            "source_span": self._node_span(s, e),
            "resolved_type": callable_t,
            "borrow_kind": "value",
            "casts": [],
            "repr": self._src_slice(s, e),
            "args": args,
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
                raise _make_east_build_error(
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

    def _parse_power(self) -> dict[str, Any]:
        """べき乗（`**`）を右結合で解析する。"""
        node = self._parse_postfix()
        if self._cur()["k"] == "**":
            op_tok = self._eat("**")
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
        return self._parse_power()

    def _lookup_method_return(self, cls_name: str, method: str) -> str:
        """クラス継承を辿ってメソッド戻り型を解決する。"""
        cur: str = cls_name
        while True:
            methods: dict[str, str] = {}
            if cur in self.class_method_return_types:
                methods = self.class_method_return_types[cur]
            if method in methods:
                value_obj: Any = methods[method]
                if isinstance(value_obj, str):
                    return value_obj
                return str(value_obj)
            next_cur_obj: Any = None
            if cur in self.class_base:
                next_cur_obj = self.class_base[cur]
            if not isinstance(next_cur_obj, str):
                break
            cur = next_cur_obj
        return "unknown"

    def _lookup_builtin_method_return(self, cls_name: str, method: str) -> str:
        """既知の組み込み型メソッドの戻り型を補助的に解決する。"""
        methods: dict[str, str] = {}
        if cls_name == "str":
            methods = {
                "strip": "str",
                "lstrip": "str",
                "rstrip": "str",
                "upper": "str",
                "lower": "str",
                "capitalize": "str",
                "split": "list[str]",
                "splitlines": "list[str]",
            }
        return methods.get(method, "unknown")

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

    def _dict_stmt_list(self, raw: Any) -> list[dict[str, Any]]:
        """動的値から `list[dict]` を安全に取り出す。"""
        out: list[dict[str, Any]] = []
        if not isinstance(raw, list):
            return out
        for item in raw:
            if isinstance(item, dict):
                out.append(item)
        return out

    def _node_kind_from_dict(self, node_dict: dict[str, Any]) -> str:
        """dict 化されたノードから kind を安全に文字列取得する。"""
        if not isinstance(node_dict, dict):
            return ""
        kind = node_dict.get("kind")
        if isinstance(kind, str):
            return kind.strip()
        if kind is None:
            return ""
        txt = str(kind).strip()
        return txt if txt != "" else ""

    def _iter_item_type(self, iter_expr: dict[str, Any] | None) -> str:
        """for 反復対象の要素型を推論する。"""
        if not isinstance(iter_expr, dict):
            return "unknown"
        t = str(iter_expr.get("resolved_type", "unknown"))
        if t.startswith("List[") and t.endswith("]"):
            t = "list[" + t[5:-1] + "]"
        if t.startswith("Set[") and t.endswith("]"):
            t = "set[" + t[4:-1] + "]"
        if t.startswith("Dict[") and t.endswith("]"):
            t = "dict[" + t[5:-1] + "]"
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
                    raise _make_east_build_error(
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
                std_attr_t = lookup_stdlib_attribute_type(owner_t, attr_name)
                if std_attr_t != "":
                    attr_t = std_attr_t
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
                    elif fn_name == "zip":
                        zip_item_types: list[str] = []
                        for arg_node in args:
                            if isinstance(arg_node, dict):
                                zip_item_types.append(_sh_infer_item_type(arg_node))
                        call_ret = f"list[tuple[{','.join(zip_item_types)}]]"
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
                    owner_t = "unknown"
                    if isinstance(owner, dict):
                        owner_t = str(owner.get("resolved_type", "unknown"))
                        if owner_t == "" or owner_t == "unknown":
                            owner_t = self.name_types.get(str(owner.get("id", "")), owner_t)
                        if owner_t != "unknown":
                            call_ret = self._lookup_method_return(owner_t, attr)
                            if call_ret == "unknown":
                                call_ret = self._lookup_builtin_method_return(owner_t, attr)
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
                stdlib_fn_runtime_call = lookup_stdlib_function_runtime_call(fn_name) if fn_name != "" else ""
                if fn_name == "print":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "print"
                    payload["runtime_call"] = "py_print"
                elif fn_name == "len":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "len"
                    payload["runtime_call"] = "py_len"
                elif fn_name == "range":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "range"
                    payload["runtime_call"] = "py_range"
                elif fn_name == "zip":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "zip"
                    payload["runtime_call"] = "zip"
                elif fn_name == "str":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "str"
                    payload["runtime_call"] = "py_to_string"
                elif fn_name in {"int", "float", "bool"}:
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = fn_name
                    runtime_call = "static_cast"
                    if fn_name == "int" and len(args) == 2:
                        runtime_call = "py_to_int64_base"
                    if fn_name == "bool" and len(args) == 1:
                        arg0 = args[0]
                        if isinstance(arg0, dict):
                            arg0_t = str(arg0.get("resolved_type", "unknown"))
                            if self._is_forbidden_object_receiver_type(arg0_t):
                                runtime_call = "py_to_bool"
                    payload["runtime_call"] = runtime_call
                elif fn_name in {"min", "max"}:
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = fn_name
                    payload["runtime_call"] = "py_min" if fn_name == "min" else "py_max"
                elif stdlib_fn_runtime_call != "":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = fn_name
                    payload["runtime_call"] = stdlib_fn_runtime_call
                    sig_ret = lookup_stdlib_function_return_type(fn_name)
                    if sig_ret != "":
                        payload["resolved_type"] = sig_ret
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
                elif fn_name == "iter":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "iter"
                    payload["runtime_call"] = "py_iter_or_raise"
                elif fn_name == "next":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "next"
                    payload["runtime_call"] = "py_next_or_stop"
                elif fn_name == "reversed":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "reversed"
                    payload["runtime_call"] = "py_reversed"
                elif fn_name == "enumerate":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "enumerate"
                    payload["runtime_call"] = "py_enumerate"
                    elem_t = "unknown"
                    if len(args) >= 1 and isinstance(args[0], dict):
                        elem_t = self._iter_item_type(args[0])
                    payload["iterable_trait"] = "yes" if elem_t != "unknown" else "unknown"
                    payload["iter_protocol"] = "static_range"
                    payload["iter_element_type"] = elem_t
                    call_ret = f"list[tuple[int64, {elem_t}]]"
                    payload["resolved_type"] = call_ret
                elif fn_name == "any":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "any"
                    payload["runtime_call"] = "py_any"
                elif fn_name == "all":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "all"
                    payload["runtime_call"] = "py_all"
                elif fn_name == "ord":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "ord"
                    payload["runtime_call"] = "py_ord"
                elif fn_name == "chr":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "chr"
                    payload["runtime_call"] = "py_chr"
                elif fn_name in {"bytes", "bytearray"}:
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = fn_name
                    payload["runtime_call"] = "bytes_ctor" if fn_name == "bytes" else "bytearray_ctor"
                elif fn_name in {"list", "set", "dict"}:
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = fn_name
                    payload["runtime_call"] = fn_name + "_ctor"
                elif isinstance(node, dict) and node.get("kind") == "Attribute":
                    attr = str(node.get("attr", ""))
                    owner = node.get("value")
                    owner_t = str(owner.get("resolved_type", "unknown")) if isinstance(owner, dict) else "unknown"
                    rc = lookup_stdlib_method_runtime_call(owner_t, attr)
                    if rc != "":
                        payload["lowered_kind"] = "BuiltinCall"
                        payload["builtin_name"] = attr
                        payload["runtime_call"] = rc
                        payload["runtime_owner"] = owner
                node = payload
                continue
            if tok["k"] == "[":
                ltok = self._eat("[")
                if self._cur()["k"] == ":":
                    self._eat(":")
                    up = None
                    if self._cur()["k"] != "]":
                        up = self._parse_ifexp()
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
                first = self._parse_ifexp()
                if self._cur()["k"] == ":":
                    self._eat(":")
                    up = None
                    if self._cur()["k"] != "]":
                        up = self._parse_ifexp()
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
            first = self._eat("NAME")
            first_name = str(first["v"])
            first_t = self.name_types.get(first_name, "unknown")
            first_node = {
                "kind": "Name",
                "source_span": self._node_span(first["s"], first["e"]),
                "resolved_type": first_t,
                "borrow_kind": "value",
                "casts": [],
                "repr": first_name,
                "id": first_name,
            }
            if self._cur()["k"] != ",":
                return first_node
            elems: list[dict[str, Any]] = [first_node]
            last_e = first["e"]
            while self._cur()["k"] == ",":
                self._eat(",")
                if self._cur()["k"] != "NAME":
                    break
                nm_tok = self._eat("NAME")
                nm = str(nm_tok["v"])
                t = self.name_types.get(nm, "unknown")
                elems.append(
                    {
                        "kind": "Name",
                        "source_span": self._node_span(nm_tok["s"], nm_tok["e"]),
                        "resolved_type": t,
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": nm,
                        "id": nm,
                    }
                )
                last_e = nm_tok["e"]
            elem_types = [str(e.get("resolved_type", "unknown")) for e in elems]
            return {
                "kind": "Tuple",
                "source_span": self._node_span(first["s"], last_e),
                "resolved_type": f"tuple[{','.join(elem_types)}]",
                "borrow_kind": "value",
                "casts": [],
                "repr": self._src_slice(first["s"], last_e),
                "elements": elems,
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
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message="invalid comprehension target in call argument",
            source_span=self._node_span(tok["s"], tok["e"]),
            hint="Use name or tuple target in generator expression.",
        )

    def _collect_and_bind_comp_target_types(
        self,
        target_expr: dict[str, Any],
        value_type: str,
        snapshots: dict[str, str],
    ) -> None:
        """内包ターゲットの各 Name へ一時的に型を設定する。"""
        kind = self._node_kind_from_dict(target_expr)
        if kind == "Name":
            nm = str(target_expr.get("id", "")).strip()
            if nm == "":
                return
            if nm not in snapshots:
                snapshots[nm] = str(self.name_types.get(nm, ""))
            target_expr["resolved_type"] = value_type
            self.name_types[nm] = value_type
            return

        if kind != "Tuple":
            return

        target_elements = self._dict_stmt_list(target_expr.get("elements"))
        elem_types: list[str] = []
        if isinstance(value_type, str) and value_type.startswith("tuple[") and value_type.endswith("]"):
            inner = value_type[6:-1].strip()
            if inner != "":
                elem_types = [p.strip() for p in _sh_split_top_commas(inner)]
        for idx, elem in enumerate(target_elements):
            if not isinstance(elem, dict):
                continue
            et = value_type
            if idx < len(elem_types):
                et0 = elem_types[idx]
                if et0 != "":
                    et = et0
            self._collect_and_bind_comp_target_types(elem, et, snapshots)

    def _restore_comp_target_types(self, snapshots: dict[str, str]) -> None:
        """内包ターゲット一時型束縛を復元する。"""
        for nm, old_t in snapshots.items():
            if old_t == "":
                self.name_types.pop(nm, None)
            else:
                self.name_types[nm] = old_t

    def _parse_call_arg_expr(self) -> dict[str, Any]:
        """呼び出し引数式を解析し、必要なら generator 引数へ lower する。"""
        first = self._parse_ifexp()
        if not (self._cur()["k"] == "NAME" and self._cur()["v"] == "for"):
            return first

        snapshots: dict[str, str] = {}
        generators: list[dict[str, Any]] = []
        first_norm = first
        end_node: Any = first

        def _reparse_expr(expr_node: dict[str, Any]) -> dict[str, Any]:
            expr_repr = expr_node.get("repr")
            if not isinstance(expr_repr, str) or expr_repr == "":
                return expr_node
            return _sh_parse_expr(
                expr_repr,
                line_no=self.line_no,
                col_base=int(expr_node.get("source_span", {}).get("col", self.col_base)),
                name_types=self.name_types,
                fn_return_types=self.fn_return_types,
                class_method_return_types=self.class_method_return_types,
                class_base=self.class_base,
            )

        while self._cur()["k"] == "NAME" and self._cur()["v"] == "for":
            self._eat("NAME")
            target = self._parse_comp_target()
            in_tok = self._eat("NAME")
            if in_tok["v"] != "in":
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="expected 'in' in generator expression",
                    source_span=self._node_span(in_tok["s"], in_tok["e"]),
                    hint="Use `for x in iterable` form.",
                )
            iter_expr = self._parse_or()
            if not isinstance(iter_expr, dict):
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="unsupported iterator expression in generator argument",
                    source_span=self._node_span(
                        int(iter_expr["source_span"]["col"]) if isinstance(iter_expr, dict) else self.col_base,
                        int(iter_expr["source_span"]["end_col"]) if isinstance(iter_expr, dict) else self.col_base + 1,
                    ),
                    hint="Use a resolvable iterable expression.",
                )

            conds: list[dict[str, Any]] = []
            while self._cur()["k"] == "NAME" and self._cur()["v"] == "if":
                self._eat("NAME")
                conds.append(self._parse_or())
            conds_norm: list[dict[str, Any]] = list(conds)

            tgt_ty = self._iter_item_type(iter_expr)
            if tgt_ty != "unknown":
                self._collect_and_bind_comp_target_types(target, tgt_ty, snapshots)
                if len(generators) == 0:
                    first_norm = _reparse_expr(first)
                conds_norm = [_reparse_expr(cond) if isinstance(cond, dict) else cond for cond in conds]

            if len(conds_norm) > 0:
                end_node = conds_norm[-1]
            else:
                end_node = iter_expr

            generators.append({"target": target, "iter": iter_expr, "ifs": conds_norm, "is_async": False})

        self._restore_comp_target_types(snapshots)
        s = int(first["source_span"]["col"]) - self.col_base
        if not isinstance(end_node, dict):
            return first
        e = int(end_node["source_span"]["end_col"]) - self.col_base
        return {
            "kind": "ListComp",
            "source_span": self._node_span(s, e),
            "resolved_type": f"list[{first_norm.get('resolved_type', 'unknown')}]",
            "borrow_kind": "value",
            "casts": [],
            "repr": self._src_slice(s, e),
            "elt": first_norm,
            "generators": generators,
            "lowered_kind": "GeneratorArg",
        }

    def _make_bin(self, left: dict[str, Any], op_sym: str, right: dict[str, Any]) -> dict[str, Any]:
        """二項演算ノードを構築し、数値昇格 cast も付与する。"""
        op_map = {
            "+": "Add",
            "-": "Sub",
            "*": "Mult",
            "**": "Pow",
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
            elif (lt in INT_TYPES or lt in FLOAT_TYPES) and (rt in INT_TYPES or rt in FLOAT_TYPES):
                out_t = "float64"
                if lt in INT_TYPES:
                    casts.append({"on": "left", "from": "int64", "to": "float64", "reason": "numeric_promotion"})
                if rt in INT_TYPES:
                    casts.append({"on": "right", "from": "int64", "to": "float64", "reason": "numeric_promotion"})
            else:
                # object/unknown を数値に固定化しない。
                out_t = "unknown"
        elif op_sym == "//":
            out_t = "int64" if lt in {"int64", "unknown"} and rt in {"int64", "unknown"} else "float64"
        elif op_sym == "+" and (
            (lt in {"bytes", "bytearray"} and rt in {"bytes", "bytearray"})
            or (lt == "str" and rt == "str")
        ):
            out_t = "bytes" if (lt in {"bytes", "bytearray"} and rt in {"bytes", "bytearray"}) else "str"
        elif op_sym == "**" and lt in {"int64", "float64"} and rt in {"int64", "float64"}:
            out_t = "float64"
            if lt == "int64":
                casts.append({"on": "left", "from": "int64", "to": "float64", "reason": "numeric_promotion"})
            if rt == "int64":
                casts.append({"on": "right", "from": "int64", "to": "float64", "reason": "numeric_promotion"})
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
            tok_v: str = str(tok["v"])
            if tok_v.startswith("0x") or tok_v.startswith("0X"):
                tok_value = int(tok_v[2:], 16)
            elif tok_v.startswith("0b") or tok_v.startswith("0B"):
                tok_value = int(tok_v[2:], 2)
            elif tok_v.startswith("0o") or tok_v.startswith("0O"):
                tok_value = int(tok_v[2:], 8)
            else:
                tok_value = int(tok_v)
            return {
                "kind": "Constant",
                "source_span": self._node_span(tok["s"], tok["e"]),
                "resolved_type": "int64",
                "borrow_kind": "value",
                "casts": [],
                "repr": tok["v"],
                "value": tok_value,
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
            str_parts: list[dict[str, Any]] = [self._eat("STR")]
            while self._cur()["k"] == "STR":
                str_parts.append(self._eat("STR"))
            if len(str_parts) > 1:
                str_nodes = [
                    _sh_parse_expr(
                        part["v"],
                        line_no=self.line_no,
                        col_base=self.col_base + int(part["s"]),
                        name_types=self.name_types,
                        fn_return_types=self.fn_return_types,
                        class_method_return_types=self.class_method_return_types,
                        class_base=self.class_base,
                    )
                    for part in str_parts
                ]
                node = str_nodes[0]
                for str_rhs in str_nodes[1:]:
                    node = {
                        "kind": "BinOp",
                        "source_span": self._node_span(str_parts[0]["s"], str_parts[-1]["e"]),
                        "resolved_type": "str",
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": self._src_slice(str_parts[0]["s"], str_parts[-1]["e"]),
                        "left": node,
                        "op": "Add",
                        "right": str_rhs,
                    }
                return node

            tok = str_parts[0]
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
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message="unterminated f-string placeholder in self_hosted parser",
                            source_span=self._node_span(tok["s"], tok["e"]),
                            hint="Close f-string placeholder with `}`.",
                        )
                    inner_expr = body[j + 1 : k].strip()
                    expr_txt = inner_expr
                    conv_txt = ""
                    fmt_txt = ""
                    conv_pos = _sh_find_top_char(inner_expr, "!")
                    fmt_pos = _sh_find_top_char(inner_expr, ":")
                    if conv_pos >= 0 and (fmt_pos < 0 or conv_pos < fmt_pos):
                        expr_txt = inner_expr[:conv_pos].strip()
                        conv_tail_end = fmt_pos if fmt_pos >= 0 else len(inner_expr)
                        conv_txt = inner_expr[conv_pos + 1 : conv_tail_end].strip()
                        if fmt_pos >= 0:
                            fmt_txt = inner_expr[fmt_pos + 1 :].strip()
                    elif fmt_pos >= 0:
                        expr_txt = inner_expr[:fmt_pos].strip()
                        fmt_txt = inner_expr[fmt_pos + 1 :].strip()
                    if expr_txt == "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message="empty f-string placeholder expression in self_hosted parser",
                            source_span=self._node_span(tok["s"], tok["e"]),
                            hint="Use `{expr}` form inside f-string placeholders.",
                        )
                    fv: dict[str, Any] = {
                        "kind": "FormattedValue",
                        "value": _sh_parse_expr(
                            expr_txt,
                            line_no=self.line_no,
                            col_base=self.col_base + tok["s"] + j + 1,
                            name_types=self.name_types,
                            fn_return_types=self.fn_return_types,
                            class_method_return_types=self.class_method_return_types,
                            class_base=self.class_base,
                        ),
                    }
                    if conv_txt != "":
                        fv["conversion"] = conv_txt
                    if fmt_txt != "":
                        fv["format_spec"] = fmt_txt
                    values.append(fv)
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
            if self._cur()["k"] == "NAME" and self._cur()["v"] == "for":
                self._eat("NAME")
                target = self._parse_comp_target()
                in_tok = self._eat("NAME")
                if in_tok["v"] != "in":
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="expected 'in' in generator expression",
                        source_span=self._node_span(in_tok["s"], in_tok["e"]),
                        hint="Use `(expr for x in iterable)` syntax.",
                    )
                iter_expr = self._parse_or()
                ifs: list[dict[str, Any]] = []
                while self._cur()["k"] == "NAME" and self._cur()["v"] == "if":
                    self._eat("NAME")
                    ifs.append(self._parse_or())
                r = self._eat(")")
                end_node = ifs[-1] if len(ifs) > 0 else iter_expr
                s = l["s"]
                e = int(end_node["source_span"]["end_col"]) - self.col_base
                return {
                    "kind": "ListComp",
                    "source_span": self._node_span(s, r["e"]),
                    "resolved_type": f"list[{first.get('resolved_type', 'unknown')}]",
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": self._src_slice(s, r["e"]),
                    "elt": first,
                    "generators": [{"target": target, "iter": iter_expr, "ifs": ifs, "is_async": False}],
                    "lowered_kind": "GeneratorArg",
                }
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
                    target = self._parse_comp_target()
                    in_tok = self._eat("NAME")
                    if in_tok["v"] != "in":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message="expected 'in' in list comprehension",
                            source_span=self._node_span(in_tok["s"], in_tok["e"]),
                            hint="Use `[x for x in iterable]` syntax.",
                        )
                    iter_expr = self._parse_or()
                    if (
                        isinstance(iter_expr, dict)
                        and iter_expr.get("kind") == "Call"
                        and isinstance(iter_expr.get("func"), dict)
                        and iter_expr.get("func", {}).get("kind") == "Name"
                        and iter_expr.get("func", {}).get("id") == "range"
                    ):
                        rargs = list(iter_expr.get("args", []))
                        range_target_span = self._node_span(self.col_base, self.col_base)
                        if isinstance(target, dict):
                            target_span_obj = target.get("source_span")
                            if isinstance(target_span_obj, dict):
                                ts = target_span_obj.get("col")
                                te = target_span_obj.get("end_col")
                            else:
                                ts = None
                                te = None
                            if isinstance(ts, int) and isinstance(te, int):
                                range_target_span = self._node_span(ts, te)
                        if len(rargs) == 1:
                            start_node = {
                                "kind": "Constant",
                                "source_span": range_target_span,
                                "resolved_type": "int64",
                                "borrow_kind": "value",
                                "casts": [],
                                "repr": "0",
                                "value": 0,
                            }
                            stop_node = rargs[0]
                            step_node = {
                                "kind": "Constant",
                                "source_span": range_target_span,
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
                                "source_span": range_target_span,
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
                        step_const_obj: Any = None
                        if isinstance(step_node, dict):
                            step_const_obj = step_node.get("value")
                        step_const: int | None = None
                        if isinstance(step_const_obj, int):
                            step_const = int(step_const_obj)
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
                        ifs.append(self._parse_or())
                    r = self._eat("]")
                    tgt_ty = self._iter_item_type(iter_expr)
                    first_norm = first
                    ifs_norm = ifs
                    if tgt_ty != "unknown":
                        snaps: dict[str, str] = {}
                        self._collect_and_bind_comp_target_types(target, tgt_ty, snaps)
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
                        self._restore_comp_target_types(snaps)
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
                                "target": target,
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
                first_key = keys[0]
                first_val = vals[0]
                if self._cur()["k"] == "NAME" and self._cur()["v"] == "for":
                    self._eat("NAME")
                    target = self._parse_comp_target()
                    in_tok = self._eat("NAME")
                    if in_tok["v"] != "in":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message="expected 'in' in dict comprehension",
                            source_span=self._node_span(in_tok["s"], in_tok["e"]),
                            hint="Use `for x in iterable` form.",
                        )
                    iter_expr = self._parse_or()
                    ifs: list[dict[str, Any]] = []
                    while self._cur()["k"] == "NAME" and self._cur()["v"] == "if":
                        self._eat("NAME")
                        ifs.append(self._parse_or())

                    key_node = first_key
                    val_node = first_val
                    ifs_norm: list[dict[str, Any]] = list(ifs)
                    iter_ty = self._iter_item_type(iter_expr)
                    if iter_ty != "unknown":
                        snapshots: dict[str, str] = {}
                        self._collect_and_bind_comp_target_types(target, iter_ty, snapshots)
                        try:
                            key_repr = first_key.get("repr")
                            val_repr = first_val.get("repr")
                            if isinstance(key_repr, str) and key_repr != "":
                                key_node = _sh_parse_expr(
                                    key_repr,
                                    line_no=self.line_no,
                                    col_base=int(first_key.get("source_span", {}).get("col", self.col_base)),
                                    name_types=self.name_types,
                                    fn_return_types=self.fn_return_types,
                                    class_method_return_types=self.class_method_return_types,
                                    class_base=self.class_base,
                                )
                            if isinstance(val_repr, str) and val_repr != "":
                                val_node = _sh_parse_expr(
                                    val_repr,
                                    line_no=self.line_no,
                                    col_base=int(first_val.get("source_span", {}).get("col", self.col_base)),
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
                        finally:
                            self._restore_comp_target_types(snapshots)
                    end_node = ifs_norm[-1] if len(ifs_norm) > 0 else iter_expr
                    end_col = int(end_node.get("source_span", {}).get("end_col", self.col_base))
                    r = self._eat("}")
                    return {
                        "kind": "DictComp",
                        "source_span": self._node_span(l["s"], end_col - self.col_base),
                        "resolved_type": f"dict[{key_node.get('resolved_type', 'unknown')},{val_node.get('resolved_type', 'unknown')}]",
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": self._src_slice(l["s"], end_col - self.col_base),
                        "key": key_node,
                        "value": val_node,
                        "generators": [
                            {
                                "target": target,
                                "iter": iter_expr,
                                "ifs": ifs_norm,
                                "is_async": False,
                            }
                        ],
                    }
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
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message=f"self_hosted parser cannot parse expression token: {tok['k']}",
            source_span=self._node_span(tok["s"], tok["e"]),
            hint="Extend self_hosted expression parser for this syntax.",
        )


def _sh_parse_expr(
    text: str,
    line_no: int,
    col_base: int,
    name_types: dict[str, str],
    fn_return_types: dict[str, str],
    class_method_return_types: dict[str, dict[str, str]] = {},
    class_base: dict[str, str | None] = {},
) -> dict[str, Any]:
    """1つの式文字列を self-hosted 方式で EAST 式ノードに変換する。"""
    txt = text.strip()
    if txt == "":
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message="empty expression in self_hosted backend",
            source_span=_sh_span(line_no, col_base, col_base),
            hint="Provide a non-empty expression.",
        )
    parser = _ShExprParser(
        txt,
        line_no,
        col_base + (len(text) - len(text.lstrip())),
        name_types,
        fn_return_types,
        class_method_return_types,
        class_base,
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
        rt_obj: Any = body_node.get("resolved_type", "unknown")
        rt: str = str(rt_obj) if isinstance(rt_obj, str) else "unknown"
        else_rt_obj: Any = else_node.get("resolved_type", "unknown")
        else_rt: str = str(else_rt_obj) if isinstance(else_rt_obj, str) else "unknown"
        if rt != else_rt:
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
            lowered_kind = "BuiltinCall" if fn_name in {"any", "all"} else None
            runtime_call = "py_any" if fn_name == "any" else ("py_all" if fn_name == "all" else "")
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
                "lowered_kind": lowered_kind,
                "builtin_name": fn_name if lowered_kind is not None else None,
                "runtime_call": runtime_call if lowered_kind is not None else None,
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
                inner_parts: list[str] = _sh_split_top_commas(inner)
                if len(inner_parts) == 1 and inner_parts[0] == inner and _sh_split_top_keyword(inner, "for") > 0 and _sh_split_top_keyword(inner, "in") > 0:
                    rewritten = txt[: open_idx + 1] + "[" + inner + "]" + txt[close_idx:]
                    return _sh_parse_expr_lowered(rewritten, ln_no=ln_no, col=col, name_types=dict(name_types))

    # Handle concatenation chains that include f-strings before generic parsing.
    top_comma_parts = _sh_split_top_commas(txt)
    is_single_top_expr = len(top_comma_parts) == 1

    adjacent_strings = _sh_extract_adjacent_string_parts(txt, ln_no, col, name_types)
    if adjacent_strings is not None and len(adjacent_strings) >= 2:
        nodes = [
            _sh_parse_expr(
                part,
                line_no=ln_no,
                col_base=part_col,
                name_types=name_types,
                fn_return_types=_SH_FN_RETURNS,
                class_method_return_types=_SH_CLASS_METHOD_RETURNS,
                class_base=_SH_CLASS_BASE,
            )
            for part, part_col in adjacent_strings
        ]
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
    if len(plus_parts) >= 2 and is_single_top_expr:
        return _sh_parse_expr(
            txt,
            line_no=ln_no,
            col_base=col,
            name_types=name_types,
            fn_return_types=_SH_FN_RETURNS,
            class_method_return_types=_SH_CLASS_METHOD_RETURNS,
            class_base=_SH_CLASS_BASE,
        )

    # dict-comp support: {k: v for x in it} / {k: v for a, b in it}
    if txt.startswith("{") and txt.endswith("}") and ":" in txt and is_single_top_expr:
        inner = txt[1:-1].strip()
        p_for = _sh_split_top_keyword(inner, "for")
        if p_for > 0:
            head = inner[:p_for].strip()
            tail = inner[p_for + 3 :].strip()
            p_in = _sh_split_top_keyword(tail, "in")
            if p_in <= 0:
                raise _make_east_build_error(
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
                raise _make_east_build_error(
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
    if txt.startswith("{") and txt.endswith("}") and ":" not in txt and is_single_top_expr:
        inner = txt[1:-1].strip()
        p_for = _sh_split_top_keyword(inner, "for")
        if p_for > 0:
            elt_txt = inner[:p_for].strip()
            tail = inner[p_for + 3 :].strip()
            p_in = _sh_split_top_keyword(tail, "in")
            if p_in <= 0:
                raise _make_east_build_error(
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
                    raise _make_east_build_error(
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

    # list-comp support: [expr for target in iter if cond] + chained for-clauses
    if txt.startswith("[") and txt.endswith("]") and is_single_top_expr:
        first_closing = -1
        depth = 0
        in_str3: str | None = None
        esc3 = False
        for i, ch in enumerate(txt):
            if in_str3 is not None:
                if esc3:
                    esc3 = False
                    continue
                if ch == "\\":
                    esc3 = True
                elif ch == in_str3:
                    in_str3 = None
                continue
            if ch in {"'", '"'}:
                in_str3 = ch
                continue
            if ch == "[":
                depth += 1
            elif ch == "]":
                if depth == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"invalid bracket nesting in self_hosted parser: {txt}",
                        source_span=_sh_span(ln_no, col, col + len(raw)),
                        hint="Check list/tuple bracket balance.",
                    )
                depth -= 1
                if depth == 0:
                    first_closing = i
                    break
        if first_closing != len(txt) - 1:
            # Delegate to full parser when this is not a standalone list expression
            # (e.g. list-comprehension result with trailing slice/index).
            return _sh_parse_expr(
                txt,
                line_no=ln_no,
                col_base=col,
                name_types=name_types,
                fn_return_types=_SH_FN_RETURNS,
                class_method_return_types=_SH_CLASS_METHOD_RETURNS,
                class_base=_SH_CLASS_BASE,
            )

        inner = txt[1:-1].strip()
        p_for = _sh_split_top_keyword(inner, "for")
        if p_for > 0:
            elt_txt = inner[:p_for].strip()
            rest = inner[p_for + 3 :].strip()
            generators: list[dict[str, Any]] = []
            comp_types: dict[str, str] = dict(name_types)
            while True:
                    p_in = _sh_split_top_keyword(rest, "in")
                    if p_in <= 0:
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"invalid list comprehension in self_hosted parser: {txt}",
                            source_span=_sh_span(ln_no, col, col + len(raw)),
                            hint="Use `[elem for item in iterable]` form.",
                        )
                    tgt_txt = rest[:p_in].strip()
                    iter_and_suffix_txt = rest[p_in + 2 :].strip()
                    if tgt_txt == "" or iter_and_suffix_txt == "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"invalid list comprehension in self_hosted parser: {txt}",
                            source_span=_sh_span(ln_no, col, col + len(raw)),
                            hint="Use `[elem for item in iterable]` form.",
                        )
                    p_next_for = _sh_split_top_keyword(iter_and_suffix_txt, "for")
                    p_next_if = _sh_split_top_keyword(iter_and_suffix_txt, "if")
                    next_pos = -1
                    if p_next_for >= 0 and (p_next_if < 0 or p_next_for < p_next_if):
                        next_pos = p_next_for
                    elif p_next_if >= 0:
                        next_pos = p_next_if
                    iter_txt = iter_and_suffix_txt
                    suffix_txt = ""
                    if next_pos >= 0:
                        iter_txt = iter_and_suffix_txt[:next_pos].strip()
                        suffix_txt = iter_and_suffix_txt[next_pos:].strip()
                    if iter_txt == "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"invalid list comprehension in self_hosted parser: {txt}",
                            source_span=_sh_span(ln_no, col, col + len(raw)),
                            hint="Use `[elem for item in iterable]` form.",
                        )

                    target_node = _sh_parse_expr_lowered(
                        tgt_txt,
                        ln_no=ln_no,
                        col=col + txt.find(tgt_txt),
                        name_types=dict(comp_types),
                    )
                    iter_node = _sh_parse_expr_lowered(
                        iter_txt,
                        ln_no=ln_no,
                        col=col + txt.find(iter_txt),
                        name_types=dict(comp_types),
                    )
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
                        step_const_obj: Any = None
                        if isinstance(step_node, dict):
                            step_const_obj = step_node.get("value")
                        step_const: int | None = None
                        if isinstance(step_const_obj, int):
                            step_const = int(step_const_obj)
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

                    comp_types = _sh_bind_comp_target_types(dict(comp_types), target_node, iter_node)
                    if_nodes: list[dict[str, Any]] = []
                    while suffix_txt.startswith("if "):
                        cond_tail = suffix_txt[3:].strip()
                        p_cond_for = _sh_split_top_keyword(cond_tail, "for")
                        p_cond_if = _sh_split_top_keyword(cond_tail, "if")
                        split_pos = -1
                        if p_cond_for >= 0 and (p_cond_if < 0 or p_cond_for < p_cond_if):
                            split_pos = p_cond_for
                        elif p_cond_if >= 0:
                            split_pos = p_cond_if
                        cond_txt = cond_tail
                        suffix_txt = ""
                        if split_pos >= 0:
                            cond_txt = cond_tail[:split_pos].strip()
                            suffix_txt = cond_tail[split_pos:].strip()
                        if cond_txt == "":
                            raise _make_east_build_error(
                                kind="unsupported_syntax",
                                message=f"invalid list comprehension condition in self_hosted parser: {txt}",
                                source_span=_sh_span(ln_no, col, col + len(raw)),
                                hint="Use `[elem for item in iterable if cond]` form.",
                            )
                        if_nodes.append(
                            _sh_parse_expr_lowered(
                                cond_txt,
                                ln_no=ln_no,
                                col=col + txt.find(cond_txt),
                                name_types=dict(comp_types),
                            )
                        )

                    generators.append(
                        {
                            "target": target_node,
                            "iter": iter_node,
                            "ifs": if_nodes,
                            "is_async": False,
                        }
                    )
                    if suffix_txt == "":
                        break
                    if not suffix_txt.startswith("for "):
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"invalid list comprehension in self_hosted parser: {txt}",
                            source_span=_sh_span(ln_no, col, col + len(raw)),
                            hint="Use `[elem for item in iterable for item2 in iterable2]` form.",
                        )
                    rest = suffix_txt[4:].strip()
                    if rest == "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"invalid list comprehension in self_hosted parser: {txt}",
                            source_span=_sh_span(ln_no, col, col + len(raw)),
                            hint="Use `[elem for item in iterable for item2 in iterable2]` form.",
                        )

            elt_node = _sh_parse_expr_lowered(elt_txt, ln_no=ln_no, col=col + txt.find(elt_txt), name_types=dict(comp_types))
            elem_t = str(elt_node.get("resolved_type", "unknown"))
            return {
                "kind": "ListComp",
                "source_span": _sh_span(ln_no, col, col + len(raw)),
                "resolved_type": f"list[{elem_t}]",
                "borrow_kind": "value",
                "casts": [],
                "repr": txt,
                "elt": elt_node,
                "generators": generators,
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
        return _sh_parse_expr(
            txt,
            line_no=ln_no,
            col_base=col,
            name_types=name_types,
            fn_return_types=_SH_FN_RETURNS,
            class_method_return_types=_SH_CLASS_METHOD_RETURNS,
            class_base=_SH_CLASS_BASE,
        )

    tuple_parts = _sh_split_top_commas(txt)
    if len(tuple_parts) >= 2 or (len(tuple_parts) == 1 and txt.endswith(",")):
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

def _sh_parse_stmt_block_mutable(body_lines: list[tuple[int, str]], *, name_types: dict[str, str], scope_label: str) -> list[dict[str, Any]]:
    """インデントブロックを文単位で解析し、EAST 文リストを返す。"""
    def _maybe_bind_self_field(
        target_expr: dict[str, Any] | None,
        value_type: str | None,
        *,
        explicit: str | None = None,
    ) -> None:
        """`self.xxx` への代入時、self フィールドの型推論を更新する。"""
        if not isinstance(target_expr, dict):
            return
        if target_expr.get("kind") != "Attribute":
            return
        owner = target_expr.get("value")
        if not isinstance(owner, dict):
            return
        if owner.get("kind") != "Name" or owner.get("id") != "self":
            return
        field_name = str(target_expr.get("attr", "")).strip()
        if field_name == "":
            return
        candidate = value_type or ""
        if candidate != "":
            name_types[field_name] = candidate
            return
        if isinstance(explicit, str) and explicit.strip() != "":
            name_types[field_name] = explicit.strip()

    body_lines, merged_line_end = _sh_merge_logical_lines(body_lines)

    stmts: list[dict[str, Any]] = []
    pending_leading_trivia: list[dict[str, Any]] = []
    pending_blank_count = 0

    skip = 0
    for i, (_, ln_txt) in enumerate(body_lines):
        if skip > 0:
            skip -= 1
            continue
        ln_no, ln_txt = body_lines[i]
        indent = len(ln_txt) - len(ln_txt.lstrip(" "))
        raw_s = ln_txt.strip()
        s = _sh_strip_inline_comment(raw_s)
        _sh_raise_if_trailing_stmt_terminator(s, line_no=ln_no, line_text=ln_txt)

        if raw_s == "":
            pending_blank_count += 1
            continue
        if raw_s.startswith("#"):
            if pending_blank_count > 0:
                pending_leading_trivia.append({"kind": "blank", "count": pending_blank_count})
                pending_blank_count = 0
            text = raw_s[1:]
            if text.startswith(" "):
                text = text[1:]
            pending_leading_trivia.append({"kind": "comment", "text": text})
            continue
        if s == "":
            continue

        sig_line, inline_fn_stmt = _sh_split_def_header_and_inline_stmt(s)
        sig = _sh_parse_def_sig(ln_no, sig_line)
        if sig is not None:
            fn_name = str(sig["name"])
            fn_ret = str(sig["ret"])
            arg_types: dict[str, str] = dict(sig["arg_types"])
            arg_order: list[str] = list(sig["arg_order"])
            arg_defaults_raw_obj: Any = sig.get("arg_defaults")
            arg_defaults_raw: dict[str, Any] = arg_defaults_raw_obj if isinstance(arg_defaults_raw_obj, dict) else {}
            fn_block: list[tuple[int, str]] = []
            j = i + 1
            if inline_fn_stmt != "":
                fn_block = [(ln_no, " " * (indent + 4) + inline_fn_stmt)]
            else:
                fn_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
                if len(fn_block) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser requires non-empty nested function body '{fn_name}'",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Add nested function statements.",
                    )
            fn_scope_types: dict[str, str] = dict(name_types)
            for arg_name, arg_ty in arg_types.items():
                fn_scope_types[arg_name] = arg_ty
            fn_stmts = _sh_parse_stmt_block(fn_block, name_types=fn_scope_types, scope_label=f"{scope_label}.{fn_name}")
            docstring, fn_stmts = _sh_extract_leading_docstring(fn_stmts)
            fn_ret = _sh_infer_return_type_for_untyped_def(fn_ret, fn_stmts)
            yield_types = _sh_collect_yield_value_types(fn_stmts)
            is_generator = len(yield_types) > 0
            fn_ret_effective = fn_ret
            yield_value_type = "unknown"
            if is_generator:
                fn_ret_effective, yield_value_type = _sh_make_generator_return_type(fn_ret, yield_types)
            arg_defaults: dict[str, Any] = {}
            arg_index_map: dict[str, int] = {}
            for arg_pos, arg_name in enumerate(arg_order):
                arg_index_map[arg_name] = int(arg_pos)
                if arg_name in arg_defaults_raw:
                    default_obj: Any = arg_defaults_raw[arg_name]
                    default_txt: str = str(default_obj).strip()
                    if default_txt != "":
                        default_col = ln_txt.find(default_txt)
                        if default_col < 0:
                            default_col = 0
                        arg_defaults[arg_name] = _sh_parse_expr_lowered(
                            default_txt,
                            ln_no=ln_no,
                            col=default_col,
                            name_types=dict(name_types),
                        )
            arg_usage_map = _sh_build_arg_usage_map(arg_order, arg_types, fn_stmts)
            callable_parts: list[str] = []
            for arg_name in arg_order:
                callable_parts.append(arg_types.get(arg_name, "unknown"))
            name_types[fn_name] = "callable[" + ", ".join(callable_parts) + "->" + fn_ret_effective + "]"
            _SH_FN_RETURNS[fn_name] = fn_ret_effective
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                {
                    "kind": "FunctionDef",
                    "name": fn_name,
                    "original_name": fn_name,
                    "source_span": _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                    "arg_types": arg_types,
                    "arg_order": arg_order,
                    "arg_defaults": arg_defaults,
                    "arg_index": arg_index_map,
                    "return_type": fn_ret_effective,
                    "arg_usage": arg_usage_map,
                    "renamed_symbols": {},
                    "docstring": docstring,
                    "body": fn_stmts,
                    "is_generator": 1 if is_generator else 0,
                    "yield_value_type": yield_value_type,
                },
            )
            skip = j - i - 1
            continue

        if s.startswith("if ") and s.endswith(":"):
            cond_txt = s[len("if ") : -1].strip()
            cond_col = ln_txt.find(cond_txt)
            cond_expr = _sh_parse_expr_lowered(cond_txt, ln_no=ln_no, col=cond_col, name_types=dict(name_types))
            then_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(then_block) == 0:
                raise _make_east_build_error(
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
            skip = j - i - 1
            continue

        if s.startswith("for "):
            for_full = s[len("for ") :].strip()
            for_head = ""
            inline_stmt_text = ""
            if for_full.endswith(":"):
                for_head = for_full[:-1].strip()
            else:
                split_colon = _sh_split_top_level_colon(for_full)
                if split_colon is not None:
                    for_head = split_colon[0]
                    inline_stmt_text = split_colon[1]
            if for_head == "":
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse for statement: {s}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `for target in iterable:` form.",
                )
            split_for = _sh_split_top_level_in(for_head)
            if split_for is None:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse for statement: {s}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `for target in iterable:` form.",
                )
            tgt_txt, iter_txt = split_for
            tgt_col = ln_txt.find(tgt_txt)
            iter_col = ln_txt.find(iter_txt)
            target_expr = _sh_parse_expr_lowered(tgt_txt, ln_no=ln_no, col=tgt_col, name_types=dict(name_types))
            iter_expr = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=iter_col, name_types=dict(name_types))
            body_block: list[tuple[int, str]] = []
            j = i + 1
            if inline_stmt_text != "":
                body_block.append((ln_no, " " * (indent + 4) + inline_stmt_text))
            else:
                body_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
                if len(body_block) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"for body is missing in '{scope_label}'",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Add indented for-body.",
                    )
            t_ty = "unknown"
            i_ty = str(iter_expr.get("resolved_type", "unknown"))
            i_ty_norm = i_ty.strip()
            iter_mode = "static_fastpath"
            iterable_trait = "unknown"
            iter_protocol = "static_range"
            tuple_target_elem_types: list[str] = []
            if i_ty.startswith("list[") and i_ty.endswith("]"):
                inner_t = i_ty[5:-1].strip()
                t_ty = inner_t
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
                if inner_t.startswith("tuple[") and inner_t.endswith("]"):
                    tuple_inner = inner_t[6:-1].strip()
                    if tuple_inner != "":
                        tuple_target_elem_types = _sh_split_top_commas(tuple_inner)
            elif i_ty.startswith("dict[") and i_ty.endswith("]"):
                dict_inner = i_ty[5:-1].strip()
                dict_parts = _sh_split_top_commas(dict_inner)
                if len(dict_parts) >= 1:
                    key_t = dict_parts[0].strip()
                    t_ty = key_t if key_t != "" else "unknown"
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty.startswith("tuple[") and i_ty.endswith("]"):
                t_ty = "unknown"
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty.startswith("set[") and i_ty.endswith("]"):
                t_ty = i_ty[4:-1]
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty == "str":
                t_ty = "str"
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty in {"bytes", "bytearray"}:
                t_ty = "uint8"
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty_norm == "Any" or i_ty_norm == "object":
                iter_mode = "runtime_protocol"
                iterable_trait = "unknown"
                iter_protocol = "runtime_protocol"
            elif i_ty_norm in {"int", "int64", "float", "float64", "bool"}:
                iterable_trait = "no"
                iter_mode = "runtime_protocol"
                iter_protocol = "runtime_protocol"
            elif "|" in i_ty_norm:
                union_parts = _sh_split_top_commas(i_ty_norm.replace("|", ","))
                for up in union_parts:
                    u = up.strip()
                    if u == "Any" or u == "object":
                        iter_mode = "runtime_protocol"
                        iter_protocol = "runtime_protocol"
                        break
            if isinstance(iter_expr, dict):
                iter_expr["iterable_trait"] = iterable_trait
                iter_expr["iter_protocol"] = iter_protocol
                iter_expr["iter_element_type"] = t_ty
            target_names: list[str] = []
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                nm = str(target_expr.get("id", ""))
                if nm != "":
                    target_names.append(nm)
            elif isinstance(target_expr, dict) and target_expr.get("kind") == "Tuple":
                elem_nodes_obj: Any = target_expr.get("elements", [])
                elem_nodes: list[dict[str, Any]] = elem_nodes_obj if isinstance(elem_nodes_obj, list) else []
                for e in elem_nodes:
                    if isinstance(e, dict) and e.get("kind") == "Name":
                        nm = str(e.get("id", ""))
                        if nm != "":
                            target_names.append(nm)
            if len(tuple_target_elem_types) > 0 and isinstance(target_expr, dict) and target_expr.get("kind") == "Tuple":
                target_expr["resolved_type"] = f"tuple[{','.join([t.strip() if t.strip() != '' else 'unknown' for t in tuple_target_elem_types])}]"
                for idx, nm in enumerate(target_names):
                    if idx < len(tuple_target_elem_types):
                        et = tuple_target_elem_types[idx].strip()
                        if et == "":
                            et = "unknown"
                        name_types[nm] = et
                        try:
                            elem_nodes[idx]["resolved_type"] = et
                        except Exception:
                            pass
                    else:
                        name_types[nm] = "unknown"
                        try:
                            elem_nodes[idx]["resolved_type"] = "unknown"
                        except Exception:
                            pass
            elif t_ty != "unknown":
                for nm in target_names:
                    name_types[nm] = t_ty
                if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                    target_expr["resolved_type"] = t_ty
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
                step_const_obj: Any = None
                if isinstance(step_node, dict):
                    step_const_obj = step_node.get("value")
                step_const: int | None = None
                if isinstance(step_const_obj, int):
                    step_const = int(step_const_obj)
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
                skip = j - i - 1
                continue
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                {
                    "kind": "For",
                    "source_span": _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                    "target": target_expr,
                    "target_type": t_ty,
                    "iter_mode": iter_mode,
                    "iter_source_type": i_ty_norm if i_ty_norm != "" else "unknown",
                    "iter_element_type": t_ty,
                    "iter": iter_expr,
                    "body": _sh_parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                    "orelse": [],
                }
            )
            skip = j - i - 1
            continue

        m_import: re.Match | None = re.match(r"^import\s+(.+)$", s, flags=re.S)
        if m_import is not None:
            names_txt = re.strip_group(m_import, 1)
            raw_parts: list[str] = []
            for p in names_txt.split(","):
                p2: str = p.strip()
                if p2 != "":
                    raw_parts.append(p2)
            if len(raw_parts) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="import statement has no module names",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `import module` or `import module as alias`.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=True)
                if parsed_alias is None:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"unsupported import clause: {part}",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use `import module` or `import module as alias` form.",
                    )
                mod_name, as_name_txt = parsed_alias
                alias_item: dict[str, str | None] = {"name": mod_name, "asname": None}
                if as_name_txt != "":
                    alias_item["asname"] = as_name_txt
                aliases.append(alias_item)
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                {
                    "kind": "Import",
                    "source_span": _sh_stmt_span(merged_line_end, ln_no, 0, len(ln_txt)),
                    "names": aliases,
                },
            )
            continue

        if s.startswith("from "):
            marker = " import "
            pos = s.find(marker)
            if pos >= 0:
                mod_txt = s[5:pos].strip()
                if mod_txt.startswith("."):
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="relative import is not supported",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use absolute import form: `from module import name`.",
                    )
        m_import_from: re.Match | None = re.match(r"^from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+import\s+(.+)$", s, flags=re.S)
        if m_import_from is not None:
            mod_name = re.strip_group(m_import_from, 1)
            names_txt = re.strip_group(m_import_from, 2)
            if names_txt == "*":
                pending_blank_count = _sh_push_stmt_with_trivia(
                    stmts,
                    pending_leading_trivia,
                    pending_blank_count,
                    {
                        "kind": "ImportFrom",
                        "source_span": _sh_stmt_span(merged_line_end, ln_no, 0, len(ln_txt)),
                        "module": mod_name,
                        "names": [{"name": "*", "asname": None}],
                        "level": 0,
                    },
                )
                continue
            raw_parts: list[str] = []
            for p in names_txt.split(","):
                p2: str = p.strip()
                if p2 != "":
                    raw_parts.append(p2)
            if len(raw_parts) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="from-import statement has no symbol names",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `from module import name` form.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                if parsed_alias is None:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"unsupported from-import clause: {part}",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use `from module import name` or `... as alias`.",
                    )
                sym_name, as_name_txt = parsed_alias
                alias_item: dict[str, str | None] = {"name": sym_name, "asname": None}
                if as_name_txt != "":
                    alias_item["asname"] = as_name_txt
                aliases.append(alias_item)
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                {
                    "kind": "ImportFrom",
                    "source_span": _sh_stmt_span(merged_line_end, ln_no, 0, len(ln_txt)),
                    "module": mod_name,
                    "names": aliases,
                    "level": 0,
                },
            )
            continue

        if s.startswith("with ") and s.endswith(":"):
            m_with: re.Match | None = re.match(r"^with\s+(.+)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$", s, flags=re.S)
            if m_with is None:
                raise _make_east_build_error(
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
                raise _make_east_build_error(
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
            skip = j - i - 1
            continue

        if s.startswith("while ") and s.endswith(":"):
            cond_txt = s[len("while ") : -1].strip()
            cond_col = ln_txt.find(cond_txt)
            cond_expr = _sh_parse_expr_lowered(cond_txt, ln_no=ln_no, col=cond_col, name_types=dict(name_types))
            body_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(body_block) == 0:
                raise _make_east_build_error(
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
            skip = j - i - 1
            continue

        if s == "try:":
            try_body, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(try_body) == 0:
                raise _make_east_build_error(
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
                exc_clause = _sh_parse_except_clause(h_s)
                if exc_clause is not None:
                    ex_type_txt, ex_name = exc_clause
                    ex_type_col = h_ln.find(ex_type_txt)
                    if ex_type_col < 0:
                        ex_type_col = h_ln.find("except")
                        if ex_type_col < 0:
                            ex_type_col = 0
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
            skip = j - i - 1
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
            continue

        if s == "pass":
            pass_stmt: dict[str, Any] = {
                "kind": "Pass",
                "source_span": _sh_stmt_span(merged_line_end, ln_no, indent, indent + 4),
            }
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, pass_stmt)
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
            continue

        if s.startswith("return "):
            rcol = ln_txt.find("return ")
            expr_txt = s[len("return ") :].strip()
            expr_col = ln_txt.find(expr_txt)
            if expr_col < 0:
                expr_col = rcol + len("return ")
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                {
                    "kind": "Return",
                    "source_span": _sh_stmt_span(merged_line_end, ln_no, rcol, len(ln_txt)),
                    "value": _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types)),
                }
            )
            continue

        if s == "yield":
            ycol = ln_txt.find("yield")
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                {
                    "kind": "Yield",
                    "source_span": _sh_stmt_span(merged_line_end, ln_no, ycol, len(ln_txt)),
                    "value": None,
                },
            )
            continue

        if s.startswith("yield "):
            ycol = ln_txt.find("yield ")
            expr_txt = s[len("yield ") :].strip()
            expr_col = ln_txt.find(expr_txt)
            if expr_col < 0:
                expr_col = ycol + len("yield ")
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                {
                    "kind": "Yield",
                    "source_span": _sh_stmt_span(merged_line_end, ln_no, ycol, len(ln_txt)),
                    "value": _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types)),
                },
            )
            continue

        parsed_typed = _sh_parse_typed_binding(s, allow_dotted_name=True)
        if parsed_typed is not None:
            typed_target, typed_ann, typed_default = parsed_typed
        else:
            typed_target, typed_ann, typed_default = "", "", ""
        if parsed_typed is not None and typed_default == "":
            target_txt = typed_target
            ann_txt = typed_ann
            ann = _sh_ann_to_type(ann_txt)
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            _maybe_bind_self_field(target_expr, None, explicit=ann)
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
            continue

        if parsed_typed is not None and typed_default != "":
            target_txt = typed_target
            ann_txt = typed_ann
            expr_txt = typed_default
            ann = _sh_ann_to_type(ann_txt)
            expr_col = ln_txt.find(expr_txt)
            val_expr = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            _maybe_bind_self_field(target_expr, None, explicit=ann)
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
            continue

        parsed_aug = _sh_parse_augassign(s)
        if parsed_aug is not None:
            target_txt, aug_op, expr_txt = parsed_aug
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
            expr_col = ln_txt.find(expr_txt)
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            val_expr = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            target_ty = "unknown"
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                target_ty = name_types.get(str(target_expr.get("id", "")), "unknown")
            decl_type: str | None = None
            if target_ty != "unknown":
                decl_type = target_ty
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                {
                    "kind": "AugAssign",
                    "source_span": _sh_stmt_span(merged_line_end, ln_no, target_col, len(ln_txt)),
                    "target": target_expr,
                    "op": op_map[aug_op],
                    "value": val_expr,
                    "declare": False,
                    "decl_type": decl_type,
                }
            )
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
            continue

        asg_split = _sh_split_top_level_assign(s)
        if asg_split is not None:
            target_txt, expr_txt = asg_split
            expr_col = ln_txt.find(expr_txt)
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            val_expr = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            decl_type = val_expr.get("resolved_type", "unknown")
            _maybe_bind_self_field(target_expr, str(decl_type) if isinstance(decl_type, str) else "")
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
            continue

        expr_col = len(ln_txt) - len(ln_txt.lstrip(" "))
        expr_stmt = _sh_parse_expr_lowered(s, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
        pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "Expr", "source_span": _sh_stmt_span(merged_line_end, ln_no, expr_col, len(ln_txt)), "value": expr_stmt})
    return stmts


def _sh_parse_stmt_block(body_lines: list[tuple[int, str]], *, name_types: dict[str, str], scope_label: str) -> list[dict[str, Any]]:
    """読み取り専用引数で受け取り、mutable 実体へコピーを渡す。"""
    body_lines_copy: list[tuple[int, str]] = list(body_lines)
    name_types_copy: dict[str, str] = dict(name_types)
    return _sh_parse_stmt_block_mutable(body_lines_copy, name_types=name_types_copy, scope_label=scope_label)


def convert_source_to_east_self_hosted(source: str, filename: str) -> dict[str, Any]:
    """Python ソースを self-hosted パーサで EAST Module に変換する。"""
    source = _sh_strip_utf8_bom(source)
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
    type_aliases: dict[str, str] = _sh_default_type_aliases()

    cur_cls: str | None = None
    cur_cls_indent = 0
    for ln_no, ln in enumerate(lines, start=1):
        s = _sh_strip_inline_comment(ln.strip())
        if s == "":
            continue
        indent = len(ln) - len(ln.lstrip(" "))
        if cur_cls is not None and indent <= cur_cls_indent and not s.startswith("#"):
            cur_cls = None
        if cur_cls is None and indent == 0:
            m_import_from = re.match(r"^from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+import\s+(.+)$", s, flags=re.S)
            if m_import_from is not None:
                mod_txt = re.strip_group(m_import_from, 1)
                names_txt = re.strip_group(m_import_from, 2)
                if mod_txt == "typing":
                    raw_parts: list[str] = []
                    for p in names_txt.split(","):
                        p2: str = p.strip()
                        if p2 != "":
                            raw_parts.append(p2)
                    for part in raw_parts:
                        parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                        if parsed_alias is None:
                            continue
                        sym_txt, as_name = parsed_alias
                        alias_name = as_name if as_name != "" else sym_txt
                        target = _sh_typing_alias_to_type_name(sym_txt)
                        if target != "":
                            type_aliases[alias_name] = target
                continue
            asg_pre = _sh_split_top_level_assign(s)
            if asg_pre is not None:
                pre_left, pre_right = asg_pre
                _sh_register_type_alias(type_aliases, pre_left, pre_right)
                continue
        cls_hdr_info = _sh_parse_class_header_base_list(s)
        if cls_hdr_info is not None:
            cls_name_info, bases_info = cls_hdr_info
            if len(bases_info) > 1:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"multiple inheritance is not supported: class '{cls_name_info}'",
                    source_span=_sh_span(ln_no, 0, len(ln)),
                    hint="Use single inheritance (`class Child(Base):`) or composition.",
                )
        cls_hdr = _sh_parse_class_header(s)
        if cls_hdr is not None:
            cur_cls_name, cur_base = cls_hdr
            cur_cls = cur_cls_name
            cur_cls_indent = indent
            if cur_base != "":
                class_base[cur_cls_name] = cur_base
            else:
                class_base[cur_cls_name] = None
            if cur_cls_name not in class_method_return_types:
                empty_methods: dict[str, str] = {}
                class_method_return_types[cur_cls_name] = empty_methods
            continue
        if cur_cls is None:
            sig_line_scan, _inline_scan = _sh_split_def_header_and_inline_stmt(s)
            sig = _sh_parse_def_sig(ln_no, sig_line_scan)
            if sig is not None:
                fn_returns[str(sig["name"])] = str(sig["ret"])
            continue
        cur_cls_name: str = cur_cls
        sig_line_scan, _inline_scan = _sh_split_def_header_and_inline_stmt(s)
        sig = _sh_parse_def_sig(ln_no, sig_line_scan, in_class=cur_cls_name)
        if sig is not None:
            methods: dict[str, str] = class_method_return_types[cur_cls_name]
            methods[str(sig["name"])] = str(sig["ret"])
            class_method_return_types[cur_cls_name] = methods

    _sh_set_parse_context(fn_returns, class_method_return_types, class_base, type_aliases)

    body_items: list[dict[str, Any]] = []
    main_stmts: list[dict[str, Any]] = []
    import_module_bindings: dict[str, str] = {}
    import_symbol_bindings: dict[str, dict[str, str]] = {}
    import_bindings: list[dict[str, Any]] = []
    import_binding_names: set[str] = set()
    first_item_attached = False
    pending_dataclass = False

    top_lines: list[tuple[int, str]] = []
    line_idx = 1
    while line_idx <= len(lines):
        top_lines.append((line_idx, lines[line_idx - 1]))
        line_idx += 1
    top_merged_lines, top_merged_end = _sh_merge_logical_lines(top_lines)
    top_merged_map: dict[int, str] = {}
    top_merged_index: dict[int, int] = {}
    for top_idx, top_pair in enumerate(top_merged_lines):
        top_ln_no, top_txt = top_pair
        top_merged_map[int(top_ln_no)] = str(top_txt)
        top_merged_index[int(top_ln_no)] = int(top_idx)
    i = 1
    while i <= len(lines):
        ln_obj = top_merged_map.get(i, lines[i - 1])
        ln: str = str(ln_obj)
        logical_end_pair = top_merged_end.get(i, (i, len(lines[i - 1])))
        logical_end = int(logical_end_pair[0])
        raw_s = ln.strip()
        s = _sh_strip_inline_comment(raw_s)
        _sh_raise_if_trailing_stmt_terminator(s, line_no=i, line_text=ln)
        if s == "" or s.startswith("#"):
            i += 1
            continue
        if ln.startswith(" "):
            i += 1
            continue

        ln_main = s
        is_main_guard = False
        if ln_main.startswith("if ") and ln_main.endswith(":"):
            cond = ln_main[3:-1].strip()
            if cond in {
                "__name__ == \"__main__\"",
                "__name__ == '__main__'",
                "\"__main__\" == __name__",
                "'__main__' == __name__",
            }:
                is_main_guard = True
        if is_main_guard:
            block: list[tuple[int, str]] = []
            if i < len(top_lines):
                block, block_end_idx = _sh_collect_indented_block(top_lines, i, 0)
                j = block_end_idx + 1
            main_name_types: dict[str, str] = {}
            main_stmts = _sh_parse_stmt_block(block, name_types=main_name_types, scope_label="__main__")
            i = j
            continue
        sig_line_full: str = s
        sig_line, inline_fn_stmt = _sh_split_def_header_and_inline_stmt(sig_line_full)
        sig_end_line = logical_end
        sig = _sh_parse_def_sig(i, sig_line)
        if sig is not None:
            fn_name = str(sig["name"])
            fn_ret = str(sig["ret"])
            arg_types: dict[str, str] = dict(sig["arg_types"])
            arg_order: list[str] = list(sig["arg_order"])
            arg_defaults_raw_obj: Any = sig.get("arg_defaults")
            arg_defaults_raw: dict[str, Any] = arg_defaults_raw_obj if isinstance(arg_defaults_raw_obj, dict) else {}
            block: list[tuple[int, str]] = []
            j = sig_end_line + 1
            if inline_fn_stmt != "":
                block = [(i, "    " + inline_fn_stmt)]
                j = i + 1
            else:
                block, block_end_idx = _sh_collect_indented_block(top_lines, j - 1, 0)
                j = block_end_idx + 1
                if len(block) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser requires non-empty function body '{fn_name}'",
                        source_span=_sh_span(i, 0, len(sig_line)),
                        hint="Add return or assignment statements in function body.",
                    )
            stmts = _sh_parse_stmt_block(block, name_types=dict(arg_types), scope_label=fn_name)
            docstring, stmts = _sh_extract_leading_docstring(stmts)
            fn_ret = _sh_infer_return_type_for_untyped_def(fn_ret, stmts)
            yield_types = _sh_collect_yield_value_types(stmts)
            is_generator = len(yield_types) > 0
            fn_ret_effective = fn_ret
            yield_value_type = "unknown"
            if is_generator:
                fn_ret_effective, yield_value_type = _sh_make_generator_return_type(fn_ret, yield_types)
            arg_defaults: dict[str, Any] = {}
            arg_index_map: dict[str, int] = {}
            for arg_pos, arg_name in enumerate(arg_order):
                arg_index_map[arg_name] = int(arg_pos)
            arg_usage_map = _sh_build_arg_usage_map(arg_order, arg_types, stmts)
            for arg_name in arg_order:
                if arg_name in arg_defaults_raw:
                    default_obj: Any = arg_defaults_raw[arg_name]
                    default_txt: str = str(default_obj).strip()
                    if default_txt != "":
                        default_col = sig_line.find(default_txt)
                        if default_col < 0:
                            default_col = 0
                        arg_defaults[arg_name] = _sh_parse_expr_lowered(
                            default_txt,
                            ln_no=i,
                            col=default_col,
                            name_types=dict(arg_types),
                        )
            item: dict[str, Any] = {
                "kind": "FunctionDef",
                "name": fn_name,
                "original_name": fn_name,
                "source_span": {"lineno": i, "col": 0, "end_lineno": block[-1][0], "end_col": len(block[-1][1])},
                "arg_types": arg_types,
                "arg_order": arg_order,
                "arg_defaults": arg_defaults,
                "arg_index": arg_index_map,
                "return_type": fn_ret_effective,
                "arg_usage": arg_usage_map,
                "renamed_symbols": {},
                "leading_comments": [],
                "leading_trivia": [],
                "docstring": docstring,
                "body": stmts,
                "is_generator": 1 if is_generator else 0,
                "yield_value_type": yield_value_type,
            }
            fn_returns[fn_name] = fn_ret_effective
            _SH_FN_RETURNS[fn_name] = fn_ret_effective
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
            raw_parts: list[str] = []
            for p in names_txt.split(","):
                p2: str = p.strip()
                if p2 != "":
                    raw_parts.append(p2)
            if len(raw_parts) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="import statement has no module names",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Use `import module` or `import module as alias`.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=True)
                if parsed_alias is None:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"unsupported import clause: {part}",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `import module` or `import module as alias` form.",
                    )
                mod_name, as_name_txt = parsed_alias
                bind_name = as_name_txt if as_name_txt != "" else mod_name.split(".")[0]
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
                alias_item: dict[str, str | None] = {"name": mod_name, "asname": None}
                if as_name_txt != "":
                    alias_item["asname"] = as_name_txt
                aliases.append(alias_item)
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
                    raise _make_east_build_error(
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
                wildcard_local = "__wildcard__" + mod_name.replace(".", "_")
                _sh_append_import_binding(
                    import_bindings=import_bindings,
                    import_binding_names=import_binding_names,
                    module_id=mod_name,
                    export_name="*",
                    local_name=wildcard_local,
                    binding_kind="wildcard",
                    source_file=filename,
                    source_line=i,
                )
                body_items.append(
                    {
                        "kind": "ImportFrom",
                        "source_span": _sh_span(i, 0, len(ln)),
                        "module": mod_name,
                        "names": [{"name": "*", "asname": None}],
                        "level": 0,
                    }
                )
                i = logical_end + 1
                continue
            raw_parts: list[str] = []
            for p in names_txt.split(","):
                p2: str = p.strip()
                if p2 != "":
                    raw_parts.append(p2)
            if len(raw_parts) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="from-import statement has no symbol names",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Use `from module import name` form.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                if parsed_alias is None:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"unsupported from-import clause: {part}",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `from module import name` or `... as alias`.",
                )
                sym_name, as_name_txt = parsed_alias
                bind_name = as_name_txt if as_name_txt != "" else sym_name
                # `Enum/IntEnum/IntFlag` は class 定義の lowering で吸収されるため、
                # 依存ヘッダ解決用の ImportBinding には積まない。
                if not (mod_name == "pytra.std.enum" and sym_name in {"Enum", "IntEnum", "IntFlag"}):
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
                alias_item: dict[str, str | None] = {"name": sym_name, "asname": None}
                if as_name_txt != "":
                    alias_item["asname"] = as_name_txt
                aliases.append(alias_item)
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

        cls_hdr_info = _sh_parse_class_header_base_list(s)
        if cls_hdr_info is not None:
            cls_name_info, bases_info = cls_hdr_info
            if len(bases_info) > 1:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"multiple inheritance is not supported: class '{cls_name_info}'",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Use single inheritance (`class Child(Base):`) or composition.",
                )
        cls_hdr = _sh_parse_class_header(s)
        if cls_hdr is not None:
            cls_name, base = cls_hdr
            base_name = base
            is_enum_base = base_name in {"Enum", "IntEnum", "IntFlag"}
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
                raise _make_east_build_error(
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
                ln_no_raw, ln_txt_raw = class_block[k]
                ln_no = int(ln_no_raw)
                ln_txt: str = str(ln_txt_raw)
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
                    if s2 == "pass":
                        class_body.append(
                            {
                                "kind": "Pass",
                                "source_span": _sh_span(ln_no, 0, len(ln_txt)),
                            }
                        )
                        k += 1
                        continue
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
                    parsed_field = _sh_parse_typed_binding(s2, allow_dotted_name=False)
                    if parsed_field is not None:
                        fname, fty_txt, fdefault = parsed_field
                        fty = _sh_ann_to_type(fty_txt)
                        field_types[fname] = fty
                        val_node: dict[str, Any] | None = None
                        if fdefault != "":
                            fexpr_txt = fdefault.strip()
                            fexpr_col = ln_txt.find(fexpr_txt)
                            val_node = _sh_parse_expr_lowered(fexpr_txt, ln_no=ln_no, col=fexpr_col, name_types={})
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
                    class_assign = _sh_split_top_level_assign(s2)
                    if class_assign is not None:
                        fname, fexpr_txt = class_assign
                        fname = fname.strip()
                        fexpr_txt = fexpr_txt.strip()
                        if _sh_is_identifier(fname) and fexpr_txt != "":
                            name_col = ln_txt.find(fname)
                            if name_col < 0:
                                name_col = 0
                            expr_col = ln_txt.find(fexpr_txt, name_col + len(fname))
                            if expr_col < 0:
                                expr_col = name_col + len(fname) + 1
                            val_node = _sh_parse_expr_lowered(fexpr_txt, ln_no=ln_no, col=expr_col, name_types={})
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
                    if is_enum_base:
                        enum_assign = _sh_split_top_level_assign(s2)
                        if enum_assign is not None:
                            fname, fexpr_txt = enum_assign
                            fname = fname.strip()
                            fexpr_txt = fexpr_txt.strip()
                            if not _sh_is_identifier(fname) or fexpr_txt == "":
                                k += 1
                                continue
                            name_col = ln_txt.find(fname)
                            if name_col < 0:
                                name_col = 0
                            expr_col = ln_txt.find(fexpr_txt, name_col + len(fname))
                            if expr_col < 0:
                                expr_col = name_col + len(fname) + 1
                            val_node = _sh_parse_expr_lowered(fexpr_txt, ln_no=ln_no, col=expr_col, name_types={})
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
                    sig_line, inline_method_stmt = _sh_split_def_header_and_inline_stmt(s2)
                    sig = _sh_parse_def_sig(ln_no, sig_line, in_class=cls_name)
                    if sig is not None:
                        mname = str(sig["name"])
                        marg_types: dict[str, str] = dict(sig["arg_types"])
                        marg_order: list[str] = list(sig["arg_order"])
                        marg_defaults_raw_obj: Any = sig.get("arg_defaults")
                        marg_defaults_raw: dict[str, Any] = marg_defaults_raw_obj if isinstance(marg_defaults_raw_obj, dict) else {}
                        mret = str(sig["ret"])
                        method_block: list[tuple[int, str]] = []
                        m = k + 1
                        if inline_method_stmt != "":
                            method_block = [(ln_no, " " * (bind + 4) + inline_method_stmt)]
                        else:
                            while m < len(class_block):
                                n_pair: tuple[int, str] = class_block[m]
                                n_no: int = int(n_pair[0])
                                n_txt: str = str(n_pair[1])
                                if n_txt.strip() == "":
                                    t = m + 1
                                    while t < len(class_block) and class_block[t][1].strip() == "":
                                        t += 1
                                    if t >= len(class_block):
                                        break
                                    t_pair: tuple[int, str] = class_block[t]
                                    t_txt: str = str(t_pair[1])
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
                                raise _make_east_build_error(
                                    kind="unsupported_syntax",
                                    message=f"self_hosted parser requires non-empty method body '{cls_name}.{mname}'",
                                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                                    hint="Add method statements.",
                                )
                        local_types: dict[str, str] = dict(marg_types)
                        field_names: list[str] = list(field_types.keys())
                        for fnm in field_names:
                            fty: str = field_types[fnm]
                            local_types[fnm] = fty
                        stmts = _sh_parse_stmt_block(method_block, name_types=local_types, scope_label=f"{cls_name}.{mname}")
                        docstring, stmts = _sh_extract_leading_docstring(stmts)
                        mret = _sh_infer_return_type_for_untyped_def(mret, stmts)
                        yield_types = _sh_collect_yield_value_types(stmts)
                        is_generator = len(yield_types) > 0
                        mret_effective = mret
                        yield_value_type = "unknown"
                        if is_generator:
                            mret_effective, yield_value_type = _sh_make_generator_return_type(mret, yield_types)
                        marg_defaults: dict[str, Any] = {}
                        for arg_name in marg_order:
                            if arg_name in marg_defaults_raw:
                                default_obj: Any = marg_defaults_raw[arg_name]
                                default_txt: str = str(default_obj).strip()
                                if default_txt != "":
                                    default_col = ln_txt.find(default_txt)
                                    if default_col < 0:
                                        default_col = bind
                                    marg_defaults[arg_name] = _sh_parse_expr_lowered(
                                        default_txt,
                                        ln_no=ln_no,
                                        col=default_col,
                                        name_types=local_types,
                                    )
                        if mname == "__init__":
                            for st in stmts:
                                if st.get("kind") == "Assign":
                                    tgt = st.get("target")
                                    tgt_value: Any = None
                                    if isinstance(tgt, dict):
                                        tgt_value = tgt.get("value")
                                    tgt_value_dict: dict[str, Any] | None = None
                                    if isinstance(tgt_value, dict):
                                        tgt_value_dict = tgt_value
                                    if (
                                        isinstance(tgt, dict)
                                        and tgt.get("kind") == "Attribute"
                                        and tgt_value_dict is not None
                                        and tgt_value_dict.get("kind") == "Name"
                                        and tgt_value_dict.get("id") == "self"
                                    ):
                                        fname = str(tgt.get("attr", ""))
                                        if fname != "":
                                            st_value = st.get("value")
                                            st_value_rt: Any = None
                                            if isinstance(st_value, dict):
                                                st_value_rt = st_value.get("resolved_type")
                                            t_val: Any = st.get("decl_type")
                                            if not isinstance(t_val, str) or t_val == "":
                                                t_val = st_value_rt
                                            if isinstance(t_val, str) and t_val != "":
                                                field_types[fname] = t_val
                                if st.get("kind") == "AnnAssign":
                                    tgt = st.get("target")
                                    tgt_value: Any = None
                                    if isinstance(tgt, dict):
                                        tgt_value = tgt.get("value")
                                    tgt_value_dict: dict[str, Any] | None = None
                                    if isinstance(tgt_value, dict):
                                        tgt_value_dict = tgt_value
                                    if (
                                        isinstance(tgt, dict)
                                        and tgt.get("kind") == "Attribute"
                                        and tgt_value_dict is not None
                                        and tgt_value_dict.get("kind") == "Name"
                                        and tgt_value_dict.get("id") == "self"
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
                        arg_usage_map = _sh_build_arg_usage_map(marg_order, marg_types, stmts)
                        if cls_name in class_method_return_types:
                            methods_map = class_method_return_types[cls_name]
                            methods_map[mname] = mret_effective
                            class_method_return_types[cls_name] = methods_map
                        if cls_name in _SH_CLASS_METHOD_RETURNS:
                            methods_map2 = _SH_CLASS_METHOD_RETURNS[cls_name]
                            methods_map2[mname] = mret_effective
                            _SH_CLASS_METHOD_RETURNS[cls_name] = methods_map2
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
                                "return_type": mret_effective,
                                "arg_usage": arg_usage_map,
                                "renamed_symbols": {},
                                "decorators": list(pending_method_decorators),
                                "docstring": docstring,
                                "body": stmts,
                                "is_generator": 1 if is_generator else 0,
                                "yield_value_type": yield_value_type,
                            }
                        )
                        pending_method_decorators = []
                        k = m
                        continue
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse class statement: {s2}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use field annotation or method definitions in class body.",
                )

            storage_hint_override = class_storage_hint_override
            base_value: str | None = None
            if base != "":
                base_value = base

            cls_item: dict[str, Any] = {
                "kind": "ClassDef",
                "name": cls_name,
                "original_name": cls_name,
                "source_span": {"lineno": i, "col": 0, "end_lineno": block[-1][0], "end_col": len(block[-1][1])},
                "base": base_value,
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
            instance_field_names: set[str] = set()
            for field_name in field_types.keys():
                if field_name not in static_field_names:
                    instance_field_names.add(field_name)
            # conservative hint:
            # - classes with instance state / __del__ / inheritance should keep reference semantics
            # - stateless, non-inherited classes can be value candidates
            if storage_hint_override != "":
                cls_item["class_storage_hint"] = storage_hint_override
            elif base_name in {"Enum", "IntEnum", "IntFlag"}:
                cls_item["class_storage_hint"] = "value"
            elif len(instance_field_names) == 0 and not has_del and base == "":
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

        top_indent = len(ln) - len(ln.lstrip(" "))
        if s.startswith("if ") and s.endswith(":"):
            cur_idx_obj = top_merged_index.get(i)
            if isinstance(cur_idx_obj, int):
                cur_idx = int(cur_idx_obj)
                then_block, j_idx = _sh_collect_indented_block(top_merged_lines, cur_idx + 1, top_indent)
                if len(then_block) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="if body is missing in 'module'",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Add indented if-body.",
                    )
                _else_stmt_list, j_idx = _sh_parse_if_tail(
                    start_idx=j_idx,
                    parent_indent=top_indent,
                    body_lines=top_merged_lines,
                    name_types={},
                    scope_label="module",
                )
                stmt_chunk = top_merged_lines[cur_idx:j_idx]
                parsed_items = _sh_parse_stmt_block(stmt_chunk, name_types={}, scope_label="module")
                if not first_item_attached and len(parsed_items) > 0:
                    first_item = parsed_items[0]
                    if isinstance(first_item, dict):
                        first_item["leading_comments"] = list(leading_file_comments)
                        first_item["leading_trivia"] = list(leading_file_trivia)
                        first_item_attached = True
                for parsed_item in parsed_items:
                    body_items.append(parsed_item)
                if j_idx < len(top_merged_lines):
                    i = int(top_merged_lines[j_idx][0])
                else:
                    i = len(lines) + 1
                continue

        if s.startswith("for "):
            cur_idx_obj = top_merged_index.get(i)
            if isinstance(cur_idx_obj, int):
                cur_idx = int(cur_idx_obj)
                for_full = s[len("for ") :].strip()
                inline_for = False
                if not for_full.endswith(":"):
                    inline_for = _sh_split_top_level_colon(for_full) is not None
                j_idx = cur_idx + 1
                if for_full.endswith(":"):
                    body_block, j_idx = _sh_collect_indented_block(top_merged_lines, cur_idx + 1, top_indent)
                    if len(body_block) == 0:
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message="for body is missing in 'module'",
                            source_span=_sh_span(i, 0, len(ln)),
                            hint="Add indented for-body.",
                        )
                elif not inline_for:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse for statement: {s}",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `for target in iterable:` form.",
                    )
                stmt_chunk = top_merged_lines[cur_idx:j_idx]
                parsed_items = _sh_parse_stmt_block(stmt_chunk, name_types={}, scope_label="module")
                if not first_item_attached and len(parsed_items) > 0:
                    first_item = parsed_items[0]
                    if isinstance(first_item, dict):
                        first_item["leading_comments"] = list(leading_file_comments)
                        first_item["leading_trivia"] = list(leading_file_trivia)
                        first_item_attached = True
                for parsed_item in parsed_items:
                    body_items.append(parsed_item)
                if j_idx < len(top_merged_lines):
                    i = int(top_merged_lines[j_idx][0])
                else:
                    i = len(lines) + 1
                continue

        parsed_top_typed = _sh_parse_typed_binding(s, allow_dotted_name=False)
        if parsed_top_typed is not None:
            top_name, top_ann, top_default = parsed_top_typed
        else:
            top_name, top_ann, top_default = "", "", ""
        if parsed_top_typed is not None and top_default != "":
            name = top_name
            ann_txt = top_ann
            expr_txt = top_default
            ann = _sh_ann_to_type(ann_txt)
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
                    "value": _sh_parse_expr_lowered(expr_txt, ln_no=i, col=expr_col, name_types={}),
                    "declare": True,
                    "decl_type": ann,
                }
            )
            i = logical_end + 1
            continue

        asg_top = _sh_split_top_level_assign(s)
        if asg_top is not None:
            asg_left, asg_right = asg_top
            target_txt = asg_left.strip()
            expr_txt = asg_right.strip()
            expr_col = ln.find(expr_txt)
            if expr_col < 0:
                expr_col = 0
            target_col = ln.find(target_txt)
            if target_col < 0:
                target_col = 0
            target_node = _sh_parse_expr_lowered(target_txt, ln_no=i, col=target_col, name_types={})
            val_node = _sh_parse_expr_lowered(expr_txt, ln_no=i, col=expr_col, name_types={})
            decl_type = str(val_node.get("resolved_type", "unknown"))
            declare_name = isinstance(target_node, dict) and target_node.get("kind") == "Name"
            assign_item: dict[str, Any] = {
                "kind": "Assign",
                "source_span": _sh_span(i, target_col, len(ln)),
                "target": target_node,
                "value": val_node,
                "declare": declare_name,
                "decl_type": decl_type if declare_name else None,
            }
            if declare_name:
                assign_item["declare_init"] = True
            body_items.append(
                assign_item
            )
            i = logical_end + 1
            continue

        if (s.startswith('"""') and s.endswith('"""')) or (s.startswith("'''") and s.endswith("'''")):
            # Module-level docstring / standalone string expression.
            body_items.append(
                {
                    "kind": "Expr",
                    "source_span": _sh_span(i, 0, len(ln)),
                    "value": _sh_parse_expr_lowered(s, ln_no=i, col=0, name_types={}),
                }
            )
            i = logical_end + 1
            continue

        expr_col = len(ln) - len(ln.lstrip(" "))
        body_items.append(
            {
                "kind": "Expr",
                "source_span": _sh_span(i, expr_col, len(ln)),
                "value": _sh_parse_expr_lowered(s, ln_no=i, col=expr_col, name_types={}),
            }
        )
        i = logical_end + 1
        continue

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
        module_id: str = ""
        if isinstance(module_id_obj, str):
            module_id = module_id_obj
        local_name: str = ""
        if isinstance(local_name_obj, str):
            local_name = local_name_obj
        export_name: str = ""
        if isinstance(export_name_obj, str):
            export_name = export_name_obj
        binding_kind: str = ""
        if isinstance(binding_kind_obj, str):
            binding_kind = binding_kind_obj
        if module_id == "" or local_name == "":
            continue
        if binding_kind == "module":
            import_module_bindings[local_name] = module_id
            continue
        if binding_kind == "symbol" and export_name != "":
            sym_binding: dict[str, str] = {}
            sym_binding["module"] = module_id
            sym_binding["name"] = export_name
            import_symbol_bindings[local_name] = sym_binding
            qref: dict[str, str] = {}
            qref["module_id"] = module_id
            qref["symbol"] = export_name
            qref["local_name"] = local_name
            qualified_symbol_refs.append(qref)

    source_span: dict[str, Any] = {}
    source_span["lineno"] = None
    source_span["col"] = None
    source_span["end_lineno"] = None
    source_span["end_col"] = None

    meta: dict[str, Any] = {}
    meta["parser_backend"] = "self_hosted"
    meta["import_bindings"] = import_bindings
    meta["qualified_symbol_refs"] = qualified_symbol_refs
    meta["import_modules"] = import_module_bindings
    meta["import_symbols"] = import_symbol_bindings

    out: dict[str, Any] = {}
    out["kind"] = "Module"
    out["source_path"] = filename
    out["source_span"] = source_span
    out["body"] = body_items
    out["main_guard_body"] = main_stmts
    out["renamed_symbols"] = renamed_symbols
    out["meta"] = meta
    return out


def convert_source_to_east_with_backend(source: str, filename: str, parser_backend: str = "self_hosted") -> dict[str, Any]:
    """指定バックエンドでソースを EAST へ変換する統一入口。"""
    if parser_backend != "self_hosted":
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message=f"unknown parser backend: {parser_backend}",
            source_span={},
            hint="Use parser_backend=self_hosted.",
        )
    return convert_source_to_east_self_hosted(source, filename)


def convert_path(input_path: Path, parser_backend: str = "self_hosted") -> dict[str, Any]:
    """Python ファイルを読み込み、EAST ドキュメントへ変換する。"""
    source = input_path.read_text(encoding="utf-8")
    return convert_source_to_east_with_backend(source, str(input_path), parser_backend=parser_backend)
