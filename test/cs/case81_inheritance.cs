using System;

public static class Program
{
    public class Base81
    {
        public int value()
        {
            return 81;
        }
    }

    public class Child81 : Base81
    {
        public int value2()
        {
            return (this.value() + 1);
        }
    }

    public static void Main(string[] args)
    {
        Child81 c = new Child81();
        Console.WriteLine(c.value2());
    }
}
