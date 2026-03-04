// Java time_impl bridge for pytra.std.time.

final class _impl {
    private _impl() {
    }

    static double perf_counter() {
        return (double) System.nanoTime() / 1_000_000_000.0;
    }
}
