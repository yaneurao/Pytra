using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public class Box100
    {
        public int seed;

        public Box100(int seed)
        {
            this.seed = seed;
        }
        public int next()
        {
            this.seed = (this.seed + 1);
            return this.seed;
        }
    }

    public static void Main(string[] args)
    {
        Box100 b = new Box100(3);
        Pytra.CsModule.py_runtime.print(b.next());
    }
}
