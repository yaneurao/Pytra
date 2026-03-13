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
    public static float64 sqrt(float64 x)
    {
        return __m.sqrt(x);
    }
    
    public static float64 sin(float64 x)
    {
        return __m.sin(x);
    }
    
    public static float64 cos(float64 x)
    {
        return __m.cos(x);
    }
    
    public static float64 tan(float64 x)
    {
        return __m.tan(x);
    }
    
    public static float64 exp(float64 x)
    {
        return __m.exp(x);
    }
    
    public static float64 log(float64 x)
    {
        return __m.log(x);
    }
    
    public static float64 log10(float64 x)
    {
        return __m.log10(x);
    }
    
    public static float64 fabs(float64 x)
    {
        return __m.fabs(x);
    }
    
    public static float64 floor(float64 x)
    {
        return __m.floor(x);
    }
    
    public static float64 ceil(float64 x)
    {
        return __m.ceil(x);
    }
    
    public static float64 pow(float64 x, float64 y)
    {
        return __m.pow(x, y);
    }
    
    public static void Main(string[] args)
    {
            float64 pi = System.Convert.ToDouble(py_extern(__m.pi));
            float64 e = System.Convert.ToDouble(py_extern(__m.e));
    }
}
