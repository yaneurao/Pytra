using System;

public static class Program
{
    public class Counter66
    {
        public static int total = 0;

        public int add(int x)
        {
            Counter66.total = (Counter66.total + x);
            return Counter66.total;
        }
    }

    public static void Main(string[] args)
    {
        Counter66 c = new Counter66();
        Console.WriteLine(c.add(5));
    }
}
