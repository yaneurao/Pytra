using System;

public static class Program
{
    public class Base91
    {
        public int value()
        {
            return 91;
        }
    }

    public class Child91 : Base91
    {
        public int value2()
        {
            return (this.value() + 1);
        }
    }

    public static void Main(string[] args)
    {
        Child91 c = new Child91();
        Console.WriteLine(c.value2());
    }
}
