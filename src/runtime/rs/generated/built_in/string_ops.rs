// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/string_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::abi;

fn _is_space(ch: &str) -> bool {
    return ((ch == " ") || (ch == "\t") || (ch == "\n") || (ch == "\r"));
}

fn _contains_char(chars: &str, ch: &str) -> bool {
    let mut i = 0;
    let n = chars.len() as i64;
    while i < n {
        if py_str_at_nonneg(&chars, ((i) as usize)) == ch {
            return true;
        }
        i += 1;
    }
    return false;
}

fn _normalize_index(idx: i64, n: i64) -> i64 {
    let mut out = idx;
    if out < 0 {
        out += n;
    }
    if out < 0 {
        out = 0;
    }
    if out > n {
        out = n;
    }
    return out;
}

fn py_join(sep: &str, parts: &[String]) -> String {
    let n = parts.len() as i64;
    if n == 0 {
        return ("").to_string();
    }
    let mut out = ("").to_string();
    let mut i = 0;
    while i < n {
        if i > 0 {
            out += sep;
        }
        out += (parts[((i) as usize)]).clone();
        i += 1;
    }
    return out;
}

fn py_split(s: &str, sep: &str, maxsplit: i64) -> Vec<String> {
    let mut out: Vec<String> = vec![];
    if sep == "" {
        out.push(s);
        return out;
    }
    let mut pos = 0;
    let mut splits = 0;
    let n = s.len() as i64;
    let m = sep.len() as i64;
    let unlimited = (maxsplit < 0);
    while true {
        if !unlimited && (splits >= maxsplit) {
            break;
        }
        let at = py_find_window(s, sep, pos, n);
        if at < 0 {
            break;
        }
        out.push(py_slice_str(&s, Some((pos) as i64), Some((at) as i64)));
        pos = at + m;
        splits += 1;
    }
    out.push(py_slice_str(&s, Some((pos) as i64), Some((n) as i64)));
    return out;
}

fn py_splitlines(s: &str) -> Vec<String> {
    let mut out: Vec<String> = vec![];
    let n = s.len() as i64;
    let mut start = 0;
    let mut i = 0;
    while i < n {
        let ch = py_str_at_nonneg(&s, ((i) as usize));
        if (ch == "\n") || (ch == "\r") {
            out.push(py_slice_str(&s, Some((start) as i64), Some((i) as i64)));
            if (ch == "\r") && (i + 1 < n) && (py_str_at_nonneg(&s, ((i + 1) as usize)) == "\n") {
                i += 1;
            }
            i += 1;
            start = i;
            continue;
        }
        i += 1;
    }
    if start < n {
        out.push(py_slice_str(&s, Some((start) as i64), Some((n) as i64)));
    } else if n > 0 {
        let last = py_str_at_nonneg(&s, ((n - 1) as usize));
        if (last == "\n") || (last == "\r") {
            out.push(("").to_string());
        }
    }
    return out;
}

fn py_count(s: &str, needle: &str) -> i64 {
    if needle == "" {
        return s.len() as i64 + 1;
    }
    let mut out = 0;
    let mut pos = 0;
    let n = s.len() as i64;
    let m = needle.len() as i64;
    while true {
        let at = py_find_window(s, needle, pos, n);
        if at < 0 {
            return out;
        }
        out += 1;
        pos = at + m;
    }
}

fn py_lstrip(s: &str) -> String {
    let mut i = 0;
    let n = s.len() as i64;
    while (i < n) && _is_space(&(py_str_at_nonneg(&s, ((i) as usize)))) {
        i += 1;
    }
    return py_slice_str(&s, Some((i) as i64), Some((n) as i64));
}

fn py_lstrip_chars(s: &str, chars: &str) -> String {
    let mut i = 0;
    let n = s.len() as i64;
    while (i < n) && _contains_char(chars, &(py_str_at_nonneg(&s, ((i) as usize)))) {
        i += 1;
    }
    return py_slice_str(&s, Some((i) as i64), Some((n) as i64));
}

fn py_rstrip(s: &str) -> String {
    let n = s.len() as i64;
    let mut i = n - 1;
    while (i >= 0) && _is_space(&(py_str_at(&s, ((i) as i64)))) {
        i -= 1;
    }
    return py_slice_str(&s, Some((0) as i64), Some((i + 1) as i64));
}

fn py_rstrip_chars(s: &str, chars: &str) -> String {
    let n = s.len() as i64;
    let mut i = n - 1;
    while (i >= 0) && _contains_char(chars, &(py_str_at(&s, ((i) as i64)))) {
        i -= 1;
    }
    return py_slice_str(&s, Some((0) as i64), Some((i + 1) as i64));
}

fn py_strip(s: &str) -> String {
    return py_rstrip(&(py_lstrip(s)));
}

fn py_strip_chars(s: &str, chars: &str) -> String {
    return py_rstrip_chars(&(py_lstrip_chars(s, chars)), chars);
}

fn py_startswith(s: &str, prefix: &str) -> bool {
    let n = s.len() as i64;
    let m = prefix.len() as i64;
    if m > n {
        return false;
    }
    let mut i = 0;
    while i < m {
        if py_str_at_nonneg(&s, ((i) as usize)) != py_str_at_nonneg(&prefix, ((i) as usize)) {
            return false;
        }
        i += 1;
    }
    return true;
}

fn py_endswith(s: &str, suffix: &str) -> bool {
    let n = s.len() as i64;
    let m = suffix.len() as i64;
    if m > n {
        return false;
    }
    let mut i = 0;
    let base = n - m;
    while i < m {
        if py_str_at(&s, ((base + i) as i64)) != py_str_at_nonneg(&suffix, ((i) as usize)) {
            return false;
        }
        i += 1;
    }
    return true;
}

fn py_find(s: &str, needle: &str) -> i64 {
    return py_find_window(s, needle, 0, s.len() as i64);
}

fn py_find_window(s: &str, needle: &str, start: i64, end: i64) -> i64 {
    let n = s.len() as i64;
    let m = needle.len() as i64;
    let lo = _normalize_index(start, n);
    let up = _normalize_index(end, n);
    if up < lo {
        return -1;
    }
    if m == 0 {
        return lo;
    }
    let mut i = lo;
    let last = up - m;
    while i <= last {
        let mut j = 0;
        let mut ok = true;
        while j < m {
            if py_str_at(&s, ((i + j) as i64)) != py_str_at_nonneg(&needle, ((j) as usize)) {
                ok = false;
                break;
            }
            j += 1;
        }
        if ok {
            return i;
        }
        i += 1;
    }
    return -1;
}

fn py_rfind(s: &str, needle: &str) -> i64 {
    return py_rfind_window(s, needle, 0, s.len() as i64);
}

fn py_rfind_window(s: &str, needle: &str, start: i64, end: i64) -> i64 {
    let n = s.len() as i64;
    let m = needle.len() as i64;
    let lo = _normalize_index(start, n);
    let up = _normalize_index(end, n);
    if up < lo {
        return -1;
    }
    if m == 0 {
        return up;
    }
    let mut i = up - m;
    while i >= lo {
        let mut j = 0;
        let mut ok = true;
        while j < m {
            if py_str_at(&s, ((i + j) as i64)) != py_str_at_nonneg(&needle, ((j) as usize)) {
                ok = false;
                break;
            }
            j += 1;
        }
        if ok {
            return i;
        }
        i -= 1;
    }
    return -1;
}

fn py_replace(s: &str, oldv: &str, newv: &str) -> String {
    if oldv == "" {
        return s;
    }
    let mut out = ("").to_string();
    let n = s.len() as i64;
    let m = oldv.len() as i64;
    let mut i = 0;
    while i < n {
        if (i + m <= n) && (py_find_window(s, oldv, i, i + m) == i) {
            out += newv;
            i += m;
        } else {
            out += py_str_at(&s, ((i) as i64));
            i += 1;
        }
    }
    return out;
}

fn main() {
    ("Pure-Python source-of-truth for string helper built-ins.").to_string();
}
