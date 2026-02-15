using System;

public static class Program
{
    public static int fib(int n)
    {
        if ((n <= 1))
        {
            return n;
        }
        return (fib((n - 1)) + fib((n - 2)));
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(fib(10));
    }
}
