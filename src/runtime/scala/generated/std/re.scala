// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/re.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def __pytra_is_Match(v: Any): Boolean = {
    v.isInstanceOf[Match]
}

def __pytra_as_Match(v: Any): Match = {
    v match {
        case obj: Match => obj
        case _ => new Match()
    }
}

class Match() {
    var _text: String = ""
    var _groups: mutable.ArrayBuffer[String] = mutable.ArrayBuffer[String]()

    def this(text: String, groups: mutable.ArrayBuffer[String]) = {
        this()
        this._text = text
        this._groups = groups
    }

    def group(idx: Long): String = {
        if (idx == 0L) {
            return __pytra_str(this._text)
        }
        if ((idx < 0L) || (idx > __pytra_len(this._groups))) {
            throw new RuntimeException(__pytra_str(IndexError("group index out of range")))
        }
        return __pytra_str(__pytra_get_index(this._groups, idx - 1L))
    }
}

def group(m: Any, idx: Long): String = {
    if (__pytra_float(m) == __pytra_float(__pytra_any_default())) {
        return ""
    }
    var mm: Match = __pytra_as_Match(m)
    return mm.group(idx)
}

def strip_group(m: Any, idx: Long): String = {
    return __pytra_strip(group(m, idx))
}

def _is_ident(s: String): Boolean = {
    if (__pytra_str(s) == __pytra_str("")) {
        return false
    }
    var h: String = __pytra_str(__pytra_slice(s, 0L, 1L))
    var is_head_alpha: Boolean = (((__pytra_str("a") <= __pytra_str(h)) && (__pytra_str(h) <= __pytra_str("z"))) || ((__pytra_str("A") <= __pytra_str(h)) && (__pytra_str(h) <= __pytra_str("Z"))))
    if (!(is_head_alpha || (__pytra_str(h) == __pytra_str("_")))) {
        return false
    }
    val __iter_0 = __pytra_as_list(__pytra_slice(s, 1L, __pytra_len(s)))
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong) {
        val ch: String = __pytra_str(__iter_0(__i_1.toInt))
        var is_alpha: Boolean = (((__pytra_str("a") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("z"))) || ((__pytra_str("A") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("Z"))))
        var is_digit: Boolean = ((__pytra_str("0") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("9")))
        if (!(is_alpha || is_digit || (__pytra_str(ch) == __pytra_str("_")))) {
            return false
        }
        __i_1 += 1L
    }
    return true
}

def _is_dotted_ident(s: String): Boolean = {
    if (__pytra_str(s) == __pytra_str("")) {
        return false
    }
    var part: String = ""
    boundary:
        given __breakLabel_2: boundary.Label[Unit] = summon[boundary.Label[Unit]]
        val __iter_0 = __pytra_as_list(s)
        var __i_1: Long = 0L
        while (__i_1 < __iter_0.size.toLong) {
            boundary:
                given __continueLabel_3: boundary.Label[Unit] = summon[boundary.Label[Unit]]
                val ch: String = __pytra_str(__iter_0(__i_1.toInt))
                if (__pytra_str(ch) == __pytra_str(".")) {
                    if (!_is_ident(part)) {
                        return false
                    }
                    part = ""
                    break(())(using __continueLabel_3)
                }
                part += ch
            __i_1 += 1L
        }
    if (!_is_ident(part)) {
        return false
    }
    if (__pytra_str(part) == __pytra_str("")) {
        return false
    }
    return true
}

def _strip_suffix_colon(s: String): String = {
    var t: String = __pytra_rstrip(s)
    if (__pytra_len(t) == 0L) {
        return ""
    }
    if (__pytra_str(__pytra_slice(t, (-1L), __pytra_len(t))) != __pytra_str(":")) {
        return ""
    }
    return __pytra_str(__pytra_slice(t, 0L, (-1L)))
}

def _is_space_ch(ch: String): Boolean = {
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

def _is_alnum_or_underscore(ch: String): Boolean = {
    var is_alpha: Boolean = (((__pytra_str("a") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("z"))) || ((__pytra_str("A") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("Z"))))
    var is_digit: Boolean = ((__pytra_str("0") <= __pytra_str(ch)) && (__pytra_str(ch) <= __pytra_str("9")))
    if (is_alpha || is_digit) {
        return true
    }
    return (__pytra_str(ch) == __pytra_str("_"))
}

def _skip_spaces(t: String, i: Long): Long = {
    while (i < __pytra_len(t)) {
        if (!_is_space_ch(__pytra_slice(t, i, i + 1L))) {
            return i
        }
        i += 1L
    }
    return i
}

def py_match(pattern: String, text: String, flags: Long): Any = {
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\[(.*)\\]$")) {
        if (!__pytra_truthy(__pytra_endswith(text, "]"))) {
            return __pytra_any_default()
        }
        var i: Any = __pytra_find(text, "[")
        if (__pytra_int(i) <= 0L) {
            return __pytra_any_default()
        }
        var head: String = __pytra_str(__pytra_slice(text, 0L, i))
        if (!_is_ident(head)) {
            return __pytra_any_default()
        }
        return new Match(text, mutable.ArrayBuffer[String](head, __pytra_slice(text, i + 1L, (-1L))))
    }
    if (__pytra_str(pattern) == __pytra_str("^def\\s+([A-Za-z_][A-Za-z0-9_]*)\\((.*)\\)\\s*(?:->\\s*(.+)\\s*)?:\\s*$")) {
        var t: String = _strip_suffix_colon(text)
        if (__pytra_str(t) == __pytra_str("")) {
            return __pytra_any_default()
        }
        var i: Long = 0L
        if (!__pytra_truthy(__pytra_startswith(t, "def"))) {
            return __pytra_any_default()
        }
        i = 3L
        if ((i >= __pytra_len(t)) || (!_is_space_ch(__pytra_slice(t, i, i + 1L)))) {
            return __pytra_any_default()
        }
        i = _skip_spaces(t, i)
        var j: Long = i
        while ((j < __pytra_len(t)) && _is_alnum_or_underscore(__pytra_slice(t, j, j + 1L))) {
            j += 1L
        }
        var name: String = __pytra_str(__pytra_slice(t, i, j))
        if (!_is_ident(name)) {
            return __pytra_any_default()
        }
        var k: Long = j
        k = _skip_spaces(t, k)
        if (((k >= __pytra_len(t)) || (__pytra_str(__pytra_slice(t, k, k + 1L)) != __pytra_str("(")))) {
            return __pytra_any_default()
        }
        var r: Long = __pytra_int(__pytra_rfind(t, ")"))
        if (r <= k) {
            return __pytra_any_default()
        }
        var args: String = __pytra_str(__pytra_slice(t, k + 1L, r))
        var tail: String = __pytra_strip(__pytra_slice(t, r + 1L, __pytra_len(t)))
        if (__pytra_str(tail) == __pytra_str("")) {
            return new Match(text, mutable.ArrayBuffer[String](name, args, ""))
        }
        if (!__pytra_truthy(__pytra_startswith(tail, "->"))) {
            return __pytra_any_default()
        }
        var ret: String = __pytra_strip(__pytra_slice(tail, 2L, __pytra_len(tail)))
        if (__pytra_str(ret) == __pytra_str("")) {
            return __pytra_any_default()
        }
        return new Match(text, mutable.ArrayBuffer[String](name, args, ret))
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)(?:\\s*=\\s*(.+))?$")) {
        var c: Any = __pytra_find(text, ":")
        if (__pytra_int(c) <= 0L) {
            return __pytra_any_default()
        }
        var name: String = __pytra_strip(__pytra_slice(text, 0L, c))
        if (!_is_ident(name)) {
            return __pytra_any_default()
        }
        var rhs: String = __pytra_str(__pytra_slice(text, c + 1L, __pytra_len(text)))
        var eq: Any = __pytra_find(rhs, "=")
        if (__pytra_int(eq) < 0L) {
            var ann: String = __pytra_strip(rhs)
            if (__pytra_str(ann) == __pytra_str("")) {
                return __pytra_any_default()
            }
            return new Match(text, mutable.ArrayBuffer[String](name, ann, ""))
        }
        var ann: String = __pytra_strip(__pytra_slice(rhs, 0L, eq))
        var py_val: String = __pytra_strip(__pytra_slice(rhs, eq + 1L, __pytra_len(rhs)))
        if ((__pytra_str(ann) == __pytra_str("")) || (__pytra_str(py_val) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        return new Match(text, mutable.ArrayBuffer[String](name, ann, py_val))
    }
    if (__pytra_str(pattern) == __pytra_str("^[A-Za-z_][A-Za-z0-9_]*$")) {
        if (_is_ident(text)) {
            return new Match(text, mutable.ArrayBuffer[Any]())
        }
        return __pytra_any_default()
    }
    if (__pytra_str(pattern) == __pytra_str("^class\\s+([A-Za-z_][A-Za-z0-9_]*)(?:\\(([A-Za-z_][A-Za-z0-9_]*)\\))?\\s*:\\s*$")) {
        var t: String = _strip_suffix_colon(text)
        if (__pytra_str(t) == __pytra_str("")) {
            return __pytra_any_default()
        }
        if (!__pytra_truthy(__pytra_startswith(t, "class"))) {
            return __pytra_any_default()
        }
        var i: Long = 5L
        if ((i >= __pytra_len(t)) || (!_is_space_ch(__pytra_slice(t, i, i + 1L)))) {
            return __pytra_any_default()
        }
        i = _skip_spaces(t, i)
        var j: Long = i
        while ((j < __pytra_len(t)) && _is_alnum_or_underscore(__pytra_slice(t, j, j + 1L))) {
            j += 1L
        }
        var name: String = __pytra_str(__pytra_slice(t, i, j))
        if (!_is_ident(name)) {
            return __pytra_any_default()
        }
        var tail: String = __pytra_strip(__pytra_slice(t, j, __pytra_len(t)))
        if (__pytra_str(tail) == __pytra_str("")) {
            return new Match(text, mutable.ArrayBuffer[String](name, ""))
        }
        if (!(__pytra_truthy(__pytra_startswith(tail, "(")) && __pytra_truthy(__pytra_endswith(tail, ")")))) {
            return __pytra_any_default()
        }
        var base: String = __pytra_strip(__pytra_slice(tail, 1L, (-1L)))
        if (!_is_ident(base)) {
            return __pytra_any_default()
        }
        return new Match(text, mutable.ArrayBuffer[String](name, base))
    }
    if (__pytra_str(pattern) == __pytra_str("^(any|all)\\((.+)\\)$")) {
        if (__pytra_truthy(__pytra_startswith(text, "any(")) && __pytra_truthy(__pytra_endswith(text, ")")) && (__pytra_len(text) > 5L)) {
            return new Match(text, mutable.ArrayBuffer[String]("any", __pytra_slice(text, 4L, (-1L))))
        }
        if (__pytra_truthy(__pytra_startswith(text, "all(")) && __pytra_truthy(__pytra_endswith(text, ")")) && (__pytra_len(text) > 5L)) {
            return new Match(text, mutable.ArrayBuffer[String]("all", __pytra_slice(text, 4L, (-1L))))
        }
        return __pytra_any_default()
    }
    if (__pytra_str(pattern) == __pytra_str("^\\[\\s*([A-Za-z_][A-Za-z0-9_]*)\\s+for\\s+([A-Za-z_][A-Za-z0-9_]*)\\s+in\\s+(.+)\\]$")) {
        if (!(__pytra_truthy(__pytra_startswith(text, "[")) && __pytra_truthy(__pytra_endswith(text, "]")))) {
            return __pytra_any_default()
        }
        var inner: String = __pytra_strip(__pytra_slice(text, 1L, (-1L)))
        var m1: String = " for "
        var m2: String = " in "
        var i: Long = __pytra_int(__pytra_find(inner, m1))
        if (i < 0L) {
            return __pytra_any_default()
        }
        var expr: String = __pytra_strip(__pytra_slice(inner, 0L, i))
        var rest: String = __pytra_str(__pytra_slice(inner, i + __pytra_len(m1), __pytra_len(inner)))
        var j: Long = __pytra_int(__pytra_find(rest, m2))
        if (j < 0L) {
            return __pytra_any_default()
        }
        var py_var: String = __pytra_strip(__pytra_slice(rest, 0L, j))
        var it: String = __pytra_strip(__pytra_slice(rest, j + __pytra_len(m2), __pytra_len(rest)))
        if ((!_is_ident(expr)) || (!_is_ident(py_var)) || (__pytra_str(it) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        return new Match(text, mutable.ArrayBuffer[String](expr, py_var, it))
    }
    if (__pytra_str(pattern) == __pytra_str("^for\\s+(.+)\\s+in\\s+(.+):$")) {
        var t: String = _strip_suffix_colon(text)
        if ((__pytra_str(t) == __pytra_str("")) || (!__pytra_truthy(__pytra_startswith(t, "for")))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_strip(__pytra_slice(t, 3L, __pytra_len(t)))
        var i: Long = __pytra_int(__pytra_find(rest, " in "))
        if (i < 0L) {
            return __pytra_any_default()
        }
        var left: String = __pytra_strip(__pytra_slice(rest, 0L, i))
        var right: String = __pytra_strip(__pytra_slice(rest, i + 4L, __pytra_len(rest)))
        if ((__pytra_str(left) == __pytra_str("")) || (__pytra_str(right) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        return new Match(text, mutable.ArrayBuffer[String](left, right))
    }
    if (__pytra_str(pattern) == __pytra_str("^with\\s+(.+)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$")) {
        var t: String = _strip_suffix_colon(text)
        if ((__pytra_str(t) == __pytra_str("")) || (!__pytra_truthy(__pytra_startswith(t, "with")))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_strip(__pytra_slice(t, 4L, __pytra_len(t)))
        var i: Long = __pytra_int(__pytra_rfind(rest, " as "))
        if (i < 0L) {
            return __pytra_any_default()
        }
        var expr: String = __pytra_strip(__pytra_slice(rest, 0L, i))
        var name: String = __pytra_strip(__pytra_slice(rest, i + 4L, __pytra_len(rest)))
        if ((__pytra_str(expr) == __pytra_str("")) || (!_is_ident(name))) {
            return __pytra_any_default()
        }
        return new Match(text, mutable.ArrayBuffer[String](expr, name))
    }
    if (__pytra_str(pattern) == __pytra_str("^except\\s+(.+?)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$")) {
        var t: String = _strip_suffix_colon(text)
        if ((__pytra_str(t) == __pytra_str("")) || (!__pytra_truthy(__pytra_startswith(t, "except")))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_strip(__pytra_slice(t, 6L, __pytra_len(t)))
        var i: Long = __pytra_int(__pytra_rfind(rest, " as "))
        if (i < 0L) {
            return __pytra_any_default()
        }
        var exc: String = __pytra_strip(__pytra_slice(rest, 0L, i))
        var name: String = __pytra_strip(__pytra_slice(rest, i + 4L, __pytra_len(rest)))
        if ((__pytra_str(exc) == __pytra_str("")) || (!_is_ident(name))) {
            return __pytra_any_default()
        }
        return new Match(text, mutable.ArrayBuffer[String](exc, name))
    }
    if (__pytra_str(pattern) == __pytra_str("^except\\s+(.+?)\\s*:\\s*$")) {
        var t: String = _strip_suffix_colon(text)
        if ((__pytra_str(t) == __pytra_str("")) || (!__pytra_truthy(__pytra_startswith(t, "except")))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_strip(__pytra_slice(t, 6L, __pytra_len(t)))
        if (__pytra_str(rest) == __pytra_str("")) {
            return __pytra_any_default()
        }
        return new Match(text, mutable.ArrayBuffer[String](rest))
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*(.+)$")) {
        var c: Any = __pytra_find(text, ":")
        if (__pytra_int(c) <= 0L) {
            return __pytra_any_default()
        }
        var target: String = __pytra_strip(__pytra_slice(text, 0L, c))
        var ann: String = __pytra_strip(__pytra_slice(text, c + 1L, __pytra_len(text)))
        if ((__pytra_str(ann) == __pytra_str("")) || (!_is_dotted_ident(target))) {
            return __pytra_any_default()
        }
        return new Match(text, mutable.ArrayBuffer[String](target, ann))
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$")) {
        var c: Any = __pytra_find(text, ":")
        if (__pytra_int(c) <= 0L) {
            return __pytra_any_default()
        }
        var target: String = __pytra_strip(__pytra_slice(text, 0L, c))
        var rhs: String = __pytra_str(__pytra_slice(text, c + 1L, __pytra_len(text)))
        var eq: Long = __pytra_int(__pytra_find(rhs, "="))
        if (eq < 0L) {
            return __pytra_any_default()
        }
        var ann: String = __pytra_strip(__pytra_slice(rhs, 0L, eq))
        var expr: String = __pytra_strip(__pytra_slice(rhs, eq + 1L, __pytra_len(rhs)))
        if ((!_is_dotted_ident(target)) || (__pytra_str(ann) == __pytra_str("")) || (__pytra_str(expr) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        return new Match(text, mutable.ArrayBuffer[String](target, ann, expr))
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*(\\+=|-=|\\*=|/=|//=|%=|&=|\\|=|\\^=|<<=|>>=)\\s*(.+)$")) {
        var ops: mutable.ArrayBuffer[String] = __pytra_as_list(mutable.ArrayBuffer[String]("<<=", ">>=", "+=", "-=", "*=", "/=", "//=", "%=", "&=", "|=", "^=")).asInstanceOf[mutable.ArrayBuffer[String]]
        var op_pos: Long = __pytra_int(-1L)
        var op_txt: String = ""
        val __iter_0 = __pytra_as_list(ops)
        var __i_1: Long = 0L
        while (__i_1 < __iter_0.size.toLong) {
            val op: String = __pytra_str(__iter_0(__i_1.toInt))
            var p: Any = __pytra_find(text, op)
            if ((__pytra_int(p) >= 0L) && ((op_pos < 0L) || (__pytra_int(p) < op_pos))) {
                op_pos = __pytra_int(p)
                op_txt = op
            }
            __i_1 += 1L
        }
        if (op_pos < 0L) {
            return __pytra_any_default()
        }
        var left: String = __pytra_strip(__pytra_slice(text, 0L, op_pos))
        var right: String = __pytra_strip(__pytra_slice(text, op_pos + __pytra_len(op_txt), __pytra_len(text)))
        if ((__pytra_str(right) == __pytra_str("")) || (!_is_dotted_ident(left))) {
            return __pytra_any_default()
        }
        return new Match(text, mutable.ArrayBuffer[String](left, op_txt, right))
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\s*,\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$")) {
        var eq: Long = __pytra_int(__pytra_find(text, "="))
        if (eq < 0L) {
            return __pytra_any_default()
        }
        var left: String = __pytra_str(__pytra_slice(text, 0L, eq))
        var right: String = __pytra_strip(__pytra_slice(text, eq + 1L, __pytra_len(text)))
        if (__pytra_str(right) == __pytra_str("")) {
            return __pytra_any_default()
        }
        var c: Long = __pytra_int(__pytra_find(left, ","))
        if (c < 0L) {
            return __pytra_any_default()
        }
        var a: String = __pytra_strip(__pytra_slice(left, 0L, c))
        var b: String = __pytra_strip(__pytra_slice(left, c + 1L, __pytra_len(left)))
        if ((!_is_ident(a)) || (!_is_ident(b))) {
            return __pytra_any_default()
        }
        return new Match(text, mutable.ArrayBuffer[String](a, b, right))
    }
    if (__pytra_str(pattern) == __pytra_str("^if\\s+__name__\\s*==\\s*[\\\"']__main__[\\\"']\\s*:\\s*$")) {
        var t: String = _strip_suffix_colon(text)
        if (__pytra_str(t) == __pytra_str("")) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_strip(t)
        if (!__pytra_truthy(__pytra_startswith(rest, "if"))) {
            return __pytra_any_default()
        }
        rest = __pytra_strip(__pytra_slice(rest, 2L, __pytra_len(rest)))
        if (!__pytra_truthy(__pytra_startswith(rest, "__name__"))) {
            return __pytra_any_default()
        }
        rest = __pytra_strip(__pytra_slice(rest, __pytra_len("__name__"), __pytra_len(rest)))
        if (!__pytra_truthy(__pytra_startswith(rest, "=="))) {
            return __pytra_any_default()
        }
        rest = __pytra_strip(__pytra_slice(rest, 2L, __pytra_len(rest)))
        if (__pytra_contains(__pytra_any_default(), rest)) {
            return new Match(text, mutable.ArrayBuffer[Any]())
        }
        return __pytra_any_default()
    }
    if (__pytra_str(pattern) == __pytra_str("^import\\s+(.+)$")) {
        if (!__pytra_truthy(__pytra_startswith(text, "import"))) {
            return __pytra_any_default()
        }
        if (__pytra_len(text) <= 6L) {
            return __pytra_any_default()
        }
        if (!_is_space_ch(__pytra_slice(text, 6L, 7L))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_strip(__pytra_slice(text, 7L, __pytra_len(text)))
        if (__pytra_str(rest) == __pytra_str("")) {
            return __pytra_any_default()
        }
        return new Match(text, mutable.ArrayBuffer[String](rest))
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_\\.]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$")) {
        var parts: mutable.ArrayBuffer[String] = text.split(" as ")
        if (__pytra_len(parts) == 1L) {
            var name: String = __pytra_strip(__pytra_str(__pytra_get_index(parts, 0L)))
            if (!_is_dotted_ident(name)) {
                return __pytra_any_default()
            }
            return new Match(text, mutable.ArrayBuffer[String](name, ""))
        }
        if (__pytra_len(parts) == 2L) {
            var name: String = __pytra_strip(__pytra_str(__pytra_get_index(parts, 0L)))
            var alias: String = __pytra_strip(__pytra_str(__pytra_get_index(parts, 1L)))
            if ((!_is_dotted_ident(name)) || (!_is_ident(alias))) {
                return __pytra_any_default()
            }
            return new Match(text, mutable.ArrayBuffer[String](name, alias))
        }
        return __pytra_any_default()
    }
    if (__pytra_str(pattern) == __pytra_str("^from\\s+([A-Za-z_][A-Za-z0-9_\\.]*)\\s+import\\s+(.+)$")) {
        if (!__pytra_truthy(__pytra_startswith(text, "from "))) {
            return __pytra_any_default()
        }
        var rest: String = __pytra_str(__pytra_slice(text, 5L, __pytra_len(text)))
        var i: Long = __pytra_int(__pytra_find(rest, " import "))
        if (i < 0L) {
            return __pytra_any_default()
        }
        var mod: String = __pytra_strip(__pytra_slice(rest, 0L, i))
        var sym: String = __pytra_strip(__pytra_slice(rest, i + 8L, __pytra_len(rest)))
        if ((!_is_dotted_ident(mod)) || (__pytra_str(sym) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        return new Match(text, mutable.ArrayBuffer[String](mod, sym))
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$")) {
        var parts: mutable.ArrayBuffer[String] = text.split(" as ")
        if (__pytra_len(parts) == 1L) {
            var name: String = __pytra_strip(__pytra_str(__pytra_get_index(parts, 0L)))
            if (!_is_ident(name)) {
                return __pytra_any_default()
            }
            return new Match(text, mutable.ArrayBuffer[String](name, ""))
        }
        if (__pytra_len(parts) == 2L) {
            var name: String = __pytra_strip(__pytra_str(__pytra_get_index(parts, 0L)))
            var alias: String = __pytra_strip(__pytra_str(__pytra_get_index(parts, 1L)))
            if ((!_is_ident(name)) || (!_is_ident(alias))) {
                return __pytra_any_default()
            }
            return new Match(text, mutable.ArrayBuffer[String](name, alias))
        }
        return __pytra_any_default()
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$")) {
        var c: Any = __pytra_find(text, ":")
        if (__pytra_int(c) <= 0L) {
            return __pytra_any_default()
        }
        var name: String = __pytra_strip(__pytra_slice(text, 0L, c))
        var rhs: String = __pytra_str(__pytra_slice(text, c + 1L, __pytra_len(text)))
        var eq: Long = __pytra_int(__pytra_find(rhs, "="))
        if (eq < 0L) {
            return __pytra_any_default()
        }
        var ann: String = __pytra_strip(__pytra_slice(rhs, 0L, eq))
        var expr: String = __pytra_strip(__pytra_slice(rhs, eq + 1L, __pytra_len(rhs)))
        if ((!_is_ident(name)) || (__pytra_str(ann) == __pytra_str("")) || (__pytra_str(expr) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        return new Match(text, mutable.ArrayBuffer[String](name, ann, expr))
    }
    if (__pytra_str(pattern) == __pytra_str("^([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$")) {
        var eq: Long = __pytra_int(__pytra_find(text, "="))
        if (eq < 0L) {
            return __pytra_any_default()
        }
        var name: String = __pytra_strip(__pytra_slice(text, 0L, eq))
        var expr: String = __pytra_strip(__pytra_slice(text, eq + 1L, __pytra_len(text)))
        if ((!_is_ident(name)) || (__pytra_str(expr) == __pytra_str(""))) {
            return __pytra_any_default()
        }
        return new Match(text, mutable.ArrayBuffer[String](name, expr))
    }
    throw new RuntimeException(__pytra_str(__pytra_any_default()))
    return null
}

def sub(pattern: String, repl: String, text: String, flags: Long): String = {
    if (__pytra_str(pattern) == __pytra_str("\\s+")) {
        var out: mutable.ArrayBuffer[String] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[String]]
        var in_ws: Boolean = false
        val __iter_0 = __pytra_as_list(text)
        var __i_1: Long = 0L
        while (__i_1 < __iter_0.size.toLong) {
            val ch: String = __pytra_str(__iter_0(__i_1.toInt))
            if (__pytra_truthy(ch.isspace())) {
                if (!in_ws) {
                    out.append(repl)
                    in_ws = true
                }
            } else {
                out.append(ch)
                in_ws = false
            }
            __i_1 += 1L
        }
        return __pytra_str(__pytra_join("", out))
    }
    if (__pytra_str(pattern) == __pytra_str("\\s+#.*$")) {
        var i: Long = 0L
        while (i < __pytra_len(text)) {
            if (__pytra_truthy(__pytra_str(__pytra_get_index(text, i)).isspace())) {
                var j: Long = i + 1L
                while ((j < __pytra_len(text)) && __pytra_truthy(__pytra_str(__pytra_get_index(text, j)).isspace())) {
                    j += 1L
                }
                if ((j < __pytra_len(text)) && (__pytra_str(__pytra_get_index(text, j)) == __pytra_str("#"))) {
                    return __pytra_str(__pytra_slice(text, 0L, i)) + __pytra_str(repl)
                }
            }
            i += 1L
        }
        return text
    }
    if (__pytra_str(pattern) == __pytra_str("[^0-9A-Za-z_]")) {
        var out: mutable.ArrayBuffer[String] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[String]]
        val __iter_2 = __pytra_as_list(text)
        var __i_3: Long = 0L
        while (__i_3 < __iter_2.size.toLong) {
            val ch: String = __pytra_str(__iter_2(__i_3.toInt))
            if (__pytra_truthy(ch.isalnum()) || (__pytra_str(ch) == __pytra_str("_"))) {
                out.append(ch)
            } else {
                out.append(repl)
            }
            __i_3 += 1L
        }
        return __pytra_str(__pytra_join("", out))
    }
    throw new RuntimeException(__pytra_str(__pytra_any_default()))
    return ""
}
