// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os.py
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
    public static class os
    {
        public static str getcwd()
        {
            return os_native.getcwd();
        }

        public static void mkdir(str p)
        {
            os_native.mkdir(p);
        }

        public static void makedirs(str p, bool exist_ok = false)
        {
            os_native.makedirs(p, exist_ok);
        }

    }
}
