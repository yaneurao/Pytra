// このファイルは `test/cs/case11_fib.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public static int fib(int n)
    {
        if ((n <= 1))
        {
            return n;
        }
        return (fib((n - 1)) + fib((n - 2)));
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(fib(10));
    }
}
