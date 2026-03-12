// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/math.py
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
    public static double sqrt(double x)
    {
        return __m.sqrt(x);
    }
    
    public static double sin(double x)
    {
        return __m.sin(x);
    }
    
    public static double cos(double x)
    {
        return __m.cos(x);
    }
    
    public static double tan(double x)
    {
        return __m.tan(x);
    }
    
    public static double exp(double x)
    {
        return __m.exp(x);
    }
    
    public static double log(double x)
    {
        return __m.log(x);
    }
    
    public static double log10(double x)
    {
        return __m.log10(x);
    }
    
    public static double fabs(double x)
    {
        return __m.fabs(x);
    }
    
    public static double floor(double x)
    {
        return __m.floor(x);
    }
    
    public static double ceil(double x)
    {
        return __m.ceil(x);
    }
    
    public static double pow(double x, double y)
    {
        return __m.pow(x, y);
    }
    
    public static void Main(string[] args)
    {
            double pi = System.Convert.ToDouble(py_extern(__m.pi));
            double e = System.Convert.ToDouble(py_extern(__m.e));
    }
}
