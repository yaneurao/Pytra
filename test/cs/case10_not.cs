using System;

public static class Program
{
    public static bool invert(bool flag)
    {
        if ((!flag))
        {
            return true;
        }
        else
        {
            return false;
        }
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(invert(false));
    }
}
