using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static void main()
    {
        List<long> nums = new List<long> { 10, 20, 30, 40, 50 };
        string text = "abcdef";
        List<long> mid_nums = Pytra.CsModule.py_runtime.py_slice(nums, (long?)(1), (long?)(4));
        string mid_text = Pytra.CsModule.py_runtime.py_slice(text, (long?)(2), (long?)(5));
        Pytra.CsModule.py_runtime.print(mid_nums[0]);
        Pytra.CsModule.py_runtime.print(mid_nums[2]);
        Pytra.CsModule.py_runtime.print(mid_text);
    }

    public static void Main(string[] args)
    {
        main();
    }
}
