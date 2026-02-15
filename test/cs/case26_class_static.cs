using System;

public static class Program
{
    public class Counter26
    {
        public static int total = 0;

        public int add(int x)
        {
            Counter26.total = (Counter26.total + x);
            return Counter26.total;
        }
    }

    public static void Main(string[] args)
    {
        Counter26 c = new Counter26();
        Console.WriteLine(c.add(5));
    }
}
