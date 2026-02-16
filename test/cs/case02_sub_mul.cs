using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static int calc(int x, int y)
    {
        return ((x - y) * 2);
    }

    public static void Main(string[] args)
    {
        Pytra.CsModule.py_runtime.print(calc(9, 4));
    }
}
