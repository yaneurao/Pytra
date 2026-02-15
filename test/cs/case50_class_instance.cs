using System;

public static class Program
{
    public class Box50
    {
        public int seed;

        public Box50(int seed)
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
        Box50 b = new Box50(3);
        Console.WriteLine(b.next());
    }
}
