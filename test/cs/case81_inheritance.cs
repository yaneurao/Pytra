// このファイルは `test/cs/case81_inheritance.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public class Base81
    {
        public int value()
        {
            return 81;
        }
    }

    public class Child81 : Base81
    {
        public int value2()
        {
            return (this.value() + 1);
        }
    }

    public static void Main(string[] args)
    {
        Child81 c = new Child81();
        Console.WriteLine(c.value2());
    }
}
