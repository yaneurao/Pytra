using System;

public static class Program
{
    public static int abs_like(int n)
    {
        if ((n < 0))
        {
            return (-n);
        }
        else
        {
            return n;
        }
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(abs_like((-12)));
    }
}
