using System.Diagnostics;

namespace Pytra.CsModule
{
    // Generated std/time.cs から参照される backing seam。
    public static class time_native
    {
        private static readonly Stopwatch _sw = Stopwatch.StartNew();

        // Python の time.perf_counter() 相当。
        public static double perf_counter()
        {
            return _sw.Elapsed.TotalSeconds;
        }
    }
}
