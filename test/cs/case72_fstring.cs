using System;

public static class Program
{
    public static string make_msg_72(string name, int count)
    {
        return $"{name}:72:{count}";
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(make_msg_72("user", 7));
    }
}
