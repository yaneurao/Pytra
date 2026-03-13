// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/zip_ops.py
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
    public static class zip_ops_helper
    {
        public static System.Collections.Generic.List<(A, B)> zip(System.Collections.Generic.List<A> lhs, System.Collections.Generic.List<B> rhs)
        {
            System.Collections.Generic.List<(A, B)> py_out = new System.Collections.Generic.List<(A, B)>();
            long i = 0;
            long n = (lhs).Count;
            if (((rhs).Count) < (n)) {
                n = (rhs).Count;
            }
            while ((i) < (n)) {
                py_out.Add((Pytra.CsModule.py_runtime.py_get(lhs, i), Pytra.CsModule.py_runtime.py_get(rhs, i)));
                i += 1;
            }
            return py_out;
        }

    }
}
