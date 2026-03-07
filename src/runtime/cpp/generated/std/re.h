// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/re.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_STD_RE_H
#define PYTRA_GENERATED_STD_RE_H

#include "runtime/cpp/core/py_types.h"

#include <optional>

namespace pytra::std::re {

    struct Match : public PyObj {
        list<str> _groups;
        str _text;
        PYTRA_DECLARE_CLASS_TYPE(PYTRA_TID_OBJECT);
        
        Match(const str& text, const rc<list<str>>& groups);
        str group(int64 idx = 0);
    };

extern int64 S;

str group(const ::std::optional<rc<Match>>& m, int64 idx = 0);
str strip_group(const ::std::optional<rc<Match>>& m, int64 idx = 0);
bool _is_ident(const str& s);
bool _is_dotted_ident(const str& s);
str _strip_suffix_colon(const str& s);
bool _is_space_ch(const str& ch);
bool _is_alnum_or_underscore(const str& ch);
int64 _skip_spaces(const str& t, int64 i);
::std::optional<rc<Match>> match(const str& pattern, const str& text, int64 flags = 0);
str sub(const str& pattern, const str& repl, const str& text, int64 flags = 0);

}  // namespace pytra::std::re

#endif  // PYTRA_GENERATED_STD_RE_H
