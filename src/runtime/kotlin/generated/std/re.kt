// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/re.py
// generated-by: tools/gen_runtime_from_manifest.py



fun __pytra_is_Match(v: Any?): Boolean {
    return v is Match
}

fun __pytra_as_Match(v: Any?): Match {
    return if (v is Match) v else Match()
}

open class Match() {
    var _text: String = ""
    var _groups: MutableList<Any?> = mutableListOf()

    constructor(text: String, groups: MutableList<Any?>) : this() {
        this._text = text
        this._groups = groups
    }

    open fun group(idx: Long): String {
        if ((__pytra_int(idx) == __pytra_int(0L))) {
            return __pytra_str(this._text)
        }
        if (((__pytra_int(idx) < __pytra_int(0L)) || (__pytra_int(idx) > __pytra_int(__pytra_len(this._groups))))) {
            throw RuntimeException(__pytra_str(IndexError("group index out of range")))
        }
        return __pytra_str(__pytra_get_index(this._groups, (idx - 1L)))
    }
}

fun group(m: Any?, idx: Long): String {
    if ((__pytra_float(m) == __pytra_float(__pytra_any_default()))) {
        return ""
    }
    var mm: Match = __pytra_as_Match(m)
    return mm.group(idx)
}

fun strip_group(m: Any?, idx: Long): String {
    return group(m, idx).strip()
}

fun _is_ident(s: String): Boolean {
    if ((__pytra_str(s) == __pytra_str(""))) {
        return false
    }
    var h: String = __pytra_str(__pytra_slice(s, 0L, 1L))
    var is_head_alpha: Boolean = (((__pytra_str("a") <= __pytra_str(h)) && (__pytra_str(h) <= __pytra_str("z"))) || ((__pytra_str("A") <= __pytra_str(h)) && (__pytra_str(h) <= __pytra_str("Z"))))
    if ((!(is_head_alpha || (__pytra_str(h) == __pytra_str("_"))))) {
        return false
    }
    val __iter_0 = __pytra_as_list(__pytra_slice(s, 1L, __pytra_len(s)))
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val ch: String = __pytra_str(__iter_0[__i_1.toInt()])
        var is_alpha: Boolean = (((__pytra_str("a") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("z"))) || ((__pytra_str("A") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("Z"))))
        var is_digit: Boolean = ((__pytra_str("0") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("9")))
        if ((!(is_alpha || is_digit || (__pytra_str(ch) == __pytra_str("_"))))) {
            return false
        }
        __i_1 += 1L
    }
    return true
}

fun _is_dotted_ident(s: String): Boolean {
    if ((__pytra_str(s) == __pytra_str(""))) {
        return false
    }
    var part: String = ""
    val __iter_0 = __pytra_as_list(s)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val ch: String = __pytra_str(__iter_0[__i_1.toInt()])
        if ((__pytra_str(ch) == __pytra_str("."))) {
            if ((!_is_ident(part))) {
                return false
            }
            part = ""
            __i_1 += 1L
            continue
        }
        part += ch
        __i_1 += 1L
    }
    if ((!_is_ident(part))) {
        return false
    }
    if ((__pytra_str(part) == __pytra_str(""))) {
        return false
    }
    return true
}

fun _strip_suffix_colon(s: String): String {
    var t: String = s.rstrip()
    if ((__pytra_int(__pytra_len(t)) == __pytra_int(0L))) {
        return ""
    }
    if ((__pytra_str(__pytra_slice(t, (-1L), __pytra_len(t))) != __pytra_str(":"))) {
        return ""
    }
    return __pytra_str(__pytra_slice(t, 0L, (-1L)))
}

fun _is_space_ch(ch: String): Boolean {
    if ((__pytra_str(ch) == __pytra_str(" "))) {
        return true
    }
    if ((__pytra_str(ch) == __pytra_str("	"))) {
        return true
    }
    if ((__pytra_str(ch) == __pytra_str("
"))) {
        return true
    }
    if ((__pytra_str(ch) == __pytra_str("\n"))) {
        return true
    }
    return false
}

fun _is_alnum_or_underscore(ch: String): Boolean {
    var is_alpha: Boolean = (((__pytra_str("a") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("z"))) || ((__pytra_str("A") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("Z"))))
    var is_digit: Boolean = ((__pytra_str("0") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("9")))
    if ((is_alpha || is_digit)) {
        return true
    }
    return (__pytra_str(ch) == __pytra_str("_"))
}

fun _skip_spaces(t: String, i: Long): Long {
    while ((__pytra_int(i) < __pytra_int(__pytra_len(t)))) {
        if ((!_is_space_ch(__pytra_slice(t, i, (i + 1L))))) {
            return i
        }
        i += 1L
    }
    return i
}

fun match(pattern: String, text: String, flags: Long): Any? {
    if ((__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\[(.*)\\]$"))) {
        if ((!__pytra_truthy(text.endswith("]")))) {
            return __pytra_any_default()
        }
        var i: Any? = text.find("[")
        if ((__pytra_int(i) <= __pytra_int(0L))) {
            return __pytra_any_default()
        }
        var head: String = __pytra_str(__pytra_slice(text, 0L, i))
        if ((!_is_ident(head))) {
            return __pytra_any_default()
        }
        return Match(text, mutableListOf(head, __pytra_slice(text, (i + 1L), (-1L))))
    }
    if ((__pytra_str(pattern) == __pytra_str("^def\\s+([A-Za-z_][A-Za-z0-9_]*)\\((.*)\\)\\s*(?:->\\s*(.+)\\s*)?:\\s*$"))) {
        var t: String = _strip_suffix_colon(text)
        if ((__pytra_str(t) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        var i: Long = 0L
        if ((!__pytra_truthy(t.startswith("def")))) {
            return __pytra_any_default()
        }
        i = 3L
        if (((__pytra_int(i) >= __pytra_int(__pytra_len(t))) || (!_is_space_ch(__pytra_slice(t, i, (i + 1L)))))) {
            return __pytra_any_default()
        }
        i = _skip_spaces(t, i)
        var j: Long = i
        while (((__pytra_int(j) < __pytra_int(__pytra_len(t))) && _is_alnum_or_underscore(__pytra_slice(t, j, (j + 1L))))) {
            j += 1L
        }
        var name: String = __pytra_str(__pytra_slice(t, i, j))
        if ((!_is_ident(name))) {
            return __pytra_any_default()
        }
        var k: Long = j
        k = _skip_spaces(t, k)
        if (((__pytra_int(k) >= __pytra_int(__pytra_len(t))) || (__pytra_str(__pytra_slice(t, k, (k + 1L))) != __pytra_str("(")))) {
            return __pytra_any_default()
        }
        var r: Long = __pytra_int(t.rfind(")"))
        if ((__pytra_int(r) <= __pytra_int(k))) {
            return __pytra_any_default()
        }
        var args: String = __pytra_str(__pytra_slice(t, (k + 1L), r))
        var tail: String = __pytra_slice(t, (r + 1L), __pytra_len(t)).strip()
        if ((__pytra_str(tail) == __pytra_str(""))) {
            return Match(text, mutableListOf(name, args, ""))
        }
        if ((!__pytra_truthy(tail.startswith("->")))) {
            return __pytra_any_default()
        }
        var ret: String = __pytra_slice(tail, 2L, __pytra_len(tail)).strip()
        if ((__pytra_str(ret) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        return Match(text, mutableListOf(name, args, ret))
    }
    if ((__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)(?:\\s*=\\s*(.+))?$"))) {
        var c: Any? = text.find(":")
        if ((__pytra_int(c) <= __pytra_int(0L))) {
            return __pytra_any_default()
        }
        var name: String = __pytra_slice(text, 0L, c).strip()
        if ((!_is_ident(name))) {
            return __pytra_any_default()
        }
        var rhs: String = __pytra_str(__pytra_slice(text, (c + 1L), __pytra_len(text)))
        var eq: Any? = rhs.find("=")
        if ((__pytra_int(eq) < __pytra_int(0L))) {
            var ann: String = rhs.strip()
            if ((__pytra_str(ann) == __pytra_str(""))) {
                return __pytra_any_default()
            }
            return Match(text, mutableListOf(name, ann, ""))
        }
        var ann: String = __pytra_slice(rhs, 0L, eq).strip()
        var val_: String = __pytra_slice(rhs, (eq + 1L), __pytra_len(rhs)).strip()
        if (((__pytra_str(ann) == __pytra_str("")) || (__pytra_str(val_) == __pytra_str("")))) {
            return __pytra_any_default()
        }
        return Match(text, mutableListOf(name, ann, val_))
    }
    if ((__pytra_str(pattern) == __pytra_str("^[A-Za-z_][A-Za-z0-9_]*$"))) {
        if (_is_ident(text)) {
            return Match(text, mutableListOf<Any?>())
        }
        return __pytra_any_default()
    }
    if ((__pytra_str(pattern) == __pytra_str("^class\\s+([A-Za-z_][A-Za-z0-9_]*)(?:\\(([A-Za-z_][A-Za-z0-9_]*)\\))?\\s*:\\s*$"))) {
        var t: String = _strip_suffix_colon(text)
        if ((__pytra_str(t) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        if ((!__pytra_truthy(t.startswith("class")))) {
            return __pytra_any_default()
        }
        var i: Long = 5L
        if (((__pytra_int(i) >= __pytra_int(__pytra_len(t))) || (!_is_space_ch(__pytra_slice(t, i, (i + 1L)))))) {
            return __pytra_any_default()
        }
        i = _skip_spaces(t, i)
        var j: Long = i
        while (((__pytra_int(j) < __pytra_int(__pytra_len(t))) && _is_alnum_or_underscore(__pytra_slice(t, j, (j + 1L))))) {
            j += 1L
        }
        var name: String = __pytra_str(__pytra_slice(t, i, j))
        if ((!_is_ident(name))) {
            return __pytra_any_default()
        }
        var tail: String = __pytra_slice(t, j, __pytra_len(t)).strip()
        if ((__pytra_str(tail) == __pytra_str(""))) {
            return Match(text, mutableListOf(name, ""))
        }
        if ((!(__pytra_truthy(tail.startswith("(")) && __pytra_truthy(tail.endswith(")"))))) {
            return __pytra_any_default()
        }
        var base: String = __pytra_slice(tail, 1L, (-1L)).strip()
        if ((!_is_ident(base))) {
            return __pytra_any_default()
        }
        return Match(text, mutableListOf(name, base))
    }
    if ((__pytra_str(pattern) == __pytra_str("^(any|all)\\((.+)\\)$"))) {
        if ((__pytra_truthy(text.startswith("any(")) && __pytra_truthy(text.endswith(")")) && (__pytra_int(__pytra_len(text)) > __pytra_int(5L)))) {
            return Match(text, mutableListOf("any", __pytra_slice(text, 4L, (-1L))))
        }
        if ((__pytra_truthy(text.startswith("all(")) && __pytra_truthy(text.endswith(")")) && (__pytra_int(__pytra_len(text)) > __pytra_int(5L)))) {
            return Match(text, mutableListOf("all", __pytra_slice(text, 4L, (-1L))))
        }
        return __pytra_any_default()
    }
    if ((__pytra_str(pattern) == __pytra_str("^\\[\\s*([A-Za-z_][A-Za-z0-9_]*)\\s+for\\s+([A-Za-z_][A-Za-z0-9_]*)\\s+in\\s+(.+)\\]$"))) {
        if ((!(__pytra_truthy(text.startswith("[")) && __pytra_truthy(text.endswith("]"))))) {
            return __pytra_any_default()
        }
        var inner: String = __pytra_slice(text, 1L, (-1L)).strip()
        var m1: String = " for "
        var m2: String = " in "
        var i: Long = __pytra_int(inner.find(m1))
        if ((__pytra_int(i) < __pytra_int(0L))) {
            return __pytra_any_default()
        }
        var expr: String = __pytra_slice(inner, 0L, i).strip()
        var rest: String = __pytra_str(__pytra_slice(inner, (i + __pytra_len(m1)), __pytra_len(inner)))
        var j: Long = __pytra_int(rest.find(m2))
        if ((__pytra_int(j) < __pytra_int(0L))) {
            return __pytra_any_default()
        }
        var var_: String = __pytra_slice(rest, 0L, j).strip()
        var it: String = __pytra_slice(rest, (j + __pytra_len(m2)), __pytra_len(rest)).strip()
        if (((!_is_ident(expr)) || (!_is_ident(var_)) || (__pytra_str(it) == __pytra_str("")))) {
            return __pytra_any_default()
        }
        return Match(text, mutableListOf(expr, var_, it))
    }
    if ((__pytra_str(pattern) == __pytra_str("^for\\s+(.+)\\s+in\\s+(.+):$"))) {
        var t: String = _strip_suffix_colon(text)
        if (((__pytra_str(t) == __pytra_str("")) || (!__pytra_truthy(t.startswith("for"))))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_slice(t, 3L, __pytra_len(t)).strip()
        var i: Long = __pytra_int(rest.find(" in "))
        if ((__pytra_int(i) < __pytra_int(0L))) {
            return __pytra_any_default()
        }
        var left: String = __pytra_slice(rest, 0L, i).strip()
        var right: String = __pytra_slice(rest, (i + 4L), __pytra_len(rest)).strip()
        if (((__pytra_str(left) == __pytra_str("")) || (__pytra_str(right) == __pytra_str("")))) {
            return __pytra_any_default()
        }
        return Match(text, mutableListOf(left, right))
    }
    if ((__pytra_str(pattern) == __pytra_str("^with\\s+(.+)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$"))) {
        var t: String = _strip_suffix_colon(text)
        if (((__pytra_str(t) == __pytra_str("")) || (!__pytra_truthy(t.startswith("with"))))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_slice(t, 4L, __pytra_len(t)).strip()
        var i: Long = __pytra_int(rest.rfind(" as "))
        if ((__pytra_int(i) < __pytra_int(0L))) {
            return __pytra_any_default()
        }
        var expr: String = __pytra_slice(rest, 0L, i).strip()
        var name: String = __pytra_slice(rest, (i + 4L), __pytra_len(rest)).strip()
        if (((__pytra_str(expr) == __pytra_str("")) || (!_is_ident(name)))) {
            return __pytra_any_default()
        }
        return Match(text, mutableListOf(expr, name))
    }
    if ((__pytra_str(pattern) == __pytra_str("^except\\s+(.+?)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$"))) {
        var t: String = _strip_suffix_colon(text)
        if (((__pytra_str(t) == __pytra_str("")) || (!__pytra_truthy(t.startswith("except"))))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_slice(t, 6L, __pytra_len(t)).strip()
        var i: Long = __pytra_int(rest.rfind(" as "))
        if ((__pytra_int(i) < __pytra_int(0L))) {
            return __pytra_any_default()
        }
        var exc: String = __pytra_slice(rest, 0L, i).strip()
        var name: String = __pytra_slice(rest, (i + 4L), __pytra_len(rest)).strip()
        if (((__pytra_str(exc) == __pytra_str("")) || (!_is_ident(name)))) {
            return __pytra_any_default()
        }
        return Match(text, mutableListOf(exc, name))
    }
    if ((__pytra_str(pattern) == __pytra_str("^except\\s+(.+?)\\s*:\\s*$"))) {
        var t: String = _strip_suffix_colon(text)
        if (((__pytra_str(t) == __pytra_str("")) || (!__pytra_truthy(t.startswith("except"))))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_slice(t, 6L, __pytra_len(t)).strip()
        if ((__pytra_str(rest) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        return Match(text, mutableListOf(rest))
    }
    if ((__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*(.+)$"))) {
        var c: Any? = text.find(":")
        if ((__pytra_int(c) <= __pytra_int(0L))) {
            return __pytra_any_default()
        }
        var target: String = __pytra_slice(text, 0L, c).strip()
        var ann: String = __pytra_slice(text, (c + 1L), __pytra_len(text)).strip()
        if (((__pytra_str(ann) == __pytra_str("")) || (!_is_dotted_ident(target)))) {
            return __pytra_any_default()
        }
        return Match(text, mutableListOf(target, ann))
    }
    if ((__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$"))) {
        var c: Any? = text.find(":")
        if ((__pytra_int(c) <= __pytra_int(0L))) {
            return __pytra_any_default()
        }
        var target: String = __pytra_slice(text, 0L, c).strip()
        var rhs: String = __pytra_str(__pytra_slice(text, (c + 1L), __pytra_len(text)))
        var eq: Long = __pytra_int(rhs.find("="))
        if ((__pytra_int(eq) < __pytra_int(0L))) {
            return __pytra_any_default()
        }
        var ann: String = __pytra_slice(rhs, 0L, eq).strip()
        var expr: String = __pytra_slice(rhs, (eq + 1L), __pytra_len(rhs)).strip()
        if (((!_is_dotted_ident(target)) || (__pytra_str(ann) == __pytra_str("")) || (__pytra_str(expr) == __pytra_str("")))) {
            return __pytra_any_default()
        }
        return Match(text, mutableListOf(target, ann, expr))
    }
    if ((__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*(\\+=|-=|\\*=|/=|//=|%=|&=|\\|=|\\^=|<<=|>>=)\\s*(.+)$"))) {
        var ops: MutableList<Any?> = __pytra_as_list(mutableListOf("<<=", ">>=", "+=", "-=", "*=", "/=", "//=", "%=", "&=", "|=", "^="))
        var op_pos: Long = __pytra_int(-1L)
        var op_txt: String = ""
        val __iter_0 = __pytra_as_list(ops)
        var __i_1: Long = 0L
        while (__i_1 < __iter_0.size.toLong()) {
            val op: String = __pytra_str(__iter_0[__i_1.toInt()])
            var p: Any? = text.find(op)
            if (((__pytra_int(p) >= __pytra_int(0L)) && ((__pytra_int(op_pos) < __pytra_int(0L)) || (__pytra_int(p) < __pytra_int(op_pos))))) {
                op_pos = __pytra_int(p)
                op_txt = op
            }
            __i_1 += 1L
        }
        if ((__pytra_int(op_pos) < __pytra_int(0L))) {
            return __pytra_any_default()
        }
        var left: String = __pytra_slice(text, 0L, op_pos).strip()
        var right: String = __pytra_slice(text, (op_pos + __pytra_len(op_txt)), __pytra_len(text)).strip()
        if (((__pytra_str(right) == __pytra_str("")) || (!_is_dotted_ident(left)))) {
            return __pytra_any_default()
        }
        return Match(text, mutableListOf(left, op_txt, right))
    }
    if ((__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\s*,\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$"))) {
        var eq: Long = __pytra_int(text.find("="))
        if ((__pytra_int(eq) < __pytra_int(0L))) {
            return __pytra_any_default()
        }
        var left: String = __pytra_str(__pytra_slice(text, 0L, eq))
        var right: String = __pytra_slice(text, (eq + 1L), __pytra_len(text)).strip()
        if ((__pytra_str(right) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        var c: Long = __pytra_int(left.find(","))
        if ((__pytra_int(c) < __pytra_int(0L))) {
            return __pytra_any_default()
        }
        var a: String = __pytra_slice(left, 0L, c).strip()
        var b: String = __pytra_slice(left, (c + 1L), __pytra_len(left)).strip()
        if (((!_is_ident(a)) || (!_is_ident(b)))) {
            return __pytra_any_default()
        }
        return Match(text, mutableListOf(a, b, right))
    }
    if ((__pytra_str(pattern) == __pytra_str("^if\\s+__name__\\s*==\\s*[\\\"']__main__[\\\"']\\s*:\\s*$"))) {
        var t: String = _strip_suffix_colon(text)
        if ((__pytra_str(t) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        var rest: String = t.strip()
        if ((!__pytra_truthy(rest.startswith("if")))) {
            return __pytra_any_default()
        }
        rest = __pytra_slice(rest, 2L, __pytra_len(rest)).strip()
        if ((!__pytra_truthy(rest.startswith("__name__")))) {
            return __pytra_any_default()
        }
        rest = __pytra_slice(rest, __pytra_len("__name__"), __pytra_len(rest)).strip()
        if ((!__pytra_truthy(rest.startswith("==")))) {
            return __pytra_any_default()
        }
        rest = __pytra_slice(rest, 2L, __pytra_len(rest)).strip()
        if ((__pytra_contains(__pytra_any_default(), rest))) {
            return Match(text, mutableListOf<Any?>())
        }
        return __pytra_any_default()
    }
    if ((__pytra_str(pattern) == __pytra_str("^import\\s+(.+)$"))) {
        if ((!__pytra_truthy(text.startswith("import")))) {
            return __pytra_any_default()
        }
        if ((__pytra_int(__pytra_len(text)) <= __pytra_int(6L))) {
            return __pytra_any_default()
        }
        if ((!_is_space_ch(__pytra_slice(text, 6L, 7L)))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_slice(text, 7L, __pytra_len(text)).strip()
        if ((__pytra_str(rest) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        return Match(text, mutableListOf(rest))
    }
    if ((__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_\\.]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$"))) {
        var parts: MutableList<Any?> = text.split(" as ")
        if ((__pytra_int(__pytra_len(parts)) == __pytra_int(1L))) {
            var name: String = __pytra_str(__pytra_get_index(parts, 0L)).strip()
            if ((!_is_dotted_ident(name))) {
                return __pytra_any_default()
            }
            return Match(text, mutableListOf(name, ""))
        }
        if ((__pytra_int(__pytra_len(parts)) == __pytra_int(2L))) {
            var name: String = __pytra_str(__pytra_get_index(parts, 0L)).strip()
            var alias: String = __pytra_str(__pytra_get_index(parts, 1L)).strip()
            if (((!_is_dotted_ident(name)) || (!_is_ident(alias)))) {
                return __pytra_any_default()
            }
            return Match(text, mutableListOf(name, alias))
        }
        return __pytra_any_default()
    }
    if ((__pytra_str(pattern) == __pytra_str("^from\\s+([A-Za-z_][A-Za-z0-9_\\.]*)\\s+import\\s+(.+)$"))) {
        if ((!__pytra_truthy(text.startswith("from ")))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_str(__pytra_slice(text, 5L, __pytra_len(text)))
        var i: Long = __pytra_int(rest.find(" import "))
        if ((__pytra_int(i) < __pytra_int(0L))) {
            return __pytra_any_default()
        }
        var mod: String = __pytra_slice(rest, 0L, i).strip()
        var sym: String = __pytra_slice(rest, (i + 8L), __pytra_len(rest)).strip()
        if (((!_is_dotted_ident(mod)) || (__pytra_str(sym) == __pytra_str("")))) {
            return __pytra_any_default()
        }
        return Match(text, mutableListOf(mod, sym))
    }
    if ((__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$"))) {
        var parts: MutableList<Any?> = text.split(" as ")
        if ((__pytra_int(__pytra_len(parts)) == __pytra_int(1L))) {
            var name: String = __pytra_str(__pytra_get_index(parts, 0L)).strip()
            if ((!_is_ident(name))) {
                return __pytra_any_default()
            }
            return Match(text, mutableListOf(name, ""))
        }
        if ((__pytra_int(__pytra_len(parts)) == __pytra_int(2L))) {
            var name: String = __pytra_str(__pytra_get_index(parts, 0L)).strip()
            var alias: String = __pytra_str(__pytra_get_index(parts, 1L)).strip()
            if (((!_is_ident(name)) || (!_is_ident(alias)))) {
                return __pytra_any_default()
            }
            return Match(text, mutableListOf(name, alias))
        }
        return __pytra_any_default()
    }
    if ((__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$"))) {
        var c: Any? = text.find(":")
        if ((__pytra_int(c) <= __pytra_int(0L))) {
            return __pytra_any_default()
        }
        var name: String = __pytra_slice(text, 0L, c).strip()
        var rhs: String = __pytra_str(__pytra_slice(text, (c + 1L), __pytra_len(text)))
        var eq: Long = __pytra_int(rhs.find("="))
        if ((__pytra_int(eq) < __pytra_int(0L))) {
            return __pytra_any_default()
        }
        var ann: String = __pytra_slice(rhs, 0L, eq).strip()
        var expr: String = __pytra_slice(rhs, (eq + 1L), __pytra_len(rhs)).strip()
        if (((!_is_ident(name)) || (__pytra_str(ann) == __pytra_str("")) || (__pytra_str(expr) == __pytra_str("")))) {
            return __pytra_any_default()
        }
        return Match(text, mutableListOf(name, ann, expr))
    }
    if ((__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$"))) {
        var eq: Long = __pytra_int(text.find("="))
        if ((__pytra_int(eq) < __pytra_int(0L))) {
            return __pytra_any_default()
        }
        var name: String = __pytra_slice(text, 0L, eq).strip()
        var expr: String = __pytra_slice(text, (eq + 1L), __pytra_len(text)).strip()
        if (((!_is_ident(name)) || (__pytra_str(expr) == __pytra_str("")))) {
            return __pytra_any_default()
        }
        return Match(text, mutableListOf(name, expr))
    }
    throw RuntimeException(__pytra_str(__pytra_any_default()))
    return null
}

fun sub(pattern: String, repl: String, text: String, flags: Long): String {
    if ((__pytra_str(pattern) == __pytra_str("\\s+"))) {
        var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
        var in_ws: Boolean = false
        val __iter_0 = __pytra_as_list(text)
        var __i_1: Long = 0L
        while (__i_1 < __iter_0.size.toLong()) {
            val ch: String = __pytra_str(__iter_0[__i_1.toInt()])
            if (__pytra_truthy(ch.isspace())) {
                if ((!in_ws)) {
                    out.add(repl)
                    in_ws = true
                }
            } else {
                out.add(ch)
                in_ws = false
            }
            __i_1 += 1L
        }
        return __pytra_str("".join(out))
    }
    if ((__pytra_str(pattern) == __pytra_str("\\s+#.*$"))) {
        var i: Long = 0L
        while ((__pytra_int(i) < __pytra_int(__pytra_len(text)))) {
            if (__pytra_truthy(__pytra_str(__pytra_get_index(text, i)).isspace())) {
                var j: Long = (i + 1L)
                while (((__pytra_int(j) < __pytra_int(__pytra_len(text))) && __pytra_truthy(__pytra_str(__pytra_get_index(text, j)).isspace()))) {
                    j += 1L
                }
                if (((__pytra_int(j) < __pytra_int(__pytra_len(text))) && (__pytra_str(__pytra_get_index(text, j)) == __pytra_str("#")))) {
                    return (__pytra_str(__pytra_slice(text, 0L, i)) + __pytra_str(repl))
                }
            }
            i += 1L
        }
        return text
    }
    if ((__pytra_str(pattern) == __pytra_str("[^0-9A-Za-z_]"))) {
        var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
        val __iter_2 = __pytra_as_list(text)
        var __i_3: Long = 0L
        while (__i_3 < __iter_2.size.toLong()) {
            val ch: String = __pytra_str(__iter_2[__i_3.toInt()])
            if ((__pytra_truthy(ch.isalnum()) || (__pytra_str(ch) == __pytra_str("_")))) {
                out.add(ch)
            } else {
                out.add(repl)
            }
            __i_3 += 1L
        }
        return __pytra_str("".join(out))
    }
    throw RuntimeException(__pytra_str(__pytra_any_default()))
    return ""
}
