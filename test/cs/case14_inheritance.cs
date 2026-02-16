using System.Collections.Generic;
using System.IO;
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
        Pytra.CsModule.py_runtime.print(d.bark());
    }
}
