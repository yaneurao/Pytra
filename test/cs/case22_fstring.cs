using System;

public static class Program
{
    public static string make_msg_22(string name, int count)
    {
        return $"{name}:22:{count}";
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(make_msg_22("user", 7));
    }
}
