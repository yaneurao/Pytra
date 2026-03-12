// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/numeric_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class numeric_ops {
    private numeric_ops() {
    }


    public static T sum(java.util.ArrayList<T> values) {
        if (((((long)(values.size()))) == (0L))) {
            return 0L;
        }
        Object acc = ((T)(values.get((int)((((0L) < 0L) ? (((long)(values.size())) + (0L)) : (0L)))))) - ((T)(values.get((int)((((0L) < 0L) ? (((long)(values.size())) + (0L)) : (0L))))));
        long i = 0L;
        long n = ((long)(values.size()));
        while (((i) < (n))) {
            acc += ((T)(values.get((int)((((i) < 0L) ? (((long)(values.size())) + (i)) : (i))))));
            i += 1L;
        }
        return acc;
    }

    public static T py_min(T a, T b) {
        if (((a) < (b))) {
            return a;
        }
        return b;
    }

    public static T py_max(T a, T b) {
        if (((a) > (b))) {
            return a;
        }
        return b;
    }

    public static void main(String[] args) {
    }
}
