#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/std/os.h"

namespace pytra::std::os {

struct PathModule {
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
        return py_os_path_splitext(p);
    }

    str abspath(const str& p) {
        return py_os_path_abspath(p);
    }

    bool exists(const str& p) {
        return py_os_path_exists(p);
    }
};

object path = make_object(PathModule{});

str getcwd() {
    return py_os_getcwd();
}

void mkdir(const str& p) {
    py_os_mkdir(p);
}

void makedirs(const str& p, bool exist_ok) {
    py_os_makedirs(p, exist_ok);
}

}  // namespace pytra::std::os
