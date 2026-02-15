using System;

public static class Program
{
    public class Base31
    {
        public int value()
        {
            return 31;
        }
    }

    public class Child31 : Base31
    {
        public int value2()
        {
            return (this.value() + 1);
        }
    }

    public static void Main(string[] args)
    {
        Child31 c = new Child31();
        Console.WriteLine(c.value2());
    }
}
