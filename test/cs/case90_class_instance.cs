using System;

public static class Program
{
    public class Box90
    {
        public int seed;

        public Box90(int seed)
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
        Box90 b = new Box90(3);
        Console.WriteLine(b.next());
    }
}
