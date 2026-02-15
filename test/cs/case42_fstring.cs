using System;

public static class Program
{
    public static string make_msg_42(string name, int count)
    {
        return $"{name}:42:{count}";
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(make_msg_42("user", 7));
    }
}
