// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/gen/std/os.h"

namespace pytra::std::os {

    object path;
    
    struct _PathModule {
        str join(const str& a, const str& b) {
            return py_os_path_join(a, b);
        }
        str dirname(const str& p) {
            return py_os_path_dirname(p);
        }
        str basename(const str& p) {
            return py_os_path_basename(p);
        }
        ::std::tuple<str, str> splitext(const str& p) {
            auto __tuple_1 = py_os_path_splitext(p);
            auto root = py_at(__tuple_1, 0);
            auto ext = py_at(__tuple_1, 1);
            return ::std::make_tuple(root, ext);
        }
        str abspath(const str& p) {
            return py_os_path_abspath(p);
        }
        bool exists(const str& p) {
            return py_os_path_exists(p);
        }
    };
    
    str getcwd() {
        return py_os_getcwd();
    }
    
    void mkdir(const str& p) {
        py_os_mkdir(p);
    }
    
    void makedirs(const str& p, bool exist_ok = false) {
        py_os_makedirs(p, exist_ok);
    }
    
    static void __pytra_module_init() {
        static bool __initialized = false;
        if (__initialized) return;
        __initialized = true;
        /* Minimal os shim for selfhost-friendly imports. */
        path = make_object(_PathModule());
    }
    
    namespace {
        struct __pytra_module_initializer {
            __pytra_module_initializer() { __pytra_module_init(); }
        };
        static const __pytra_module_initializer __pytra_module_initializer_instance{};
    }  // namespace
    
}  // namespace pytra::std::os
