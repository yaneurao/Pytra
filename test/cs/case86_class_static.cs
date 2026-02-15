using System;

public static class Program
{
    public class Counter86
    {
        public static int total = 0;

        public int add(int x)
        {
            Counter86.total = (Counter86.total + x);
            return Counter86.total;
        }
    }

    public static void Main(string[] args)
    {
        Counter86 c = new Counter86();
        Console.WriteLine(c.add(5));
    }
}
