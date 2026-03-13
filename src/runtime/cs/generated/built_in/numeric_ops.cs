// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/numeric_ops.py
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
    public static class numeric_ops_helper
    {
        public static T sum(System.Collections.Generic.List<T> values)
        {
            if (((values).Count) == (0)) {
                return 0;
            }
            var acc = Pytra.CsModule.py_runtime.py_get(values, 0) - Pytra.CsModule.py_runtime.py_get(values, 0);
            int64 i = 0;
            int64 n = (values).Count;
            while ((i) < (n)) {
                acc += Pytra.CsModule.py_runtime.py_get(values, i);
                i += 1;
            }
            return acc;
        }

        public static T py_min(T a, T b)
        {
            if ((a) < (b)) {
                return a;
            }
            return b;
        }

        public static T py_max(T a, T b)
        {
            if ((a) > (b)) {
                return a;
            }
            return b;
        }

    }
}
