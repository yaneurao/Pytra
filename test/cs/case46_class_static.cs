// このファイルは `test/cs/case46_class_static.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public class Counter46
    {
        public static int total = 0;

        public int add(int x)
        {
            Counter46.total = (Counter46.total + x);
            return Counter46.total;
        }
    }

    public static void Main(string[] args)
    {
        Counter46 c = new Counter46();
        Console.WriteLine(c.add(5));
    }
}
