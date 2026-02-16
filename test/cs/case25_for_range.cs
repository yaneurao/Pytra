using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static int sum_range_29(int n)
    {
        int total = 0;
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = n;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
        {
            total = (total + i);
        }
        return total;
    }

    public static void Main(string[] args)
    {
        Pytra.CsModule.py_runtime.print(sum_range_29(5));
    }
}
