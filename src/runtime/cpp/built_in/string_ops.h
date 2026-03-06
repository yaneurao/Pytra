// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/string_ops.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_BUILT_IN_STRING_OPS_H
#define PYTRA_BUILT_IN_STRING_OPS_H

#include "runtime/cpp/core/built_in/py_types.h"

bool _is_space(const str& ch);
bool _contains_char(const str& chars, const str& ch);
int64 _normalize_index(int64 idx, int64 n);
str py_bi_lstrip(const str& s);
str py_bi_lstrip_chars(const str& s, const str& chars);
str py_bi_rstrip(const str& s);
str py_bi_rstrip_chars(const str& s, const str& chars);
str py_bi_strip(const str& s);
str py_bi_strip_chars(const str& s, const str& chars);
bool py_bi_startswith(const str& s, const str& prefix);
bool py_bi_endswith(const str& s, const str& suffix);
int64 py_bi_find(const str& s, const str& needle);
int64 py_bi_find_window(const str& s, const str& needle, int64 start, int64 end);
int64 py_bi_rfind(const str& s, const str& needle);
int64 py_bi_rfind_window(const str& s, const str& needle, int64 start, int64 end);
str py_bi_replace(const str& s, const str& oldv, const str& newv);

#endif  // PYTRA_BUILT_IN_STRING_OPS_H
