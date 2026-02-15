using System;

public static class Program
{
    public class Box80
    {
        public int seed;

        public Box80(int seed)
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
        Box80 b = new Box80(3);
        Console.WriteLine(b.next());
    }
}
