using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static int sum_range_29(int n)
    {
        int total = 0;
        var __range_start_i = 0;
        var __range_stop_i = n;
        var __range_step_i = 1;
        if (__range_step_i == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __range_start_i; (__range_step_i > 0) ? (i < __range_stop_i) : (i > __range_stop_i); i += __range_step_i)
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
