using System;

public static class Program
{
    public static int pick_55(int a, int b, bool flag)
    {
        int c = ((flag && (a > b)) ? a : b);
        return c;
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(pick_55(10, 3, true));
    }
}
