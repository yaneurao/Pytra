"""Pure-Python source-of-truth for string helper built-ins."""

from pytra.std import abi


def _is_space(ch: str) -> bool:
    return ch == " " or ch == "\t" or ch == "\n" or ch == "\r"


def _contains_char(chars: str, ch: str) -> bool:
    i = 0
    n = len(chars)
    while i < n:
        if chars[i] == ch:
            return True
        i += 1
    return False


def _normalize_index(idx: int, n: int) -> int:
    out = idx
    if out < 0:
        out += n
    if out < 0:
        out = 0
    if out > n:
        out = n
    return out


@abi(args={"parts": "value_readonly"}, ret="value")
def py_join(sep: str, parts: list[str]) -> str:
    n = len(parts)
    if n == 0:
        return ""
    out = ""
    i = 0
    while i < n:
        if i > 0:
            out += sep
        out += parts[i]
        i += 1
    return out


def py_lstrip(s: str) -> str:
    i = 0
    n = len(s)
    while i < n and _is_space(s[i]):
        i += 1
    return s[i:n]


def py_lstrip_chars(s: str, chars: str) -> str:
    i = 0
    n = len(s)
    while i < n and _contains_char(chars, s[i]):
        i += 1
    return s[i:n]


def py_rstrip(s: str) -> str:
    n = len(s)
    i = n - 1
    while i >= 0 and _is_space(s[i]):
        i -= 1
    return s[0 : i + 1]


def py_rstrip_chars(s: str, chars: str) -> str:
    n = len(s)
    i = n - 1
    while i >= 0 and _contains_char(chars, s[i]):
        i -= 1
    return s[0 : i + 1]


def py_strip(s: str) -> str:
    return py_rstrip(py_lstrip(s))


def py_strip_chars(s: str, chars: str) -> str:
    return py_rstrip_chars(py_lstrip_chars(s, chars), chars)


def py_startswith(s: str, prefix: str) -> bool:
    n = len(s)
    m = len(prefix)
    if m > n:
        return False
    i = 0
    while i < m:
        if s[i] != prefix[i]:
            return False
        i += 1
    return True


def py_endswith(s: str, suffix: str) -> bool:
    n = len(s)
    m = len(suffix)
    if m > n:
        return False
    i = 0
    base = n - m
    while i < m:
        if s[base + i] != suffix[i]:
            return False
        i += 1
    return True


def py_find(s: str, needle: str) -> int:
    return py_find_window(s, needle, 0, len(s))


def py_find_window(s: str, needle: str, start: int, end: int) -> int:
    n = len(s)
    m = len(needle)
    lo = _normalize_index(start, n)
    up = _normalize_index(end, n)
    if up < lo:
        return -1
    if m == 0:
        return lo
    i = lo
    last = up - m
    while i <= last:
        j = 0
        ok = True
        while j < m:
            if s[i + j] != needle[j]:
                ok = False
                break
            j += 1
        if ok:
            return i
        i += 1
    return -1


def py_rfind(s: str, needle: str) -> int:
    return py_rfind_window(s, needle, 0, len(s))


def py_rfind_window(s: str, needle: str, start: int, end: int) -> int:
    n = len(s)
    m = len(needle)
    lo = _normalize_index(start, n)
    up = _normalize_index(end, n)
    if up < lo:
        return -1
    if m == 0:
        return up
    i = up - m
    while i >= lo:
        j = 0
        ok = True
        while j < m:
            if s[i + j] != needle[j]:
                ok = False
                break
            j += 1
        if ok:
            return i
        i -= 1
    return -1


def py_replace(s: str, oldv: str, newv: str) -> str:
    if oldv == "":
        return s
    out = ""
    n = len(s)
    m = len(oldv)
    i = 0
    while i < n:
        if i + m <= n and py_find_window(s, oldv, i, i + m) == i:
            out += newv
            i += m
        else:
            out += s[i]
            i += 1
    return out
