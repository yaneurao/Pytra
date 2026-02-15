using System;
using dataclasses;

public static class Program
{
    public class Point99
    {
        public int x;
        public int y = 10;
        public Point99(int x, int y = 10)
        {
            this.x = x;
            this.y = y;
        }

        public int total()
        {
            return (this.x + this.y);
        }
    }

    public static void Main(string[] args)
    {
        Point99 p = new Point99(3);
        Console.WriteLine(p.total());
    }
}
