// このファイルは `test/cs/case07_float.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public static double half(double x)
    {
        return (x / 2.0);
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(half(5.0));
    }
}
