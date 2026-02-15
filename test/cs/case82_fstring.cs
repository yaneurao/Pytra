using System;

public static class Program
{
    public static string make_msg_82(string name, int count)
    {
        return $"{name}:82:{count}";
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(make_msg_82("user", 7));
    }
}
