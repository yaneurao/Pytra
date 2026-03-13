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
using Pytra.CsModule;

public static class Program
{
    public static str getcwd()
    {
        return __os.getcwd();
    }
    
    public static void mkdir(str p)
    {
        __os.mkdir(p);
    }
    
    public static void makedirs(str p, bool exist_ok = false)
    {
        __os.makedirs(p, exist_ok);
    }
    
    public static void Main(string[] args)
    {
    }
}
