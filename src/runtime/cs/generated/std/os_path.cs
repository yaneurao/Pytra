// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os_path.py
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
    public static class os_path
    {
        public static str join(str a, str b)
        {
            return os_path_native.join(a, b);
        }

        public static str dirname(str p)
        {
            return os_path_native.dirname(p);
        }

        public static str basename(str p)
        {
            return os_path_native.basename(p);
        }

        public static (str, str) splitext(str p)
        {
            return os_path_native.splitext(p);
        }

        public static str abspath(str p)
        {
            return os_path_native.abspath(p);
        }

        public static bool exists(str p)
        {
            return os_path_native.exists(p);
        }

    }
}
