using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static int comp_like_24(int x)
    {
        List<int> values = /* comprehension */ null;
        return (x + 1);
    }

    public static void Main(string[] args)
    {
        Pytra.CsModule.py_runtime.print(comp_like_24(5));
    }
}
