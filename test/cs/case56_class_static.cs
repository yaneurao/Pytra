// このファイルは `test/cs/case56_class_static.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public class Counter56
    {
        public static int total = 0;

        public int add(int x)
        {
            Counter56.total = (Counter56.total + x);
            return Counter56.total;
        }
    }

    public static void Main(string[] args)
    {
        Counter56 c = new Counter56();
        Console.WriteLine(c.add(5));
    }
}
