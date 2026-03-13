// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/scalar_ops.py
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
    public static class scalar_ops_helper
    {
        public static int64 py_to_int64_base(str v, int64 py_base)
        {
            return __b.py_int(v, py_base);
        }

        public static int64 py_ord(str ch)
        {
            return __b.ord(ch);
        }

        public static str py_chr(int64 codepoint)
        {
            return __b.chr(codepoint);
        }

    }
}
