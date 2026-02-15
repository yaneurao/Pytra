// このファイルは `test/cs/case08_nested_call.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public static int inc(int x)
    {
        return (x + 1);
    }

    public static int twice(int x)
    {
        return inc(inc(x));
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(twice(10));
    }
}
