using System;

public static class Program
{
    public class Base41
    {
        public int value()
        {
            return 41;
        }
    }

    public class Child41 : Base41
    {
        public int value2()
        {
            return (this.value() + 1);
        }
    }

    public static void Main(string[] args)
    {
        Child41 c = new Child41();
        Console.WriteLine(c.value2());
    }
}
