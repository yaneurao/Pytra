using System;

public static class Program
{
    public static string make_msg_52(string name, int count)
    {
        return $"{name}:52:{count}";
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(make_msg_52("user", 7));
    }
}
