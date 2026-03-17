using System;
using System.Collections.Generic;
using System.Linq;
using Any = System.Object;
using int64 = System.Int64;
using float64 = System.Double;
using str = System.String;
using Pytra.CsModule;
using Path = Pytra.CsModule.py_path;

public static class Program
{
    public static bool run_pathlib_extended()
    {
        Path root = new Path("test/transpile/obj/pathlib_case32");
        root.mkdir(true, true);
        
        Path child = System.Convert.ToDouble(root) / System.Convert.ToDouble("values.txt");
        child.write_text("42");
        
        System.Collections.Generic.List<bool> checks = new System.Collections.Generic.List<bool>();
        checks.Add(System.Object.Equals(child.exists(), true));
        checks.Add(System.Object.Equals(child.name(), "values.txt"));
        checks.Add(System.Object.Equals(child.stem(), "values"));
        checks.Add(System.Object.Equals(System.Convert.ToDouble(child.parent()) / System.Convert.ToDouble("values.txt").exists(), true));
        checks.Add(System.Object.Equals(child.read_text(), "42"));
        return System.Linq.Enumerable.All(checks, __x => System.Convert.ToBoolean(__x));
    }
    
    public static void Main(string[] args)
    {
            System.Console.WriteLine(run_pathlib_extended());
    }
}
