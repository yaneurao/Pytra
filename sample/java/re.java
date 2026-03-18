// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/re.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class re {
    private re() {
    }

    public static long S = 1L;


    public static class Match {
        public String _text;
        public java.util.ArrayList<String> _groups;

        public Match(String text, java.util.ArrayList<String> groups) {
            this._text = text;
            this._groups = groups;
        }

        public String group(long idx) {
            if (((idx) == (0L))) {
                return this._text;
            }
            if ((((idx) < (0L)) || ((idx) > (((long)(this._groups.size())))))) {
                throw new RuntimeException(PyRuntime.pyToString(new IndexError("group index out of range")));
            }
            return String.valueOf(this._groups.get((int)((((idx - 1L) < 0L) ? (((long)(this._groups.size())) + (idx - 1L)) : (idx - 1L)))));
        }
    }

    public static String group(Object m, long idx) {
        if (((m) == (null))) {
            return "";
        }
        Match mm = m;
        return mm.group(idx);
    }

    public static String strip_group(Object m, long idx) {
        return group(m, idx).strip();
    }

    public static boolean _is_ident(String s) {
        if ((java.util.Objects.equals(s, ""))) {
            return false;
        }
        String h = PyRuntime.__pytra_str_slice(s, (((0L) < 0L) ? (((long)(s.length())) + (0L)) : (0L)), (((1L) < 0L) ? (((long)(s.length())) + (1L)) : (1L)));
        boolean is_head_alpha = (((("a") <= (h)) && ((h) <= ("z"))) || ((("A") <= (h)) && ((h) <= ("Z"))));
        if ((!(is_head_alpha || (java.util.Objects.equals(h, "_"))))) {
            return false;
        }
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(PyRuntime.__pytra_str_slice(s, (((1L) < 0L) ? (((long)(s.length())) + (1L)) : (1L)), (((((long)(s.length()))) < 0L) ? (((long)(s.length())) + (((long)(s.length())))) : (((long)(s.length())))))));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            String ch = String.valueOf(__iter_0.get((int)(__iter_i_1)));
            boolean is_alpha = (((("a") <= (ch)) && ((ch) <= ("z"))) || ((("A") <= (ch)) && ((ch) <= ("Z"))));
            boolean is_digit = ((("0") <= (ch)) && ((ch) <= ("9")));
            if ((!(is_alpha || is_digit || (java.util.Objects.equals(ch, "_"))))) {
                return false;
            }
        }
        return true;
    }

    public static boolean _is_dotted_ident(String s) {
        if ((java.util.Objects.equals(s, ""))) {
            return false;
        }
        String part = "";
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(s));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            String ch = String.valueOf(__iter_0.get((int)(__iter_i_1)));
            if ((java.util.Objects.equals(ch, "."))) {
                if ((!_is_ident(part))) {
                    return false;
                }
                part = "";
                continue;
            }
            part += ch;
        }
        if ((!_is_ident(part))) {
            return false;
        }
        if ((java.util.Objects.equals(part, ""))) {
            return false;
        }
        return true;
    }

    public static String _strip_suffix_colon(String s) {
        String t = s.rstrip();
        if (((((long)(t.length()))) == (0L))) {
            return "";
        }
        if ((!(java.util.Objects.equals(PyRuntime.__pytra_str_slice(t, ((((-(1L))) < 0L) ? (((long)(t.length())) + ((-(1L)))) : ((-(1L)))), (((((long)(t.length()))) < 0L) ? (((long)(t.length())) + (((long)(t.length())))) : (((long)(t.length()))))), ":")))) {
            return "";
        }
        return PyRuntime.__pytra_str_slice(t, (((0L) < 0L) ? (((long)(t.length())) + (0L)) : (0L)), ((((-(1L))) < 0L) ? (((long)(t.length())) + ((-(1L)))) : ((-(1L)))));
    }

    public static boolean _is_space_ch(String ch) {
        if ((java.util.Objects.equals(ch, " "))) {
            return true;
        }
        if ((java.util.Objects.equals(ch, "\t"))) {
            return true;
        }
        if ((java.util.Objects.equals(ch, "\r"))) {
            return true;
        }
        if ((java.util.Objects.equals(ch, "\n"))) {
            return true;
        }
        return false;
    }

    public static boolean _is_alnum_or_underscore(String ch) {
        boolean is_alpha = (((("a") <= (ch)) && ((ch) <= ("z"))) || ((("A") <= (ch)) && ((ch) <= ("Z"))));
        boolean is_digit = ((("0") <= (ch)) && ((ch) <= ("9")));
        if ((is_alpha || is_digit)) {
            return true;
        }
        return (java.util.Objects.equals(ch, "_"));
    }

    public static long _skip_spaces(String t, long i) {
        while (((i) < (((long)(t.length()))))) {
            if ((!_is_space_ch(PyRuntime.__pytra_str_slice(t, (((i) < 0L) ? (((long)(t.length())) + (i)) : (i)), (((i + 1L) < 0L) ? (((long)(t.length())) + (i + 1L)) : (i + 1L)))))) {
                return i;
            }
            i += 1L;
        }
        return i;
    }

    public static Object match(String pattern, String text, long flags) {
        if ((java.util.Objects.equals(pattern, "^([A-Za-z_][A-Za-z0-9_]*)\\[(.*)\\]$"))) {
            if ((!text.endswith("]"))) {
                return null;
            }
            Object i = text.find("[");
            if (((i) <= (0L))) {
                return null;
            }
            String head = PyRuntime.__pytra_str_slice(text, (((0L) < 0L) ? (((long)(text.length())) + (0L)) : (0L)), (((i) < 0L) ? (((long)(text.length())) + (i)) : (i)));
            if ((!_is_ident(head))) {
                return null;
            }
            return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(head, PyRuntime.__pytra_str_slice(text, (((i + 1L) < 0L) ? (((long)(text.length())) + (i + 1L)) : (i + 1L)), ((((-(1L))) < 0L) ? (((long)(text.length())) + ((-(1L)))) : ((-(1L))))))));
        }
        if ((java.util.Objects.equals(pattern, "^def\\s+([A-Za-z_][A-Za-z0-9_]*)\\((.*)\\)\\s*(?:->\\s*(.+)\\s*)?:\\s*$"))) {
            String t = _strip_suffix_colon(text);
            if ((java.util.Objects.equals(t, ""))) {
                return null;
            }
            long i = 0L;
            if ((!t.startswith("def"))) {
                return null;
            }
            i = 3L;
            if ((((i) >= (((long)(t.length())))) || (!_is_space_ch(PyRuntime.__pytra_str_slice(t, (((i) < 0L) ? (((long)(t.length())) + (i)) : (i)), (((i + 1L) < 0L) ? (((long)(t.length())) + (i + 1L)) : (i + 1L))))))) {
                return null;
            }
            i = _skip_spaces(t, i);
            long j = i;
            while ((((j) < (((long)(t.length())))) && _is_alnum_or_underscore(PyRuntime.__pytra_str_slice(t, (((j) < 0L) ? (((long)(t.length())) + (j)) : (j)), (((j + 1L) < 0L) ? (((long)(t.length())) + (j + 1L)) : (j + 1L)))))) {
                j += 1L;
            }
            String name = PyRuntime.__pytra_str_slice(t, (((i) < 0L) ? (((long)(t.length())) + (i)) : (i)), (((j) < 0L) ? (((long)(t.length())) + (j)) : (j)));
            if ((!_is_ident(name))) {
                return null;
            }
            long k = j;
            k = _skip_spaces(t, k);
            if ((((k) >= (((long)(t.length())))) || (!(java.util.Objects.equals(PyRuntime.__pytra_str_slice(t, (((k) < 0L) ? (((long)(t.length())) + (k)) : (k)), (((k + 1L) < 0L) ? (((long)(t.length())) + (k + 1L)) : (k + 1L))), "("))))) {
                return null;
            }
            long r = t.rfind(")");
            if (((r) <= (k))) {
                return null;
            }
            String args = PyRuntime.__pytra_str_slice(t, (((k + 1L) < 0L) ? (((long)(t.length())) + (k + 1L)) : (k + 1L)), (((r) < 0L) ? (((long)(t.length())) + (r)) : (r)));
            String tail = PyRuntime.__pytra_str_slice(t, (((r + 1L) < 0L) ? (((long)(t.length())) + (r + 1L)) : (r + 1L)), (((((long)(t.length()))) < 0L) ? (((long)(t.length())) + (((long)(t.length())))) : (((long)(t.length()))))).strip();
            if ((java.util.Objects.equals(tail, ""))) {
                return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(name, args, "")));
            }
            if ((!tail.startswith("->"))) {
                return null;
            }
            String ret = PyRuntime.__pytra_str_slice(tail, (((2L) < 0L) ? (((long)(tail.length())) + (2L)) : (2L)), (((((long)(tail.length()))) < 0L) ? (((long)(tail.length())) + (((long)(tail.length())))) : (((long)(tail.length()))))).strip();
            if ((java.util.Objects.equals(ret, ""))) {
                return null;
            }
            return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(name, args, ret)));
        }
        if ((java.util.Objects.equals(pattern, "^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)(?:\\s*=\\s*(.+))?$"))) {
            Object c = text.find(":");
            if (((c) <= (0L))) {
                return null;
            }
            String name = PyRuntime.__pytra_str_slice(text, (((0L) < 0L) ? (((long)(text.length())) + (0L)) : (0L)), (((c) < 0L) ? (((long)(text.length())) + (c)) : (c))).strip();
            if ((!_is_ident(name))) {
                return null;
            }
            String rhs = PyRuntime.__pytra_str_slice(text, (((c + 1L) < 0L) ? (((long)(text.length())) + (c + 1L)) : (c + 1L)), (((((long)(text.length()))) < 0L) ? (((long)(text.length())) + (((long)(text.length())))) : (((long)(text.length())))));
            Object eq = rhs.find("=");
            if (((eq) < (0L))) {
                String ann = rhs.strip();
                if ((java.util.Objects.equals(ann, ""))) {
                    return null;
                }
                return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(name, ann, "")));
            }
            String ann = PyRuntime.__pytra_str_slice(rhs, (((0L) < 0L) ? (((long)(rhs.length())) + (0L)) : (0L)), (((eq) < 0L) ? (((long)(rhs.length())) + (eq)) : (eq))).strip();
            String val = PyRuntime.__pytra_str_slice(rhs, (((eq + 1L) < 0L) ? (((long)(rhs.length())) + (eq + 1L)) : (eq + 1L)), (((((long)(rhs.length()))) < 0L) ? (((long)(rhs.length())) + (((long)(rhs.length())))) : (((long)(rhs.length()))))).strip();
            if (((java.util.Objects.equals(ann, "")) || (java.util.Objects.equals(val, "")))) {
                return null;
            }
            return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(name, ann, val)));
        }
        if ((java.util.Objects.equals(pattern, "^[A-Za-z_][A-Za-z0-9_]*$"))) {
            if (_is_ident(text)) {
                return new Match(text, new java.util.ArrayList<Object>());
            }
            return null;
        }
        if ((java.util.Objects.equals(pattern, "^class\\s+([A-Za-z_][A-Za-z0-9_]*)(?:\\(([A-Za-z_][A-Za-z0-9_]*)\\))?\\s*:\\s*$"))) {
            String t = _strip_suffix_colon(text);
            if ((java.util.Objects.equals(t, ""))) {
                return null;
            }
            if ((!t.startswith("class"))) {
                return null;
            }
            long i = 5L;
            if ((((i) >= (((long)(t.length())))) || (!_is_space_ch(PyRuntime.__pytra_str_slice(t, (((i) < 0L) ? (((long)(t.length())) + (i)) : (i)), (((i + 1L) < 0L) ? (((long)(t.length())) + (i + 1L)) : (i + 1L))))))) {
                return null;
            }
            i = _skip_spaces(t, i);
            long j = i;
            while ((((j) < (((long)(t.length())))) && _is_alnum_or_underscore(PyRuntime.__pytra_str_slice(t, (((j) < 0L) ? (((long)(t.length())) + (j)) : (j)), (((j + 1L) < 0L) ? (((long)(t.length())) + (j + 1L)) : (j + 1L)))))) {
                j += 1L;
            }
            String name = PyRuntime.__pytra_str_slice(t, (((i) < 0L) ? (((long)(t.length())) + (i)) : (i)), (((j) < 0L) ? (((long)(t.length())) + (j)) : (j)));
            if ((!_is_ident(name))) {
                return null;
            }
            String tail = PyRuntime.__pytra_str_slice(t, (((j) < 0L) ? (((long)(t.length())) + (j)) : (j)), (((((long)(t.length()))) < 0L) ? (((long)(t.length())) + (((long)(t.length())))) : (((long)(t.length()))))).strip();
            if ((java.util.Objects.equals(tail, ""))) {
                return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(name, "")));
            }
            if ((!(tail.startswith("(") && tail.endswith(")")))) {
                return null;
            }
            String base = PyRuntime.__pytra_str_slice(tail, (((1L) < 0L) ? (((long)(tail.length())) + (1L)) : (1L)), ((((-(1L))) < 0L) ? (((long)(tail.length())) + ((-(1L)))) : ((-(1L))))).strip();
            if ((!_is_ident(base))) {
                return null;
            }
            return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(name, base)));
        }
        if ((java.util.Objects.equals(pattern, "^(any|all)\\((.+)\\)$"))) {
            if ((text.startswith("any(") && text.endswith(")") && ((((long)(text.length()))) > (5L)))) {
                return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList("any", PyRuntime.__pytra_str_slice(text, (((4L) < 0L) ? (((long)(text.length())) + (4L)) : (4L)), ((((-(1L))) < 0L) ? (((long)(text.length())) + ((-(1L)))) : ((-(1L))))))));
            }
            if ((text.startswith("all(") && text.endswith(")") && ((((long)(text.length()))) > (5L)))) {
                return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList("all", PyRuntime.__pytra_str_slice(text, (((4L) < 0L) ? (((long)(text.length())) + (4L)) : (4L)), ((((-(1L))) < 0L) ? (((long)(text.length())) + ((-(1L)))) : ((-(1L))))))));
            }
            return null;
        }
        if ((java.util.Objects.equals(pattern, "^\\[\\s*([A-Za-z_][A-Za-z0-9_]*)\\s+for\\s+([A-Za-z_][A-Za-z0-9_]*)\\s+in\\s+(.+)\\]$"))) {
            if ((!(text.startswith("[") && text.endswith("]")))) {
                return null;
            }
            String inner = PyRuntime.__pytra_str_slice(text, (((1L) < 0L) ? (((long)(text.length())) + (1L)) : (1L)), ((((-(1L))) < 0L) ? (((long)(text.length())) + ((-(1L)))) : ((-(1L))))).strip();
            String m1 = " for ";
            String m2 = " in ";
            long i = inner.find(m1);
            if (((i) < (0L))) {
                return null;
            }
            String expr = PyRuntime.__pytra_str_slice(inner, (((0L) < 0L) ? (((long)(inner.length())) + (0L)) : (0L)), (((i) < 0L) ? (((long)(inner.length())) + (i)) : (i))).strip();
            String rest = PyRuntime.__pytra_str_slice(inner, (((i + ((long)(m1.length()))) < 0L) ? (((long)(inner.length())) + (i + ((long)(m1.length())))) : (i + ((long)(m1.length())))), (((((long)(inner.length()))) < 0L) ? (((long)(inner.length())) + (((long)(inner.length())))) : (((long)(inner.length())))));
            long j = rest.find(m2);
            if (((j) < (0L))) {
                return null;
            }
            String var = PyRuntime.__pytra_str_slice(rest, (((0L) < 0L) ? (((long)(rest.length())) + (0L)) : (0L)), (((j) < 0L) ? (((long)(rest.length())) + (j)) : (j))).strip();
            String it = PyRuntime.__pytra_str_slice(rest, (((j + ((long)(m2.length()))) < 0L) ? (((long)(rest.length())) + (j + ((long)(m2.length())))) : (j + ((long)(m2.length())))), (((((long)(rest.length()))) < 0L) ? (((long)(rest.length())) + (((long)(rest.length())))) : (((long)(rest.length()))))).strip();
            if (((!_is_ident(expr)) || (!_is_ident(var)) || (java.util.Objects.equals(it, "")))) {
                return null;
            }
            return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(expr, var, it)));
        }
        if ((java.util.Objects.equals(pattern, "^for\\s+(.+)\\s+in\\s+(.+):$"))) {
            String t = _strip_suffix_colon(text);
            if (((java.util.Objects.equals(t, "")) || (!t.startswith("for")))) {
                return null;
            }
            String rest = PyRuntime.__pytra_str_slice(t, (((3L) < 0L) ? (((long)(t.length())) + (3L)) : (3L)), (((((long)(t.length()))) < 0L) ? (((long)(t.length())) + (((long)(t.length())))) : (((long)(t.length()))))).strip();
            long i = rest.find(" in ");
            if (((i) < (0L))) {
                return null;
            }
            String left = PyRuntime.__pytra_str_slice(rest, (((0L) < 0L) ? (((long)(rest.length())) + (0L)) : (0L)), (((i) < 0L) ? (((long)(rest.length())) + (i)) : (i))).strip();
            String right = PyRuntime.__pytra_str_slice(rest, (((i + 4L) < 0L) ? (((long)(rest.length())) + (i + 4L)) : (i + 4L)), (((((long)(rest.length()))) < 0L) ? (((long)(rest.length())) + (((long)(rest.length())))) : (((long)(rest.length()))))).strip();
            if (((java.util.Objects.equals(left, "")) || (java.util.Objects.equals(right, "")))) {
                return null;
            }
            return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(left, right)));
        }
        if ((java.util.Objects.equals(pattern, "^with\\s+(.+)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$"))) {
            String t = _strip_suffix_colon(text);
            if (((java.util.Objects.equals(t, "")) || (!t.startswith("with")))) {
                return null;
            }
            String rest = PyRuntime.__pytra_str_slice(t, (((4L) < 0L) ? (((long)(t.length())) + (4L)) : (4L)), (((((long)(t.length()))) < 0L) ? (((long)(t.length())) + (((long)(t.length())))) : (((long)(t.length()))))).strip();
            long i = rest.rfind(" as ");
            if (((i) < (0L))) {
                return null;
            }
            String expr = PyRuntime.__pytra_str_slice(rest, (((0L) < 0L) ? (((long)(rest.length())) + (0L)) : (0L)), (((i) < 0L) ? (((long)(rest.length())) + (i)) : (i))).strip();
            String name = PyRuntime.__pytra_str_slice(rest, (((i + 4L) < 0L) ? (((long)(rest.length())) + (i + 4L)) : (i + 4L)), (((((long)(rest.length()))) < 0L) ? (((long)(rest.length())) + (((long)(rest.length())))) : (((long)(rest.length()))))).strip();
            if (((java.util.Objects.equals(expr, "")) || (!_is_ident(name)))) {
                return null;
            }
            return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(expr, name)));
        }
        if ((java.util.Objects.equals(pattern, "^except\\s+(.+?)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$"))) {
            String t = _strip_suffix_colon(text);
            if (((java.util.Objects.equals(t, "")) || (!t.startswith("except")))) {
                return null;
            }
            String rest = PyRuntime.__pytra_str_slice(t, (((6L) < 0L) ? (((long)(t.length())) + (6L)) : (6L)), (((((long)(t.length()))) < 0L) ? (((long)(t.length())) + (((long)(t.length())))) : (((long)(t.length()))))).strip();
            long i = rest.rfind(" as ");
            if (((i) < (0L))) {
                return null;
            }
            String exc = PyRuntime.__pytra_str_slice(rest, (((0L) < 0L) ? (((long)(rest.length())) + (0L)) : (0L)), (((i) < 0L) ? (((long)(rest.length())) + (i)) : (i))).strip();
            String name = PyRuntime.__pytra_str_slice(rest, (((i + 4L) < 0L) ? (((long)(rest.length())) + (i + 4L)) : (i + 4L)), (((((long)(rest.length()))) < 0L) ? (((long)(rest.length())) + (((long)(rest.length())))) : (((long)(rest.length()))))).strip();
            if (((java.util.Objects.equals(exc, "")) || (!_is_ident(name)))) {
                return null;
            }
            return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(exc, name)));
        }
        if ((java.util.Objects.equals(pattern, "^except\\s+(.+?)\\s*:\\s*$"))) {
            String t = _strip_suffix_colon(text);
            if (((java.util.Objects.equals(t, "")) || (!t.startswith("except")))) {
                return null;
            }
            String rest = PyRuntime.__pytra_str_slice(t, (((6L) < 0L) ? (((long)(t.length())) + (6L)) : (6L)), (((((long)(t.length()))) < 0L) ? (((long)(t.length())) + (((long)(t.length())))) : (((long)(t.length()))))).strip();
            if ((java.util.Objects.equals(rest, ""))) {
                return null;
            }
            return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(rest)));
        }
        if ((java.util.Objects.equals(pattern, "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*(.+)$"))) {
            Object c = text.find(":");
            if (((c) <= (0L))) {
                return null;
            }
            String target = PyRuntime.__pytra_str_slice(text, (((0L) < 0L) ? (((long)(text.length())) + (0L)) : (0L)), (((c) < 0L) ? (((long)(text.length())) + (c)) : (c))).strip();
            String ann = PyRuntime.__pytra_str_slice(text, (((c + 1L) < 0L) ? (((long)(text.length())) + (c + 1L)) : (c + 1L)), (((((long)(text.length()))) < 0L) ? (((long)(text.length())) + (((long)(text.length())))) : (((long)(text.length()))))).strip();
            if (((java.util.Objects.equals(ann, "")) || (!_is_dotted_ident(target)))) {
                return null;
            }
            return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(target, ann)));
        }
        if ((java.util.Objects.equals(pattern, "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$"))) {
            Object c = text.find(":");
            if (((c) <= (0L))) {
                return null;
            }
            String target = PyRuntime.__pytra_str_slice(text, (((0L) < 0L) ? (((long)(text.length())) + (0L)) : (0L)), (((c) < 0L) ? (((long)(text.length())) + (c)) : (c))).strip();
            String rhs = PyRuntime.__pytra_str_slice(text, (((c + 1L) < 0L) ? (((long)(text.length())) + (c + 1L)) : (c + 1L)), (((((long)(text.length()))) < 0L) ? (((long)(text.length())) + (((long)(text.length())))) : (((long)(text.length())))));
            long eq = rhs.find("=");
            if (((eq) < (0L))) {
                return null;
            }
            String ann = PyRuntime.__pytra_str_slice(rhs, (((0L) < 0L) ? (((long)(rhs.length())) + (0L)) : (0L)), (((eq) < 0L) ? (((long)(rhs.length())) + (eq)) : (eq))).strip();
            String expr = PyRuntime.__pytra_str_slice(rhs, (((eq + 1L) < 0L) ? (((long)(rhs.length())) + (eq + 1L)) : (eq + 1L)), (((((long)(rhs.length()))) < 0L) ? (((long)(rhs.length())) + (((long)(rhs.length())))) : (((long)(rhs.length()))))).strip();
            if (((!_is_dotted_ident(target)) || (java.util.Objects.equals(ann, "")) || (java.util.Objects.equals(expr, "")))) {
                return null;
            }
            return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(target, ann, expr)));
        }
        if ((java.util.Objects.equals(pattern, "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*(\\+=|-=|\\*=|/=|//=|%=|&=|\\|=|\\^=|<<=|>>=)\\s*(.+)$"))) {
            java.util.ArrayList<String> ops = new java.util.ArrayList<String>(java.util.Arrays.asList("<<=", ">>=", "+=", "-=", "*=", "/=", "//=", "%=", "&=", "|=", "^="));
            long op_pos = (-(1L));
            String op_txt = "";
            java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(ops));
            for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
                String op = String.valueOf(__iter_0.get((int)(__iter_i_1)));
                Object p = text.find(op);
                if ((((p) >= (0L)) && (((op_pos) < (0L)) || ((p) < (op_pos))))) {
                    op_pos = p;
                    op_txt = op;
                }
            }
            if (((op_pos) < (0L))) {
                return null;
            }
            String left = PyRuntime.__pytra_str_slice(text, (((0L) < 0L) ? (((long)(text.length())) + (0L)) : (0L)), (((op_pos) < 0L) ? (((long)(text.length())) + (op_pos)) : (op_pos))).strip();
            String right = PyRuntime.__pytra_str_slice(text, (((op_pos + ((long)(op_txt.length()))) < 0L) ? (((long)(text.length())) + (op_pos + ((long)(op_txt.length())))) : (op_pos + ((long)(op_txt.length())))), (((((long)(text.length()))) < 0L) ? (((long)(text.length())) + (((long)(text.length())))) : (((long)(text.length()))))).strip();
            if (((java.util.Objects.equals(right, "")) || (!_is_dotted_ident(left)))) {
                return null;
            }
            return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(left, op_txt, right)));
        }
        if ((java.util.Objects.equals(pattern, "^([A-Za-z_][A-Za-z0-9_]*)\\s*,\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$"))) {
            long eq = text.find("=");
            if (((eq) < (0L))) {
                return null;
            }
            String left = PyRuntime.__pytra_str_slice(text, (((0L) < 0L) ? (((long)(text.length())) + (0L)) : (0L)), (((eq) < 0L) ? (((long)(text.length())) + (eq)) : (eq)));
            String right = PyRuntime.__pytra_str_slice(text, (((eq + 1L) < 0L) ? (((long)(text.length())) + (eq + 1L)) : (eq + 1L)), (((((long)(text.length()))) < 0L) ? (((long)(text.length())) + (((long)(text.length())))) : (((long)(text.length()))))).strip();
            if ((java.util.Objects.equals(right, ""))) {
                return null;
            }
            long c = left.find(",");
            if (((c) < (0L))) {
                return null;
            }
            String a = PyRuntime.__pytra_str_slice(left, (((0L) < 0L) ? (((long)(left.length())) + (0L)) : (0L)), (((c) < 0L) ? (((long)(left.length())) + (c)) : (c))).strip();
            String b = PyRuntime.__pytra_str_slice(left, (((c + 1L) < 0L) ? (((long)(left.length())) + (c + 1L)) : (c + 1L)), (((((long)(left.length()))) < 0L) ? (((long)(left.length())) + (((long)(left.length())))) : (((long)(left.length()))))).strip();
            if (((!_is_ident(a)) || (!_is_ident(b)))) {
                return null;
            }
            return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(a, b, right)));
        }
        if ((java.util.Objects.equals(pattern, "^if\\s+__name__\\s*==\\s*[\\\"']__main__[\\\"']\\s*:\\s*$"))) {
            String t = _strip_suffix_colon(text);
            if ((java.util.Objects.equals(t, ""))) {
                return null;
            }
            String rest = t.strip();
            if ((!rest.startswith("if"))) {
                return null;
            }
            rest = PyRuntime.__pytra_str_slice(rest, (((2L) < 0L) ? (((long)(rest.length())) + (2L)) : (2L)), (((((long)(rest.length()))) < 0L) ? (((long)(rest.length())) + (((long)(rest.length())))) : (((long)(rest.length()))))).strip();
            if ((!rest.startswith("__name__"))) {
                return null;
            }
            rest = PyRuntime.__pytra_str_slice(rest, (((((long)("__name__".length()))) < 0L) ? (((long)(rest.length())) + (((long)("__name__".length())))) : (((long)("__name__".length())))), (((((long)(rest.length()))) < 0L) ? (((long)(rest.length())) + (((long)(rest.length())))) : (((long)(rest.length()))))).strip();
            if ((!rest.startswith("=="))) {
                return null;
            }
            rest = PyRuntime.__pytra_str_slice(rest, (((2L) < 0L) ? (((long)(rest.length())) + (2L)) : (2L)), (((((long)(rest.length()))) < 0L) ? (((long)(rest.length())) + (((long)(rest.length())))) : (((long)(rest.length()))))).strip();
            if (((java.util.Objects.equals(rest, "\"__main__\"")) || (java.util.Objects.equals(rest, "'__main__'")))) {
                return new Match(text, new java.util.ArrayList<Object>());
            }
            return null;
        }
        if ((java.util.Objects.equals(pattern, "^import\\s+(.+)$"))) {
            if ((!text.startswith("import"))) {
                return null;
            }
            if (((((long)(text.length()))) <= (6L))) {
                return null;
            }
            if ((!_is_space_ch(PyRuntime.__pytra_str_slice(text, (((6L) < 0L) ? (((long)(text.length())) + (6L)) : (6L)), (((7L) < 0L) ? (((long)(text.length())) + (7L)) : (7L)))))) {
                return null;
            }
            String rest = PyRuntime.__pytra_str_slice(text, (((7L) < 0L) ? (((long)(text.length())) + (7L)) : (7L)), (((((long)(text.length()))) < 0L) ? (((long)(text.length())) + (((long)(text.length())))) : (((long)(text.length()))))).strip();
            if ((java.util.Objects.equals(rest, ""))) {
                return null;
            }
            return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(rest)));
        }
        if ((java.util.Objects.equals(pattern, "^([A-Za-z_][A-Za-z0-9_\\.]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$"))) {
            java.util.ArrayList<String> parts = text.split(" as ");
            if (((((long)(parts.size()))) == (1L))) {
                String name = String.valueOf(parts.get((int)((((0L) < 0L) ? (((long)(parts.size())) + (0L)) : (0L))))).strip();
                if ((!_is_dotted_ident(name))) {
                    return null;
                }
                return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(name, "")));
            }
            if (((((long)(parts.size()))) == (2L))) {
                String name = String.valueOf(parts.get((int)((((0L) < 0L) ? (((long)(parts.size())) + (0L)) : (0L))))).strip();
                String alias = String.valueOf(parts.get((int)((((1L) < 0L) ? (((long)(parts.size())) + (1L)) : (1L))))).strip();
                if (((!_is_dotted_ident(name)) || (!_is_ident(alias)))) {
                    return null;
                }
                return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(name, alias)));
            }
            return null;
        }
        if ((java.util.Objects.equals(pattern, "^from\\s+([A-Za-z_][A-Za-z0-9_\\.]*)\\s+import\\s+(.+)$"))) {
            if ((!text.startswith("from "))) {
                return null;
            }
            String rest = PyRuntime.__pytra_str_slice(text, (((5L) < 0L) ? (((long)(text.length())) + (5L)) : (5L)), (((((long)(text.length()))) < 0L) ? (((long)(text.length())) + (((long)(text.length())))) : (((long)(text.length())))));
            long i = rest.find(" import ");
            if (((i) < (0L))) {
                return null;
            }
            String mod = PyRuntime.__pytra_str_slice(rest, (((0L) < 0L) ? (((long)(rest.length())) + (0L)) : (0L)), (((i) < 0L) ? (((long)(rest.length())) + (i)) : (i))).strip();
            String sym = PyRuntime.__pytra_str_slice(rest, (((i + 8L) < 0L) ? (((long)(rest.length())) + (i + 8L)) : (i + 8L)), (((((long)(rest.length()))) < 0L) ? (((long)(rest.length())) + (((long)(rest.length())))) : (((long)(rest.length()))))).strip();
            if (((!_is_dotted_ident(mod)) || (java.util.Objects.equals(sym, "")))) {
                return null;
            }
            return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(mod, sym)));
        }
        if ((java.util.Objects.equals(pattern, "^([A-Za-z_][A-Za-z0-9_]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$"))) {
            java.util.ArrayList<String> parts = text.split(" as ");
            if (((((long)(parts.size()))) == (1L))) {
                String name = String.valueOf(parts.get((int)((((0L) < 0L) ? (((long)(parts.size())) + (0L)) : (0L))))).strip();
                if ((!_is_ident(name))) {
                    return null;
                }
                return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(name, "")));
            }
            if (((((long)(parts.size()))) == (2L))) {
                String name = String.valueOf(parts.get((int)((((0L) < 0L) ? (((long)(parts.size())) + (0L)) : (0L))))).strip();
                String alias = String.valueOf(parts.get((int)((((1L) < 0L) ? (((long)(parts.size())) + (1L)) : (1L))))).strip();
                if (((!_is_ident(name)) || (!_is_ident(alias)))) {
                    return null;
                }
                return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(name, alias)));
            }
            return null;
        }
        if ((java.util.Objects.equals(pattern, "^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$"))) {
            Object c = text.find(":");
            if (((c) <= (0L))) {
                return null;
            }
            String name = PyRuntime.__pytra_str_slice(text, (((0L) < 0L) ? (((long)(text.length())) + (0L)) : (0L)), (((c) < 0L) ? (((long)(text.length())) + (c)) : (c))).strip();
            String rhs = PyRuntime.__pytra_str_slice(text, (((c + 1L) < 0L) ? (((long)(text.length())) + (c + 1L)) : (c + 1L)), (((((long)(text.length()))) < 0L) ? (((long)(text.length())) + (((long)(text.length())))) : (((long)(text.length())))));
            long eq = rhs.find("=");
            if (((eq) < (0L))) {
                return null;
            }
            String ann = PyRuntime.__pytra_str_slice(rhs, (((0L) < 0L) ? (((long)(rhs.length())) + (0L)) : (0L)), (((eq) < 0L) ? (((long)(rhs.length())) + (eq)) : (eq))).strip();
            String expr = PyRuntime.__pytra_str_slice(rhs, (((eq + 1L) < 0L) ? (((long)(rhs.length())) + (eq + 1L)) : (eq + 1L)), (((((long)(rhs.length()))) < 0L) ? (((long)(rhs.length())) + (((long)(rhs.length())))) : (((long)(rhs.length()))))).strip();
            if (((!_is_ident(name)) || (java.util.Objects.equals(ann, "")) || (java.util.Objects.equals(expr, "")))) {
                return null;
            }
            return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(name, ann, expr)));
        }
        if ((java.util.Objects.equals(pattern, "^([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$"))) {
            long eq = text.find("=");
            if (((eq) < (0L))) {
                return null;
            }
            String name = PyRuntime.__pytra_str_slice(text, (((0L) < 0L) ? (((long)(text.length())) + (0L)) : (0L)), (((eq) < 0L) ? (((long)(text.length())) + (eq)) : (eq))).strip();
            String expr = PyRuntime.__pytra_str_slice(text, (((eq + 1L) < 0L) ? (((long)(text.length())) + (eq + 1L)) : (eq + 1L)), (((((long)(text.length()))) < 0L) ? (((long)(text.length())) + (((long)(text.length())))) : (((long)(text.length()))))).strip();
            if (((!_is_ident(name)) || (java.util.Objects.equals(expr, "")))) {
                return null;
            }
            return new Match(text, new java.util.ArrayList<String>(java.util.Arrays.asList(name, expr)));
        }
        throw new RuntimeException(PyRuntime.pyToString(null));
    }

    public static String sub(String pattern, String repl, String text, long flags) {
        if ((java.util.Objects.equals(pattern, "\\s+"))) {
            java.util.ArrayList<String> out = new java.util.ArrayList<String>();
            boolean in_ws = false;
            java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(text));
            for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
                String ch = String.valueOf(__iter_0.get((int)(__iter_i_1)));
                if (PyRuntime.__pytra_truthy(ch.isspace())) {
                    if ((!in_ws)) {
                        out.add(repl);
                        in_ws = true;
                    }
                } else {
                    out.add(ch);
                    in_ws = false;
                }
            }
            return "".join(out);
        }
        if ((java.util.Objects.equals(pattern, "\\s+#.*$"))) {
            long i = 0L;
            while (((i) < (((long)(text.length()))))) {
                if (PyRuntime.__pytra_truthy(String.valueOf(String.valueOf(text.charAt((int)((((i) < 0L) ? (((long)(text.length())) + (i)) : (i)))))).isspace())) {
                    long j = i + 1L;
                    while ((((j) < (((long)(text.length())))) && String.valueOf(String.valueOf(text.charAt((int)((((j) < 0L) ? (((long)(text.length())) + (j)) : (j)))))).isspace())) {
                        j += 1L;
                    }
                    if ((((j) < (((long)(text.length())))) && (java.util.Objects.equals(String.valueOf(String.valueOf(text.charAt((int)((((j) < 0L) ? (((long)(text.length())) + (j)) : (j)))))), "#")))) {
                        return PyRuntime.__pytra_str_slice(text, (((0L) < 0L) ? (((long)(text.length())) + (0L)) : (0L)), (((i) < 0L) ? (((long)(text.length())) + (i)) : (i))) + repl;
                    }
                }
                i += 1L;
            }
            return text;
        }
        if ((java.util.Objects.equals(pattern, "[^0-9A-Za-z_]"))) {
            java.util.ArrayList<String> out = new java.util.ArrayList<String>();
            java.util.ArrayList<Object> __iter_2 = ((java.util.ArrayList<Object>)(Object)(text));
            for (long __iter_i_3 = 0L; __iter_i_3 < ((long)(__iter_2.size())); __iter_i_3 += 1L) {
                String ch = String.valueOf(__iter_2.get((int)(__iter_i_3)));
                if ((ch.isalnum() || (java.util.Objects.equals(ch, "_")))) {
                    out.add(ch);
                } else {
                    out.add(repl);
                }
            }
            return "".join(out);
        }
        throw new RuntimeException(PyRuntime.pyToString(null));
    }

    public static void main(String[] args) {
    }
}
