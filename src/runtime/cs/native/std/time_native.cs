using System.Diagnostics;

namespace Pytra.CsModule
{
    // Generated std/time.cs uses this as the substrate seam.
    public static class time_native
    {
        private static readonly Stopwatch _sw = Stopwatch.StartNew();

        // Python's time.perf_counter() equivalent.
        public static double perf_counter()
        {
            return _sw.Elapsed.TotalSeconds;
        }
    }
}
