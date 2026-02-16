using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static bool invert(bool flag)
    {
        if ((!flag))
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
        Pytra.CsModule.py_runtime.print(invert(false));
    }
}
