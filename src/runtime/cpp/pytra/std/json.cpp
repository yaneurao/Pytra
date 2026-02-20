#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/typing.h"

namespace pytra::std::json {

    /* Pure Python JSON utilities for selfhost-friendly transpilation. */
    
    
    
    struct _JsonParser : public PyObj {
        str text;
        int64 n;
        int64 i;
        
        _JsonParser(const str& text) {
            this->text = text;
            this->n = make_object(py_len(text));
            this->i = make_object(0);
        }
        object parse() {
            this->_skip_ws();
            object out = make_object(this->_parse_value());
            this->_skip_ws();
            if (this->i != this->n)
                throw ValueError("invalid json: trailing characters");
            return out;
        }
        void _skip_ws() {
            while ((this->i < this->n) && (::std::find(" \t\r\n".begin(), " \t\r\n".end(), this->text[this->i]) != " \t\r\n".end())) {
                this->i++;
            }
        }
        object _parse_value() {
            if (this->i >= this->n)
                throw ValueError("invalid json: unexpected end");
            str ch = this->text[this->i];
            if (ch == "{")
                return this->_parse_object();
            if (ch == "[")
                return this->_parse_array();
            if (ch == "\"")
                return this->_parse_string();
            if ((ch == "t") && (py_slice(this->text, this->i, this->i + 4) == "true")) {
                this->i += 4;
                return true;
            }
            if ((ch == "f") && (py_slice(this->text, this->i, this->i + 5) == "false")) {
                this->i += 5;
                return false;
            }
            if ((ch == "n") && (py_slice(this->text, this->i, this->i + 4) == "null")) {
                this->i += 4;
                return ::std::nullopt;
            }
            return this->_parse_number();
        }
        dict<str, object> _parse_object() {
            dict<str, object> out = dict<str, object>{};
            this->i++;
            this->_skip_ws();
            if ((this->i < this->n) && (this->text.at(this->i) == '}')) {
                this->i++;
                return out;
            }
            while (true) {
                this->_skip_ws();
                if ((this->i >= this->n) || (this->text.at(this->i) != '"'))
                    throw ValueError("invalid json object key");
                str key = this->_parse_string();
                this->_skip_ws();
                if ((this->i >= this->n) || (this->text.at(this->i) != ':'))
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
        list<object> _parse_array() {
            list<object> out = list<object>{};
            this->i++;
            this->_skip_ws();
            if ((this->i < this->n) && (this->text.at(this->i) == ']')) {
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
            if (this->text.at(this->i) != '"')
                throw ValueError("invalid json string");
            this->i++;
            list<str> out_chars = list<str>{};
            while (this->i < this->n) {
                str ch = this->text[this->i];
                this->i++;
                if (ch == "\"")
                    return py_to_string("".join(out_chars));
                if (ch == "\\") {
                    if (this->i >= this->n)
                        throw ValueError("invalid json string escape");
                    str esc = this->text[this->i];
                    this->i++;
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
                                                        if (this->i + 4 > this->n)
                                                            throw ValueError("invalid json unicode escape");
                                                        str hx = py_slice(this->text, this->i, this->i + 4);
                                                        this->i += 4;
                                                        try {
                                                            out_chars.append(str(chr(py_int(hx, 16))));
                                                        }
                                                        catch (const ::std::exception& exc) {
                                                            throw ValueError("invalid json unicode escape");
                                                        }
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
        ::std::any _parse_number() {
            int64 start = this->i;
            if (this->text.at(this->i) == '-')
                this->i++;
            if (this->i >= this->n)
                throw ValueError("invalid json number");
            if (this->text.at(this->i) == '0') {
                this->i++;
            } else {
                if (!(py_isdigit()))
                    throw ValueError("invalid json number");
                while ((this->i < this->n) && (py_isdigit())) {
                    this->i++;
                }
            }
            bool is_float = false;
            if ((this->i < this->n) && (this->text.at(this->i) == '.')) {
                is_float = true;
                this->i++;
                if ((this->i >= this->n) || (!(py_isdigit())))
                    throw ValueError("invalid json number");
                while ((this->i < this->n) && (py_isdigit())) {
                    this->i++;
                }
            }
            if ((this->i < this->n) && (::std::find(set<str>{"e", "E"}.begin(), set<str>{"e", "E"}.end(), this->text[this->i]) != set<str>{"e", "E"}.end())) {
                is_float = true;
                this->i++;
                if ((this->i < this->n) && (::std::find(set<str>{"+", "-"}.begin(), set<str>{"+", "-"}.end(), this->text[this->i]) != set<str>{"+", "-"}.end()))
                    this->i++;
                if ((this->i >= this->n) || (!(py_isdigit())))
                    throw ValueError("invalid json exponent");
                while ((this->i < this->n) && (py_isdigit())) {
                    this->i++;
                }
            }
            str token = py_slice(this->text, start, this->i);
            return (is_float ? static_cast<float64>(token) : py_to_int64(token));
        }
    };
    
    object loads(const str& text) {
        return ::rc_new<_JsonParser>(text)->parse();
    }
    
    str _escape_str(const str& s, bool ensure_ascii) {
        list<str> out = list<str>{"\""};
        for (str ch : s) {
            ::std::any code = make_object(ord(ch));
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
                                            out.append(str("\\u" + format(code & 0xFFFF, "04x")));
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
        return py_to_string("".join(out));
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
        for (object x : values)
            inner.append(str(" " * indent * (level + 1) + _dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1)));
        return py_to_string("[\n" + ",\n".join(inner) + "\n" + " " * indent * level + "]");
    }
    
    str _dump_json_dict(const dict<object, object>& values, bool ensure_ascii, const ::std::optional<int>& indent, const str& item_sep, const str& key_sep, int64 level) {
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
        return py_to_string("{\n" + ",\n".join(inner) + "\n" + " " * indent * level + "}");
    }
    
    str _dump_json_value(const object& v, bool ensure_ascii, const ::std::optional<int>& indent, const str& item_sep, const str& key_sep, int64 level) {
        if (py_is_none(v))
            return "null";
        if (py_is_bool(v))
            return (v ? "true" : "false");
        if (false)
            return py_to_string(v);
        if (py_is_str(v))
            return _escape_str(py_to_string(v), ensure_ascii);
        if (py_is_list(v))
            return py_to_string(_dump_json_list(v, ensure_ascii, indent, item_sep, key_sep, level));
        if (py_is_dict(v))
            return py_to_string(_dump_json_dict(v, ensure_ascii, indent, item_sep, key_sep, level));
        throw TypeError("json.dumps unsupported type: " + py_to_string(type(v).__name__));
    }
    
    str dumps(const object& obj, bool ensure_ascii, const ::std::optional<int>& indent, const ::std::optional<::std::tuple<str, str>>& separators) {
        if (py_is_none(separators)) {
            if (py_is_none(indent)) {
                str item_sep = ",";
                str key_sep = ":";
            } else {
                str item_sep = ",";
                str key_sep = ": ";
            }
        } else {
            auto __tuple_3 = separators;
            ::std::any item_sep = ::std::get<0>(__tuple_3);
            ::std::any key_sep = ::std::get<1>(__tuple_3);
        }
        
        return py_to_string(_dump_json_value(obj, ensure_ascii, indent, py_to_string(item_sep), py_to_string(key_sep), 0));
    }
    
}  // namespace pytra::std::json
