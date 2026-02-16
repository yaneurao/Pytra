using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public class Point
    {
        public int x;
        public int y;

        public Point(int x, int y)
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
        Point p = new Point(2, 5);
        Pytra.CsModule.py_runtime.print(p.total());
    }
}
