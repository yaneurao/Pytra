using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static void main()
    {
        sbyte i = 1;
        Pytra.CsModule.py_runtime.print((i * 2));
    }

    public static void Main(string[] args)
    {
        main();
    }
}
