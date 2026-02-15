using System;

public static class Program
{
    public static int calc(int x, int y)
    {
        return ((x - y) * 2);
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(calc(9, 4));
    }
}
