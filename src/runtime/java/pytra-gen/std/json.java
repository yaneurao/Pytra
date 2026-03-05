// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class tmp {
    private tmp() {
    }

    public static String _EMPTY = "";
    public static String _COMMA_NL = ",\n";
    public static String _HEX_DIGITS = "0123456789abcdef";


    public static class _JsonParser {
        public String text;
        public long n;
        public long i;

        public _JsonParser(String text) {
            this.text = text;
            this.n = ((long)(text.length()));
            this.i = 0L;
        }

        public Object parse() {
            this._skip_ws();
            Object out = this._parse_value();
            this._skip_ws();
            if ((this.i != this.n)) {
                throw new RuntimeException(PyRuntime.pyToString("invalid json: trailing characters"));
            }
            return out;
        }

        public void _skip_ws() {
            while (((this.i < this.n) && _is_ws(String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i))))))))) {
                this.i += 1L;
            }
        }

        public Object _parse_value() {
            if ((this.i >= this.n)) {
                throw new RuntimeException(PyRuntime.pyToString("invalid json: unexpected end"));
            }
            String ch = String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i))))));
            if ((java.util.Objects.equals(ch, "{"))) {
                return this._parse_object();
            }
            if ((java.util.Objects.equals(ch, "["))) {
                return this._parse_array();
            }
            if ((java.util.Objects.equals(ch, "\""))) {
                return this._parse_string();
            }
            if (((java.util.Objects.equals(ch, "t")) && (java.util.Objects.equals(PyRuntime.__pytra_str_slice(this.text, (((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i)), (((this.i + 4L) < 0L) ? (((long)(this.text.length())) + (this.i + 4L)) : (this.i + 4L))), "true")))) {
                this.i += 4L;
                return true;
            }
            if (((java.util.Objects.equals(ch, "f")) && (java.util.Objects.equals(PyRuntime.__pytra_str_slice(this.text, (((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i)), (((this.i + 5L) < 0L) ? (((long)(this.text.length())) + (this.i + 5L)) : (this.i + 5L))), "false")))) {
                this.i += 5L;
                return false;
            }
            if (((java.util.Objects.equals(ch, "n")) && (java.util.Objects.equals(PyRuntime.__pytra_str_slice(this.text, (((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i)), (((this.i + 4L) < 0L) ? (((long)(this.text.length())) + (this.i + 4L)) : (this.i + 4L))), "null")))) {
                this.i += 4L;
                return null;
            }
            return this._parse_number();
        }

        public java.util.HashMap<String, Object> _parse_object() {
            java.util.HashMap<String, Object> out = new java.util.HashMap<String, Object>();
            this.i += 1L;
            this._skip_ws();
            if (((this.i < this.n) && (java.util.Objects.equals(String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i)))))), "}")))) {
                this.i += 1L;
                return out;
            }
            while (true) {
                this._skip_ws();
                if (((this.i >= this.n) || (!(java.util.Objects.equals(String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i)))))), "\""))))) {
                    throw new RuntimeException(PyRuntime.pyToString("invalid json object key"));
                }
                String key = this._parse_string();
                this._skip_ws();
                if (((this.i >= this.n) || (!(java.util.Objects.equals(String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i)))))), ":"))))) {
                    throw new RuntimeException(PyRuntime.pyToString("invalid json object: missing ':'"));
                }
                this.i += 1L;
                this._skip_ws();
                out.put(key, this._parse_value());
                this._skip_ws();
                if ((this.i >= this.n)) {
                    throw new RuntimeException(PyRuntime.pyToString("invalid json object: unexpected end"));
                }
                String ch = String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i))))));
                this.i += 1L;
                if ((java.util.Objects.equals(ch, "}"))) {
                    return out;
                }
                if ((!(java.util.Objects.equals(ch, ",")))) {
                    throw new RuntimeException(PyRuntime.pyToString("invalid json object separator"));
                }
            }
            return null;
        }

        public java.util.ArrayList<Object> _parse_array() {
            java.util.ArrayList<Object> out = new java.util.ArrayList<Object>();
            this.i += 1L;
            this._skip_ws();
            if (((this.i < this.n) && (java.util.Objects.equals(String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i)))))), "]")))) {
                this.i += 1L;
                return out;
            }
            while (true) {
                this._skip_ws();
                out.add(this._parse_value());
                this._skip_ws();
                if ((this.i >= this.n)) {
                    throw new RuntimeException(PyRuntime.pyToString("invalid json array: unexpected end"));
                }
                String ch = String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i))))));
                this.i += 1L;
                if ((java.util.Objects.equals(ch, "]"))) {
                    return out;
                }
                if ((!(java.util.Objects.equals(ch, ",")))) {
                    throw new RuntimeException(PyRuntime.pyToString("invalid json array separator"));
                }
            }
            return null;
        }

        public String _parse_string() {
            if ((!(java.util.Objects.equals(String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i)))))), "\"")))) {
                throw new RuntimeException(PyRuntime.pyToString("invalid json string"));
            }
            this.i += 1L;
            java.util.ArrayList<String> out_chars = new java.util.ArrayList<String>();
            while ((this.i < this.n)) {
                String ch = String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i))))));
                this.i += 1L;
                if ((java.util.Objects.equals(ch, "\""))) {
                    return _EMPTY.join(out_chars);
                }
                if ((java.util.Objects.equals(ch, "\\"))) {
                    if ((this.i >= this.n)) {
                        throw new RuntimeException(PyRuntime.pyToString("invalid json string escape"));
                    }
                    String esc = String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i))))));
                    this.i += 1L;
                    if ((java.util.Objects.equals(esc, "\""))) {
                        out_chars.add("\"");
                    } else {
                        if ((java.util.Objects.equals(esc, "\\"))) {
                            out_chars.add("\\");
                        } else {
                            if ((java.util.Objects.equals(esc, "/"))) {
                                out_chars.add("/");
                            } else {
                                if ((java.util.Objects.equals(esc, "b"))) {
                                    out_chars.add("");
                                } else {
                                    if ((java.util.Objects.equals(esc, "f"))) {
                                        out_chars.add("");
                                    } else {
                                        if ((java.util.Objects.equals(esc, "n"))) {
                                            out_chars.add("\n");
                                        } else {
                                            if ((java.util.Objects.equals(esc, "r"))) {
                                                out_chars.add("");
                                            } else {
                                                if ((java.util.Objects.equals(esc, "t"))) {
                                                    out_chars.add("	");
                                                } else {
                                                    if ((java.util.Objects.equals(esc, "u"))) {
                                                        if ((this.i + 4L > this.n)) {
                                                            throw new RuntimeException(PyRuntime.pyToString("invalid json unicode escape"));
                                                        }
                                                        String hx = PyRuntime.__pytra_str_slice(this.text, (((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i)), (((this.i + 4L) < 0L) ? (((long)(this.text.length())) + (this.i + 4L)) : (this.i + 4L)));
                                                        this.i += 4L;
                                                        out_chars.add(chr(_int_from_hex4(hx)));
                                                    } else {
                                                        throw new RuntimeException(PyRuntime.pyToString("invalid json escape"));
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                } else {
                    out_chars.add(ch);
                }
            }
            throw new RuntimeException(PyRuntime.pyToString("unterminated json string"));
        }

        public Object _parse_number() {
            long start = this.i;
            if ((java.util.Objects.equals(String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i)))))), "-"))) {
                this.i += 1L;
            }
            if ((this.i >= this.n)) {
                throw new RuntimeException(PyRuntime.pyToString("invalid json number"));
            }
            if ((java.util.Objects.equals(String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i)))))), "0"))) {
                this.i += 1L;
            } else {
                if ((!_is_digit(String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i))))))))) {
                    throw new RuntimeException(PyRuntime.pyToString("invalid json number"));
                }
                while (((this.i < this.n) && _is_digit(String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i))))))))) {
                    this.i += 1L;
                }
            }
            boolean is_float = false;
            if (((this.i < this.n) && (java.util.Objects.equals(String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i)))))), ".")))) {
                is_float = true;
                this.i += 1L;
                if (((this.i >= this.n) || (!_is_digit(String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i)))))))))) {
                    throw new RuntimeException(PyRuntime.pyToString("invalid json number"));
                }
                while (((this.i < this.n) && _is_digit(String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i))))))))) {
                    this.i += 1L;
                }
            }
            if ((this.i < this.n)) {
                String exp_ch = String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i))))));
                if (((java.util.Objects.equals(exp_ch, "e")) || (java.util.Objects.equals(exp_ch, "E")))) {
                    is_float = true;
                    this.i += 1L;
                    if ((this.i < this.n)) {
                        String sign = String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i))))));
                        if (((java.util.Objects.equals(sign, "+")) || (java.util.Objects.equals(sign, "-")))) {
                            this.i += 1L;
                        }
                    }
                    if (((this.i >= this.n) || (!_is_digit(String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i)))))))))) {
                        throw new RuntimeException(PyRuntime.pyToString("invalid json exponent"));
                    }
                    while (((this.i < this.n) && _is_digit(String.valueOf(String.valueOf(this.text.charAt((int)((((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i))))))))) {
                        this.i += 1L;
                    }
                }
            }
            String token = PyRuntime.__pytra_str_slice(this.text, (((start) < 0L) ? (((long)(this.text.length())) + (start)) : (start)), (((this.i) < 0L) ? (((long)(this.text.length())) + (this.i)) : (this.i)));
            if (is_float) {
                double num_f = _float(token);
                return num_f;
            }
            long num_i = _int(token);
            return num_i;
        }
    }

    public static boolean _is_ws(String ch) {
        return ((java.util.Objects.equals(ch, " ")) || (java.util.Objects.equals(ch, "	")) || (java.util.Objects.equals(ch, "")) || (java.util.Objects.equals(ch, "\n")));
    }

    public static boolean _is_digit(String ch) {
        return ((ch >= "0") && (ch <= "9"));
    }

    public static long _hex_value(String ch) {
        if (((ch >= "0") && (ch <= "9"))) {
            return _int(ch);
        }
        if (((java.util.Objects.equals(ch, "a")) || (java.util.Objects.equals(ch, "A")))) {
            return 10L;
        }
        if (((java.util.Objects.equals(ch, "b")) || (java.util.Objects.equals(ch, "B")))) {
            return 11L;
        }
        if (((java.util.Objects.equals(ch, "c")) || (java.util.Objects.equals(ch, "C")))) {
            return 12L;
        }
        if (((java.util.Objects.equals(ch, "d")) || (java.util.Objects.equals(ch, "D")))) {
            return 13L;
        }
        if (((java.util.Objects.equals(ch, "e")) || (java.util.Objects.equals(ch, "E")))) {
            return 14L;
        }
        if (((java.util.Objects.equals(ch, "f")) || (java.util.Objects.equals(ch, "F")))) {
            return 15L;
        }
        throw new RuntimeException(PyRuntime.pyToString("invalid json unicode escape"));
    }

    public static long _int_from_hex4(String hx) {
        if ((((long)(hx.length())) != 4L)) {
            throw new RuntimeException(PyRuntime.pyToString("invalid json unicode escape"));
        }
        long v0 = _hex_value(PyRuntime.__pytra_str_slice(hx, (((0L) < 0L) ? (((long)(hx.length())) + (0L)) : (0L)), (((1L) < 0L) ? (((long)(hx.length())) + (1L)) : (1L))));
        long v1 = _hex_value(PyRuntime.__pytra_str_slice(hx, (((1L) < 0L) ? (((long)(hx.length())) + (1L)) : (1L)), (((2L) < 0L) ? (((long)(hx.length())) + (2L)) : (2L))));
        long v2 = _hex_value(PyRuntime.__pytra_str_slice(hx, (((2L) < 0L) ? (((long)(hx.length())) + (2L)) : (2L)), (((3L) < 0L) ? (((long)(hx.length())) + (3L)) : (3L))));
        long v3 = _hex_value(PyRuntime.__pytra_str_slice(hx, (((3L) < 0L) ? (((long)(hx.length())) + (3L)) : (3L)), (((4L) < 0L) ? (((long)(hx.length())) + (4L)) : (4L))));
        return v0 * 4096L + v1 * 256L + v2 * 16L + v3;
    }

    public static String _hex4(long code) {
        long v = code % 65536L;
        long d3 = v % 16L;
        v = v / 16L;
        long d2 = v % 16L;
        v = v / 16L;
        long d1 = v % 16L;
        v = v / 16L;
        long d0 = v % 16L;
        String p0 = _HEX_DIGITS;
        String p1 = _HEX_DIGITS;
        String p2 = _HEX_DIGITS;
        String p3 = _HEX_DIGITS;
        return p0 + p1 + p2 + p3;
    }

    public static Object loads(String text) {
        return _JsonParser(text).parse();
    }

    public static String _escape_str(String s, boolean ensure_ascii) {
        java.util.ArrayList<String> out = new java.util.ArrayList<String>(java.util.Arrays.asList("\""));
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(s));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            String ch = String.valueOf(__iter_0.get((int)(__iter_i_1)));
            long code = ord(ch);
            if ((java.util.Objects.equals(ch, "\""))) {
                out.add("\\\"");
            } else {
                if ((java.util.Objects.equals(ch, "\\"))) {
                    out.add("\\\\");
                } else {
                    if ((java.util.Objects.equals(ch, ""))) {
                        out.add("\\b");
                    } else {
                        if ((java.util.Objects.equals(ch, ""))) {
                            out.add("\\f");
                        } else {
                            if ((java.util.Objects.equals(ch, "\n"))) {
                                out.add("\\n");
                            } else {
                                if ((java.util.Objects.equals(ch, ""))) {
                                    out.add("\\r");
                                } else {
                                    if ((java.util.Objects.equals(ch, "	"))) {
                                        out.add("\\t");
                                    } else {
                                        if ((ensure_ascii && (code > 127L))) {
                                            out.add("\\u" + _hex4(code));
                                        } else {
                                            out.add(ch);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        out.add("\"");
        return _EMPTY.join(out);
    }

    public static String _dump_json_list(java.util.ArrayList<Object> values, boolean ensure_ascii, Object indent, String item_sep, String key_sep, long level) {
        if ((((long)(values.size())) == 0L)) {
            return "[]";
        }
        if ((indent == null)) {
            java.util.ArrayList<String> dumped = new java.util.ArrayList<String>();
            java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(values));
            for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
                Object x = __iter_0.get((int)(__iter_i_1));
                String dumped_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level);
                dumped.add(dumped_txt);
            }
            return "[" + item_sep.join(dumped) + "]";
        }
        long indent_i = _int(indent);
        java.util.ArrayList<String> inner = new java.util.ArrayList<String>();
        java.util.ArrayList<Object> __iter_2 = ((java.util.ArrayList<Object>)(Object)(values));
        for (long __iter_i_3 = 0L; __iter_i_3 < ((long)(__iter_2.size())); __iter_i_3 += 1L) {
            Object x = __iter_2.get((int)(__iter_i_3));
            String prefix = " " * (indent_i * (level + 1L));
            String value_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1L);
            inner.add(prefix + value_txt);
        }
        return "[\n" + _COMMA_NL.join(inner) + "\n" + " " * (indent_i * level) + "]";
    }

    public static String _dump_json_dict(java.util.HashMap<String, Object> values, boolean ensure_ascii, Object indent, String item_sep, String key_sep, long level) {
        if ((((long)(values.size())) == 0L)) {
            return "{}";
        }
        if ((indent == null)) {
            java.util.ArrayList<String> parts = new java.util.ArrayList<String>();
            java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(values.items()));
            for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
                java.util.ArrayList<Object> __iter_item_2 = ((java.util.ArrayList<Object>)(Object)(__iter_0.get((int)(__iter_i_1))));
                Object k = __iter_item_2.get(0);
                Object x = __iter_item_2.get(1);
                String k_txt = _escape_str(String.valueOf(k), ensure_ascii);
                String v_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level);
                parts.add(k_txt + key_sep + v_txt);
            }
            return "{" + item_sep.join(parts) + "}";
        }
        long indent_i = _int(indent);
        java.util.ArrayList<String> inner = new java.util.ArrayList<String>();
        java.util.ArrayList<Object> __iter_3 = ((java.util.ArrayList<Object>)(Object)(values.items()));
        for (long __iter_i_4 = 0L; __iter_i_4 < ((long)(__iter_3.size())); __iter_i_4 += 1L) {
            java.util.ArrayList<Object> __iter_item_5 = ((java.util.ArrayList<Object>)(Object)(__iter_3.get((int)(__iter_i_4))));
            Object k = __iter_item_5.get(0);
            Object x = __iter_item_5.get(1);
            String prefix = " " * (indent_i * (level + 1L));
            String k_txt = _escape_str(String.valueOf(k), ensure_ascii);
            String v_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1L);
            inner.add(prefix + k_txt + key_sep + v_txt);
        }
        return "{\n" + _COMMA_NL.join(inner) + "\n" + " " * (indent_i * level) + "}";
    }

    public static String _dump_json_value(Object v, boolean ensure_ascii, Object indent, String item_sep, String key_sep, long level) {
        if ((v == null)) {
            return "null";
        }
        if ((((Object)(v)) instanceof PYTRA_TID_BOOL)) {
            return ((PyRuntime.__pytra_truthy(v)) ? ("true") : ("false"));
        }
        if ((((Object)(v)) instanceof PYTRA_TID_INT)) {
            return String.valueOf(v);
        }
        if ((((Object)(v)) instanceof PYTRA_TID_FLOAT)) {
            return String.valueOf(v);
        }
        if ((((Object)(v)) instanceof PYTRA_TID_STR)) {
            return _escape_str(v, ensure_ascii);
        }
        if ((((Object)(v)) instanceof PYTRA_TID_LIST)) {
            java.util.ArrayList<Object> as_list = list(v);
            return _dump_json_list(as_list, ensure_ascii, indent, item_sep, key_sep, level);
        }
        if ((((Object)(v)) instanceof PYTRA_TID_DICT)) {
            java.util.HashMap<String, Object> as_dict = dict(v);
            return _dump_json_dict(as_dict, ensure_ascii, indent, item_sep, key_sep, level);
        }
        throw new RuntimeException(PyRuntime.pyToString("json.dumps unsupported type"));
    }

    public static String dumps(Any obj, boolean ensure_ascii, Object indent, Object separators) {
        String item_sep = ",";
        String key_sep = (((indent == null)) ? (":") : (": "));
        if ((separators == null)) {
            java.util.ArrayList<Object> __tuple_0 = ((java.util.ArrayList<Object>)(Object)(separators));
            item_sep = __tuple_0.get(0);
            key_sep = __tuple_0.get(1);
        }
        return _dump_json_value(obj, ensure_ascii, indent, item_sep, key_sep, 0L);
    }

    public static void main(String[] args) {
    }
}
