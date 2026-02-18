"""EAST ベースの言語エミッタ共通基底。"""

from __future__ import annotations

from typing import Any


class BaseEmitter:
    """EAST -> 各言語のコード生成で共通利用する最小基底クラス。"""

    def __init__(self, east_doc: dict[str, Any]) -> None:
        """共通の出力状態と一時変数カウンタを初期化する。"""
        self.doc = east_doc
        self.lines: list[str] = []
        self.indent = 0
        self.tmp_id = 0

    def emit_stmt(self, stmt: Any) -> None:
        """文ノード出力フック。派生クラス側で実装する。"""
        return

    def emit(self, line: str = "") -> None:
        """現在のインデントで1行を出力バッファへ追加する。"""
        self.lines.append(("    " * self.indent) + line)

    def emit_stmt_list(self, stmts: list[Any]) -> None:
        for stmt in stmts:
            self.emit_stmt(stmt)  # type: ignore[attr-defined]

    def next_tmp(self, prefix: str = "__tmp") -> str:
        """衝突しない一時変数名を生成する。"""
        self.tmp_id += 1
        return f"{prefix}_{self.tmp_id}"

    def any_dict_get(self, obj: Any, key: str, default_value: Any) -> Any:
        """dict 風入力から key を取得し、失敗時は既定値を返す。"""
        if not isinstance(obj, dict):
            return default_value
        if key in obj:
            return obj[key]
        return default_value

    def any_to_dict(self, v: Any) -> dict[str, Any] | None:
        """動的値を dict に安全に変換する。変換不能なら None。"""
        out: dict[str, Any] | None = None
        if isinstance(v, dict):
            out = v
        return out

    def any_to_list(self, v: Any) -> list[Any]:
        """動的値を list に安全に変換する。変換不能なら空 list。"""
        out: list[Any] = []
        if isinstance(v, list):
            out = v
        return out

    def any_to_str(self, v: Any) -> str:
        """動的値を str に安全に変換する。変換不能なら空文字。"""
        out = ""
        if isinstance(v, str):
            out = v
        return out

    def get_expr_type(self, expr: Any) -> str:
        """式ノードから解決済み型文字列を取得する。"""
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
        """型名エイリアスを内部表現へ正規化する。"""
        if not isinstance(t, str):
            return ""
        s = str(t)
        if s == "byte":
            return "uint8"
        if s == "any":
            return "Any"
        if s == "object":
            return "object"
        return s

    def is_any_like_type(self, t: Any) -> bool:
        """Any 同等（Any/object/unknown/Union 含む）型か判定する。"""
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
        """型文字列が list[...] かを返す。"""
        return isinstance(t, str) and t.startswith("list[")

    def is_set_type(self, t: Any) -> bool:
        """型文字列が set[...] かを返す。"""
        return isinstance(t, str) and t.startswith("set[")

    def is_dict_type(self, t: Any) -> bool:
        """型文字列が dict[...] かを返す。"""
        return isinstance(t, str) and t.startswith("dict[")

    def is_indexable_sequence_type(self, t: Any) -> bool:
        """添字アクセス可能なシーケンス型か判定する。"""
        return isinstance(t, str) and (t.startswith("list[") or t in {"str", "bytes", "bytearray"})

    def _is_forbidden_object_receiver_type_text(self, s: str) -> bool:
        """object レシーバ禁止ルールに抵触する型文字列か判定する。"""
        if s in {"Any", "object", "any"}:
            return True
        if "|" in s:
            parts = self.split_union(s)
            for p in parts:
                if p == "None":
                    continue
                if p in {"Any", "object", "any"}:
                    return True
            return False
        return False

    def is_forbidden_object_receiver_type(self, t: Any) -> bool:
        """object レシーバ禁止ルールに抵触する型か判定する。"""
        s = self.normalize_type_name(t)
        return self._is_forbidden_object_receiver_type_text(s)
