// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/contains.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class contains {
    private contains() {
    }


    public static boolean py_contains_dict_object(Object values, Object key) {
        String needle = String.valueOf(key);
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(values));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            Object cur = __iter_0.get((int)(__iter_i_1));
            if ((java.util.Objects.equals(cur, needle))) {
                return true;
            }
        }
        return false;
    }

    public static boolean py_contains_list_object(Object values, Object key) {
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(values));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            Object cur = __iter_0.get((int)(__iter_i_1));
            if (((cur) == (key))) {
                return true;
            }
        }
        return false;
    }

    public static boolean py_contains_set_object(Object values, Object key) {
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(values));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            Object cur = __iter_0.get((int)(__iter_i_1));
            if (((cur) == (key))) {
                return true;
            }
        }
        return false;
    }

    public static boolean py_contains_str_object(Object values, Object key) {
        String needle = String.valueOf(key);
        String haystack = String.valueOf(values);
        long n = ((long)(haystack.length()));
        long m = ((long)(needle.length()));
        if (((m) == (0L))) {
            return true;
        }
        long i = 0L;
        long last = n - m;
        while (((i) <= (last))) {
            long j = 0L;
            boolean ok = true;
            while (((j) < (m))) {
                if ((!(java.util.Objects.equals(String.valueOf(String.valueOf(haystack.charAt((int)((((i + j) < 0L) ? (((long)(haystack.length())) + (i + j)) : (i + j)))))), String.valueOf(String.valueOf(needle.charAt((int)((((j) < 0L) ? (((long)(needle.length())) + (j)) : (j)))))))))) {
                    ok = false;
                    break;
                }
                j += 1L;
            }
            if (ok) {
                return true;
            }
            i += 1L;
        }
        return false;
    }

    public static void main(String[] args) {
    }
}
