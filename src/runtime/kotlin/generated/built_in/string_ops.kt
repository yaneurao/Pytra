// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/string_ops.py
// generated-by: tools/gen_runtime_from_manifest.py



fun _is_space(ch: String): Boolean {
    return ((__pytra_str(ch) == __pytra_str(" ")) || (__pytra_str(ch) == __pytra_str("	")) || (__pytra_str(ch) == __pytra_str("\n")) || (__pytra_str(ch) == __pytra_str("
")))
}

fun _contains_char(chars: String, ch: String): Boolean {
    var i: Long = 0L
    var n: Long = __pytra_len(chars)
    while ((__pytra_int(i) < __pytra_int(n))) {
        if ((__pytra_str(__pytra_get_index(chars, i)) == __pytra_str(ch))) {
            return true
        }
        i += 1L
    }
    return false
}

fun _normalize_index(idx: Long, n: Long): Long {
    var out: Long = idx
    if ((__pytra_int(out) < __pytra_int(0L))) {
        out += n
    }
    if ((__pytra_int(out) < __pytra_int(0L))) {
        out = 0L
    }
    if ((__pytra_int(out) > __pytra_int(n))) {
        out = n
    }
    return out
}

fun py_join(sep: String, parts: MutableList<Any?>): String {
    var n: Long = __pytra_len(parts)
    if ((__pytra_int(n) == __pytra_int(0L))) {
        return ""
    }
    var out: String = ""
    var i: Long = 0L
    while ((__pytra_int(i) < __pytra_int(n))) {
        if ((__pytra_int(i) > __pytra_int(0L))) {
            out += sep
        }
        out += __pytra_str(__pytra_get_index(parts, i))
        i += 1L
    }
    return out
}

fun py_split(s: String, sep: String, maxsplit: Long): MutableList<Any?> {
    var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    if ((__pytra_str(sep) == __pytra_str(""))) {
        out.add(s)
        return out
    }
    var pos: Long = 0L
    var splits: Long = 0L
    var n: Long = __pytra_len(s)
    var m: Long = __pytra_len(sep)
    var unlimited: Boolean = (__pytra_int(maxsplit) < __pytra_int(0L))
    while (true) {
        if (((!unlimited) && (__pytra_int(splits) >= __pytra_int(maxsplit)))) {
            break
        }
        var at: Long = py_find_window(s, sep, pos, n)
        if ((__pytra_int(at) < __pytra_int(0L))) {
            break
        }
        out.add(__pytra_slice(s, pos, at))
        pos = (at + m)
        splits += 1L
    }
    out.add(__pytra_slice(s, pos, n))
    return out
}

fun py_splitlines(s: String): MutableList<Any?> {
    var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var n: Long = __pytra_len(s)
    var start: Long = 0L
    var i: Long = 0L
    while ((__pytra_int(i) < __pytra_int(n))) {
        var ch: String = __pytra_str(__pytra_get_index(s, i))
        if (((__pytra_str(ch) == __pytra_str("\n")) || (__pytra_str(ch) == __pytra_str("
")))) {
            out.add(__pytra_slice(s, start, i))
            if (((__pytra_str(ch) == __pytra_str("
")) && (__pytra_int(i + 1L) < __pytra_int(n)) && (__pytra_str(__pytra_get_index(s, (i + 1L))) == __pytra_str("\n")))) {
                i += 1L
            }
            i += 1L
            start = i
            continue
        }
        i += 1L
    }
    if ((__pytra_int(start) < __pytra_int(n))) {
        out.add(__pytra_slice(s, start, n))
    } else {
        if ((__pytra_int(n) > __pytra_int(0L))) {
            var last: String = __pytra_str(__pytra_get_index(s, (n - 1L)))
            if (((__pytra_str(last) == __pytra_str("\n")) || (__pytra_str(last) == __pytra_str("
")))) {
                out.add("")
            }
        }
    }
    return out
}

fun py_count(s: String, needle: String): Long {
    if ((__pytra_str(needle) == __pytra_str(""))) {
        return (__pytra_len(s) + 1L)
    }
    var out: Long = 0L
    var pos: Long = 0L
    var n: Long = __pytra_len(s)
    var m: Long = __pytra_len(needle)
    while (true) {
        var at: Long = py_find_window(s, needle, pos, n)
        if ((__pytra_int(at) < __pytra_int(0L))) {
            return out
        }
        out += 1L
        pos = (at + m)
    }
    return 0L
}

fun py_lstrip(s: String): String {
    var i: Long = 0L
    var n: Long = __pytra_len(s)
    while (((__pytra_int(i) < __pytra_int(n)) && _is_space(__pytra_str(__pytra_get_index(s, i))))) {
        i += 1L
    }
    return __pytra_str(__pytra_slice(s, i, n))
}

fun py_lstrip_chars(s: String, chars: String): String {
    var i: Long = 0L
    var n: Long = __pytra_len(s)
    while (((__pytra_int(i) < __pytra_int(n)) && _contains_char(chars, __pytra_str(__pytra_get_index(s, i))))) {
        i += 1L
    }
    return __pytra_str(__pytra_slice(s, i, n))
}

fun py_rstrip(s: String): String {
    var n: Long = __pytra_len(s)
    var i: Long = (n - 1L)
    while (((__pytra_int(i) >= __pytra_int(0L)) && _is_space(__pytra_str(__pytra_get_index(s, i))))) {
        i -= 1L
    }
    return __pytra_str(__pytra_slice(s, 0L, (i + 1L)))
}

fun py_rstrip_chars(s: String, chars: String): String {
    var n: Long = __pytra_len(s)
    var i: Long = (n - 1L)
    while (((__pytra_int(i) >= __pytra_int(0L)) && _contains_char(chars, __pytra_str(__pytra_get_index(s, i))))) {
        i -= 1L
    }
    return __pytra_str(__pytra_slice(s, 0L, (i + 1L)))
}

fun py_strip(s: String): String {
    return py_rstrip(py_lstrip(s))
}

fun py_strip_chars(s: String, chars: String): String {
    return py_rstrip_chars(py_lstrip_chars(s, chars), chars)
}

fun py_startswith(s: String, prefix: String): Boolean {
    var n: Long = __pytra_len(s)
    var m: Long = __pytra_len(prefix)
    if ((__pytra_int(m) > __pytra_int(n))) {
        return false
    }
    var i: Long = 0L
    while ((__pytra_int(i) < __pytra_int(m))) {
        if ((__pytra_str(__pytra_get_index(s, i)) != __pytra_str(__pytra_get_index(prefix, i)))) {
            return false
        }
        i += 1L
    }
    return true
}

fun py_endswith(s: String, suffix: String): Boolean {
    var n: Long = __pytra_len(s)
    var m: Long = __pytra_len(suffix)
    if ((__pytra_int(m) > __pytra_int(n))) {
        return false
    }
    var i: Long = 0L
    var base: Long = (n - m)
    while ((__pytra_int(i) < __pytra_int(m))) {
        if ((__pytra_str(__pytra_get_index(s, (base + i))) != __pytra_str(__pytra_get_index(suffix, i)))) {
            return false
        }
        i += 1L
    }
    return true
}

fun py_find(s: String, needle: String): Long {
    return py_find_window(s, needle, 0L, __pytra_len(s))
}

fun py_find_window(s: String, needle: String, start: Long, end: Long): Long {
    var n: Long = __pytra_len(s)
    var m: Long = __pytra_len(needle)
    var lo: Long = _normalize_index(start, n)
    var up: Long = _normalize_index(end, n)
    if ((__pytra_int(up) < __pytra_int(lo))) {
        return __pytra_int(-1L)
    }
    if ((__pytra_int(m) == __pytra_int(0L))) {
        return lo
    }
    var i: Long = lo
    var last: Long = (up - m)
    while ((__pytra_int(i) <= __pytra_int(last))) {
        var j: Long = 0L
        var ok: Boolean = true
        while ((__pytra_int(j) < __pytra_int(m))) {
            if ((__pytra_str(__pytra_get_index(s, (i + j))) != __pytra_str(__pytra_get_index(needle, j)))) {
                ok = false
                break
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

fun py_rfind(s: String, needle: String): Long {
    return py_rfind_window(s, needle, 0L, __pytra_len(s))
}

fun py_rfind_window(s: String, needle: String, start: Long, end: Long): Long {
    var n: Long = __pytra_len(s)
    var m: Long = __pytra_len(needle)
    var lo: Long = _normalize_index(start, n)
    var up: Long = _normalize_index(end, n)
    if ((__pytra_int(up) < __pytra_int(lo))) {
        return __pytra_int(-1L)
    }
    if ((__pytra_int(m) == __pytra_int(0L))) {
        return up
    }
    var i: Long = (up - m)
    while ((__pytra_int(i) >= __pytra_int(lo))) {
        var j: Long = 0L
        var ok: Boolean = true
        while ((__pytra_int(j) < __pytra_int(m))) {
            if ((__pytra_str(__pytra_get_index(s, (i + j))) != __pytra_str(__pytra_get_index(needle, j)))) {
                ok = false
                break
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

fun py_replace(s: String, oldv: String, newv: String): String {
    if ((__pytra_str(oldv) == __pytra_str(""))) {
        return s
    }
    var out: String = ""
    var n: Long = __pytra_len(s)
    var m: Long = __pytra_len(oldv)
    var i: Long = 0L
    while ((__pytra_int(i) < __pytra_int(n))) {
        if (((__pytra_int(i + m) <= __pytra_int(n)) && (__pytra_int(py_find_window(s, oldv, i, (i + m))) == __pytra_int(i)))) {
            out += newv
            i += m
        } else {
            out += __pytra_str(__pytra_get_index(s, i))
            i += 1L
        }
    }
    return out
}
