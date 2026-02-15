using System;

public static class Program
{
    public class Box30
    {
        public int seed;

        public Box30(int seed)
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
        Box30 b = new Box30(3);
        Console.WriteLine(b.next());
    }
}
