#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/std/glob.h"

namespace pytra::std::glob {

list<str> glob(const str& pattern) {
    return py_glob_glob(pattern);
}

}  // namespace pytra::std::glob
