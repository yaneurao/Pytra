// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/predicates.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class predicates {
    private predicates() {
    }


    public static boolean py_any(Any values) {
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(values));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            Object value = __iter_0.get((int)(__iter_i_1));
            if (PyRuntime.__pytra_truthy(value)) {
                return true;
            }
        }
        return false;
    }

    public static boolean py_all(Any values) {
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(values));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            Object value = __iter_0.get((int)(__iter_i_1));
            if ((!PyRuntime.__pytra_truthy(value))) {
                return false;
            }
        }
        return true;
    }

    public static void main(String[] args) {
    }
}
