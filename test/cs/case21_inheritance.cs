using System;

public static class Program
{
    public class Base21
    {
        public int value()
        {
            return 21;
        }
    }

    public class Child21 : Base21
    {
        public int value2()
        {
            return (this.value() + 1);
        }
    }

    public static void Main(string[] args)
    {
        Child21 c = new Child21();
        Console.WriteLine(c.value2());
    }
}
