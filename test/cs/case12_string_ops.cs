using System;

public static class Program
{
    public static string decorate(string name)
    {
        string prefix = "[USER] ";
        string message = (prefix + name);
        return (message + "!");
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(decorate("Alice"));
    }
}
