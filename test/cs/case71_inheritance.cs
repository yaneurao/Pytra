// このファイルは `test/cs/case71_inheritance.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

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
