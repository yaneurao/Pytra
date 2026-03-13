// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/string_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class string_ops {
    private string_ops() {
    }


    public static boolean _is_space(String ch) {
        return ((java.util.Objects.equals(ch, " ")) || (java.util.Objects.equals(ch, "\t")) || (java.util.Objects.equals(ch, "\n")) || (java.util.Objects.equals(ch, "\r")));
    }

    public static boolean _contains_char(String chars, String ch) {
        long i = 0L;
        long n = ((long)(chars.length()));
        while (((i) < (n))) {
            if ((java.util.Objects.equals(String.valueOf(String.valueOf(chars.charAt((int)((((i) < 0L) ? (((long)(chars.length())) + (i)) : (i)))))), ch))) {
                return true;
            }
            i += 1L;
        }
        return false;
    }

    public static long _normalize_index(long idx, long n) {
        long out = idx;
        if (((out) < (0L))) {
            out += n;
        }
        if (((out) < (0L))) {
            out = 0L;
        }
        if (((out) > (n))) {
            out = n;
        }
        return out;
    }

    public static String py_join(String sep, java.util.ArrayList<String> parts) {
        long n = ((long)(parts.size()));
        if (((n) == (0L))) {
            return "";
        }
        String out = "";
        long i = 0L;
        while (((i) < (n))) {
            if (((i) > (0L))) {
                out += sep;
            }
            out += String.valueOf(parts.get((int)((((i) < 0L) ? (((long)(parts.size())) + (i)) : (i)))));
            i += 1L;
        }
        return out;
    }

    public static java.util.ArrayList<String> py_split(String s, String sep, long maxsplit) {
        java.util.ArrayList<String> out = new java.util.ArrayList<String>();
        if ((java.util.Objects.equals(sep, ""))) {
            out.add(s);
            return out;
        }
        long pos = 0L;
        long splits = 0L;
        long n = ((long)(s.length()));
        long m = ((long)(sep.length()));
        boolean unlimited = ((maxsplit) < (0L));
        while (true) {
            if (((!unlimited) && ((splits) >= (maxsplit)))) {
                break;
            }
            long at = py_find_window(s, sep, pos, n);
            if (((at) < (0L))) {
                break;
            }
            out.add(PyRuntime.__pytra_str_slice(s, (((pos) < 0L) ? (((long)(s.length())) + (pos)) : (pos)), (((at) < 0L) ? (((long)(s.length())) + (at)) : (at))));
            pos = at + m;
            splits += 1L;
        }
        out.add(PyRuntime.__pytra_str_slice(s, (((pos) < 0L) ? (((long)(s.length())) + (pos)) : (pos)), (((n) < 0L) ? (((long)(s.length())) + (n)) : (n))));
        return out;
    }

    public static java.util.ArrayList<String> py_splitlines(String s) {
        java.util.ArrayList<String> out = new java.util.ArrayList<String>();
        long n = ((long)(s.length()));
        long start = 0L;
        long i = 0L;
        while (((i) < (n))) {
            String ch = String.valueOf(String.valueOf(s.charAt((int)((((i) < 0L) ? (((long)(s.length())) + (i)) : (i))))));
            if (((java.util.Objects.equals(ch, "\n")) || (java.util.Objects.equals(ch, "\r")))) {
                out.add(PyRuntime.__pytra_str_slice(s, (((start) < 0L) ? (((long)(s.length())) + (start)) : (start)), (((i) < 0L) ? (((long)(s.length())) + (i)) : (i))));
                if (((java.util.Objects.equals(ch, "\r")) && ((i + 1L) < (n)) && (java.util.Objects.equals(String.valueOf(String.valueOf(s.charAt((int)((((i + 1L) < 0L) ? (((long)(s.length())) + (i + 1L)) : (i + 1L)))))), "\n")))) {
                    i += 1L;
                }
                i += 1L;
                start = i;
                continue;
            }
            i += 1L;
        }
        if (((start) < (n))) {
            out.add(PyRuntime.__pytra_str_slice(s, (((start) < 0L) ? (((long)(s.length())) + (start)) : (start)), (((n) < 0L) ? (((long)(s.length())) + (n)) : (n))));
        } else {
            if (((n) > (0L))) {
                String last = String.valueOf(String.valueOf(s.charAt((int)((((n - 1L) < 0L) ? (((long)(s.length())) + (n - 1L)) : (n - 1L))))));
                if (((java.util.Objects.equals(last, "\n")) || (java.util.Objects.equals(last, "\r")))) {
                    out.add("");
                }
            }
        }
        return out;
    }

    public static long py_count(String s, String needle) {
        if ((java.util.Objects.equals(needle, ""))) {
            return ((long)(s.length())) + 1L;
        }
        long out = 0L;
        long pos = 0L;
        long n = ((long)(s.length()));
        long m = ((long)(needle.length()));
        while (true) {
            long at = py_find_window(s, needle, pos, n);
            if (((at) < (0L))) {
                return out;
            }
            out += 1L;
            pos = at + m;
        }
        return 0L;
    }

    public static String py_lstrip(String s) {
        long i = 0L;
        long n = ((long)(s.length()));
        while ((((i) < (n)) && _is_space(String.valueOf(String.valueOf(s.charAt((int)((((i) < 0L) ? (((long)(s.length())) + (i)) : (i))))))))) {
            i += 1L;
        }
        return PyRuntime.__pytra_str_slice(s, (((i) < 0L) ? (((long)(s.length())) + (i)) : (i)), (((n) < 0L) ? (((long)(s.length())) + (n)) : (n)));
    }

    public static String py_lstrip_chars(String s, String chars) {
        long i = 0L;
        long n = ((long)(s.length()));
        while ((((i) < (n)) && _contains_char(chars, String.valueOf(String.valueOf(s.charAt((int)((((i) < 0L) ? (((long)(s.length())) + (i)) : (i))))))))) {
            i += 1L;
        }
        return PyRuntime.__pytra_str_slice(s, (((i) < 0L) ? (((long)(s.length())) + (i)) : (i)), (((n) < 0L) ? (((long)(s.length())) + (n)) : (n)));
    }

    public static String py_rstrip(String s) {
        long n = ((long)(s.length()));
        long i = n - 1L;
        while ((((i) >= (0L)) && _is_space(String.valueOf(String.valueOf(s.charAt((int)((((i) < 0L) ? (((long)(s.length())) + (i)) : (i))))))))) {
            i -= 1L;
        }
        return PyRuntime.__pytra_str_slice(s, (((0L) < 0L) ? (((long)(s.length())) + (0L)) : (0L)), (((i + 1L) < 0L) ? (((long)(s.length())) + (i + 1L)) : (i + 1L)));
    }

    public static String py_rstrip_chars(String s, String chars) {
        long n = ((long)(s.length()));
        long i = n - 1L;
        while ((((i) >= (0L)) && _contains_char(chars, String.valueOf(String.valueOf(s.charAt((int)((((i) < 0L) ? (((long)(s.length())) + (i)) : (i))))))))) {
            i -= 1L;
        }
        return PyRuntime.__pytra_str_slice(s, (((0L) < 0L) ? (((long)(s.length())) + (0L)) : (0L)), (((i + 1L) < 0L) ? (((long)(s.length())) + (i + 1L)) : (i + 1L)));
    }

    public static String py_strip(String s) {
        return py_rstrip(py_lstrip(s));
    }

    public static String py_strip_chars(String s, String chars) {
        return py_rstrip_chars(py_lstrip_chars(s, chars), chars);
    }

    public static boolean py_startswith(String s, String prefix) {
        long n = ((long)(s.length()));
        long m = ((long)(prefix.length()));
        if (((m) > (n))) {
            return false;
        }
        long i = 0L;
        while (((i) < (m))) {
            if ((!(java.util.Objects.equals(String.valueOf(String.valueOf(s.charAt((int)((((i) < 0L) ? (((long)(s.length())) + (i)) : (i)))))), String.valueOf(String.valueOf(prefix.charAt((int)((((i) < 0L) ? (((long)(prefix.length())) + (i)) : (i)))))))))) {
                return false;
            }
            i += 1L;
        }
        return true;
    }

    public static boolean py_endswith(String s, String suffix) {
        long n = ((long)(s.length()));
        long m = ((long)(suffix.length()));
        if (((m) > (n))) {
            return false;
        }
        long i = 0L;
        long base = n - m;
        while (((i) < (m))) {
            if ((!(java.util.Objects.equals(String.valueOf(String.valueOf(s.charAt((int)((((base + i) < 0L) ? (((long)(s.length())) + (base + i)) : (base + i)))))), String.valueOf(String.valueOf(suffix.charAt((int)((((i) < 0L) ? (((long)(suffix.length())) + (i)) : (i)))))))))) {
                return false;
            }
            i += 1L;
        }
        return true;
    }

    public static long py_find(String s, String needle) {
        return py_find_window(s, needle, 0L, ((long)(s.length())));
    }

    public static long py_find_window(String s, String needle, long start, long end) {
        long n = ((long)(s.length()));
        long m = ((long)(needle.length()));
        long lo = _normalize_index(start, n);
        long up = _normalize_index(end, n);
        if (((up) < (lo))) {
            return (-(1L));
        }
        if (((m) == (0L))) {
            return lo;
        }
        long i = lo;
        long last = up - m;
        while (((i) <= (last))) {
            long j = 0L;
            boolean ok = true;
            while (((j) < (m))) {
                if ((!(java.util.Objects.equals(String.valueOf(String.valueOf(s.charAt((int)((((i + j) < 0L) ? (((long)(s.length())) + (i + j)) : (i + j)))))), String.valueOf(String.valueOf(needle.charAt((int)((((j) < 0L) ? (((long)(needle.length())) + (j)) : (j)))))))))) {
                    ok = false;
                    break;
                }
                j += 1L;
            }
            if (ok) {
                return i;
            }
            i += 1L;
        }
        return (-(1L));
    }

    public static long py_rfind(String s, String needle) {
        return py_rfind_window(s, needle, 0L, ((long)(s.length())));
    }

    public static long py_rfind_window(String s, String needle, long start, long end) {
        long n = ((long)(s.length()));
        long m = ((long)(needle.length()));
        long lo = _normalize_index(start, n);
        long up = _normalize_index(end, n);
        if (((up) < (lo))) {
            return (-(1L));
        }
        if (((m) == (0L))) {
            return up;
        }
        long i = up - m;
        while (((i) >= (lo))) {
            long j = 0L;
            boolean ok = true;
            while (((j) < (m))) {
                if ((!(java.util.Objects.equals(String.valueOf(String.valueOf(s.charAt((int)((((i + j) < 0L) ? (((long)(s.length())) + (i + j)) : (i + j)))))), String.valueOf(String.valueOf(needle.charAt((int)((((j) < 0L) ? (((long)(needle.length())) + (j)) : (j)))))))))) {
                    ok = false;
                    break;
                }
                j += 1L;
            }
            if (ok) {
                return i;
            }
            i -= 1L;
        }
        return (-(1L));
    }

    public static String py_replace(String s, String oldv, String newv) {
        if ((java.util.Objects.equals(oldv, ""))) {
            return s;
        }
        String out = "";
        long n = ((long)(s.length()));
        long m = ((long)(oldv.length()));
        long i = 0L;
        while (((i) < (n))) {
            if ((((i + m) <= (n)) && ((py_find_window(s, oldv, i, i + m)) == (i)))) {
                out += newv;
                i += m;
            } else {
                out += String.valueOf(String.valueOf(s.charAt((int)((((i) < 0L) ? (((long)(s.length())) + (i)) : (i))))));
                i += 1L;
            }
        }
        return out;
    }

    public static void main(String[] args) {
    }
}
