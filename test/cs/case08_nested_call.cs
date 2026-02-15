using System;

public static class Program
{
    public static int inc(int x)
    {
        return (x + 1);
    }

    public static int twice(int x)
    {
        return inc(inc(x));
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(twice(10));
    }
}
