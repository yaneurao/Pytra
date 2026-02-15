using System;

public static class Program
{
    public class Base61
    {
        public int value()
        {
            return 61;
        }
    }

    public class Child61 : Base61
    {
        public int value2()
        {
            return (this.value() + 1);
        }
    }

    public static void Main(string[] args)
    {
        Child61 c = new Child61();
        Console.WriteLine(c.value2());
    }
}
