"""Minimal pure-Python regex subset used by Pytra selfhost path."""

from __future__ import annotations

S = 1


class Match:
    """Small match object compatible with group() usage in this repository."""

    def __init__(self, text: str, groups: list[str]) -> None:
        self._text = text
        self._groups = groups

    def group(self, idx: int = 0) -> str:
        if idx == 0:
            return self._text
        if idx < 0 or idx > len(self._groups):
            raise IndexError("group index out of range")
        return self._groups[idx - 1]


def group(m: Match | None, idx: int = 0) -> str:
    """`Match | None` から group を安全取得する（None は空文字）。"""
    if m is None:
        return ""
    mm: Match = m
    return mm.group(idx)


def strip_group(m: Match | None, idx: int = 0) -> str:
    """group を取得して前後空白を除去する。"""
    return group(m, idx).strip()


def _is_ident(s: str) -> bool:
    if s == "":
        return False
    h = s[0:1]
    is_head_alpha = ("a" <= h <= "z") or ("A" <= h <= "Z")
    if not (is_head_alpha or h == "_"):
        return False
    for ch in s[1:]:
        is_alpha = ("a" <= ch <= "z") or ("A" <= ch <= "Z")
        is_digit = ("0" <= ch <= "9")
        if not (is_alpha or is_digit or ch == "_"):
            return False
    return True


def _is_dotted_ident(s: str) -> bool:
    if s == "":
        return False
    part = ""
    for ch in s:
        if ch == ".":
            if not _is_ident(part):
                return False
            part = ""
            continue
        part += ch
    if not _is_ident(part):
        return False
    if part == "":
        return False
    return True


def _strip_suffix_colon(s: str) -> str:
    t = s.rstrip()
    if len(t) == 0:
        return ""
    if t[-1:] != ":":
        return ""
    return t[:-1]


def _is_space_ch(ch: str) -> bool:
    if ch == " ":
        return True
    if ch == "\t":
        return True
    if ch == "\r":
        return True
    if ch == "\n":
        return True
    return False


def _is_alnum_or_underscore(ch: str) -> bool:
    is_alpha = ("a" <= ch <= "z") or ("A" <= ch <= "Z")
    is_digit = ("0" <= ch <= "9")
    if is_alpha or is_digit:
        return True
    return ch == "_"


def _skip_spaces(t: str, i: int) -> int:
    while i < len(t):
        if not _is_space_ch(t[i : i + 1]):
            return i
        i += 1
    return i


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
        if t == "":
            return None
        i = 0
        if not t.startswith("def"):
            return None
        i = 3
        if i >= len(t) or not _is_space_ch(t[i : i + 1]):
            return None
        i = _skip_spaces(t, i)
        j = i
        while j < len(t) and _is_alnum_or_underscore(t[j : j + 1]):
            j += 1
        name: str = t[i:j]
        if not _is_ident(name):
            return None
        k = j
        k = _skip_spaces(t, k)
        if k >= len(t) or t[k : k + 1] != "(":
            return None
        r: int = t.rfind(")")
        if r <= k:
            return None
        args: str = t[k + 1 : r]
        tail: str = t[r + 1 :].strip()
        if tail == "":
            return Match(text, [name, args, ""])
        if not tail.startswith("->"):
            return None
        ret: str = tail[2:].strip()
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
            return Match(text, [name, ann, ""])
        ann = rhs[:eq].strip()
        val = rhs[eq + 1 :].strip()
        if ann == "" or val == "":
            return None
        return Match(text, [name, ann, val])

    # ^[A-Za-z_][A-Za-z0-9_]*$
    if pattern == r"^[A-Za-z_][A-Za-z0-9_]*$":
        if _is_ident(text):
            return Match(text, [])
        return None

    # ^class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\(([A-Za-z_][A-Za-z0-9_]*)\))?\s*:\s*$
    if pattern == r"^class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\(([A-Za-z_][A-Za-z0-9_]*)\))?\s*:\s*$":
        t = _strip_suffix_colon(text)
        if t == "":
            return None
        if not t.startswith("class"):
            return None
        i = 5
        if i >= len(t) or not _is_space_ch(t[i : i + 1]):
            return None
        i = _skip_spaces(t, i)
        j = i
        while j < len(t) and _is_alnum_or_underscore(t[j : j + 1]):
            j += 1
        name: str = t[i:j]
        if not _is_ident(name):
            return None
        tail: str = t[j:].strip()
        if tail == "":
            return Match(text, [name, ""])
        if not (tail.startswith("(") and tail.endswith(")")):
            return None
        base: str = tail[1:-1].strip()
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
        inner: str = text[1:-1].strip()
        m1 = " for "
        m2 = " in "
        i: int = inner.find(m1)
        if i < 0:
            return None
        expr: str = inner[:i].strip()
        rest: str = inner[i + len(m1) :]
        j: int = rest.find(m2)
        if j < 0:
            return None
        var: str = rest[:j].strip()
        it: str = rest[j + len(m2) :].strip()
        if not _is_ident(expr) or not _is_ident(var) or it == "":
            return None
        return Match(text, [expr, var, it])

    # ^for\s+(.+)\s+in\s+(.+):$
    if pattern == r"^for\s+(.+)\s+in\s+(.+):$":
        t = _strip_suffix_colon(text)
        if t == "" or not t.startswith("for"):
            return None
        rest: str = t[3:].strip()
        i: int = rest.find(" in ")
        if i < 0:
            return None
        left: str = rest[:i].strip()
        right: str = rest[i + 4 :].strip()
        if left == "" or right == "":
            return None
        return Match(text, [left, right])

    # ^with\s+(.+)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$
    if pattern == r"^with\s+(.+)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$":
        t = _strip_suffix_colon(text)
        if t == "" or not t.startswith("with"):
            return None
        rest: str = t[4:].strip()
        i: int = rest.rfind(" as ")
        if i < 0:
            return None
        expr: str = rest[:i].strip()
        name: str = rest[i + 4 :].strip()
        if expr == "" or not _is_ident(name):
            return None
        return Match(text, [expr, name])

    # ^except\s+(.+?)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$
    if pattern == r"^except\s+(.+?)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$":
        t = _strip_suffix_colon(text)
        if t == "" or not t.startswith("except"):
            return None
        rest: str = t[6:].strip()
        i: int = rest.rfind(" as ")
        if i < 0:
            return None
        exc: str = rest[:i].strip()
        name: str = rest[i + 4 :].strip()
        if exc == "" or not _is_ident(name):
            return None
        return Match(text, [exc, name])

    # ^except\s+(.+?)\s*:\s*$
    if pattern == r"^except\s+(.+?)\s*:\s*$":
        t = _strip_suffix_colon(text)
        if t == "" or not t.startswith("except"):
            return None
        rest: str = t[6:].strip()
        if rest == "":
            return None
        return Match(text, [rest])

    # ^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:\s*(.+)$
    if pattern == r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:\s*(.+)$":
        c = text.find(":")
        if c <= 0:
            return None
        target: str = text[:c].strip()
        ann: str = text[c + 1 :].strip()
        if ann == "" or not _is_dotted_ident(target):
            return None
        return Match(text, [target, ann])

    # ^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:\s*([^=]+?)\s*=\s*(.+)$
    if pattern == r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:\s*([^=]+?)\s*=\s*(.+)$":
        c = text.find(":")
        if c <= 0:
            return None
        target: str = text[:c].strip()
        rhs: str = text[c + 1 :]
        eq: int = rhs.find("=")
        if eq < 0:
            return None
        ann: str = rhs[:eq].strip()
        expr: str = rhs[eq + 1 :].strip()
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
        left: str = text[:op_pos].strip()
        right: str = text[op_pos + len(op_txt) :].strip()
        if right == "" or not _is_dotted_ident(left):
            return None
        return Match(text, [left, op_txt, right])

    # ^([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$
    if pattern == r"^([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$":
        eq: int = text.find("=")
        if eq < 0:
            return None
        left: str = text[:eq]
        right: str = text[eq + 1 :].strip()
        if right == "":
            return None
        c: int = left.find(",")
        if c < 0:
            return None
        a: str = left[:c].strip()
        b: str = left[c + 1 :].strip()
        if not _is_ident(a) or not _is_ident(b):
            return None
        return Match(text, [a, b, right])

    # ^if\s+__name__\s*==\s*[\"']__main__[\"']\s*:\s*$
    if pattern == r"^if\s+__name__\s*==\s*[\"']__main__[\"']\s*:\s*$":
        t = _strip_suffix_colon(text)
        if t == "":
            return None
        rest: str = t.strip()
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
        rest: str = text[6:].strip()
        if rest == "":
            return None
        return Match(text, [rest])

    # ^([A-Za-z_][A-Za-z0-9_\.]*)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?$
    if pattern == r"^([A-Za-z_][A-Za-z0-9_\.]*)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?$":
        parts: list[str] = text.split(" as ")
        if len(parts) == 1:
            name: str = parts[0].strip()
            if not _is_dotted_ident(name):
                return None
            return Match(text, [name, ""])
        if len(parts) == 2:
            name: str = parts[0].strip()
            alias: str = parts[1].strip()
            if not _is_dotted_ident(name) or not _is_ident(alias):
                return None
            return Match(text, [name, alias])
        return None

    # ^from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+import\s+(.+)$
    if pattern == r"^from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+import\s+(.+)$":
        if not text.startswith("from "):
            return None
        rest: str = text[5:]
        i: int = rest.find(" import ")
        if i < 0:
            return None
        mod: str = rest[:i].strip()
        sym: str = rest[i + 8 :].strip()
        if not _is_dotted_ident(mod) or sym == "":
            return None
        return Match(text, [mod, sym])

    # ^([A-Za-z_][A-Za-z0-9_]*)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?$
    if pattern == r"^([A-Za-z_][A-Za-z0-9_]*)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?$":
        parts: list[str] = text.split(" as ")
        if len(parts) == 1:
            name: str = parts[0].strip()
            if not _is_ident(name):
                return None
            return Match(text, [name, ""])
        if len(parts) == 2:
            name: str = parts[0].strip()
            alias: str = parts[1].strip()
            if not _is_ident(name) or not _is_ident(alias):
                return None
            return Match(text, [name, alias])
        return None

    # ^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^=]+?)\s*=\s*(.+)$
    if pattern == r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^=]+?)\s*=\s*(.+)$":
        c = text.find(":")
        if c <= 0:
            return None
        name: str = text[:c].strip()
        rhs: str = text[c + 1 :]
        eq: int = rhs.find("=")
        if eq < 0:
            return None
        ann: str = rhs[:eq].strip()
        expr: str = rhs[eq + 1 :].strip()
        if not _is_ident(name) or ann == "" or expr == "":
            return None
        return Match(text, [name, ann, expr])

    # ^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$
    if pattern == r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$":
        eq: int = text.find("=")
        if eq < 0:
            return None
        name: str = text[:eq].strip()
        expr: str = text[eq + 1 :].strip()
        if not _is_ident(name) or expr == "":
            return None
        return Match(text, [name, expr])

    raise ValueError(f"unsupported regex pattern in pytra.std.re: {pattern}")


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

    raise ValueError(f"unsupported regex sub pattern in pytra.std.re: {pattern}")
