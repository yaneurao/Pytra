// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_STD_JSON_H
#define PYTRA_GENERATED_STD_JSON_H

#include "runtime/cpp/core/py_types.h"

#include <tuple>
#include <optional>

namespace pytra::std::json {

struct JsonObj;
struct JsonArr;
struct JsonValue;
struct _JsonParser;

    struct JsonObj {
        dict<str, object> raw;
        
        JsonObj(const dict<str, object>& raw);
        ::std::optional<JsonValue> get(const str& key);
        ::std::optional<JsonObj> get_obj(const str& key);
        ::std::optional<JsonArr> get_arr(const str& key);
        ::std::optional<str> get_str(const str& key);
        ::std::optional<int64> get_int(const str& key);
        ::std::optional<float64> get_float(const str& key);
        ::std::optional<bool> get_bool(const str& key);
    };

    struct JsonArr {
        object raw;
        
        JsonArr(const object& raw);
        ::std::optional<JsonValue> get(int64 index);
        ::std::optional<JsonObj> get_obj(int64 index);
        ::std::optional<JsonArr> get_arr(int64 index);
        ::std::optional<str> get_str(int64 index);
        ::std::optional<int64> get_int(int64 index);
        ::std::optional<float64> get_float(int64 index);
        ::std::optional<bool> get_bool(int64 index);
    };

    struct JsonValue {
        object raw;
        
        JsonValue(const object& raw);
        ::std::optional<JsonObj> as_obj();
        ::std::optional<JsonArr> as_arr();
        ::std::optional<str> as_str();
        ::std::optional<int64> as_int();
        ::std::optional<float64> as_float();
        ::std::optional<bool> as_bool();
    };

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
list<object> _json_array_items(const object& raw);
list<object> _json_new_array();
object _json_obj_require(const dict<str, object>& raw, const str& key);
int64 _json_indent_value(const ::std::optional<int64>& indent);
object loads(const str& text);
::std::optional<JsonObj> loads_obj(const str& text);
::std::optional<JsonArr> loads_arr(const str& text);
str _join_strs(const rc<list<str>>& parts, const str& sep);
str _escape_str(const str& s, bool ensure_ascii);
str _dump_json_list(const list<object>& values, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level);
str _dump_json_dict(const dict<str, object>& values, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level);
str _dump_json_value(const object& v, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level);
str dumps(const object& obj, bool ensure_ascii = true, const ::std::optional<int64>& indent = ::std::nullopt, const ::std::optional<::std::tuple<str, str>>& separators = ::std::nullopt);

}  // namespace pytra::std::json

#endif  // PYTRA_GENERATED_STD_JSON_H
