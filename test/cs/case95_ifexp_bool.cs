using System;

public static class Program
{
    public static int pick_95(int a, int b, bool flag)
    {
        int c = ((flag && (a > b)) ? a : b);
        return c;
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(pick_95(10, 3, true));
    }
}
