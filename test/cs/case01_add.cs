using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static int add(int a, int b)
    {
        return (a + b);
    }

    public static void Main(string[] args)
    {
        Pytra.CsModule.py_runtime.print(add(3, 4));
    }
}
