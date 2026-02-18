"""EAST ベースの言語エミッタ共通基底。"""

from __future__ import annotations

from typing import Any


class BaseEmitter:
    """EAST -> 各言語のコード生成で共通利用する最小基底クラス。"""

    def __init__(self, east_doc: dict[str, Any]) -> None:
        self.doc = east_doc
        self.lines: list[str] = []
        self.indent = 0
        self.tmp_id = 0

    def emit(self, line: str = "") -> None:
        self.lines.append(("    " * self.indent) + line)

    def emit_stmt_list(self, stmts: list[Any]) -> None:
        for stmt in stmts:
            self.emit_stmt(stmt)  # type: ignore[attr-defined]

    def next_tmp(self, prefix: str = "__tmp") -> str:
        self.tmp_id += 1
        return f"{prefix}_{self.tmp_id}"

    def any_dict_get(self, obj: Any, key: str, default: Any) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return default

    def get_expr_type(self, expr: Any) -> str:
        if expr is None or not isinstance(expr, dict):
            return ""
        t = expr.get("resolved_type")
        return t if isinstance(t, str) else ""

    def is_name(self, node: Any, name: str | None = None) -> bool:
        if not isinstance(node, dict) or node.get("kind") != "Name":
            return False
        if name is None:
            return True
        return str(node.get("id", "")) == name

    def is_call(self, node: Any) -> bool:
        return isinstance(node, dict) and node.get("kind") == "Call"

    def is_attr(self, node: Any, attr: str | None = None) -> bool:
        if not isinstance(node, dict) or node.get("kind") != "Attribute":
            return False
        if attr is None:
            return True
        return str(node.get("attr", "")) == attr

    def split_generic(self, s: str) -> list[str]:
        if s == "":
            return []
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

    def split_union(self, s: str) -> list[str]:
        out: list[str] = []
        depth = 0
        start = 0
        for i, ch in enumerate(s):
            if ch in {"[", "("}:
                depth += 1
            elif ch in {"]", ")"}:
                depth -= 1
            elif ch == "|" and depth == 0:
                part = s[start:i].strip()
                if part != "":
                    out.append(part)
                start = i + 1
        tail = s[start:].strip()
        if tail != "":
            out.append(tail)
        return out

    def normalize_type_name(self, t: Any) -> str:
        if not isinstance(t, str):
            return ""
        s = str(t)
        if s == "any":
            return "Any"
        if s == "object":
            return "object"
        return s

    def is_any_like_type(self, t: Any) -> bool:
        s = self.normalize_type_name(t)
        if s == "":
            return False
        if s in {"Any", "object", "unknown"}:
            return True
        if "|" in s:
            parts = self.split_union(s)
            return any(self.is_any_like_type(p) for p in parts if p != "None")
        return False

    def is_list_type(self, t: Any) -> bool:
        return isinstance(t, str) and t.startswith("list[")

    def is_set_type(self, t: Any) -> bool:
        return isinstance(t, str) and t.startswith("set[")

    def is_dict_type(self, t: Any) -> bool:
        return isinstance(t, str) and t.startswith("dict[")

    def is_indexable_sequence_type(self, t: Any) -> bool:
        return isinstance(t, str) and (t.startswith("list[") or t in {"str", "bytes", "bytearray"})
