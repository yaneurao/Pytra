using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static bool is_large(int n)
    {
        if ((n >= 10))
        {
            return true;
        }
        else
        {
            return false;
        }
    }

    public static void Main(string[] args)
    {
        Pytra.CsModule.py_runtime.print(is_large(11));
    }
}
