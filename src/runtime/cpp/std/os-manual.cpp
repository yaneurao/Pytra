#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/std/os.h"

namespace pytra::std::os {

str getcwd() {
    return str(::std::filesystem::current_path().generic_string());
}

void mkdir(const str& p) {
    const ::std::filesystem::path target(p.std());
    ::std::error_code ec;
    const bool created = ::std::filesystem::create_directory(target, ec);
    if (!created && !::std::filesystem::exists(target, ec)) {
        throw ::std::runtime_error("mkdir failed: " + p.std());
    }
}

void makedirs(const str& p, bool exist_ok) {
    const ::std::filesystem::path target(p.std());
    ::std::error_code ec;
    const bool created = ::std::filesystem::create_directories(target, ec);
    if (!created && !exist_ok && !::std::filesystem::exists(target, ec)) {
        throw ::std::runtime_error("makedirs failed: " + p.std());
    }
}

}  // namespace pytra::std::os
