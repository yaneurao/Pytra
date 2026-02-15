using System;

public static class Program
{
    public class Box70
    {
        public int seed;

        public Box70(int seed)
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
        Box70 b = new Box70(3);
        Console.WriteLine(b.next());
    }
}
