using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static string make_msg_22(string name, int count)
    {
        return $"{name}:22:{count}";
    }

    public static void Main(string[] args)
    {
        Pytra.CsModule.py_runtime.print(make_msg_22("user", 7));
    }
}
