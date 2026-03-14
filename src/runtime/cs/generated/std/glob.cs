// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/glob.py
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
    public static class glob
    {
        public static System.Collections.Generic.List<str> glob(str pattern)
        {
            return glob_native.glob(pattern);
        }

    }
}
