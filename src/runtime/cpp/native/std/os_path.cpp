#include "runtime/cpp/generated/std/os_path.h"
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
