using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static string greet(string name)
    {
        return ("Hello, " + name);
    }

    public static void Main(string[] args)
    {
        Pytra.CsModule.py_runtime.print(greet("Codex"));
    }
}
