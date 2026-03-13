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
    public static str join(str a, str b)
    {
        return __path.join(a, b);
    }
    
    public static str dirname(str p)
    {
        return __path.dirname(p);
    }
    
    public static str basename(str p)
    {
        return __path.basename(p);
    }
    
    public static (str, str) splitext(str p)
    {
        return __path.splitext(p);
    }
    
    public static str abspath(str p)
    {
        return __path.abspath(p);
    }
    
    public static bool exists(str p)
    {
        return __path.exists(p);
    }
    
    public static void Main(string[] args)
    {
    }
}
