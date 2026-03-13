// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/string_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func _is_space(ch string) bool {
    return __pytra_truthy(((__pytra_str(ch) == __pytra_str(" ")) || (__pytra_str(ch) == __pytra_str("	")) || (__pytra_str(ch) == __pytra_str("\n")) || (__pytra_str(ch) == __pytra_str("
"))))
}

func _contains_char(chars string, ch string) bool {
    var i int64 = int64(0)
    var n int64 = __pytra_len(chars)
    for (i < n) {
        if (__pytra_str(__pytra_str(__pytra_get_index(chars, i))) == __pytra_str(ch)) {
            return __pytra_truthy(true)
        }
        i += int64(1)
    }
    return __pytra_truthy(false)
}

func _normalize_index(idx int64, n int64) int64 {
    var out int64 = idx
    if (out < int64(0)) {
        out += n
    }
    if (out < int64(0)) {
        out = int64(0)
    }
    if (out > n) {
        out = n
    }
    return out
}

func py_join(sep string, parts []any) string {
    var n int64 = __pytra_len(parts)
    if (n == int64(0)) {
        return __pytra_str("")
    }
    var out string = __pytra_str("")
    var i int64 = int64(0)
    for (i < n) {
        if (i > int64(0)) {
            out += sep
        }
        out += __pytra_str(__pytra_get_index(parts, i))
        i += int64(1)
    }
    return __pytra_str(out)
}

func py_split(s string, sep string, maxsplit int64) []any {
    var out []any = __pytra_as_list([]any{})
    if (__pytra_str(sep) == __pytra_str("")) {
        out = append(out, s)
        return __pytra_as_list(out)
    }
    var pos int64 = int64(0)
    var splits int64 = int64(0)
    var n int64 = __pytra_len(s)
    var m int64 = __pytra_len(sep)
    var unlimited bool = __pytra_truthy((maxsplit < int64(0)))
    for true {
        if ((!unlimited) && (splits >= maxsplit)) {
            break
        }
        var at int64 = py_find_window(s, sep, pos, n)
        if (at < int64(0)) {
            break
        }
        out = append(out, __pytra_slice(s, pos, at))
        pos = (at + m)
        splits += int64(1)
    }
    out = append(out, __pytra_slice(s, pos, n))
    return __pytra_as_list(out)
}

func py_splitlines(s string) []any {
    var out []any = __pytra_as_list([]any{})
    var n int64 = __pytra_len(s)
    var start int64 = int64(0)
    var i int64 = int64(0)
    for (i < n) {
        var ch string = __pytra_str(__pytra_str(__pytra_get_index(s, i)))
        if ((__pytra_str(ch) == __pytra_str("\n")) || (__pytra_str(ch) == __pytra_str("
"))) {
            out = append(out, __pytra_slice(s, start, i))
            if ((__pytra_str(ch) == __pytra_str("
")) && ((i + int64(1)) < n) && (__pytra_str(__pytra_str(__pytra_get_index(s, (i + int64(1))))) == __pytra_str("\n"))) {
                i += int64(1)
            }
            i += int64(1)
            start = i
            continue
        }
        i += int64(1)
    }
    if (start < n) {
        out = append(out, __pytra_slice(s, start, n))
    } else {
        if (n > int64(0)) {
            var last string = __pytra_str(__pytra_str(__pytra_get_index(s, (n - int64(1)))))
            if ((__pytra_str(last) == __pytra_str("\n")) || (__pytra_str(last) == __pytra_str("
"))) {
                out = append(out, "")
            }
        }
    }
    return __pytra_as_list(out)
}

func py_count(s string, needle string) int64 {
    if (__pytra_str(needle) == __pytra_str("")) {
        return (__pytra_len(s) + int64(1))
    }
    var out int64 = int64(0)
    var pos int64 = int64(0)
    var n int64 = __pytra_len(s)
    var m int64 = __pytra_len(needle)
    for true {
        var at int64 = py_find_window(s, needle, pos, n)
        if (at < int64(0)) {
            return out
        }
        out += int64(1)
        pos = (at + m)
    }
    return 0
}

func py_lstrip(s string) string {
    var i int64 = int64(0)
    var n int64 = __pytra_len(s)
    for ((i < n) && _is_space(__pytra_str(__pytra_get_index(s, i)))) {
        i += int64(1)
    }
    return __pytra_str(__pytra_slice(s, i, n))
}

func py_lstrip_chars(s string, chars string) string {
    var i int64 = int64(0)
    var n int64 = __pytra_len(s)
    for ((i < n) && _contains_char(chars, __pytra_str(__pytra_get_index(s, i)))) {
        i += int64(1)
    }
    return __pytra_str(__pytra_slice(s, i, n))
}

func py_rstrip(s string) string {
    var n int64 = __pytra_len(s)
    var i int64 = (n - int64(1))
    for ((i >= int64(0)) && _is_space(__pytra_str(__pytra_get_index(s, i)))) {
        i -= int64(1)
    }
    return __pytra_str(__pytra_slice(s, int64(0), (i + int64(1))))
}

func py_rstrip_chars(s string, chars string) string {
    var n int64 = __pytra_len(s)
    var i int64 = (n - int64(1))
    for ((i >= int64(0)) && _contains_char(chars, __pytra_str(__pytra_get_index(s, i)))) {
        i -= int64(1)
    }
    return __pytra_str(__pytra_slice(s, int64(0), (i + int64(1))))
}

func py_strip(s string) string {
    return __pytra_str(py_rstrip(py_lstrip(s)))
}

func py_strip_chars(s string, chars string) string {
    return __pytra_str(py_rstrip_chars(py_lstrip_chars(s, chars), chars))
}

func py_startswith(s string, prefix string) bool {
    var n int64 = __pytra_len(s)
    var m int64 = __pytra_len(prefix)
    if (m > n) {
        return __pytra_truthy(false)
    }
    var i int64 = int64(0)
    for (i < m) {
        if (__pytra_str(__pytra_str(__pytra_get_index(s, i))) != __pytra_str(__pytra_str(__pytra_get_index(prefix, i)))) {
            return __pytra_truthy(false)
        }
        i += int64(1)
    }
    return __pytra_truthy(true)
}

func py_endswith(s string, suffix string) bool {
    var n int64 = __pytra_len(s)
    var m int64 = __pytra_len(suffix)
    if (m > n) {
        return __pytra_truthy(false)
    }
    var i int64 = int64(0)
    var base int64 = (n - m)
    for (i < m) {
        if (__pytra_str(__pytra_str(__pytra_get_index(s, (base + i)))) != __pytra_str(__pytra_str(__pytra_get_index(suffix, i)))) {
            return __pytra_truthy(false)
        }
        i += int64(1)
    }
    return __pytra_truthy(true)
}

func py_find(s string, needle string) int64 {
    return py_find_window(s, needle, int64(0), __pytra_len(s))
}

func py_find_window(s string, needle string, start int64, end int64) int64 {
    var n int64 = __pytra_len(s)
    var m int64 = __pytra_len(needle)
    var lo int64 = _normalize_index(start, n)
    var up int64 = _normalize_index(end, n)
    if (up < lo) {
        return (-int64(1))
    }
    if (m == int64(0)) {
        return lo
    }
    var i int64 = lo
    var last int64 = (up - m)
    for (i <= last) {
        var j int64 = int64(0)
        var ok bool = __pytra_truthy(true)
        for (j < m) {
            if (__pytra_str(__pytra_str(__pytra_get_index(s, (i + j)))) != __pytra_str(__pytra_str(__pytra_get_index(needle, j)))) {
                ok = __pytra_truthy(false)
                break
            }
            j += int64(1)
        }
        if ok {
            return i
        }
        i += int64(1)
    }
    return (-int64(1))
}

func py_rfind(s string, needle string) int64 {
    return py_rfind_window(s, needle, int64(0), __pytra_len(s))
}

func py_rfind_window(s string, needle string, start int64, end int64) int64 {
    var n int64 = __pytra_len(s)
    var m int64 = __pytra_len(needle)
    var lo int64 = _normalize_index(start, n)
    var up int64 = _normalize_index(end, n)
    if (up < lo) {
        return (-int64(1))
    }
    if (m == int64(0)) {
        return up
    }
    var i int64 = (up - m)
    for (i >= lo) {
        var j int64 = int64(0)
        var ok bool = __pytra_truthy(true)
        for (j < m) {
            if (__pytra_str(__pytra_str(__pytra_get_index(s, (i + j)))) != __pytra_str(__pytra_str(__pytra_get_index(needle, j)))) {
                ok = __pytra_truthy(false)
                break
            }
            j += int64(1)
        }
        if ok {
            return i
        }
        i -= int64(1)
    }
    return (-int64(1))
}

func py_replace(s string, oldv string, newv string) string {
    if (__pytra_str(oldv) == __pytra_str("")) {
        return __pytra_str(s)
    }
    var out string = __pytra_str("")
    var n int64 = __pytra_len(s)
    var m int64 = __pytra_len(oldv)
    var i int64 = int64(0)
    for (i < n) {
        if (((i + m) <= n) && (py_find_window(s, oldv, i, (i + m)) == i)) {
            out += newv
            i += m
        } else {
            out += __pytra_str(__pytra_get_index(s, i))
            i += int64(1)
        }
    }
    return __pytra_str(out)
}
