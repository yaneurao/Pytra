// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/string_ops.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_BUILT_IN_STRING_OPS_H
#define PYTRA_GENERATED_BUILT_IN_STRING_OPS_H

#include "runtime/cpp/native/core/py_types.h"

bool _is_space(const str& ch);
bool _contains_char(const str& chars, const str& ch);
int64 _normalize_index(int64 idx, int64 n);
str py_join(const str& sep, const list<str>& parts);
list<str> py_split(const str& s, const str& sep, int64 maxsplit);
list<str> py_splitlines(const str& s);
int64 py_count(const str& s, const str& needle);
str py_lstrip(const str& s);
str py_lstrip_chars(const str& s, const str& chars);
str py_rstrip(const str& s);
str py_rstrip_chars(const str& s, const str& chars);
str py_strip(const str& s);
str py_strip_chars(const str& s, const str& chars);
bool py_startswith(const str& s, const str& prefix);
bool py_endswith(const str& s, const str& suffix);
int64 py_find(const str& s, const str& needle);
int64 py_find_window(const str& s, const str& needle, int64 start, int64 end);
int64 py_rfind(const str& s, const str& needle);
int64 py_rfind_window(const str& s, const str& needle, int64 start, int64 end);
str py_replace(const str& s, const str& oldv, const str& newv);

#endif  // PYTRA_GENERATED_BUILT_IN_STRING_OPS_H
