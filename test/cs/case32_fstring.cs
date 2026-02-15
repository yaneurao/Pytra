using System;

public static class Program
{
    public static string make_msg_32(string name, int count)
    {
        return $"{name}:32:{count}";
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(make_msg_32("user", 7));
    }
}
