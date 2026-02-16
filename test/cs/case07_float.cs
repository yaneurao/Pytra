using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static double half(double x)
    {
        return (x / 2.0);
    }

    public static void Main(string[] args)
    {
        Pytra.CsModule.py_runtime.print(half(5.0));
    }
}
