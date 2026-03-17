// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
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
    public static class sys
    {
        public static System.Collections.Generic.List<str> argv { get { return sys_native.argv; } }
        public static System.Collections.Generic.List<str> path { get { return sys_native.path; } }

        public static void exit(int64 code = 0)
        {
            sys_native.exit(code);
        }

        public static void set_argv(System.Collections.Generic.List<str> values)
        {
            sys_native.set_argv(values);
        }

        public static void set_path(System.Collections.Generic.List<str> values)
        {
            sys_native.set_path(values);
        }

        public static void write_stderr(str text)
        {
            sys_native.write_stderr(text);
        }

        public static void write_stdout(str text)
        {
            sys_native.write_stdout(text);
        }

    }
}
