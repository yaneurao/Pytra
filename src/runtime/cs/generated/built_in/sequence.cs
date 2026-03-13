// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/sequence.py
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
    public static class sequence_helper
    {
        public static System.Collections.Generic.List<int64> py_range(int64 start, int64 stop, int64 step)
        {
            System.Collections.Generic.List<int64> py_out = new System.Collections.Generic.List<int64>();
            if ((step) == (0)) {
                return py_out;
            }
            if ((step) > (0)) {
                int64 i = start;
                while ((i) < (stop)) {
                    py_out.Add(i);
                    i += step;
                }
            } else {
                int64 i = start;
                while ((i) > (stop)) {
                    py_out.Add(i);
                    i += step;
                }
            }
            return py_out;
        }

        public static str py_repeat(str v, int64 n)
        {
            if ((n) <= (0)) {
                return "";
            }
            str py_out = "";
            int64 i = 0;
            while ((i) < (n)) {
                py_out += v;
                i += 1;
            }
            return py_out;
        }

    }
}
