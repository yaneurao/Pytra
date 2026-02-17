using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static long calc(long x, long y)
    {
        return ((x - y) * 2L);
    }

    public static double div_calc(long x, long y)
    {
        return ((double)(x) / (double)(y));
    }

    public static void Main(string[] args)
    {
        Pytra.CsModule.py_runtime.print(calc(9L, 4L));
        Pytra.CsModule.py_runtime.print(div_calc(9L, 4L));
    }
}
