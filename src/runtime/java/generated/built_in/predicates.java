// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/predicates.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class predicates {
    private predicates() {
    }


    public static boolean py_any(Any values) {
        long i = 0L;
        long n = PyRuntime.__pytra_len(values);
        while (((i) < (n))) {
            if (PyRuntime.__pytra_truthy(values.get((int)((((i) < 0L) ? (((long)(values.size())) + (i)) : (i)))))) {
                return true;
            }
            i += 1L;
        }
        return false;
    }

    public static boolean py_all(Any values) {
        long i = 0L;
        long n = PyRuntime.__pytra_len(values);
        while (((i) < (n))) {
            if ((!PyRuntime.__pytra_truthy(values.get((int)((((i) < 0L) ? (((long)(values.size())) + (i)) : (i))))))) {
                return false;
            }
            i += 1L;
        }
        return true;
    }

    public static void main(String[] args) {
    }
}
