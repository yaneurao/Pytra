using System;

public static class Program
{
    public class Counter46
    {
        public static int total = 0;

        public int add(int x)
        {
            Counter46.total = (Counter46.total + x);
            return Counter46.total;
        }
    }

    public static void Main(string[] args)
    {
        Counter46 c = new Counter46();
        Console.WriteLine(c.add(5));
    }
}
