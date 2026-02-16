using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static int mul3(int n)
    {
        return (n * 3);
    }

    public static void Main(string[] args)
    {
        int value = 7;
        Pytra.CsModule.py_runtime.print(mul3(value));
    }
}
