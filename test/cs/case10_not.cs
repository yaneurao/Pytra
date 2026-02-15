// このファイルは `test/cs/case10_not.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public static bool invert(bool flag)
    {
        if ((!flag))
        {
            return true;
        }
        else
        {
            return false;
        }
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(invert(false));
    }
}
