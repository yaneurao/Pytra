// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/gen/std/os.h"

namespace pytra::std::os {

    _PathModule path;
    
    struct _PathModule {
        str join(const str& a, const str& b) {
            return pytra::std::os::path.join(a, b);
        }
        str dirname(const str& p) {
            return pytra::std::os::path.dirname(p);
        }
        str basename(const str& p) {
            return pytra::std::os::path.basename(p);
        }
        ::std::tuple<str, str> splitext(const str& p) {
            auto __tuple_1 = pytra::std::os::path.splitext(p);
            auto root = py_at(__tuple_1, 0);
            auto ext = py_at(__tuple_1, 1);
            return ::std::make_tuple(root, ext);
        }
        str abspath(const str& p) {
            return pytra::std::os::path.abspath(p);
        }
        bool exists(const str& p) {
            return pytra::std::os::path.exists(p);
        }
    };
    
    str getcwd() {
        return pytra::std::os::getcwd();
    }
    
    void mkdir(const str& p) {
        pytra::std::os::mkdir(p);
    }
    
    void makedirs(const str& p, bool exist_ok = false) {
        pytra::std::os::makedirs(p, exist_ok);
    }
    
    static void __pytra_module_init() {
        static bool __initialized = false;
        if (__initialized) return;
        __initialized = true;
        /* Minimal os shim for selfhost-friendly imports. */
        path = _PathModule();
    }
    
}  // namespace pytra::std::os
