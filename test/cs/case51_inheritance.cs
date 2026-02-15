using System;

public static class Program
{
    public class Base51
    {
        public int value()
        {
            return 51;
        }
    }

    public class Child51 : Base51
    {
        public int value2()
        {
            return (this.value() + 1);
        }
    }

    public static void Main(string[] args)
    {
        Child51 c = new Child51();
        Console.WriteLine(c.value2());
    }
}
