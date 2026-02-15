using System;

public static class Program
{
    public static bool has_key_53(string k)
    {
        Dictionary<string, int> d = new Dictionary<object, object> { { "a", 1 }, { "b", 2 } };
        if (d.Contains(k))
        {
            return true;
        }
        else
        {
            return false;
        }
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(has_key_53("a"));
    }
}
