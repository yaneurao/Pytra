// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/string_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

function _is_space(ch) {
    return ch === " " || ch === "\t" || ch === "\n" || ch === "\r";
}

function _contains_char(chars, ch) {
    let i = 0;
    let n = (chars).length;
    while (i < n) {
        if (chars[(((i) < 0) ? ((chars).length + (i)) : (i))] === ch) {
            return true;
        }
        i += 1;
    }
    return false;
}

function _normalize_index(idx, n) {
    let out = idx;
    if (out < 0) {
        out += n;
    }
    if (out < 0) {
        out = 0;
    }
    if (out > n) {
        out = n;
    }
    return out;
}

function py_join(sep, parts) {
    let n = (parts).length;
    if (n === 0) {
        return "";
    }
    let out = "";
    let i = 0;
    while (i < n) {
        if (i > 0) {
            out += sep;
        }
        out += parts[(((i) < 0) ? ((parts).length + (i)) : (i))];
        i += 1;
    }
    return out;
}

function py_split(s, sep, maxsplit) {
    let out = [];
    if (sep === "") {
        out.push(s);
        return out;
    }
    let pos = 0;
    let splits = 0;
    let n = (s).length;
    let m = (sep).length;
    let unlimited = maxsplit < 0;
    while (true) {
        if (!unlimited && splits >= maxsplit) {
            break;
        }
        let at = py_find_window(s, sep, pos, n);
        if (at < 0) {
            break;
        }
        out.push(s.slice(pos, at));
        pos = at + m;
        splits += 1;
    }
    out.push(s.slice(pos, n));
    return out;
}

function py_splitlines(s) {
    let out = [];
    let n = (s).length;
    let start = 0;
    let i = 0;
    while (i < n) {
        let ch = s[(((i) < 0) ? ((s).length + (i)) : (i))];
        if (ch === "\n" || ch === "\r") {
            out.push(s.slice(start, i));
            if (ch === "\r" && i + 1 < n && s[(((i + 1) < 0) ? ((s).length + (i + 1)) : (i + 1))] === "\n") {
                i += 1;
            }
            i += 1;
            start = i;
            continue;
        }
        i += 1;
    }
    if (start < n) {
        out.push(s.slice(start, n));
    } else {
        if (n > 0) {
            let last = s[(((n - 1) < 0) ? ((s).length + (n - 1)) : (n - 1))];
            if (last === "\n" || last === "\r") {
                out.push("");
            }
        }
    }
    return out;
}

function py_count(s, needle) {
    if (needle === "") {
        return (s).length + 1;
    }
    let out = 0;
    let pos = 0;
    let n = (s).length;
    let m = (needle).length;
    while (true) {
        let at = py_find_window(s, needle, pos, n);
        if (at < 0) {
            return out;
        }
        out += 1;
        pos = at + m;
    }
}

function py_lstrip(s) {
    let i = 0;
    let n = (s).length;
    while (i < n && _is_space(s[(((i) < 0) ? ((s).length + (i)) : (i))])) {
        i += 1;
    }
    return s.slice(i, n);
}

function py_lstrip_chars(s, chars) {
    let i = 0;
    let n = (s).length;
    while (i < n && _contains_char(chars, s[(((i) < 0) ? ((s).length + (i)) : (i))])) {
        i += 1;
    }
    return s.slice(i, n);
}

function py_rstrip(s) {
    let n = (s).length;
    let i = n - 1;
    while (i >= 0 && _is_space(s[(((i) < 0) ? ((s).length + (i)) : (i))])) {
        i -= 1;
    }
    return s.slice(0, i + 1);
}

function py_rstrip_chars(s, chars) {
    let n = (s).length;
    let i = n - 1;
    while (i >= 0 && _contains_char(chars, s[(((i) < 0) ? ((s).length + (i)) : (i))])) {
        i -= 1;
    }
    return s.slice(0, i + 1);
}

function py_strip(s) {
    return py_rstrip(py_lstrip(s));
}

function py_strip_chars(s, chars) {
    return py_rstrip_chars(py_lstrip_chars(s, chars), chars);
}

function py_startswith(s, prefix) {
    let n = (s).length;
    let m = (prefix).length;
    if (m > n) {
        return false;
    }
    let i = 0;
    while (i < m) {
        if (s[(((i) < 0) ? ((s).length + (i)) : (i))] !== prefix[(((i) < 0) ? ((prefix).length + (i)) : (i))]) {
            return false;
        }
        i += 1;
    }
    return true;
}

function py_endswith(s, suffix) {
    let n = (s).length;
    let m = (suffix).length;
    if (m > n) {
        return false;
    }
    let i = 0;
    let base = n - m;
    while (i < m) {
        if (s[(((base + i) < 0) ? ((s).length + (base + i)) : (base + i))] !== suffix[(((i) < 0) ? ((suffix).length + (i)) : (i))]) {
            return false;
        }
        i += 1;
    }
    return true;
}

function py_find(s, needle) {
    return py_find_window(s, needle, 0, (s).length);
}

function py_find_window(s, needle, start, end) {
    let n = (s).length;
    let m = (needle).length;
    let lo = _normalize_index(start, n);
    let up = _normalize_index(end, n);
    if (up < lo) {
        return -1;
    }
    if (m === 0) {
        return lo;
    }
    let i = lo;
    let last = up - m;
    while (i <= last) {
        let j = 0;
        let ok = true;
        while (j < m) {
            if (s[(((i + j) < 0) ? ((s).length + (i + j)) : (i + j))] !== needle[(((j) < 0) ? ((needle).length + (j)) : (j))]) {
                ok = false;
                break;
            }
            j += 1;
        }
        if (ok) {
            return i;
        }
        i += 1;
    }
    return -1;
}

function py_rfind(s, needle) {
    return py_rfind_window(s, needle, 0, (s).length);
}

function py_rfind_window(s, needle, start, end) {
    let n = (s).length;
    let m = (needle).length;
    let lo = _normalize_index(start, n);
    let up = _normalize_index(end, n);
    if (up < lo) {
        return -1;
    }
    if (m === 0) {
        return up;
    }
    let i = up - m;
    while (i >= lo) {
        let j = 0;
        let ok = true;
        while (j < m) {
            if (s[(((i + j) < 0) ? ((s).length + (i + j)) : (i + j))] !== needle[(((j) < 0) ? ((needle).length + (j)) : (j))]) {
                ok = false;
                break;
            }
            j += 1;
        }
        if (ok) {
            return i;
        }
        i -= 1;
    }
    return -1;
}

function py_replace(s, oldv, newv) {
    if (oldv === "") {
        return s;
    }
    let out = "";
    let n = (s).length;
    let m = (oldv).length;
    let i = 0;
    while (i < n) {
        if (i + m <= n && py_find_window(s, oldv, i, i + m) === i) {
            out += newv;
            i += m;
        } else {
            out += s[(((i) < 0) ? ((s).length + (i)) : (i))];
            i += 1;
        }
    }
    return out;
}

module.exports = {py_join, py_split, py_splitlines, py_count, py_lstrip, py_lstrip_chars, py_rstrip, py_rstrip_chars, py_strip, py_strip_chars, py_startswith, py_endswith, py_find, py_find_window, py_rfind, py_rfind_window, py_replace};
