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
        public static bool _is_space(string ch)
        {
            return (((ch) == (" ")) || ((ch) == ("\t")) || ((ch) == ("\n")) || ((ch) == ("\r")));
        }

        public static bool _contains_char(string chars, string ch)
        {
            long i = 0;
            long n = (chars).Length;
            while ((i) < (n)) {
                if ((Pytra.CsModule.py_runtime.py_get(chars, i)) == (ch)) {
                    return true;
                }
                i += 1;
            }
            return false;
        }

        public static long _normalize_index(long idx, long n)
        {
            long py_out = idx;
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

        public static string py_join(string sep, System.Collections.Generic.List<string> parts)
        {
            long n = (parts).Count;
            if ((n) == (0)) {
                return "";
            }
            string py_out = "";
            long i = 0;
            while ((i) < (n)) {
                if ((i) > (0)) {
                    py_out += sep;
                }
                py_out += Pytra.CsModule.py_runtime.py_get(parts, i);
                i += 1;
            }
            return py_out;
        }

        public static System.Collections.Generic.List<string> py_split(string s, string sep, long maxsplit)
        {
            System.Collections.Generic.List<string> py_out = new System.Collections.Generic.List<string>();
            if ((sep) == ("")) {
                py_out.Add(s);
                return py_out;
            }
            long pos = 0;
            long splits = 0;
            long n = (s).Length;
            long m = (sep).Length;
            bool unlimited = (maxsplit) < (0);
            while (true) {
                if ((!unlimited) && ((splits) >= (maxsplit))) {
                    break;
                }
                long at = py_find_window(s, sep, pos, n);
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

        public static System.Collections.Generic.List<string> py_splitlines(string s)
        {
            System.Collections.Generic.List<string> py_out = new System.Collections.Generic.List<string>();
            long n = (s).Length;
            long start = 0;
            long i = 0;
            while ((i) < (n)) {
                string ch = Pytra.CsModule.py_runtime.py_get(s, i);
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
                    string last = Pytra.CsModule.py_runtime.py_get(s, n - 1);
                    if (((last) == ("\n")) || ((last) == ("\r"))) {
                        py_out.Add("");
                    }
                }
            }
            return py_out;
        }

        public static long py_count(string s, string needle)
        {
            if ((needle) == ("")) {
                return (s).Length + 1;
            }
            long py_out = 0;
            long pos = 0;
            long n = (s).Length;
            long m = (needle).Length;
            while (true) {
                long at = py_find_window(s, needle, pos, n);
                if ((at) < (0)) {
                    return py_out;
                }
                py_out += 1;
                pos = at + m;
            }
        return default(long);
        }

        public static string py_lstrip(string s)
        {
            long i = 0;
            long n = (s).Length;
            while (((i) < (n)) && (_is_space(Pytra.CsModule.py_runtime.py_get(s, i)))) {
                i += 1;
            }
            return Pytra.CsModule.py_runtime.py_slice(s, System.Convert.ToInt64(i), System.Convert.ToInt64(n));
        }

        public static string py_lstrip_chars(string s, string chars)
        {
            long i = 0;
            long n = (s).Length;
            while (((i) < (n)) && (_contains_char(chars, Pytra.CsModule.py_runtime.py_get(s, i)))) {
                i += 1;
            }
            return Pytra.CsModule.py_runtime.py_slice(s, System.Convert.ToInt64(i), System.Convert.ToInt64(n));
        }

        public static string py_rstrip(string s)
        {
            long n = (s).Length;
            long i = n - 1;
            while (((i) >= (0)) && (_is_space(Pytra.CsModule.py_runtime.py_get(s, i)))) {
                i -= 1;
            }
            return Pytra.CsModule.py_runtime.py_slice(s, System.Convert.ToInt64(0), System.Convert.ToInt64(i + 1));
        }

        public static string py_rstrip_chars(string s, string chars)
        {
            long n = (s).Length;
            long i = n - 1;
            while (((i) >= (0)) && (_contains_char(chars, Pytra.CsModule.py_runtime.py_get(s, i)))) {
                i -= 1;
            }
            return Pytra.CsModule.py_runtime.py_slice(s, System.Convert.ToInt64(0), System.Convert.ToInt64(i + 1));
        }

        public static string py_strip(string s)
        {
            return py_rstrip(py_lstrip(s));
        }

        public static string py_strip_chars(string s, string chars)
        {
            return py_rstrip_chars(py_lstrip_chars(s, chars), chars);
        }

        public static bool py_startswith(string s, string prefix)
        {
            long n = (s).Length;
            long m = (prefix).Length;
            if ((m) > (n)) {
                return false;
            }
            long i = 0;
            while ((i) < (m)) {
                if ((Pytra.CsModule.py_runtime.py_get(s, i)) != (Pytra.CsModule.py_runtime.py_get(prefix, i))) {
                    return false;
                }
                i += 1;
            }
            return true;
        }

        public static bool py_endswith(string s, string suffix)
        {
            long n = (s).Length;
            long m = (suffix).Length;
            if ((m) > (n)) {
                return false;
            }
            long i = 0;
            long py_base = n - m;
            while ((i) < (m)) {
                if ((Pytra.CsModule.py_runtime.py_get(s, py_base + i)) != (Pytra.CsModule.py_runtime.py_get(suffix, i))) {
                    return false;
                }
                i += 1;
            }
            return true;
        }

        public static long py_find(string s, string needle)
        {
            return py_find_window(s, needle, 0, (s).Length);
        }

        public static long py_find_window(string s, string needle, long start, long end)
        {
            long n = (s).Length;
            long m = (needle).Length;
            long lo = _normalize_index(start, n);
            long up = _normalize_index(end, n);
            if ((up) < (lo)) {
                return -1;
            }
            if ((m) == (0)) {
                return lo;
            }
            long i = lo;
            long last = up - m;
            while ((i) <= (last)) {
                long j = 0;
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

        public static long py_rfind(string s, string needle)
        {
            return py_rfind_window(s, needle, 0, (s).Length);
        }

        public static long py_rfind_window(string s, string needle, long start, long end)
        {
            long n = (s).Length;
            long m = (needle).Length;
            long lo = _normalize_index(start, n);
            long up = _normalize_index(end, n);
            if ((up) < (lo)) {
                return -1;
            }
            if ((m) == (0)) {
                return up;
            }
            long i = up - m;
            while ((i) >= (lo)) {
                long j = 0;
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

        public static string py_replace(string s, string oldv, string newv)
        {
            if ((oldv) == ("")) {
                return s;
            }
            string py_out = "";
            long n = (s).Length;
            long m = (oldv).Length;
            long i = 0;
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
