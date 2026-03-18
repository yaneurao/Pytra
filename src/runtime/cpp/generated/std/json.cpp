// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/native/core/py_runtime.h"

#include "runtime/cpp/generated/std/json.h"
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
            return int64(::std::stoll(ch));
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
        if (hx.size() != 4)
            throw ValueError("invalid json unicode escape");
        int64 v0 = _hex_value(py_str_slice(hx, 0, 1));
        int64 v1 = _hex_value(py_str_slice(hx, 1, 2));
        int64 v2 = _hex_value(py_str_slice(hx, 2, 3));
        int64 v3 = _hex_value(py_str_slice(hx, 3, 4));
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
        str p0 = py_to_string(py_str_slice(_HEX_DIGITS, d0, d0 + 1));
        str p1 = py_to_string(py_str_slice(_HEX_DIGITS, d1, d1 + 1));
        str p2 = py_to_string(py_str_slice(_HEX_DIGITS, d2, d2 + 1));
        str p3 = py_to_string(py_str_slice(_HEX_DIGITS, d3, d3 + 1));
        return p0 + p1 + p2 + p3;
    }
    
    int64 _json_indent_value(const ::std::optional<int64>& indent) {
        if (!indent.has_value())
            throw ValueError("json indent is required");
        int64 indent_i = (indent).value();
        return indent_i;
    }
    
    JsonVal _jv_obj_require(const dict<str, JsonVal>& raw, const str& key) {
        for (::std::tuple<str, JsonVal> __itobj_1 : raw) {
            str k = py_to_string(py_at(__itobj_1, 0));
            JsonVal value = py_at(__itobj_1, 1);
            if (k == key)
                return value;
        }
        throw ValueError("json object key not found: " + key);
    }
    

    JsonObj::JsonObj(const dict<str, JsonVal>& raw) {
            this->raw = raw;
    }

    ::std::optional<JsonValue> JsonObj::get(const str& key) const {
            if (!py_contains(this->raw, key))
                return ::std::nullopt;
            return JsonValue(_jv_obj_require(this->raw, key));
    }

    ::std::optional<JsonObj> JsonObj::get_obj(const str& key) const {
            if (!py_contains(this->raw, key))
                return ::std::nullopt;
            return JsonValue(_jv_obj_require(this->raw, key)).as_obj();
    }

    ::std::optional<JsonArr> JsonObj::get_arr(const str& key) const {
            if (!py_contains(this->raw, key))
                return ::std::nullopt;
            return JsonValue(_jv_obj_require(this->raw, key)).as_arr();
    }

    ::std::optional<str> JsonObj::get_str(const str& key) const {
            if (!py_contains(this->raw, key))
                return ::std::nullopt;
            return JsonValue(_jv_obj_require(this->raw, key)).as_str();
    }

    ::std::optional<int64> JsonObj::get_int(const str& key) const {
            if (!py_contains(this->raw, key))
                return ::std::nullopt;
            return JsonValue(_jv_obj_require(this->raw, key)).as_int();
    }

    ::std::optional<float64> JsonObj::get_float(const str& key) const {
            if (!py_contains(this->raw, key))
                return ::std::nullopt;
            return JsonValue(_jv_obj_require(this->raw, key)).as_float();
    }

    ::std::optional<bool> JsonObj::get_bool(const str& key) const {
            if (!py_contains(this->raw, key))
                return ::std::nullopt;
            return JsonValue(_jv_obj_require(this->raw, key)).as_bool();
    }
    

    JsonArr::JsonArr(const rc<list<JsonVal>>& raw) {
            this->raw = raw;
    }

    ::std::optional<JsonValue> JsonArr::get(int64 index) const {
            if ((index < 0) || (index >= (rc_list_ref(this->raw)).size()))
                return ::std::nullopt;
            return JsonValue(py_list_at_ref(rc_list_ref(this->raw), index));
    }

    ::std::optional<JsonObj> JsonArr::get_obj(int64 index) const {
            if ((index < 0) || (index >= (rc_list_ref(this->raw)).size()))
                return ::std::nullopt;
            return JsonValue(py_list_at_ref(rc_list_ref(this->raw), index)).as_obj();
    }

    ::std::optional<JsonArr> JsonArr::get_arr(int64 index) const {
            if ((index < 0) || (index >= (rc_list_ref(this->raw)).size()))
                return ::std::nullopt;
            return JsonValue(py_list_at_ref(rc_list_ref(this->raw), index)).as_arr();
    }

    ::std::optional<str> JsonArr::get_str(int64 index) const {
            if ((index < 0) || (index >= (rc_list_ref(this->raw)).size()))
                return ::std::nullopt;
            return JsonValue(py_list_at_ref(rc_list_ref(this->raw), index)).as_str();
    }

    ::std::optional<int64> JsonArr::get_int(int64 index) const {
            if ((index < 0) || (index >= (rc_list_ref(this->raw)).size()))
                return ::std::nullopt;
            return JsonValue(py_list_at_ref(rc_list_ref(this->raw), index)).as_int();
    }

    ::std::optional<float64> JsonArr::get_float(int64 index) const {
            if ((index < 0) || (index >= (rc_list_ref(this->raw)).size()))
                return ::std::nullopt;
            return JsonValue(py_list_at_ref(rc_list_ref(this->raw), index)).as_float();
    }

    ::std::optional<bool> JsonArr::get_bool(int64 index) const {
            if ((index < 0) || (index >= (rc_list_ref(this->raw)).size()))
                return ::std::nullopt;
            return JsonValue(py_list_at_ref(rc_list_ref(this->raw), index)).as_bool();
    }
    

    JsonValue::JsonValue(const JsonVal& raw) {
            this->raw = raw;
    }

    ::std::optional<JsonObj> JsonValue::as_obj() const {
            JsonVal jv = this->raw;
            if ((jv).tag == PYTRA_TID_DICT)
                return JsonObj(cast(dict, jv));
            return ::std::nullopt;
    }

    ::std::optional<JsonArr> JsonValue::as_arr() const {
            JsonVal jv = this->raw;
            if ((jv).tag == PYTRA_TID_LIST)
                return JsonArr(py_to<rc<list<JsonVal>>>(cast(list, jv)));
            return ::std::nullopt;
    }

    ::std::optional<str> JsonValue::as_str() const {
            JsonVal jv = this->raw;
            if ((jv).tag == PYTRA_TID_STR)
                return jv.str_val;
            return ::std::nullopt;
    }

    ::std::optional<int64> JsonValue::as_int() const {
            JsonVal jv = this->raw;
            if ((jv).tag == PYTRA_TID_INT)
                return jv.int64_val;
            return ::std::nullopt;
    }

    ::std::optional<float64> JsonValue::as_float() const {
            JsonVal jv = this->raw;
            if ((jv).tag == PYTRA_TID_FLOAT)
                return jv.float64_val;
            return ::std::nullopt;
    }

    ::std::optional<bool> JsonValue::as_bool() const {
            JsonVal jv = this->raw;
            if ((jv).tag == PYTRA_TID_BOOL)
                return jv.bool_val;
            return ::std::nullopt;
    }
    

    _JsonParser::_JsonParser(const str& text) {
            this->text = text;
            this->n = text.size();
            this->i = 0;
    }

    JsonVal _JsonParser::parse() {
            this->_skip_ws();
            JsonVal out = this->_parse_value();
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

    JsonVal _JsonParser::_parse_value() {
            if (this->i >= this->n)
                throw ValueError("invalid json: unexpected end");
            str ch = this->text[this->i];
            if (ch == "{")
                return this->_parse_object();
            if (ch == "[")
                return this->_parse_array();
            if (ch == "\"")
                return this->_parse_string();
            if ((ch == "t") && (py_str_slice(this->text, this->i, this->i + 4) == "true")) {
                this->i += 4;
                return true;
            }
            if ((ch == "f") && (py_str_slice(this->text, this->i, this->i + 5) == "false")) {
                this->i += 5;
                return false;
            }
            if ((ch == "n") && (py_str_slice(this->text, this->i, this->i + 4) == "null")) {
                this->i += 4;
                return ::std::nullopt;
            }
            return this->_parse_number();
    }

    dict<str, JsonVal> _JsonParser::_parse_object() {
            dict<str, JsonVal> out = {};
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
                out[key] = this->_parse_value();
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

    rc<list<JsonVal>> _JsonParser::_parse_array() {
            rc<list<JsonVal>> out = rc_list_from_value(list<JsonVal>{});
            this->i++;
            this->_skip_ws();
            if ((this->i < this->n) && (this->text[this->i] == "]")) {
                this->i++;
                return out;
            }
            while (true) {
                this->_skip_ws();
                rc_list_ref(out).append(this->_parse_value());
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
                        rc_list_ref(out_chars).append("\"");
                    } else if (esc == "\\") {
                        rc_list_ref(out_chars).append("\\");
                    } else if (esc == "/") {
                        rc_list_ref(out_chars).append("/");
                    } else if (esc == "b") {
                        rc_list_ref(out_chars).append("\b");
                    } else if (esc == "f") {
                        rc_list_ref(out_chars).append("\f");
                    } else if (esc == "n") {
                        rc_list_ref(out_chars).append("\n");
                    } else if (esc == "r") {
                        rc_list_ref(out_chars).append("\r");
                    } else if (esc == "t") {
                        rc_list_ref(out_chars).append("\t");
                    } else if (esc == "u") {
                        if (this->i + 4 > this->n)
                            throw ValueError("invalid json unicode escape");
                        str hx = py_str_slice(this->text, this->i, this->i + 4);
                        this->i += 4;
                        rc_list_ref(out_chars).append(py_chr(_int_from_hex4(hx)));
                    } else {
                        throw ValueError("invalid json escape");
                    }
                } else {
                    rc_list_ref(out_chars).append(ch);
                }
            }
            throw ValueError("unterminated json string");
    }

    JsonVal _JsonParser::_parse_number() {
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
            str token = py_str_slice(this->text, start, this->i);
            if (is_float) {
                float64 num_f = float64(::std::stod(token.std()));
                return num_f;
            }
            int64 num_i = int64(::std::stoll(token));
            return num_i;
    }
    
    JsonValue loads(const str& text) {
        return JsonValue(_JsonParser(text).parse());
    }
    
    ::std::optional<JsonObj> loads_obj(const str& text) {
        JsonVal val = _JsonParser(text).parse();
        if ((val).tag == PYTRA_TID_DICT)
            return JsonObj(cast(dict, val));
        return ::std::nullopt;
    }
    
    ::std::optional<JsonArr> loads_arr(const str& text) {
        JsonVal val = _JsonParser(text).parse();
        if ((val).tag == PYTRA_TID_LIST)
            return JsonArr(py_to<rc<list<JsonVal>>>(cast(list, val)));
        return ::std::nullopt;
    }
    
    str _join_strs(const rc<list<str>>& parts, const str& sep) {
        if ((rc_list_ref(parts)).empty())
            return "";
        str out = py_list_at_ref(rc_list_ref(parts), 0);
        int64 i = 1;
        while (i < (rc_list_ref(parts)).size()) {
            out = out + sep + py_list_at_ref(rc_list_ref(parts), i);
            i++;
        }
        return out;
    }
    
    str _escape_str(const str& s, bool ensure_ascii) {
        rc<list<str>> out = rc_list_from_value(list<str>{"\""});
        for (str ch : s) {
            int64 code = int64(py_ord(ch));
            if (ch == "\"") {
                rc_list_ref(out).append("\\\"");
            } else if (ch == "\\") {
                rc_list_ref(out).append("\\\\");
            } else if (ch == "\b") {
                rc_list_ref(out).append("\\b");
            } else if (ch == "\f") {
                rc_list_ref(out).append("\\f");
            } else if (ch == "\n") {
                rc_list_ref(out).append("\\n");
            } else if (ch == "\r") {
                rc_list_ref(out).append("\\r");
            } else if (ch == "\t") {
                rc_list_ref(out).append("\\t");
            } else if ((ensure_ascii) && (code > 0x7F)) {
                rc_list_ref(out).append("\\u" + _hex4(code));
            } else {
                rc_list_ref(out).append(ch);
            }
        }
        rc_list_ref(out).append("\"");
        return _join_strs(out, _EMPTY);
    }
    
    str _dump_json_list(const rc<list<JsonVal>>& values, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level) {
        if ((rc_list_ref(values)).empty())
            return "[]";
        if (!indent.has_value()) {
            rc<list<str>> dumped = rc_list_from_value(list<str>{});
            for (JsonVal x : rc_list_ref(values)) {
                str dumped_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level);
                rc_list_ref(dumped).append(dumped_txt);
            }
            return "[" + _join_strs(dumped, item_sep) + "]";
        }
        int64 indent_i = _json_indent_value(indent);
        rc<list<str>> inner = rc_list_from_value(list<str>{});
        for (JsonVal x : rc_list_ref(values)) {
            str prefix = py_repeat(" ", indent_i * (level + 1));
            str value_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1);
            rc_list_ref(inner).append(prefix + value_txt);
        }
        return "[\n" + _join_strs(inner, _COMMA_NL) + "\n" + py_repeat(" ", indent_i * level) + "]";
    }
    
    str _dump_json_dict(const dict<str, JsonVal>& values, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level) {
        if (py_len(values) == 0)
            return "{}";
        if (!indent.has_value()) {
            rc<list<str>> parts = rc_list_from_value(list<str>{});
            for (::std::tuple<str, JsonVal> __itobj_2 : values) {
                str k = py_to_string(py_at(__itobj_2, 0));
                JsonVal x = py_at(__itobj_2, 1);
                str k_txt = _escape_str(k, ensure_ascii);
                str v_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level);
                rc_list_ref(parts).append(k_txt + key_sep + v_txt);
            }
            return "{" + _join_strs(parts, item_sep) + "}";
        }
        int64 indent_i = _json_indent_value(indent);
        rc<list<str>> inner = rc_list_from_value(list<str>{});
        for (::std::tuple<str, JsonVal> __itobj_3 : values) {
            str k = py_to_string(py_at(__itobj_3, 0));
            JsonVal x = py_at(__itobj_3, 1);
            str prefix = py_repeat(" ", indent_i * (level + 1));
            str k_txt = _escape_str(k, ensure_ascii);
            str v_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1);
            rc_list_ref(inner).append(prefix + k_txt + key_sep + v_txt);
        }
        return "{\n" + _join_strs(inner, _COMMA_NL) + "\n" + py_repeat(" ", indent_i * level) + "}";
    }
    
    str _dump_json_value(const JsonVal& v, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level) {
        if (v.tag == PYTRA_TID_NONE)
            return "null";
        if ((v).tag == PYTRA_TID_BOOL) {
            bool raw_b = py_to<bool>(v.bool_val);
            if (raw_b)
                return "true";
            return "false";
        }
        if ((v).tag == PYTRA_TID_INT)
            return py_to_string(v.int64_val);
        if ((v).tag == PYTRA_TID_FLOAT)
            return py_to_string(v.float64_val);
        if ((v).tag == PYTRA_TID_STR)
            return _escape_str(v.str_val, ensure_ascii);
        if ((v).tag == PYTRA_TID_LIST)
            return _dump_json_list(py_to<rc<list<JsonVal>>>(cast(list, v)), ensure_ascii, indent, item_sep, key_sep, level);
        if ((v).tag == PYTRA_TID_DICT)
            return _dump_json_dict(cast(dict, v), ensure_ascii, indent, item_sep, key_sep, level);
        throw TypeError("json.dumps unsupported type");
    }
    
    str dumps(const JsonVal& obj, bool ensure_ascii, const ::std::optional<int64>& indent, const ::std::optional<::std::tuple<str, str>>& separators) {
        str item_sep = ",";
        str key_sep = (!indent.has_value() ? ":" : ": ");
        if (separators.has_value()) {
            auto __tuple_4 = *(separators);
            item_sep = ::std::get<0>(__tuple_4);
            key_sep = ::std::get<1>(__tuple_4);
        }
        return _dump_json_value(obj, ensure_ascii, indent, item_sep, key_sep, 0);
    }
    
    str dumps_jv(const JsonVal& jv, bool ensure_ascii, const ::std::optional<int64>& indent, const ::std::optional<::std::tuple<str, str>>& separators) {
        str item_sep = ",";
        str key_sep = (!indent.has_value() ? ":" : ": ");
        if (separators.has_value()) {
            auto __tuple_5 = *(separators);
            item_sep = ::std::get<0>(__tuple_5);
            key_sep = ::std::get<1>(__tuple_5);
        }
        return _dump_json_value(jv, ensure_ascii, indent, item_sep, key_sep, 0);
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
