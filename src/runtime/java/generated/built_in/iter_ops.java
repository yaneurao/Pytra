// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class iter_ops {
    private iter_ops() {
    }


    public static Object py_reversed_object(Object values) {
        java.util.ArrayList<Object> out = new java.util.ArrayList<Object>();
        long i = PyRuntime.__pytra_len(values) - 1L;
        while (((i) >= (0L))) {
            out.add(values.get((int)((((i) < 0L) ? (((long)(values.size())) + (i)) : (i)))));
            i -= 1L;
        }
        return out;
    }

    public static Object py_enumerate_object(Object values, long start) {
        java.util.ArrayList<Object> out = new java.util.ArrayList<Object>();
        long i = 0L;
        long n = PyRuntime.__pytra_len(values);
        while (((i) < (n))) {
            out.add(new java.util.ArrayList<Object>(java.util.Arrays.asList(start + i, values.get((int)((((i) < 0L) ? (((long)(values.size())) + (i)) : (i)))))));
            i += 1L;
        }
        return out;
    }

    public static void main(String[] args) {
    }
}
