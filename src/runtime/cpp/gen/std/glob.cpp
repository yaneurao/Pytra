// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/glob.py
// generated-by: src/py2cpp.py

#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/gen/std/glob.h"

namespace pytra::std::glob {

    /* Minimal glob shim for selfhost-friendly imports. */
    
    
    
    list<str> glob(const str& pattern) {
        return static_cast<list<str>>(py_glob_glob(pattern));
    }
    
}  // namespace pytra::std::glob
