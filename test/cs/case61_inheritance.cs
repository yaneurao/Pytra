// このファイルは `test/cs/case61_inheritance.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public class Base61
    {
        public int value()
        {
            return 61;
        }
    }

    public class Child61 : Base61
    {
        public int value2()
        {
            return (this.value() + 1);
        }
    }

    public static void Main(string[] args)
    {
        Child61 c = new Child61();
        Console.WriteLine(c.value2());
    }
}
