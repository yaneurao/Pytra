using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static long lcg_next(long state)
    {
        return (((1664525L * state) + 1013904223L) % 4294967296L);
    }

    public static double run_pi_trial(long total_samples, long seed)
    {
        long inside = 0L;
        long state = seed;
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = total_samples;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var __pytra_unused_4 = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (__pytra_unused_4 < __pytra_range_stop_2) : (__pytra_unused_4 > __pytra_range_stop_2); __pytra_unused_4 += __pytra_range_step_3)
        {
            state = lcg_next(state);
            double x = ((double)(state) / (double)(4294967296.0));
            state = lcg_next(state);
            double y = ((double)(state) / (double)(4294967296.0));
            double dx = (x - 0.5);
            double dy = (y - 0.5);
            if (Pytra.CsModule.py_runtime.py_bool((((dx * dx) + (dy * dy)) <= 0.25)))
            {
                inside = (inside + 1L);
            }
        }
        return ((double)((4.0 * inside)) / (double)(total_samples));
    }

    public static void run_monte_carlo_pi()
    {
        long samples = 54000000L;
        long seed = 123456789L;
        double start = Pytra.CsModule.time.perf_counter();
        double pi_est = run_pi_trial(samples, seed);
        double elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("samples:", samples);
        Pytra.CsModule.py_runtime.print("pi_estimate:", pi_est);
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_monte_carlo_pi();
    }
}
