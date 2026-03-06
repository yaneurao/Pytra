// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_STD_JSON_H
#define PYTRA_STD_JSON_H

#include "runtime/cpp/core/built_in/py_types.ext.h"

#include <tuple>
#include <optional>

namespace pytra::std::json {

    struct _JsonParser {
        str text;
        int64 n;
        int64 i;
        
        _JsonParser(const str& text);
        object parse();
        void _skip_ws();
        object _parse_value();
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
        dict<str, object> _parse_object() {
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
        object _parse_array() {
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
        str _parse_string() {
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
                        out_chars.append(str(""));
                    } else if (esc == "f") {
                        out_chars.append(str("
"));
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
        object _parse_number() {
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

extern str _EMPTY;
extern str _COMMA_NL;
extern str _HEX_DIGITS;

bool _is_ws(const str& ch);
bool _is_digit(const str& ch);
int64 _hex_value(const str& ch);
int64 _int_from_hex4(const str& hx);
str _hex4(int64 code);
object loads(const str& text);
str _escape_str(const str& s, bool ensure_ascii);
str _dump_json_list(const list<object>& values, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level);
str _dump_json_dict(const dict<str, object>& values, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level);
str _dump_json_value(const object& v, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level);
str dumps(const object& obj, bool ensure_ascii, const ::std::optional<int64>& indent, const ::std::optional<::std::tuple<str, str>>& separators);

}  // namespace pytra::std::json

#endif  // PYTRA_STD_JSON_H
