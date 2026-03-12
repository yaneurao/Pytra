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
        public static System.Collections.Generic.List<long> py_range(long start, long stop, long step)
        {
            System.Collections.Generic.List<long> py_out = new System.Collections.Generic.List<long>();
            if ((step) == (0)) {
                return py_out;
            }
            if ((step) > (0)) {
                long i = start;
                while ((i) < (stop)) {
                    py_out.Add(i);
                    i += step;
                }
            } else {
                long i = start;
                while ((i) > (stop)) {
                    py_out.Add(i);
                    i += step;
                }
            }
            return py_out;
        }

        public static string py_repeat(string v, long n)
        {
            if ((n) <= (0)) {
                return "";
            }
            string py_out = "";
            long i = 0;
            while ((i) < (n)) {
                py_out += v;
                i += 1;
            }
            return py_out;
        }

    }
}
