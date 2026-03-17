using System;
using System.Collections.Generic;

namespace Pytra.CsModule
{
    // Generated std/sys.cs delegates host bindings through this native seam.
    public static class sys_native
    {
        private static readonly List<string> _argv = new List<string>();
        private static readonly List<string> _path = new List<string>();

        public static List<string> argv { get { return _argv; } }
        public static List<string> path { get { return _path; } }

        public static void exit(long code)
        {
            System.Environment.Exit((int)code);
        }

        public static void set_argv(List<string> values)
        {
            _argv.Clear();
            _argv.AddRange(values);
        }

        public static void set_path(List<string> values)
        {
            _path.Clear();
            _path.AddRange(values);
        }

        public static void write_stderr(string text)
        {
            Console.Error.Write(text);
        }

        public static void write_stdout(string text)
        {
            Console.Write(text);
        }
    }
}
