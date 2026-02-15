using System;

public static class Program
{
    public class Counter96
    {
        public static int total = 0;

        public int add(int x)
        {
            Counter96.total = (Counter96.total + x);
            return Counter96.total;
        }
    }

    public static void Main(string[] args)
    {
        Counter96 c = new Counter96();
        Console.WriteLine(c.add(5));
    }
}
