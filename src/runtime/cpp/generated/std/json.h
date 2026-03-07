// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_STD_JSON_H
#define PYTRA_GENERATED_STD_JSON_H

#include "runtime/cpp/core/py_types.h"

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
        dict<str, object> _parse_object();
        object _parse_array();
        str _parse_string();
        object _parse_number();
    };

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
str dumps(const object& obj, bool ensure_ascii = true, const ::std::optional<int64>& indent = ::std::nullopt, const ::std::optional<::std::tuple<str, str>>& separators = ::std::nullopt);

}  // namespace pytra::std::json

#endif  // PYTRA_GENERATED_STD_JSON_H
