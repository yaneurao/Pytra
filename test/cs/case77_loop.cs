using System;

public static class Program
{
    public static int calc_77(List<int> values)
    {
        int total = 0;
        foreach (var v in values)
        {
            if (((v % 2) == 0))
            {
                total = (total + v);
            }
            else
            {
                total = (total + (v * 2));
            }
        }
        return total;
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(calc_77(new List<object> { 1, 2, 3, 4 }));
    }
}
