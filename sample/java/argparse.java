// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/argparse.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class argparse {
    private argparse() {
    }


    public static class Namespace {
        public java.util.HashMap<String, Any> values;

        public Namespace(Any values) {
            if (((values) == (null))) {
                this.values = new java.util.HashMap<Object, Object>();
                return;
            }
            this.values = values;
        }
    }

    public static class _ArgSpec {
        public java.util.ArrayList<String> names;
        public String action;
        public java.util.ArrayList<String> choices;
        public Any _default;
        public String help_text;
        public boolean is_optional;
        public String dest;

        public _ArgSpec(java.util.ArrayList<String> names, String action, java.util.ArrayList<String> choices, Object _default, String help_text) {
            this.names = names;
            this.action = action;
            this.choices = choices;
            this._default = _default;
            this.help_text = help_text;
            this.is_optional = (((((long)(names.size()))) > (0L)) && String.valueOf(names.get((int)((((0L) < 0L) ? (((long)(names.size())) + (0L)) : (0L))))).startswith("-"));
            if (this.is_optional) {
                Object base = String.valueOf(names.get((int)(((((-(1L))) < 0L) ? (((long)(names.size())) + ((-(1L)))) : ((-(1L))))))).lstrip("-").replace("-", "_");
                this.dest = base;
            } else {
                this.dest = String.valueOf(names.get((int)((((0L) < 0L) ? (((long)(names.size())) + (0L)) : (0L)))));
            }
        }
    }

    public static class ArgumentParser {
        public String description;
        public java.util.ArrayList<_ArgSpec> _specs;

        public ArgumentParser(String description) {
            this.description = description;
            this._specs = new java.util.ArrayList<Object>();
        }

        public void add_argument(String name0, String name1, String name2, String name3, String help, String action, java.util.ArrayList<String> choices, Object _default) {
            java.util.ArrayList<String> names = new java.util.ArrayList<String>();
            if ((!(java.util.Objects.equals(name0, "")))) {
                names.add(name0);
            }
            if ((!(java.util.Objects.equals(name1, "")))) {
                names.add(name1);
            }
            if ((!(java.util.Objects.equals(name2, "")))) {
                names.add(name2);
            }
            if ((!(java.util.Objects.equals(name3, "")))) {
                names.add(name3);
            }
            if (((((long)(names.size()))) == (0L))) {
                throw new RuntimeException(PyRuntime.pyToString("add_argument requires at least one name"));
            }
            _ArgSpec spec = _ArgSpec(names, action, choices, _default, help);
            this._specs.add(spec);
        }

        public void _fail(String msg) {
            if ((!(java.util.Objects.equals(msg, "")))) {
                sys.write_stderr(null);
            }
            throw new RuntimeException(PyRuntime.pyToString(new SystemExit(2L)));
        }

        public java.util.HashMap<String, Any> parse_args(Any argv) {
            java.util.ArrayList<String> args = null;
            if (((argv) == (null))) {
                args = sys.argv;
            } else {
                args = list(argv);
            }
            java.util.ArrayList<_ArgSpec> specs_pos = new java.util.ArrayList<_ArgSpec>();
            java.util.ArrayList<_ArgSpec> specs_opt = new java.util.ArrayList<_ArgSpec>();
            java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(this._specs));
            for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
                _ArgSpec s = ((_ArgSpec)(__iter_0.get((int)(__iter_i_1))));
                if (PyRuntime.__pytra_truthy(s.is_optional)) {
                    specs_opt.add(s);
                } else {
                    specs_pos.add(s);
                }
            }
            java.util.HashMap<String, Long> by_name = new java.util.HashMap<String, Long>();
            long spec_i = 0L;
            java.util.ArrayList<Object> __iter_2 = ((java.util.ArrayList<Object>)(Object)(specs_opt));
            for (long __iter_i_3 = 0L; __iter_i_3 < ((long)(__iter_2.size())); __iter_i_3 += 1L) {
                _ArgSpec s = ((_ArgSpec)(__iter_2.get((int)(__iter_i_3))));
                java.util.ArrayList<Object> __iter_4 = ((java.util.ArrayList<Object>)(Object)(s.names));
                for (long __iter_i_5 = 0L; __iter_i_5 < ((long)(__iter_4.size())); __iter_i_5 += 1L) {
                    Object n = __iter_4.get((int)(__iter_i_5));
                    by_name.put(n, spec_i);
                }
                spec_i += 1L;
            }
            java.util.HashMap<String, Any> values = new java.util.HashMap<String, Any>();
            java.util.ArrayList<Object> __iter_6 = ((java.util.ArrayList<Object>)(Object)(this._specs));
            for (long __iter_i_7 = 0L; __iter_i_7 < ((long)(__iter_6.size())); __iter_i_7 += 1L) {
                _ArgSpec s = ((_ArgSpec)(__iter_6.get((int)(__iter_i_7))));
                if ((java.util.Objects.equals(s.action, "store_true"))) {
                    values.put(s.dest, ((((s._default) == (null))) ? (PyRuntime.__pytra_truthy(s._default)) : (false)));
                } else {
                    if (((s._default) == (null))) {
                        values.put(s.dest, s._default);
                    } else {
                        values.put(s.dest, null);
                    }
                }
            }
            long pos_i = 0L;
            long i = 0L;
            while (((i) < (((long)(args.size()))))) {
                String tok = String.valueOf(args.get((int)((((i) < 0L) ? (((long)(args.size())) + (i)) : (i)))));
                if (PyRuntime.__pytra_truthy(tok.startswith("-"))) {
                    if ((!(by_name.containsKey(tok)))) {
                        this._fail(null);
                    }
                    _ArgSpec spec = ((_ArgSpec)(specs_opt.get((int)((((((Long)(by_name.get(tok)))) < 0L) ? (((long)(specs_opt.size())) + (((Long)(by_name.get(tok))))) : (((Long)(by_name.get(tok)))))))));
                    if ((java.util.Objects.equals(spec.action, "store_true"))) {
                        values.put(spec.dest, true);
                        i += 1L;
                        continue;
                    }
                    if (((i + 1L) >= (((long)(args.size()))))) {
                        this._fail(null);
                    }
                    String val = String.valueOf(args.get((int)((((i + 1L) < 0L) ? (((long)(args.size())) + (i + 1L)) : (i + 1L)))));
                    if ((((PyRuntime.__pytra_len(spec.choices)) > (0L)) && (!(spec.choices.contains(val))))) {
                        this._fail(null);
                    }
                    values.put(spec.dest, val);
                    i += 2L;
                    continue;
                }
                if (((pos_i) >= (((long)(specs_pos.size()))))) {
                    this._fail(null);
                }
                _ArgSpec spec = ((_ArgSpec)(specs_pos.get((int)((((pos_i) < 0L) ? (((long)(specs_pos.size())) + (pos_i)) : (pos_i))))));
                values.put(spec.dest, tok);
                pos_i += 1L;
                i += 1L;
            }
            if (((pos_i) < (((long)(specs_pos.size()))))) {
                this._fail(null);
            }
            return values;
        }
    }

    public static void main(String[] args) {
    }
}
