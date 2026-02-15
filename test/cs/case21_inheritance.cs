// このファイルは `test/cs/case21_inheritance.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

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
