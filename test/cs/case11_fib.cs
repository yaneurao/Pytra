using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static int fib(int n)
    {
        if ((n <= 1))
        {
            return n;
        }
        return (fib((n - 1)) + fib((n - 2)));
    }

    public static void Main(string[] args)
    {
        Pytra.CsModule.py_runtime.print(fib(10));
    }
}
