// このファイルは `test/cs/case49_try_raise.cs` の変換結果（C#サンプル）です。
// Python入力との対応関係を追いやすくするため、日本語コメントを付与しています。
// 仕様変更時は、対応する Python 側ケースと合わせて更新してください。

using System;

public static class Program
{
    public static int maybe_fail_49(bool flag)
    {
        try
        {
            if (flag)
            {
                throw new Exception(Exception("fail-49"));
            }
            return 10;
        }
        catch (Exception ex)
        {
            return 20;
        }
        finally
        {
        }
    }

    public static void Main(string[] args)
    {
        Console.WriteLine(maybe_fail_49(true));
    }
}
