using System;

public static class Program
{
    public static int maybe_fail_29(bool flag)
    {
        try
        {
            if (flag)
            {
                throw new Exception(Exception("fail-29"));
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
        Console.WriteLine(maybe_fail_29(true));
    }
}
