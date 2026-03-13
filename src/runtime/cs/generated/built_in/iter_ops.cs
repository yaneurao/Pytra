// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
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
    public static class iter_ops_helper
    {
        public static object py_reversed_object(object values)
        {
            System.Collections.Generic.List<object> py_out = new System.Collections.Generic.List<object>();
            int64 i = (values).Count() - 1;
            while ((i) >= (0)) {
                py_out.Add(values[System.Convert.ToInt32(i)]);
                i -= 1;
            }
            return py_out;
        }

        public static object py_enumerate_object(object values, int64 start = 0)
        {
            System.Collections.Generic.List<object> py_out = new System.Collections.Generic.List<object>();
            int64 i = 0;
            int64 n = (values).Count();
            while ((i) < (n)) {
                py_out.Add(new System.Collections.Generic.List<object> { start + i, values[System.Convert.ToInt32(i)] });
                i += 1;
            }
            return py_out;
        }

    }
}
