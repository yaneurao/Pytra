#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/json.h"

#include "pytra/std/typing.h"

namespace pytra::std::json {

    /* Pure Python JSON utilities for selfhost-friendly transpilation. */
    
    
    
    str _EMPTY = "";
    
    str _COMMA_NL = ",\n";
    
    str _HEX_DIGITS = "0123456789abcdef";
    
    bool _is_ws(const str& ch) {
        return (ch == " ") || (ch == "\t") || (ch == "\r") || (ch == "\n");
    }
    
    bool _is_digit(const str& ch) {
        return (ch >= "0") && (ch <= "9");
    }
    
    int64 _hex_value(const str& ch) {
        if ((ch >= "0") && (ch <= "9"))
            return py_to_int64(ch);
        ::std::any low = make_object(ch.lower());
        if (low == "a")
            return 10;
        if (low == "b")
            return 11;
        if (low == "c")
            return 12;
        if (low == "d")
            return 13;
        if (low == "e")
            return 14;
        if (low == "f")
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
        ::std::any p0 = make_object(py_slice(_HEX_DIGITS, d0, d0 + 1));
        ::std::any p1 = make_object(py_slice(_HEX_DIGITS, d1, d1 + 1));
        ::std::any p2 = make_object(py_slice(_HEX_DIGITS, d2, d2 + 1));
        ::std::any p3 = make_object(py_slice(_HEX_DIGITS, d3, d3 + 1));
        return py_to_string(p0 + p1 + p2 + p3);
    }
    
    struct _JsonParser {
        inline static str text;
        inline static int64 n;
        inline static int64 i;
        
        _JsonParser(const str& text) {
            _JsonParser::text = text;
            _JsonParser::n = py_len(text);
            _JsonParser::i = 0;
        }
        void parse() {
            this->_skip_ws();
            void out = this->_parse_value();
            this->_skip_ws();
            if (_JsonParser::i != _JsonParser::n)
                throw ValueError("invalid json: trailing characters");
            return out;
        }
        void _skip_ws() {
            while ((_JsonParser::i < _JsonParser::n) && (_is_ws(_JsonParser::text[_JsonParser::i]))) {
                _JsonParser::i++;
            }
        }
        void _parse_value() {
            if (_JsonParser::i >= _JsonParser::n)
                throw ValueError("invalid json: unexpected end");
            str ch = _JsonParser::text[_JsonParser::i];
            if (ch == "{")
                return this->_parse_object();
            if (ch == "[")
                return this->_parse_array();
            if (ch == "\"")
                return this->_parse_string();
            if ((ch == "t") && (py_slice(_JsonParser::text, _JsonParser::i, _JsonParser::i + 4) == "true")) {
                _JsonParser::i += 4;
                return true;
            }
            if ((ch == "f") && (py_slice(_JsonParser::text, _JsonParser::i, _JsonParser::i + 5) == "false")) {
                _JsonParser::i += 5;
                return false;
            }
            if ((ch == "n") && (py_slice(_JsonParser::text, _JsonParser::i, _JsonParser::i + 4) == "null")) {
                _JsonParser::i += 4;
                return ::std::nullopt;
            }
            return this->_parse_number();
        }
        dict<str, object> _parse_object() {
            dict<str, object> out = dict<str, object>{};
            _JsonParser::i++;
            this->_skip_ws();
            if ((_JsonParser::i < _JsonParser::n) && (_JsonParser::text.at(_JsonParser::i) == '}')) {
                _JsonParser::i++;
                return out;
            }
            while (true) {
                this->_skip_ws();
                if ((_JsonParser::i >= _JsonParser::n) || (_JsonParser::text.at(_JsonParser::i) != '"'))
                    throw ValueError("invalid json object key");
                str key = this->_parse_string();
                this->_skip_ws();
                if ((_JsonParser::i >= _JsonParser::n) || (_JsonParser::text.at(_JsonParser::i) != ':'))
                    throw ValueError("invalid json object: missing ':'");
                _JsonParser::i++;
                this->_skip_ws();
                out[key] = make_object(this->_parse_value());
                this->_skip_ws();
                if (_JsonParser::i >= _JsonParser::n)
                    throw ValueError("invalid json object: unexpected end");
                str ch = _JsonParser::text[_JsonParser::i];
                _JsonParser::i++;
                if (ch == "}")
                    return out;
                if (ch != ",")
                    throw ValueError("invalid json object separator");
            }
        }
        list<object> _parse_array() {
            list<object> out = list<object>{};
            _JsonParser::i++;
            this->_skip_ws();
            if ((_JsonParser::i < _JsonParser::n) && (_JsonParser::text.at(_JsonParser::i) == ']')) {
                _JsonParser::i++;
                return out;
            }
            while (true) {
                this->_skip_ws();
                out.append(this->_parse_value());
                this->_skip_ws();
                if (_JsonParser::i >= _JsonParser::n)
                    throw ValueError("invalid json array: unexpected end");
                str ch = _JsonParser::text[_JsonParser::i];
                _JsonParser::i++;
                if (ch == "]")
                    return out;
                if (ch != ",")
                    throw ValueError("invalid json array separator");
            }
        }
        str _parse_string() {
            if (_JsonParser::text.at(_JsonParser::i) != '"')
                throw ValueError("invalid json string");
            _JsonParser::i++;
            list<str> out_chars = list<str>{};
            while (_JsonParser::i < _JsonParser::n) {
                str ch = _JsonParser::text[_JsonParser::i];
                _JsonParser::i++;
                if (ch == "\"")
                    return py_to_string(_EMPTY.join(out_chars));
                if (ch == "\\") {
                    if (_JsonParser::i >= _JsonParser::n)
                        throw ValueError("invalid json string escape");
                    str esc = _JsonParser::text[_JsonParser::i];
                    _JsonParser::i++;
                    if (esc == "\"") {
                        out_chars.append(str("\""));
                    } else {
                        if (esc == "\\") {
                            out_chars.append(str("\\"));
                        } else {
                            if (esc == "/") {
                                out_chars.append(str("/"));
                            } else {
                                if (esc == "b") {
                                    out_chars.append(str(""));
                                } else {
                                    if (esc == "f") {
                                        out_chars.append(str(""));
                                    } else {
                                        if (esc == "n") {
                                            out_chars.append(str("\n"));
                                        } else {
                                            if (esc == "r") {
                                                out_chars.append(str("\r"));
                                            } else {
                                                if (esc == "t") {
                                                    out_chars.append(str("\t"));
                                                } else {
                                                    if (esc == "u") {
                                                        if (_JsonParser::i + 4 > _JsonParser::n)
                                                            throw ValueError("invalid json unicode escape");
                                                        str hx = py_slice(_JsonParser::text, _JsonParser::i, _JsonParser::i + 4);
                                                        _JsonParser::i += 4;
                                                        out_chars.append(str(py_chr(_int_from_hex4(hx))));
                                                    } else {
                                                        throw ValueError("invalid json escape");
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
                    out_chars.append(str(ch));
                }
            }
            throw ValueError("unterminated json string");
        }
        void _parse_number() {
            int64 start = _JsonParser::i;
            if (_JsonParser::text.at(_JsonParser::i) == '-')
                _JsonParser::i++;
            if (_JsonParser::i >= _JsonParser::n)
                throw ValueError("invalid json number");
            if (_JsonParser::text.at(_JsonParser::i) == '0') {
                _JsonParser::i++;
            } else {
                if (!(_is_digit(_JsonParser::text[_JsonParser::i])))
                    throw ValueError("invalid json number");
                while ((_JsonParser::i < _JsonParser::n) && (_is_digit(_JsonParser::text[_JsonParser::i]))) {
                    _JsonParser::i++;
                }
            }
            bool is_float = false;
            if ((_JsonParser::i < _JsonParser::n) && (_JsonParser::text.at(_JsonParser::i) == '.')) {
                is_float = true;
                _JsonParser::i++;
                if ((_JsonParser::i >= _JsonParser::n) || (!(_is_digit(_JsonParser::text[_JsonParser::i]))))
                    throw ValueError("invalid json number");
                while ((_JsonParser::i < _JsonParser::n) && (_is_digit(_JsonParser::text[_JsonParser::i]))) {
                    _JsonParser::i++;
                }
            }
            if (_JsonParser::i < _JsonParser::n) {
                str exp_ch = _JsonParser::text[_JsonParser::i];
                if ((exp_ch == "e") || (exp_ch == "E")) {
                    is_float = true;
                    _JsonParser::i++;
                    if (_JsonParser::i < _JsonParser::n) {
                        str sign = _JsonParser::text[_JsonParser::i];
                        if ((sign == "+") || (sign == "-"))
                            _JsonParser::i++;
                    }
                    if ((_JsonParser::i >= _JsonParser::n) || (!(_is_digit(_JsonParser::text[_JsonParser::i]))))
                        throw ValueError("invalid json exponent");
                    while ((_JsonParser::i < _JsonParser::n) && (_is_digit(_JsonParser::text[_JsonParser::i]))) {
                        _JsonParser::i++;
                    }
                }
            }
            str token = py_slice(_JsonParser::text, start, _JsonParser::i);
            if (is_float)
                return static_cast<float64>(token);
            return py_to_int64(token);
        }
    };
    
    void loads(const str& text) {
        return _JsonParser(text).parse();
    }
    
    str _escape_str(const str& s, bool ensure_ascii) {
        list<str> out = list<str>{"\""};
        for (str ch : s) {
            ::std::any code = make_object(py_ord(ch));
            if (ch == "\"") {
                out.append(str("\\\""));
            } else {
                if (ch == "\\") {
                    out.append(str("\\\\"));
                } else {
                    if (ch == "") {
                        out.append(str("\\b"));
                    } else {
                        if (ch == "") {
                            out.append(str("\\f"));
                        } else {
                            if (ch == "\n") {
                                out.append(str("\\n"));
                            } else {
                                if (ch == "\r") {
                                    out.append(str("\\r"));
                                } else {
                                    if (ch == "\t") {
                                        out.append(str("\\t"));
                                    } else {
                                        if ((ensure_ascii) && (code > 0x7F))
                                            out.append(str("\\u" + _hex4(int64(py_to_int64(code)))));
                                        else
                                            out.append(str(ch));
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        out.append(str("\""));
        return py_to_string(_EMPTY.join(out));
    }
    
    str _dump_json_list(const list<object>& values, bool ensure_ascii, const ::std::optional<int>& indent, const str& item_sep, const str& key_sep, int64 level) {
        if (py_len(values) == 0)
            return "[]";
        if (py_is_none(indent)) {
            list<str> dumped = list<str>{};
            for (object x : values)
                dumped.append(str(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level)));
            return py_to_string("[" + item_sep.join(dumped) + "]");
        }
        list<str> inner = list<str>{};
        for (object x : values) {
            ::std::any prefix = make_object(" " * indent * (level + 1));
            inner.append(str(prefix + _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1)));
        }
        return py_to_string("[\n" + _COMMA_NL.join(inner) + "\n" + " " * indent * level + "]");
    }
    
    str _dump_json_dict(const dict<str, object>& values, bool ensure_ascii, const ::std::optional<int>& indent, const str& item_sep, const str& key_sep, int64 level) {
        if (py_len(values) == 0)
            return "{}";
        if (py_is_none(indent)) {
            list<str> parts = list<str>{};
            for (auto __it_1 : values) {
                auto k = ::std::get<0>(__it_1);
                auto x = ::std::get<1>(__it_1);
                str k_txt = _escape_str(py_to_string(k), ensure_ascii);
                ::std::any v_txt = make_object(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level));
                parts.append(str(k_txt + key_sep + v_txt));
            }
            return py_to_string("{" + item_sep.join(parts) + "}");
        }
        list<str> inner = list<str>{};
        for (auto __it_2 : values) {
            auto k = ::std::get<0>(__it_2);
            auto x = ::std::get<1>(__it_2);
            ::std::any prefix = make_object(" " * indent * (level + 1));
            str k_txt = _escape_str(py_to_string(k), ensure_ascii);
            ::std::any v_txt = make_object(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1));
            inner.append(str(prefix + k_txt + key_sep + v_txt));
        }
        return py_to_string("{\n" + _COMMA_NL.join(inner) + "\n" + " " * indent * level + "}");
    }
    
    str _dump_json_value(const object& v, bool ensure_ascii, const ::std::optional<int>& indent, const str& item_sep, const str& key_sep, int64 level) {
        if (py_is_none(v))
            return "null";
        if (py_is_bool(v))
            return (v ? "true" : "false");
        if (py_is_int(v))
            return py_to_string(v);
        if (py_is_float(v))
            return py_to_string(v);
        if (py_is_str(v))
            return _escape_str(py_to_string(v), ensure_ascii);
        if (py_is_list(v))
            return py_to_string(_dump_json_list(list(v), ensure_ascii, indent, item_sep, key_sep, level));
        if (py_is_dict(v))
            return py_to_string(_dump_json_dict(dict(v), ensure_ascii, indent, item_sep, key_sep, level));
        throw TypeError("json.dumps unsupported type: " + py_to_string(type(v).__name__));
    }
    
    str dumps(const object& obj, bool ensure_ascii, const ::std::optional<int>& indent, const ::std::optional<::std::tuple<str, str>>& separators) {
        str item_sep = ",";
        str key_sep = (py_is_none(indent) ? ":" : ": ");
        if (!py_is_none(separators)) {
            auto __tuple_3 = *(separators);
            item_sep = ::std::get<0>(__tuple_3);
            key_sep = ::std::get<1>(__tuple_3);
        }
        return py_to_string(_dump_json_value(obj, ensure_ascii, indent, item_sep, key_sep, 0));
    }
    
}  // namespace pytra::std::json
