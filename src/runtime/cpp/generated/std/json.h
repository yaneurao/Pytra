// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_STD_JSON_H
#define PYTRA_GENERATED_STD_JSON_H

#include "runtime/cpp/native/core/py_runtime.h"

#include <tuple>
#include <optional>

namespace pytra::std::json {

struct JsonObj;
struct JsonArr;
struct JsonValue;
struct _JsonParser;

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


extern str _EMPTY;
extern str _COMMA_NL;
extern str _HEX_DIGITS;

    struct JsonObj {
        dict<str, JsonVal> raw;
        
        JsonObj(const dict<str, JsonVal>& raw);
        ::std::optional<JsonValue> get(const str& key) const;
        ::std::optional<JsonObj> get_obj(const str& key) const;
        ::std::optional<JsonArr> get_arr(const str& key) const;
        ::std::optional<str> get_str(const str& key) const;
        ::std::optional<int64> get_int(const str& key) const;
        ::std::optional<float64> get_float(const str& key) const;
        ::std::optional<bool> get_bool(const str& key) const;
    };

    struct JsonArr {
        rc<list<JsonVal>> raw;
        
        JsonArr(const rc<list<JsonVal>>& raw);
        ::std::optional<JsonValue> get(int64 index) const;
        ::std::optional<JsonObj> get_obj(int64 index) const;
        ::std::optional<JsonArr> get_arr(int64 index) const;
        ::std::optional<str> get_str(int64 index) const;
        ::std::optional<int64> get_int(int64 index) const;
        ::std::optional<float64> get_float(int64 index) const;
        ::std::optional<bool> get_bool(int64 index) const;
    };

    struct JsonValue {
        JsonVal raw;
        
        JsonValue(const JsonVal& raw);
        ::std::optional<JsonObj> as_obj() const;
        ::std::optional<JsonArr> as_arr() const;
        ::std::optional<str> as_str() const;
        ::std::optional<int64> as_int() const;
        ::std::optional<float64> as_float() const;
        ::std::optional<bool> as_bool() const;
    };

    struct _JsonParser {
        str text;
        int64 n;
        int64 i;
        
        _JsonParser(const str& text);
        JsonVal parse();
        void _skip_ws();
        JsonVal _parse_value();
        dict<str, JsonVal> _parse_object();
        rc<list<JsonVal>> _parse_array();
        str _parse_string();
        JsonVal _parse_number();
    };


bool _is_ws(const str& ch);
bool _is_digit(const str& ch);
int64 _hex_value(const str& ch);
int64 _int_from_hex4(const str& hx);
str _hex4(int64 code);
int64 _json_indent_value(const ::std::optional<int64>& indent);
JsonVal _jv_obj_require(const dict<str, JsonVal>& raw, const str& key);
JsonValue loads(const str& text);
::std::optional<JsonObj> loads_obj(const str& text);
::std::optional<JsonArr> loads_arr(const str& text);
str _join_strs(const rc<list<str>>& parts, const str& sep);
str _escape_str(const str& s, bool ensure_ascii);
str _dump_json_list(const rc<list<JsonVal>>& values, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level);
str _dump_json_dict(const dict<str, JsonVal>& values, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level);
str _dump_json_value(const JsonVal& v, bool ensure_ascii, const ::std::optional<int64>& indent, const str& item_sep, const str& key_sep, int64 level);
str dumps(const JsonVal& obj, bool ensure_ascii = true, const ::std::optional<int64>& indent = ::std::nullopt, const ::std::optional<::std::tuple<str, str>>& separators = ::std::nullopt);
str dumps_jv(const JsonVal& jv, bool ensure_ascii = true, const ::std::optional<int64>& indent = ::std::nullopt, const ::std::optional<::std::tuple<str, str>>& separators = ::std::nullopt);

}  // namespace pytra::std::json

#endif  // PYTRA_GENERATED_STD_JSON_H
