using System;

public static class Program
{
    public class Counter56
    {
        public static int total = 0;

        public int add(int x)
        {
            Counter56.total = (Counter56.total + x);
            return Counter56.total;
        }
    }

    public static void Main(string[] args)
    {
        Counter56 c = new Counter56();
        Console.WriteLine(c.add(5));
    }
}
