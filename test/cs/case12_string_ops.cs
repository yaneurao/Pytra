using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static string decorate(string name)
    {
        string prefix = "[USER] ";
        string message = (prefix + name);
        return (message + "!");
    }

    public static void Main(string[] args)
    {
        Pytra.CsModule.py_runtime.print(decorate("Alice"));
    }
}
