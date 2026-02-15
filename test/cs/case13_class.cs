using System;

public static class Program
{
    public class Multiplier
    {
        public int mul(int x, int y)
        {
            return (x * y);
        }
    }

    public static void Main(string[] args)
    {
        Multiplier m = new Multiplier();
        Console.WriteLine(m.mul(6, 7));
    }
}
