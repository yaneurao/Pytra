// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/re.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_STD_RE_H
#define PYTRA_STD_RE_H

#include <optional>

namespace pytra::std::re {

struct Match;

extern int64 S;

str group(const ::std::optional<rc<Match>>& m, int64 idx);
str strip_group(const ::std::optional<rc<Match>>& m, int64 idx);
bool _is_ident(const str& s);
bool _is_dotted_ident(const str& s);
str _strip_suffix_colon(const str& s);
bool _is_space_ch(const str& ch);
bool _is_alnum_or_underscore(const str& ch);
int64 _skip_spaces(const str& t, int64 i);
::std::optional<rc<Match>> match(const str& pattern, const str& text, int64 flags);
str sub(const str& pattern, const str& repl, const str& text, int64 flags);

}  // namespace pytra::std::re

#endif  // PYTRA_STD_RE_H
