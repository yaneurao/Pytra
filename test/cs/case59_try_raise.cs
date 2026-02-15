using System;

public static class Program
{
    public static int maybe_fail_59(bool flag)
    {
        try
        {
            if (flag)
            {
                throw new Exception(Exception("fail-59"));
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
        Console.WriteLine(maybe_fail_59(true));
    }
}
