// このファイルは `test/cs/case14_inheritance.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

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
