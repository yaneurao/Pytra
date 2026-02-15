// このファイルは `test/cs/case51_inheritance.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

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
