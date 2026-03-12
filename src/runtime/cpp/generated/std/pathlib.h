// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_STD_PATHLIB_H
#define PYTRA_GENERATED_STD_PATHLIB_H

#include "runtime/cpp/native/core/py_types.h"

#include "generated/std/glob.h"

namespace pytra::std::pathlib {

struct Path;

    struct Path {
        str _value;
        
        Path(const str& value);
        str __str__();
        str __repr__();
        str __fspath__();
        Path __truediv__(const str& rhs);
        Path parent();
        rc<list<Path>> parents();
        str name();
        str suffix();
        str stem();
        Path resolve();
        bool exists();
        void mkdir(bool parents = false, bool exist_ok = false);
        str read_text(const str& encoding = "utf-8");
        int64 write_text(const str& text, const str& encoding = "utf-8");
        rc<list<Path>> glob(const str& pattern);
        Path cwd();
    };


}  // namespace pytra::std::pathlib

#endif  // PYTRA_GENERATED_STD_PATHLIB_H
