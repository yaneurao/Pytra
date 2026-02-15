// このファイルは `test/cs/case73_dict_in.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public static bool has_key_73(string k)
    {
        Dictionary<string, int> d = new Dictionary<object, object> { { "a", 1 }, { "b", 2 } };
        if (d.Contains(k))
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
        Console.WriteLine(has_key_73("a"));
    }
}
