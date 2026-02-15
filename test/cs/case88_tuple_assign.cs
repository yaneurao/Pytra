// このファイルは `test/cs/case88_tuple_assign.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public static int swap_sum_88(int a, int b)
    {
        int x = a;
        int y = b;
        var _tmp_tuple = Tuple.Create(y, x);
        x = _tmp_tuple.Item1;
        y = _tmp_tuple.Item2;
        return (x + y);
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(swap_sum_88(10, 20));
    }
}
