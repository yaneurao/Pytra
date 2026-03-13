// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/timeit.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class timeit {
    private timeit() {
    }


    public static double default_timer() {
        return _impl.perf_counter();
    }

    public static void main(String[] args) {
    }
}
