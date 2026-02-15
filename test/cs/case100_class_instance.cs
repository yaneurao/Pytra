using System.Collections.Generic;
using System.IO;
using System;
using TList = System.Collections.Generic.List;

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
        Console.WriteLine(b.next());
    }
}
