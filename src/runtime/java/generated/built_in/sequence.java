// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/sequence.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class sequence {
    private sequence() {
    }


    public static java.util.ArrayList<Long> py_range(long start, long stop, long step) {
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        if (((step) == (0L))) {
            return out;
        }
        if (((step) > (0L))) {
            long i = start;
            while (((i) < (stop))) {
                out.add(i);
                i += step;
            }
        } else {
            long i = start;
            while (((i) > (stop))) {
                out.add(i);
                i += step;
            }
        }
        return out;
    }

    public static String py_repeat(String v, long n) {
        if (((n) <= (0L))) {
            return "";
        }
        String out = "";
        long i = 0L;
        while (((i) < (n))) {
            out += v;
            i += 1L;
        }
        return out;
    }

    public static void main(String[] args) {
    }
}
