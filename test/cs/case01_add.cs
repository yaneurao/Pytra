// このファイルは `test/cs/case01_add.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public static int add(int a, int b)
    {
        return (a + b);
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(add(3, 4));
    }
}
