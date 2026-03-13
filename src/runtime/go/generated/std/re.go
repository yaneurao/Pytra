// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/re.py
// generated-by: tools/gen_runtime_from_manifest.py

package main

type MatchLike interface {
    group(idx int64) string
}


func __pytra_is_Match(v any) bool {
    _, ok := v.(*Match)
    return ok
}

func __pytra_as_Match(v any) *Match {
    if t, ok := v.(*Match); ok {
        return t
    }
    return nil
}

type Match struct {
    _text string
    _groups []any
}

func NewMatch(text string, groups []any) *Match {
    self := &Match{}
    self.Init(text, groups)
    return self
}

func (self *Match) Init(text string, groups []any) {
    self._text = text
    self._groups = groups
}

func (self *Match) group(idx int64) string {
    if (idx == int64(0)) {
        return __pytra_str(self._text)
    }
    if ((idx < int64(0)) || (idx > __pytra_len(self._groups))) {
        panic(__pytra_str(IndexError("group index out of range")))
    }
    return __pytra_str(__pytra_str(__pytra_get_index(self._groups, (idx - int64(1)))))
}

func group(m any, idx int64) string {
    if (m == nil) {
        return __pytra_str("")
    }
    var mm *Match = __pytra_as_Match(m)
    return __pytra_str(mm.group(idx))
}

func strip_group(m any, idx int64) string {
    return __pytra_str(group(m, idx).strip())
}

func _is_ident(s string) bool {
    if (__pytra_str(s) == __pytra_str("")) {
        return __pytra_truthy(false)
    }
    var h string = __pytra_str(__pytra_slice(s, int64(0), int64(1)))
    var is_head_alpha bool = __pytra_truthy((((__pytra_str("a") <= __pytra_str(h)) && (__pytra_str(h) <= __pytra_str("z"))) || ((__pytra_str("A") <= __pytra_str(h)) && (__pytra_str(h) <= __pytra_str("Z")))))
    if (!(is_head_alpha || (__pytra_str(h) == __pytra_str("_")))) {
        return __pytra_truthy(false)
    }
    __iter_0 := __pytra_as_list(__pytra_slice(s, int64(1), __pytra_len(s)))
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        var ch string = __pytra_str(__iter_0[__i_1])
        var is_alpha bool = __pytra_truthy((((__pytra_str("a") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("z"))) || ((__pytra_str("A") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("Z")))))
        var is_digit bool = __pytra_truthy(((__pytra_str("0") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("9"))))
        if (!(is_alpha || is_digit || (__pytra_str(ch) == __pytra_str("_")))) {
            return __pytra_truthy(false)
        }
    }
    return __pytra_truthy(true)
}

func _is_dotted_ident(s string) bool {
    if (__pytra_str(s) == __pytra_str("")) {
        return __pytra_truthy(false)
    }
    var part string = __pytra_str("")
    __iter_0 := __pytra_as_list(s)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        var ch string = __pytra_str(__iter_0[__i_1])
        if (__pytra_str(ch) == __pytra_str(".")) {
            if (!_is_ident(part)) {
                return __pytra_truthy(false)
            }
            part = __pytra_str("")
            continue
        }
        part += ch
    }
    if (!_is_ident(part)) {
        return __pytra_truthy(false)
    }
    if (__pytra_str(part) == __pytra_str("")) {
        return __pytra_truthy(false)
    }
    return __pytra_truthy(true)
}

func _strip_suffix_colon(s string) string {
    var t string = __pytra_str(s.rstrip())
    if (__pytra_len(t) == int64(0)) {
        return __pytra_str("")
    }
    if (__pytra_str(__pytra_slice(t, (-int64(1)), __pytra_len(t))) != __pytra_str(":")) {
        return __pytra_str("")
    }
    return __pytra_str(__pytra_slice(t, int64(0), (-int64(1))))
}

func _is_space_ch(ch string) bool {
    if (__pytra_str(ch) == __pytra_str(" ")) {
        return __pytra_truthy(true)
    }
    if (__pytra_str(ch) == __pytra_str("	")) {
        return __pytra_truthy(true)
    }
    if (__pytra_str(ch) == __pytra_str("
")) {
        return __pytra_truthy(true)
    }
    if (__pytra_str(ch) == __pytra_str("\n")) {
        return __pytra_truthy(true)
    }
    return __pytra_truthy(false)
}

func _is_alnum_or_underscore(ch string) bool {
    var is_alpha bool = __pytra_truthy((((__pytra_str("a") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("z"))) || ((__pytra_str("A") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("Z")))))
    var is_digit bool = __pytra_truthy(((__pytra_str("0") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("9"))))
    if (is_alpha || is_digit) {
        return __pytra_truthy(true)
    }
    return __pytra_truthy((__pytra_str(ch) == __pytra_str("_")))
}

func _skip_spaces(t string, i int64) int64 {
    for (i < __pytra_len(t)) {
        if (!_is_space_ch(__pytra_slice(t, i, (i + int64(1))))) {
            return i
        }
        i += int64(1)
    }
    return i
}

func match(pattern string, text string, flags int64) any {
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\[(.*)\\]$")) {
        if (!__pytra_truthy(text.endswith("]"))) {
            return nil
        }
        var i any = text.find("[")
        if (__pytra_int(i) <= int64(0)) {
            return nil
        }
        var head string = __pytra_str(__pytra_slice(text, int64(0), i))
        if (!_is_ident(head)) {
            return nil
        }
        return NewMatch(text, []any{head, __pytra_slice(text, (i + int64(1)), (-int64(1)))})
    }
    if (__pytra_str(pattern) == __pytra_str("^def\\s+([A-Za-z_][A-Za-z0-9_]*)\\((.*)\\)\\s*(?:->\\s*(.+)\\s*)?:\\s*$")) {
        var t string = __pytra_str(_strip_suffix_colon(text))
        if (__pytra_str(t) == __pytra_str("")) {
            return nil
        }
        var i int64 = int64(0)
        if (!__pytra_truthy(t.startswith("def"))) {
            return nil
        }
        i = int64(3)
        if ((i >= __pytra_len(t)) || (!_is_space_ch(__pytra_slice(t, i, (i + int64(1)))))) {
            return nil
        }
        i = _skip_spaces(t, i)
        var j int64 = i
        for ((j < __pytra_len(t)) && _is_alnum_or_underscore(__pytra_slice(t, j, (j + int64(1))))) {
            j += int64(1)
        }
        var name string = __pytra_str(__pytra_slice(t, i, j))
        if (!_is_ident(name)) {
            return nil
        }
        var k int64 = j
        k = _skip_spaces(t, k)
        if ((k >= __pytra_len(t)) || (__pytra_str(__pytra_slice(t, k, (k + int64(1)))) != __pytra_str("("))) {
            return nil
        }
        var r int64 = t.rfind(")")
        if (r <= k) {
            return nil
        }
        var args string = __pytra_str(__pytra_slice(t, (k + int64(1)), r))
        var tail string = __pytra_str(__pytra_slice(t, (r + int64(1)), __pytra_len(t)).strip())
        if (__pytra_str(tail) == __pytra_str("")) {
            return NewMatch(text, []any{name, args, ""})
        }
        if (!__pytra_truthy(tail.startswith("->"))) {
            return nil
        }
        var ret string = __pytra_str(__pytra_slice(tail, int64(2), __pytra_len(tail)).strip())
        if (__pytra_str(ret) == __pytra_str("")) {
            return nil
        }
        return NewMatch(text, []any{name, args, ret})
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)(?:\\s*=\\s*(.+))?$")) {
        var c any = text.find(":")
        if (__pytra_int(c) <= int64(0)) {
            return nil
        }
        var name string = __pytra_str(__pytra_slice(text, int64(0), c).strip())
        if (!_is_ident(name)) {
            return nil
        }
        var rhs string = __pytra_str(__pytra_slice(text, (c + int64(1)), __pytra_len(text)))
        var eq any = rhs.find("=")
        if (__pytra_int(eq) < int64(0)) {
            var ann string = __pytra_str(rhs.strip())
            if (__pytra_str(ann) == __pytra_str("")) {
                return nil
            }
            return NewMatch(text, []any{name, ann, ""})
        }
        var ann string = __pytra_str(__pytra_slice(rhs, int64(0), eq).strip())
        var val string = __pytra_str(__pytra_slice(rhs, (eq + int64(1)), __pytra_len(rhs)).strip())
        if ((__pytra_str(ann) == __pytra_str("")) || (__pytra_str(val) == __pytra_str(""))) {
            return nil
        }
        return NewMatch(text, []any{name, ann, val})
    }
    if (__pytra_str(pattern) == __pytra_str("^[A-Za-z_][A-Za-z0-9_]*$")) {
        if _is_ident(text) {
            return NewMatch(text, []any{})
        }
        return nil
    }
    if (__pytra_str(pattern) == __pytra_str("^class\\s+([A-Za-z_][A-Za-z0-9_]*)(?:\\(([A-Za-z_][A-Za-z0-9_]*)\\))?\\s*:\\s*$")) {
        var t string = __pytra_str(_strip_suffix_colon(text))
        if (__pytra_str(t) == __pytra_str("")) {
            return nil
        }
        if (!__pytra_truthy(t.startswith("class"))) {
            return nil
        }
        var i int64 = int64(5)
        if ((i >= __pytra_len(t)) || (!_is_space_ch(__pytra_slice(t, i, (i + int64(1)))))) {
            return nil
        }
        i = _skip_spaces(t, i)
        var j int64 = i
        for ((j < __pytra_len(t)) && _is_alnum_or_underscore(__pytra_slice(t, j, (j + int64(1))))) {
            j += int64(1)
        }
        var name string = __pytra_str(__pytra_slice(t, i, j))
        if (!_is_ident(name)) {
            return nil
        }
        var tail string = __pytra_str(__pytra_slice(t, j, __pytra_len(t)).strip())
        if (__pytra_str(tail) == __pytra_str("")) {
            return NewMatch(text, []any{name, ""})
        }
        if (!(__pytra_truthy(tail.startswith("(")) && __pytra_truthy(tail.endswith(")")))) {
            return nil
        }
        var base string = __pytra_str(__pytra_slice(tail, int64(1), (-int64(1))).strip())
        if (!_is_ident(base)) {
            return nil
        }
        return NewMatch(text, []any{name, base})
    }
    if (__pytra_str(pattern) == __pytra_str("^(any|all)\\((.+)\\)$")) {
        if (__pytra_truthy(text.startswith("any(")) && __pytra_truthy(text.endswith(")")) && (__pytra_len(text) > int64(5))) {
            return NewMatch(text, []any{"any", __pytra_slice(text, int64(4), (-int64(1)))})
        }
        if (__pytra_truthy(text.startswith("all(")) && __pytra_truthy(text.endswith(")")) && (__pytra_len(text) > int64(5))) {
            return NewMatch(text, []any{"all", __pytra_slice(text, int64(4), (-int64(1)))})
        }
        return nil
    }
    if (__pytra_str(pattern) == __pytra_str("^\\[\\s*([A-Za-z_][A-Za-z0-9_]*)\\s+for\\s+([A-Za-z_][A-Za-z0-9_]*)\\s+in\\s+(.+)\\]$")) {
        if (!(__pytra_truthy(text.startswith("[")) && __pytra_truthy(text.endswith("]")))) {
            return nil
        }
        var inner string = __pytra_str(__pytra_slice(text, int64(1), (-int64(1))).strip())
        var m1 string = __pytra_str(" for ")
        var m2 string = __pytra_str(" in ")
        var i int64 = inner.find(m1)
        if (i < int64(0)) {
            return nil
        }
        var expr string = __pytra_str(__pytra_slice(inner, int64(0), i).strip())
        var rest string = __pytra_str(__pytra_slice(inner, (i + __pytra_len(m1)), __pytra_len(inner)))
        var j int64 = rest.find(m2)
        if (j < int64(0)) {
            return nil
        }
        var var_ string = __pytra_str(__pytra_slice(rest, int64(0), j).strip())
        var it string = __pytra_str(__pytra_slice(rest, (j + __pytra_len(m2)), __pytra_len(rest)).strip())
        if ((!_is_ident(expr)) || (!_is_ident(var_)) || (__pytra_str(it) == __pytra_str(""))) {
            return nil
        }
        return NewMatch(text, []any{expr, var_, it})
    }
    if (__pytra_str(pattern) == __pytra_str("^for\\s+(.+)\\s+in\\s+(.+):$")) {
        var t string = __pytra_str(_strip_suffix_colon(text))
        if ((__pytra_str(t) == __pytra_str("")) || (!__pytra_truthy(t.startswith("for")))) {
            return nil
        }
        var rest string = __pytra_str(__pytra_slice(t, int64(3), __pytra_len(t)).strip())
        var i int64 = rest.find(" in ")
        if (i < int64(0)) {
            return nil
        }
        var left string = __pytra_str(__pytra_slice(rest, int64(0), i).strip())
        var right string = __pytra_str(__pytra_slice(rest, (i + int64(4)), __pytra_len(rest)).strip())
        if ((__pytra_str(left) == __pytra_str("")) || (__pytra_str(right) == __pytra_str(""))) {
            return nil
        }
        return NewMatch(text, []any{left, right})
    }
    if (__pytra_str(pattern) == __pytra_str("^with\\s+(.+)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$")) {
        var t string = __pytra_str(_strip_suffix_colon(text))
        if ((__pytra_str(t) == __pytra_str("")) || (!__pytra_truthy(t.startswith("with")))) {
            return nil
        }
        var rest string = __pytra_str(__pytra_slice(t, int64(4), __pytra_len(t)).strip())
        var i int64 = rest.rfind(" as ")
        if (i < int64(0)) {
            return nil
        }
        var expr string = __pytra_str(__pytra_slice(rest, int64(0), i).strip())
        var name string = __pytra_str(__pytra_slice(rest, (i + int64(4)), __pytra_len(rest)).strip())
        if ((__pytra_str(expr) == __pytra_str("")) || (!_is_ident(name))) {
            return nil
        }
        return NewMatch(text, []any{expr, name})
    }
    if (__pytra_str(pattern) == __pytra_str("^except\\s+(.+?)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$")) {
        var t string = __pytra_str(_strip_suffix_colon(text))
        if ((__pytra_str(t) == __pytra_str("")) || (!__pytra_truthy(t.startswith("except")))) {
            return nil
        }
        var rest string = __pytra_str(__pytra_slice(t, int64(6), __pytra_len(t)).strip())
        var i int64 = rest.rfind(" as ")
        if (i < int64(0)) {
            return nil
        }
        var exc string = __pytra_str(__pytra_slice(rest, int64(0), i).strip())
        var name string = __pytra_str(__pytra_slice(rest, (i + int64(4)), __pytra_len(rest)).strip())
        if ((__pytra_str(exc) == __pytra_str("")) || (!_is_ident(name))) {
            return nil
        }
        return NewMatch(text, []any{exc, name})
    }
    if (__pytra_str(pattern) == __pytra_str("^except\\s+(.+?)\\s*:\\s*$")) {
        var t string = __pytra_str(_strip_suffix_colon(text))
        if ((__pytra_str(t) == __pytra_str("")) || (!__pytra_truthy(t.startswith("except")))) {
            return nil
        }
        var rest string = __pytra_str(__pytra_slice(t, int64(6), __pytra_len(t)).strip())
        if (__pytra_str(rest) == __pytra_str("")) {
            return nil
        }
        return NewMatch(text, []any{rest})
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*(.+)$")) {
        var c any = text.find(":")
        if (__pytra_int(c) <= int64(0)) {
            return nil
        }
        var target string = __pytra_str(__pytra_slice(text, int64(0), c).strip())
        var ann string = __pytra_str(__pytra_slice(text, (c + int64(1)), __pytra_len(text)).strip())
        if ((__pytra_str(ann) == __pytra_str("")) || (!_is_dotted_ident(target))) {
            return nil
        }
        return NewMatch(text, []any{target, ann})
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$")) {
        var c any = text.find(":")
        if (__pytra_int(c) <= int64(0)) {
            return nil
        }
        var target string = __pytra_str(__pytra_slice(text, int64(0), c).strip())
        var rhs string = __pytra_str(__pytra_slice(text, (c + int64(1)), __pytra_len(text)))
        var eq int64 = rhs.find("=")
        if (eq < int64(0)) {
            return nil
        }
        var ann string = __pytra_str(__pytra_slice(rhs, int64(0), eq).strip())
        var expr string = __pytra_str(__pytra_slice(rhs, (eq + int64(1)), __pytra_len(rhs)).strip())
        if ((!_is_dotted_ident(target)) || (__pytra_str(ann) == __pytra_str("")) || (__pytra_str(expr) == __pytra_str(""))) {
            return nil
        }
        return NewMatch(text, []any{target, ann, expr})
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*(\\+=|-=|\\*=|/=|//=|%=|&=|\\|=|\\^=|<<=|>>=)\\s*(.+)$")) {
        var ops []any = __pytra_as_list([]any{"<<=", ">>=", "+=", "-=", "*=", "/=", "//=", "%=", "&=", "|=", "^="})
        var op_pos int64 = (-int64(1))
        var op_txt string = __pytra_str("")
        __iter_0 := __pytra_as_list(ops)
        for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
            var op string = __pytra_str(__iter_0[__i_1])
            var p any = text.find(op)
            if ((__pytra_int(p) >= int64(0)) && ((op_pos < int64(0)) || (__pytra_int(p) < op_pos))) {
                op_pos = p
                op_txt = __pytra_str(op)
            }
        }
        if (op_pos < int64(0)) {
            return nil
        }
        var left string = __pytra_str(__pytra_slice(text, int64(0), op_pos).strip())
        var right string = __pytra_str(__pytra_slice(text, (op_pos + __pytra_len(op_txt)), __pytra_len(text)).strip())
        if ((__pytra_str(right) == __pytra_str("")) || (!_is_dotted_ident(left))) {
            return nil
        }
        return NewMatch(text, []any{left, op_txt, right})
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\s*,\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$")) {
        var eq int64 = text.find("=")
        if (eq < int64(0)) {
            return nil
        }
        var left string = __pytra_str(__pytra_slice(text, int64(0), eq))
        var right string = __pytra_str(__pytra_slice(text, (eq + int64(1)), __pytra_len(text)).strip())
        if (__pytra_str(right) == __pytra_str("")) {
            return nil
        }
        var c int64 = left.find(",")
        if (c < int64(0)) {
            return nil
        }
        var a string = __pytra_str(__pytra_slice(left, int64(0), c).strip())
        var b string = __pytra_str(__pytra_slice(left, (c + int64(1)), __pytra_len(left)).strip())
        if ((!_is_ident(a)) || (!_is_ident(b))) {
            return nil
        }
        return NewMatch(text, []any{a, b, right})
    }
    if (__pytra_str(pattern) == __pytra_str("^if\\s+__name__\\s*==\\s*[\\\"']__main__[\\\"']\\s*:\\s*$")) {
        var t string = __pytra_str(_strip_suffix_colon(text))
        if (__pytra_str(t) == __pytra_str("")) {
            return nil
        }
        var rest string = __pytra_str(t.strip())
        if (!__pytra_truthy(rest.startswith("if"))) {
            return nil
        }
        rest = __pytra_str(__pytra_slice(rest, int64(2), __pytra_len(rest)).strip())
        if (!__pytra_truthy(rest.startswith("__name__"))) {
            return nil
        }
        rest = __pytra_str(__pytra_slice(rest, __pytra_len("__name__"), __pytra_len(rest)).strip())
        if (!__pytra_truthy(rest.startswith("=="))) {
            return nil
        }
        rest = __pytra_str(__pytra_slice(rest, int64(2), __pytra_len(rest)).strip())
        if ((__pytra_str(rest) == __pytra_str("\"__main__\"")) || (__pytra_str(rest) == __pytra_str("'__main__'"))) {
            return NewMatch(text, []any{})
        }
        return nil
    }
    if (__pytra_str(pattern) == __pytra_str("^import\\s+(.+)$")) {
        if (!__pytra_truthy(text.startswith("import"))) {
            return nil
        }
        if (__pytra_len(text) <= int64(6)) {
            return nil
        }
        if (!_is_space_ch(__pytra_slice(text, int64(6), int64(7)))) {
            return nil
        }
        var rest string = __pytra_str(__pytra_slice(text, int64(7), __pytra_len(text)).strip())
        if (__pytra_str(rest) == __pytra_str("")) {
            return nil
        }
        return NewMatch(text, []any{rest})
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_\\.]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$")) {
        var parts []any = __pytra_as_list(text.split(" as "))
        if (__pytra_len(parts) == int64(1)) {
            var name string = __pytra_str(__pytra_str(__pytra_get_index(parts, int64(0))).strip())
            if (!_is_dotted_ident(name)) {
                return nil
            }
            return NewMatch(text, []any{name, ""})
        }
        if (__pytra_len(parts) == int64(2)) {
            var name string = __pytra_str(__pytra_str(__pytra_get_index(parts, int64(0))).strip())
            var alias string = __pytra_str(__pytra_str(__pytra_get_index(parts, int64(1))).strip())
            if ((!_is_dotted_ident(name)) || (!_is_ident(alias))) {
                return nil
            }
            return NewMatch(text, []any{name, alias})
        }
        return nil
    }
    if (__pytra_str(pattern) == __pytra_str("^from\\s+([A-Za-z_][A-Za-z0-9_\\.]*)\\s+import\\s+(.+)$")) {
        if (!__pytra_truthy(text.startswith("from "))) {
            return nil
        }
        var rest string = __pytra_str(__pytra_slice(text, int64(5), __pytra_len(text)))
        var i int64 = rest.find(" import ")
        if (i < int64(0)) {
            return nil
        }
        var mod string = __pytra_str(__pytra_slice(rest, int64(0), i).strip())
        var sym string = __pytra_str(__pytra_slice(rest, (i + int64(8)), __pytra_len(rest)).strip())
        if ((!_is_dotted_ident(mod)) || (__pytra_str(sym) == __pytra_str(""))) {
            return nil
        }
        return NewMatch(text, []any{mod, sym})
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$")) {
        var parts []any = __pytra_as_list(text.split(" as "))
        if (__pytra_len(parts) == int64(1)) {
            var name string = __pytra_str(__pytra_str(__pytra_get_index(parts, int64(0))).strip())
            if (!_is_ident(name)) {
                return nil
            }
            return NewMatch(text, []any{name, ""})
        }
        if (__pytra_len(parts) == int64(2)) {
            var name string = __pytra_str(__pytra_str(__pytra_get_index(parts, int64(0))).strip())
            var alias string = __pytra_str(__pytra_str(__pytra_get_index(parts, int64(1))).strip())
            if ((!_is_ident(name)) || (!_is_ident(alias))) {
                return nil
            }
            return NewMatch(text, []any{name, alias})
        }
        return nil
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$")) {
        var c any = text.find(":")
        if (__pytra_int(c) <= int64(0)) {
            return nil
        }
        var name string = __pytra_str(__pytra_slice(text, int64(0), c).strip())
        var rhs string = __pytra_str(__pytra_slice(text, (c + int64(1)), __pytra_len(text)))
        var eq int64 = rhs.find("=")
        if (eq < int64(0)) {
            return nil
        }
        var ann string = __pytra_str(__pytra_slice(rhs, int64(0), eq).strip())
        var expr string = __pytra_str(__pytra_slice(rhs, (eq + int64(1)), __pytra_len(rhs)).strip())
        if ((!_is_ident(name)) || (__pytra_str(ann) == __pytra_str("")) || (__pytra_str(expr) == __pytra_str(""))) {
            return nil
        }
        return NewMatch(text, []any{name, ann, expr})
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$")) {
        var eq int64 = text.find("=")
        if (eq < int64(0)) {
            return nil
        }
        var name string = __pytra_str(__pytra_slice(text, int64(0), eq).strip())
        var expr string = __pytra_str(__pytra_slice(text, (eq + int64(1)), __pytra_len(text)).strip())
        if ((!_is_ident(name)) || (__pytra_str(expr) == __pytra_str(""))) {
            return nil
        }
        return NewMatch(text, []any{name, expr})
    }
    panic(__pytra_str(nil))
    return nil
}

func sub(pattern string, repl string, text string, flags int64) string {
    if (__pytra_str(pattern) == __pytra_str("\\s+")) {
        var out []any = __pytra_as_list([]any{})
        var in_ws bool = __pytra_truthy(false)
        __iter_0 := __pytra_as_list(text)
        for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
            var ch string = __pytra_str(__iter_0[__i_1])
            if __pytra_truthy(ch.isspace()) {
                if (!in_ws) {
                    out = append(out, repl)
                    in_ws = __pytra_truthy(true)
                }
            } else {
                out = append(out, ch)
                in_ws = __pytra_truthy(false)
            }
        }
        return __pytra_str("".join(out))
    }
    if (__pytra_str(pattern) == __pytra_str("\\s+#.*$")) {
        var i int64 = int64(0)
        for (i < __pytra_len(text)) {
            if __pytra_truthy(__pytra_str(__pytra_get_index(text, i)).isspace()) {
                var j int64 = (i + int64(1))
                for ((j < __pytra_len(text)) && __pytra_truthy(__pytra_str(__pytra_get_index(text, j)).isspace())) {
                    j += int64(1)
                }
                if ((j < __pytra_len(text)) && (__pytra_str(__pytra_str(__pytra_get_index(text, j))) == __pytra_str("#"))) {
                    return __pytra_str((__pytra_str(__pytra_slice(text, int64(0), i)) + __pytra_str(repl)))
                }
            }
            i += int64(1)
        }
        return __pytra_str(text)
    }
    if (__pytra_str(pattern) == __pytra_str("[^0-9A-Za-z_]")) {
        var out []any = __pytra_as_list([]any{})
        __iter_2 := __pytra_as_list(text)
        for __i_3 := int64(0); __i_3 < int64(len(__iter_2)); __i_3 += 1 {
            var ch string = __pytra_str(__iter_2[__i_3])
            if (__pytra_truthy(ch.isalnum()) || (__pytra_str(ch) == __pytra_str("_"))) {
                out = append(out, ch)
            } else {
                out = append(out, repl)
            }
        }
        return __pytra_str("".join(out))
    }
    panic(__pytra_str(nil))
    return ""
}
