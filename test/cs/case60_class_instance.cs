using System;

public static class Program
{
    public class Box60
    {
        public int seed;

        public Box60(int seed)
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
        Box60 b = new Box60(3);
        Console.WriteLine(b.next());
    }
}
