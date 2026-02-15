using System;

public static class Program
{
    public class Counter76
    {
        public static int total = 0;

        public int add(int x)
        {
            Counter76.total = (Counter76.total + x);
            return Counter76.total;
        }
    }

    public static void Main(string[] args)
    {
        Counter76 c = new Counter76();
        Console.WriteLine(c.add(5));
    }
}
