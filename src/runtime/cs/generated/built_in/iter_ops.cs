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
        public static System.Collections.Generic.List<object> py_reversed_object(object values)
        {
            System.Collections.Generic.List<object> py_out = new System.Collections.Generic.List<object>();
            foreach (var value in ((System.Collections.IEnumerable)(values))) {
                py_out.Add(value);
            }
            return reversed(py_out);
        }

        public static System.Collections.Generic.List<object> py_enumerate_object(object values, long start = 0)
        {
            System.Collections.Generic.List<object> py_out = new System.Collections.Generic.List<object>();
            long i = start;
            foreach (var value in ((System.Collections.IEnumerable)(values))) {
                py_out.Add(new System.Collections.Generic.List<object> { i, value });
                i += 1;
            }
            return py_out;
        }

    }
}
