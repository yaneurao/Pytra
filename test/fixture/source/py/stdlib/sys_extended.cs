using System;
using System.Collections.Generic;
using System.Linq;
using Any = System.Object;
using int64 = System.Int64;
using float64 = System.Double;
using str = System.String;
using Pytra.CsModule;
using sys = Pytra.CsModule.sys;

public static class Program
{
    public static bool run_sys_extended()
    {
        System.Collections.Generic.List<bool> checks = new System.Collections.Generic.List<bool>();
        var old_argv = args;
        var old_path = sys.path;
        sys.set_argv(new System.Collections.Generic.List<string> { "a", "b" });
        sys.set_path(new System.Collections.Generic.List<string> { "x" });
        checks.Add(System.Object.Equals(Pytra.CsModule.py_runtime.py_runtime_value_isinstance(args, Pytra.CsModule.py_runtime.PYTRA_TID_LIST), true));
        checks.Add(System.Object.Equals(Pytra.CsModule.py_runtime.py_runtime_value_isinstance(sys.path, Pytra.CsModule.py_runtime.PYTRA_TID_LIST), true));
        checks.Add(System.Object.Equals(args[System.Convert.ToInt32(0)], "a"));
        checks.Add(System.Object.Equals(sys.path[System.Convert.ToInt32(0)], "x"));
        sys.set_argv(old_argv);
        sys.set_path(old_path);
        return System.Linq.Enumerable.All(checks, __x => System.Convert.ToBoolean(__x));
    }
    
    public static void Main(string[] args)
    {
            System.Console.WriteLine(run_sys_extended());
    }
}
