// Generated std/time.java delegates host bindings through this native seam.

public final class time_native {
    private time_native() {
    }

    public static double perf_counter() {
        return (double) System.nanoTime() / 1_000_000_000.0;
    }
}
