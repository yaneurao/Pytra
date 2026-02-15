using System;

public static class Program
{
    public class Counter
    {
        public static int value = 0;

        public int inc()
        {
            Counter.value = (Counter.value + 1);
            return Counter.value;
        }
    }

    public static void Main(string[] args)
    {
        Counter c = new Counter();
        Console.WriteLine(c.inc());
    }
}
