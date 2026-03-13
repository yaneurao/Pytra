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
using Pytra.CsModule;

public static class Program
{
    public static string join(string a, string b)
    {
        return __path.join(a, b);
    }
    
    public static string dirname(string p)
    {
        return __path.dirname(p);
    }
    
    public static string basename(string p)
    {
        return __path.basename(p);
    }
    
    public static (string, string) splitext(string p)
    {
        return __path.splitext(p);
    }
    
    public static string abspath(string p)
    {
        return __path.abspath(p);
    }
    
    public static bool exists(string p)
    {
        return __path.exists(p);
    }
    
    public static void Main(string[] args)
    {
    }
}
