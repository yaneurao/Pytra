// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class iter_ops {
    private iter_ops() {
    }


    public static java.util.ArrayList<Object> py_reversed_object(Object values) {
        java.util.ArrayList<Object> out = new java.util.ArrayList<Object>();
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(values));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            Object value = __iter_0.get((int)(__iter_i_1));
            out.add(value);
        }
        return reversed(out);
    }

    public static java.util.ArrayList<Object> py_enumerate_object(Object values, long start) {
        java.util.ArrayList<Object> out = new java.util.ArrayList<Object>();
        long i = start;
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(values));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            Object value = __iter_0.get((int)(__iter_i_1));
            out.add(new java.util.ArrayList<Object>(java.util.Arrays.asList(i, value)));
            i += 1L;
        }
        return out;
    }

    public static void main(String[] args) {
    }
}
