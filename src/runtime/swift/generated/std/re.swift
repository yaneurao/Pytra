// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/re.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func __pytra_is_Match(_ v: Any?) -> Bool {
    return v is Match
}

class Match {
    var _text: String = ""
    var _groups: [Any] = []

    init(_ text: String, _ groups: [Any]) {
        self._text = text
        self._groups = groups
    }

    func group(_ idx: Int64) -> String {
        if (__pytra_int(idx) == __pytra_int(Int64(0))) {
            return __pytra_str(self._text)
        }
        if ((__pytra_int(idx) < __pytra_int(Int64(0))) || (__pytra_int(idx) > __pytra_int(__pytra_len(self._groups)))) {
            fatalError("pytra raise")
        }
        return __pytra_str(__pytra_getIndex(self._groups, (idx - Int64(1))))
    }
}

func group(_ m: Any, _ idx: Int64) -> String {
    if (__pytra_float(m) == __pytra_float(__pytra_any_default())) {
        return ""
    }
    var mm: Match = (m as? Match) ?? Match()
    return mm.group(idx)
}

func strip_group(_ m: Any, _ idx: Int64) -> String {
    return group(m, idx).strip()
}

func _is_ident(_ s: String) -> Bool {
    if (__pytra_str(s) == __pytra_str("")) {
        return false
    }
    var h: String = __pytra_str(__pytra_slice(s, Int64(0), Int64(1)))
    var is_head_alpha: Bool = (((__pytra_str("a") <= __pytra_str(h)) && (__pytra_str(h) <= __pytra_str("z"))) || ((__pytra_str("A") <= __pytra_str(h)) && (__pytra_str(h) <= __pytra_str("Z"))))
    if (!(is_head_alpha || (__pytra_str(h) == __pytra_str("_")))) {
        return false
    }
    do {
        let __iter_0 = __pytra_as_list(__pytra_slice(s, Int64(1), __pytra_len(s)))
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let ch: String = __pytra_str(__iter_0[Int(__i_1)])
            var is_alpha: Bool = (((__pytra_str("a") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("z"))) || ((__pytra_str("A") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("Z"))))
            var is_digit: Bool = ((__pytra_str("0") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("9")))
            if (!(is_alpha || is_digit || (__pytra_str(ch) == __pytra_str("_")))) {
                return false
            }
            __i_1 += 1
        }
    }
    return true
}

func _is_dotted_ident(_ s: String) -> Bool {
    if (__pytra_str(s) == __pytra_str("")) {
        return false
    }
    var part: String = ""
    do {
        let __iter_0 = __pytra_as_list(s)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let ch: String = __pytra_str(__iter_0[Int(__i_1)])
            if (__pytra_str(ch) == __pytra_str(".")) {
                if (!_is_ident(part)) {
                    return false
                }
                part = ""
                __i_1 += 1
                continue
            }
            part += ch
            __i_1 += 1
        }
    }
    if (!_is_ident(part)) {
        return false
    }
    if (__pytra_str(part) == __pytra_str("")) {
        return false
    }
    return true
}

func _strip_suffix_colon(_ s: String) -> String {
    var t: String = s.rstrip()
    if (__pytra_int(__pytra_len(t)) == __pytra_int(Int64(0))) {
        return ""
    }
    if (__pytra_str(__pytra_slice(t, (-Int64(1)), __pytra_len(t))) != __pytra_str(":")) {
        return ""
    }
    return __pytra_str(__pytra_slice(t, Int64(0), (-Int64(1))))
}

func _is_space_ch(_ ch: String) -> Bool {
    if (__pytra_str(ch) == __pytra_str(" ")) {
        return true
    }
    if (__pytra_str(ch) == __pytra_str("	")) {
        return true
    }
    if (__pytra_str(ch) == __pytra_str("
")) {
        return true
    }
    if (__pytra_str(ch) == __pytra_str("\n")) {
        return true
    }
    return false
}

func _is_alnum_or_underscore(_ ch: String) -> Bool {
    var is_alpha: Bool = (((__pytra_str("a") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("z"))) || ((__pytra_str("A") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("Z"))))
    var is_digit: Bool = ((__pytra_str("0") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("9")))
    if (is_alpha || is_digit) {
        return true
    }
    return (__pytra_str(ch) == __pytra_str("_"))
}

func _skip_spaces(_ t: String, _ i: Int64) -> Int64 {
    while (__pytra_int(i) < __pytra_int(__pytra_len(t))) {
        if (!_is_space_ch(__pytra_slice(t, i, (i + Int64(1))))) {
            return i
        }
        i += Int64(1)
    }
    return i
}

func match(_ pattern: String, _ text: String, _ flags: Int64) -> Any {
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\[(.*)\\]$")) {
        if (!__pytra_truthy(text.endswith("]"))) {
            return __pytra_any_default()
        }
        var i: Any = text.find("[")
        if (__pytra_int(i) <= __pytra_int(Int64(0))) {
            return __pytra_any_default()
        }
        var head: String = __pytra_str(__pytra_slice(text, Int64(0), i))
        if (!_is_ident(head)) {
            return __pytra_any_default()
        }
        return Match(text, [head, __pytra_slice(text, (i + Int64(1)), (-Int64(1)))])
    }
    if (__pytra_str(pattern) == __pytra_str("^def\\s+([A-Za-z_][A-Za-z0-9_]*)\\((.*)\\)\\s*(?:->\\s*(.+)\\s*)?:\\s*$")) {
        var t: String = _strip_suffix_colon(text)
        if (__pytra_str(t) == __pytra_str("")) {
            return __pytra_any_default()
        }
        var i: Int64 = Int64(0)
        if (!__pytra_truthy(t.startswith("def"))) {
            return __pytra_any_default()
        }
        i = Int64(3)
        if ((__pytra_int(i) >= __pytra_int(__pytra_len(t))) || (!_is_space_ch(__pytra_slice(t, i, (i + Int64(1)))))) {
            return __pytra_any_default()
        }
        i = _skip_spaces(t, i)
        var j: Int64 = i
        while ((__pytra_int(j) < __pytra_int(__pytra_len(t))) && _is_alnum_or_underscore(__pytra_slice(t, j, (j + Int64(1))))) {
            j += Int64(1)
        }
        var name: String = __pytra_str(__pytra_slice(t, i, j))
        if (!_is_ident(name)) {
            return __pytra_any_default()
        }
        var k: Int64 = j
        k = _skip_spaces(t, k)
        if ((__pytra_int(k) >= __pytra_int(__pytra_len(t))) || (__pytra_str(__pytra_slice(t, k, (k + Int64(1)))) != __pytra_str("("))) {
            return __pytra_any_default()
        }
        var r: Int64 = __pytra_int(t.rfind(")"))
        if (__pytra_int(r) <= __pytra_int(k)) {
            return __pytra_any_default()
        }
        var args: String = __pytra_str(__pytra_slice(t, (k + Int64(1)), r))
        var tail: String = __pytra_slice(t, (r + Int64(1)), __pytra_len(t)).strip()
        if (__pytra_str(tail) == __pytra_str("")) {
            return Match(text, [name, args, ""])
        }
        if (!__pytra_truthy(tail.startswith("->"))) {
            return __pytra_any_default()
        }
        var ret: String = __pytra_slice(tail, Int64(2), __pytra_len(tail)).strip()
        if (__pytra_str(ret) == __pytra_str("")) {
            return __pytra_any_default()
        }
        return Match(text, [name, args, ret])
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)(?:\\s*=\\s*(.+))?$")) {
        var c: Any = text.find(":")
        if (__pytra_int(c) <= __pytra_int(Int64(0))) {
            return __pytra_any_default()
        }
        var name: String = __pytra_slice(text, Int64(0), c).strip()
        if (!_is_ident(name)) {
            return __pytra_any_default()
        }
        var rhs: String = __pytra_str(__pytra_slice(text, (c + Int64(1)), __pytra_len(text)))
        var eq: Any = rhs.find("=")
        if (__pytra_int(eq) < __pytra_int(Int64(0))) {
            var ann: String = rhs.strip()
            if (__pytra_str(ann) == __pytra_str("")) {
                return __pytra_any_default()
            }
            return Match(text, [name, ann, ""])
        }
        var ann: String = __pytra_slice(rhs, Int64(0), eq).strip()
        var val: String = __pytra_slice(rhs, (eq + Int64(1)), __pytra_len(rhs)).strip()
        if ((__pytra_str(ann) == __pytra_str("")) || (__pytra_str(val) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        return Match(text, [name, ann, val])
    }
    if (__pytra_str(pattern) == __pytra_str("^[A-Za-z_][A-Za-z0-9_]*$")) {
        if _is_ident(text) {
            return Match(text, [])
        }
        return __pytra_any_default()
    }
    if (__pytra_str(pattern) == __pytra_str("^class\\s+([A-Za-z_][A-Za-z0-9_]*)(?:\\(([A-Za-z_][A-Za-z0-9_]*)\\))?\\s*:\\s*$")) {
        var t: String = _strip_suffix_colon(text)
        if (__pytra_str(t) == __pytra_str("")) {
            return __pytra_any_default()
        }
        if (!__pytra_truthy(t.startswith("class"))) {
            return __pytra_any_default()
        }
        var i: Int64 = Int64(5)
        if ((__pytra_int(i) >= __pytra_int(__pytra_len(t))) || (!_is_space_ch(__pytra_slice(t, i, (i + Int64(1)))))) {
            return __pytra_any_default()
        }
        i = _skip_spaces(t, i)
        var j: Int64 = i
        while ((__pytra_int(j) < __pytra_int(__pytra_len(t))) && _is_alnum_or_underscore(__pytra_slice(t, j, (j + Int64(1))))) {
            j += Int64(1)
        }
        var name: String = __pytra_str(__pytra_slice(t, i, j))
        if (!_is_ident(name)) {
            return __pytra_any_default()
        }
        var tail: String = __pytra_slice(t, j, __pytra_len(t)).strip()
        if (__pytra_str(tail) == __pytra_str("")) {
            return Match(text, [name, ""])
        }
        if (!(__pytra_truthy(tail.startswith("(")) && __pytra_truthy(tail.endswith(")")))) {
            return __pytra_any_default()
        }
        var base: String = __pytra_slice(tail, Int64(1), (-Int64(1))).strip()
        if (!_is_ident(base)) {
            return __pytra_any_default()
        }
        return Match(text, [name, base])
    }
    if (__pytra_str(pattern) == __pytra_str("^(any|all)\\((.+)\\)$")) {
        if (__pytra_truthy(text.startswith("any(")) && __pytra_truthy(text.endswith(")")) && (__pytra_int(__pytra_len(text)) > __pytra_int(Int64(5)))) {
            return Match(text, ["any", __pytra_slice(text, Int64(4), (-Int64(1)))])
        }
        if (__pytra_truthy(text.startswith("all(")) && __pytra_truthy(text.endswith(")")) && (__pytra_int(__pytra_len(text)) > __pytra_int(Int64(5)))) {
            return Match(text, ["all", __pytra_slice(text, Int64(4), (-Int64(1)))])
        }
        return __pytra_any_default()
    }
    if (__pytra_str(pattern) == __pytra_str("^\\[\\s*([A-Za-z_][A-Za-z0-9_]*)\\s+for\\s+([A-Za-z_][A-Za-z0-9_]*)\\s+in\\s+(.+)\\]$")) {
        if (!(__pytra_truthy(text.startswith("[")) && __pytra_truthy(text.endswith("]")))) {
            return __pytra_any_default()
        }
        var inner: String = __pytra_slice(text, Int64(1), (-Int64(1))).strip()
        var m1: String = " for "
        var m2: String = " in "
        var i: Int64 = __pytra_int(inner.find(m1))
        if (__pytra_int(i) < __pytra_int(Int64(0))) {
            return __pytra_any_default()
        }
        var expr: String = __pytra_slice(inner, Int64(0), i).strip()
        var rest: String = __pytra_str(__pytra_slice(inner, (i + __pytra_len(m1)), __pytra_len(inner)))
        var j: Int64 = __pytra_int(rest.find(m2))
        if (__pytra_int(j) < __pytra_int(Int64(0))) {
            return __pytra_any_default()
        }
        var var_: String = __pytra_slice(rest, Int64(0), j).strip()
        var it: String = __pytra_slice(rest, (j + __pytra_len(m2)), __pytra_len(rest)).strip()
        if ((!_is_ident(expr)) || (!_is_ident(var_)) || (__pytra_str(it) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        return Match(text, [expr, var_, it])
    }
    if (__pytra_str(pattern) == __pytra_str("^for\\s+(.+)\\s+in\\s+(.+):$")) {
        var t: String = _strip_suffix_colon(text)
        if ((__pytra_str(t) == __pytra_str("")) || (!__pytra_truthy(t.startswith("for")))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_slice(t, Int64(3), __pytra_len(t)).strip()
        var i: Int64 = __pytra_int(rest.find(" in "))
        if (__pytra_int(i) < __pytra_int(Int64(0))) {
            return __pytra_any_default()
        }
        var left: String = __pytra_slice(rest, Int64(0), i).strip()
        var right: String = __pytra_slice(rest, (i + Int64(4)), __pytra_len(rest)).strip()
        if ((__pytra_str(left) == __pytra_str("")) || (__pytra_str(right) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        return Match(text, [left, right])
    }
    if (__pytra_str(pattern) == __pytra_str("^with\\s+(.+)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$")) {
        var t: String = _strip_suffix_colon(text)
        if ((__pytra_str(t) == __pytra_str("")) || (!__pytra_truthy(t.startswith("with")))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_slice(t, Int64(4), __pytra_len(t)).strip()
        var i: Int64 = __pytra_int(rest.rfind(" as "))
        if (__pytra_int(i) < __pytra_int(Int64(0))) {
            return __pytra_any_default()
        }
        var expr: String = __pytra_slice(rest, Int64(0), i).strip()
        var name: String = __pytra_slice(rest, (i + Int64(4)), __pytra_len(rest)).strip()
        if ((__pytra_str(expr) == __pytra_str("")) || (!_is_ident(name))) {
            return __pytra_any_default()
        }
        return Match(text, [expr, name])
    }
    if (__pytra_str(pattern) == __pytra_str("^except\\s+(.+?)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$")) {
        var t: String = _strip_suffix_colon(text)
        if ((__pytra_str(t) == __pytra_str("")) || (!__pytra_truthy(t.startswith("except")))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_slice(t, Int64(6), __pytra_len(t)).strip()
        var i: Int64 = __pytra_int(rest.rfind(" as "))
        if (__pytra_int(i) < __pytra_int(Int64(0))) {
            return __pytra_any_default()
        }
        var exc: String = __pytra_slice(rest, Int64(0), i).strip()
        var name: String = __pytra_slice(rest, (i + Int64(4)), __pytra_len(rest)).strip()
        if ((__pytra_str(exc) == __pytra_str("")) || (!_is_ident(name))) {
            return __pytra_any_default()
        }
        return Match(text, [exc, name])
    }
    if (__pytra_str(pattern) == __pytra_str("^except\\s+(.+?)\\s*:\\s*$")) {
        var t: String = _strip_suffix_colon(text)
        if ((__pytra_str(t) == __pytra_str("")) || (!__pytra_truthy(t.startswith("except")))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_slice(t, Int64(6), __pytra_len(t)).strip()
        if (__pytra_str(rest) == __pytra_str("")) {
            return __pytra_any_default()
        }
        return Match(text, [rest])
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*(.+)$")) {
        var c: Any = text.find(":")
        if (__pytra_int(c) <= __pytra_int(Int64(0))) {
            return __pytra_any_default()
        }
        var target: String = __pytra_slice(text, Int64(0), c).strip()
        var ann: String = __pytra_slice(text, (c + Int64(1)), __pytra_len(text)).strip()
        if ((__pytra_str(ann) == __pytra_str("")) || (!_is_dotted_ident(target))) {
            return __pytra_any_default()
        }
        return Match(text, [target, ann])
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$")) {
        var c: Any = text.find(":")
        if (__pytra_int(c) <= __pytra_int(Int64(0))) {
            return __pytra_any_default()
        }
        var target: String = __pytra_slice(text, Int64(0), c).strip()
        var rhs: String = __pytra_str(__pytra_slice(text, (c + Int64(1)), __pytra_len(text)))
        var eq: Int64 = __pytra_int(rhs.find("="))
        if (__pytra_int(eq) < __pytra_int(Int64(0))) {
            return __pytra_any_default()
        }
        var ann: String = __pytra_slice(rhs, Int64(0), eq).strip()
        var expr: String = __pytra_slice(rhs, (eq + Int64(1)), __pytra_len(rhs)).strip()
        if ((!_is_dotted_ident(target)) || (__pytra_str(ann) == __pytra_str("")) || (__pytra_str(expr) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        return Match(text, [target, ann, expr])
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*(\\+=|-=|\\*=|/=|//=|%=|&=|\\|=|\\^=|<<=|>>=)\\s*(.+)$")) {
        var ops: [Any] = __pytra_as_list(["<<=", ">>=", "+=", "-=", "*=", "/=", "//=", "%=", "&=", "|=", "^="])
        var op_pos: Int64 = __pytra_int(-Int64(1))
        var op_txt: String = ""
        do {
            let __iter_0 = __pytra_as_list(ops)
            var __i_1: Int64 = 0
            while __i_1 < Int64(__iter_0.count) {
                let op: String = __pytra_str(__iter_0[Int(__i_1)])
                var p: Any = text.find(op)
                if ((__pytra_int(p) >= __pytra_int(Int64(0))) && ((__pytra_int(op_pos) < __pytra_int(Int64(0))) || (__pytra_int(p) < __pytra_int(op_pos)))) {
                    op_pos = __pytra_int(p)
                    op_txt = op
                }
                __i_1 += 1
            }
        }
        if (__pytra_int(op_pos) < __pytra_int(Int64(0))) {
            return __pytra_any_default()
        }
        var left: String = __pytra_slice(text, Int64(0), op_pos).strip()
        var right: String = __pytra_slice(text, (op_pos + __pytra_len(op_txt)), __pytra_len(text)).strip()
        if ((__pytra_str(right) == __pytra_str("")) || (!_is_dotted_ident(left))) {
            return __pytra_any_default()
        }
        return Match(text, [left, op_txt, right])
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\s*,\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$")) {
        var eq: Int64 = __pytra_int(text.find("="))
        if (__pytra_int(eq) < __pytra_int(Int64(0))) {
            return __pytra_any_default()
        }
        var left: String = __pytra_str(__pytra_slice(text, Int64(0), eq))
        var right: String = __pytra_slice(text, (eq + Int64(1)), __pytra_len(text)).strip()
        if (__pytra_str(right) == __pytra_str("")) {
            return __pytra_any_default()
        }
        var c: Int64 = __pytra_int(left.find(","))
        if (__pytra_int(c) < __pytra_int(Int64(0))) {
            return __pytra_any_default()
        }
        var a: String = __pytra_slice(left, Int64(0), c).strip()
        var b: String = __pytra_slice(left, (c + Int64(1)), __pytra_len(left)).strip()
        if ((!_is_ident(a)) || (!_is_ident(b))) {
            return __pytra_any_default()
        }
        return Match(text, [a, b, right])
    }
    if (__pytra_str(pattern) == __pytra_str("^if\\s+__name__\\s*==\\s*[\\\"']__main__[\\\"']\\s*:\\s*$")) {
        var t: String = _strip_suffix_colon(text)
        if (__pytra_str(t) == __pytra_str("")) {
            return __pytra_any_default()
        }
        var rest: String = t.strip()
        if (!__pytra_truthy(rest.startswith("if"))) {
            return __pytra_any_default()
        }
        rest = __pytra_slice(rest, Int64(2), __pytra_len(rest)).strip()
        if (!__pytra_truthy(rest.startswith("__name__"))) {
            return __pytra_any_default()
        }
        rest = __pytra_slice(rest, __pytra_len("__name__"), __pytra_len(rest)).strip()
        if (!__pytra_truthy(rest.startswith("=="))) {
            return __pytra_any_default()
        }
        rest = __pytra_slice(rest, Int64(2), __pytra_len(rest)).strip()
        if ((__pytra_str(rest) == __pytra_str("\"__main__\"")) || (__pytra_str(rest) == __pytra_str("'__main__'"))) {
            return Match(text, [])
        }
        return __pytra_any_default()
    }
    if (__pytra_str(pattern) == __pytra_str("^import\\s+(.+)$")) {
        if (!__pytra_truthy(text.startswith("import"))) {
            return __pytra_any_default()
        }
        if (__pytra_int(__pytra_len(text)) <= __pytra_int(Int64(6))) {
            return __pytra_any_default()
        }
        if (!_is_space_ch(__pytra_slice(text, Int64(6), Int64(7)))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_slice(text, Int64(7), __pytra_len(text)).strip()
        if (__pytra_str(rest) == __pytra_str("")) {
            return __pytra_any_default()
        }
        return Match(text, [rest])
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_\\.]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$")) {
        var parts: [Any] = text.split(" as ")
        if (__pytra_int(__pytra_len(parts)) == __pytra_int(Int64(1))) {
            var name: String = __pytra_str(__pytra_getIndex(parts, Int64(0))).strip()
            if (!_is_dotted_ident(name)) {
                return __pytra_any_default()
            }
            return Match(text, [name, ""])
        }
        if (__pytra_int(__pytra_len(parts)) == __pytra_int(Int64(2))) {
            var name: String = __pytra_str(__pytra_getIndex(parts, Int64(0))).strip()
            var alias: String = __pytra_str(__pytra_getIndex(parts, Int64(1))).strip()
            if ((!_is_dotted_ident(name)) || (!_is_ident(alias))) {
                return __pytra_any_default()
            }
            return Match(text, [name, alias])
        }
        return __pytra_any_default()
    }
    if (__pytra_str(pattern) == __pytra_str("^from\\s+([A-Za-z_][A-Za-z0-9_\\.]*)\\s+import\\s+(.+)$")) {
        if (!__pytra_truthy(text.startswith("from "))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_str(__pytra_slice(text, Int64(5), __pytra_len(text)))
        var i: Int64 = __pytra_int(rest.find(" import "))
        if (__pytra_int(i) < __pytra_int(Int64(0))) {
            return __pytra_any_default()
        }
        var mod: String = __pytra_slice(rest, Int64(0), i).strip()
        var sym: String = __pytra_slice(rest, (i + Int64(8)), __pytra_len(rest)).strip()
        if ((!_is_dotted_ident(mod)) || (__pytra_str(sym) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        return Match(text, [mod, sym])
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$")) {
        var parts: [Any] = text.split(" as ")
        if (__pytra_int(__pytra_len(parts)) == __pytra_int(Int64(1))) {
            var name: String = __pytra_str(__pytra_getIndex(parts, Int64(0))).strip()
            if (!_is_ident(name)) {
                return __pytra_any_default()
            }
            return Match(text, [name, ""])
        }
        if (__pytra_int(__pytra_len(parts)) == __pytra_int(Int64(2))) {
            var name: String = __pytra_str(__pytra_getIndex(parts, Int64(0))).strip()
            var alias: String = __pytra_str(__pytra_getIndex(parts, Int64(1))).strip()
            if ((!_is_ident(name)) || (!_is_ident(alias))) {
                return __pytra_any_default()
            }
            return Match(text, [name, alias])
        }
        return __pytra_any_default()
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$")) {
        var c: Any = text.find(":")
        if (__pytra_int(c) <= __pytra_int(Int64(0))) {
            return __pytra_any_default()
        }
        var name: String = __pytra_slice(text, Int64(0), c).strip()
        var rhs: String = __pytra_str(__pytra_slice(text, (c + Int64(1)), __pytra_len(text)))
        var eq: Int64 = __pytra_int(rhs.find("="))
        if (__pytra_int(eq) < __pytra_int(Int64(0))) {
            return __pytra_any_default()
        }
        var ann: String = __pytra_slice(rhs, Int64(0), eq).strip()
        var expr: String = __pytra_slice(rhs, (eq + Int64(1)), __pytra_len(rhs)).strip()
        if ((!_is_ident(name)) || (__pytra_str(ann) == __pytra_str("")) || (__pytra_str(expr) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        return Match(text, [name, ann, expr])
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$")) {
        var eq: Int64 = __pytra_int(text.find("="))
        if (__pytra_int(eq) < __pytra_int(Int64(0))) {
            return __pytra_any_default()
        }
        var name: String = __pytra_slice(text, Int64(0), eq).strip()
        var expr: String = __pytra_slice(text, (eq + Int64(1)), __pytra_len(text)).strip()
        if ((!_is_ident(name)) || (__pytra_str(expr) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        return Match(text, [name, expr])
    }
    fatalError("pytra raise")
    return __pytra_any_default()
}

func sub(_ pattern: String, _ repl: String, _ text: String, _ flags: Int64) -> String {
    if (__pytra_str(pattern) == __pytra_str("\\s+")) {
        var out: [Any] = __pytra_as_list([])
        var in_ws: Bool = false
        do {
            let __iter_0 = __pytra_as_list(text)
            var __i_1: Int64 = 0
            while __i_1 < Int64(__iter_0.count) {
                let ch: String = __pytra_str(__iter_0[Int(__i_1)])
                if __pytra_truthy(ch.isspace()) {
                    if (!in_ws) {
                        out.append(repl)
                        in_ws = true
                    }
                } else {
                    out.append(ch)
                    in_ws = false
                }
                __i_1 += 1
            }
        }
        return __pytra_str("".join(out))
    }
    if (__pytra_str(pattern) == __pytra_str("\\s+#.*$")) {
        var i: Int64 = Int64(0)
        while (__pytra_int(i) < __pytra_int(__pytra_len(text))) {
            if __pytra_truthy(__pytra_str(__pytra_getIndex(text, i)).isspace()) {
                var j: Int64 = (i + Int64(1))
                while ((__pytra_int(j) < __pytra_int(__pytra_len(text))) && __pytra_truthy(__pytra_str(__pytra_getIndex(text, j)).isspace())) {
                    j += Int64(1)
                }
                if ((__pytra_int(j) < __pytra_int(__pytra_len(text))) && (__pytra_str(__pytra_getIndex(text, j)) == __pytra_str("#"))) {
                    return (__pytra_str(__pytra_slice(text, Int64(0), i)) + __pytra_str(repl))
                }
            }
            i += Int64(1)
        }
        return text
    }
    if (__pytra_str(pattern) == __pytra_str("[^0-9A-Za-z_]")) {
        var out: [Any] = __pytra_as_list([])
        do {
            let __iter_2 = __pytra_as_list(text)
            var __i_3: Int64 = 0
            while __i_3 < Int64(__iter_2.count) {
                let ch: String = __pytra_str(__iter_2[Int(__i_3)])
                if (__pytra_truthy(ch.isalnum()) || (__pytra_str(ch) == __pytra_str("_"))) {
                    out.append(ch)
                } else {
                    out.append(repl)
                }
                __i_3 += 1
            }
        }
        return __pytra_str("".join(out))
    }
    fatalError("pytra raise")
    return ""
}
