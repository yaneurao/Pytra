// このファイルは `test/cs/case06_string.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public static string greet(string name)
    {
        return ("Hello, " + name);
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(greet("Codex"));
    }
}
