using System;

namespace PyCs.CsModule
{
    // Python の print 相当を提供する最小ランタイム。
    public static class py_runtime
    {
        public static void print(params object[] args)
        {
            if (args == null || args.Length == 0)
            {
                Console.WriteLine();
                return;
            }
            Console.WriteLine(string.Join(" ", args));
        }
    }
}
