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
            foreach (var value in ((System.Collections.IEnumerable)(values))) {
                if (Pytra.CsModule.py_runtime.py_bool(value)) {
                    return true;
                }
            }
            return false;
        }

        public static bool py_all(object values)
        {
            foreach (var value in ((System.Collections.IEnumerable)(values))) {
                if (!(Pytra.CsModule.py_runtime.py_bool(value))) {
                    return false;
                }
            }
            return true;
        }

    }
}
