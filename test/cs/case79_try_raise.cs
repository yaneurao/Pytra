using System;

public static class Program
{
    public static int maybe_fail_79(bool flag)
    {
        try
        {
            if (flag)
            {
                throw new Exception(Exception("fail-79"));
            }
            return 10;
        }
        catch (Exception ex)
        {
            return 20;
        }
        finally
        {
        }
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(maybe_fail_79(true));
    }
}
