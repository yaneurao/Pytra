// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/zip_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class zip_ops {
    private zip_ops() {
    }


    public static java.util.ArrayList<java.util.ArrayList<Object>> zip(java.util.ArrayList<A> lhs, java.util.ArrayList<B> rhs) {
        java.util.ArrayList<java.util.ArrayList<Object>> out = new java.util.ArrayList<java.util.ArrayList<Object>>();
        long i = 0L;
        long n = ((long)(lhs.size()));
        if (((((long)(rhs.size()))) < (n))) {
            n = ((long)(rhs.size()));
        }
        while (((i) < (n))) {
            out.add(new java.util.ArrayList<Object>(java.util.Arrays.asList(((A)(lhs.get((int)((((i) < 0L) ? (((long)(lhs.size())) + (i)) : (i)))))), ((B)(rhs.get((int)((((i) < 0L) ? (((long)(rhs.size())) + (i)) : (i)))))))));
            i += 1L;
        }
        return out;
    }

    public static void main(String[] args) {
    }
}
