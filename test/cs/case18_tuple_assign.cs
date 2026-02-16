using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static int swap_sum_18(int a, int b)
    {
        int x = a;
        int y = b;
        var __pytra_tuple_1 = Tuple.Create(y, x);
        x = __pytra_tuple_1.Item1;
        y = __pytra_tuple_1.Item2;
        return (x + y);
    }

    public static void Main(string[] args)
    {
        Pytra.CsModule.py_runtime.print(swap_sum_18(10, 20));
    }
}
