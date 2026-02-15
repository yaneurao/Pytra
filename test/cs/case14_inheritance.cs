using System;

public static class Program
{
    public class Animal
    {
        public string sound()
        {
            return "generic";
        }
    }

    public class Dog : Animal
    {
        public string bark()
        {
            return (this.sound() + "-bark");
        }
    }

    public static void Main(string[] args)
    {
        Dog d = new Dog();
        Console.WriteLine(d.bark());
    }
}
