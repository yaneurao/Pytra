// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: tools/gen_runtime_from_manifest.py

#ifndef PYTRA_GEN_STD_JSON_H
#define PYTRA_GEN_STD_JSON_H

// forward declarations
bool _is_ws(const str& ch);
bool _is_digit(const str& ch);
int64 _hex_value(const str& ch);
int64 _int_from_hex4(const str& hx);
str _hex4(int64 code);
int64 _json_indent_value(const ::std::optional<int64>& indent);
JsonVal _jv_obj_require(const dict<str, JsonVal>& raw, const str& key);
JsonValue loads(const str& text);
str _join_strs(const list<str>& parts, const str& sep);
str _escape_str(const str& s, bool ensure_ascii);
str _dump_json_list(const list<JsonVal>& values, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level);
str _dump_json_dict(const dict<str, JsonVal>& values, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level);
str _dump_json_value(const JsonVal& v, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level);
str dumps(const JsonVal& obj, bool ensure_ascii = true, const ::std::optional<int64>& indent = ::std::nullopt, const ::std::optional<::std::tuple<str, str>>& separators = ::std::nullopt);
str dumps_jv(const JsonVal& jv, bool ensure_ascii = true, const ::std::optional<int64>& indent = ::std::nullopt, const ::std::optional<::std::tuple<str, str>>& separators = ::std::nullopt);

str _EMPTY;
str _COMMA_NL;
str _HEX_DIGITS;

/* Pure Python JSON utilities for selfhost-friendly transpilation. */

struct JsonVal {
    pytra_type_id tag;
    bool bool_val;
    int64 int64_val;
    float64 float64_val;
    str str_val;
    rc<list<JsonVal>> list_jsonval_val;
    rc<dict<str, JsonVal>> dict_str_jsonval_val;

    JsonVal() : tag(PYTRA_TID_NONE) {}
    JsonVal(const bool& v) : tag(PYTRA_TID_BOOL), bool_val(v) {}
    JsonVal(const int64& v) : tag(PYTRA_TID_INT), int64_val(v) {}
    JsonVal(const float64& v) : tag(PYTRA_TID_FLOAT), float64_val(v) {}
    JsonVal(const str& v) : tag(PYTRA_TID_STR), str_val(v) {}
    JsonVal(const rc<list<JsonVal>>& v) : tag(PYTRA_TID_LIST), list_jsonval_val(v) {}
    JsonVal(const rc<dict<str, JsonVal>>& v) : tag(PYTRA_TID_DICT), dict_str_jsonval_val(v) {}
    JsonVal(::std::monostate) : tag(PYTRA_TID_NONE) {}
};


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

struct JsonObj {
    dict<str, JsonVal> raw;
    
    JsonObj(const dict<str, JsonVal>& raw) {
        this->raw = raw;
    }
    ::std::optional<JsonValue> get(const str& key) const {
        if (!py_contains(this->raw, key))
            return ::std::nullopt;
        return JsonValue(_jv_obj_require(this->raw, key));
    }
    ::std::optional<JsonObj> get_obj(const str& key) const {
        if (!py_contains(this->raw, key))
            return ::std::nullopt;
        return JsonValue(_jv_obj_require(this->raw, key)).as_obj();
    }
    ::std::optional<JsonArr> get_arr(const str& key) const {
        if (!py_contains(this->raw, key))
            return ::std::nullopt;
        return JsonValue(_jv_obj_require(this->raw, key)).as_arr();
    }
    ::std::optional<str> get_str(const str& key) const {
        if (!py_contains(this->raw, key))
            return ::std::nullopt;
        return JsonValue(_jv_obj_require(this->raw, key)).as_str();
    }
    ::std::optional<int64> get_int(const str& key) const {
        if (!py_contains(this->raw, key))
            return ::std::nullopt;
        return JsonValue(_jv_obj_require(this->raw, key)).as_int();
    }
    ::std::optional<float64> get_float(const str& key) const {
        if (!py_contains(this->raw, key))
            return ::std::nullopt;
        return JsonValue(_jv_obj_require(this->raw, key)).as_float();
    }
    ::std::optional<bool> get_bool(const str& key) const {
        if (!py_contains(this->raw, key))
            return ::std::nullopt;
        return JsonValue(_jv_obj_require(this->raw, key)).as_bool();
    }
};

struct JsonArr {
    list<JsonVal> raw;
    
    JsonArr(const list<JsonVal>& raw) {
        this->raw = raw;
    }
    ::std::optional<JsonValue> get(int64 index) const {
        if ((index < 0) || (index >= (this->raw).size()))
            return ::std::nullopt;
        return JsonValue(this->raw[index]);
    }
    ::std::optional<JsonObj> get_obj(int64 index) const {
        if ((index < 0) || (index >= (this->raw).size()))
            return ::std::nullopt;
        return JsonValue(this->raw[index]).as_obj();
    }
    ::std::optional<JsonArr> get_arr(int64 index) const {
        if ((index < 0) || (index >= (this->raw).size()))
            return ::std::nullopt;
        return JsonValue(this->raw[index]).as_arr();
    }
    ::std::optional<str> get_str(int64 index) const {
        if ((index < 0) || (index >= (this->raw).size()))
            return ::std::nullopt;
        return JsonValue(this->raw[index]).as_str();
    }
    ::std::optional<int64> get_int(int64 index) const {
        if ((index < 0) || (index >= (this->raw).size()))
            return ::std::nullopt;
        return JsonValue(this->raw[index]).as_int();
    }
    ::std::optional<float64> get_float(int64 index) const {
        if ((index < 0) || (index >= (this->raw).size()))
            return ::std::nullopt;
        return JsonValue(this->raw[index]).as_float();
    }
    ::std::optional<bool> get_bool(int64 index) const {
        if ((index < 0) || (index >= (this->raw).size()))
            return ::std::nullopt;
        return JsonValue(this->raw[index]).as_bool();
    }
};

struct JsonValue {
    JsonVal raw;
    
    JsonValue(const JsonVal& raw) {
        this->raw = raw;
    }
    ::std::optional<JsonObj> as_obj() const {
        JsonVal jv = this->raw;
        if ((jv).tag == PYTRA_TID_DICT)
            return JsonObj(cast(dict, jv));
        return ::std::nullopt;
    }
    ::std::optional<JsonArr> as_arr() const {
        JsonVal jv = this->raw;
        if ((jv).tag == PYTRA_TID_LIST)
            return JsonArr(cast(list, jv));
        return ::std::nullopt;
    }
    ::std::optional<str> as_str() const {
        JsonVal jv = this->raw;
        if ((jv).tag == PYTRA_TID_STR)
            return jv.str_val;
        return ::std::nullopt;
    }
    ::std::optional<int64> as_int() const {
        JsonVal jv = this->raw;
        if ((jv).tag == PYTRA_TID_INT)
            return jv.int64_val;
        return ::std::nullopt;
    }
    ::std::optional<float64> as_float() const {
        JsonVal jv = this->raw;
        if ((jv).tag == PYTRA_TID_FLOAT)
            return jv.float64_val;
        return ::std::nullopt;
    }
    ::std::optional<bool> as_bool() const {
        JsonVal jv = this->raw;
        if ((jv).tag == PYTRA_TID_BOOL)
            return jv.bool_val;
        return ::std::nullopt;
    }
};

struct _JsonParser {
    str text;
    int64 n;
    int64 i;
    
    _JsonParser(const str& text) {
        this->text = text;
        this->n = text.size();
        this->i = 0;
    }
    JsonVal parse() {
        this->_skip_ws();
        JsonVal out = this->_parse_value();
        this->_skip_ws();
        if (this->i != this->n)
            throw ValueError("invalid json: trailing characters");
        return out;
    }
    void _skip_ws() {
        while ((this->i < this->n) && (_is_ws(this->text[this->i]))) {
            this->i++;
        }
    }
    JsonVal _parse_value() {
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
    dict<str, JsonVal> _parse_object() {
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
    list<JsonVal> _parse_array() {
        list<JsonVal> out = {};
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
    str _parse_string() {
        if (this->text[this->i] != "\"")
            throw ValueError("invalid json string");
        this->i++;
        list<str> out_chars = {};
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
                    out_chars.append("\"");
                } else if (esc == "\\") {
                    out_chars.append("\\");
                } else if (esc == "/") {
                    out_chars.append("/");
                } else if (esc == "b") {
                    out_chars.append("\b");
                } else if (esc == "f") {
                    out_chars.append("\f");
                } else if (esc == "n") {
                    out_chars.append("\n");
                } else if (esc == "r") {
                    out_chars.append("\r");
                } else if (esc == "t") {
                    out_chars.append("\t");
                } else if (esc == "u") {
                    if (this->i + 4 > this->n)
                        throw ValueError("invalid json unicode escape");
                    str hx = py_str_slice(this->text, this->i, this->i + 4);
                    this->i += 4;
                    out_chars.append(str(py_chr(_int_from_hex4(hx))));
                } else {
                    throw ValueError("invalid json escape");
                }
            } else {
                out_chars.append(ch);
            }
        }
        throw ValueError("unterminated json string");
    }
    JsonVal _parse_number() {
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
};

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
        return JsonArr(cast(list, val));
    return ::std::nullopt;
}

str _join_strs(const list<str>& parts, const str& sep) {
    if (parts.empty())
        return "";
    str out = parts[0];
    int64 i = 1;
    while (i < parts.size()) {
        out = out + sep + parts[i];
        i++;
    }
    return out;
}

str _escape_str(const str& s, bool ensure_ascii) {
    list<str> out = list<str>{"\""};
    for (str ch : s) {
        int64 code = int64(py_ord(ch));
        if (ch == "\"") {
            out.append("\\\"");
        } else if (ch == "\\") {
            out.append("\\\\");
        } else if (ch == "\b") {
            out.append("\\b");
        } else if (ch == "\f") {
            out.append("\\f");
        } else if (ch == "\n") {
            out.append("\\n");
        } else if (ch == "\r") {
            out.append("\\r");
        } else if (ch == "\t") {
            out.append("\\t");
        } else if ((ensure_ascii) && (code > 0x7F)) {
            out.append("\\u" + _hex4(code));
        } else {
            out.append(ch);
        }
    }
    out.append("\"");
    return _join_strs(out, _EMPTY);
}

str _dump_json_list(const list<JsonVal>& values, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level) {
    if (values.empty())
        return "[]";
    if (!indent.has_value()) {
        list<str> dumped = {};
        for (JsonVal x : values) {
            str dumped_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level);
            dumped.append(dumped_txt);
        }
        return "[" + _join_strs(dumped, item_sep) + "]";
    }
    int64 indent_i = _json_indent_value(indent);
    list<str> inner = {};
    for (JsonVal x : values) {
        str prefix = py_repeat(" ", indent_i * (level + 1));
        str value_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1);
        inner.append(prefix + value_txt);
    }
    return "[\n" + _join_strs(inner, _COMMA_NL) + "\n" + py_repeat(" ", indent_i * level) + "]";
}

str _dump_json_dict(const dict<str, JsonVal>& values, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level) {
    if (py_len(values) == 0)
        return "{}";
    if (!indent.has_value()) {
        list<str> parts = {};
        for (::std::tuple<str, JsonVal> __itobj_2 : values) {
            str k = py_to_string(py_at(__itobj_2, 0));
            JsonVal x = py_at(__itobj_2, 1);
            str k_txt = _escape_str(k, ensure_ascii);
            str v_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level);
            parts.append(k_txt + key_sep + v_txt);
        }
        return "{" + _join_strs(parts, item_sep) + "}";
    }
    int64 indent_i = _json_indent_value(indent);
    list<str> inner = {};
    for (::std::tuple<str, JsonVal> __itobj_3 : values) {
        str k = py_to_string(py_at(__itobj_3, 0));
        JsonVal x = py_at(__itobj_3, 1);
        str prefix = py_repeat(" ", indent_i * (level + 1));
        str k_txt = _escape_str(k, ensure_ascii);
        str v_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1);
        inner.append(prefix + k_txt + key_sep + v_txt);
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
        return _dump_json_list(cast(list, v), ensure_ascii, indent, item_sep, key_sep, level);
    if ((v).tag == PYTRA_TID_DICT)
        return _dump_json_dict(cast(dict, v), ensure_ascii, indent, item_sep, key_sep, level);
    throw TypeError("json.dumps unsupported type");
}

str dumps(const JsonVal& obj, bool ensure_ascii = true, const ::std::optional<int64>& indent = ::std::nullopt, const ::std::optional<::std::tuple<str, str>>& separators = ::std::nullopt) {
    str item_sep = ",";
    str key_sep = (!indent.has_value() ? ":" : ": ");
    if (separators.has_value()) {
        auto __tuple_4 = *(separators);
        item_sep = ::std::get<0>(__tuple_4);
        key_sep = ::std::get<1>(__tuple_4);
    }
    return _dump_json_value(obj, ensure_ascii, indent, item_sep, key_sep, 0);
}

str dumps_jv(const JsonVal& jv, bool ensure_ascii = true, const ::std::optional<int64>& indent = ::std::nullopt, const ::std::optional<::std::tuple<str, str>>& separators = ::std::nullopt) {
    str item_sep = ",";
    str key_sep = (!indent.has_value() ? ":" : ": ");
    if (separators.has_value()) {
        auto __tuple_5 = *(separators);
        item_sep = ::std::get<0>(__tuple_5);
        key_sep = ::std::get<1>(__tuple_5);
    }
    return _dump_json_value(jv, ensure_ascii, indent, item_sep, key_sep, 0);
}

#endif  // PYTRA_GEN_STD_JSON_H
