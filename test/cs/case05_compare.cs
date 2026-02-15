using System;

public static class Program
{
    public static bool is_large(int n)
    {
        if ((n >= 10))
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
        Console.WriteLine(is_large(11));
    }
}
