// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/predicates.py
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
    public static class predicates_helper
    {
        public static bool py_any(object values)
        {
            long i = 0;
            long n = (values).Count();
            while ((i) < (n)) {
                if (Pytra.CsModule.py_runtime.py_bool(values[System.Convert.ToInt32(i)])) {
                    return true;
                }
                i += 1;
            }
            return false;
        }

        public static bool py_all(object values)
        {
            long i = 0;
            long n = (values).Count();
            while ((i) < (n)) {
                if (!(Pytra.CsModule.py_runtime.py_bool(values[System.Convert.ToInt32(i)]))) {
                    return false;
                }
                i += 1;
            }
            return true;
        }

    }
}
