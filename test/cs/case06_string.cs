using System;

public static class Program
{
    public static string greet(string name)
    {
        return ("Hello, " + name);
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(greet("Codex"));
    }
}
