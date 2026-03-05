// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/glob.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/gen/std/glob.h"

namespace pytra::std::glob {

    list<str> glob(const str& pattern) {
        return pytra::std::glob::glob(pattern);
    }
    
    static void __pytra_module_init() {
        static bool __initialized = false;
        if (__initialized) return;
        __initialized = true;
        /* Minimal glob shim for selfhost-friendly imports. */
    }
    
}  // namespace pytra::std::glob
