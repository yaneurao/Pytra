using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static int calc_17(List<int> values)
    {
        int total = 0;
        foreach (var v in values)
        {
            if (((v % 2) == 0))
            {
                total = (total + v);
            }
            else
            {
                total = (total + (v * 2));
            }
        }
        return total;
    }

    public static void Main(string[] args)
    {
        Pytra.CsModule.py_runtime.print(calc_17(new List<int> { 1, 2, 3, 4 }));
    }
}
