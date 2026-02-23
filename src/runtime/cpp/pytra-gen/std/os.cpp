// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os.py
// generated-by: src/py2cpp.py

#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/os.h"

namespace pytra::std::os {

    /* Minimal os shim for selfhost-friendly imports. */
    
    
    
    struct _PathModule : public PyObj {
        str join(const str& a, const str& b) {
            return py_to_string(py_os_path_join(a, b));
        }
        str dirname(const str& p) {
            return py_to_string(py_os_path_dirname(p));
        }
        str basename(const str& p) {
            return py_to_string(py_os_path_basename(p));
        }
        ::std::tuple<str, str> splitext(const str& p) {
            auto __tuple_1 = py_os_path_splitext(p);
            auto root = ::std::get<0>(__tuple_1);
            auto ext = ::std::get<1>(__tuple_1);
            return ::std::make_tuple(root, ext);
        }
        str abspath(const str& p) {
            return py_to_string(py_os_path_abspath(p));
        }
        bool exists(const str& p) {
            return py_to_bool(py_os_path_exists(p));
        }
    };
    
    rc<_PathModule> path = ::rc_new<_PathModule>();
    
    str getcwd() {
        return py_to_string(py_os_getcwd());
    }
    
    void mkdir(const str& p) {
        py_os_mkdir(p);
    }
    
    void makedirs(const str& p, bool exist_ok) {
        py_os_makedirs(p, exist_ok);
    }
    
}  // namespace pytra::std::os
