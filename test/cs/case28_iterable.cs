using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static void main()
    {
        List<long> l = new List<long> { 1, 2, 3 };
        long sum = 0;
        foreach (var v in l)
        {
            sum = (sum + v);
        }
        Pytra.CsModule.py_runtime.print(sum);
    }

    public static void Main(string[] args)
    {
        main();
    }
}
