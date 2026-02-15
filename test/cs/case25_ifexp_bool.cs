using System;

public static class Program
{
    public static int pick_25(int a, int b, bool flag)
    {
        int c = ((flag && (a > b)) ? a : b);
        return c;
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(pick_25(10, 3, true));
    }
}
