// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class sys {
    private sys() {
    }

    public static java.util.ArrayList<String> argv = extern(__s.argv);
    public static java.util.ArrayList<String> path = extern(__s.path);
    public static Object stderr = extern(__s.stderr);
    public static Object stdout = extern(__s.stdout);


    public static void exit(long code) {
        __s.exit(code);
    }

    public static void set_argv(java.util.ArrayList<String> values) {
        argv.clear();
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(values));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            String v = String.valueOf(__iter_0.get((int)(__iter_i_1)));
            argv.add(v);
        }
    }

    public static void set_path(java.util.ArrayList<String> values) {
        path.clear();
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(values));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            String v = String.valueOf(__iter_0.get((int)(__iter_i_1)));
            path.add(v);
        }
    }

    public static void write_stderr(String text) {
        __s.stderr.write(text);
    }

    public static void write_stdout(String text) {
        __s.stdout.write(text);
    }

    public static void main(String[] args) {
    }
}
