// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/native/core/py_runtime.h"

#include "runtime/cpp/generated/std/json.h"
#include "runtime/cpp/native/core/process_runtime.h"
#include "runtime/cpp/native/core/scope_exit.h"

#include "generated/built_in/contains.h"
#include "generated/built_in/scalar_ops.h"
#include "generated/built_in/sequence.h"

namespace pytra::std::json {

    str _EMPTY;
    str _COMMA_NL;
    str _HEX_DIGITS;
    
    /* Pure Python JSON utilities for selfhost-friendly transpilation. */
    
    bool _is_ws(const str& ch) {
        return (ch == " ") || (ch == "\t") || (ch == "\r") || (ch == "\n");
    }
    
    bool _is_digit(const str& ch) {
        return (ch >= "0") && (ch <= "9");
    }
    
    int64 _hex_value(const str& ch) {
        if ((ch >= "0") && (ch <= "9"))
            return py_to_int64(ch);
        if ((ch == "a") || (ch == "A"))
            return 10;
        if ((ch == "b") || (ch == "B"))
            return 11;
        if ((ch == "c") || (ch == "C"))
            return 12;
        if ((ch == "d") || (ch == "D"))
            return 13;
        if ((ch == "e") || (ch == "E"))
            return 14;
        if ((ch == "f") || (ch == "F"))
            return 15;
        throw ValueError("invalid json unicode escape");
    }
    
    int64 _int_from_hex4(const str& hx) {
        if (py_len(hx) != 4)
            throw ValueError("invalid json unicode escape");
        int64 v0 = _hex_value(py_slice(hx, 0, 1));
        int64 v1 = _hex_value(py_slice(hx, 1, 2));
        int64 v2 = _hex_value(py_slice(hx, 2, 3));
        int64 v3 = _hex_value(py_slice(hx, 3, 4));
        return v0 * 4096 + v1 * 256 + v2 * 16 + v3;
    }
    
    str _hex4(int64 code) {
        int64 v = code % 65536;
        int64 d3 = v % 16;
        v = v / 16;
        int64 d2 = v % 16;
        v = v / 16;
        int64 d1 = v % 16;
        v = v / 16;
        int64 d0 = v % 16;
        str p0 = py_to_string(py_slice(_HEX_DIGITS, d0, d0 + 1));
        str p1 = py_to_string(py_slice(_HEX_DIGITS, d1, d1 + 1));
        str p2 = py_to_string(py_slice(_HEX_DIGITS, d2, d2 + 1));
        str p3 = py_to_string(py_slice(_HEX_DIGITS, d3, d3 + 1));
        return p0 + p1 + p2 + p3;
    }
    
    list<object> _json_array_items(const object& raw) {
        return list<object>(raw);
    }
    
    list<object> _json_new_array() {
        return list<object>{};
    }
    
    object _json_obj_require(const dict<str, object>& raw, const str& key) {
        for (::std::tuple<str, object> __itobj_1 : raw) {
            str k = py_to_string(py_at(__itobj_1, 0));
            auto value = py_at(__itobj_1, 1);
            if (k == key)
                return value;
        }
        throw ValueError("json object key not found: " + key);
    }
    
    int64 _json_indent_value(const ::std::optional<int64>& indent) {
        if (py_is_none(indent))
            throw ValueError("json indent is required");
        int64 indent_i = (indent).value();
        return indent_i;
    }
    

    JsonObj::JsonObj(const dict<str, object>& raw) {
            this->raw = raw;
    }

    ::std::optional<JsonValue> JsonObj::get(const str& key) {
            if (!py_contains(this->raw, key))
                return ::std::nullopt;
            object value = make_object(_json_obj_require(this->raw, key));
            return JsonValue(value);
    }

    ::std::optional<JsonObj> JsonObj::get_obj(const str& key) {
            if (!py_contains(this->raw, key))
                return ::std::nullopt;
            object value = make_object(_json_obj_require(this->raw, key));
            return JsonValue(value).as_obj();
    }

    ::std::optional<JsonArr> JsonObj::get_arr(const str& key) {
            if (!py_contains(this->raw, key))
                return ::std::nullopt;
            object value = make_object(_json_obj_require(this->raw, key));
            return JsonValue(value).as_arr();
    }

    ::std::optional<str> JsonObj::get_str(const str& key) {
            if (!py_contains(this->raw, key))
                return ::std::nullopt;
            object value = make_object(_json_obj_require(this->raw, key));
            return JsonValue(value).as_str();
    }

    ::std::optional<int64> JsonObj::get_int(const str& key) {
            if (!py_contains(this->raw, key))
                return ::std::nullopt;
            object value = make_object(_json_obj_require(this->raw, key));
            return JsonValue(value).as_int();
    }

    ::std::optional<float64> JsonObj::get_float(const str& key) {
            if (!py_contains(this->raw, key))
                return ::std::nullopt;
            object value = make_object(_json_obj_require(this->raw, key));
            return JsonValue(value).as_float();
    }

    ::std::optional<bool> JsonObj::get_bool(const str& key) {
            if (!py_contains(this->raw, key))
                return ::std::nullopt;
            object value = make_object(_json_obj_require(this->raw, key));
            return JsonValue(value).as_bool();
    }
    

    JsonArr::JsonArr(const object& raw) {
            this->raw = raw;
    }

    ::std::optional<JsonValue> JsonArr::get(int64 index) {
            if ((index < 0) || (index >= py_len(_json_array_items(this->raw))))
                return ::std::nullopt;
            return JsonValue(py_at(_json_array_items(this->raw), py_to<int64>(index)));
    }

    ::std::optional<JsonObj> JsonArr::get_obj(int64 index) {
            if ((index < 0) || (index >= py_len(_json_array_items(this->raw))))
                return ::std::nullopt;
            return JsonValue(py_at(_json_array_items(this->raw), py_to<int64>(index))).as_obj();
    }

    ::std::optional<JsonArr> JsonArr::get_arr(int64 index) {
            if ((index < 0) || (index >= py_len(_json_array_items(this->raw))))
                return ::std::nullopt;
            return JsonValue(py_at(_json_array_items(this->raw), py_to<int64>(index))).as_arr();
    }

    ::std::optional<str> JsonArr::get_str(int64 index) {
            if ((index < 0) || (index >= py_len(_json_array_items(this->raw))))
                return ::std::nullopt;
            return JsonValue(py_at(_json_array_items(this->raw), py_to<int64>(index))).as_str();
    }

    ::std::optional<int64> JsonArr::get_int(int64 index) {
            if ((index < 0) || (index >= py_len(_json_array_items(this->raw))))
                return ::std::nullopt;
            return JsonValue(py_at(_json_array_items(this->raw), py_to<int64>(index))).as_int();
    }

    ::std::optional<float64> JsonArr::get_float(int64 index) {
            if ((index < 0) || (index >= py_len(_json_array_items(this->raw))))
                return ::std::nullopt;
            return JsonValue(py_at(_json_array_items(this->raw), py_to<int64>(index))).as_float();
    }

    ::std::optional<bool> JsonArr::get_bool(int64 index) {
            if ((index < 0) || (index >= py_len(_json_array_items(this->raw))))
                return ::std::nullopt;
            return JsonValue(py_at(_json_array_items(this->raw), py_to<int64>(index))).as_bool();
    }
    

    JsonValue::JsonValue(const object& raw) {
            this->raw = make_object(raw);
    }

    ::std::optional<JsonObj> JsonValue::as_obj() {
            object raw = make_object(this->raw);
            if (py_runtime_value_isinstance(raw, PYTRA_TID_DICT)) {
                dict<str, object> raw_obj = dict<str, object>(raw);
                return JsonObj(raw_obj);
            }
            return ::std::nullopt;
    }

    ::std::optional<JsonArr> JsonValue::as_arr() {
            object raw = make_object(this->raw);
            if (py_runtime_value_isinstance(raw, PYTRA_TID_LIST)) {
                object raw_arr = make_object(list<object>(raw));
                return JsonArr(raw_arr);
            }
            return ::std::nullopt;
    }

    ::std::optional<str> JsonValue::as_str() {
            object raw = make_object(this->raw);
            if (py_runtime_value_isinstance(raw, PYTRA_TID_STR))
                return raw;
            return ::std::nullopt;
    }

    ::std::optional<int64> JsonValue::as_int() {
            object raw = make_object(this->raw);
            if (py_runtime_value_isinstance(raw, PYTRA_TID_BOOL))
                return ::std::nullopt;
            if (py_runtime_value_isinstance(raw, PYTRA_TID_INT)) {
                int64 raw_i = py_to_int64(raw);
                return raw_i;
            }
            return ::std::nullopt;
    }

    ::std::optional<float64> JsonValue::as_float() {
            object raw = make_object(this->raw);
            if (py_runtime_value_isinstance(raw, PYTRA_TID_FLOAT)) {
                float64 raw_f = py_to_float64(raw);
                return raw_f;
            }
            return ::std::nullopt;
    }

    ::std::optional<bool> JsonValue::as_bool() {
            object raw = make_object(this->raw);
            if (py_runtime_value_isinstance(raw, PYTRA_TID_BOOL)) {
                bool raw_b = py_to<bool>(raw);
                return raw_b;
            }
            return ::std::nullopt;
    }
    

    _JsonParser::_JsonParser(const str& text) {
            this->text = text;
            this->n = py_len(text);
            this->i = 0;
    }

    object _JsonParser::parse() {
            this->_skip_ws();
            object out = make_object(this->_parse_value());
            this->_skip_ws();
            if (this->i != this->n)
                throw ValueError("invalid json: trailing characters");
            return out;
    }

    void _JsonParser::_skip_ws() {
            while ((this->i < this->n) && (_is_ws(this->text[this->i]))) {
                this->i++;
            }
    }

    object _JsonParser::_parse_value() {
            if (this->i >= this->n)
                throw ValueError("invalid json: unexpected end");
            str ch = this->text[this->i];
            if (ch == "{")
                return make_object(this->_parse_object());
            if (ch == "[")
                return make_object(this->_parse_array());
            if (ch == "\"")
                return make_object(this->_parse_string());
            if ((ch == "t") && (py_slice(this->text, this->i, this->i + 4) == "true")) {
                this->i += 4;
                return make_object(true);
            }
            if ((ch == "f") && (py_slice(this->text, this->i, this->i + 5) == "false")) {
                this->i += 5;
                return make_object(false);
            }
            if ((ch == "n") && (py_slice(this->text, this->i, this->i + 4) == "null")) {
                this->i += 4;
                return make_object(::std::nullopt);
            }
            return this->_parse_number();
    }

    dict<str, object> _JsonParser::_parse_object() {
            dict<str, object> out = dict<str, object>{};
            this->i++;
            this->_skip_ws();
            if ((this->i < this->n) && (this->text[this->i] == "}")) {
                this->i++;
                return out;
            }
            while (true) {
                this->_skip_ws();
                if ((this->i >= this->n) || (this->text[this->i] != "\""))
                    throw ValueError("invalid json object key");
                str key = this->_parse_string();
                this->_skip_ws();
                if ((this->i >= this->n) || (this->text[this->i] != ":"))
                    throw ValueError("invalid json object: missing ':'");
                this->i++;
                this->_skip_ws();
                out[key] = make_object(this->_parse_value());
                this->_skip_ws();
                if (this->i >= this->n)
                    throw ValueError("invalid json object: unexpected end");
                str ch = this->text[this->i];
                this->i++;
                if (ch == "}")
                    return out;
                if (ch != ",")
                    throw ValueError("invalid json object separator");
            }
    }

    object _JsonParser::_parse_array() {
            list<object> out = _json_new_array();
            this->i++;
            this->_skip_ws();
            if ((this->i < this->n) && (this->text[this->i] == "]")) {
                this->i++;
                return out;
            }
            while (true) {
                this->_skip_ws();
                out.append(this->_parse_value());
                this->_skip_ws();
                if (this->i >= this->n)
                    throw ValueError("invalid json array: unexpected end");
                str ch = this->text[this->i];
                this->i++;
                if (ch == "]")
                    return out;
                if (ch != ",")
                    throw ValueError("invalid json array separator");
            }
    }

    str _JsonParser::_parse_string() {
            if (this->text[this->i] != "\"")
                throw ValueError("invalid json string");
            this->i++;
            rc<list<str>> out_chars = rc_list_from_value(list<str>{});
            while (this->i < this->n) {
                str ch = this->text[this->i];
                this->i++;
                if (ch == "\"")
                    return _join_strs(out_chars, _EMPTY);
                if (ch == "\\") {
                    if (this->i >= this->n)
                        throw ValueError("invalid json string escape");
                    str esc = this->text[this->i];
                    this->i++;
                    if (esc == "\"") {
                        py_list_append_mut(rc_list_ref(out_chars), "\"");
                    } else if (esc == "\\") {
                        py_list_append_mut(rc_list_ref(out_chars), "\\");
                    } else if (esc == "/") {
                        py_list_append_mut(rc_list_ref(out_chars), "/");
                    } else if (esc == "b") {
                        py_list_append_mut(rc_list_ref(out_chars), "\b");
                    } else if (esc == "f") {
                        py_list_append_mut(rc_list_ref(out_chars), "\f");
                    } else if (esc == "n") {
                        py_list_append_mut(rc_list_ref(out_chars), "\n");
                    } else if (esc == "r") {
                        py_list_append_mut(rc_list_ref(out_chars), "\r");
                    } else if (esc == "t") {
                        py_list_append_mut(rc_list_ref(out_chars), "\t");
                    } else if (esc == "u") {
                        if (this->i + 4 > this->n)
                            throw ValueError("invalid json unicode escape");
                        str hx = py_slice(this->text, this->i, this->i + 4);
                        this->i += 4;
                        py_list_append_mut(rc_list_ref(out_chars), py_chr(_int_from_hex4(hx)));
                    } else {
                        throw ValueError("invalid json escape");
                    }
                } else {
                    py_list_append_mut(rc_list_ref(out_chars), ch);
                }
            }
            throw ValueError("unterminated json string");
    }

    object _JsonParser::_parse_number() {
            int64 start = this->i;
            if (this->text[this->i] == "-")
                this->i++;
            if (this->i >= this->n)
                throw ValueError("invalid json number");
            if (this->text[this->i] == "0") {
                this->i++;
            } else {
                if (!(_is_digit(this->text[this->i])))
                    throw ValueError("invalid json number");
                while ((this->i < this->n) && (_is_digit(this->text[this->i]))) {
                    this->i++;
                }
            }
            bool is_float = false;
            if ((this->i < this->n) && (this->text[this->i] == ".")) {
                is_float = true;
                this->i++;
                if ((this->i >= this->n) || (!(_is_digit(this->text[this->i]))))
                    throw ValueError("invalid json number");
                while ((this->i < this->n) && (_is_digit(this->text[this->i]))) {
                    this->i++;
                }
            }
            if (this->i < this->n) {
                str exp_ch = this->text[this->i];
                if ((exp_ch == "e") || (exp_ch == "E")) {
                    is_float = true;
                    this->i++;
                    if (this->i < this->n) {
                        str sign = this->text[this->i];
                        if ((sign == "+") || (sign == "-"))
                            this->i++;
                    }
                    if ((this->i >= this->n) || (!(_is_digit(this->text[this->i]))))
                        throw ValueError("invalid json exponent");
                    while ((this->i < this->n) && (_is_digit(this->text[this->i]))) {
                        this->i++;
                    }
                }
            }
            str token = py_slice(this->text, start, this->i);
            if (is_float) {
                float64 num_f = py_to_float64(token);
                return make_object(num_f);
            }
            int64 num_i = py_to_int64(token);
            return make_object(num_i);
    }
    
    object loads(const str& text) {
        return _JsonParser(text).parse();
    }
    
    ::std::optional<JsonObj> loads_obj(const str& text) {
        object value = make_object(_JsonParser(text).parse());
        if (py_runtime_value_isinstance(value, PYTRA_TID_DICT)) {
            dict<str, object> raw_obj = dict<str, object>(value);
            return JsonObj(raw_obj);
        }
        return ::std::nullopt;
    }
    
    ::std::optional<JsonArr> loads_arr(const str& text) {
        object value = make_object(_JsonParser(text).parse());
        if (py_runtime_value_isinstance(value, PYTRA_TID_LIST)) {
            object raw_arr = make_object(list<object>(value));
            return JsonArr(raw_arr);
        }
        return ::std::nullopt;
    }
    
    str _join_strs(const rc<list<str>>& parts, const str& sep) {
        if ((rc_list_ref(parts)).empty())
            return "";
        str out = py_at(parts, py_to<int64>(0));
        int64 i = 1;
        while (i < py_len(parts)) {
            out = out + sep + py_at(parts, py_to<int64>(i));
            i++;
        }
        return out;
    }
    
    str _escape_str(const str& s, bool ensure_ascii) {
        rc<list<str>> out = rc_list_from_value(list<str>{"\""});
        for (str ch : s) {
            int64 code = py_to<int64>(py_ord(ch));
            if (ch == "\"") {
                py_list_append_mut(rc_list_ref(out), "\\\"");
            } else if (ch == "\\") {
                py_list_append_mut(rc_list_ref(out), "\\\\");
            } else if (ch == "\b") {
                py_list_append_mut(rc_list_ref(out), "\\b");
            } else if (ch == "\f") {
                py_list_append_mut(rc_list_ref(out), "\\f");
            } else if (ch == "\n") {
                py_list_append_mut(rc_list_ref(out), "\\n");
            } else if (ch == "\r") {
                py_list_append_mut(rc_list_ref(out), "\\r");
            } else if (ch == "\t") {
                py_list_append_mut(rc_list_ref(out), "\\t");
            } else if ((ensure_ascii) && (code > 0x7F)) {
                py_list_append_mut(rc_list_ref(out), "\\u" + _hex4(code));
            } else {
                py_list_append_mut(rc_list_ref(out), ch);
            }
        }
        py_list_append_mut(rc_list_ref(out), "\"");
        return _join_strs(out, _EMPTY);
    }
    
    str _dump_json_list(const object& values, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level) {
        if (py_len(values) == 0)
            return "[]";
        if (py_is_none(indent)) {
            rc<list<str>> dumped = rc_list_from_value(list<str>{});
            {
                object __iter_obj_2 = ([&]() -> object { object __obj = values; if (!__obj) throw TypeError("NoneType is not iterable"); return __obj->py_iter_or_raise(); }());
                while (true) {
                    ::std::optional<object> __next_3 = ([&]() -> ::std::optional<object> { object __iter = __iter_obj_2; if (!__iter) throw TypeError("NoneType is not an iterator"); return __iter->py_next_or_stop(); }());
                    if (!__next_3.has_value()) break;
                    object x = *__next_3;
                    str dumped_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level);
                    py_list_append_mut(rc_list_ref(dumped), dumped_txt);
                }
            }
            return "[" + _join_strs(dumped, item_sep) + "]";
        }
        int64 indent_i = _json_indent_value(indent);
        rc<list<str>> inner = rc_list_from_value(list<str>{});
        {
            object __iter_obj_4 = ([&]() -> object { object __obj = values; if (!__obj) throw TypeError("NoneType is not iterable"); return __obj->py_iter_or_raise(); }());
            while (true) {
                ::std::optional<object> __next_5 = ([&]() -> ::std::optional<object> { object __iter = __iter_obj_4; if (!__iter) throw TypeError("NoneType is not an iterator"); return __iter->py_next_or_stop(); }());
                if (!__next_5.has_value()) break;
                object x = *__next_5;
                str prefix = py_repeat(" ", indent_i * (level + 1));
                str value_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1);
                py_list_append_mut(rc_list_ref(inner), prefix + value_txt);
            }
        }
        return "[\n" + _join_strs(inner, _COMMA_NL) + "\n" + py_repeat(" ", indent_i * level) + "]";
    }
    
    str _dump_json_dict(const dict<str, object>& values, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level) {
        if (py_len(values) == 0)
            return "{}";
        if (py_is_none(indent)) {
            rc<list<str>> parts = rc_list_from_value(list<str>{});
            for (::std::tuple<str, object> __itobj_6 : values) {
                str k = py_to_string(py_at(__itobj_6, 0));
                auto x = py_at(__itobj_6, 1);
                str k_txt = _escape_str(k, ensure_ascii);
                str v_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level);
                py_list_append_mut(rc_list_ref(parts), k_txt + key_sep + v_txt);
            }
            return "{" + _join_strs(parts, item_sep) + "}";
        }
        int64 indent_i = _json_indent_value(indent);
        rc<list<str>> inner = rc_list_from_value(list<str>{});
        for (::std::tuple<str, object> __itobj_7 : values) {
            str k = py_to_string(py_at(__itobj_7, 0));
            auto x = py_at(__itobj_7, 1);
            str prefix = py_repeat(" ", indent_i * (level + 1));
            str k_txt = _escape_str(k, ensure_ascii);
            str v_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1);
            py_list_append_mut(rc_list_ref(inner), prefix + k_txt + key_sep + v_txt);
        }
        return "{\n" + _join_strs(inner, _COMMA_NL) + "\n" + py_repeat(" ", indent_i * level) + "}";
    }
    
    str _dump_json_value(const object& v, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level) {
        if (py_is_none(v))
            return "null";
        if (py_runtime_value_isinstance(v, PYTRA_TID_BOOL)) {
            bool raw_b = py_to<bool>(v);
            return (raw_b ? "true" : "false");
        }
        if (py_runtime_value_isinstance(v, PYTRA_TID_INT))
            return py_to_string(v);
        if (py_runtime_value_isinstance(v, PYTRA_TID_FLOAT))
            return py_to_string(v);
        if (py_runtime_value_isinstance(v, PYTRA_TID_STR))
            return _escape_str(py_to_string(v), ensure_ascii);
        if (py_runtime_value_isinstance(v, PYTRA_TID_LIST)) {
            object as_list = make_object(list<object>(v));
            return _dump_json_list(as_list, ensure_ascii, indent, item_sep, key_sep, level);
        }
        if (py_runtime_value_isinstance(v, PYTRA_TID_DICT)) {
            dict<str, object> as_dict = dict<str, object>(v);
            return _dump_json_dict(as_dict, ensure_ascii, indent, item_sep, key_sep, level);
        }
        throw TypeError("json.dumps unsupported type");
    }
    
    str dumps(const object& obj, bool ensure_ascii, const ::std::optional<int64>& indent, const ::std::optional<::std::tuple<str, str>>& separators) {
        str item_sep = ",";
        str key_sep = (py_is_none(indent) ? ":" : ": ");
        if (!py_is_none(separators)) {
            auto __tuple_8 = *(separators);
            item_sep = ::std::get<0>(__tuple_8);
            key_sep = ::std::get<1>(__tuple_8);
        }
        return _dump_json_value(obj, ensure_ascii, indent, item_sep, key_sep, 0);
    }
    
    static void __pytra_module_init() {
        static bool __initialized = false;
        if (__initialized) return;
        __initialized = true;
        _EMPTY = "";
        _COMMA_NL = ",\n";
        _HEX_DIGITS = "0123456789abcdef";
    }
    
    namespace {
        struct __pytra_module_initializer {
            __pytra_module_initializer() { __pytra_module_init(); }
        };
        static const __pytra_module_initializer __pytra_module_initializer_instance{};
    }  // namespace
    
}  // namespace pytra::std::json
