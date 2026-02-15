using System;

public static class Program
{
    public class Box40
    {
        public int seed;

        public Box40(int seed)
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
        Box40 b = new Box40(3);
        Console.WriteLine(b.next());
    }
}
