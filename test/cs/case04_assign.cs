// このファイルは `test/cs/case04_assign.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public static int square_plus_one(int n)
    {
        int result = (n * n);
        result = (result + 1);
        return result;
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(square_plus_one(5));
    }
}
