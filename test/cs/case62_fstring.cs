using System;

public static class Program
{
    public static string make_msg_62(string name, int count)
    {
        return $"{name}:62:{count}";
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(make_msg_62("user", 7));
    }
}
