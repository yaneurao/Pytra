// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def __pytra_is_JsonObj(v: Any): Boolean = {
    v.isInstanceOf[JsonObj]
}

def __pytra_as_JsonObj(v: Any): JsonObj = {
    v match {
        case obj: JsonObj => obj
        case _ => new JsonObj()
    }
}

def __pytra_is_JsonArr(v: Any): Boolean = {
    v.isInstanceOf[JsonArr]
}

def __pytra_as_JsonArr(v: Any): JsonArr = {
    v match {
        case obj: JsonArr => obj
        case _ => new JsonArr()
    }
}

def __pytra_is_JsonValue(v: Any): Boolean = {
    v.isInstanceOf[JsonValue]
}

def __pytra_as_JsonValue(v: Any): JsonValue = {
    v match {
        case obj: JsonValue => obj
        case _ => new JsonValue()
    }
}

def __pytra_is__JsonParser(v: Any): Boolean = {
    v.isInstanceOf[_JsonParser]
}

def __pytra_as__JsonParser(v: Any): _JsonParser = {
    v match {
        case obj: _JsonParser => obj
        case _ => new _JsonParser()
    }
}

class JsonObj() {
    var raw: mutable.LinkedHashMap[Any, Any] = mutable.LinkedHashMap[Any, Any]()

    def this(raw: mutable.LinkedHashMap[Any, Any]) = {
        this()
        this.raw = raw
    }

    def get(key: String): Any = {
        if (!__pytra_contains(this.raw, key)) {
            return __pytra_any_default()
        }
        var value: Any = _json_obj_require(this.raw, key)
        return new JsonValue(value)
    }

    def get_obj(key: String): Any = {
        if (!__pytra_contains(this.raw, key)) {
            return __pytra_any_default()
        }
        var value: Any = _json_obj_require(this.raw, key)
        return new JsonValue(value).as_obj()
    }

    def get_arr(key: String): Any = {
        if (!__pytra_contains(this.raw, key)) {
            return __pytra_any_default()
        }
        var value: Any = _json_obj_require(this.raw, key)
        return new JsonValue(value).as_arr()
    }

    def get_str(key: String): Any = {
        if (!__pytra_contains(this.raw, key)) {
            return __pytra_any_default()
        }
        var value: Any = _json_obj_require(this.raw, key)
        return new JsonValue(value).as_str()
    }

    def get_int(key: String): Any = {
        if (!__pytra_contains(this.raw, key)) {
            return __pytra_any_default()
        }
        var value: Any = _json_obj_require(this.raw, key)
        return new JsonValue(value).as_int()
    }

    def get_float(key: String): Any = {
        if (!__pytra_contains(this.raw, key)) {
            return __pytra_any_default()
        }
        var value: Any = _json_obj_require(this.raw, key)
        return new JsonValue(value).as_float()
    }

    def get_bool(key: String): Any = {
        if (!__pytra_contains(this.raw, key)) {
            return __pytra_any_default()
        }
        var value: Any = _json_obj_require(this.raw, key)
        return new JsonValue(value).as_bool()
    }
}

class JsonArr() {
    var raw: mutable.ArrayBuffer[Any] = mutable.ArrayBuffer[Any]()

    def this(raw: mutable.ArrayBuffer[Any]) = {
        this()
        this.raw = raw
    }

    def get(index: Long): Any = {
        if ((index < 0L) || (index >= __pytra_len(_json_array_items(this.raw)))) {
            return __pytra_any_default()
        }
        return new JsonValue(__pytra_get_index(_json_array_items(this.raw), index))
    }

    def get_obj(index: Long): Any = {
        if ((index < 0L) || (index >= __pytra_len(_json_array_items(this.raw)))) {
            return __pytra_any_default()
        }
        return new JsonValue(__pytra_get_index(_json_array_items(this.raw), index)).as_obj()
    }

    def get_arr(index: Long): Any = {
        if ((index < 0L) || (index >= __pytra_len(_json_array_items(this.raw)))) {
            return __pytra_any_default()
        }
        return new JsonValue(__pytra_get_index(_json_array_items(this.raw), index)).as_arr()
    }

    def get_str(index: Long): Any = {
        if ((index < 0L) || (index >= __pytra_len(_json_array_items(this.raw)))) {
            return __pytra_any_default()
        }
        return new JsonValue(__pytra_get_index(_json_array_items(this.raw), index)).as_str()
    }

    def get_int(index: Long): Any = {
        if ((index < 0L) || (index >= __pytra_len(_json_array_items(this.raw)))) {
            return __pytra_any_default()
        }
        return new JsonValue(__pytra_get_index(_json_array_items(this.raw), index)).as_int()
    }

    def get_float(index: Long): Any = {
        if ((index < 0L) || (index >= __pytra_len(_json_array_items(this.raw)))) {
            return __pytra_any_default()
        }
        return new JsonValue(__pytra_get_index(_json_array_items(this.raw), index)).as_float()
    }

    def get_bool(index: Long): Any = {
        if ((index < 0L) || (index >= __pytra_len(_json_array_items(this.raw)))) {
            return __pytra_any_default()
        }
        return new JsonValue(__pytra_get_index(_json_array_items(this.raw), index)).as_bool()
    }
}

class JsonValue() {
    var raw: Any = null

    def this(raw: Any) = {
        this()
        this.raw = raw
    }

    def as_obj(): Any = {
        var raw: Any = this.raw
        if (false) {
            var raw_obj: mutable.LinkedHashMap[Any, Any] = dict(raw)
            return new JsonObj(raw_obj)
        }
        return __pytra_any_default()
    }

    def as_arr(): Any = {
        var raw: Any = this.raw
        if (false) {
            var raw_arr: mutable.ArrayBuffer[Any] = list(raw)
            return new JsonArr(raw_arr)
        }
        return __pytra_any_default()
    }

    def as_str(): Any = {
        var raw: Any = this.raw
        if (false) {
            return raw
        }
        return __pytra_any_default()
    }

    def as_int(): Any = {
        var raw: Any = this.raw
        if (false) {
            return __pytra_any_default()
        }
        if (false) {
            var raw_i: Long = __pytra_int(raw)
            return raw_i
        }
        return __pytra_any_default()
    }

    def as_float(): Any = {
        var raw: Any = this.raw
        if (false) {
            var raw_f: Double = __pytra_float(raw)
            return raw_f
        }
        return __pytra_any_default()
    }

    def as_bool(): Any = {
        var raw: Any = this.raw
        if (false) {
            var raw_b: Boolean = __pytra_truthy(raw)
            return raw_b
        }
        return __pytra_any_default()
    }
}

class _JsonParser() {
    var text: String = ""
    var n: Long = 0L
    var i: Long = 0L

    def this(text: String) = {
        this()
        this.text = text
        this.n = __pytra_len(text)
        this.i = 0L
    }

    def parse(): Any = {
        this._skip_ws()
        var out: Any = this._parse_value()
        this._skip_ws()
        if (this.i != this.n) {
            throw new RuntimeException(__pytra_str("invalid json: trailing characters"))
        }
        return out
    }

    def _skip_ws(): Unit = {
        while ((this.i < this.n) && _is_ws(__pytra_str(__pytra_get_index(this.text, this.i)))) {
            this.i += 1L
        }
    }

    def _parse_value(): Any = {
        if (this.i >= this.n) {
            throw new RuntimeException(__pytra_str("invalid json: unexpected end"))
        }
        var ch: String = __pytra_str(__pytra_get_index(this.text, this.i))
        if (__pytra_str(ch) == __pytra_str("{")) {
            return this._parse_object()
        }
        if (__pytra_str(ch) == __pytra_str("[")) {
            return this._parse_array()
        }
        if (__pytra_str(ch) == __pytra_str("\"")) {
            return this._parse_string()
        }
        if ((__pytra_str(ch) == __pytra_str("t")) && (__pytra_str(__pytra_slice(this.text, this.i, this.i + 4L)) == __pytra_str("true"))) {
            this.i += 4L
            return true
        }
        if ((__pytra_str(ch) == __pytra_str("f")) && (__pytra_str(__pytra_slice(this.text, this.i, this.i + 5L)) == __pytra_str("false"))) {
            this.i += 5L
            return false
        }
        if ((__pytra_str(ch) == __pytra_str("n")) && (__pytra_str(__pytra_slice(this.text, this.i, this.i + 4L)) == __pytra_str("null"))) {
            this.i += 4L
            return __pytra_any_default()
        }
        return this._parse_number()
    }

    def _parse_object(): mutable.LinkedHashMap[Any, Any] = {
        var out: mutable.LinkedHashMap[Any, Any] = __pytra_as_dict(mutable.LinkedHashMap[Any, Any]())
        this.i += 1L
        this._skip_ws()
        if ((this.i < this.n) && (__pytra_str(__pytra_get_index(this.text, this.i)) == __pytra_str("}"))) {
            this.i += 1L
            return out
        }
        while (true) {
            this._skip_ws()
            if ((this.i >= this.n) || (__pytra_str(__pytra_get_index(this.text, this.i)) != __pytra_str("\""))) {
                throw new RuntimeException(__pytra_str("invalid json object key"))
            }
            var key: String = this._parse_string()
            this._skip_ws()
            if ((this.i >= this.n) || (__pytra_str(__pytra_get_index(this.text, this.i)) != __pytra_str(":"))) {
                throw new RuntimeException(__pytra_str("invalid json object: missing ':'"))
            }
            this.i += 1L
            this._skip_ws()
            __pytra_set_index(out, key, this._parse_value())
            this._skip_ws()
            if (this.i >= this.n) {
                throw new RuntimeException(__pytra_str("invalid json object: unexpected end"))
            }
            var ch: String = __pytra_str(__pytra_get_index(this.text, this.i))
            this.i += 1L
            if (__pytra_str(ch) == __pytra_str("}")) {
                return out
            }
            if (__pytra_str(ch) != __pytra_str(",")) {
                throw new RuntimeException(__pytra_str("invalid json object separator"))
            }
        }
        return mutable.LinkedHashMap[Any, Any]()
    }

    def _parse_array(): mutable.ArrayBuffer[Any] = {
        var out: mutable.ArrayBuffer[Any] = _json_new_array()
        this.i += 1L
        this._skip_ws()
        if ((this.i < this.n) && (__pytra_str(__pytra_get_index(this.text, this.i)) == __pytra_str("]"))) {
            this.i += 1L
            return out
        }
        while (true) {
            this._skip_ws()
            out.append(this._parse_value())
            this._skip_ws()
            if (this.i >= this.n) {
                throw new RuntimeException(__pytra_str("invalid json array: unexpected end"))
            }
            var ch: String = __pytra_str(__pytra_get_index(this.text, this.i))
            this.i += 1L
            if (__pytra_str(ch) == __pytra_str("]")) {
                return out
            }
            if (__pytra_str(ch) != __pytra_str(",")) {
                throw new RuntimeException(__pytra_str("invalid json array separator"))
            }
        }
        return mutable.ArrayBuffer[Any]()
    }

    def _parse_string(): String = {
        if (__pytra_str(__pytra_get_index(this.text, this.i)) != __pytra_str("\"")) {
            throw new RuntimeException(__pytra_str("invalid json string"))
        }
        this.i += 1L
        var out_chars: mutable.ArrayBuffer[String] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[String]]
        while (this.i < this.n) {
            var ch: String = __pytra_str(__pytra_get_index(this.text, this.i))
            this.i += 1L
            if (__pytra_str(ch) == __pytra_str("\"")) {
                return _join_strs(out_chars, _EMPTY)
            }
            if (__pytra_str(ch) == __pytra_str("\\")) {
                if (this.i >= this.n) {
                    throw new RuntimeException(__pytra_str("invalid json string escape"))
                }
                var esc: String = __pytra_str(__pytra_get_index(this.text, this.i))
                this.i += 1L
                if (__pytra_str(esc) == __pytra_str("\"")) {
                    out_chars.append("\"")
                } else {
                    if (__pytra_str(esc) == __pytra_str("\\")) {
                        out_chars.append("\\")
                    } else {
                        if (__pytra_str(esc) == __pytra_str("/")) {
                            out_chars.append("/")
                        } else {
                            if (__pytra_str(esc) == __pytra_str("b")) {
                                out_chars.append("")
                            } else {
                                if (__pytra_str(esc) == __pytra_str("f")) {
                                    out_chars.append("
")
                                } else {
                                    if (__pytra_str(esc) == __pytra_str("n")) {
                                        out_chars.append("\n")
                                    } else {
                                        if (__pytra_str(esc) == __pytra_str("r")) {
                                            out_chars.append("
")
                                        } else {
                                            if (__pytra_str(esc) == __pytra_str("t")) {
                                                out_chars.append("	")
                                            } else {
                                                if (__pytra_str(esc) == __pytra_str("u")) {
                                                    if (this.i + 4L > this.n) {
                                                        throw new RuntimeException(__pytra_str("invalid json unicode escape"))
                                                    }
                                                    var hx: String = __pytra_str(__pytra_slice(this.text, this.i, this.i + 4L))
                                                    this.i += 4L
                                                    out_chars.append(chr(_int_from_hex4(hx)))
                                                } else {
                                                    throw new RuntimeException(__pytra_str("invalid json escape"))
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
                out_chars.append(ch)
            }
        }
        throw new RuntimeException(__pytra_str("unterminated json string"))
        return ""
    }

    def _parse_number(): Any = {
        var start: Long = __pytra_int(this.i)
        if (__pytra_str(__pytra_get_index(this.text, this.i)) == __pytra_str("-")) {
            this.i += 1L
        }
        if (this.i >= this.n) {
            throw new RuntimeException(__pytra_str("invalid json number"))
        }
        if (__pytra_str(__pytra_get_index(this.text, this.i)) == __pytra_str("0")) {
            this.i += 1L
        } else {
            if (!_is_digit(__pytra_str(__pytra_get_index(this.text, this.i)))) {
                throw new RuntimeException(__pytra_str("invalid json number"))
            }
            while ((this.i < this.n) && _is_digit(__pytra_str(__pytra_get_index(this.text, this.i)))) {
                this.i += 1L
            }
        }
        var is_float: Boolean = false
        if ((this.i < this.n) && (__pytra_str(__pytra_get_index(this.text, this.i)) == __pytra_str("."))) {
            is_float = true
            this.i += 1L
            if ((this.i >= this.n) || (!_is_digit(__pytra_str(__pytra_get_index(this.text, this.i))))) {
                throw new RuntimeException(__pytra_str("invalid json number"))
            }
            while ((this.i < this.n) && _is_digit(__pytra_str(__pytra_get_index(this.text, this.i)))) {
                this.i += 1L
            }
        }
        if (this.i < this.n) {
            var exp_ch: String = __pytra_str(__pytra_get_index(this.text, this.i))
            if ((__pytra_str(exp_ch) == __pytra_str("e")) || (__pytra_str(exp_ch) == __pytra_str("E"))) {
                is_float = true
                this.i += 1L
                if (this.i < this.n) {
                    var sign: String = __pytra_str(__pytra_get_index(this.text, this.i))
                    if ((__pytra_str(sign) == __pytra_str("+")) || (__pytra_str(sign) == __pytra_str("-"))) {
                        this.i += 1L
                    }
                }
                if ((this.i >= this.n) || (!_is_digit(__pytra_str(__pytra_get_index(this.text, this.i))))) {
                    throw new RuntimeException(__pytra_str("invalid json exponent"))
                }
                while ((this.i < this.n) && _is_digit(__pytra_str(__pytra_get_index(this.text, this.i)))) {
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

def _is_ws(ch: String): Boolean = {
    return ((__pytra_str(ch) == __pytra_str(" ")) || (__pytra_str(ch) == __pytra_str("	")) || (__pytra_str(ch) == __pytra_str("
")) || (__pytra_str(ch) == __pytra_str("\n")))
}

def _is_digit(ch: String): Boolean = {
    return ((__pytra_str(ch) >= __pytra_str("0")) && (__pytra_str(ch) <= __pytra_str("9")))
}

def _hex_value(ch: String): Long = {
    if ((__pytra_str(ch) >= __pytra_str("0")) && (__pytra_str(ch) <= __pytra_str("9"))) {
        return __pytra_int(ch)
    }
    if ((__pytra_str(ch) == __pytra_str("a")) || (__pytra_str(ch) == __pytra_str("A"))) {
        return 10L
    }
    if ((__pytra_str(ch) == __pytra_str("b")) || (__pytra_str(ch) == __pytra_str("B"))) {
        return 11L
    }
    if ((__pytra_str(ch) == __pytra_str("c")) || (__pytra_str(ch) == __pytra_str("C"))) {
        return 12L
    }
    if ((__pytra_str(ch) == __pytra_str("d")) || (__pytra_str(ch) == __pytra_str("D"))) {
        return 13L
    }
    if ((__pytra_str(ch) == __pytra_str("e")) || (__pytra_str(ch) == __pytra_str("E"))) {
        return 14L
    }
    if ((__pytra_str(ch) == __pytra_str("f")) || (__pytra_str(ch) == __pytra_str("F"))) {
        return 15L
    }
    throw new RuntimeException(__pytra_str("invalid json unicode escape"))
    return 0L
}

def _int_from_hex4(hx: String): Long = {
    if (__pytra_len(hx) != 4L) {
        throw new RuntimeException(__pytra_str("invalid json unicode escape"))
    }
    var v0: Long = _hex_value(__pytra_slice(hx, 0L, 1L))
    var v1: Long = _hex_value(__pytra_slice(hx, 1L, 2L))
    var v2: Long = _hex_value(__pytra_slice(hx, 2L, 3L))
    var v3: Long = _hex_value(__pytra_slice(hx, 3L, 4L))
    return (((v0 * 4096L + v1 * 256L) + v2 * 16L) + v3)
}

def _hex4(code: Long): String = {
    var v: Long = code % 65536L
    var d3: Long = v % 16L
    v = __pytra_int(v / 16L)
    var d2: Long = v % 16L
    v = __pytra_int(v / 16L)
    var d1: Long = v % 16L
    v = __pytra_int(v / 16L)
    var d0: Long = v % 16L
    var p0: String = __pytra_str(__pytra_slice(_HEX_DIGITS, d0, d0 + 1L))
    var p1: String = __pytra_str(__pytra_slice(_HEX_DIGITS, d1, d1 + 1L))
    var p2: String = __pytra_str(__pytra_slice(_HEX_DIGITS, d2, d2 + 1L))
    var p3: String = __pytra_str(__pytra_slice(_HEX_DIGITS, d3, d3 + 1L))
    return (__pytra_str(__pytra_str(__pytra_str(p0) + __pytra_str(p1)) + __pytra_str(p2)) + __pytra_str(p3))
}

def _json_array_items(raw: Any): mutable.ArrayBuffer[Any] = {
    return list(raw)
}

def _json_new_array(): mutable.ArrayBuffer[Any] = {
    return list()
}

def _json_obj_require(raw: mutable.LinkedHashMap[Any, Any], key: String): Any = {
    val __iter_0 = __pytra_as_list(raw.items())
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong) {
        val __it_2 = __iter_0(__i_1.toInt)
        val __tuple_3 = __pytra_as_list(__it_2)
        var k: Any = __tuple_3(0)
        var value: Any = __tuple_3(1)
        if (__pytra_str(k) == __pytra_str(key)) {
            return value
        }
        __i_1 += 1L
    }
    throw new RuntimeException(__pytra_str(__pytra_str("json object key not found: ") + __pytra_str(key)))
    return null
}

def _json_indent_value(indent: Any): Long = {
    if (__pytra_float(indent) == __pytra_float(__pytra_any_default())) {
        throw new RuntimeException(__pytra_str("json indent is required"))
    }
    var indent_i: Long = __pytra_int(indent)
    return indent_i
}

def loads(text: String): Any = {
    return new _JsonParser(text).parse()
}

def loads_obj(text: String): Any = {
    var value: Any = new _JsonParser(text).parse()
    if (false) {
        var raw_obj: mutable.LinkedHashMap[Any, Any] = dict(value)
        return new JsonObj(raw_obj)
    }
    return __pytra_any_default()
}

def loads_arr(text: String): Any = {
    var value: Any = new _JsonParser(text).parse()
    if (false) {
        var raw_arr: mutable.ArrayBuffer[Any] = list(value)
        return new JsonArr(raw_arr)
    }
    return __pytra_any_default()
}

def _join_strs(parts: mutable.ArrayBuffer[String], sep: String): String = {
    if (__pytra_len(parts) == 0L) {
        return ""
    }
    var out: String = __pytra_str(__pytra_get_index(parts, 0L))
    var i: Long = 1L
    while (i < __pytra_len(parts)) {
        out = (__pytra_str(__pytra_str(out) + __pytra_str(sep)) + __pytra_str(__pytra_get_index(parts, i)))
        i += 1L
    }
    return out
}

def _escape_str(s: String, ensure_ascii: Boolean): String = {
    var out: mutable.ArrayBuffer[String] = __pytra_as_list(mutable.ArrayBuffer[String]("\"")).asInstanceOf[mutable.ArrayBuffer[String]]
    val __iter_0 = __pytra_as_list(s)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong) {
        val ch: String = __pytra_str(__iter_0(__i_1.toInt))
        var code: Long = __pytra_int(ord(ch))
        if (__pytra_str(ch) == __pytra_str("\"")) {
            out.append("\\\"")
        } else {
            if (__pytra_str(ch) == __pytra_str("\\")) {
                out.append("\\\\")
            } else {
                if (__pytra_str(ch) == __pytra_str("")) {
                    out.append("\\b")
                } else {
                    if (__pytra_str(ch) == __pytra_str("
")) {
                        out.append("\\f")
                    } else {
                        if (__pytra_str(ch) == __pytra_str("\n")) {
                            out.append("\\n")
                        } else {
                            if (__pytra_str(ch) == __pytra_str("
")) {
                                out.append("\\r")
                            } else {
                                if (__pytra_str(ch) == __pytra_str("	")) {
                                    out.append("\\t")
                                } else {
                                    if (ensure_ascii && (code > 127L)) {
                                        out.append(__pytra_str("\\u") + __pytra_str(_hex4(code)))
                                    } else {
                                        out.append(ch)
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
    out.append("\"")
    return _join_strs(out, _EMPTY)
}

def _dump_json_list(values: mutable.ArrayBuffer[Any], ensure_ascii: Boolean, indent: Any, item_sep: String, key_sep: String, level: Long): String = {
    if (__pytra_len(values) == 0L) {
        return "[]"
    }
    if (__pytra_float(indent) == __pytra_float(__pytra_any_default())) {
        var dumped: mutable.ArrayBuffer[String] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[String]]
        val __iter_0 = __pytra_as_list(values)
        var __i_1: Long = 0L
        while (__i_1 < __iter_0.size.toLong) {
            val x = __iter_0(__i_1.toInt)
            var dumped_txt: String = __pytra_str(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level))
            dumped.append(dumped_txt)
            __i_1 += 1L
        }
        return (__pytra_str(__pytra_str("[") + __pytra_str(_join_strs(dumped, item_sep))) + __pytra_str("]"))
    }
    var indent_i: Long = _json_indent_value(indent)
    var inner: mutable.ArrayBuffer[String] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[String]]
    val __iter_2 = __pytra_as_list(values)
    var __i_3: Long = 0L
    while (__i_3 < __iter_2.size.toLong) {
        val x = __iter_2(__i_3.toInt)
        var prefix: String = __pytra_str(" " * (indent_i * (level + 1L)))
        var value_txt: String = __pytra_str(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1L))
        inner.append(__pytra_str(prefix) + __pytra_str(value_txt))
        __i_3 += 1L
    }
    return __pytra_str(((__pytra_str(__pytra_str("[\n") + __pytra_str(_join_strs(inner, _COMMA_NL))) + __pytra_str("\n")) + (" " * indent_i * level)) + "]")
}

def _dump_json_dict(values: mutable.LinkedHashMap[Any, Any], ensure_ascii: Boolean, indent: Any, item_sep: String, key_sep: String, level: Long): String = {
    if (__pytra_len(values) == 0L) {
        return "{}"
    }
    if (__pytra_float(indent) == __pytra_float(__pytra_any_default())) {
        var parts: mutable.ArrayBuffer[String] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[String]]
        val __iter_0 = __pytra_as_list(values.items())
        var __i_1: Long = 0L
        while (__i_1 < __iter_0.size.toLong) {
            val __it_2 = __iter_0(__i_1.toInt)
            val __tuple_3 = __pytra_as_list(__it_2)
            var k: Any = __tuple_3(0)
            var x: Any = __tuple_3(1)
            var k_txt: String = _escape_str(__pytra_str(k), ensure_ascii)
            var v_txt: String = __pytra_str(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level))
            parts.append((__pytra_str(__pytra_str(k_txt) + __pytra_str(key_sep)) + __pytra_str(v_txt)))
            __i_1 += 1L
        }
        return (__pytra_str(__pytra_str("{") + __pytra_str(_join_strs(parts, item_sep))) + __pytra_str("}"))
    }
    var indent_i: Long = _json_indent_value(indent)
    var inner: mutable.ArrayBuffer[String] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[String]]
    val __iter_4 = __pytra_as_list(values.items())
    var __i_5: Long = 0L
    while (__i_5 < __iter_4.size.toLong) {
        val __it_6 = __iter_4(__i_5.toInt)
        val __tuple_7 = __pytra_as_list(__it_6)
        var k: Any = __tuple_7(0)
        var x: Any = __tuple_7(1)
        var prefix: String = __pytra_str(" " * (indent_i * (level + 1L)))
        var k_txt: String = _escape_str(__pytra_str(k), ensure_ascii)
        var v_txt: String = __pytra_str(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1L))
        inner.append((__pytra_str(__pytra_str(__pytra_str(prefix) + __pytra_str(k_txt)) + __pytra_str(key_sep)) + __pytra_str(v_txt)))
        __i_5 += 1L
    }
    return __pytra_str(((__pytra_str(__pytra_str("{\n") + __pytra_str(_join_strs(inner, _COMMA_NL))) + __pytra_str("\n")) + (" " * indent_i * level)) + "}")
}

def _dump_json_value(v: Any, ensure_ascii: Boolean, indent: Any, item_sep: String, key_sep: String, level: Long): String = {
    if (__pytra_float(v) == __pytra_float(__pytra_any_default())) {
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
        var as_list: mutable.ArrayBuffer[Any] = list(v)
        return _dump_json_list(as_list, ensure_ascii, indent, item_sep, key_sep, level)
    }
    if (false) {
        var as_dict: mutable.LinkedHashMap[Any, Any] = dict(v)
        return _dump_json_dict(as_dict, ensure_ascii, indent, item_sep, key_sep, level)
    }
    throw new RuntimeException(__pytra_str("json.dumps unsupported type"))
    return ""
}

def dumps(obj: Any, ensure_ascii: Boolean, indent: Any, separators: mutable.ArrayBuffer[Any]): String = {
    var item_sep: String = ","
    var key_sep: String = __pytra_str(__pytra_ifexp((__pytra_float(indent) == __pytra_float(__pytra_any_default())), ":", ": "))
    if (__pytra_float(separators) == __pytra_float(__pytra_any_default())) {
        val __tuple_0 = __pytra_as_list(separators)
        item_sep = __tuple_0(0)
        key_sep = __tuple_0(1)
    }
    return _dump_json_value(obj, ensure_ascii, indent, item_sep, key_sep, 0L)
}
