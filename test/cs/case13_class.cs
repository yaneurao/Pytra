// このファイルは `test/cs/case13_class.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public class Multiplier
    {
        public int mul(int x, int y)
        {
            return (x * y);
        }
    }

    public static void Main(string[] args)
    {
        Multiplier m = new Multiplier();
        Console.WriteLine(m.mul(6, 7));
    }
}
