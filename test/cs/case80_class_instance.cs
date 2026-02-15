// このファイルは `test/cs/case80_class_instance.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public class Box80
    {
        public int seed;

        public Box80(int seed)
        {
            this.seed = seed;
        }
        public int next()
        {
            this.seed = (this.seed + 1);
            return this.seed;
        }
    }

    public static void Main(string[] args)
    {
        Box80 b = new Box80(3);
        Console.WriteLine(b.next());
    }
}
