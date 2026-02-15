// このファイルは `test/cs/case15_class_member.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public class Counter
    {
        public static int value = 0;

        public int inc()
        {
            Counter.value = (Counter.value + 1);
            return Counter.value;
        }
    }

    public static void Main(string[] args)
    {
        Counter c = new Counter();
        Console.WriteLine(c.inc());
    }
}
