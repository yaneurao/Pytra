// このファイルは `test/cs/case12_string_ops.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public static string decorate(string name)
    {
        string prefix = "[USER] ";
        string message = (prefix + name);
        return (message + "!");
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(decorate("Alice"));
    }
}
