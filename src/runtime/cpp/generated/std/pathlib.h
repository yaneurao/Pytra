// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_STD_PATHLIB_H
#define PYTRA_GENERATED_STD_PATHLIB_H

#include "runtime/cpp/native/core/py_runtime.h"

#include "generated/std/glob.h"

namespace pytra::std::pathlib {

struct Path;

    struct Path {
        Path(const ::std::variant<str, Path>& value);
        str __str__() const;
        str __repr__() const;
        str __fspath__() const;
        Path __truediv__(const ::std::variant<str, Path>& rhs) const;
        Path parent() const;
        rc<list<Path>> parents() const;
        str name() const;
        str suffix() const;
        str stem() const;
        Path resolve() const;
        bool exists() const;
        void mkdir(bool parents = false, bool exist_ok = false) const;
        str read_text(const str& encoding = "utf-8") const;
        int64 write_text(const str& text, const str& encoding = "utf-8") const;
        rc<list<Path>> glob(const str& pattern) const;
        Path cwd();
    };


}  // namespace pytra::std::pathlib

#endif  // PYTRA_GENERATED_STD_PATHLIB_H
