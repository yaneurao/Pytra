// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: tools/gen_runtime_from_manifest.py



fun __pytra_is_JsonObj(v: Any?): Boolean {
    return v is JsonObj
}

fun __pytra_as_JsonObj(v: Any?): JsonObj {
    return if (v is JsonObj) v else JsonObj()
}

fun __pytra_is_JsonArr(v: Any?): Boolean {
    return v is JsonArr
}

fun __pytra_as_JsonArr(v: Any?): JsonArr {
    return if (v is JsonArr) v else JsonArr()
}

fun __pytra_is_JsonValue(v: Any?): Boolean {
    return v is JsonValue
}

fun __pytra_as_JsonValue(v: Any?): JsonValue {
    return if (v is JsonValue) v else JsonValue()
}

fun __pytra_is__JsonParser(v: Any?): Boolean {
    return v is _JsonParser
}

fun __pytra_as__JsonParser(v: Any?): _JsonParser {
    return if (v is _JsonParser) v else _JsonParser()
}

open class JsonObj() {
    var raw: MutableMap<Any, Any?> = mutableMapOf()

    constructor(raw: MutableMap<Any, Any?>) : this() {
        this.raw = raw
    }

    open fun get(key: String): Any? {
        if (((!__pytra_contains(this.raw, key)))) {
            return __pytra_any_default()
        }
        var value: Any? = _json_obj_require(this.raw, key)
        return JsonValue(value)
    }

    open fun get_obj(key: String): Any? {
        if (((!__pytra_contains(this.raw, key)))) {
            return __pytra_any_default()
        }
        var value: Any? = _json_obj_require(this.raw, key)
        return JsonValue(value).as_obj()
    }

    open fun get_arr(key: String): Any? {
        if (((!__pytra_contains(this.raw, key)))) {
            return __pytra_any_default()
        }
        var value: Any? = _json_obj_require(this.raw, key)
        return JsonValue(value).as_arr()
    }

    open fun get_str(key: String): Any? {
        if (((!__pytra_contains(this.raw, key)))) {
            return __pytra_any_default()
        }
        var value: Any? = _json_obj_require(this.raw, key)
        return JsonValue(value).as_str()
    }

    open fun get_int(key: String): Any? {
        if (((!__pytra_contains(this.raw, key)))) {
            return __pytra_any_default()
        }
        var value: Any? = _json_obj_require(this.raw, key)
        return JsonValue(value).as_int()
    }

    open fun get_float(key: String): Any? {
        if (((!__pytra_contains(this.raw, key)))) {
            return __pytra_any_default()
        }
        var value: Any? = _json_obj_require(this.raw, key)
        return JsonValue(value).as_float()
    }

    open fun get_bool(key: String): Any? {
        if (((!__pytra_contains(this.raw, key)))) {
            return __pytra_any_default()
        }
        var value: Any? = _json_obj_require(this.raw, key)
        return JsonValue(value).as_bool()
    }
}

open class JsonArr() {
    var raw: MutableList<Any?> = mutableListOf()

    constructor(raw: MutableList<Any?>) : this() {
        this.raw = raw
    }

    open fun get(index: Long): Any? {
        if (((__pytra_int(index) < __pytra_int(0L)) || (__pytra_int(index) >= __pytra_int(__pytra_len(_json_array_items(this.raw)))))) {
            return __pytra_any_default()
        }
        return JsonValue(__pytra_get_index(_json_array_items(this.raw), index))
    }

    open fun get_obj(index: Long): Any? {
        if (((__pytra_int(index) < __pytra_int(0L)) || (__pytra_int(index) >= __pytra_int(__pytra_len(_json_array_items(this.raw)))))) {
            return __pytra_any_default()
        }
        return JsonValue(__pytra_get_index(_json_array_items(this.raw), index)).as_obj()
    }

    open fun get_arr(index: Long): Any? {
        if (((__pytra_int(index) < __pytra_int(0L)) || (__pytra_int(index) >= __pytra_int(__pytra_len(_json_array_items(this.raw)))))) {
            return __pytra_any_default()
        }
        return JsonValue(__pytra_get_index(_json_array_items(this.raw), index)).as_arr()
    }

    open fun get_str(index: Long): Any? {
        if (((__pytra_int(index) < __pytra_int(0L)) || (__pytra_int(index) >= __pytra_int(__pytra_len(_json_array_items(this.raw)))))) {
            return __pytra_any_default()
        }
        return JsonValue(__pytra_get_index(_json_array_items(this.raw), index)).as_str()
    }

    open fun get_int(index: Long): Any? {
        if (((__pytra_int(index) < __pytra_int(0L)) || (__pytra_int(index) >= __pytra_int(__pytra_len(_json_array_items(this.raw)))))) {
            return __pytra_any_default()
        }
        return JsonValue(__pytra_get_index(_json_array_items(this.raw), index)).as_int()
    }

    open fun get_float(index: Long): Any? {
        if (((__pytra_int(index) < __pytra_int(0L)) || (__pytra_int(index) >= __pytra_int(__pytra_len(_json_array_items(this.raw)))))) {
            return __pytra_any_default()
        }
        return JsonValue(__pytra_get_index(_json_array_items(this.raw), index)).as_float()
    }

    open fun get_bool(index: Long): Any? {
        if (((__pytra_int(index) < __pytra_int(0L)) || (__pytra_int(index) >= __pytra_int(__pytra_len(_json_array_items(this.raw)))))) {
            return __pytra_any_default()
        }
        return JsonValue(__pytra_get_index(_json_array_items(this.raw), index)).as_bool()
    }
}

open class JsonValue() {
    var raw: Any? = null

    constructor(raw: Any?) : this() {
        this.raw = raw
    }

    open fun as_obj(): Any? {
        var raw: Any? = this.raw
        if (false) {
            var raw_obj: MutableMap<Any, Any?> = dict(raw)
            return JsonObj(raw_obj)
        }
        return __pytra_any_default()
    }

    open fun as_arr(): Any? {
        var raw: Any? = this.raw
        if (false) {
            var raw_arr: MutableList<Any?> = list(raw)
            return JsonArr(raw_arr)
        }
        return __pytra_any_default()
    }

    open fun as_str(): Any? {
        var raw: Any? = this.raw
        if (false) {
            return raw
        }
        return __pytra_any_default()
    }

    open fun as_int(): Any? {
        var raw: Any? = this.raw
        if (false) {
            return __pytra_any_default()
        }
        if (false) {
            var raw_i: Long = __pytra_int(raw)
            return raw_i
        }
        return __pytra_any_default()
    }

    open fun as_float(): Any? {
        var raw: Any? = this.raw
        if (false) {
            var raw_f: Double = __pytra_float(raw)
            return raw_f
        }
        return __pytra_any_default()
    }

    open fun as_bool(): Any? {
        var raw: Any? = this.raw
        if (false) {
            var raw_b: Boolean = __pytra_truthy(raw)
            return raw_b
        }
        return __pytra_any_default()
    }
}

open class _JsonParser() {
    var text: String = ""
    var n: Long = 0L
    var i: Long = 0L

    constructor(text: String) : this() {
        this.text = text
        this.n = __pytra_len(text)
        this.i = 0L
    }

    open fun parse(): Any? {
        this._skip_ws()
        var out: Any? = this._parse_value()
        this._skip_ws()
        if ((__pytra_int(this.i) != __pytra_int(this.n))) {
            throw RuntimeException(__pytra_str("invalid json: trailing characters"))
        }
        return out
    }

    open fun _skip_ws() {
        while (((__pytra_int(this.i) < __pytra_int(this.n)) && _is_ws(__pytra_str(__pytra_get_index(this.text, this.i))))) {
            this.i += 1L
        }
    }

    open fun _parse_value(): Any? {
        if ((__pytra_int(this.i) >= __pytra_int(this.n))) {
            throw RuntimeException(__pytra_str("invalid json: unexpected end"))
        }
        var ch: String = __pytra_str(__pytra_get_index(this.text, this.i))
        if ((__pytra_str(ch) == __pytra_str("{"))) {
            return this._parse_object()
        }
        if ((__pytra_str(ch) == __pytra_str("["))) {
            return this._parse_array()
        }
        if ((__pytra_str(ch) == __pytra_str("\""))) {
            return this._parse_string()
        }
        if (((__pytra_str(ch) == __pytra_str("t")) && (__pytra_str(__pytra_slice(this.text, this.i, (this.i + 4L))) == __pytra_str("true")))) {
            this.i += 4L
            return true
        }
        if (((__pytra_str(ch) == __pytra_str("f")) && (__pytra_str(__pytra_slice(this.text, this.i, (this.i + 5L))) == __pytra_str("false")))) {
            this.i += 5L
            return false
        }
        if (((__pytra_str(ch) == __pytra_str("n")) && (__pytra_str(__pytra_slice(this.text, this.i, (this.i + 4L))) == __pytra_str("null")))) {
            this.i += 4L
            return __pytra_any_default()
        }
        return this._parse_number()
    }

    open fun _parse_object(): MutableMap<Any, Any?> {
        var out: MutableMap<Any, Any?> = __pytra_as_dict(mutableMapOf<Any, Any?>())
        this.i += 1L
        this._skip_ws()
        if (((__pytra_int(this.i) < __pytra_int(this.n)) && (__pytra_str(__pytra_get_index(this.text, this.i)) == __pytra_str("}")))) {
            this.i += 1L
            return out
        }
        while (true) {
            this._skip_ws()
            if (((__pytra_int(this.i) >= __pytra_int(this.n)) || (__pytra_str(__pytra_get_index(this.text, this.i)) != __pytra_str("\"")))) {
                throw RuntimeException(__pytra_str("invalid json object key"))
            }
            var key: String = this._parse_string()
            this._skip_ws()
            if (((__pytra_int(this.i) >= __pytra_int(this.n)) || (__pytra_str(__pytra_get_index(this.text, this.i)) != __pytra_str(":")))) {
                throw RuntimeException(__pytra_str("invalid json object: missing ':'"))
            }
            this.i += 1L
            this._skip_ws()
            __pytra_set_index(out, key, this._parse_value())
            this._skip_ws()
            if ((__pytra_int(this.i) >= __pytra_int(this.n))) {
                throw RuntimeException(__pytra_str("invalid json object: unexpected end"))
            }
            var ch: String = __pytra_str(__pytra_get_index(this.text, this.i))
            this.i += 1L
            if ((__pytra_str(ch) == __pytra_str("}"))) {
                return out
            }
            if ((__pytra_str(ch) != __pytra_str(","))) {
                throw RuntimeException(__pytra_str("invalid json object separator"))
            }
        }
        return mutableMapOf()
    }

    open fun _parse_array(): MutableList<Any?> {
        var out: MutableList<Any?> = _json_new_array()
        this.i += 1L
        this._skip_ws()
        if (((__pytra_int(this.i) < __pytra_int(this.n)) && (__pytra_str(__pytra_get_index(this.text, this.i)) == __pytra_str("]")))) {
            this.i += 1L
            return out
        }
        while (true) {
            this._skip_ws()
            out.add(this._parse_value())
            this._skip_ws()
            if ((__pytra_int(this.i) >= __pytra_int(this.n))) {
                throw RuntimeException(__pytra_str("invalid json array: unexpected end"))
            }
            var ch: String = __pytra_str(__pytra_get_index(this.text, this.i))
            this.i += 1L
            if ((__pytra_str(ch) == __pytra_str("]"))) {
                return out
            }
            if ((__pytra_str(ch) != __pytra_str(","))) {
                throw RuntimeException(__pytra_str("invalid json array separator"))
            }
        }
        return mutableListOf()
    }

    open fun _parse_string(): String {
        if ((__pytra_str(__pytra_get_index(this.text, this.i)) != __pytra_str("\""))) {
            throw RuntimeException(__pytra_str("invalid json string"))
        }
        this.i += 1L
        var out_chars: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
        while ((__pytra_int(this.i) < __pytra_int(this.n))) {
            var ch: String = __pytra_str(__pytra_get_index(this.text, this.i))
            this.i += 1L
            if ((__pytra_str(ch) == __pytra_str("\""))) {
                return _join_strs(out_chars, _EMPTY)
            }
            if ((__pytra_str(ch) == __pytra_str("\\"))) {
                if ((__pytra_int(this.i) >= __pytra_int(this.n))) {
                    throw RuntimeException(__pytra_str("invalid json string escape"))
                }
                var esc: String = __pytra_str(__pytra_get_index(this.text, this.i))
                this.i += 1L
                if ((__pytra_str(esc) == __pytra_str("\""))) {
                    out_chars.add("\"")
                } else {
                    if ((__pytra_str(esc) == __pytra_str("\\"))) {
                        out_chars.add("\\")
                    } else {
                        if ((__pytra_str(esc) == __pytra_str("/"))) {
                            out_chars.add("/")
                        } else {
                            if ((__pytra_str(esc) == __pytra_str("b"))) {
                                out_chars.add("")
                            } else {
                                if ((__pytra_str(esc) == __pytra_str("f"))) {
                                    out_chars.add("
")
                                } else {
                                    if ((__pytra_str(esc) == __pytra_str("n"))) {
                                        out_chars.add("\n")
                                    } else {
                                        if ((__pytra_str(esc) == __pytra_str("r"))) {
                                            out_chars.add("
")
                                        } else {
                                            if ((__pytra_str(esc) == __pytra_str("t"))) {
                                                out_chars.add("	")
                                            } else {
                                                if ((__pytra_str(esc) == __pytra_str("u"))) {
                                                    if ((__pytra_int(this.i + 4L) > __pytra_int(this.n))) {
                                                        throw RuntimeException(__pytra_str("invalid json unicode escape"))
                                                    }
                                                    var hx: String = __pytra_str(__pytra_slice(this.text, this.i, (this.i + 4L)))
                                                    this.i += 4L
                                                    out_chars.add(chr(_int_from_hex4(hx)))
                                                } else {
                                                    throw RuntimeException(__pytra_str("invalid json escape"))
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
                out_chars.add(ch)
            }
        }
        throw RuntimeException(__pytra_str("unterminated json string"))
        return ""
    }

    open fun _parse_number(): Any? {
        var start: Long = __pytra_int(this.i)
        if ((__pytra_str(__pytra_get_index(this.text, this.i)) == __pytra_str("-"))) {
            this.i += 1L
        }
        if ((__pytra_int(this.i) >= __pytra_int(this.n))) {
            throw RuntimeException(__pytra_str("invalid json number"))
        }
        if ((__pytra_str(__pytra_get_index(this.text, this.i)) == __pytra_str("0"))) {
            this.i += 1L
        } else {
            if ((!_is_digit(__pytra_str(__pytra_get_index(this.text, this.i))))) {
                throw RuntimeException(__pytra_str("invalid json number"))
            }
            while (((__pytra_int(this.i) < __pytra_int(this.n)) && _is_digit(__pytra_str(__pytra_get_index(this.text, this.i))))) {
                this.i += 1L
            }
        }
        var is_float: Boolean = false
        if (((__pytra_int(this.i) < __pytra_int(this.n)) && (__pytra_str(__pytra_get_index(this.text, this.i)) == __pytra_str(".")))) {
            is_float = true
            this.i += 1L
            if (((__pytra_int(this.i) >= __pytra_int(this.n)) || (!_is_digit(__pytra_str(__pytra_get_index(this.text, this.i)))))) {
                throw RuntimeException(__pytra_str("invalid json number"))
            }
            while (((__pytra_int(this.i) < __pytra_int(this.n)) && _is_digit(__pytra_str(__pytra_get_index(this.text, this.i))))) {
                this.i += 1L
            }
        }
        if ((__pytra_int(this.i) < __pytra_int(this.n))) {
            var exp_ch: String = __pytra_str(__pytra_get_index(this.text, this.i))
            if (((__pytra_str(exp_ch) == __pytra_str("e")) || (__pytra_str(exp_ch) == __pytra_str("E")))) {
                is_float = true
                this.i += 1L
                if ((__pytra_int(this.i) < __pytra_int(this.n))) {
                    var sign: String = __pytra_str(__pytra_get_index(this.text, this.i))
                    if (((__pytra_str(sign) == __pytra_str("+")) || (__pytra_str(sign) == __pytra_str("-")))) {
                        this.i += 1L
                    }
                }
                if (((__pytra_int(this.i) >= __pytra_int(this.n)) || (!_is_digit(__pytra_str(__pytra_get_index(this.text, this.i)))))) {
                    throw RuntimeException(__pytra_str("invalid json exponent"))
                }
                while (((__pytra_int(this.i) < __pytra_int(this.n)) && _is_digit(__pytra_str(__pytra_get_index(this.text, this.i))))) {
                    this.i += 1L
                }
            }
        }
        var token: String = __pytra_str(__pytra_slice(this.text, start, this.i))
        if (is_float) {
            var num_f: Double = __pytra_float(token)
            return num_f
        }
        var num_i: Long = __pytra_int(token)
        return num_i
    }
}

fun _is_ws(ch: String): Boolean {
    return ((__pytra_str(ch) == __pytra_str(" ")) || (__pytra_str(ch) == __pytra_str("	")) || (__pytra_str(ch) == __pytra_str("
")) || (__pytra_str(ch) == __pytra_str("\n")))
}

fun _is_digit(ch: String): Boolean {
    return ((__pytra_str(ch) >= __pytra_str("0")) && (__pytra_str(ch) <= __pytra_str("9")))
}

fun _hex_value(ch: String): Long {
    if (((__pytra_str(ch) >= __pytra_str("0")) && (__pytra_str(ch) <= __pytra_str("9")))) {
        return __pytra_int(ch)
    }
    if (((__pytra_str(ch) == __pytra_str("a")) || (__pytra_str(ch) == __pytra_str("A")))) {
        return 10L
    }
    if (((__pytra_str(ch) == __pytra_str("b")) || (__pytra_str(ch) == __pytra_str("B")))) {
        return 11L
    }
    if (((__pytra_str(ch) == __pytra_str("c")) || (__pytra_str(ch) == __pytra_str("C")))) {
        return 12L
    }
    if (((__pytra_str(ch) == __pytra_str("d")) || (__pytra_str(ch) == __pytra_str("D")))) {
        return 13L
    }
    if (((__pytra_str(ch) == __pytra_str("e")) || (__pytra_str(ch) == __pytra_str("E")))) {
        return 14L
    }
    if (((__pytra_str(ch) == __pytra_str("f")) || (__pytra_str(ch) == __pytra_str("F")))) {
        return 15L
    }
    throw RuntimeException(__pytra_str("invalid json unicode escape"))
    return 0L
}

fun _int_from_hex4(hx: String): Long {
    if ((__pytra_int(__pytra_len(hx)) != __pytra_int(4L))) {
        throw RuntimeException(__pytra_str("invalid json unicode escape"))
    }
    var v0: Long = _hex_value(__pytra_slice(hx, 0L, 1L))
    var v1: Long = _hex_value(__pytra_slice(hx, 1L, 2L))
    var v2: Long = _hex_value(__pytra_slice(hx, 2L, 3L))
    var v3: Long = _hex_value(__pytra_slice(hx, 3L, 4L))
    return ((((v0 * 4096L) + (v1 * 256L)) + (v2 * 16L)) + v3)
}

fun _hex4(code: Long): String {
    var v: Long = (code % 65536L)
    var d3: Long = (v % 16L)
    v = (v / 16L)
    var d2: Long = (v % 16L)
    v = (v / 16L)
    var d1: Long = (v % 16L)
    v = (v / 16L)
    var d0: Long = (v % 16L)
    var p0: String = __pytra_str(__pytra_slice(_HEX_DIGITS, d0, (d0 + 1L)))
    var p1: String = __pytra_str(__pytra_slice(_HEX_DIGITS, d1, (d1 + 1L)))
    var p2: String = __pytra_str(__pytra_slice(_HEX_DIGITS, d2, (d2 + 1L)))
    var p3: String = __pytra_str(__pytra_slice(_HEX_DIGITS, d3, (d3 + 1L)))
    return (__pytra_str(__pytra_str(__pytra_str(p0) + __pytra_str(p1)) + __pytra_str(p2)) + __pytra_str(p3))
}

fun _json_array_items(raw: Any?): MutableList<Any?> {
    return list(raw)
}

fun _json_new_array(): MutableList<Any?> {
    return list()
}

fun _json_obj_require(raw: MutableMap<Any, Any?>, key: String): Any? {
    val __iter_0 = __pytra_as_list(raw.items())
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val __it_2 = __iter_0[__i_1.toInt()]
        val __tuple_3 = __pytra_as_list(__it_2)
        var k: Any? = __tuple_3[0]
        var value: Any? = __tuple_3[1]
        if ((__pytra_str(k) == __pytra_str(key))) {
            return value
        }
        __i_1 += 1L
    }
    throw RuntimeException(__pytra_str((__pytra_str("json object key not found: ") + __pytra_str(key))))
    return null
}

fun _json_indent_value(indent: Any?): Long {
    if ((__pytra_float(indent) == __pytra_float(__pytra_any_default()))) {
        throw RuntimeException(__pytra_str("json indent is required"))
    }
    var indent_i: Long = __pytra_int(indent)
    return indent_i
}

fun loads(text: String): Any? {
    return _JsonParser(text).parse()
}

fun loads_obj(text: String): Any? {
    var value: Any? = _JsonParser(text).parse()
    if (false) {
        var raw_obj: MutableMap<Any, Any?> = dict(value)
        return JsonObj(raw_obj)
    }
    return __pytra_any_default()
}

fun loads_arr(text: String): Any? {
    var value: Any? = _JsonParser(text).parse()
    if (false) {
        var raw_arr: MutableList<Any?> = list(value)
        return JsonArr(raw_arr)
    }
    return __pytra_any_default()
}

fun _join_strs(parts: MutableList<Any?>, sep: String): String {
    if ((__pytra_int(__pytra_len(parts)) == __pytra_int(0L))) {
        return ""
    }
    var out: String = __pytra_str(__pytra_get_index(parts, 0L))
    var i: Long = 1L
    while ((__pytra_int(i) < __pytra_int(__pytra_len(parts)))) {
        out = (__pytra_str(__pytra_str(out) + __pytra_str(sep)) + __pytra_str(__pytra_get_index(parts, i)))
        i += 1L
    }
    return out
}

fun _escape_str(s: String, ensure_ascii: Boolean): String {
    var out: MutableList<Any?> = __pytra_as_list(mutableListOf("\""))
    val __iter_0 = __pytra_as_list(s)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val ch: String = __pytra_str(__iter_0[__i_1.toInt()])
        var code: Long = __pytra_int(ord(ch))
        if ((__pytra_str(ch) == __pytra_str("\""))) {
            out.add("\\\"")
        } else {
            if ((__pytra_str(ch) == __pytra_str("\\"))) {
                out.add("\\\\")
            } else {
                if ((__pytra_str(ch) == __pytra_str(""))) {
                    out.add("\\b")
                } else {
                    if ((__pytra_str(ch) == __pytra_str("
"))) {
                        out.add("\\f")
                    } else {
                        if ((__pytra_str(ch) == __pytra_str("\n"))) {
                            out.add("\\n")
                        } else {
                            if ((__pytra_str(ch) == __pytra_str("
"))) {
                                out.add("\\r")
                            } else {
                                if ((__pytra_str(ch) == __pytra_str("	"))) {
                                    out.add("\\t")
                                } else {
                                    if ((ensure_ascii && (__pytra_int(code) > __pytra_int(127L)))) {
                                        out.add((__pytra_str("\\u") + __pytra_str(_hex4(code))))
                                    } else {
                                        out.add(ch)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        __i_1 += 1L
    }
    out.add("\"")
    return _join_strs(out, _EMPTY)
}

fun _dump_json_list(values: MutableList<Any?>, ensure_ascii: Boolean, indent: Any?, item_sep: String, key_sep: String, level: Long): String {
    if ((__pytra_int(__pytra_len(values)) == __pytra_int(0L))) {
        return "[]"
    }
    if ((__pytra_float(indent) == __pytra_float(__pytra_any_default()))) {
        var dumped: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
        val __iter_0 = __pytra_as_list(values)
        var __i_1: Long = 0L
        while (__i_1 < __iter_0.size.toLong()) {
            val x = __iter_0[__i_1.toInt()]
            var dumped_txt: String = __pytra_str(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level))
            dumped.add(dumped_txt)
            __i_1 += 1L
        }
        return (__pytra_str(__pytra_str("[") + __pytra_str(_join_strs(dumped, item_sep))) + __pytra_str("]"))
    }
    var indent_i: Long = _json_indent_value(indent)
    var inner: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __iter_2 = __pytra_as_list(values)
    var __i_3: Long = 0L
    while (__i_3 < __iter_2.size.toLong()) {
        val x = __iter_2[__i_3.toInt()]
        var prefix: String = __pytra_str(" " * (indent_i * (level + 1L)))
        var value_txt: String = __pytra_str(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, (level + 1L)))
        inner.add((__pytra_str(prefix) + __pytra_str(value_txt)))
        __i_3 += 1L
    }
    return __pytra_str(((__pytra_str(__pytra_str("[\n") + __pytra_str(_join_strs(inner, _COMMA_NL))) + __pytra_str("\n")) + (" " * (indent_i * level))) + "]")
}

fun _dump_json_dict(values: MutableMap<Any, Any?>, ensure_ascii: Boolean, indent: Any?, item_sep: String, key_sep: String, level: Long): String {
    if ((__pytra_int(__pytra_len(values)) == __pytra_int(0L))) {
        return "{}"
    }
    if ((__pytra_float(indent) == __pytra_float(__pytra_any_default()))) {
        var parts: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
        val __iter_0 = __pytra_as_list(values.items())
        var __i_1: Long = 0L
        while (__i_1 < __iter_0.size.toLong()) {
            val __it_2 = __iter_0[__i_1.toInt()]
            val __tuple_3 = __pytra_as_list(__it_2)
            var k: Any? = __tuple_3[0]
            var x: Any? = __tuple_3[1]
            var k_txt: String = _escape_str(__pytra_str(k), ensure_ascii)
            var v_txt: String = __pytra_str(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level))
            parts.add((__pytra_str(__pytra_str(k_txt) + __pytra_str(key_sep)) + __pytra_str(v_txt)))
            __i_1 += 1L
        }
        return (__pytra_str(__pytra_str("{") + __pytra_str(_join_strs(parts, item_sep))) + __pytra_str("}"))
    }
    var indent_i: Long = _json_indent_value(indent)
    var inner: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __iter_4 = __pytra_as_list(values.items())
    var __i_5: Long = 0L
    while (__i_5 < __iter_4.size.toLong()) {
        val __it_6 = __iter_4[__i_5.toInt()]
        val __tuple_7 = __pytra_as_list(__it_6)
        var k: Any? = __tuple_7[0]
        var x: Any? = __tuple_7[1]
        var prefix: String = __pytra_str(" " * (indent_i * (level + 1L)))
        var k_txt: String = _escape_str(__pytra_str(k), ensure_ascii)
        var v_txt: String = __pytra_str(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, (level + 1L)))
        inner.add((__pytra_str(__pytra_str(__pytra_str(prefix) + __pytra_str(k_txt)) + __pytra_str(key_sep)) + __pytra_str(v_txt)))
        __i_5 += 1L
    }
    return __pytra_str(((__pytra_str(__pytra_str("{\n") + __pytra_str(_join_strs(inner, _COMMA_NL))) + __pytra_str("\n")) + (" " * (indent_i * level))) + "}")
}

fun _dump_json_value(v: Any?, ensure_ascii: Boolean, indent: Any?, item_sep: String, key_sep: String, level: Long): String {
    if ((__pytra_float(v) == __pytra_float(__pytra_any_default()))) {
        return "null"
    }
    if (false) {
        var raw_b: Boolean = __pytra_truthy(v)
        return __pytra_str(__pytra_ifexp(raw_b, "true", "false"))
    }
    if (false) {
        return __pytra_str(v)
    }
    if (false) {
        return __pytra_str(v)
    }
    if (false) {
        return _escape_str(v, ensure_ascii)
    }
    if (false) {
        var as_list: MutableList<Any?> = list(v)
        return _dump_json_list(as_list, ensure_ascii, indent, item_sep, key_sep, level)
    }
    if (false) {
        var as_dict: MutableMap<Any, Any?> = dict(v)
        return _dump_json_dict(as_dict, ensure_ascii, indent, item_sep, key_sep, level)
    }
    throw RuntimeException(__pytra_str("json.dumps unsupported type"))
    return ""
}

fun dumps(obj: Any, ensure_ascii: Boolean, indent: Any?, separators: MutableList<Any?>): String {
    var item_sep: String = ","
    var key_sep: String = __pytra_str(__pytra_ifexp((__pytra_float(indent) == __pytra_float(__pytra_any_default())), ":", ": "))
    if ((__pytra_float(separators) == __pytra_float(__pytra_any_default()))) {
        val __tuple_0 = __pytra_as_list(separators)
        item_sep = __tuple_0[0]
        key_sep = __tuple_0[1]
    }
    return _dump_json_value(obj, ensure_ascii, indent, item_sep, key_sep, 0L)
}
