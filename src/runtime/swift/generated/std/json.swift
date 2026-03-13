// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func __pytra_is_JsonObj(_ v: Any?) -> Bool {
    return v is JsonObj
}

func __pytra_is_JsonArr(_ v: Any?) -> Bool {
    return v is JsonArr
}

func __pytra_is_JsonValue(_ v: Any?) -> Bool {
    return v is JsonValue
}

func __pytra_is__JsonParser(_ v: Any?) -> Bool {
    return v is _JsonParser
}

class JsonObj {
    var raw: [AnyHashable: Any] = [:]

    init(_ raw: [AnyHashable: Any]) {
        self.raw = raw
    }

    func get(_ key: String) -> Any {
        if ((!__pytra_contains(self.raw, key))) {
            return __pytra_any_default()
        }
        var value: Any = _json_obj_require(self.raw, key)
        return JsonValue(value)
    }

    func get_obj(_ key: String) -> Any {
        if ((!__pytra_contains(self.raw, key))) {
            return __pytra_any_default()
        }
        var value: Any = _json_obj_require(self.raw, key)
        return JsonValue(value).as_obj()
    }

    func get_arr(_ key: String) -> Any {
        if ((!__pytra_contains(self.raw, key))) {
            return __pytra_any_default()
        }
        var value: Any = _json_obj_require(self.raw, key)
        return JsonValue(value).as_arr()
    }

    func get_str(_ key: String) -> Any {
        if ((!__pytra_contains(self.raw, key))) {
            return __pytra_any_default()
        }
        var value: Any = _json_obj_require(self.raw, key)
        return JsonValue(value).as_str()
    }

    func get_int(_ key: String) -> Any {
        if ((!__pytra_contains(self.raw, key))) {
            return __pytra_any_default()
        }
        var value: Any = _json_obj_require(self.raw, key)
        return JsonValue(value).as_int()
    }

    func get_float(_ key: String) -> Any {
        if ((!__pytra_contains(self.raw, key))) {
            return __pytra_any_default()
        }
        var value: Any = _json_obj_require(self.raw, key)
        return JsonValue(value).as_float()
    }

    func get_bool(_ key: String) -> Any {
        if ((!__pytra_contains(self.raw, key))) {
            return __pytra_any_default()
        }
        var value: Any = _json_obj_require(self.raw, key)
        return JsonValue(value).as_bool()
    }
}

class JsonArr {
    var raw: [Any] = []

    init(_ raw: [Any]) {
        self.raw = raw
    }

    func get(_ index: Int64) -> Any {
        if ((__pytra_int(index) < __pytra_int(Int64(0))) || (__pytra_int(index) >= __pytra_int(__pytra_len(_json_array_items(self.raw))))) {
            return __pytra_any_default()
        }
        return JsonValue(__pytra_getIndex(_json_array_items(self.raw), index))
    }

    func get_obj(_ index: Int64) -> Any {
        if ((__pytra_int(index) < __pytra_int(Int64(0))) || (__pytra_int(index) >= __pytra_int(__pytra_len(_json_array_items(self.raw))))) {
            return __pytra_any_default()
        }
        return JsonValue(__pytra_getIndex(_json_array_items(self.raw), index)).as_obj()
    }

    func get_arr(_ index: Int64) -> Any {
        if ((__pytra_int(index) < __pytra_int(Int64(0))) || (__pytra_int(index) >= __pytra_int(__pytra_len(_json_array_items(self.raw))))) {
            return __pytra_any_default()
        }
        return JsonValue(__pytra_getIndex(_json_array_items(self.raw), index)).as_arr()
    }

    func get_str(_ index: Int64) -> Any {
        if ((__pytra_int(index) < __pytra_int(Int64(0))) || (__pytra_int(index) >= __pytra_int(__pytra_len(_json_array_items(self.raw))))) {
            return __pytra_any_default()
        }
        return JsonValue(__pytra_getIndex(_json_array_items(self.raw), index)).as_str()
    }

    func get_int(_ index: Int64) -> Any {
        if ((__pytra_int(index) < __pytra_int(Int64(0))) || (__pytra_int(index) >= __pytra_int(__pytra_len(_json_array_items(self.raw))))) {
            return __pytra_any_default()
        }
        return JsonValue(__pytra_getIndex(_json_array_items(self.raw), index)).as_int()
    }

    func get_float(_ index: Int64) -> Any {
        if ((__pytra_int(index) < __pytra_int(Int64(0))) || (__pytra_int(index) >= __pytra_int(__pytra_len(_json_array_items(self.raw))))) {
            return __pytra_any_default()
        }
        return JsonValue(__pytra_getIndex(_json_array_items(self.raw), index)).as_float()
    }

    func get_bool(_ index: Int64) -> Any {
        if ((__pytra_int(index) < __pytra_int(Int64(0))) || (__pytra_int(index) >= __pytra_int(__pytra_len(_json_array_items(self.raw))))) {
            return __pytra_any_default()
        }
        return JsonValue(__pytra_getIndex(_json_array_items(self.raw), index)).as_bool()
    }
}

class JsonValue {
    var raw: Any = __pytra_any_default()

    init(_ raw: Any) {
        self.raw = raw
    }

    func as_obj() -> Any {
        var raw: Any = self.raw
        if false {
            var raw_obj: [AnyHashable: Any] = dict(raw)
            return JsonObj(raw_obj)
        }
        return __pytra_any_default()
    }

    func as_arr() -> Any {
        var raw: Any = self.raw
        if false {
            var raw_arr: [Any] = list(raw)
            return JsonArr(raw_arr)
        }
        return __pytra_any_default()
    }

    func as_str() -> Any {
        var raw: Any = self.raw
        if false {
            return raw
        }
        return __pytra_any_default()
    }

    func as_int() -> Any {
        var raw: Any = self.raw
        if false {
            return __pytra_any_default()
        }
        if false {
            var raw_i: Int64 = __pytra_int(raw)
            return raw_i
        }
        return __pytra_any_default()
    }

    func as_float() -> Any {
        var raw: Any = self.raw
        if false {
            var raw_f: Double = __pytra_float(raw)
            return raw_f
        }
        return __pytra_any_default()
    }

    func as_bool() -> Any {
        var raw: Any = self.raw
        if false {
            var raw_b: Bool = __pytra_truthy(raw)
            return raw_b
        }
        return __pytra_any_default()
    }
}

class _JsonParser {
    var text: String = ""
    var n: Int64 = 0
    var i: Int64 = 0

    init(_ text: String) {
        self.text = text
        self.n = __pytra_len(text)
        self.i = Int64(0)
    }

    func parse() -> Any {
        self._skip_ws()
        var out: Any = self._parse_value()
        self._skip_ws()
        if (__pytra_int(self.i) != __pytra_int(self.n)) {
            fatalError("pytra raise")
        }
        return out
    }

    func _skip_ws() {
        while ((__pytra_int(self.i) < __pytra_int(self.n)) && _is_ws(__pytra_str(__pytra_getIndex(self.text, self.i)))) {
            self.i += Int64(1)
        }
    }

    func _parse_value() -> Any {
        if (__pytra_int(self.i) >= __pytra_int(self.n)) {
            fatalError("pytra raise")
        }
        var ch: String = __pytra_str(__pytra_getIndex(self.text, self.i))
        if (__pytra_str(ch) == __pytra_str("{")) {
            return self._parse_object()
        }
        if (__pytra_str(ch) == __pytra_str("[")) {
            return self._parse_array()
        }
        if (__pytra_str(ch) == __pytra_str("\"")) {
            return self._parse_string()
        }
        if ((__pytra_str(ch) == __pytra_str("t")) && (__pytra_str(__pytra_slice(self.text, self.i, (self.i + Int64(4)))) == __pytra_str("true"))) {
            self.i += Int64(4)
            return true
        }
        if ((__pytra_str(ch) == __pytra_str("f")) && (__pytra_str(__pytra_slice(self.text, self.i, (self.i + Int64(5)))) == __pytra_str("false"))) {
            self.i += Int64(5)
            return false
        }
        if ((__pytra_str(ch) == __pytra_str("n")) && (__pytra_str(__pytra_slice(self.text, self.i, (self.i + Int64(4)))) == __pytra_str("null"))) {
            self.i += Int64(4)
            return __pytra_any_default()
        }
        return self._parse_number()
    }

    func _parse_object() -> [AnyHashable: Any] {
        var out: [AnyHashable: Any] = __pytra_as_dict([:])
        self.i += Int64(1)
        self._skip_ws()
        if ((__pytra_int(self.i) < __pytra_int(self.n)) && (__pytra_str(__pytra_getIndex(self.text, self.i)) == __pytra_str("}"))) {
            self.i += Int64(1)
            return out
        }
        while true {
            self._skip_ws()
            if ((__pytra_int(self.i) >= __pytra_int(self.n)) || (__pytra_str(__pytra_getIndex(self.text, self.i)) != __pytra_str("\""))) {
                fatalError("pytra raise")
            }
            var key: String = self._parse_string()
            self._skip_ws()
            if ((__pytra_int(self.i) >= __pytra_int(self.n)) || (__pytra_str(__pytra_getIndex(self.text, self.i)) != __pytra_str(":"))) {
                fatalError("pytra raise")
            }
            self.i += Int64(1)
            self._skip_ws()
            out[AnyHashable(__pytra_str(key))] = self._parse_value()
            self._skip_ws()
            if (__pytra_int(self.i) >= __pytra_int(self.n)) {
                fatalError("pytra raise")
            }
            var ch: String = __pytra_str(__pytra_getIndex(self.text, self.i))
            self.i += Int64(1)
            if (__pytra_str(ch) == __pytra_str("}")) {
                return out
            }
            if (__pytra_str(ch) != __pytra_str(",")) {
                fatalError("pytra raise")
            }
        }
        return [:]
    }

    func _parse_array() -> [Any] {
        var out: [Any] = _json_new_array()
        self.i += Int64(1)
        self._skip_ws()
        if ((__pytra_int(self.i) < __pytra_int(self.n)) && (__pytra_str(__pytra_getIndex(self.text, self.i)) == __pytra_str("]"))) {
            self.i += Int64(1)
            return out
        }
        while true {
            self._skip_ws()
            out.append(self._parse_value())
            self._skip_ws()
            if (__pytra_int(self.i) >= __pytra_int(self.n)) {
                fatalError("pytra raise")
            }
            var ch: String = __pytra_str(__pytra_getIndex(self.text, self.i))
            self.i += Int64(1)
            if (__pytra_str(ch) == __pytra_str("]")) {
                return out
            }
            if (__pytra_str(ch) != __pytra_str(",")) {
                fatalError("pytra raise")
            }
        }
        return []
    }

    func _parse_string() -> String {
        if (__pytra_str(__pytra_getIndex(self.text, self.i)) != __pytra_str("\"")) {
            fatalError("pytra raise")
        }
        self.i += Int64(1)
        var out_chars: [Any] = __pytra_as_list([])
        while (__pytra_int(self.i) < __pytra_int(self.n)) {
            var ch: String = __pytra_str(__pytra_getIndex(self.text, self.i))
            self.i += Int64(1)
            if (__pytra_str(ch) == __pytra_str("\"")) {
                return _join_strs(out_chars, _EMPTY)
            }
            if (__pytra_str(ch) == __pytra_str("\\")) {
                if (__pytra_int(self.i) >= __pytra_int(self.n)) {
                    fatalError("pytra raise")
                }
                var esc: String = __pytra_str(__pytra_getIndex(self.text, self.i))
                self.i += Int64(1)
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
                                                    if (__pytra_int(self.i + Int64(4)) > __pytra_int(self.n)) {
                                                        fatalError("pytra raise")
                                                    }
                                                    var hx: String = __pytra_str(__pytra_slice(self.text, self.i, (self.i + Int64(4))))
                                                    self.i += Int64(4)
                                                    out_chars.append(chr(_int_from_hex4(hx)))
                                                } else {
                                                    fatalError("pytra raise")
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
        fatalError("pytra raise")
        return ""
    }

    func _parse_number() -> Any {
        var start: Int64 = __pytra_int(self.i)
        if (__pytra_str(__pytra_getIndex(self.text, self.i)) == __pytra_str("-")) {
            self.i += Int64(1)
        }
        if (__pytra_int(self.i) >= __pytra_int(self.n)) {
            fatalError("pytra raise")
        }
        if (__pytra_str(__pytra_getIndex(self.text, self.i)) == __pytra_str("0")) {
            self.i += Int64(1)
        } else {
            if (!_is_digit(__pytra_str(__pytra_getIndex(self.text, self.i)))) {
                fatalError("pytra raise")
            }
            while ((__pytra_int(self.i) < __pytra_int(self.n)) && _is_digit(__pytra_str(__pytra_getIndex(self.text, self.i)))) {
                self.i += Int64(1)
            }
        }
        var is_float: Bool = false
        if ((__pytra_int(self.i) < __pytra_int(self.n)) && (__pytra_str(__pytra_getIndex(self.text, self.i)) == __pytra_str("."))) {
            is_float = true
            self.i += Int64(1)
            if ((__pytra_int(self.i) >= __pytra_int(self.n)) || (!_is_digit(__pytra_str(__pytra_getIndex(self.text, self.i))))) {
                fatalError("pytra raise")
            }
            while ((__pytra_int(self.i) < __pytra_int(self.n)) && _is_digit(__pytra_str(__pytra_getIndex(self.text, self.i)))) {
                self.i += Int64(1)
            }
        }
        if (__pytra_int(self.i) < __pytra_int(self.n)) {
            var exp_ch: String = __pytra_str(__pytra_getIndex(self.text, self.i))
            if ((__pytra_str(exp_ch) == __pytra_str("e")) || (__pytra_str(exp_ch) == __pytra_str("E"))) {
                is_float = true
                self.i += Int64(1)
                if (__pytra_int(self.i) < __pytra_int(self.n)) {
                    var sign: String = __pytra_str(__pytra_getIndex(self.text, self.i))
                    if ((__pytra_str(sign) == __pytra_str("+")) || (__pytra_str(sign) == __pytra_str("-"))) {
                        self.i += Int64(1)
                    }
                }
                if ((__pytra_int(self.i) >= __pytra_int(self.n)) || (!_is_digit(__pytra_str(__pytra_getIndex(self.text, self.i))))) {
                    fatalError("pytra raise")
                }
                while ((__pytra_int(self.i) < __pytra_int(self.n)) && _is_digit(__pytra_str(__pytra_getIndex(self.text, self.i)))) {
                    self.i += Int64(1)
                }
            }
        }
        var token: String = __pytra_str(__pytra_slice(self.text, start, self.i))
        if is_float {
            var num_f: Double = __pytra_float(token)
            return num_f
        }
        var num_i: Int64 = __pytra_int(token)
        return num_i
    }
}

func _is_ws(_ ch: String) -> Bool {
    return ((__pytra_str(ch) == __pytra_str(" ")) || (__pytra_str(ch) == __pytra_str("	")) || (__pytra_str(ch) == __pytra_str("
")) || (__pytra_str(ch) == __pytra_str("\n")))
}

func _is_digit(_ ch: String) -> Bool {
    return ((__pytra_str(ch) >= __pytra_str("0")) && (__pytra_str(ch) <= __pytra_str("9")))
}

func _hex_value(_ ch: String) -> Int64 {
    if ((__pytra_str(ch) >= __pytra_str("0")) && (__pytra_str(ch) <= __pytra_str("9"))) {
        return __pytra_int(ch)
    }
    if ((__pytra_str(ch) == __pytra_str("a")) || (__pytra_str(ch) == __pytra_str("A"))) {
        return Int64(10)
    }
    if ((__pytra_str(ch) == __pytra_str("b")) || (__pytra_str(ch) == __pytra_str("B"))) {
        return Int64(11)
    }
    if ((__pytra_str(ch) == __pytra_str("c")) || (__pytra_str(ch) == __pytra_str("C"))) {
        return Int64(12)
    }
    if ((__pytra_str(ch) == __pytra_str("d")) || (__pytra_str(ch) == __pytra_str("D"))) {
        return Int64(13)
    }
    if ((__pytra_str(ch) == __pytra_str("e")) || (__pytra_str(ch) == __pytra_str("E"))) {
        return Int64(14)
    }
    if ((__pytra_str(ch) == __pytra_str("f")) || (__pytra_str(ch) == __pytra_str("F"))) {
        return Int64(15)
    }
    fatalError("pytra raise")
    return 0
}

func _int_from_hex4(_ hx: String) -> Int64 {
    if (__pytra_int(__pytra_len(hx)) != __pytra_int(Int64(4))) {
        fatalError("pytra raise")
    }
    var v0: Int64 = _hex_value(__pytra_slice(hx, Int64(0), Int64(1)))
    var v1: Int64 = _hex_value(__pytra_slice(hx, Int64(1), Int64(2)))
    var v2: Int64 = _hex_value(__pytra_slice(hx, Int64(2), Int64(3)))
    var v3: Int64 = _hex_value(__pytra_slice(hx, Int64(3), Int64(4)))
    return ((((v0 * Int64(4096)) + (v1 * Int64(256))) + (v2 * Int64(16))) + v3)
}

func _hex4(_ code: Int64) -> String {
    var v: Int64 = (code % Int64(65536))
    var d3: Int64 = (v % Int64(16))
    v = (v / Int64(16))
    var d2: Int64 = (v % Int64(16))
    v = (v / Int64(16))
    var d1: Int64 = (v % Int64(16))
    v = (v / Int64(16))
    var d0: Int64 = (v % Int64(16))
    var p0: String = __pytra_str(__pytra_slice(_HEX_DIGITS, d0, (d0 + Int64(1))))
    var p1: String = __pytra_str(__pytra_slice(_HEX_DIGITS, d1, (d1 + Int64(1))))
    var p2: String = __pytra_str(__pytra_slice(_HEX_DIGITS, d2, (d2 + Int64(1))))
    var p3: String = __pytra_str(__pytra_slice(_HEX_DIGITS, d3, (d3 + Int64(1))))
    return (__pytra_str(__pytra_str(__pytra_str(p0) + __pytra_str(p1)) + __pytra_str(p2)) + __pytra_str(p3))
}

func _json_array_items(_ raw: Any) -> [Any] {
    return list(raw)
}

func _json_new_array() -> [Any] {
    return list()
}

func _json_obj_require(_ raw: [AnyHashable: Any], _ key: String) -> Any {
    do {
        let __iter_0 = __pytra_as_list(raw.items())
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let __tuple_2 = __pytra_as_list(__iter_0[Int(__i_1)])
            let k = __tuple_2[Int(0)]
            let value = __tuple_2[Int(1)]
            if (__pytra_str(k) == __pytra_str(key)) {
                return value
            }
            __i_1 += 1
        }
    }
    fatalError("pytra raise")
    return __pytra_any_default()
}

func _json_indent_value(_ indent: Any) -> Int64 {
    if (__pytra_float(indent) == __pytra_float(__pytra_any_default())) {
        fatalError("pytra raise")
    }
    var indent_i: Int64 = __pytra_int(indent)
    return indent_i
}

func loads(_ text: String) -> Any {
    return _JsonParser(text).parse()
}

func loads_obj(_ text: String) -> Any {
    var value: Any = _JsonParser(text).parse()
    if false {
        var raw_obj: [AnyHashable: Any] = dict(value)
        return JsonObj(raw_obj)
    }
    return __pytra_any_default()
}

func loads_arr(_ text: String) -> Any {
    var value: Any = _JsonParser(text).parse()
    if false {
        var raw_arr: [Any] = list(value)
        return JsonArr(raw_arr)
    }
    return __pytra_any_default()
}

func _join_strs(_ parts: [Any], _ sep: String) -> String {
    if (__pytra_int(__pytra_len(parts)) == __pytra_int(Int64(0))) {
        return ""
    }
    var out: String = __pytra_str(__pytra_getIndex(parts, Int64(0)))
    var i: Int64 = Int64(1)
    while (__pytra_int(i) < __pytra_int(__pytra_len(parts))) {
        out = (__pytra_str(__pytra_str(out) + __pytra_str(sep)) + __pytra_str(__pytra_getIndex(parts, i)))
        i += Int64(1)
    }
    return out
}

func _escape_str(_ s: String, _ ensure_ascii: Bool) -> String {
    var out: [Any] = __pytra_as_list(["\""])
    do {
        let __iter_0 = __pytra_as_list(s)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let ch: String = __pytra_str(__iter_0[Int(__i_1)])
            var code: Int64 = __pytra_int(ord(ch))
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
                                        if (ensure_ascii && (__pytra_int(code) > __pytra_int(Int64(127)))) {
                                            out.append((__pytra_str("\\u") + __pytra_str(_hex4(code))))
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
            __i_1 += 1
        }
    }
    out.append("\"")
    return _join_strs(out, _EMPTY)
}

func _dump_json_list(_ values: [Any], _ ensure_ascii: Bool, _ indent: Any, _ item_sep: String, _ key_sep: String, _ level: Int64) -> String {
    if (__pytra_int(__pytra_len(values)) == __pytra_int(Int64(0))) {
        return "[]"
    }
    if (__pytra_float(indent) == __pytra_float(__pytra_any_default())) {
        var dumped: [Any] = __pytra_as_list([])
        do {
            let __iter_0 = __pytra_as_list(values)
            var __i_1: Int64 = 0
            while __i_1 < Int64(__iter_0.count) {
                let x = __iter_0[Int(__i_1)]
                var dumped_txt: String = __pytra_str(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level))
                dumped.append(dumped_txt)
                __i_1 += 1
            }
        }
        return (__pytra_str(__pytra_str("[") + __pytra_str(_join_strs(dumped, item_sep))) + __pytra_str("]"))
    }
    var indent_i: Int64 = _json_indent_value(indent)
    var inner: [Any] = __pytra_as_list([])
    do {
        let __iter_2 = __pytra_as_list(values)
        var __i_3: Int64 = 0
        while __i_3 < Int64(__iter_2.count) {
            let x = __iter_2[Int(__i_3)]
            var prefix: String = __pytra_str(" " * (indent_i * (level + Int64(1))))
            var value_txt: String = __pytra_str(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, (level + Int64(1))))
            inner.append((__pytra_str(prefix) + __pytra_str(value_txt)))
            __i_3 += 1
        }
    }
    return __pytra_str(((__pytra_str(__pytra_str("[\n") + __pytra_str(_join_strs(inner, _COMMA_NL))) + __pytra_str("\n")) + (" " * (indent_i * level))) + "]")
}

func _dump_json_dict(_ values: [AnyHashable: Any], _ ensure_ascii: Bool, _ indent: Any, _ item_sep: String, _ key_sep: String, _ level: Int64) -> String {
    if (__pytra_int(__pytra_len(values)) == __pytra_int(Int64(0))) {
        return "{}"
    }
    if (__pytra_float(indent) == __pytra_float(__pytra_any_default())) {
        var parts: [Any] = __pytra_as_list([])
        do {
            let __iter_0 = __pytra_as_list(values.items())
            var __i_1: Int64 = 0
            while __i_1 < Int64(__iter_0.count) {
                let __tuple_2 = __pytra_as_list(__iter_0[Int(__i_1)])
                let k = __tuple_2[Int(0)]
                let x = __tuple_2[Int(1)]
                var k_txt: String = _escape_str(__pytra_str(k), ensure_ascii)
                var v_txt: String = __pytra_str(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level))
                parts.append((__pytra_str(__pytra_str(k_txt) + __pytra_str(key_sep)) + __pytra_str(v_txt)))
                __i_1 += 1
            }
        }
        return (__pytra_str(__pytra_str("{") + __pytra_str(_join_strs(parts, item_sep))) + __pytra_str("}"))
    }
    var indent_i: Int64 = _json_indent_value(indent)
    var inner: [Any] = __pytra_as_list([])
    do {
        let __iter_2 = __pytra_as_list(values.items())
        var __i_3: Int64 = 0
        while __i_3 < Int64(__iter_2.count) {
            let __tuple_4 = __pytra_as_list(__iter_2[Int(__i_3)])
            let k = __tuple_4[Int(0)]
            let x = __tuple_4[Int(1)]
            var prefix: String = __pytra_str(" " * (indent_i * (level + Int64(1))))
            var k_txt: String = _escape_str(__pytra_str(k), ensure_ascii)
            var v_txt: String = __pytra_str(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, (level + Int64(1))))
            inner.append((__pytra_str(__pytra_str(__pytra_str(prefix) + __pytra_str(k_txt)) + __pytra_str(key_sep)) + __pytra_str(v_txt)))
            __i_3 += 1
        }
    }
    return __pytra_str(((__pytra_str(__pytra_str("{\n") + __pytra_str(_join_strs(inner, _COMMA_NL))) + __pytra_str("\n")) + (" " * (indent_i * level))) + "}")
}

func _dump_json_value(_ v: Any, _ ensure_ascii: Bool, _ indent: Any, _ item_sep: String, _ key_sep: String, _ level: Int64) -> String {
    if (__pytra_float(v) == __pytra_float(__pytra_any_default())) {
        return "null"
    }
    if false {
        var raw_b: Bool = __pytra_truthy(v)
        return __pytra_str(__pytra_ifexp(raw_b, "true", "false"))
    }
    if false {
        return __pytra_str(v)
    }
    if false {
        return __pytra_str(v)
    }
    if false {
        return _escape_str(v, ensure_ascii)
    }
    if false {
        var as_list: [Any] = list(v)
        return _dump_json_list(as_list, ensure_ascii, indent, item_sep, key_sep, level)
    }
    if false {
        var as_dict: [AnyHashable: Any] = dict(v)
        return _dump_json_dict(as_dict, ensure_ascii, indent, item_sep, key_sep, level)
    }
    fatalError("pytra raise")
    return ""
}

func dumps(_ obj: Any, _ ensure_ascii: Bool, _ indent: Any, _ separators: [Any]) -> String {
    var item_sep: String = ","
    var key_sep: String = __pytra_str(__pytra_ifexp((__pytra_float(indent) == __pytra_float(__pytra_any_default())), ":", ": "))
    if (__pytra_float(separators) == __pytra_float(__pytra_any_default())) {
        let __tuple_0 = __pytra_as_list(separators)
        item_sep = __tuple_0[0]
        key_sep = __tuple_0[1]
    }
    return _dump_json_value(obj, ensure_ascii, indent, item_sep, key_sep, Int64(0))
}
