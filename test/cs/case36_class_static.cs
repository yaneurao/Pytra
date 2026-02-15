using System;

public static class Program
{
    public class Counter36
    {
        public static int total = 0;

        public int add(int x)
        {
            Counter36.total = (Counter36.total + x);
            return Counter36.total;
        }
    }

    public static void Main(string[] args)
    {
        Counter36 c = new Counter36();
        Console.WriteLine(c.add(5));
    }
}
