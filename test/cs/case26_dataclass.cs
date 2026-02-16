// このファイルは `test/cs/case99_dataclass.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;
using dataclasses;

public static class Program
{
    public class Point99
    {
        public int x;
        public int y = 10;
        public Point99(int x, int y = 10)
        {
            this.x = x;
            this.y = y;
        }

        public int total()
        {
            return (this.x + this.y);
        }
    }

    public static void Main(string[] args)
    {
        Point99 p = new Point99(3);
        Console.WriteLine(p.total());
    }
}
