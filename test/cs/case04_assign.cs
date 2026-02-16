using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static int square_plus_one(int n)
    {
        int result = (n * n);
        result = (result + 1);
        return result;
    }

    public static void Main(string[] args)
    {
        Pytra.CsModule.py_runtime.print(square_plus_one(5));
    }
}
