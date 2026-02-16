using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public class Multiplier
    {
        public int mul(int x, int y)
        {
            return (x * y);
        }
    }

    public static void Main(string[] args)
    {
        Multiplier m = new Multiplier();
        Pytra.CsModule.py_runtime.print(m.mul(6, 7));
    }
}
