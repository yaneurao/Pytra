using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static int maybe_fail_19(bool flag)
    {
        try
        {
            if (flag)
            {
                throw new Exception("fail-19");
            }
            return 10;
        }
        catch (Exception ex)
        {
            return 20;
        }
        finally
        {
        }
    }

    public static void Main(string[] args)
    {
        Pytra.CsModule.py_runtime.print(maybe_fail_19(true));
    }
}
