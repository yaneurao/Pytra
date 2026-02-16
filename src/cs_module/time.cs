using System.Diagnostics;

namespace PyCs.CsModule
{
    // Python の time モジュール相当（必要最小限）。
    public static class time
    {
        private static readonly Stopwatch _sw = Stopwatch.StartNew();

        // Python の time.perf_counter() 相当。
        public static double perf_counter()
        {
            return _sw.Elapsed.TotalSeconds;
        }
    }
}
