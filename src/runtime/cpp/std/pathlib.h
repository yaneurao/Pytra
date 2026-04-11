#ifndef PYTRA_RUNTIME_STD_PATHLIB_H
#define PYTRA_RUNTIME_STD_PATHLIB_H

#include "core/py_runtime.h"

class Path {
public:
    str _value;

    Path() = default;
    Path(const str& value);
    Path(const char* value);
    Path(const Path& value) = default;
    explicit Path(const object& value);

    str __str__() const;
    str __repr__() const;
    str __fspath__() const;
    Path __truediv__(const object& rhs) const;
    Path parent() const;
    list<Path> parents() const;
    str name() const;
    str suffix() const;
    str stem() const;
    Path with_suffix(const str& suffix) const;
    Path relative_to(const object& other) const;
    Path resolve() const;
    bool exists() const;
    void mkdir(bool parents = false, bool exist_ok = false) const;
    str read_text(const str& encoding = str("utf-8")) const;
    int64 write_text(const str& text, const str& encoding = str("utf-8")) const;
    Path joinpath(const str& part) const;
    Path joinpath(const Path& part) const;
    Path joinpath(const str& part0, const str& part1) const;
    list<Path> glob(const str& pattern) const;
    static Path cwd();
};

inline int64 py_pathlib_write_text(const Path& path, const str& text) {
    return path.write_text(text);
}

inline int64 py_pathlib_write_text(const Path& path, const str& text, const str& encoding) {
    return path.write_text(text, encoding);
}

#endif  // PYTRA_RUNTIME_STD_PATHLIB_H
