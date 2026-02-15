using System;

public static class Program
{
    public class Box20
    {
        public int seed;

        public Box20(int seed)
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
        Box20 b = new Box20(3);
        Console.WriteLine(b.next());
    }
}
