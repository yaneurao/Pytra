#!/usr/bin/env python3
"""Python source -> EAST converter (self-hosted parser only)."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any


BorrowKind = str  # "value" | "readonly_ref" | "mutable_ref" | "move"
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


@dataclass
class EastBuildError(Exception):
    """EAST generation error with contract fields."""

    kind: str
    message: str
    source_span: dict[str, int | None]
    hint: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "message": self.message,
            "source_span": self.source_span,
            "hint": self.hint,
        }


def convert_source_to_east(source: str, filename: str) -> dict[str, Any]:
    """Backward-compatible alias; self-hosted parser only."""
    return convert_source_to_east_self_hosted(source, filename)

def _sh_span(line: int, col: int, end_col: int) -> dict[str, int]:
    return {"lineno": line, "col": col, "end_lineno": line, "end_col": end_col}


def _sh_ann_to_type(ann: str) -> str:
    mapping = {
        "int": "int64",
        "float": "float64",
        "bool": "bool",
        "str": "str",
        "None": "None",
        "bytes": "list[uint8]",
        "bytearray": "list[uint8]",
    }
    txt = ann.strip()
    if txt in mapping:
        return mapping[txt]
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\[(.*)\]$", txt)
    if m is None:
        return txt
    head = m.group(1)
    inner = m.group(2).strip()
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
        out: list[dict[str, Any]] = []
        i = 0
        while i < len(text):
            ch = text[i]
            if ch.isspace():
                i += 1
                continue
            if ch.isdigit():
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
                q3 = text[i : i + 3]
                j = i + 3
                while j + 2 < len(text):
                    if text[j : j + 3] == q3:
                        j += 3
                        break
                    j += 1
                if j > len(text) or text[j - 3 : j] != q3:
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message="unterminated triple-quoted string literal in self_hosted parser",
                        source_span=_sh_span(self.line_no, self.col_base + i, self.col_base + len(text)),
                        hint="Close triple-quoted string with matching quote.",
                    )
                out.append({"k": "STR", "v": text[i:j], "s": i, "e": j})
                i = j
                continue
            if ch in {"'", '"'}:
                q = ch
                j = i + 1
                while j < len(text):
                    if text[j] == "\\":
                        j += 2
                        continue
                    if text[j] == q:
                        j += 1
                        break
                    j += 1
                if j > len(text) or text[j - 1] != q:
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message="unterminated string literal in self_hosted parser",
                        source_span=_sh_span(self.line_no, self.col_base + i, self.col_base + len(text)),
                        hint="Close string literal with matching quote.",
                    )
                out.append({"k": "STR", "v": text[i:j], "s": i, "e": j})
                i = j
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
        return self.tokens[self.pos]

    def _eat(self, kind: str | None = None) -> dict[str, Any]:
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
        return _sh_span(self.line_no, self.col_base + s, self.col_base + e)

    def _src_slice(self, s: int, e: int) -> str:
        return self.src[s:e].strip()

    def parse(self) -> dict[str, Any]:
        node = self._parse_or()
        self._eat("EOF")
        return node

    def _parse_or(self) -> dict[str, Any]:
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
        node = self._parse_bitxor()
        while self._cur()["k"] == "|":
            op_tok = self._eat()
            right = self._parse_bitxor()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_bitxor(self) -> dict[str, Any]:
        node = self._parse_bitand()
        while self._cur()["k"] == "^":
            op_tok = self._eat()
            right = self._parse_bitand()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_bitand(self) -> dict[str, Any]:
        node = self._parse_shift()
        while self._cur()["k"] == "&":
            op_tok = self._eat()
            right = self._parse_shift()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_shift(self) -> dict[str, Any]:
        node = self._parse_addsub()
        while self._cur()["k"] in {"<<", ">>"}:
            op_tok = self._eat()
            right = self._parse_addsub()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_addsub(self) -> dict[str, Any]:
        node = self._parse_muldiv()
        while self._cur()["k"] in {"+", "-"}:
            op_tok = self._eat()
            right = self._parse_muldiv()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_muldiv(self) -> dict[str, Any]:
        node = self._parse_unary()
        while self._cur()["k"] in {"*", "/", "//", "%"}:
            op_tok = self._eat()
            right = self._parse_unary()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_unary(self) -> dict[str, Any]:
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
        cur: str | None = cls_name
        while cur is not None:
            methods = self.class_method_return_types.get(cur, {})
            if method in methods:
                return methods[method]
            cur = self.class_base.get(cur)
        return "unknown"

    def _parse_postfix(self) -> dict[str, Any]:
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
                attr_t = "unknown"
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
                                kw_val = self._parse_or()
                                keywords.append({"arg": str(name_tok["v"]), "value": kw_val})
                            else:
                                self.pos = save_pos
                                args.append(self._parse_or())
                        else:
                            args.append(self._parse_or())
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
                    elif fn_name in {"Exception", "RuntimeError"}:
                        call_ret = "Exception"
                    elif fn_name in self.fn_return_types:
                        call_ret = self.fn_return_types[fn_name]
                    elif fn_name in self.class_method_return_types:
                        call_ret = fn_name
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
                node = {
                    "kind": "Subscript",
                    "source_span": self._node_span(s, e),
                    "resolved_type": "unknown",
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": self._src_slice(s, e),
                    "value": node,
                    "slice": first,
                }
                continue
            return node

    def _make_bin(self, left: dict[str, Any], op_sym: str, right: dict[str, Any]) -> dict[str, Any]:
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
                "value": int(tok["v"]),
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
            raw = tok["v"]
            return {
                "kind": "Constant",
                "source_span": self._node_span(tok["s"], tok["e"]),
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
                "repr": raw,
                "value": raw[1:-1],
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
            first = self._parse_or()
            if self._cur()["k"] == ",":
                elements = [first]
                while self._cur()["k"] == ",":
                    self._eat(",")
                    if self._cur()["k"] == ")":
                        break
                    elements.append(self._parse_or())
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
                first = self._parse_or()
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
                    iter_expr = self._parse_or()
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
                        ifs.append(self._parse_or())
                    r = self._eat("]")
                    tgt_name = str(tgt_tok["v"])
                    return {
                        "kind": "ListComp",
                        "source_span": self._node_span(l["s"], r["e"]),
                        "resolved_type": f"list[{str(first.get('resolved_type', 'unknown'))}]",
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": self._src_slice(l["s"], r["e"]),
                        "elt": first,
                        "generators": [
                            {
                                "target": {
                                    "kind": "Name",
                                    "source_span": self._node_span(tgt_tok["s"], tgt_tok["e"]),
                                    "resolved_type": "unknown",
                                    "borrow_kind": "value",
                                    "casts": [],
                                    "repr": tgt_name,
                                    "id": tgt_name,
                                },
                                "iter": iter_expr,
                                "ifs": ifs,
                            }
                        ],
                    }

                elements.append(first)
                while True:
                    if self._cur()["k"] == ",":
                        self._eat(",")
                        if self._cur()["k"] == "]":
                            break
                        elements.append(self._parse_or())
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
            first = self._parse_or()
            if self._cur()["k"] == ":":
                keys = [first]
                vals: list[dict[str, Any]] = []
                self._eat(":")
                vals.append(self._parse_or())
                while self._cur()["k"] == ",":
                    self._eat(",")
                    if self._cur()["k"] == "}":
                        break
                    keys.append(self._parse_or())
                    self._eat(":")
                    vals.append(self._parse_or())
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
                elements.append(self._parse_or())
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


def convert_source_to_east_self_hosted(source: str, filename: str) -> dict[str, Any]:
    """Self-hosted parser path for the growing EAST subset."""
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

    def parse_def_sig(ln_no: int, ln: str, *, in_class: str | None = None) -> dict[str, Any] | None:
        m_def = re.match(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\((.*)\)\s*(?:->\s*(.+)\s*)?:\s*$", ln)
        if m_def is None:
            return None
        arg_types: dict[str, str] = {}
        args_raw = m_def.group(2)
        if args_raw.strip() != "":
            for p_txt, _off in _sh_split_args_with_offsets(args_raw):
                p = p_txt.strip()
                if p == "":
                    continue
                if in_class is not None and p == "self":
                    arg_types["self"] = in_class
                    continue
                if ":" not in p:
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse parameter: {p_txt}",
                        source_span=_sh_span(ln_no, 0, len(ln)),
                        hint="Use `name: Type` style parameters.",
                    )
                pn, pt = p.split(":", 1)
                pn = pn.strip()
                pt = pt.strip()
                if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", pn):
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse parameter name: {pn}",
                        source_span=_sh_span(ln_no, 0, len(ln)),
                        hint="Use valid identifier for parameter name.",
                    )
                if pt == "":
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse parameter type: {p_txt}",
                        source_span=_sh_span(ln_no, 0, len(ln)),
                        hint="Use `name: Type` style parameters.",
                    )
                arg_types[pn] = _sh_ann_to_type(pt)
        return {
            "name": m_def.group(1),
            "ret": _sh_ann_to_type(m_def.group(3).strip()) if m_def.group(3) is not None else "None",
            "arg_types": arg_types,
        }

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
        m_cls = re.match(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\(([A-Za-z_][A-Za-z0-9_]*)\))?\s*:\s*$", ln)
        if m_cls is not None:
            cur_cls = m_cls.group(1)
            cur_cls_indent = indent
            class_base[cur_cls] = m_cls.group(2)
            class_method_return_types.setdefault(cur_cls, {})
            continue
        if cur_cls is None:
            sig = parse_def_sig(ln_no, ln)
            if sig is not None:
                fn_returns[str(sig["name"])] = str(sig["ret"])
            continue
        sig = parse_def_sig(ln_no, ln, in_class=cur_cls)
        if sig is not None:
            class_method_return_types[cur_cls][str(sig["name"])] = str(sig["ret"])

    def split_top_commas(txt: str) -> list[str]:
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

    def parse_expr(expr_txt: str, *, ln_no: int, col: int, name_types: dict[str, str]) -> dict[str, Any]:
        raw = expr_txt
        txt = raw.strip()

        def split_top_keyword(text: str, kw: str) -> int:
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

        # if-expression: a if cond else b
        p_if = split_top_keyword(txt, "if")
        p_else = split_top_keyword(txt, "else")
        if p_if >= 0 and p_else > p_if:
            body_txt = txt[:p_if].strip()
            test_txt = txt[p_if + 2 : p_else].strip()
            else_txt = txt[p_else + 4 :].strip()
            body_node = parse_expr(body_txt, ln_no=ln_no, col=col + txt.find(body_txt), name_types=dict(name_types))
            test_node = parse_expr(test_txt, ln_no=ln_no, col=col + txt.find(test_txt), name_types=dict(name_types))
            else_node = parse_expr(else_txt, ln_no=ln_no, col=col + txt.rfind(else_txt), name_types=dict(name_types))
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

        def split_top_plus(text: str) -> list[str]:
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

        # Handle concatenation chains that include f-strings before generic parsing.
        plus_parts = split_top_plus(txt)
        if len(plus_parts) >= 2 and any(p.startswith("f\"") or p.startswith("f'") for p in plus_parts):
            nodes = [parse_expr(p, ln_no=ln_no, col=col + txt.find(p), name_types=dict(name_types)) for p in plus_parts]
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

        # dict literal: {"a": 1, "b": 2}
        if txt.startswith("{") and txt.endswith("}") and ":" in txt:
            inner = txt[1:-1].strip()
            entries: list[dict[str, Any]] = []
            if inner != "":
                for part in split_top_commas(inner):
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
                            "key": parse_expr(ktxt, ln_no=ln_no, col=col + txt.find(ktxt), name_types=dict(name_types)),
                            "value": parse_expr(vtxt, ln_no=ln_no, col=col + txt.find(vtxt), name_types=dict(name_types)),
                        }
                    )
            kt = "unknown"
            vt = "unknown"
            if len(entries) > 0:
                kt = str(entries[0]["key"].get("resolved_type", "unknown"))
                vt = str(entries[0]["value"].get("resolved_type", "unknown"))
            return {
                "kind": "Dict",
                "source_span": _sh_span(ln_no, col, col + len(raw)),
                "resolved_type": f"dict[{kt},{vt}]",
                "borrow_kind": "value",
                "casts": [],
                "repr": txt,
                "entries": entries,
            }

        # Very simple list-comp support: [x for x in <iter>]
        m_lc = re.match(r"^\[\s*([A-Za-z_][A-Za-z0-9_]*)\s+for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.+)\]$", txt)
        if m_lc is not None:
            elt_name = m_lc.group(1)
            tgt_name = m_lc.group(2)
            iter_txt = m_lc.group(3).strip()
            iter_node = parse_expr(iter_txt, ln_no=ln_no, col=col + txt.find(iter_txt), name_types=dict(name_types))
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
                    tail = inner[i:]
                    if tail != "":
                        values.append(
                            {
                                "kind": "Constant",
                                "source_span": _sh_span(ln_no, col, col + len(raw)),
                                "resolved_type": "str",
                                "borrow_kind": "value",
                                "casts": [],
                                "repr": repr(tail),
                                "value": tail,
                            }
                        )
                    break
                if j > i:
                    lit = inner[i:j]
                    values.append(
                        {
                            "kind": "Constant",
                            "source_span": _sh_span(ln_no, col, col + len(raw)),
                            "resolved_type": "str",
                            "borrow_kind": "value",
                            "casts": [],
                            "repr": repr(lit),
                            "value": lit,
                        }
                    )
                k = inner.find("}", j + 1)
                if k < 0:
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message="unterminated f-string placeholder in self_hosted parser",
                        source_span=_sh_span(ln_no, col, col + len(raw)),
                        hint="Close f-string placeholder with `}`.",
                    )
                inner_expr = inner[j + 1 : k].strip()
                values.append({"kind": "FormattedValue", "value": parse_expr(inner_expr, ln_no=ln_no, col=col, name_types=dict(name_types))})
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

        tuple_parts = split_top_commas(txt)
        if len(tuple_parts) >= 2:
            elems = [parse_expr(p, ln_no=ln_no, col=col + txt.find(p), name_types=dict(name_types)) for p in tuple_parts]
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
            fn_return_types=fn_returns,
            class_method_return_types=class_method_return_types,
            class_base=class_base,
        )

    def parse_stmt_block(body_lines: list[tuple[int, str]], *, name_types: dict[str, str], scope_label: str) -> list[dict[str, Any]]:
        def bracket_delta(txt: str) -> int:
            depth = 0
            in_str: str | None = None
            esc = False
            i = 0
            while i < len(txt):
                ch = txt[i]
                if in_str is not None:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == in_str:
                        if i + 2 < len(txt) and txt[i : i + 3] == in_str * 3:
                            i += 2
                        else:
                            in_str = None
                    i += 1
                    continue
                if i + 2 < len(txt) and txt[i : i + 3] in {"'''", '"""'}:
                    in_str = txt[i]
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
                elif ch in {")", "]", "}"}:
                    depth -= 1
                i += 1
            return depth

        merged_lines: list[tuple[int, str]] = []
        k = 0
        while k < len(body_lines):
            ln_no, ln_txt = body_lines[k]
            acc = ln_txt
            d = bracket_delta(ln_txt)
            while d > 0 and k + 1 < len(body_lines):
                k += 1
                acc += " " + body_lines[k][1].strip()
                d += bracket_delta(body_lines[k][1])
            merged_lines.append((ln_no, acc))
            k += 1
        body_lines = merged_lines

        stmts: list[dict[str, Any]] = []

        def collect_indented_block(start: int, parent_indent: int) -> tuple[list[tuple[int, str]], int]:
            out: list[tuple[int, str]] = []
            j = start
            while j < len(body_lines):
                n_no, n_ln = body_lines[j]
                if n_ln.strip() == "":
                    j += 1
                    continue
                n_indent = len(n_ln) - len(n_ln.lstrip(" "))
                if n_indent <= parent_indent:
                    break
                out.append((n_no, n_ln))
                j += 1
            return out, j

        def split_top_level_assign(text: str) -> tuple[str, str] | None:
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

        def strip_inline_comment(text: str) -> str:
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

        i = 0
        while i < len(body_lines):
            ln_no, ln_txt = body_lines[i]
            indent = len(ln_txt) - len(ln_txt.lstrip(" "))
            s = strip_inline_comment(ln_txt.strip())

            if s == "" or s.startswith("#"):
                i += 1
                continue

            if s.startswith("if ") and s.endswith(":"):
                def parse_if_tail(start_idx: int, parent_indent: int) -> tuple[list[dict[str, Any]], int]:
                    if start_idx >= len(body_lines):
                        return [], start_idx
                    t_no, t_ln = body_lines[start_idx]
                    t_indent = len(t_ln) - len(t_ln.lstrip(" "))
                    t_s = t_ln.strip()
                    if t_indent != parent_indent:
                        return [], start_idx
                    if t_s == "else:":
                        else_block, k2 = collect_indented_block(start_idx + 1, parent_indent)
                        if len(else_block) == 0:
                            raise EastBuildError(
                                kind="unsupported_syntax",
                                message=f"else body is missing in '{scope_label}'",
                                source_span=_sh_span(t_no, 0, len(t_ln)),
                                hint="Add indented else-body.",
                            )
                        return parse_stmt_block(else_block, name_types=dict(name_types), scope_label=scope_label), k2
                    if t_s.startswith("elif ") and t_s.endswith(":"):
                        cond_txt2 = t_s[len("elif ") : -1].strip()
                        cond_col2 = t_ln.find(cond_txt2)
                        cond_expr2 = parse_expr(cond_txt2, ln_no=t_no, col=cond_col2, name_types=dict(name_types))
                        elif_block, k2 = collect_indented_block(start_idx + 1, parent_indent)
                        if len(elif_block) == 0:
                            raise EastBuildError(
                                kind="unsupported_syntax",
                                message=f"elif body is missing in '{scope_label}'",
                                source_span=_sh_span(t_no, 0, len(t_ln)),
                                hint="Add indented elif-body.",
                            )
                        nested_orelse, k3 = parse_if_tail(k2, parent_indent)
                        return [
                            {
                                "kind": "If",
                                "source_span": _sh_span(t_no, t_ln.find("elif "), len(t_ln)),
                                "test": cond_expr2,
                                "body": parse_stmt_block(elif_block, name_types=dict(name_types), scope_label=scope_label),
                                "orelse": nested_orelse,
                            }
                        ], k3
                    return [], start_idx

                cond_txt = s[len("if ") : -1].strip()
                cond_col = ln_txt.find(cond_txt)
                cond_expr = parse_expr(cond_txt, ln_no=ln_no, col=cond_col, name_types=dict(name_types))
                then_block, j = collect_indented_block(i + 1, indent)
                if len(then_block) == 0:
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message=f"if body is missing in '{scope_label}'",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Add indented if-body.",
                    )
                else_stmt_list, j = parse_if_tail(j, indent)
                stmts.append(
                    {
                        "kind": "If",
                        "source_span": _sh_span(ln_no, ln_txt.find("if "), len(ln_txt)),
                        "test": cond_expr,
                        "body": parse_stmt_block(then_block, name_types=dict(name_types), scope_label=scope_label),
                        "orelse": else_stmt_list,
                    }
                )
                i = j
                continue

            if s.startswith("for ") and s.endswith(":"):
                m_for = re.match(r"^for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.+):$", s)
                if m_for is None:
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse for statement: {s}",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use `for name in iterable:` form.",
                    )
                tgt = m_for.group(1)
                iter_txt = m_for.group(2).strip()
                iter_col = ln_txt.find(iter_txt)
                iter_expr = parse_expr(iter_txt, ln_no=ln_no, col=iter_col, name_types=dict(name_types))
                body_block, j = collect_indented_block(i + 1, indent)
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
                if t_ty != "unknown":
                    name_types[tgt] = t_ty
                if (
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
                    name_types[tgt] = "int64"
                    step_const = step_node.get("value") if isinstance(step_node, dict) else None
                    mode = "dynamic"
                    if step_const == 1:
                        mode = "ascending"
                    elif step_const == -1:
                        mode = "descending"
                    stmts.append(
                        {
                            "kind": "ForRange",
                            "source_span": _sh_span(ln_no, 0, len(ln_txt)),
                            "target": {
                                "kind": "Name",
                                "source_span": _sh_span(ln_no, ln_txt.find(tgt), ln_txt.find(tgt) + len(tgt)),
                                "resolved_type": "int64",
                                "borrow_kind": "value",
                                "casts": [],
                                "repr": tgt,
                                "id": tgt,
                            },
                            "target_type": "int64",
                            "start": start_node,
                            "stop": stop_node,
                            "step": step_node,
                            "range_mode": mode,
                            "body": parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                            "orelse": [],
                        }
                    )
                    i = j
                    continue
                stmts.append(
                    {
                        "kind": "For",
                        "source_span": _sh_span(ln_no, 0, len(ln_txt)),
                        "target": {
                            "kind": "Name",
                            "source_span": _sh_span(ln_no, ln_txt.find(tgt), ln_txt.find(tgt) + len(tgt)),
                            "resolved_type": name_types.get(tgt, "unknown"),
                            "borrow_kind": "value",
                            "casts": [],
                            "repr": tgt,
                            "id": tgt,
                        },
                        "target_type": name_types.get(tgt, "unknown"),
                        "iter": iter_expr,
                        "body": parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                        "orelse": [],
                    }
                )
                i = j
                continue

            if s.startswith("while ") and s.endswith(":"):
                cond_txt = s[len("while ") : -1].strip()
                cond_col = ln_txt.find(cond_txt)
                cond_expr = parse_expr(cond_txt, ln_no=ln_no, col=cond_col, name_types=dict(name_types))
                body_block, j = collect_indented_block(i + 1, indent)
                if len(body_block) == 0:
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message=f"while body is missing in '{scope_label}'",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Add indented while-body.",
                    )
                stmts.append(
                    {
                        "kind": "While",
                        "source_span": _sh_span(ln_no, 0, len(ln_txt)),
                        "test": cond_expr,
                        "body": parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                        "orelse": [],
                    }
                )
                i = j
                continue

            if s == "try:":
                try_body, j = collect_indented_block(i + 1, indent)
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
                    m_exc = re.match(r"^except\s+([A-Za-z_][A-Za-z0-9_]*)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$", h_s)
                    if m_exc is not None:
                        ex_type = m_exc.group(1)
                        ex_name = m_exc.group(2)
                        h_body, k = collect_indented_block(j + 1, indent)
                        handlers.append(
                            {
                                "kind": "ExceptHandler",
                                "type": {
                                    "kind": "Name",
                                    "source_span": _sh_span(h_no, h_ln.find(ex_type), h_ln.find(ex_type) + len(ex_type)),
                                    "resolved_type": "unknown",
                                    "borrow_kind": "value",
                                    "casts": [],
                                    "repr": ex_type,
                                    "id": ex_type,
                                },
                                "name": ex_name,
                                "body": parse_stmt_block(h_body, name_types=dict(name_types), scope_label=scope_label),
                            }
                        )
                        j = k
                        continue
                    if h_s == "finally:":
                        f_body, k = collect_indented_block(j + 1, indent)
                        finalbody = parse_stmt_block(f_body, name_types=dict(name_types), scope_label=scope_label)
                        j = k
                        continue
                    break
                stmts.append(
                    {
                        "kind": "Try",
                        "source_span": _sh_span(ln_no, 0, len(ln_txt)),
                        "body": parse_stmt_block(try_body, name_types=dict(name_types), scope_label=scope_label),
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
                stmts.append(
                    {
                        "kind": "Raise",
                        "source_span": _sh_span(ln_no, ln_txt.find("raise "), len(ln_txt)),
                        "exc": parse_expr(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types)),
                    }
                )
                i += 1
                continue

            if s == "pass":
                stmts.append({"kind": "Pass", "source_span": _sh_span(ln_no, indent, indent + 4)})
                i += 1
                continue

            if s.startswith("return "):
                rcol = ln_txt.find("return ")
                expr_txt = ln_txt[rcol + len("return ") :].strip()
                expr_col = ln_txt.find(expr_txt, rcol + len("return "))
                stmts.append(
                    {
                        "kind": "Return",
                        "source_span": _sh_span(ln_no, rcol, len(ln_txt)),
                        "value": parse_expr(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types)),
                    }
                )
                i += 1
                continue

            m_ann_decl = re.match(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:\s*(.+)$", s)
            if m_ann_decl is not None and "=" not in s:
                target_txt = m_ann_decl.group(1)
                ann = _sh_ann_to_type(m_ann_decl.group(2))
                target_col = ln_txt.find(target_txt)
                target_expr = parse_expr(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
                if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                    name_types[str(target_expr.get("id", ""))] = ann
                stmts.append(
                    {
                        "kind": "AnnAssign",
                        "source_span": _sh_span(ln_no, target_col, len(ln_txt)),
                        "target": target_expr,
                        "annotation": ann,
                        "value": None,
                        "declare": True,
                        "decl_type": ann,
                    }
                )
                i += 1
                continue

            m_ann = re.match(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:\s*([^=]+?)\s*=\s*(.+)$", s)
            if m_ann is not None:
                target_txt = m_ann.group(1)
                ann = _sh_ann_to_type(m_ann.group(2))
                expr_txt = m_ann.group(3).strip()
                expr_col = ln_txt.find(expr_txt)
                val_expr = parse_expr(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
                target_col = ln_txt.find(target_txt)
                target_expr = parse_expr(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
                if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                    name_types[str(target_expr.get("id", ""))] = ann
                stmts.append(
                    {
                        "kind": "AnnAssign",
                        "source_span": _sh_span(ln_no, target_col, len(ln_txt)),
                        "target": target_expr,
                        "annotation": ann,
                        "value": val_expr,
                        "declare": True,
                        "decl_type": ann,
                    }
                )
                i += 1
                continue

            m_aug = re.match(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*(\+=|-=|\*=|/=)\s*(.+)$", s)
            if m_aug is not None:
                target_txt = m_aug.group(1)
                op_map = {"+=": "Add", "-=": "Sub", "*=": "Mult", "/=": "Div"}
                expr_txt = m_aug.group(3).strip()
                expr_col = ln_txt.find(expr_txt)
                target_col = ln_txt.find(target_txt)
                target_expr = parse_expr(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
                val_expr = parse_expr(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
                target_ty = "unknown"
                if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                    target_ty = name_types.get(str(target_expr.get("id", "")), "unknown")
                stmts.append(
                    {
                        "kind": "AugAssign",
                        "source_span": _sh_span(ln_no, target_col, len(ln_txt)),
                        "target": target_expr,
                        "op": op_map[m_aug.group(2)],
                        "value": val_expr,
                        "declare": False,
                        "decl_type": target_ty if target_ty != "unknown" else None,
                    }
                )
                i += 1
                continue

            m_tasg = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", s)
            if m_tasg is not None:
                n1 = m_tasg.group(1)
                n2 = m_tasg.group(2)
                expr_txt = m_tasg.group(3).strip()
                expr_col = ln_txt.find(expr_txt)
                rhs = parse_expr(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
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
                    stmts.append(
                        {
                            "kind": "Swap",
                            "source_span": _sh_span(ln_no, c1, len(ln_txt)),
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
                stmts.append(
                    {
                        "kind": "Assign",
                        "source_span": _sh_span(ln_no, c1, len(ln_txt)),
                        "target": target_expr,
                        "value": rhs,
                        "declare": False,
                        "decl_type": None,
                    }
                )
                i += 1
                continue

            asg_split = split_top_level_assign(s)
            if asg_split is not None:
                target_txt, expr_txt = asg_split
                expr_col = ln_txt.find(expr_txt)
                target_col = ln_txt.find(target_txt)
                target_expr = parse_expr(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
                val_expr = parse_expr(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
                decl_type = val_expr.get("resolved_type", "unknown")
                if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                    nm = str(target_expr.get("id", ""))
                    if nm != "":
                        name_types[nm] = str(decl_type)
                stmts.append(
                    {
                        "kind": "Assign",
                        "source_span": _sh_span(ln_no, target_col, len(ln_txt)),
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
            expr_stmt = parse_expr(s, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            stmts.append({"kind": "Expr", "source_span": _sh_span(ln_no, expr_col, len(ln_txt)), "value": expr_stmt})
            i += 1
        return stmts

    body_items: list[dict[str, Any]] = []
    main_stmts: list[dict[str, Any]] = []
    first_item_attached = False
    pending_dataclass = False

    i = 1
    while i <= len(lines):
        ln = lines[i - 1]
        s = ln.strip()
        if s == "" or s.startswith("#"):
            i += 1
            continue
        if ln.startswith(" "):
            i += 1
            continue

        m_main = re.match(r"^if\s+__name__\s*==\s*[\"']__main__[\"']\s*:\s*$", ln)
        if m_main is not None:
            block: list[tuple[int, str]] = []
            j = i + 1
            while j <= len(lines):
                bl = lines[j - 1]
                if bl.strip() == "":
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
        sig_end_line = i
        if s.startswith("def ") and not s.endswith(":"):
            j = i + 1
            merged = s
            while j <= len(lines):
                part = lines[j - 1].strip()
                if part == "":
                    j += 1
                    continue
                merged += part
                sig_end_line = j
                if part.endswith(":"):
                    break
                j += 1
            sig_line = merged
        sig = parse_def_sig(i, sig_line)
        if sig is not None:
            fn_name = str(sig["name"])
            fn_ret = str(sig["ret"])
            arg_types = dict(sig["arg_types"])
            block: list[tuple[int, str]] = []
            j = sig_end_line + 1
            while j <= len(lines):
                bl = lines[j - 1]
                if bl.strip() == "":
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
            item = {
                "kind": "FunctionDef",
                "name": fn_name,
                "original_name": fn_name,
                "source_span": {"lineno": i, "col": 0, "end_lineno": block[-1][0], "end_col": len(block[-1][1])},
                "arg_types": arg_types,
                "return_type": fn_ret,
                "arg_usage": {n: "readonly" for n in arg_types.keys()},
                "renamed_symbols": {},
                "leading_comments": [],
                "leading_trivia": [],
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
        if re.match(r"^(from\s+[A-Za-z_][A-Za-z0-9_\.]*\s+import\s+.+|import\s+[A-Za-z_][A-Za-z0-9_\.]*)\s*$", s):
            i += 1
            continue
        if s.startswith("@"):
            i += 1
            continue

        m_cls = re.match(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\(([A-Za-z_][A-Za-z0-9_]*)\))?\s*:\s*$", ln)
        if m_cls is not None:
            cls_name = m_cls.group(1)
            base = m_cls.group(2)
            cls_indent = len(ln) - len(ln.lstrip(" "))
            block: list[tuple[int, str]] = []
            j = i + 1
            while j <= len(lines):
                bl = lines[j - 1]
                if bl.strip() == "":
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

            field_types: dict[str, str] = {}
            class_body: list[dict[str, Any]] = []
            k = 0
            while k < len(block):
                ln_no, ln_txt = block[k]
                s2 = re.sub(r"\s+#.*$", "", ln_txt).strip()
                bind = len(ln_txt) - len(ln_txt.lstrip(" "))
                if bind == cls_indent + 4:
                    m_field = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^=]+?)(?:\s*=\s*(.+))?$", s2)
                    if m_field is not None:
                        fname = m_field.group(1)
                        fty = _sh_ann_to_type(m_field.group(2))
                        field_types[fname] = fty
                        val_node = None
                        if m_field.group(3) is not None:
                            fexpr_txt = m_field.group(3).strip()
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
                    sig = parse_def_sig(ln_no, ln_txt, in_class=cls_name)
                    if sig is not None:
                        mname = str(sig["name"])
                        marg_types = dict(sig["arg_types"])
                        mret = str(sig["ret"])
                        method_block: list[tuple[int, str]] = []
                        m = k + 1
                        while m < len(block):
                            n_no, n_txt = block[m]
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
                        if mname == "__init__":
                            for st in stmts:
                                if st.get("kind") == "Assign":
                                    tgt = st.get("target")
                                    if (
                                        isinstance(tgt, dict)
                                        and tgt.get("kind") == "Attribute"
                                        and isinstance(tgt.get("value"), dict)
                                        and tgt.get("value", {}).get("kind") == "Name"
                                        and tgt.get("value", {}).get("id") == "self"
                                    ):
                                        fname = str(tgt.get("attr", ""))
                                        if fname != "":
                                            t = st.get("decl_type") or (st.get("value") or {}).get("resolved_type")
                                            if isinstance(t, str) and t != "":
                                                field_types[fname] = t
                                if st.get("kind") == "AnnAssign":
                                    tgt = st.get("target")
                                    if (
                                        isinstance(tgt, dict)
                                        and tgt.get("kind") == "Attribute"
                                        and isinstance(tgt.get("value"), dict)
                                        and tgt.get("value", {}).get("kind") == "Name"
                                        and tgt.get("value", {}).get("id") == "self"
                                    ):
                                        fname = str(tgt.get("attr", ""))
                                        ann = st.get("annotation")
                                        if fname != "" and isinstance(ann, str) and ann != "":
                                            field_types[fname] = ann
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
                                "return_type": mret,
                                "arg_usage": {n: "readonly" for n in marg_types.keys()},
                                "renamed_symbols": {},
                                "body": stmts,
                            }
                        )
                        k = m
                        continue
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse class statement: {s2}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use field annotation or method definitions in class body.",
                )

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
            pending_dataclass = False
            if not first_item_attached:
                cls_item["leading_comments"] = list(leading_file_comments)
                cls_item["leading_trivia"] = list(leading_file_trivia)
                first_item_attached = True
            body_items.append(cls_item)
            i = j
            continue

        m_ann_top = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^=]+?)\s*=\s*(.+)$", s)
        if m_ann_top is not None:
            name = m_ann_top.group(1)
            ann = _sh_ann_to_type(m_ann_top.group(2))
            expr_txt = m_ann_top.group(3).strip()
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
            i += 1
            continue

        raise EastBuildError(
            kind="unsupported_syntax",
            message=f"self_hosted parser cannot parse top-level statement: {s}",
            source_span=_sh_span(i, 0, len(ln)),
            hint="Use def/class/top-level typed assignment/main guard.",
        )

    if len(main_stmts) == 0:
        raise EastBuildError(
            kind="unsupported_syntax",
            message="self_hosted parser requires if __name__ == \"__main__\": block",
            source_span={"lineno": None, "col": None, "end_lineno": None, "end_col": None},
            hint="Add main guard block with print(...).",
        )

    renamed_symbols: dict[str, str] = {}
    for item in body_items:
        if item.get("kind") == "FunctionDef" and item.get("name") == "main":
            renamed_symbols["main"] = "__pytra_main"
            item["name"] = "__pytra_main"

    return {
        "kind": "Module",
        "source_path": filename,
        "source_span": {"lineno": None, "col": None, "end_lineno": None, "end_col": None},
        "body": body_items,
        "main_guard_body": main_stmts,
        "renamed_symbols": renamed_symbols,
        "meta": {"parser_backend": "self_hosted"},
    }


def convert_source_to_east_with_backend(source: str, filename: str, parser_backend: str = "self_hosted") -> dict[str, Any]:
    if parser_backend != "self_hosted":
        raise EastBuildError(
            kind="unsupported_syntax",
            message=f"unknown parser backend: {parser_backend}",
            source_span={"lineno": None, "col": None, "end_lineno": None, "end_col": None},
            hint="Use parser_backend=self_hosted.",
        )
    return convert_source_to_east_self_hosted(source, filename)


def convert_path(input_path: Path, parser_backend: str = "self_hosted") -> dict[str, Any]:
    """Read Python file and convert to EAST document."""
    source = input_path.read_text(encoding="utf-8")
    return convert_source_to_east_with_backend(source, str(input_path), parser_backend=parser_backend)


def _dump_json(obj: dict[str, Any], *, pretty: bool) -> str:
    """Serialize output JSON in compact or pretty mode."""
    if pretty:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _indent(lines: list[str], level: int = 1) -> list[str]:
    """Indent helper for human-readable C++-style rendering."""
    prefix = "    " * level
    return [prefix + ln if ln else "" for ln in lines]


def _fmt_span(span: dict[str, Any] | None) -> str:
    """Format source span as `line:col` for comments."""
    if not span:
        return "?:?"
    ln = span.get("lineno")
    col = span.get("col")
    if ln is None or col is None:
        return "?:?"
    return f"{ln}:{col}"


def _render_expr(expr: dict[str, Any] | None) -> str:
    """Render EAST expression as compact C++-style pseudo expression."""
    if expr is None:
        return "/* none */"
    rep = expr.get("repr")
    if rep is None:
        rep = f"<{expr.get('kind', 'Expr')}>"
    typ = expr.get("resolved_type", "unknown")
    borrow = expr.get("borrow_kind", "value")
    casts = expr.get("casts", [])
    cast_txt = ""
    if casts:
        cast_parts = []
        for c in casts:
            cast_parts.append(f"{c.get('on')}:{c.get('from')}->{c.get('to')}({c.get('reason')})")
        cast_txt = " casts=" + ",".join(cast_parts)
    return f"{rep} /* type={typ}, borrow={borrow}{cast_txt} */"


def _expr_repr(expr: dict[str, Any] | None) -> str:
    """Best-effort expression representation (without metadata suffix)."""
    if expr is None:
        return "/* none */"
    rep = expr.get("repr")
    if rep is None:
        return f"<{expr.get('kind', 'Expr')}>"
    return rep


def _cpp_type_name(east_type: str | None) -> str:
    """Map EAST type names to human-view C++-like type labels."""
    if east_type is None:
        return "auto"
    if east_type in INT_TYPES | FLOAT_TYPES | {"bool", "str", "Path", "Exception", "None"}:
        return east_type
    if east_type.startswith("list["):
        return east_type
    if east_type.startswith("dict["):
        return east_type
    if east_type.startswith("set["):
        return east_type
    if east_type.startswith("tuple["):
        return east_type
    return "auto"


def _render_stmt(stmt: dict[str, Any], level: int = 1) -> list[str]:
    """Render one EAST statement as C++-style pseudo source lines."""
    k = stmt.get("kind")
    sp = _fmt_span(stmt.get("source_span"))
    pad = "    " * level
    out: list[str] = []

    if k == "Import":
        names = ", ".join((n["name"] if n.get("asname") is None else f"{n['name']} as {n['asname']}") for n in stmt.get("names", []))
        out.append(f"// [{sp}] import {names};")
        return _indent(out, level)
    if k == "ImportFrom":
        names = ", ".join((n["name"] if n.get("asname") is None else f"{n['name']} as {n['asname']}") for n in stmt.get("names", []))
        out.append(f"// [{sp}] from {stmt.get('module')} import {names};")
        return _indent(out, level)
    if k == "Pass":
        return _indent([f"// [{sp}] pass;"], level)
    if k == "Break":
        return _indent([f"// [{sp}] break;"], level)
    if k == "Continue":
        return _indent([f"// [{sp}] continue;"], level)
    if k == "Return":
        v = _render_expr(stmt.get("value")) if stmt.get("value") is not None else "/* void */"
        return _indent([f"// [{sp}]", f"return {v};"], level)
    if k == "Expr":
        return _indent([f"// [{sp}]", f"{_render_expr(stmt.get('value'))};"], level)
    if k == "Assign":
        return _indent(
            [
                f"// [{sp}]",
                f"{_render_expr(stmt.get('target'))} = {_render_expr(stmt.get('value'))};",
            ],
            level,
        )
    if k == "Swap":
        return _indent(
            [
                f"// [{sp}]",
                f"py_swap({_render_expr(stmt.get('left'))}, {_render_expr(stmt.get('right'))});",
            ],
            level,
        )
    if k == "AnnAssign":
        ann = stmt.get("annotation", "auto")
        return _indent(
            [
                f"// [{sp}]",
                f"{ann} {_render_expr(stmt.get('target'))} = {_render_expr(stmt.get('value'))};",
            ],
            level,
        )
    if k == "AugAssign":
        op = stmt.get("op", "Op")
        return _indent(
            [
                f"// [{sp}]",
                f"{_render_expr(stmt.get('target'))} /* {op} */= {_render_expr(stmt.get('value'))};",
            ],
            level,
        )
    if k == "If":
        out.append(f"{pad}// [{sp}]")
        out.append(f"{pad}if ({_render_expr(stmt.get('test'))}) {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        if stmt.get("orelse"):
            out.append(f"{pad}else {{")
            for s in stmt.get("orelse", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        return out
    if k == "For":
        tgt_expr = stmt.get("target")
        tgt = _expr_repr(tgt_expr)
        tgt_ty = _cpp_type_name((tgt_expr or {}).get("resolved_type") if isinstance(tgt_expr, dict) else None)
        out.append(f"{pad}// [{sp}]")
        out.append(f"{pad}for ({tgt_ty} {tgt} : { _render_expr(stmt.get('iter')) }) {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        if stmt.get("orelse"):
            out.append(f"{pad}// for-else")
            out.append(f"{pad}{{")
            for s in stmt.get("orelse", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        return out
    if k == "ForRange":
        tgt_expr = stmt.get("target")
        tgt = _expr_repr(tgt_expr)
        tgt_ty = _cpp_type_name((tgt_expr or {}).get("resolved_type") if isinstance(tgt_expr, dict) else None)
        start = _render_expr(stmt.get("start"))
        stop = _render_expr(stmt.get("stop"))
        step = _render_expr(stmt.get("step"))
        mode = stmt.get("range_mode", "dynamic")
        if mode == "ascending":
            cond = f"({tgt}) < ({stop})"
        elif mode == "descending":
            cond = f"({tgt}) > ({stop})"
        else:
            cond = f"({step}) > 0 ? ({tgt}) < ({stop}) : ({tgt}) > ({stop})"
        out.append(f"{pad}// [{sp}]")
        out.append(f"{pad}for ({tgt_ty} {tgt} = {start}; {cond}; {tgt} += ({step})) {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        if stmt.get("orelse"):
            out.append(f"{pad}// for-else")
            out.append(f"{pad}{{")
            for s in stmt.get("orelse", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        return out
    if k == "While":
        out.append(f"{pad}// [{sp}]")
        out.append(f"{pad}while ({_render_expr(stmt.get('test'))}) {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        if stmt.get("orelse"):
            out.append(f"{pad}// while-else")
            out.append(f"{pad}{{")
            for s in stmt.get("orelse", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        return out
    if k == "Raise":
        return _indent([f"// [{sp}]", f"throw {_render_expr(stmt.get('exc'))};"], level)
    if k == "Try":
        out.append(f"{pad}// [{sp}]")
        out.append(f"{pad}try {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        for h in stmt.get("handlers", []):
            ex_name = h.get("name") or "ex"
            ex_type = _render_expr(h.get("type"))
            out.append(f"{pad}catch ({ex_type} as {ex_name}) {{")
            for s in h.get("body", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        if stmt.get("orelse"):
            out.append(f"{pad}// try-else")
            out.append(f"{pad}{{")
            for s in stmt.get("orelse", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        if stmt.get("finalbody"):
            out.append(f"{pad}/* finally */ {{")
            for s in stmt.get("finalbody", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        return out
    if k == "FunctionDef":
        name = stmt.get("name", "fn")
        ret = stmt.get("return_type", "None")
        arg_types: dict[str, str] = stmt.get("arg_types", {})
        arg_usage: dict[str, str] = stmt.get("arg_usage", {})
        params = []
        for n, t in arg_types.items():
            usage = arg_usage.get(n, "readonly")
            params.append(f"{t} {n} /* {usage} */")
        out.append(f"{pad}// [{sp}] function original={stmt.get('original_name', name)}")
        out.append(f"{pad}{ret} {name}({', '.join(params)}) {{")
        rs = stmt.get("renamed_symbols", {})
        if rs:
            out.append(("    " * (level + 1)) + f"// renamed_symbols: {rs}")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        return out
    if k == "ClassDef":
        name = stmt.get("name", "Class")
        out.append(f"{pad}// [{sp}] class original={stmt.get('original_name', name)}")
        out.append(f"{pad}struct {name} {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}};")
        return out

    return _indent([f"// [{sp}] <unsupported stmt kind={k}>"], level)


def render_east_human_cpp(out_doc: dict[str, Any]) -> str:
    """Render whole EAST output into human-readable C++-style pseudo code."""
    lines: list[str] = []
    lines.append("// EAST Human View (C++-style pseudo source)")
    lines.append("// Generated by src/east.py")
    lines.append("")
    if not out_doc.get("ok", False):
        err = out_doc.get("error", {})
        lines.append("/* EAST generation failed */")
        lines.append(f"// kind: {err.get('kind')}")
        lines.append(f"// message: {err.get('message')}")
        lines.append(f"// source_span: {err.get('source_span')}")
        lines.append(f"// hint: {err.get('hint')}")
        lines.append("")
        return "\n".join(lines) + "\n"

    east = out_doc["east"]
    lines.append(f"namespace east_view /* source: {east.get('source_path')} */ {{")
    lines.append("")
    rs = east.get("renamed_symbols", {})
    if rs:
        lines.append("    // renamed_symbols")
        for k, v in rs.items():
            lines.append(f"    //   {k} -> {v}")
        lines.append("")

    lines.append("    // module body")
    for s in east.get("body", []):
        lines.extend(_render_stmt(s, 1))
    lines.append("")

    lines.append("    // main guard body")
    lines.append("    int64 __east_main_guard() {")
    for s in east.get("main_guard_body", []):
        lines.extend(_render_stmt(s, 2))
    lines.append("        return 0;")
    lines.append("    }")
    lines.append("")
    lines.append("} // namespace east_view")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for EAST JSON/human-view generation."""
    parser = argparse.ArgumentParser(description="Convert Python source into EAST JSON")
    parser.add_argument("input", help="Input Python file")
    parser.add_argument("-o", "--output", help="Output EAST JSON path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--human-output", help="Output human-readable C++-style EAST path")
    parser.add_argument("--parser-backend", choices=["self_hosted"], default="self_hosted", help="Parser backend")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        east = convert_path(input_path, parser_backend=args.parser_backend)
    except SyntaxError as exc:
        err = {
            "kind": "unsupported_syntax",
            "message": str(exc),
            "source_span": {
                "lineno": exc.lineno,
                "col": exc.offset,
                "end_lineno": exc.end_lineno,
                "end_col": exc.end_offset,
            },
            "hint": "Fix Python syntax errors before EAST conversion.",
        }
        out = {"ok": False, "error": err}
        payload = _dump_json(out, pretty=True)
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(payload + "\n", encoding="utf-8")
        else:
            print(payload)
        if args.human_output:
            human_path = Path(args.human_output)
            human_path.parent.mkdir(parents=True, exist_ok=True)
            human_path.write_text(render_east_human_cpp(out), encoding="utf-8")
        return 1
    except EastBuildError as exc:
        out = {"ok": False, "error": exc.to_payload()}
        payload = _dump_json(out, pretty=True)
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(payload + "\n", encoding="utf-8")
        else:
            print(payload)
        if args.human_output:
            human_path = Path(args.human_output)
            human_path.parent.mkdir(parents=True, exist_ok=True)
            human_path.write_text(render_east_human_cpp(out), encoding="utf-8")
        return 1

    out = {"ok": True, "east": east}
    payload = _dump_json(out, pretty=args.pretty)
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if args.human_output:
        human_path = Path(args.human_output)
        human_path.parent.mkdir(parents=True, exist_ok=True)
        human_path.write_text(render_east_human_cpp(out), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
