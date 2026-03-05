// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/re.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/gen/std/re.h"


namespace pytra::std::re {

    int64 S;
    
    struct Match : public PyObj {
        list<str> _groups;
        str _text;
        PYTRA_DECLARE_CLASS_TYPE(PYTRA_TID_OBJECT);
        
        Match(const str& text, const list<str>& groups) {
            this->_text = text;
            this->_groups = groups;
        }
        str group(int64 idx = 0) {
            if (idx == 0)
                return this->_text;
            if ((idx < 0) || (idx > py_len(this->_groups)))
                throw IndexError("group index out of range");
            return this->_groups[idx - 1];
        }
    };
    
    str group(const ::std::optional<rc<Match>>& m, int64 idx = 0) {
        /* `Match | None` から group を安全取得する（None は空文字）。 */
        if (py_is_none(m))
            return "";
        rc<Match> mm = (m).value();
        return mm->group(idx);
    }
    
    str strip_group(const ::std::optional<rc<Match>>& m, int64 idx = 0) {
        /* group を取得して前後空白を除去する。 */
        return py_strip(group(m, idx));
    }
    
    bool _is_ident(const str& s) {
        if (s == "")
            return false;
        str h = py_slice(s, 0, 1);
        bool is_head_alpha = ("a" <= h && h <= "z") || ("A" <= h && h <= "Z");
        if (!((is_head_alpha) || (h == "_")))
            return false;
        for (str ch : py_slice(s, 1, py_len(s))) {
            bool is_alpha = ("a" <= ch && ch <= "z") || ("A" <= ch && ch <= "Z");
            bool is_digit = "0" <= ch && ch <= "9";
            if (!((is_alpha) || (is_digit) || (ch == "_")))
                return false;
        }
        return true;
    }
    
    bool _is_dotted_ident(const str& s) {
        if (s == "")
            return false;
        str part = "";
        for (str ch : s) {
            if (ch == ".") {
                if (!(_is_ident(part)))
                    return false;
                part = "";
                continue;
            }
            part += ch;
        }
        if (!(_is_ident(part)))
            return false;
        if (part == "")
            return false;
        return true;
    }
    
    str _strip_suffix_colon(const str& s) {
        str t = py_rstrip(s);
        if (py_len(t) == 0)
            return "";
        if (py_slice(t, -(1), py_len(t)) != ":")
            return "";
        return py_slice(t, 0, -(1));
    }
    
    bool _is_space_ch(const str& ch) {
        if (ch == " ")
            return true;
        if (ch == "\t")
            return true;
        if (ch == "\r")
            return true;
        if (ch == "\n")
            return true;
        return false;
    }
    
    bool _is_alnum_or_underscore(const str& ch) {
        bool is_alpha = ("a" <= ch && ch <= "z") || ("A" <= ch && ch <= "Z");
        bool is_digit = "0" <= ch && ch <= "9";
        if ((is_alpha) || (is_digit))
            return true;
        return ch == "_";
    }
    
    int64 _skip_spaces(const str& t, int64 i) {
        while (i < py_len(t)) {
            if (!(_is_space_ch(py_slice(t, i, i + 1))))
                return i;
            i++;
        }
        return i;
    }
    
    ::std::optional<rc<Match>> match(const str& pattern, const str& text, int64 flags = 0) {
        // ^([A-Za-z_][A-Za-z0-9_]*)\[(.*)\]$
        if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\[(.*)\\]$") {
            if (!(py_endswith(text, "]")))
                return ::std::nullopt;
            auto i = py_find(text, "[");
            if (i <= 0)
                return ::std::nullopt;
            str head = py_slice(text, 0, i);
            if (!(_is_ident(head)))
                return ::std::nullopt;
            return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{head, py_slice(text, i + 1, -(1))}));
        }
        if (pattern == "^def\\s+([A-Za-z_][A-Za-z0-9_]*)\\((.*)\\)\\s*(?:->\\s*(.+)\\s*)?:\\s*$") {
            str t = _strip_suffix_colon(text);
            if (t == "")
                return ::std::nullopt;
            int64 i = 0;
            if (!(py_startswith(t, "def")))
                return ::std::nullopt;
            i = 3;
            if ((i >= py_len(t)) || (!(_is_space_ch(py_slice(t, i, i + 1)))))
                return ::std::nullopt;
            i = _skip_spaces(t, i);
            int64 j = i;
            while ((j < py_len(t)) && (_is_alnum_or_underscore(py_slice(t, j, j + 1)))) {
                j++;
            }
            str name = py_slice(t, i, j);
            if (!(_is_ident(name)))
                return ::std::nullopt;
            int64 k = j;
            k = _skip_spaces(t, k);
            if ((k >= py_len(t)) || (py_slice(t, k, k + 1) != "("))
                return ::std::nullopt;
            int64 r = py_to<int64>(py_rfind(t, ")"));
            if (r <= k)
                return ::std::nullopt;
            str args = py_slice(t, k + 1, r);
            str tail = py_strip(py_slice(t, r + 1, py_len(t)));
            if (tail == "")
                return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{name, args, ""}));
            if (!(py_startswith(tail, "->")))
                return ::std::nullopt;
            str ret = py_strip(py_slice(tail, 2, py_len(tail)));
            if (ret == "")
                return ::std::nullopt;
            return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{name, args, ret}));
        }
        if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)(?:\\s*=\\s*(.+))?$") {
            auto c = py_find(text, ":");
            if (c <= 0)
                return ::std::nullopt;
            str name = py_strip(py_slice(text, 0, c));
            if (!(_is_ident(name)))
                return ::std::nullopt;
            str rhs = py_slice(text, c + 1, py_len(text));
            auto eq = py_find(rhs, "=");
            if (eq < 0) {
                str ann = py_strip(rhs);
                if (ann == "")
                    return ::std::nullopt;
                return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{name, ann, ""}));
            }
            str ann = py_strip(py_slice(rhs, 0, eq));
            str val = py_strip(py_slice(rhs, eq + 1, py_len(rhs)));
            if ((ann == "") || (val == ""))
                return ::std::nullopt;
            return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{name, ann, val}));
        }
        if (pattern == "^[A-Za-z_][A-Za-z0-9_]*$") {
            if (_is_ident(text))
                return ::rc_new<Match>(text, py_to_str_list_from_object(make_object(list<object>{})));
            return ::std::nullopt;
        }
        if (pattern == "^class\\s+([A-Za-z_][A-Za-z0-9_]*)(?:\\(([A-Za-z_][A-Za-z0-9_]*)\\))?\\s*:\\s*$") {
            str t = _strip_suffix_colon(text);
            if (t == "")
                return ::std::nullopt;
            if (!(py_startswith(t, "class")))
                return ::std::nullopt;
            int64 i = 5;
            if ((i >= py_len(t)) || (!(_is_space_ch(py_slice(t, i, i + 1)))))
                return ::std::nullopt;
            i = _skip_spaces(t, i);
            int64 j = i;
            while ((j < py_len(t)) && (_is_alnum_or_underscore(py_slice(t, j, j + 1)))) {
                j++;
            }
            str name = py_slice(t, i, j);
            if (!(_is_ident(name)))
                return ::std::nullopt;
            str tail = py_strip(py_slice(t, j, py_len(t)));
            if (tail == "")
                return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{name, ""}));
            if (!((py_startswith(tail, "(")) && (py_endswith(tail, ")"))))
                return ::std::nullopt;
            str base = py_strip(py_slice(tail, 1, -(1)));
            if (!(_is_ident(base)))
                return ::std::nullopt;
            return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{name, base}));
        }
        if (pattern == "^(any|all)\\((.+)\\)$") {
            if ((py_startswith(text, "any(")) && (py_endswith(text, ")")) && (py_len(text) > 5))
                return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{"any", py_slice(text, 4, -(1))}));
            if ((py_startswith(text, "all(")) && (py_endswith(text, ")")) && (py_len(text) > 5))
                return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{"all", py_slice(text, 4, -(1))}));
            return ::std::nullopt;
        }
        if (pattern == "^\\[\\s*([A-Za-z_][A-Za-z0-9_]*)\\s+for\\s+([A-Za-z_][A-Za-z0-9_]*)\\s+in\\s+(.+)\\]$") {
            if (!((py_startswith(text, "[")) && (py_endswith(text, "]"))))
                return ::std::nullopt;
            str inner = py_strip(py_slice(text, 1, -(1)));
            str m1 = " for ";
            str m2 = " in ";
            int64 i = py_to<int64>(py_find(inner, m1));
            if (i < 0)
                return ::std::nullopt;
            str expr = py_strip(py_slice(inner, 0, i));
            str rest = py_slice(inner, i + py_len(m1), py_len(inner));
            int64 j = py_to<int64>(py_find(rest, m2));
            if (j < 0)
                return ::std::nullopt;
            str var = py_strip(py_slice(rest, 0, j));
            str it = py_strip(py_slice(rest, j + py_len(m2), py_len(rest)));
            if ((!(_is_ident(expr))) || (!(_is_ident(var))) || (it == ""))
                return ::std::nullopt;
            return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{expr, var, it}));
        }
        if (pattern == "^for\\s+(.+)\\s+in\\s+(.+):$") {
            str t = _strip_suffix_colon(text);
            if ((t == "") || (!(py_startswith(t, "for"))))
                return ::std::nullopt;
            str rest = py_strip(py_slice(t, 3, py_len(t)));
            int64 i = py_to<int64>(py_find(rest, " in "));
            if (i < 0)
                return ::std::nullopt;
            str left = py_strip(py_slice(rest, 0, i));
            str right = py_strip(py_slice(rest, i + 4, py_len(rest)));
            if ((left == "") || (right == ""))
                return ::std::nullopt;
            return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{left, right}));
        }
        if (pattern == "^with\\s+(.+)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$") {
            str t = _strip_suffix_colon(text);
            if ((t == "") || (!(py_startswith(t, "with"))))
                return ::std::nullopt;
            str rest = py_strip(py_slice(t, 4, py_len(t)));
            int64 i = py_to<int64>(py_rfind(rest, " as "));
            if (i < 0)
                return ::std::nullopt;
            str expr = py_strip(py_slice(rest, 0, i));
            str name = py_strip(py_slice(rest, i + 4, py_len(rest)));
            if ((expr == "") || (!(_is_ident(name))))
                return ::std::nullopt;
            return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{expr, name}));
        }
        if (pattern == "^except\\s+(.+?)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$") {
            str t = _strip_suffix_colon(text);
            if ((t == "") || (!(py_startswith(t, "except"))))
                return ::std::nullopt;
            str rest = py_strip(py_slice(t, 6, py_len(t)));
            int64 i = py_to<int64>(py_rfind(rest, " as "));
            if (i < 0)
                return ::std::nullopt;
            str exc = py_strip(py_slice(rest, 0, i));
            str name = py_strip(py_slice(rest, i + 4, py_len(rest)));
            if ((exc == "") || (!(_is_ident(name))))
                return ::std::nullopt;
            return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{exc, name}));
        }
        if (pattern == "^except\\s+(.+?)\\s*:\\s*$") {
            str t = _strip_suffix_colon(text);
            if ((t == "") || (!(py_startswith(t, "except"))))
                return ::std::nullopt;
            str rest = py_strip(py_slice(t, 6, py_len(t)));
            if (rest == "")
                return ::std::nullopt;
            return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{rest}));
        }
        if (pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*(.+)$") {
            auto c = py_find(text, ":");
            if (c <= 0)
                return ::std::nullopt;
            str target = py_strip(py_slice(text, 0, c));
            str ann = py_strip(py_slice(text, c + 1, py_len(text)));
            if ((ann == "") || (!(_is_dotted_ident(target))))
                return ::std::nullopt;
            return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{target, ann}));
        }
        if (pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$") {
            auto c = py_find(text, ":");
            if (c <= 0)
                return ::std::nullopt;
            str target = py_strip(py_slice(text, 0, c));
            str rhs = py_slice(text, c + 1, py_len(text));
            int64 eq = py_to<int64>(py_find(rhs, "="));
            if (eq < 0)
                return ::std::nullopt;
            str ann = py_strip(py_slice(rhs, 0, eq));
            str expr = py_strip(py_slice(rhs, eq + 1, py_len(rhs)));
            if ((!(_is_dotted_ident(target))) || (ann == "") || (expr == ""))
                return ::std::nullopt;
            return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{target, ann, expr}));
        }
        if (pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*(\\+=|-=|\\*=|/=|//=|%=|&=|\\|=|\\^=|<<=|>>=)\\s*(.+)$") {
            list<str> ops = list<str>{"<<=", ">>=", "+=", "-=", "*=", "/=", "//=", "%=", "&=", "|=", "^="};
            int64 op_pos = -(1);
            str op_txt = "";
            for (object __itobj_1 : py_dyn_range(ops)) {
                str op = py_to_string(__itobj_1);
                auto p = py_find(text, op);
                if ((p >= 0) && ((op_pos < 0) || (p < op_pos))) {
                    op_pos = py_to<int64>(p);
                    op_txt = op;
                }
            }
            if (op_pos < 0)
                return ::std::nullopt;
            str left = py_strip(py_slice(text, 0, op_pos));
            str right = py_strip(py_slice(text, op_pos + py_len(op_txt), py_len(text)));
            if ((right == "") || (!(_is_dotted_ident(left))))
                return ::std::nullopt;
            return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{left, op_txt, right}));
        }
        if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*,\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$") {
            int64 eq = py_to<int64>(py_find(text, "="));
            if (eq < 0)
                return ::std::nullopt;
            str left = py_slice(text, 0, eq);
            str right = py_strip(py_slice(text, eq + 1, py_len(text)));
            if (right == "")
                return ::std::nullopt;
            int64 c = py_to<int64>(py_find(left, ","));
            if (c < 0)
                return ::std::nullopt;
            str a = py_strip(py_slice(left, 0, c));
            str b = py_strip(py_slice(left, c + 1, py_len(left)));
            if ((!(_is_ident(a))) || (!(_is_ident(b))))
                return ::std::nullopt;
            return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{a, b, right}));
        }
        if (pattern == "^if\\s+__name__\\s*==\\s*[\\\"']__main__[\\\"']\\s*:\\s*$") {
            str t = _strip_suffix_colon(text);
            if (t == "")
                return ::std::nullopt;
            str rest = py_strip(t);
            if (!(py_startswith(rest, "if")))
                return ::std::nullopt;
            rest = py_strip(py_slice(rest, 2, py_len(rest)));
            if (!(py_startswith(rest, "__name__")))
                return ::std::nullopt;
            rest = py_strip(py_slice(rest, py_len("__name__"), py_len(rest)));
            if (!(py_startswith(rest, "==")))
                return ::std::nullopt;
            rest = py_strip(py_slice(rest, 2, py_len(rest)));
            if (py_contains(set<str>{"\"__main__\"", "'__main__'"}, rest))
                return ::rc_new<Match>(text, py_to_str_list_from_object(make_object(list<object>{})));
            return ::std::nullopt;
        }
        if (pattern == "^import\\s+(.+)$") {
            if (!(py_startswith(text, "import")))
                return ::std::nullopt;
            if (py_len(text) <= 6)
                return ::std::nullopt;
            if (!(_is_space_ch(py_slice(text, 6, 7))))
                return ::std::nullopt;
            str rest = py_strip(py_slice(text, 7, py_len(text)));
            if (rest == "")
                return ::std::nullopt;
            return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{rest}));
        }
        if (pattern == "^([A-Za-z_][A-Za-z0-9_\\.]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$") {
            list<str> parts = text.split(" as ");
            if (py_len(parts) == 1) {
                str name = py_strip(parts[0]);
                if (!(_is_dotted_ident(name)))
                    return ::std::nullopt;
                return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{name, ""}));
            }
            if (py_len(parts) == 2) {
                str name = py_strip(parts[0]);
                str alias = py_strip(parts[1]);
                if ((!(_is_dotted_ident(name))) || (!(_is_ident(alias))))
                    return ::std::nullopt;
                return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{name, alias}));
            }
            return ::std::nullopt;
        }
        if (pattern == "^from\\s+([A-Za-z_][A-Za-z0-9_\\.]*)\\s+import\\s+(.+)$") {
            if (!(py_startswith(text, "from ")))
                return ::std::nullopt;
            str rest = py_slice(text, 5, py_len(text));
            int64 i = py_to<int64>(py_find(rest, " import "));
            if (i < 0)
                return ::std::nullopt;
            str mod = py_strip(py_slice(rest, 0, i));
            str sym = py_strip(py_slice(rest, i + 8, py_len(rest)));
            if ((!(_is_dotted_ident(mod))) || (sym == ""))
                return ::std::nullopt;
            return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{mod, sym}));
        }
        if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$") {
            list<str> parts = text.split(" as ");
            if (py_len(parts) == 1) {
                str name = py_strip(parts[0]);
                if (!(_is_ident(name)))
                    return ::std::nullopt;
                return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{name, ""}));
            }
            if (py_len(parts) == 2) {
                str name = py_strip(parts[0]);
                str alias = py_strip(parts[1]);
                if ((!(_is_ident(name))) || (!(_is_ident(alias))))
                    return ::std::nullopt;
                return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{name, alias}));
            }
            return ::std::nullopt;
        }
        if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$") {
            int64 c = py_find(text, ":");
            if (c <= 0)
                return ::std::nullopt;
            str name = py_strip(py_slice(text, 0, c));
            str rhs = py_slice(text, c + 1, py_len(text));
            int64 eq = py_to<int64>(py_find(rhs, "="));
            if (eq < 0)
                return ::std::nullopt;
            str ann = py_strip(py_slice(rhs, 0, eq));
            str expr = py_strip(py_slice(rhs, eq + 1, py_len(rhs)));
            if ((!(_is_ident(name))) || (ann == "") || (expr == ""))
                return ::std::nullopt;
            return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{name, ann, expr}));
        }
        if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$") {
            int64 eq = py_to<int64>(py_find(text, "="));
            if (eq < 0)
                return ::std::nullopt;
            str name = py_strip(py_slice(text, 0, eq));
            str expr = py_strip(py_slice(text, eq + 1, py_len(text)));
            if ((!(_is_ident(name))) || (expr == ""))
                return ::std::nullopt;
            return ::rc_new<Match>(text, py_to_str_list_from_object(list<str>{name, expr}));
        }
        throw ValueError("unsupported regex pattern in pytra.std.re: " + pattern);
    }
    
    str sub(const str& pattern, const str& repl, const str& text, int64 flags = 0) {
        if (pattern == "\\s+") {
            list<str> out = {};
            bool in_ws = false;
            for (str ch : text) {
                if (ch.isspace()) {
                    if (!(in_ws)) {
                        out.append(repl);
                        in_ws = true;
                    }
                } else {
                    out.append(ch);
                    in_ws = false;
                }
            }
            return str("").join(out);
        }
        if (pattern == "\\s+#.*$") {
            int64 i = 0;
            while (i < py_len(text)) {
                if (text[i].isspace()) {
                    int64 j = i + 1;
                    while ((j < py_len(text)) && (text[j].isspace())) {
                        j++;
                    }
                    if ((j < py_len(text)) && (text[j] == "#"))
                        return py_slice(text, 0, i) + repl;
                }
                i++;
            }
            return text;
        }
        if (pattern == "[^0-9A-Za-z_]") {
            list<str> out = {};
            for (str ch : text) {
                if ((ch.isalnum()) || (ch == "_"))
                    out.append(ch);
                else
                    out.append(repl);
            }
            return str("").join(out);
        }
        throw ValueError("unsupported regex sub pattern in pytra.std.re: " + pattern);
    }
    
    static void __pytra_module_init() {
        static bool __initialized = false;
        if (__initialized) return;
        __initialized = true;
        /* Minimal pure-Python regex subset used by Pytra selfhost path. */
        S = 1;
    }
    
    namespace {
        struct __pytra_module_initializer {
            __pytra_module_initializer() { __pytra_module_init(); }
        };
        static const __pytra_module_initializer __pytra_module_initializer_instance{};
    }  // namespace
    
}  // namespace pytra::std::re
