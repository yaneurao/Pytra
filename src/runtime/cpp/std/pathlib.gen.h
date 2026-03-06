// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_STD_PATHLIB_GEN_H
#define PYTRA_STD_PATHLIB_GEN_H

#include "runtime/cpp/core/py_types.ext.h"

#include "std/glob.gen.h"

namespace pytra::std::pathlib {

    struct Path {
        str _value;
        
        Path(const str& value);
        str __str__();
        str __repr__();
        str __fspath__();
        Path __truediv__(const str& rhs);
        Path parent();
        list<Path> parents();
        str name();
        str suffix();
        str stem();
        Path resolve();
        bool exists();
        void mkdir(bool parents = false, bool exist_ok = false);
        str read_text(const str& encoding = "utf-8");
        int64 write_text(const str& text, const str& encoding = "utf-8");
        list<Path> glob(const str& pattern);
        Path cwd();
    };


}  // namespace pytra::std::pathlib

#endif  // PYTRA_STD_PATHLIB_GEN_H
