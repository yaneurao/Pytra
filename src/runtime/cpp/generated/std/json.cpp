// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/py_runtime.h"

#include "runtime/cpp/generated/std/json.h"

#include "pytra/built_in/string_ops.h"

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
            list<object> out = list<object>{};
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
            list<str> out_chars = {};
            while (this->i < this->n) {
                str ch = this->text[this->i];
                this->i++;
                if (ch == "\"")
                    return _EMPTY.join(out_chars);
                if (ch == "\\") {
                    if (this->i >= this->n)
                        throw ValueError("invalid json string escape");
                    str esc = this->text[this->i];
                    this->i++;
                    if (esc == "\"") {
                        out_chars.append(str("\""));
                    } else if (esc == "\\") {
                        out_chars.append(str("\\"));
                    } else if (esc == "/") {
                        out_chars.append(str("/"));
                    } else if (esc == "b") {
                        out_chars.append(str("\b"));
                    } else if (esc == "f") {
                        out_chars.append(str("\f"));
                    } else if (esc == "n") {
                        out_chars.append(str("\n"));
                    } else if (esc == "r") {
                        out_chars.append(str("\r"));
                    } else if (esc == "t") {
                        out_chars.append(str("\t"));
                    } else if (esc == "u") {
                        if (this->i + 4 > this->n)
                            throw ValueError("invalid json unicode escape");
                        str hx = py_slice(this->text, this->i, this->i + 4);
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
    
    str _escape_str(const str& s, bool ensure_ascii) {
        list<str> out = list<str>{"\""};
        for (str ch : s) {
            int64 code = py_to<int64>(py_ord(ch));
            if (ch == "\"") {
                out.append(str("\\\""));
            } else if (ch == "\\") {
                out.append(str("\\\\"));
            } else if (ch == "\b") {
                out.append(str("\\b"));
            } else if (ch == "\f") {
                out.append(str("\\f"));
            } else if (ch == "\n") {
                out.append(str("\\n"));
            } else if (ch == "\r") {
                out.append(str("\\r"));
            } else if (ch == "\t") {
                out.append(str("\\t"));
            } else if ((ensure_ascii) && (code > 0x7F)) {
                out.append(str("\\u" + _hex4(code)));
            } else {
                out.append(ch);
            }
        }
        out.append(str("\""));
        return _EMPTY.join(out);
    }
    
    str _dump_json_list(const object& values, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level) {
        if (py_len(values) == 0)
            return "[]";
        if (py_is_none(indent)) {
            list<str> dumped = {};
            for (object x : py_dyn_range(values)) {
                str dumped_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level);
                dumped.append(dumped_txt);
            }
            return "[" + str(item_sep).join(dumped) + "]";
        }
        int64 indent_i = py_to_int64(indent);
        list<str> inner = {};
        for (object x : py_dyn_range(values)) {
            str prefix = py_repeat(" ", indent_i * (level + 1));
            str value_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1);
            inner.append(str(prefix + value_txt));
        }
        return "[\n" + _COMMA_NL.join(inner) + "\n" + py_repeat(" ", indent_i * level) + "]";
    }
    
    str _dump_json_dict(const dict<str, object>& values, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level) {
        if (py_len(values) == 0)
            return "{}";
        if (py_is_none(indent)) {
            list<str> parts = {};
            for (::std::tuple<str, object> __itobj_1 : values) {
                str k = py_to_string(py_at(__itobj_1, 0));
                auto x = py_at(__itobj_1, 1);
                str k_txt = _escape_str(k, ensure_ascii);
                str v_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level);
                parts.append(str(k_txt + key_sep + v_txt));
            }
            return "{" + str(item_sep).join(parts) + "}";
        }
        int64 indent_i = py_to_int64(indent);
        list<str> inner = {};
        for (::std::tuple<str, object> __itobj_2 : values) {
            str k = py_to_string(py_at(__itobj_2, 0));
            auto x = py_at(__itobj_2, 1);
            str prefix = py_repeat(" ", indent_i * (level + 1));
            str k_txt = _escape_str(k, ensure_ascii);
            str v_txt = _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1);
            inner.append(str(prefix + k_txt + key_sep + v_txt));
        }
        return "{\n" + _COMMA_NL.join(inner) + "\n" + py_repeat(" ", indent_i * level) + "}";
    }
    
    str _dump_json_value(const object& v, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level) {
        if (py_is_none(v))
            return "null";
        if (py_isinstance(v, PYTRA_TID_BOOL))
            return (v ? "true" : "false");
        if (py_isinstance(v, PYTRA_TID_INT))
            return py_to_string(v);
        if (py_isinstance(v, PYTRA_TID_FLOAT))
            return py_to_string(v);
        if (py_isinstance(v, PYTRA_TID_STR))
            return _escape_str(py_to_string(v), ensure_ascii);
        if (py_isinstance(v, PYTRA_TID_LIST)) {
            object as_list = make_object(list<object>(v));
            return _dump_json_list(as_list, ensure_ascii, indent, item_sep, key_sep, level);
        }
        if (py_isinstance(v, PYTRA_TID_DICT)) {
            dict<str, object> as_dict = dict<str, object>(v);
            return _dump_json_dict(as_dict, ensure_ascii, indent, item_sep, key_sep, level);
        }
        throw TypeError("json.dumps unsupported type");
    }
    
    str dumps(const object& obj, bool ensure_ascii, const ::std::optional<int64>& indent, const ::std::optional<::std::tuple<str, str>>& separators) {
        str item_sep = ",";
        str key_sep = (py_is_none(indent) ? ":" : ": ");
        if (!py_is_none(separators)) {
            auto __tuple_3 = *(separators);
            item_sep = ::std::get<0>(__tuple_3);
            key_sep = ::std::get<1>(__tuple_3);
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
