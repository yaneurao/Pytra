// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: tools/gen_runtime_from_manifest.py

package main

type JsonObjLike interface {
    get(key string) any
    get_obj(key string) any
    get_arr(key string) any
    get_str(key string) any
    get_int(key string) any
    get_float(key string) any
    get_bool(key string) any
}

type JsonArrLike interface {
    get(index int64) any
    get_obj(index int64) any
    get_arr(index int64) any
    get_str(index int64) any
    get_int(index int64) any
    get_float(index int64) any
    get_bool(index int64) any
}

type JsonValueLike interface {
    as_obj() any
    as_arr() any
    as_str() any
    as_int() any
    as_float() any
    as_bool() any
}

type _JsonParserLike interface {
    parse() any
    _skip_ws()
    _parse_value() any
    _parse_object() map[any]any
    _parse_array() []any
    _parse_string() string
    _parse_number() any
}


func __pytra_is_JsonObj(v any) bool {
    _, ok := v.(*JsonObj)
    return ok
}

func __pytra_as_JsonObj(v any) *JsonObj {
    if t, ok := v.(*JsonObj); ok {
        return t
    }
    return nil
}

func __pytra_is_JsonArr(v any) bool {
    _, ok := v.(*JsonArr)
    return ok
}

func __pytra_as_JsonArr(v any) *JsonArr {
    if t, ok := v.(*JsonArr); ok {
        return t
    }
    return nil
}

func __pytra_is_JsonValue(v any) bool {
    _, ok := v.(*JsonValue)
    return ok
}

func __pytra_as_JsonValue(v any) *JsonValue {
    if t, ok := v.(*JsonValue); ok {
        return t
    }
    return nil
}

func __pytra_is__JsonParser(v any) bool {
    _, ok := v.(*_JsonParser)
    return ok
}

func __pytra_as__JsonParser(v any) *_JsonParser {
    if t, ok := v.(*_JsonParser); ok {
        return t
    }
    return nil
}

type JsonObj struct {
    raw map[any]any
}

func NewJsonObj(raw map[any]any) *JsonObj {
    self := &JsonObj{}
    self.Init(raw)
    return self
}

func (self *JsonObj) Init(raw map[any]any) {
    self.raw = raw
}

func (self *JsonObj) get(key string) any {
    if ((!__pytra_contains(self.raw, key))) {
        return nil
    }
    var value any = _json_obj_require(self.raw, key)
    return NewJsonValue(value)
}

func (self *JsonObj) get_obj(key string) any {
    if ((!__pytra_contains(self.raw, key))) {
        return nil
    }
    var value any = _json_obj_require(self.raw, key)
    return NewJsonValue(value).as_obj()
}

func (self *JsonObj) get_arr(key string) any {
    if ((!__pytra_contains(self.raw, key))) {
        return nil
    }
    var value any = _json_obj_require(self.raw, key)
    return NewJsonValue(value).as_arr()
}

func (self *JsonObj) get_str(key string) any {
    if ((!__pytra_contains(self.raw, key))) {
        return nil
    }
    var value any = _json_obj_require(self.raw, key)
    return NewJsonValue(value).as_str()
}

func (self *JsonObj) get_int(key string) any {
    if ((!__pytra_contains(self.raw, key))) {
        return nil
    }
    var value any = _json_obj_require(self.raw, key)
    return NewJsonValue(value).as_int()
}

func (self *JsonObj) get_float(key string) any {
    if ((!__pytra_contains(self.raw, key))) {
        return nil
    }
    var value any = _json_obj_require(self.raw, key)
    return NewJsonValue(value).as_float()
}

func (self *JsonObj) get_bool(key string) any {
    if ((!__pytra_contains(self.raw, key))) {
        return nil
    }
    var value any = _json_obj_require(self.raw, key)
    return NewJsonValue(value).as_bool()
}

type JsonArr struct {
    raw []any
}

func NewJsonArr(raw []any) *JsonArr {
    self := &JsonArr{}
    self.Init(raw)
    return self
}

func (self *JsonArr) Init(raw []any) {
    self.raw = raw
}

func (self *JsonArr) get(index int64) any {
    if ((index < int64(0)) || (index >= __pytra_len(_json_array_items(self.raw)))) {
        return nil
    }
    return NewJsonValue(__pytra_get_index(_json_array_items(self.raw), index))
}

func (self *JsonArr) get_obj(index int64) any {
    if ((index < int64(0)) || (index >= __pytra_len(_json_array_items(self.raw)))) {
        return nil
    }
    return NewJsonValue(__pytra_get_index(_json_array_items(self.raw), index)).as_obj()
}

func (self *JsonArr) get_arr(index int64) any {
    if ((index < int64(0)) || (index >= __pytra_len(_json_array_items(self.raw)))) {
        return nil
    }
    return NewJsonValue(__pytra_get_index(_json_array_items(self.raw), index)).as_arr()
}

func (self *JsonArr) get_str(index int64) any {
    if ((index < int64(0)) || (index >= __pytra_len(_json_array_items(self.raw)))) {
        return nil
    }
    return NewJsonValue(__pytra_get_index(_json_array_items(self.raw), index)).as_str()
}

func (self *JsonArr) get_int(index int64) any {
    if ((index < int64(0)) || (index >= __pytra_len(_json_array_items(self.raw)))) {
        return nil
    }
    return NewJsonValue(__pytra_get_index(_json_array_items(self.raw), index)).as_int()
}

func (self *JsonArr) get_float(index int64) any {
    if ((index < int64(0)) || (index >= __pytra_len(_json_array_items(self.raw)))) {
        return nil
    }
    return NewJsonValue(__pytra_get_index(_json_array_items(self.raw), index)).as_float()
}

func (self *JsonArr) get_bool(index int64) any {
    if ((index < int64(0)) || (index >= __pytra_len(_json_array_items(self.raw)))) {
        return nil
    }
    return NewJsonValue(__pytra_get_index(_json_array_items(self.raw), index)).as_bool()
}

type JsonValue struct {
    raw any
}

func NewJsonValue(raw any) *JsonValue {
    self := &JsonValue{}
    self.Init(raw)
    return self
}

func (self *JsonValue) Init(raw any) {
    self.raw = raw
}

func (self *JsonValue) as_obj() any {
    var raw any = self.raw
    if false {
        var raw_obj map[any]any = __pytra_as_dict(dict(raw))
        return NewJsonObj(raw_obj)
    }
    return nil
}

func (self *JsonValue) as_arr() any {
    var raw any = self.raw
    if false {
        var raw_arr []any = __pytra_as_list(list(raw))
        return NewJsonArr(raw_arr)
    }
    return nil
}

func (self *JsonValue) as_str() any {
    var raw any = self.raw
    if false {
        return raw
    }
    return nil
}

func (self *JsonValue) as_int() any {
    var raw any = self.raw
    if false {
        return nil
    }
    if false {
        var raw_i int64 = __pytra_int(raw)
        return raw_i
    }
    return nil
}

func (self *JsonValue) as_float() any {
    var raw any = self.raw
    if false {
        var raw_f float64 = __pytra_float(raw)
        return raw_f
    }
    return nil
}

func (self *JsonValue) as_bool() any {
    var raw any = self.raw
    if false {
        var raw_b bool = __pytra_truthy(__pytra_truthy(raw))
        return raw_b
    }
    return nil
}

type _JsonParser struct {
    text string
    n int64
    i int64
}

func New_JsonParser(text string) *_JsonParser {
    self := &_JsonParser{}
    self.Init(text)
    return self
}

func (self *_JsonParser) Init(text string) {
    self.text = text
    self.n = __pytra_len(text)
    self.i = int64(0)
}

func (self *_JsonParser) parse() any {
    self._skip_ws()
    var out any = self._parse_value()
    self._skip_ws()
    if (self.i != self.n) {
        panic(__pytra_str("invalid json: trailing characters"))
    }
    return out
}

func (self *_JsonParser) _skip_ws() {
    for ((self.i < self.n) && _is_ws(__pytra_str(__pytra_get_index(self.text, self.i)))) {
        self.i += int64(1)
    }
}

func (self *_JsonParser) _parse_value() any {
    if (self.i >= self.n) {
        panic(__pytra_str("invalid json: unexpected end"))
    }
    var ch string = __pytra_str(__pytra_str(__pytra_get_index(self.text, self.i)))
    if (__pytra_str(ch) == __pytra_str("{")) {
        return self._parse_object()
    }
    if (__pytra_str(ch) == __pytra_str("[")) {
        return self._parse_array()
    }
    if (__pytra_str(ch) == __pytra_str("\"")) {
        return self._parse_string()
    }
    if ((__pytra_str(ch) == __pytra_str("t")) && (__pytra_str(__pytra_slice(self.text, self.i, (self.i + int64(4)))) == __pytra_str("true"))) {
        self.i += int64(4)
        return true
    }
    if ((__pytra_str(ch) == __pytra_str("f")) && (__pytra_str(__pytra_slice(self.text, self.i, (self.i + int64(5)))) == __pytra_str("false"))) {
        self.i += int64(5)
        return false
    }
    if ((__pytra_str(ch) == __pytra_str("n")) && (__pytra_str(__pytra_slice(self.text, self.i, (self.i + int64(4)))) == __pytra_str("null"))) {
        self.i += int64(4)
        return nil
    }
    return self._parse_number()
}

func (self *_JsonParser) _parse_object() map[any]any {
    var out map[any]any = __pytra_as_dict(map[any]any{})
    self.i += int64(1)
    self._skip_ws()
    if ((self.i < self.n) && (__pytra_str(__pytra_str(__pytra_get_index(self.text, self.i))) == __pytra_str("}"))) {
        self.i += int64(1)
        return __pytra_as_dict(out)
    }
    for true {
        self._skip_ws()
        if ((self.i >= self.n) || (__pytra_str(__pytra_str(__pytra_get_index(self.text, self.i))) != __pytra_str("\""))) {
            panic(__pytra_str("invalid json object key"))
        }
        var key string = __pytra_str(self._parse_string())
        self._skip_ws()
        if ((self.i >= self.n) || (__pytra_str(__pytra_str(__pytra_get_index(self.text, self.i))) != __pytra_str(":"))) {
            panic(__pytra_str("invalid json object: missing ':'"))
        }
        self.i += int64(1)
        self._skip_ws()
        __pytra_set_index(out, key, self._parse_value())
        self._skip_ws()
        if (self.i >= self.n) {
            panic(__pytra_str("invalid json object: unexpected end"))
        }
        var ch string = __pytra_str(__pytra_str(__pytra_get_index(self.text, self.i)))
        self.i += int64(1)
        if (__pytra_str(ch) == __pytra_str("}")) {
            return __pytra_as_dict(out)
        }
        if (__pytra_str(ch) != __pytra_str(",")) {
            panic(__pytra_str("invalid json object separator"))
        }
    }
    return nil
}

func (self *_JsonParser) _parse_array() []any {
    var out []any = __pytra_as_list(_json_new_array())
    self.i += int64(1)
    self._skip_ws()
    if ((self.i < self.n) && (__pytra_str(__pytra_str(__pytra_get_index(self.text, self.i))) == __pytra_str("]"))) {
        self.i += int64(1)
        return __pytra_as_list(out)
    }
    for true {
        self._skip_ws()
        out = append(out, self._parse_value())
        self._skip_ws()
        if (self.i >= self.n) {
            panic(__pytra_str("invalid json array: unexpected end"))
        }
        var ch string = __pytra_str(__pytra_str(__pytra_get_index(self.text, self.i)))
        self.i += int64(1)
        if (__pytra_str(ch) == __pytra_str("]")) {
            return __pytra_as_list(out)
        }
        if (__pytra_str(ch) != __pytra_str(",")) {
            panic(__pytra_str("invalid json array separator"))
        }
    }
    return nil
}

func (self *_JsonParser) _parse_string() string {
    if (__pytra_str(__pytra_str(__pytra_get_index(self.text, self.i))) != __pytra_str("\"")) {
        panic(__pytra_str("invalid json string"))
    }
    self.i += int64(1)
    var out_chars []any = __pytra_as_list([]any{})
    for (self.i < self.n) {
        var ch string = __pytra_str(__pytra_str(__pytra_get_index(self.text, self.i)))
        self.i += int64(1)
        if (__pytra_str(ch) == __pytra_str("\"")) {
            return __pytra_str(_join_strs(out_chars, _EMPTY))
        }
        if (__pytra_str(ch) == __pytra_str("\\")) {
            if (self.i >= self.n) {
                panic(__pytra_str("invalid json string escape"))
            }
            var esc string = __pytra_str(__pytra_str(__pytra_get_index(self.text, self.i)))
            self.i += int64(1)
            if (__pytra_str(esc) == __pytra_str("\"")) {
                out_chars = append(out_chars, "\"")
            } else {
                if (__pytra_str(esc) == __pytra_str("\\")) {
                    out_chars = append(out_chars, "\\")
                } else {
                    if (__pytra_str(esc) == __pytra_str("/")) {
                        out_chars = append(out_chars, "/")
                    } else {
                        if (__pytra_str(esc) == __pytra_str("b")) {
                            out_chars = append(out_chars, "")
                        } else {
                            if (__pytra_str(esc) == __pytra_str("f")) {
                                out_chars = append(out_chars, "
")
                            } else {
                                if (__pytra_str(esc) == __pytra_str("n")) {
                                    out_chars = append(out_chars, "\n")
                                } else {
                                    if (__pytra_str(esc) == __pytra_str("r")) {
                                        out_chars = append(out_chars, "
")
                                    } else {
                                        if (__pytra_str(esc) == __pytra_str("t")) {
                                            out_chars = append(out_chars, "	")
                                        } else {
                                            if (__pytra_str(esc) == __pytra_str("u")) {
                                                if ((self.i + int64(4)) > self.n) {
                                                    panic(__pytra_str("invalid json unicode escape"))
                                                }
                                                var hx string = __pytra_str(__pytra_slice(self.text, self.i, (self.i + int64(4))))
                                                self.i += int64(4)
                                                out_chars = append(out_chars, chr(_int_from_hex4(hx)))
                                            } else {
                                                panic(__pytra_str("invalid json escape"))
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
            out_chars = append(out_chars, ch)
        }
    }
    panic(__pytra_str("unterminated json string"))
    return ""
}

func (self *_JsonParser) _parse_number() any {
    var start int64 = self.i
    if (__pytra_str(__pytra_str(__pytra_get_index(self.text, self.i))) == __pytra_str("-")) {
        self.i += int64(1)
    }
    if (self.i >= self.n) {
        panic(__pytra_str("invalid json number"))
    }
    if (__pytra_str(__pytra_str(__pytra_get_index(self.text, self.i))) == __pytra_str("0")) {
        self.i += int64(1)
    } else {
        if (!_is_digit(__pytra_str(__pytra_get_index(self.text, self.i)))) {
            panic(__pytra_str("invalid json number"))
        }
        for ((self.i < self.n) && _is_digit(__pytra_str(__pytra_get_index(self.text, self.i)))) {
            self.i += int64(1)
        }
    }
    var is_float bool = __pytra_truthy(false)
    if ((self.i < self.n) && (__pytra_str(__pytra_str(__pytra_get_index(self.text, self.i))) == __pytra_str("."))) {
        is_float = __pytra_truthy(true)
        self.i += int64(1)
        if ((self.i >= self.n) || (!_is_digit(__pytra_str(__pytra_get_index(self.text, self.i))))) {
            panic(__pytra_str("invalid json number"))
        }
        for ((self.i < self.n) && _is_digit(__pytra_str(__pytra_get_index(self.text, self.i)))) {
            self.i += int64(1)
        }
    }
    if (self.i < self.n) {
        var exp_ch string = __pytra_str(__pytra_str(__pytra_get_index(self.text, self.i)))
        if ((__pytra_str(exp_ch) == __pytra_str("e")) || (__pytra_str(exp_ch) == __pytra_str("E"))) {
            is_float = __pytra_truthy(true)
            self.i += int64(1)
            if (self.i < self.n) {
                var sign string = __pytra_str(__pytra_str(__pytra_get_index(self.text, self.i)))
                if ((__pytra_str(sign) == __pytra_str("+")) || (__pytra_str(sign) == __pytra_str("-"))) {
                    self.i += int64(1)
                }
            }
            if ((self.i >= self.n) || (!_is_digit(__pytra_str(__pytra_get_index(self.text, self.i))))) {
                panic(__pytra_str("invalid json exponent"))
            }
            for ((self.i < self.n) && _is_digit(__pytra_str(__pytra_get_index(self.text, self.i)))) {
                self.i += int64(1)
            }
        }
    }
    var token string = __pytra_str(__pytra_slice(self.text, start, self.i))
    if is_float {
        var num_f float64 = __pytra_float(token)
        return num_f
    }
    var num_i int64 = __pytra_int(token)
    return num_i
}

func _is_ws(ch string) bool {
    return __pytra_truthy(((__pytra_str(ch) == __pytra_str(" ")) || (__pytra_str(ch) == __pytra_str("	")) || (__pytra_str(ch) == __pytra_str("
")) || (__pytra_str(ch) == __pytra_str("\n"))))
}

func _is_digit(ch string) bool {
    return __pytra_truthy(((__pytra_str(ch) >= __pytra_str("0")) && (__pytra_str(ch) <= __pytra_str("9"))))
}

func _hex_value(ch string) int64 {
    if ((__pytra_str(ch) >= __pytra_str("0")) && (__pytra_str(ch) <= __pytra_str("9"))) {
        return __pytra_int(ch)
    }
    if ((__pytra_str(ch) == __pytra_str("a")) || (__pytra_str(ch) == __pytra_str("A"))) {
        return int64(10)
    }
    if ((__pytra_str(ch) == __pytra_str("b")) || (__pytra_str(ch) == __pytra_str("B"))) {
        return int64(11)
    }
    if ((__pytra_str(ch) == __pytra_str("c")) || (__pytra_str(ch) == __pytra_str("C"))) {
        return int64(12)
    }
    if ((__pytra_str(ch) == __pytra_str("d")) || (__pytra_str(ch) == __pytra_str("D"))) {
        return int64(13)
    }
    if ((__pytra_str(ch) == __pytra_str("e")) || (__pytra_str(ch) == __pytra_str("E"))) {
        return int64(14)
    }
    if ((__pytra_str(ch) == __pytra_str("f")) || (__pytra_str(ch) == __pytra_str("F"))) {
        return int64(15)
    }
    panic(__pytra_str("invalid json unicode escape"))
    return 0
}

func _int_from_hex4(hx string) int64 {
    if (__pytra_len(hx) != int64(4)) {
        panic(__pytra_str("invalid json unicode escape"))
    }
    var v0 int64 = _hex_value(__pytra_slice(hx, int64(0), int64(1)))
    var v1 int64 = _hex_value(__pytra_slice(hx, int64(1), int64(2)))
    var v2 int64 = _hex_value(__pytra_slice(hx, int64(2), int64(3)))
    var v3 int64 = _hex_value(__pytra_slice(hx, int64(3), int64(4)))
    return ((((v0 * int64(4096)) + (v1 * int64(256))) + (v2 * int64(16))) + v3)
}

func _hex4(code int64) string {
    var v int64 = (code % int64(65536))
    var d3 int64 = (v % int64(16))
    v = __pytra_int((v / int64(16)))
    var d2 int64 = (v % int64(16))
    v = __pytra_int((v / int64(16)))
    var d1 int64 = (v % int64(16))
    v = __pytra_int((v / int64(16)))
    var d0 int64 = (v % int64(16))
    var p0 string = __pytra_str(__pytra_slice(_HEX_DIGITS, d0, (d0 + int64(1))))
    var p1 string = __pytra_str(__pytra_slice(_HEX_DIGITS, d1, (d1 + int64(1))))
    var p2 string = __pytra_str(__pytra_slice(_HEX_DIGITS, d2, (d2 + int64(1))))
    var p3 string = __pytra_str(__pytra_slice(_HEX_DIGITS, d3, (d3 + int64(1))))
    return __pytra_str((__pytra_str((__pytra_str((__pytra_str(p0) + __pytra_str(p1))) + __pytra_str(p2))) + __pytra_str(p3)))
}

func _json_array_items(raw any) []any {
    return __pytra_as_list(list(raw))
}

func _json_new_array() []any {
    return __pytra_as_list(list())
}

func _json_obj_require(raw map[any]any, key string) any {
    __iter_0 := __pytra_as_list(raw.items())
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        __it_2 := __iter_0[__i_1]
        __tuple_3 := __pytra_as_list(__it_2)
        var k any = __tuple_3[0]
        _ = k
        var value any = __tuple_3[1]
        _ = value
        if (__pytra_str(k) == __pytra_str(key)) {
            return value
        }
    }
    panic(__pytra_str((__pytra_str("json object key not found: ") + __pytra_str(key))))
    return nil
}

func _json_indent_value(indent any) int64 {
    if (indent == nil) {
        panic(__pytra_str("json indent is required"))
    }
    var indent_i int64 = __pytra_int(indent)
    return indent_i
}

func loads(text string) any {
    return New_JsonParser(text).parse()
}

func loads_obj(text string) any {
    var value any = New_JsonParser(text).parse()
    if false {
        var raw_obj map[any]any = __pytra_as_dict(dict(value))
        return NewJsonObj(raw_obj)
    }
    return nil
}

func loads_arr(text string) any {
    var value any = New_JsonParser(text).parse()
    if false {
        var raw_arr []any = __pytra_as_list(list(value))
        return NewJsonArr(raw_arr)
    }
    return nil
}

func _join_strs(parts []any, sep string) string {
    if (__pytra_len(parts) == int64(0)) {
        return __pytra_str("")
    }
    var out string = __pytra_str(__pytra_str(__pytra_get_index(parts, int64(0))))
    var i int64 = int64(1)
    for (i < __pytra_len(parts)) {
        out = __pytra_str((__pytra_str((__pytra_str(out) + __pytra_str(sep))) + __pytra_str(__pytra_str(__pytra_get_index(parts, i)))))
        i += int64(1)
    }
    return __pytra_str(out)
}

func _escape_str(s string, ensure_ascii bool) string {
    var out []any = __pytra_as_list([]any{"\""})
    __iter_0 := __pytra_as_list(s)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        var ch string = __pytra_str(__iter_0[__i_1])
        var code int64 = ord(ch)
        if (__pytra_str(ch) == __pytra_str("\"")) {
            out = append(out, "\\\"")
        } else {
            if (__pytra_str(ch) == __pytra_str("\\")) {
                out = append(out, "\\\\")
            } else {
                if (__pytra_str(ch) == __pytra_str("")) {
                    out = append(out, "\\b")
                } else {
                    if (__pytra_str(ch) == __pytra_str("
")) {
                        out = append(out, "\\f")
                    } else {
                        if (__pytra_str(ch) == __pytra_str("\n")) {
                            out = append(out, "\\n")
                        } else {
                            if (__pytra_str(ch) == __pytra_str("
")) {
                                out = append(out, "\\r")
                            } else {
                                if (__pytra_str(ch) == __pytra_str("	")) {
                                    out = append(out, "\\t")
                                } else {
                                    if (ensure_ascii && (code > int64(127))) {
                                        out = append(out, (__pytra_str("\\u") + __pytra_str(_hex4(code))))
                                    } else {
                                        out = append(out, ch)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    out = append(out, "\"")
    return __pytra_str(_join_strs(out, _EMPTY))
}

func _dump_json_list(values []any, ensure_ascii bool, indent any, item_sep string, key_sep string, level int64) string {
    if (__pytra_len(values) == int64(0)) {
        return __pytra_str("[]")
    }
    if (indent == nil) {
        var dumped []any = __pytra_as_list([]any{})
        __iter_0 := __pytra_as_list(values)
        for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
            x := __iter_0[__i_1]
            var dumped_txt string = __pytra_str(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level))
            dumped = append(dumped, dumped_txt)
        }
        return __pytra_str((__pytra_str((__pytra_str("[") + __pytra_str(_join_strs(dumped, item_sep)))) + __pytra_str("]")))
    }
    var indent_i int64 = _json_indent_value(indent)
    var inner []any = __pytra_as_list([]any{})
    __iter_2 := __pytra_as_list(values)
    for __i_3 := int64(0); __i_3 < int64(len(__iter_2)); __i_3 += 1 {
        x := __iter_2[__i_3]
        var prefix string = __pytra_str((" " * (indent_i * (level + int64(1)))))
        var value_txt string = __pytra_str(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, (level + int64(1))))
        inner = append(inner, (__pytra_str(prefix) + __pytra_str(value_txt)))
    }
    return __pytra_str((((__pytra_str((__pytra_str("[\n") + __pytra_str(_join_strs(inner, _COMMA_NL)))) + __pytra_str("\n")) + (" " * (indent_i * level))) + "]"))
}

func _dump_json_dict(values map[any]any, ensure_ascii bool, indent any, item_sep string, key_sep string, level int64) string {
    if (__pytra_len(values) == int64(0)) {
        return __pytra_str("{}")
    }
    if (indent == nil) {
        var parts []any = __pytra_as_list([]any{})
        __iter_0 := __pytra_as_list(values.items())
        for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
            __it_2 := __iter_0[__i_1]
            __tuple_3 := __pytra_as_list(__it_2)
            var k any = __tuple_3[0]
            _ = k
            var x any = __tuple_3[1]
            _ = x
            var k_txt string = __pytra_str(_escape_str(__pytra_str(k), ensure_ascii))
            var v_txt string = __pytra_str(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level))
            parts = append(parts, (__pytra_str((__pytra_str(k_txt) + __pytra_str(key_sep))) + __pytra_str(v_txt)))
        }
        return __pytra_str((__pytra_str((__pytra_str("{") + __pytra_str(_join_strs(parts, item_sep)))) + __pytra_str("}")))
    }
    var indent_i int64 = _json_indent_value(indent)
    var inner []any = __pytra_as_list([]any{})
    __iter_4 := __pytra_as_list(values.items())
    for __i_5 := int64(0); __i_5 < int64(len(__iter_4)); __i_5 += 1 {
        __it_6 := __iter_4[__i_5]
        __tuple_7 := __pytra_as_list(__it_6)
        var k any = __tuple_7[0]
        _ = k
        var x any = __tuple_7[1]
        _ = x
        var prefix string = __pytra_str((" " * (indent_i * (level + int64(1)))))
        var k_txt string = __pytra_str(_escape_str(__pytra_str(k), ensure_ascii))
        var v_txt string = __pytra_str(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, (level + int64(1))))
        inner = append(inner, (__pytra_str((__pytra_str((__pytra_str(prefix) + __pytra_str(k_txt))) + __pytra_str(key_sep))) + __pytra_str(v_txt)))
    }
    return __pytra_str((((__pytra_str((__pytra_str("{\n") + __pytra_str(_join_strs(inner, _COMMA_NL)))) + __pytra_str("\n")) + (" " * (indent_i * level))) + "}"))
}

func _dump_json_value(v any, ensure_ascii bool, indent any, item_sep string, key_sep string, level int64) string {
    if (v == nil) {
        return __pytra_str("null")
    }
    if false {
        var raw_b bool = __pytra_truthy(__pytra_truthy(v))
        return __pytra_str(__pytra_ifexp(raw_b, "true", "false"))
    }
    if false {
        return __pytra_str(__pytra_str(v))
    }
    if false {
        return __pytra_str(__pytra_str(v))
    }
    if false {
        return __pytra_str(_escape_str(v, ensure_ascii))
    }
    if false {
        var as_list []any = __pytra_as_list(list(v))
        return __pytra_str(_dump_json_list(as_list, ensure_ascii, indent, item_sep, key_sep, level))
    }
    if false {
        var as_dict map[any]any = __pytra_as_dict(dict(v))
        return __pytra_str(_dump_json_dict(as_dict, ensure_ascii, indent, item_sep, key_sep, level))
    }
    panic(__pytra_str("json.dumps unsupported type"))
    return ""
}

func dumps(obj *Any, ensure_ascii bool, indent any, separators []any) string {
    var item_sep string = __pytra_str(",")
    var key_sep string = __pytra_str(__pytra_ifexp((indent == nil), ":", ": "))
    if (separators == nil) {
        __tuple_0 := __pytra_as_list(separators)
        item_sep = __tuple_0[0]
        key_sep = __tuple_0[1]
    }
    return __pytra_str(_dump_json_value(obj, ensure_ascii, indent, item_sep, key_sep, int64(0)))
}
