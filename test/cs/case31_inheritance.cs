// このファイルは `test/cs/case31_inheritance.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public class Base31
    {
        public int value()
        {
            return 31;
        }
    }

    public class Child31 : Base31
    {
        public int value2()
        {
            return (this.value() + 1);
        }
    }

    public static void Main(string[] args)
    {
        Child31 c = new Child31();
        Console.WriteLine(c.value2());
    }
}
