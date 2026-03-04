// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: tools/gen_java_std_runtime_from_canonical.py

public final class pathlib {
    private pathlib() {
    }


    public static class Path {
        public String _value;

        public Path(String value) {
            this._value = value;
        }

        public String __str__() {
            return this._value;
        }

        public String __repr__() {
            return "Path(" + this._value + ")";
        }

        public String __fspath__() {
            return this._value;
        }

        public PyRuntime.Path __truediv__(String rhs) {
            return new Path(os.path.join(this._value, rhs));
        }

        public PyRuntime.Path parent() {
            Object parent_txt = os.path.dirname(this._value);
            if ((java.util.Objects.equals(parent_txt, ""))) {
                parent_txt = ".";
            }
            return new Path(parent_txt);
        }

        public java.util.ArrayList<PyRuntime.Path> parents() {
            java.util.ArrayList<PyRuntime.Path> out = new java.util.ArrayList<PyRuntime.Path>();
            String current = os.path.dirname(this._value);
            while (true) {
                if ((java.util.Objects.equals(current, ""))) {
                    current = ".";
                }
                out.add(new Path(current));
                String next_current = os.path.dirname(current);
                if ((java.util.Objects.equals(next_current, ""))) {
                    next_current = ".";
                }
                if ((java.util.Objects.equals(next_current, current))) {
                    break;
                }
                current = next_current;
            }
            return out;
        }

        public String name() {
            return os.path.basename(this._value);
        }

        public String suffix() {
            java.util.ArrayList<Object> __tuple_0 = ((java.util.ArrayList<Object>)(Object)(os.path.splitext(os.path.basename(this._value))));
            Object __ = __tuple_0.get(0);
            Object ext = __tuple_0.get(1);
            return ext;
        }

        public String stem() {
            java.util.ArrayList<Object> __tuple_0 = ((java.util.ArrayList<Object>)(Object)(os.path.splitext(os.path.basename(this._value))));
            Object root = __tuple_0.get(0);
            Object __ = __tuple_0.get(1);
            return root;
        }

        public PyRuntime.Path resolve() {
            return new Path(os.path.abspath(this._value));
        }

        public boolean exists() {
            return os.path.exists(this._value);
        }

        public void mkdir(boolean parents, boolean exist_ok) {
            if (parents) {
                os.makedirs(this._value, exist_ok);
                return;
            }
            if ((exist_ok && os.path.exists(this._value))) {
                return;
            }
            os.mkdir(this._value);
        }

        public String read_text(String encoding) {
            PyFile f = open(this._value, "r", encoding);
            return f.read();
            f.close();
            return "";
        }

        public long write_text(String text, String encoding) {
            PyFile f = open(this._value, "w", encoding);
            return f.write(text);
            f.close();
            return 0L;
        }

        public java.util.ArrayList<PyRuntime.Path> glob(String pattern) {
            java.util.ArrayList<String> paths = py_glob.glob(os.path.join(this._value, pattern));
            java.util.ArrayList<PyRuntime.Path> out = new java.util.ArrayList<PyRuntime.Path>();
            java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(paths));
            for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
                String p = String.valueOf(__iter_0.get((int)(__iter_i_1)));
                out.add(new Path(p));
            }
            return out;
        }

        public PyRuntime.Path cwd() {
            return new Path(os.getcwd());
        }
    }

    public static void main(String[] args) {
    }
}
