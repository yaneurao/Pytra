"""Minimal pure-Python regex subset used by Pytra selfhost path."""

from __future__ import annotations

from pylib.std.typing import Any

S = 1


class Match:
    """Small match object compatible with group() usage in this repository."""

    def __init__(self, text: str, groups: list[Any]) -> None:
        self._text = text
        self._groups = groups

    def group(self, idx: int = 0) -> Any:
        if idx == 0:
            return self._text
        if idx < 0 or idx > len(self._groups):
            raise IndexError("group index out of range")
        return self._groups[idx - 1]


def _is_ident(s: str) -> bool:
    if s == "":
        return False
    if not (s[0].isalpha() or s[0] == "_"):
        return False
    for ch in s[1:]:
        if not (ch.isalnum() or ch == "_"):
            return False
    return True


def _is_dotted_ident(s: str) -> bool:
    parts = s.split(".")
    if len(parts) == 0:
        return False
    for p in parts:
        if not _is_ident(p):
            return False
    return True


def _strip_suffix_colon(s: str) -> str | None:
    t = s.rstrip()
    if not t.endswith(":"):
        return None
    return t[:-1]


def match(pattern: str, text: str, flags: int = 0) -> Match | None:
    # ^([A-Za-z_][A-Za-z0-9_]*)\[(.*)\]$
    if pattern == r"^([A-Za-z_][A-Za-z0-9_]*)\[(.*)\]$":
        if not text.endswith("]"):
            return None
        i = text.find("[")
        if i <= 0:
            return None
        head = text[:i]
        if not _is_ident(head):
            return None
        return Match(text, [head, text[i + 1 : -1]])

    # ^def\s+([A-Za-z_][A-Za-z0-9_]*)\((.*)\)\s*(?:->\s*(.+)\s*)?:\s*$
    if pattern == r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\((.*)\)\s*(?:->\s*(.+)\s*)?:\s*$":
        t = _strip_suffix_colon(text)
        if t is None:
            return None
        i = 0
        if not t.startswith("def"):
            return None
        i = 3
        if i >= len(t) or not t[i].isspace():
            return None
        while i < len(t) and t[i].isspace():
            i += 1
        j = i
        while j < len(t) and (t[j].isalnum() or t[j] == "_"):
            j += 1
        name = t[i:j]
        if not _is_ident(name):
            return None
        k = j
        while k < len(t) and t[k].isspace():
            k += 1
        if k >= len(t) or t[k] != "(":
            return None
        r = t.rfind(")")
        if r <= k:
            return None
        args = t[k + 1 : r]
        tail = t[r + 1 :].strip()
        if tail == "":
            return Match(text, [name, args, None])
        if not tail.startswith("->"):
            return None
        ret = tail[2:].strip()
        if ret == "":
            return None
        return Match(text, [name, args, ret])

    # ^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^=]+?)(?:\s*=\s*(.+))?$
    if pattern == r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^=]+?)(?:\s*=\s*(.+))?$":
        c = text.find(":")
        if c <= 0:
            return None
        name = text[:c].strip()
        if not _is_ident(name):
            return None
        rhs = text[c + 1 :]
        eq = rhs.find("=")
        if eq < 0:
            ann = rhs.strip()
            if ann == "":
                return None
            return Match(text, [name, ann, None])
        ann = rhs[:eq].strip()
        val = rhs[eq + 1 :].strip()
        if ann == "" or val == "":
            return None
        return Match(text, [name, ann, val])

    # ^[A-Za-z_][A-Za-z0-9_]*$
    if pattern == r"^[A-Za-z_][A-Za-z0-9_]*$":
        return Match(text, []) if _is_ident(text) else None

    # ^class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\(([A-Za-z_][A-Za-z0-9_]*)\))?\s*:\s*$
    if pattern == r"^class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\(([A-Za-z_][A-Za-z0-9_]*)\))?\s*:\s*$":
        t = _strip_suffix_colon(text)
        if t is None:
            return None
        if not t.startswith("class"):
            return None
        i = 5
        if i >= len(t) or not t[i].isspace():
            return None
        while i < len(t) and t[i].isspace():
            i += 1
        j = i
        while j < len(t) and (t[j].isalnum() or t[j] == "_"):
            j += 1
        name = t[i:j]
        if not _is_ident(name):
            return None
        tail = t[j:].strip()
        if tail == "":
            return Match(text, [name, None])
        if not (tail.startswith("(") and tail.endswith(")")):
            return None
        base = tail[1:-1].strip()
        if not _is_ident(base):
            return None
        return Match(text, [name, base])

    # ^(any|all)\((.+)\)$
    if pattern == r"^(any|all)\((.+)\)$":
        if text.startswith("any(") and text.endswith(")") and len(text) > 5:
            return Match(text, ["any", text[4:-1]])
        if text.startswith("all(") and text.endswith(")") and len(text) > 5:
            return Match(text, ["all", text[4:-1]])
        return None

    # ^\[\s*([A-Za-z_][A-Za-z0-9_]*)\s+for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.+)\]$
    if pattern == r"^\[\s*([A-Za-z_][A-Za-z0-9_]*)\s+for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.+)\]$":
        if not (text.startswith("[") and text.endswith("]")):
            return None
        inner = text[1:-1].strip()
        m1 = " for "
        m2 = " in "
        i = inner.find(m1)
        if i < 0:
            return None
        expr = inner[:i].strip()
        rest = inner[i + len(m1) :]
        j = rest.find(m2)
        if j < 0:
            return None
        var = rest[:j].strip()
        it = rest[j + len(m2) :].strip()
        if not _is_ident(expr) or not _is_ident(var) or it == "":
            return None
        return Match(text, [expr, var, it])

    # ^for\s+(.+)\s+in\s+(.+):$
    if pattern == r"^for\s+(.+)\s+in\s+(.+):$":
        t = _strip_suffix_colon(text)
        if t is None or not t.startswith("for"):
            return None
        rest = t[3:].strip()
        i = rest.find(" in ")
        if i < 0:
            return None
        left = rest[:i].strip()
        right = rest[i + 4 :].strip()
        if left == "" or right == "":
            return None
        return Match(text, [left, right])

    # ^with\s+(.+)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$
    if pattern == r"^with\s+(.+)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$":
        t = _strip_suffix_colon(text)
        if t is None or not t.startswith("with"):
            return None
        rest = t[4:].strip()
        i = rest.rfind(" as ")
        if i < 0:
            return None
        expr = rest[:i].strip()
        name = rest[i + 4 :].strip()
        if expr == "" or not _is_ident(name):
            return None
        return Match(text, [expr, name])

    # ^except\s+(.+?)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$
    if pattern == r"^except\s+(.+?)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$":
        t = _strip_suffix_colon(text)
        if t is None or not t.startswith("except"):
            return None
        rest = t[6:].strip()
        i = rest.rfind(" as ")
        if i < 0:
            return None
        exc = rest[:i].strip()
        name = rest[i + 4 :].strip()
        if exc == "" or not _is_ident(name):
            return None
        return Match(text, [exc, name])

    # ^except\s+(.+?)\s*:\s*$
    if pattern == r"^except\s+(.+?)\s*:\s*$":
        t = _strip_suffix_colon(text)
        if t is None or not t.startswith("except"):
            return None
        rest = t[6:].strip()
        if rest == "":
            return None
        return Match(text, [rest])

    # ^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:\s*(.+)$
    if pattern == r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:\s*(.+)$":
        c = text.find(":")
        if c <= 0:
            return None
        target = text[:c].strip()
        ann = text[c + 1 :].strip()
        if ann == "" or not _is_dotted_ident(target):
            return None
        return Match(text, [target, ann])

    # ^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:\s*([^=]+?)\s*=\s*(.+)$
    if pattern == r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:\s*([^=]+?)\s*=\s*(.+)$":
        c = text.find(":")
        if c <= 0:
            return None
        target = text[:c].strip()
        rhs = text[c + 1 :]
        eq = rhs.find("=")
        if eq < 0:
            return None
        ann = rhs[:eq].strip()
        expr = rhs[eq + 1 :].strip()
        if not _is_dotted_ident(target) or ann == "" or expr == "":
            return None
        return Match(text, [target, ann, expr])

    # ^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*(\+=|-=|\*=|/=|//=|%=|&=|\|=|\^=|<<=|>>=)\s*(.+)$
    if pattern == r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*(\+=|-=|\*=|/=|//=|%=|&=|\|=|\^=|<<=|>>=)\s*(.+)$":
        ops = ["<<=", ">>=", "+=", "-=", "*=", "/=", "//=", "%=", "&=", "|=", "^="]
        op_pos = -1
        op_txt = ""
        for op in ops:
            p = text.find(op)
            if p >= 0 and (op_pos < 0 or p < op_pos):
                op_pos = p
                op_txt = op
        if op_pos < 0:
            return None
        left = text[:op_pos].strip()
        right = text[op_pos + len(op_txt) :].strip()
        if right == "" or not _is_dotted_ident(left):
            return None
        return Match(text, [left, op_txt, right])

    # ^([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$
    if pattern == r"^([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$":
        eq = text.find("=")
        if eq < 0:
            return None
        left = text[:eq]
        right = text[eq + 1 :].strip()
        if right == "":
            return None
        c = left.find(",")
        if c < 0:
            return None
        a = left[:c].strip()
        b = left[c + 1 :].strip()
        if not _is_ident(a) or not _is_ident(b):
            return None
        return Match(text, [a, b, right])

    # ^if\s+__name__\s*==\s*[\"']__main__[\"']\s*:\s*$
    if pattern == r"^if\s+__name__\s*==\s*[\"']__main__[\"']\s*:\s*$":
        t = _strip_suffix_colon(text)
        if t is None:
            return None
        rest = t.strip()
        if not rest.startswith("if"):
            return None
        rest = rest[2:].strip()
        if not rest.startswith("__name__"):
            return None
        rest = rest[len("__name__") :].strip()
        if not rest.startswith("=="):
            return None
        rest = rest[2:].strip()
        if rest in {'"__main__"', "'__main__'"}:
            return Match(text, [])
        return None

    # ^import\s+(.+)$
    if pattern == r"^import\s+(.+)$":
        if not text.startswith("import"):
            return None
        rest = text[6:].strip()
        if rest == "":
            return None
        return Match(text, [rest])

    # ^([A-Za-z_][A-Za-z0-9_\.]*)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?$
    if pattern == r"^([A-Za-z_][A-Za-z0-9_\.]*)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?$":
        parts = text.split(" as ")
        if len(parts) == 1:
            name = parts[0].strip()
            if not _is_dotted_ident(name):
                return None
            return Match(text, [name, None])
        if len(parts) == 2:
            name = parts[0].strip()
            alias = parts[1].strip()
            if not _is_dotted_ident(name) or not _is_ident(alias):
                return None
            return Match(text, [name, alias])
        return None

    # ^from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+import\s+(.+)$
    if pattern == r"^from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+import\s+(.+)$":
        if not text.startswith("from "):
            return None
        rest = text[5:]
        i = rest.find(" import ")
        if i < 0:
            return None
        mod = rest[:i].strip()
        sym = rest[i + 8 :].strip()
        if not _is_dotted_ident(mod) or sym == "":
            return None
        return Match(text, [mod, sym])

    # ^([A-Za-z_][A-Za-z0-9_]*)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?$
    if pattern == r"^([A-Za-z_][A-Za-z0-9_]*)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?$":
        parts = text.split(" as ")
        if len(parts) == 1:
            name = parts[0].strip()
            if not _is_ident(name):
                return None
            return Match(text, [name, None])
        if len(parts) == 2:
            name = parts[0].strip()
            alias = parts[1].strip()
            if not _is_ident(name) or not _is_ident(alias):
                return None
            return Match(text, [name, alias])
        return None

    # ^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^=]+?)\s*=\s*(.+)$
    if pattern == r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^=]+?)\s*=\s*(.+)$":
        c = text.find(":")
        if c <= 0:
            return None
        name = text[:c].strip()
        rhs = text[c + 1 :]
        eq = rhs.find("=")
        if eq < 0:
            return None
        ann = rhs[:eq].strip()
        expr = rhs[eq + 1 :].strip()
        if not _is_ident(name) or ann == "" or expr == "":
            return None
        return Match(text, [name, ann, expr])

    # ^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$
    if pattern == r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$":
        eq = text.find("=")
        if eq < 0:
            return None
        name = text[:eq].strip()
        expr = text[eq + 1 :].strip()
        if not _is_ident(name) or expr == "":
            return None
        return Match(text, [name, expr])

    raise ValueError(f"unsupported regex pattern in pylib.std.re: {pattern}")


def sub(pattern: str, repl: str, text: str, flags: int = 0) -> str:
    if pattern == r"\s+":
        out: list[str] = []
        in_ws = False
        for ch in text:
            if ch.isspace():
                if not in_ws:
                    out.append(repl)
                    in_ws = True
            else:
                out.append(ch)
                in_ws = False
        return "".join(out)

    if pattern == r"\s+#.*$":
        i = 0
        while i < len(text):
            if text[i].isspace():
                j = i + 1
                while j < len(text) and text[j].isspace():
                    j += 1
                if j < len(text) and text[j] == "#":
                    return text[:i] + repl
            i += 1
        return text

    if pattern == r"[^0-9A-Za-z_]":
        out: list[str] = []
        for ch in text:
            if ch.isalnum() or ch == "_":
                out.append(ch)
            else:
                out.append(repl)
        return "".join(out)

    raise ValueError(f"unsupported regex sub pattern in pylib.std.re: {pattern}")
