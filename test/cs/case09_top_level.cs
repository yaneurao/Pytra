// このファイルは `test/cs/case09_top_level.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public static int mul3(int n)
    {
        return (n * 3);
    }

    public static void Main(string[] args)
    {
        int value = 7;
        Console.WriteLine(mul3(value));
    }
}
