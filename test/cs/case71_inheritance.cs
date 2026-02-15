using System;

public static class Program
{
    public class Base71
    {
        public int value()
        {
            return 71;
        }
    }

    public class Child71 : Base71
    {
        public int value2()
        {
            return (this.value() + 1);
        }
    }

    public static void Main(string[] args)
    {
        Child71 c = new Child71();
        Console.WriteLine(c.value2());
    }
}
