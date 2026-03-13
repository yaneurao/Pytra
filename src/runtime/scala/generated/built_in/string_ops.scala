// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/string_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def _is_space(ch: String): Boolean = {
    return ((__pytra_str(ch) == __pytra_str(" ")) || (__pytra_str(ch) == __pytra_str("	")) || (__pytra_str(ch) == __pytra_str("\n")) || (__pytra_str(ch) == __pytra_str("
")))
}

def _contains_char(chars: String, ch: String): Boolean = {
    var i: Long = 0L
    var n: Long = __pytra_len(chars)
    while (i < n) {
        if (__pytra_str(__pytra_get_index(chars, i)) == __pytra_str(ch)) {
            return true
        }
        i += 1L
    }
    return false
}

def _normalize_index(idx: Long, n: Long): Long = {
    var out: Long = idx
    if (out < 0L) {
        out += n
    }
    if (out < 0L) {
        out = 0L
    }
    if (out > n) {
        out = n
    }
    return out
}

def py_join(sep: String, parts: mutable.ArrayBuffer[String]): String = {
    var n: Long = __pytra_len(parts)
    if (n == 0L) {
        return ""
    }
    var out: String = ""
    var i: Long = 0L
    while (i < n) {
        if (i > 0L) {
            out += sep
        }
        out += __pytra_str(__pytra_get_index(parts, i))
        i += 1L
    }
    return out
}

def py_split(s: String, sep: String, maxsplit: Long): mutable.ArrayBuffer[String] = {
    var out: mutable.ArrayBuffer[String] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[String]]
    if (__pytra_str(sep) == __pytra_str("")) {
        out.append(s)
        return out
    }
    var pos: Long = 0L
    var splits: Long = 0L
    var n: Long = __pytra_len(s)
    var m: Long = __pytra_len(sep)
    var unlimited: Boolean = (maxsplit < 0L)
    boundary:
        given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        while (true) {
            boundary:
                given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                if ((!unlimited) && (splits >= maxsplit)) {
                    break(())(using __breakLabel_0)
                }
                var at: Long = py_find_window(s, sep, pos, n)
                if (at < 0L) {
                    break(())(using __breakLabel_0)
                }
                out.append(__pytra_slice(s, pos, at))
                pos = at + m
                splits += 1L
        }
    out.append(__pytra_slice(s, pos, n))
    return out
}

def py_splitlines(s: String): mutable.ArrayBuffer[String] = {
    var out: mutable.ArrayBuffer[String] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[String]]
    var n: Long = __pytra_len(s)
    var start: Long = 0L
    var i: Long = 0L
    boundary:
        given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        while (i < n) {
            boundary:
                given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                var ch: String = __pytra_str(__pytra_get_index(s, i))
                if ((__pytra_str(ch) == __pytra_str("\n")) || (__pytra_str(ch) == __pytra_str("
"))) {
                    out.append(__pytra_slice(s, start, i))
                    if ((__pytra_str(ch) == __pytra_str("
")) && (i + 1L < n) && (__pytra_str(__pytra_get_index(s, i + 1L)) == __pytra_str("\n"))) {
                        i += 1L
                    }
                    i += 1L
                    start = i
                    break(())(using __continueLabel_1)
                }
                i += 1L
        }
    if (start < n) {
        out.append(__pytra_slice(s, start, n))
    } else {
        if (n > 0L) {
            var last: String = __pytra_str(__pytra_get_index(s, n - 1L))
            if ((__pytra_str(last) == __pytra_str("\n")) || (__pytra_str(last) == __pytra_str("
"))) {
                out.append("")
            }
        }
    }
    return out
}

def py_count(s: String, needle: String): Long = {
    if (__pytra_str(needle) == __pytra_str("")) {
        return __pytra_len(s) + 1L
    }
    var out: Long = 0L
    var pos: Long = 0L
    var n: Long = __pytra_len(s)
    var m: Long = __pytra_len(needle)
    while (true) {
        var at: Long = py_find_window(s, needle, pos, n)
        if (at < 0L) {
            return out
        }
        out += 1L
        pos = at + m
    }
    return 0L
}

def py_lstrip(s: String): String = {
    var i: Long = 0L
    var n: Long = __pytra_len(s)
    while ((i < n) && _is_space(__pytra_str(__pytra_get_index(s, i)))) {
        i += 1L
    }
    return __pytra_str(__pytra_slice(s, i, n))
}

def py_lstrip_chars(s: String, chars: String): String = {
    var i: Long = 0L
    var n: Long = __pytra_len(s)
    while ((i < n) && _contains_char(chars, __pytra_str(__pytra_get_index(s, i)))) {
        i += 1L
    }
    return __pytra_str(__pytra_slice(s, i, n))
}

def py_rstrip(s: String): String = {
    var n: Long = __pytra_len(s)
    var i: Long = n - 1L
    while ((i >= 0L) && _is_space(__pytra_str(__pytra_get_index(s, i)))) {
        i -= 1L
    }
    return __pytra_str(__pytra_slice(s, 0L, i + 1L))
}

def py_rstrip_chars(s: String, chars: String): String = {
    var n: Long = __pytra_len(s)
    var i: Long = n - 1L
    while ((i >= 0L) && _contains_char(chars, __pytra_str(__pytra_get_index(s, i)))) {
        i -= 1L
    }
    return __pytra_str(__pytra_slice(s, 0L, i + 1L))
}

def py_strip(s: String): String = {
    return py_rstrip(py_lstrip(s))
}

def py_strip_chars(s: String, chars: String): String = {
    return py_rstrip_chars(py_lstrip_chars(s, chars), chars)
}

def py_startswith(s: String, prefix: String): Boolean = {
    var n: Long = __pytra_len(s)
    var m: Long = __pytra_len(prefix)
    if (m > n) {
        return false
    }
    var i: Long = 0L
    while (i < m) {
        if (__pytra_str(__pytra_get_index(s, i)) != __pytra_str(__pytra_get_index(prefix, i))) {
            return false
        }
        i += 1L
    }
    return true
}

def py_endswith(s: String, suffix: String): Boolean = {
    var n: Long = __pytra_len(s)
    var m: Long = __pytra_len(suffix)
    if (m > n) {
        return false
    }
    var i: Long = 0L
    var base: Long = n - m
    while (i < m) {
        if (__pytra_str(__pytra_get_index(s, base + i)) != __pytra_str(__pytra_get_index(suffix, i))) {
            return false
        }
        i += 1L
    }
    return true
}

def py_find(s: String, needle: String): Long = {
    return py_find_window(s, needle, 0L, __pytra_len(s))
}

def py_find_window(s: String, needle: String, start: Long, end: Long): Long = {
    var n: Long = __pytra_len(s)
    var m: Long = __pytra_len(needle)
    var lo: Long = _normalize_index(start, n)
    var up: Long = _normalize_index(end, n)
    if (up < lo) {
        return __pytra_int(-1L)
    }
    if (m == 0L) {
        return lo
    }
    var i: Long = lo
    var last: Long = up - m
    while (i <= last) {
        var j: Long = 0L
        var ok: Boolean = true
        boundary:
            given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
            while (j < m) {
                boundary:
                    given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    if (__pytra_str(__pytra_get_index(s, i + j)) != __pytra_str(__pytra_get_index(needle, j))) {
                        ok = false
                        break(())(using __breakLabel_0)
                    }
                    j += 1L
            }
        if (ok) {
            return i
        }
        i += 1L
    }
    return __pytra_int(-1L)
}

def py_rfind(s: String, needle: String): Long = {
    return py_rfind_window(s, needle, 0L, __pytra_len(s))
}

def py_rfind_window(s: String, needle: String, start: Long, end: Long): Long = {
    var n: Long = __pytra_len(s)
    var m: Long = __pytra_len(needle)
    var lo: Long = _normalize_index(start, n)
    var up: Long = _normalize_index(end, n)
    if (up < lo) {
        return __pytra_int(-1L)
    }
    if (m == 0L) {
        return up
    }
    var i: Long = up - m
    while (i >= lo) {
        var j: Long = 0L
        var ok: Boolean = true
        boundary:
            given __breakLabel_0: boundary.Label[Unit] = summon[boundary.Label[Unit]]
            while (j < m) {
                boundary:
                    given __continueLabel_1: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                    if (__pytra_str(__pytra_get_index(s, i + j)) != __pytra_str(__pytra_get_index(needle, j))) {
                        ok = false
                        break(())(using __breakLabel_0)
                    }
                    j += 1L
            }
        if (ok) {
            return i
        }
        i -= 1L
    }
    return __pytra_int(-1L)
}

def py_replace(s: String, oldv: String, newv: String): String = {
    if (__pytra_str(oldv) == __pytra_str("")) {
        return s
    }
    var out: String = ""
    var n: Long = __pytra_len(s)
    var m: Long = __pytra_len(oldv)
    var i: Long = 0L
    while (i < n) {
        if ((i + m <= n) && (py_find_window(s, oldv, i, i + m) == i)) {
            out += newv
            i += m
        } else {
            out += __pytra_str(__pytra_get_index(s, i))
            i += 1L
        }
    }
    return out
}
