using System;

public static class Program
{
    public static int swap_sum_58(int a, int b)
    {
        int x = a;
        int y = b;
        var _tmp_tuple = Tuple.Create(y, x);
        x = _tmp_tuple.Item1;
        y = _tmp_tuple.Item2;
        return (x + y);
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(swap_sum_58(10, 20));
    }
}
