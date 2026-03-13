// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/string_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

using System;
using System.Collections.Generic;
using System.Linq;
using Any = System.Object;
using int64 = System.Int64;
using float64 = System.Double;
using str = System.String;

namespace Pytra.CsModule
{
    public static class string_ops_helper
    {
        public static bool _is_space(str ch)
        {
            return (((ch) == (" ")) || ((ch) == ("\t")) || ((ch) == ("\n")) || ((ch) == ("\r")));
        }

        public static bool _contains_char(str chars, str ch)
        {
            int64 i = 0;
            int64 n = (chars).Length;
            while ((i) < (n)) {
                if ((Pytra.CsModule.py_runtime.py_get(chars, i)) == (ch)) {
                    return true;
                }
                i += 1;
            }
            return false;
        }

        public static int64 _normalize_index(int64 idx, int64 n)
        {
            int64 py_out = idx;
            if ((py_out) < (0)) {
                py_out += n;
            }
            if ((py_out) < (0)) {
                py_out = 0;
            }
            if ((py_out) > (n)) {
                py_out = n;
            }
            return py_out;
        }

        public static str py_join(str sep, System.Collections.Generic.List<str> parts)
        {
            int64 n = (parts).Count;
            if ((n) == (0)) {
                return "";
            }
            str py_out = "";
            int64 i = 0;
            while ((i) < (n)) {
                if ((i) > (0)) {
                    py_out += sep;
                }
                py_out += Pytra.CsModule.py_runtime.py_get(parts, i);
                i += 1;
            }
            return py_out;
        }

        public static System.Collections.Generic.List<str> py_split(str s, str sep, int64 maxsplit)
        {
            System.Collections.Generic.List<str> py_out = new System.Collections.Generic.List<str>();
            if ((sep) == ("")) {
                py_out.Add(s);
                return py_out;
            }
            int64 pos = 0;
            int64 splits = 0;
            int64 n = (s).Length;
            int64 m = (sep).Length;
            bool unlimited = (maxsplit) < (0);
            while (true) {
                if ((!unlimited) && ((splits) >= (maxsplit))) {
                    break;
                }
                int64 at = py_find_window(s, sep, pos, n);
                if ((at) < (0)) {
                    break;
                }
                py_out.Add(Pytra.CsModule.py_runtime.py_slice(s, System.Convert.ToInt64(pos), System.Convert.ToInt64(at)));
                pos = at + m;
                splits += 1;
            }
            py_out.Add(Pytra.CsModule.py_runtime.py_slice(s, System.Convert.ToInt64(pos), System.Convert.ToInt64(n)));
            return py_out;
        }

        public static System.Collections.Generic.List<str> py_splitlines(str s)
        {
            System.Collections.Generic.List<str> py_out = new System.Collections.Generic.List<str>();
            int64 n = (s).Length;
            int64 start = 0;
            int64 i = 0;
            while ((i) < (n)) {
                str ch = Pytra.CsModule.py_runtime.py_get(s, i);
                if (((ch) == ("\n")) || ((ch) == ("\r"))) {
                    py_out.Add(Pytra.CsModule.py_runtime.py_slice(s, System.Convert.ToInt64(start), System.Convert.ToInt64(i)));
                    if (((ch) == ("\r")) && ((i + 1) < (n)) && ((Pytra.CsModule.py_runtime.py_get(s, i + 1)) == ("\n"))) {
                        i += 1;
                    }
                    i += 1;
                    start = i;
                    continue;
                }
                i += 1;
            }
            if ((start) < (n)) {
                py_out.Add(Pytra.CsModule.py_runtime.py_slice(s, System.Convert.ToInt64(start), System.Convert.ToInt64(n)));
            } else {
                if ((n) > (0)) {
                    str last = Pytra.CsModule.py_runtime.py_get(s, n - 1);
                    if (((last) == ("\n")) || ((last) == ("\r"))) {
                        py_out.Add("");
                    }
                }
            }
            return py_out;
        }

        public static int64 py_count(str s, str needle)
        {
            if ((needle) == ("")) {
                return (s).Length + 1;
            }
            int64 py_out = 0;
            int64 pos = 0;
            int64 n = (s).Length;
            int64 m = (needle).Length;
            while (true) {
                int64 at = py_find_window(s, needle, pos, n);
                if ((at) < (0)) {
                    return py_out;
                }
                py_out += 1;
                pos = at + m;
            }
        return default(int64);
        }

        public static str py_lstrip(str s)
        {
            int64 i = 0;
            int64 n = (s).Length;
            while (((i) < (n)) && (_is_space(Pytra.CsModule.py_runtime.py_get(s, i)))) {
                i += 1;
            }
            return Pytra.CsModule.py_runtime.py_slice(s, System.Convert.ToInt64(i), System.Convert.ToInt64(n));
        }

        public static str py_lstrip_chars(str s, str chars)
        {
            int64 i = 0;
            int64 n = (s).Length;
            while (((i) < (n)) && (_contains_char(chars, Pytra.CsModule.py_runtime.py_get(s, i)))) {
                i += 1;
            }
            return Pytra.CsModule.py_runtime.py_slice(s, System.Convert.ToInt64(i), System.Convert.ToInt64(n));
        }

        public static str py_rstrip(str s)
        {
            int64 n = (s).Length;
            int64 i = n - 1;
            while (((i) >= (0)) && (_is_space(Pytra.CsModule.py_runtime.py_get(s, i)))) {
                i -= 1;
            }
            return Pytra.CsModule.py_runtime.py_slice(s, System.Convert.ToInt64(0), System.Convert.ToInt64(i + 1));
        }

        public static str py_rstrip_chars(str s, str chars)
        {
            int64 n = (s).Length;
            int64 i = n - 1;
            while (((i) >= (0)) && (_contains_char(chars, Pytra.CsModule.py_runtime.py_get(s, i)))) {
                i -= 1;
            }
            return Pytra.CsModule.py_runtime.py_slice(s, System.Convert.ToInt64(0), System.Convert.ToInt64(i + 1));
        }

        public static str py_strip(str s)
        {
            return py_rstrip(py_lstrip(s));
        }

        public static str py_strip_chars(str s, str chars)
        {
            return py_rstrip_chars(py_lstrip_chars(s, chars), chars);
        }

        public static bool py_startswith(str s, str prefix)
        {
            int64 n = (s).Length;
            int64 m = (prefix).Length;
            if ((m) > (n)) {
                return false;
            }
            int64 i = 0;
            while ((i) < (m)) {
                if ((Pytra.CsModule.py_runtime.py_get(s, i)) != (Pytra.CsModule.py_runtime.py_get(prefix, i))) {
                    return false;
                }
                i += 1;
            }
            return true;
        }

        public static bool py_endswith(str s, str suffix)
        {
            int64 n = (s).Length;
            int64 m = (suffix).Length;
            if ((m) > (n)) {
                return false;
            }
            int64 i = 0;
            int64 py_base = n - m;
            while ((i) < (m)) {
                if ((Pytra.CsModule.py_runtime.py_get(s, py_base + i)) != (Pytra.CsModule.py_runtime.py_get(suffix, i))) {
                    return false;
                }
                i += 1;
            }
            return true;
        }

        public static int64 py_find(str s, str needle)
        {
            return py_find_window(s, needle, 0, (s).Length);
        }

        public static int64 py_find_window(str s, str needle, int64 start, int64 end)
        {
            int64 n = (s).Length;
            int64 m = (needle).Length;
            int64 lo = _normalize_index(start, n);
            int64 up = _normalize_index(end, n);
            if ((up) < (lo)) {
                return -1;
            }
            if ((m) == (0)) {
                return lo;
            }
            int64 i = lo;
            int64 last = up - m;
            while ((i) <= (last)) {
                int64 j = 0;
                bool ok = true;
                while ((j) < (m)) {
                    if ((Pytra.CsModule.py_runtime.py_get(s, i + j)) != (Pytra.CsModule.py_runtime.py_get(needle, j))) {
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

        public static int64 py_rfind(str s, str needle)
        {
            return py_rfind_window(s, needle, 0, (s).Length);
        }

        public static int64 py_rfind_window(str s, str needle, int64 start, int64 end)
        {
            int64 n = (s).Length;
            int64 m = (needle).Length;
            int64 lo = _normalize_index(start, n);
            int64 up = _normalize_index(end, n);
            if ((up) < (lo)) {
                return -1;
            }
            if ((m) == (0)) {
                return up;
            }
            int64 i = up - m;
            while ((i) >= (lo)) {
                int64 j = 0;
                bool ok = true;
                while ((j) < (m)) {
                    if ((Pytra.CsModule.py_runtime.py_get(s, i + j)) != (Pytra.CsModule.py_runtime.py_get(needle, j))) {
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

        public static str py_replace(str s, str oldv, str newv)
        {
            if ((oldv) == ("")) {
                return s;
            }
            str py_out = "";
            int64 n = (s).Length;
            int64 m = (oldv).Length;
            int64 i = 0;
            while ((i) < (n)) {
                if (((i + m) <= (n)) && ((py_find_window(s, oldv, i, i + m)) == (i))) {
                    py_out += newv;
                    i += m;
                } else {
                    py_out += Pytra.CsModule.py_runtime.py_get(s, i);
                    i += 1;
                }
            }
            return py_out;
        }

    }
}
