// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/re.py
// generated-by: tools/gen_runtime_from_manifest.py

using System;
using System.Collections.Generic;
using System.Linq;
using Any = System.Object;
using int64 = System.Int64;
using float64 = System.Double;
using str = System.String;
using Pytra.CsModule;

public class Match
{
    public static readonly long PYTRA_TYPE_ID = Pytra.CsModule.py_runtime.py_register_class_type(Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT);
    public string _text;
    public System.Collections.Generic.List<string> _groups;
    
    public Match(string text, System.Collections.Generic.List<string> groups)
    {
        this._text = text;
        this._groups = groups;
    }
    
    public string group(long idx = 0)
    {
        if ((idx) == (0)) {
            return this._text;
        }
        if (((idx) < (0)) || ((idx) > ((this._groups).Count))) {
            throw new System.Exception("group index out of range");
        }
        return Pytra.CsModule.py_runtime.py_get(this._groups, idx - 1);
    }
}

public static class Program
{
    public static string group(Match m, long idx = 0)
    {
        if ((m) == (null)) {
            return "";
        }
        Match mm = m;
        return mm.group(idx);
    }
    
    public static string strip_group(Match m, long idx = 0)
    {
        return group(m, idx).Trim();
    }
    
    public static bool _is_ident(string s)
    {
        if ((s) == ("")) {
            return false;
        }
        string h = Pytra.CsModule.py_runtime.py_slice(s, System.Convert.ToInt64(0), System.Convert.ToInt64(1));
        bool is_head_alpha = ((("a") <= (h) && (h) <= ("z")) || (("A") <= (h) && (h) <= ("Z")));
        if (!(((is_head_alpha) || ((h) == ("_"))))) {
            return false;
        }
        foreach (var ch in (Pytra.CsModule.py_runtime.py_slice(s, System.Convert.ToInt64(1), null)).Select(__ch => __ch.ToString())) {
            bool is_alpha = ((("a") <= (ch) && (ch) <= ("z")) || (("A") <= (ch) && (ch) <= ("Z")));
            bool is_digit = ("0") <= (ch) && (ch) <= ("9");
            if (!(((is_alpha) || (is_digit) || ((ch) == ("_"))))) {
                return false;
            }
        }
        return true;
    }
    
    public static bool _is_dotted_ident(string s)
    {
        if ((s) == ("")) {
            return false;
        }
        string part = "";
        foreach (var ch in (s).Select(__ch => __ch.ToString())) {
            if ((ch) == (".")) {
                if (!_is_ident(part)) {
                    return false;
                }
                part = "";
                continue;
            }
            part += ch;
        }
        if (!_is_ident(part)) {
            return false;
        }
        if ((part) == ("")) {
            return false;
        }
        return true;
    }
    
    public static string _strip_suffix_colon(string s)
    {
        string t = s.rstrip();
        if (((t).Length) == (0)) {
            return "";
        }
        if ((Pytra.CsModule.py_runtime.py_slice(t, System.Convert.ToInt64(-1), null)) != (":")) {
            return "";
        }
        return Pytra.CsModule.py_runtime.py_slice(t, null, System.Convert.ToInt64(-1));
    }
    
    public static bool _is_space_ch(string ch)
    {
        if ((ch) == (" ")) {
            return true;
        }
        if ((ch) == ("\t")) {
            return true;
        }
        if ((ch) == ("\r")) {
            return true;
        }
        if ((ch) == ("\n")) {
            return true;
        }
        return false;
    }
    
    public static bool _is_alnum_or_underscore(string ch)
    {
        bool is_alpha = ((("a") <= (ch) && (ch) <= ("z")) || (("A") <= (ch) && (ch) <= ("Z")));
        bool is_digit = ("0") <= (ch) && (ch) <= ("9");
        if ((is_alpha) || (is_digit)) {
            return true;
        }
        return (ch) == ("_");
    }
    
    public static long _skip_spaces(string t, long i)
    {
        while ((i) < ((t).Length)) {
            if (!_is_space_ch(Pytra.CsModule.py_runtime.py_slice(t, System.Convert.ToInt64(i), System.Convert.ToInt64(i + 1)))) {
                return i;
            }
            i += 1;
        }
        return i;
    }
    
    public static Match match(string pattern, string text, long flags = 0)
    {
        // ^([A-Za-z_][A-Za-z0-9_]*)\[(.*)\]$
        if ((pattern) == ("^([A-Za-z_][A-Za-z0-9_]*)\\[(.*)\\]$")) {
            if (!text.EndsWith("]")) {
                return null;
            }
            var i = text.IndexOf("[");
            if ((i) <= (0)) {
                return null;
            }
            string head = Pytra.CsModule.py_runtime.py_slice(text, null, System.Convert.ToInt64(i));
            if (!_is_ident(head)) {
                return null;
            }
            return new Match(text, new System.Collections.Generic.List<string> { head, Pytra.CsModule.py_runtime.py_slice(text, System.Convert.ToInt64(i + 1), System.Convert.ToInt64(-1)) });
        }
        if ((pattern) == ("^def\\s+([A-Za-z_][A-Za-z0-9_]*)\\((.*)\\)\\s*(?:->\\s*(.+)\\s*)?:\\s*$")) {
            string t = _strip_suffix_colon(text);
            if ((t) == ("")) {
                return null;
            }
            long i = 0;
            if (!t.StartsWith("def")) {
                return null;
            }
            i = 3;
            if (((i) >= ((t).Length)) || (!_is_space_ch(Pytra.CsModule.py_runtime.py_slice(t, System.Convert.ToInt64(i), System.Convert.ToInt64(i + 1))))) {
                return null;
            }
            i = _skip_spaces(t, i);
            long j = i;
            while (((j) < ((t).Length)) && (_is_alnum_or_underscore(Pytra.CsModule.py_runtime.py_slice(t, System.Convert.ToInt64(j), System.Convert.ToInt64(j + 1))))) {
                j += 1;
            }
            string name = Pytra.CsModule.py_runtime.py_slice(t, System.Convert.ToInt64(i), System.Convert.ToInt64(j));
            if (!_is_ident(name)) {
                return null;
            }
            long k = j;
            k = _skip_spaces(t, k);
            if (((k) >= ((t).Length)) || ((Pytra.CsModule.py_runtime.py_slice(t, System.Convert.ToInt64(k), System.Convert.ToInt64(k + 1))) != ("("))) {
                return null;
            }
            long r = System.Convert.ToInt64(t.LastIndexOf(")"));
            if ((r) <= (k)) {
                return null;
            }
            string args = Pytra.CsModule.py_runtime.py_slice(t, System.Convert.ToInt64(k + 1), System.Convert.ToInt64(r));
            string tail = Pytra.CsModule.py_runtime.py_slice(t, System.Convert.ToInt64(r + 1), null).Trim();
            if ((tail) == ("")) {
                return new Match(text, new System.Collections.Generic.List<string> { name, args, "" });
            }
            if (!tail.StartsWith("->")) {
                return null;
            }
            string ret = Pytra.CsModule.py_runtime.py_slice(tail, System.Convert.ToInt64(2), null).Trim();
            if ((ret) == ("")) {
                return null;
            }
            return new Match(text, new System.Collections.Generic.List<string> { name, args, ret });
        }
        if ((pattern) == ("^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)(?:\\s*=\\s*(.+))?$")) {
            var c = text.IndexOf(":");
            if ((c) <= (0)) {
                return null;
            }
            string name = Pytra.CsModule.py_runtime.py_slice(text, null, System.Convert.ToInt64(c)).Trim();
            if (!_is_ident(name)) {
                return null;
            }
            string rhs = Pytra.CsModule.py_runtime.py_slice(text, System.Convert.ToInt64(c + 1), null);
            var eq = rhs.IndexOf("=");
            if ((eq) < (0)) {
                string ann = rhs.Trim();
                if ((ann) == ("")) {
                    return null;
                }
                return new Match(text, new System.Collections.Generic.List<string> { name, ann, "" });
            }
            string ann = Pytra.CsModule.py_runtime.py_slice(rhs, null, System.Convert.ToInt64(eq)).Trim();
            string val = Pytra.CsModule.py_runtime.py_slice(rhs, System.Convert.ToInt64(eq + 1), null).Trim();
            if (((ann) == ("")) || ((val) == (""))) {
                return null;
            }
            return new Match(text, new System.Collections.Generic.List<string> { name, ann, val });
        }
        if ((pattern) == ("^[A-Za-z_][A-Za-z0-9_]*$")) {
            if (_is_ident(text)) {
                return new Match(text, new System.Collections.Generic.List<object>());
            }
            return null;
        }
        if ((pattern) == ("^class\\s+([A-Za-z_][A-Za-z0-9_]*)(?:\\(([A-Za-z_][A-Za-z0-9_]*)\\))?\\s*:\\s*$")) {
            string t = _strip_suffix_colon(text);
            if ((t) == ("")) {
                return null;
            }
            if (!t.StartsWith("class")) {
                return null;
            }
            long i = 5;
            if (((i) >= ((t).Length)) || (!_is_space_ch(Pytra.CsModule.py_runtime.py_slice(t, System.Convert.ToInt64(i), System.Convert.ToInt64(i + 1))))) {
                return null;
            }
            i = _skip_spaces(t, i);
            long j = i;
            while (((j) < ((t).Length)) && (_is_alnum_or_underscore(Pytra.CsModule.py_runtime.py_slice(t, System.Convert.ToInt64(j), System.Convert.ToInt64(j + 1))))) {
                j += 1;
            }
            string name = Pytra.CsModule.py_runtime.py_slice(t, System.Convert.ToInt64(i), System.Convert.ToInt64(j));
            if (!_is_ident(name)) {
                return null;
            }
            string tail = Pytra.CsModule.py_runtime.py_slice(t, System.Convert.ToInt64(j), null).Trim();
            if ((tail) == ("")) {
                return new Match(text, new System.Collections.Generic.List<string> { name, "" });
            }
            if (!(((tail.StartsWith("(")) && (tail.EndsWith(")"))))) {
                return null;
            }
            string py_base = Pytra.CsModule.py_runtime.py_slice(tail, System.Convert.ToInt64(1), System.Convert.ToInt64(-1)).Trim();
            if (!_is_ident(py_base)) {
                return null;
            }
            return new Match(text, new System.Collections.Generic.List<string> { name, py_base });
        }
        if ((pattern) == ("^(any|all)\\((.+)\\)$")) {
            if ((text.StartsWith("any(")) && (text.EndsWith(")")) && (((text).Length) > (5))) {
                return new Match(text, new System.Collections.Generic.List<string> { "any", Pytra.CsModule.py_runtime.py_slice(text, System.Convert.ToInt64(4), System.Convert.ToInt64(-1)) });
            }
            if ((text.StartsWith("all(")) && (text.EndsWith(")")) && (((text).Length) > (5))) {
                return new Match(text, new System.Collections.Generic.List<string> { "all", Pytra.CsModule.py_runtime.py_slice(text, System.Convert.ToInt64(4), System.Convert.ToInt64(-1)) });
            }
            return null;
        }
        if ((pattern) == ("^\\[\\s*([A-Za-z_][A-Za-z0-9_]*)\\s+for\\s+([A-Za-z_][A-Za-z0-9_]*)\\s+in\\s+(.+)\\]$")) {
            if (!(((text.StartsWith("[")) && (text.EndsWith("]"))))) {
                return null;
            }
            string inner = Pytra.CsModule.py_runtime.py_slice(text, System.Convert.ToInt64(1), System.Convert.ToInt64(-1)).Trim();
            string m1 = " for ";
            string m2 = " in ";
            long i = System.Convert.ToInt64(inner.IndexOf(m1));
            if ((i) < (0)) {
                return null;
            }
            string expr = Pytra.CsModule.py_runtime.py_slice(inner, null, System.Convert.ToInt64(i)).Trim();
            string rest = Pytra.CsModule.py_runtime.py_slice(inner, System.Convert.ToInt64(i + (m1).Length), null);
            long j = System.Convert.ToInt64(rest.IndexOf(m2));
            if ((j) < (0)) {
                return null;
            }
            string py_var = Pytra.CsModule.py_runtime.py_slice(rest, null, System.Convert.ToInt64(j)).Trim();
            string it = Pytra.CsModule.py_runtime.py_slice(rest, System.Convert.ToInt64(j + (m2).Length), null).Trim();
            if ((!_is_ident(expr)) || (!_is_ident(py_var)) || ((it) == (""))) {
                return null;
            }
            return new Match(text, new System.Collections.Generic.List<string> { expr, py_var, it });
        }
        if ((pattern) == ("^for\\s+(.+)\\s+in\\s+(.+):$")) {
            string t = _strip_suffix_colon(text);
            if (((t) == ("")) || (!t.StartsWith("for"))) {
                return null;
            }
            string rest = Pytra.CsModule.py_runtime.py_slice(t, System.Convert.ToInt64(3), null).Trim();
            long i = System.Convert.ToInt64(rest.IndexOf(" in "));
            if ((i) < (0)) {
                return null;
            }
            string left = Pytra.CsModule.py_runtime.py_slice(rest, null, System.Convert.ToInt64(i)).Trim();
            string right = Pytra.CsModule.py_runtime.py_slice(rest, System.Convert.ToInt64(i + 4), null).Trim();
            if (((left) == ("")) || ((right) == (""))) {
                return null;
            }
            return new Match(text, new System.Collections.Generic.List<string> { left, right });
        }
        if ((pattern) == ("^with\\s+(.+)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$")) {
            string t = _strip_suffix_colon(text);
            if (((t) == ("")) || (!t.StartsWith("with"))) {
                return null;
            }
            string rest = Pytra.CsModule.py_runtime.py_slice(t, System.Convert.ToInt64(4), null).Trim();
            long i = System.Convert.ToInt64(rest.LastIndexOf(" as "));
            if ((i) < (0)) {
                return null;
            }
            string expr = Pytra.CsModule.py_runtime.py_slice(rest, null, System.Convert.ToInt64(i)).Trim();
            string name = Pytra.CsModule.py_runtime.py_slice(rest, System.Convert.ToInt64(i + 4), null).Trim();
            if (((expr) == ("")) || (!_is_ident(name))) {
                return null;
            }
            return new Match(text, new System.Collections.Generic.List<string> { expr, name });
        }
        if ((pattern) == ("^except\\s+(.+?)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$")) {
            string t = _strip_suffix_colon(text);
            if (((t) == ("")) || (!t.StartsWith("except"))) {
                return null;
            }
            string rest = Pytra.CsModule.py_runtime.py_slice(t, System.Convert.ToInt64(6), null).Trim();
            long i = System.Convert.ToInt64(rest.LastIndexOf(" as "));
            if ((i) < (0)) {
                return null;
            }
            string exc = Pytra.CsModule.py_runtime.py_slice(rest, null, System.Convert.ToInt64(i)).Trim();
            string name = Pytra.CsModule.py_runtime.py_slice(rest, System.Convert.ToInt64(i + 4), null).Trim();
            if (((exc) == ("")) || (!_is_ident(name))) {
                return null;
            }
            return new Match(text, new System.Collections.Generic.List<string> { exc, name });
        }
        if ((pattern) == ("^except\\s+(.+?)\\s*:\\s*$")) {
            string t = _strip_suffix_colon(text);
            if (((t) == ("")) || (!t.StartsWith("except"))) {
                return null;
            }
            string rest = Pytra.CsModule.py_runtime.py_slice(t, System.Convert.ToInt64(6), null).Trim();
            if ((rest) == ("")) {
                return null;
            }
            return new Match(text, new System.Collections.Generic.List<string> { rest });
        }
        if ((pattern) == ("^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*(.+)$")) {
            var c = text.IndexOf(":");
            if ((c) <= (0)) {
                return null;
            }
            string target = Pytra.CsModule.py_runtime.py_slice(text, null, System.Convert.ToInt64(c)).Trim();
            string ann = Pytra.CsModule.py_runtime.py_slice(text, System.Convert.ToInt64(c + 1), null).Trim();
            if (((ann) == ("")) || (!_is_dotted_ident(target))) {
                return null;
            }
            return new Match(text, new System.Collections.Generic.List<string> { target, ann });
        }
        if ((pattern) == ("^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$")) {
            var c = text.IndexOf(":");
            if ((c) <= (0)) {
                return null;
            }
            string target = Pytra.CsModule.py_runtime.py_slice(text, null, System.Convert.ToInt64(c)).Trim();
            string rhs = Pytra.CsModule.py_runtime.py_slice(text, System.Convert.ToInt64(c + 1), null);
            long eq = System.Convert.ToInt64(rhs.IndexOf("="));
            if ((eq) < (0)) {
                return null;
            }
            string ann = Pytra.CsModule.py_runtime.py_slice(rhs, null, System.Convert.ToInt64(eq)).Trim();
            string expr = Pytra.CsModule.py_runtime.py_slice(rhs, System.Convert.ToInt64(eq + 1), null).Trim();
            if ((!_is_dotted_ident(target)) || ((ann) == ("")) || ((expr) == (""))) {
                return null;
            }
            return new Match(text, new System.Collections.Generic.List<string> { target, ann, expr });
        }
        if ((pattern) == ("^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*(\\+=|-=|\\*=|/=|//=|%=|&=|\\|=|\\^=|<<=|>>=)\\s*(.+)$")) {
            System.Collections.Generic.List<string> ops = new System.Collections.Generic.List<string> { "<<=", ">>=", "+=", "-=", "*=", "/=", "//=", "%=", "&=", "|=", "^=" };
            long op_pos = -1;
            string op_txt = "";
            foreach (var op in ops) {
                var p = text.IndexOf(op);
                if (((p) >= (0)) && ((((op_pos) < (0)) || ((p) < (op_pos))))) {
                    op_pos = System.Convert.ToInt64(p);
                    op_txt = op;
                }
            }
            if ((op_pos) < (0)) {
                return null;
            }
            string left = Pytra.CsModule.py_runtime.py_slice(text, null, System.Convert.ToInt64(op_pos)).Trim();
            string right = Pytra.CsModule.py_runtime.py_slice(text, System.Convert.ToInt64(op_pos + (op_txt).Length), null).Trim();
            if (((right) == ("")) || (!_is_dotted_ident(left))) {
                return null;
            }
            return new Match(text, new System.Collections.Generic.List<string> { left, op_txt, right });
        }
        if ((pattern) == ("^([A-Za-z_][A-Za-z0-9_]*)\\s*,\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$")) {
            long eq = System.Convert.ToInt64(text.IndexOf("="));
            if ((eq) < (0)) {
                return null;
            }
            string left = Pytra.CsModule.py_runtime.py_slice(text, null, System.Convert.ToInt64(eq));
            string right = Pytra.CsModule.py_runtime.py_slice(text, System.Convert.ToInt64(eq + 1), null).Trim();
            if ((right) == ("")) {
                return null;
            }
            long c = System.Convert.ToInt64(left.IndexOf(","));
            if ((c) < (0)) {
                return null;
            }
            string a = Pytra.CsModule.py_runtime.py_slice(left, null, System.Convert.ToInt64(c)).Trim();
            string b = Pytra.CsModule.py_runtime.py_slice(left, System.Convert.ToInt64(c + 1), null).Trim();
            if ((!_is_ident(a)) || (!_is_ident(b))) {
                return null;
            }
            return new Match(text, new System.Collections.Generic.List<string> { a, b, right });
        }
        if ((pattern) == ("^if\\s+__name__\\s*==\\s*[\\\"']__main__[\\\"']\\s*:\\s*$")) {
            string t = _strip_suffix_colon(text);
            if ((t) == ("")) {
                return null;
            }
            string rest = t.Trim();
            if (!rest.StartsWith("if")) {
                return null;
            }
            rest = Pytra.CsModule.py_runtime.py_slice(rest, System.Convert.ToInt64(2), null).Trim();
            if (!rest.StartsWith("__name__")) {
                return null;
            }
            rest = Pytra.CsModule.py_runtime.py_slice(rest, System.Convert.ToInt64(("__name__").Length), null).Trim();
            if (!rest.StartsWith("==")) {
                return null;
            }
            rest = Pytra.CsModule.py_runtime.py_slice(rest, System.Convert.ToInt64(2), null).Trim();
            if ((new System.Collections.Generic.HashSet<string> { "\"__main__\"", "'__main__'" }).Contains(rest)) {
                return new Match(text, new System.Collections.Generic.List<object>());
            }
            return null;
        }
        if ((pattern) == ("^import\\s+(.+)$")) {
            if (!text.StartsWith("import")) {
                return null;
            }
            if (((text).Length) <= (6)) {
                return null;
            }
            if (!_is_space_ch(Pytra.CsModule.py_runtime.py_slice(text, System.Convert.ToInt64(6), System.Convert.ToInt64(7)))) {
                return null;
            }
            string rest = Pytra.CsModule.py_runtime.py_slice(text, System.Convert.ToInt64(7), null).Trim();
            if ((rest) == ("")) {
                return null;
            }
            return new Match(text, new System.Collections.Generic.List<string> { rest });
        }
        if ((pattern) == ("^([A-Za-z_][A-Za-z0-9_\\.]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$")) {
            System.Collections.Generic.List<string> parts = new System.Collections.Generic.List<string>(text.Split(new string[] { System.Convert.ToString(" as ") }, System.StringSplitOptions.None));
            if (((parts).Count) == (1)) {
                string name = Pytra.CsModule.py_runtime.py_get(parts, 0).Trim();
                if (!_is_dotted_ident(name)) {
                    return null;
                }
                return new Match(text, new System.Collections.Generic.List<string> { name, "" });
            }
            if (((parts).Count) == (2)) {
                string name = Pytra.CsModule.py_runtime.py_get(parts, 0).Trim();
                string alias = Pytra.CsModule.py_runtime.py_get(parts, 1).Trim();
                if ((!_is_dotted_ident(name)) || (!_is_ident(alias))) {
                    return null;
                }
                return new Match(text, new System.Collections.Generic.List<string> { name, alias });
            }
            return null;
        }
        if ((pattern) == ("^from\\s+([A-Za-z_][A-Za-z0-9_\\.]*)\\s+import\\s+(.+)$")) {
            if (!text.StartsWith("from ")) {
                return null;
            }
            string rest = Pytra.CsModule.py_runtime.py_slice(text, System.Convert.ToInt64(5), null);
            long i = System.Convert.ToInt64(rest.IndexOf(" import "));
            if ((i) < (0)) {
                return null;
            }
            string mod = Pytra.CsModule.py_runtime.py_slice(rest, null, System.Convert.ToInt64(i)).Trim();
            string sym = Pytra.CsModule.py_runtime.py_slice(rest, System.Convert.ToInt64(i + 8), null).Trim();
            if ((!_is_dotted_ident(mod)) || ((sym) == (""))) {
                return null;
            }
            return new Match(text, new System.Collections.Generic.List<string> { mod, sym });
        }
        if ((pattern) == ("^([A-Za-z_][A-Za-z0-9_]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$")) {
            System.Collections.Generic.List<string> parts = new System.Collections.Generic.List<string>(text.Split(new string[] { System.Convert.ToString(" as ") }, System.StringSplitOptions.None));
            if (((parts).Count) == (1)) {
                string name = Pytra.CsModule.py_runtime.py_get(parts, 0).Trim();
                if (!_is_ident(name)) {
                    return null;
                }
                return new Match(text, new System.Collections.Generic.List<string> { name, "" });
            }
            if (((parts).Count) == (2)) {
                string name = Pytra.CsModule.py_runtime.py_get(parts, 0).Trim();
                string alias = Pytra.CsModule.py_runtime.py_get(parts, 1).Trim();
                if ((!_is_ident(name)) || (!_is_ident(alias))) {
                    return null;
                }
                return new Match(text, new System.Collections.Generic.List<string> { name, alias });
            }
            return null;
        }
        if ((pattern) == ("^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$")) {
            var c = text.IndexOf(":");
            if ((c) <= (0)) {
                return null;
            }
            string name = Pytra.CsModule.py_runtime.py_slice(text, null, System.Convert.ToInt64(c)).Trim();
            string rhs = Pytra.CsModule.py_runtime.py_slice(text, System.Convert.ToInt64(c + 1), null);
            long eq = System.Convert.ToInt64(rhs.IndexOf("="));
            if ((eq) < (0)) {
                return null;
            }
            string ann = Pytra.CsModule.py_runtime.py_slice(rhs, null, System.Convert.ToInt64(eq)).Trim();
            string expr = Pytra.CsModule.py_runtime.py_slice(rhs, System.Convert.ToInt64(eq + 1), null).Trim();
            if ((!_is_ident(name)) || ((ann) == ("")) || ((expr) == (""))) {
                return null;
            }
            return new Match(text, new System.Collections.Generic.List<string> { name, ann, expr });
        }
        if ((pattern) == ("^([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$")) {
            long eq = System.Convert.ToInt64(text.IndexOf("="));
            if ((eq) < (0)) {
                return null;
            }
            string name = Pytra.CsModule.py_runtime.py_slice(text, null, System.Convert.ToInt64(eq)).Trim();
            string expr = Pytra.CsModule.py_runtime.py_slice(text, System.Convert.ToInt64(eq + 1), null).Trim();
            if ((!_is_ident(name)) || ((expr) == (""))) {
                return null;
            }
            return new Match(text, new System.Collections.Generic.List<string> { name, expr });
        }
        throw new System.Exception($"unsupported regex pattern in pytra.std.re: {pattern}");
    return default(Match);
    }
    
    public static string sub(string pattern, string repl, string text, long flags = 0)
    {
        if ((pattern) == ("\\s+")) {
            System.Collections.Generic.List<string> py_out = new System.Collections.Generic.List<string>();
            bool in_ws = false;
            foreach (var ch in (text).Select(__ch => __ch.ToString())) {
                if (ch.isspace()) {
                    if (!in_ws) {
                        py_out.Add(repl);
                        in_ws = true;
                    }
                } else {
                    py_out.Add(ch);
                    in_ws = false;
                }
            }
            return string.Join("", py_out);
        }
        if ((pattern) == ("\\s+#.*$")) {
            long i = 0;
            while ((i) < ((text).Length)) {
                if (Pytra.CsModule.py_runtime.py_get(text, i).isspace()) {
                    long j = i + 1;
                    while (((j) < ((text).Length)) && (Pytra.CsModule.py_runtime.py_get(text, j).isspace())) {
                        j += 1;
                    }
                    if (((j) < ((text).Length)) && ((Pytra.CsModule.py_runtime.py_get(text, j)) == ("#"))) {
                        return Pytra.CsModule.py_runtime.py_slice(text, null, System.Convert.ToInt64(i)) + repl;
                    }
                }
                i += 1;
            }
            return text;
        }
        if ((pattern) == ("[^0-9A-Za-z_]")) {
            System.Collections.Generic.List<string> py_out = new System.Collections.Generic.List<string>();
            foreach (var ch in (text).Select(__ch => __ch.ToString())) {
                if ((ch.isalnum()) || ((ch) == ("_"))) {
                    py_out.Add(ch);
                } else {
                    py_out.Add(repl);
                }
            }
            return string.Join("", py_out);
        }
        throw new System.Exception($"unsupported regex sub pattern in pytra.std.re: {pattern}");
    return default(string);
    }
    
    public static void Main(string[] args)
    {
            long S = 1;
    }
}
