// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/assertions.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class assertions {
    private assertions() {
    }


    public static boolean _eq_any(Object actual, Object expected) {
        return ((py_to_string(actual)) == (py_to_string(expected)));
        return ((actual) == (expected));
        return false;
    }

    public static boolean py_assert_true(boolean cond, String label) {
        if (cond) {
            return true;
        }
        if ((!(java.util.Objects.equals(label, "")))) {
            System.out.println(null);
        } else {
            System.out.println("[assert_true] False");
        }
        return false;
    }

    public static boolean py_assert_eq(Object actual, Object expected, String label) {
        boolean ok = _eq_any(actual, expected);
        if (ok) {
            return true;
        }
        if ((!(java.util.Objects.equals(label, "")))) {
            System.out.println(null);
        } else {
            System.out.println(null);
        }
        return false;
    }

    public static boolean py_assert_all(java.util.ArrayList<Boolean> results, String label) {
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(results));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            boolean v = ((Boolean)(__iter_0.get((int)(__iter_i_1))));
            if ((!v)) {
                if ((!(java.util.Objects.equals(label, "")))) {
                    System.out.println(null);
                } else {
                    System.out.println("[assert_all] False");
                }
                return false;
            }
        }
        return true;
    }

    public static boolean py_assert_stdout(java.util.ArrayList<String> expected_lines, Object fn) {
        return true;
    }

    public static void main(String[] args) {
    }
}
