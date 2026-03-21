#include "core/py_runtime.h"
#include "core/process_runtime.h"

/* Pure-Python source-of-truth for string helper built-ins. */

bool _is_space(const str& ch) {
    return (ch == " ") || (ch == "\t") || (ch == "\n") || (ch == "\r");
}

bool _contains_char(const str& chars, const str& ch) {
    int64 i = 0;
    int64 n = chars.size();
    while (i < n) {
        if (chars[i] == ch)
            return true;
        i++;
    }
    return false;
}

int64 _normalize_index(int64 idx, int64 n) {
    int64 out = idx;
    if (out < 0)
        out += n;
    if (out < 0)
        out = 0;
    if (out > n)
        out = n;
    return out;
}

str py_join(const str& sep, const list<str>& parts) {
    int64 n = parts.size();
    if (n == 0)
        return "";
    str out = "";
    int64 i = 0;
    while (i < n) {
        if (i > 0)
            out += sep;
        out += parts[i];
        i++;
    }
    return out;
}

list<str> py_split(const str& s, const str& sep, int64 maxsplit) {
    rc<list<str>> out = rc_list_from_value(list<str>{});
    if (sep == "") {
        rc_list_ref(out).append(s);
        return rc_list_copy_value(out);
    }
    int64 pos = 0;
    int64 splits = 0;
    int64 n = s.size();
    int64 m = sep.size();
    bool unlimited = maxsplit < 0;
    while (true) {
        if ((!(unlimited)) && (splits >= maxsplit))
            break;
        int64 at = py_find_window(s, sep, pos, n);
        if (at < 0)
            break;
        rc_list_ref(out).append(py_str_slice(s, pos, at));
        pos = at + m;
        splits++;
    }
    rc_list_ref(out).append(py_str_slice(s, pos, n));
    return rc_list_copy_value(out);
}

list<str> py_splitlines(const str& s) {
    rc<list<str>> out = rc_list_from_value(list<str>{});
    int64 n = s.size();
    int64 start = 0;
    int64 i = 0;
    while (i < n) {
        str ch = s[i];
        if ((ch == "\n") || (ch == "\r")) {
            rc_list_ref(out).append(py_str_slice(s, start, i));
            if ((ch == "\r") && (i + 1 < n) && (s[i + 1] == "\n"))
                i++;
            i++;
            start = i;
            continue;
        }
        i++;
    }
    if (start < n) {
        rc_list_ref(out).append(py_str_slice(s, start, n));
    } else if (n > 0) {
        auto __idx_1 = n - 1;
        str last = s[__idx_1];
        if ((last == "\n") || (last == "\r"))
            rc_list_ref(out).append("");
    }
    return rc_list_copy_value(out);
}

int64 py_count(const str& s, const str& needle) {
    if (needle == "")
        return s.size() + 1;
    int64 out = 0;
    int64 pos = 0;
    int64 n = s.size();
    int64 m = needle.size();
    while (true) {
        int64 at = py_find_window(s, needle, pos, n);
        if (at < 0)
            return out;
        out++;
        pos = at + m;
    }
}

str py_lstrip(const str& s) {
    int64 i = 0;
    int64 n = s.size();
    while ((i < n) && (_is_space(s[i]))) {
        i++;
    }
    return py_str_slice(s, i, n);
}

str py_lstrip_chars(const str& s, const str& chars) {
    int64 i = 0;
    int64 n = s.size();
    while ((i < n) && (_contains_char(chars, s[i]))) {
        i++;
    }
    return py_str_slice(s, i, n);
}

str py_rstrip(const str& s) {
    int64 n = s.size();
    int64 i = n - 1;
    while ((i >= 0) && (_is_space(s[i]))) {
        i--;
    }
    return py_str_slice(s, 0, i + 1);
}

str py_rstrip_chars(const str& s, const str& chars) {
    int64 n = s.size();
    int64 i = n - 1;
    while ((i >= 0) && (_contains_char(chars, s[i]))) {
        i--;
    }
    return py_str_slice(s, 0, i + 1);
}

str py_strip(const str& s) {
    return py_rstrip(py_lstrip(s));
}

str py_strip_chars(const str& s, const str& chars) {
    return py_rstrip_chars(py_lstrip_chars(s, chars), chars);
}

bool py_startswith(const str& s, const str& prefix) {
    int64 n = s.size();
    int64 m = prefix.size();
    if (m > n)
        return false;
    int64 i = 0;
    while (i < m) {
        if (s[i] != prefix[i])
            return false;
        i++;
    }
    return true;
}

bool py_endswith(const str& s, const str& suffix) {
    int64 n = s.size();
    int64 m = suffix.size();
    if (m > n)
        return false;
    int64 i = 0;
    int64 base = n - m;
    while (i < m) {
        if (s[base + i] != suffix[i])
            return false;
        i++;
    }
    return true;
}

int64 py_find(const str& s, const str& needle) {
    return py_find_window(s, needle, 0, s.size());
}

int64 py_find_window(const str& s, const str& needle, int64 start, int64 end) {
    int64 n = s.size();
    int64 m = needle.size();
    int64 lo = _normalize_index(start, n);
    int64 up = _normalize_index(end, n);
    if (up < lo)
        return -(1);
    if (m == 0)
        return lo;
    int64 i = lo;
    int64 last = up - m;
    while (i <= last) {
        int64 j = 0;
        bool ok = true;
        while (j < m) {
            if (s[i + j] != needle[j]) {
                ok = false;
                break;
            }
            j++;
        }
        if (ok)
            return i;
        i++;
    }
    return -(1);
}

int64 py_rfind(const str& s, const str& needle) {
    return py_rfind_window(s, needle, 0, s.size());
}

int64 py_rfind_window(const str& s, const str& needle, int64 start, int64 end) {
    int64 n = s.size();
    int64 m = needle.size();
    int64 lo = _normalize_index(start, n);
    int64 up = _normalize_index(end, n);
    if (up < lo)
        return -(1);
    if (m == 0)
        return up;
    int64 i = up - m;
    while (i >= lo) {
        int64 j = 0;
        bool ok = true;
        while (j < m) {
            if (s[i + j] != needle[j]) {
                ok = false;
                break;
            }
            j++;
        }
        if (ok)
            return i;
        i--;
    }
    return -(1);
}

str py_replace(const str& s, const str& oldv, const str& newv) {
    if (oldv == "")
        return s;
    str out = "";
    int64 n = s.size();
    int64 m = oldv.size();
    int64 i = 0;
    while (i < n) {
        if ((i + m <= n) && (py_find_window(s, oldv, i, i + m) == i)) {
            out += newv;
            i += m;
        } else {
            out += s[i];
            i++;
        }
    }
    return out;
}
