// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/string_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func _is_space(_ ch: String) -> Bool {
    return ((__pytra_str(ch) == __pytra_str(" ")) || (__pytra_str(ch) == __pytra_str("	")) || (__pytra_str(ch) == __pytra_str("\n")) || (__pytra_str(ch) == __pytra_str("
")))
}

func _contains_char(_ chars: String, _ ch: String) -> Bool {
    var i: Int64 = Int64(0)
    var n: Int64 = __pytra_len(chars)
    while (__pytra_int(i) < __pytra_int(n)) {
        if (__pytra_str(__pytra_getIndex(chars, i)) == __pytra_str(ch)) {
            return true
        }
        i += Int64(1)
    }
    return false
}

func _normalize_index(_ idx: Int64, _ n: Int64) -> Int64 {
    var out: Int64 = idx
    if (__pytra_int(out) < __pytra_int(Int64(0))) {
        out += n
    }
    if (__pytra_int(out) < __pytra_int(Int64(0))) {
        out = Int64(0)
    }
    if (__pytra_int(out) > __pytra_int(n)) {
        out = n
    }
    return out
}

func py_join(_ sep: String, _ parts: [Any]) -> String {
    var n: Int64 = __pytra_len(parts)
    if (__pytra_int(n) == __pytra_int(Int64(0))) {
        return ""
    }
    var out: String = ""
    var i: Int64 = Int64(0)
    while (__pytra_int(i) < __pytra_int(n)) {
        if (__pytra_int(i) > __pytra_int(Int64(0))) {
            out += sep
        }
        out += __pytra_str(__pytra_getIndex(parts, i))
        i += Int64(1)
    }
    return out
}

func py_split(_ s: String, _ sep: String, _ maxsplit: Int64) -> [Any] {
    var out: [Any] = __pytra_as_list([])
    if (__pytra_str(sep) == __pytra_str("")) {
        out.append(s)
        return out
    }
    var pos: Int64 = Int64(0)
    var splits: Int64 = Int64(0)
    var n: Int64 = __pytra_len(s)
    var m: Int64 = __pytra_len(sep)
    var unlimited: Bool = (__pytra_int(maxsplit) < __pytra_int(Int64(0)))
    while true {
        if ((!unlimited) && (__pytra_int(splits) >= __pytra_int(maxsplit))) {
            break
        }
        var at: Int64 = py_find_window(s, sep, pos, n)
        if (__pytra_int(at) < __pytra_int(Int64(0))) {
            break
        }
        out.append(__pytra_slice(s, pos, at))
        pos = (at + m)
        splits += Int64(1)
    }
    out.append(__pytra_slice(s, pos, n))
    return out
}

func py_splitlines(_ s: String) -> [Any] {
    var out: [Any] = __pytra_as_list([])
    var n: Int64 = __pytra_len(s)
    var start: Int64 = Int64(0)
    var i: Int64 = Int64(0)
    while (__pytra_int(i) < __pytra_int(n)) {
        var ch: String = __pytra_str(__pytra_getIndex(s, i))
        if ((__pytra_str(ch) == __pytra_str("\n")) || (__pytra_str(ch) == __pytra_str("
"))) {
            out.append(__pytra_slice(s, start, i))
            if ((__pytra_str(ch) == __pytra_str("
")) && (__pytra_int(i + Int64(1)) < __pytra_int(n)) && (__pytra_str(__pytra_getIndex(s, (i + Int64(1)))) == __pytra_str("\n"))) {
                i += Int64(1)
            }
            i += Int64(1)
            start = i
            continue
        }
        i += Int64(1)
    }
    if (__pytra_int(start) < __pytra_int(n)) {
        out.append(__pytra_slice(s, start, n))
    } else {
        if (__pytra_int(n) > __pytra_int(Int64(0))) {
            var last: String = __pytra_str(__pytra_getIndex(s, (n - Int64(1))))
            if ((__pytra_str(last) == __pytra_str("\n")) || (__pytra_str(last) == __pytra_str("
"))) {
                out.append("")
            }
        }
    }
    return out
}

func py_count(_ s: String, _ needle: String) -> Int64 {
    if (__pytra_str(needle) == __pytra_str("")) {
        return (__pytra_len(s) + Int64(1))
    }
    var out: Int64 = Int64(0)
    var pos: Int64 = Int64(0)
    var n: Int64 = __pytra_len(s)
    var m: Int64 = __pytra_len(needle)
    while true {
        var at: Int64 = py_find_window(s, needle, pos, n)
        if (__pytra_int(at) < __pytra_int(Int64(0))) {
            return out
        }
        out += Int64(1)
        pos = (at + m)
    }
    return 0
}

func py_lstrip(_ s: String) -> String {
    var i: Int64 = Int64(0)
    var n: Int64 = __pytra_len(s)
    while ((__pytra_int(i) < __pytra_int(n)) && _is_space(__pytra_str(__pytra_getIndex(s, i)))) {
        i += Int64(1)
    }
    return __pytra_str(__pytra_slice(s, i, n))
}

func py_lstrip_chars(_ s: String, _ chars: String) -> String {
    var i: Int64 = Int64(0)
    var n: Int64 = __pytra_len(s)
    while ((__pytra_int(i) < __pytra_int(n)) && _contains_char(chars, __pytra_str(__pytra_getIndex(s, i)))) {
        i += Int64(1)
    }
    return __pytra_str(__pytra_slice(s, i, n))
}

func py_rstrip(_ s: String) -> String {
    var n: Int64 = __pytra_len(s)
    var i: Int64 = (n - Int64(1))
    while ((__pytra_int(i) >= __pytra_int(Int64(0))) && _is_space(__pytra_str(__pytra_getIndex(s, i)))) {
        i -= Int64(1)
    }
    return __pytra_str(__pytra_slice(s, Int64(0), (i + Int64(1))))
}

func py_rstrip_chars(_ s: String, _ chars: String) -> String {
    var n: Int64 = __pytra_len(s)
    var i: Int64 = (n - Int64(1))
    while ((__pytra_int(i) >= __pytra_int(Int64(0))) && _contains_char(chars, __pytra_str(__pytra_getIndex(s, i)))) {
        i -= Int64(1)
    }
    return __pytra_str(__pytra_slice(s, Int64(0), (i + Int64(1))))
}

func py_strip(_ s: String) -> String {
    return py_rstrip(py_lstrip(s))
}

func py_strip_chars(_ s: String, _ chars: String) -> String {
    return py_rstrip_chars(py_lstrip_chars(s, chars), chars)
}

func py_startswith(_ s: String, _ prefix: String) -> Bool {
    var n: Int64 = __pytra_len(s)
    var m: Int64 = __pytra_len(prefix)
    if (__pytra_int(m) > __pytra_int(n)) {
        return false
    }
    var i: Int64 = Int64(0)
    while (__pytra_int(i) < __pytra_int(m)) {
        if (__pytra_str(__pytra_getIndex(s, i)) != __pytra_str(__pytra_getIndex(prefix, i))) {
            return false
        }
        i += Int64(1)
    }
    return true
}

func py_endswith(_ s: String, _ suffix: String) -> Bool {
    var n: Int64 = __pytra_len(s)
    var m: Int64 = __pytra_len(suffix)
    if (__pytra_int(m) > __pytra_int(n)) {
        return false
    }
    var i: Int64 = Int64(0)
    var base: Int64 = (n - m)
    while (__pytra_int(i) < __pytra_int(m)) {
        if (__pytra_str(__pytra_getIndex(s, (base + i))) != __pytra_str(__pytra_getIndex(suffix, i))) {
            return false
        }
        i += Int64(1)
    }
    return true
}

func py_find(_ s: String, _ needle: String) -> Int64 {
    return py_find_window(s, needle, Int64(0), __pytra_len(s))
}

func py_find_window(_ s: String, _ needle: String, _ start: Int64, _ end: Int64) -> Int64 {
    var n: Int64 = __pytra_len(s)
    var m: Int64 = __pytra_len(needle)
    var lo: Int64 = _normalize_index(start, n)
    var up: Int64 = _normalize_index(end, n)
    if (__pytra_int(up) < __pytra_int(lo)) {
        return __pytra_int(-Int64(1))
    }
    if (__pytra_int(m) == __pytra_int(Int64(0))) {
        return lo
    }
    var i: Int64 = lo
    var last: Int64 = (up - m)
    while (__pytra_int(i) <= __pytra_int(last)) {
        var j: Int64 = Int64(0)
        var ok: Bool = true
        while (__pytra_int(j) < __pytra_int(m)) {
            if (__pytra_str(__pytra_getIndex(s, (i + j))) != __pytra_str(__pytra_getIndex(needle, j))) {
                ok = false
                break
            }
            j += Int64(1)
        }
        if ok {
            return i
        }
        i += Int64(1)
    }
    return __pytra_int(-Int64(1))
}

func py_rfind(_ s: String, _ needle: String) -> Int64 {
    return py_rfind_window(s, needle, Int64(0), __pytra_len(s))
}

func py_rfind_window(_ s: String, _ needle: String, _ start: Int64, _ end: Int64) -> Int64 {
    var n: Int64 = __pytra_len(s)
    var m: Int64 = __pytra_len(needle)
    var lo: Int64 = _normalize_index(start, n)
    var up: Int64 = _normalize_index(end, n)
    if (__pytra_int(up) < __pytra_int(lo)) {
        return __pytra_int(-Int64(1))
    }
    if (__pytra_int(m) == __pytra_int(Int64(0))) {
        return up
    }
    var i: Int64 = (up - m)
    while (__pytra_int(i) >= __pytra_int(lo)) {
        var j: Int64 = Int64(0)
        var ok: Bool = true
        while (__pytra_int(j) < __pytra_int(m)) {
            if (__pytra_str(__pytra_getIndex(s, (i + j))) != __pytra_str(__pytra_getIndex(needle, j))) {
                ok = false
                break
            }
            j += Int64(1)
        }
        if ok {
            return i
        }
        i -= Int64(1)
    }
    return __pytra_int(-Int64(1))
}

func py_replace(_ s: String, _ oldv: String, _ newv: String) -> String {
    if (__pytra_str(oldv) == __pytra_str("")) {
        return s
    }
    var out: String = ""
    var n: Int64 = __pytra_len(s)
    var m: Int64 = __pytra_len(oldv)
    var i: Int64 = Int64(0)
    while (__pytra_int(i) < __pytra_int(n)) {
        if ((__pytra_int(i + m) <= __pytra_int(n)) && (__pytra_int(py_find_window(s, oldv, i, (i + m))) == __pytra_int(i))) {
            out += newv
            i += m
        } else {
            out += __pytra_str(__pytra_getIndex(s, i))
            i += Int64(1)
        }
    }
    return out
}
