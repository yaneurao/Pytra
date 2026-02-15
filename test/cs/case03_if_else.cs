// このファイルは `test/cs/case03_if_else.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public static int abs_like(int n)
    {
        if ((n < 0))
        {
            return (-n);
        }
        else
        {
            return n;
        }
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(abs_like((-12)));
    }
}
