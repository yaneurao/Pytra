// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/contains.py
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
    public static class contains_helper
    {
        public static bool py_contains_dict_object(object values, object key)
        {
            str needle = System.Convert.ToString(key);
            foreach (var cur in ((System.Collections.IEnumerable)(values))) {
                if ((cur) == (needle)) {
                    return true;
                }
            }
            return false;
        }

        public static bool py_contains_list_object(object values, object key)
        {
            foreach (var cur in ((System.Collections.IEnumerable)(values))) {
                if ((cur) == (key)) {
                    return true;
                }
            }
            return false;
        }

        public static bool py_contains_set_object(object values, object key)
        {
            foreach (var cur in ((System.Collections.IEnumerable)(values))) {
                if ((cur) == (key)) {
                    return true;
                }
            }
            return false;
        }

        public static bool py_contains_str_object(object values, object key)
        {
            str needle = System.Convert.ToString(key);
            str haystack = System.Convert.ToString(values);
            int64 n = (haystack).Length;
            int64 m = (needle).Length;
            if ((m) == (0)) {
                return true;
            }
            int64 i = 0;
            int64 last = n - m;
            while ((i) <= (last)) {
                int64 j = 0;
                bool ok = true;
                while ((j) < (m)) {
                    if ((Pytra.CsModule.py_runtime.py_get(haystack, i + j)) != (Pytra.CsModule.py_runtime.py_get(needle, j))) {
                        ok = false;
                        break;
                    }
                    j += 1;
                }
                if (ok) {
                    return true;
                }
                i += 1;
            }
            return false;
        }

    }
}
