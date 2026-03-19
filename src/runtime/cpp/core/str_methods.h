#ifndef PYTRA_CORE_STR_METHODS_H
#define PYTRA_CORE_STR_METHODS_H

#include "core/py_types.h"
#include "built_in/string_ops.h"

inline list<str> str::split(const str& sep, int64 maxsplit) const {
    return py_split(*this, sep, maxsplit);
}

inline list<str> str::split(const str& sep) const {
    return split(sep, -1);
}

inline list<str> str::splitlines() const {
    return py_splitlines(*this);
}

inline int64 str::count(const str& needle) const {
    return py_count(*this, needle);
}

inline str str::join(const list<str>& parts) const {
    return py_join(*this, parts);
}

#endif  // PYTRA_CORE_STR_METHODS_H
