#include "runtime/cpp/std/os_path.ext.h"
#include <filesystem>

namespace pytra::std::os_path {

str join(const str& a, const str& b) {
    if (a.empty()) return b;
    if (b.empty()) return a;
    const char tail = a.std().back();
    if (tail == '/' || tail == '\\') return a + b;
    return a + "/" + b;
}

str dirname(const str& p) {
    const ::std::string s = p.std();
    const ::std::size_t pos = s.find_last_of("/\\");
    if (pos == ::std::string::npos) return str("");
    return str(s.substr(0, pos));
}

str basename(const str& p) {
    const ::std::string s = p.std();
    const ::std::size_t pos = s.find_last_of("/\\");
    if (pos == ::std::string::npos) return str(s);
    return str(s.substr(pos + 1));
}

::std::tuple<str, str> splitext(const str& p) {
    const ::std::string s = p.std();
    const ::std::size_t sep = s.find_last_of("/\\");
    const ::std::size_t dot = s.find_last_of('.');
    if (dot == ::std::string::npos) return ::std::tuple<str, str>{str(s), str("")};
    if (sep != ::std::string::npos && dot < sep + 1) return ::std::tuple<str, str>{str(s), str("")};
    return ::std::tuple<str, str>{str(s.substr(0, dot)), str(s.substr(dot))};
}

str abspath(const str& p) {
    return str(::std::filesystem::absolute(::std::filesystem::path(p.std())).generic_string());
}

bool exists(const str& p) {
    return ::std::filesystem::exists(::std::filesystem::path(p.std()));
}

}  // namespace pytra::std::os_path

str py_os_path_join(const str& a, const str& b) {
    return pytra::std::os_path::join(a, b);
}

str py_os_path_dirname(const str& p) {
    return pytra::std::os_path::dirname(p);
}

str py_os_path_basename(const str& p) {
    return pytra::std::os_path::basename(p);
}

::std::tuple<str, str> py_os_path_splitext(const str& p) {
    return pytra::std::os_path::splitext(p);
}

str py_os_path_abspath(const str& p) {
    return pytra::std::os_path::abspath(p);
}

bool py_os_path_exists(const str& p) {
    return pytra::std::os_path::exists(p);
}
