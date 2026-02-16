using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static bool has_key_23(string k)
    {
        Dictionary<string, int> d = new Dictionary<string, int> { { "a", 1 }, { "b", 2 } };
        if (Pytra.CsModule.py_runtime.py_in(k, d))
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
        Pytra.CsModule.py_runtime.print(has_key_23("a"));
    }
}
