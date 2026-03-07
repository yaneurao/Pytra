#include "runtime/cpp/generated/std/glob.h"
#include <filesystem>

namespace pytra::std::glob {

namespace {

bool glob_match_simple(const str& text, const str& pattern) {
    const ::std::string s = text.std();
    const ::std::string p = pattern.std();
    ::std::size_t si = 0;
    ::std::size_t pi = 0;
    ::std::size_t star = ::std::string::npos;
    ::std::size_t mark = 0;
    while (si < s.size()) {
        if (pi < p.size() && (p[pi] == '?' || p[pi] == s[si])) {
            ++si;
            ++pi;
            continue;
        }
        if (pi < p.size() && p[pi] == '*') {
            star = pi++;
            mark = si;
            continue;
        }
        if (star != ::std::string::npos) {
            pi = star + 1;
            si = ++mark;
            continue;
        }
        return false;
    }
    while (pi < p.size() && p[pi] == '*') ++pi;
    return pi == p.size();
}

}  // namespace

list<str> glob(const str& pattern) {
    const ::std::string pat = pattern.std();
    const ::std::size_t sep = pat.find_last_of("/\\");
    const ::std::string dir = (sep == ::std::string::npos) ? "." : pat.substr(0, sep);
    const ::std::string mask = (sep == ::std::string::npos) ? pat : pat.substr(sep + 1);
    list<str> out{};
    ::std::error_code ec{};
    if (mask.find('*') == ::std::string::npos && mask.find('?') == ::std::string::npos) {
        const ::std::filesystem::path single = ::std::filesystem::path(pat);
        if (::std::filesystem::exists(single, ec)) out.append(str(single.generic_string()));
        return out;
    }
    for (const auto& ent : ::std::filesystem::directory_iterator(::std::filesystem::path(dir), ec)) {
        if (ec) break;
        const str name(ent.path().filename().generic_string());
        if (!glob_match_simple(name, str(mask))) continue;
        out.append(str(ent.path().generic_string()));
    }
    return out;
}

}  // namespace pytra::std::glob
