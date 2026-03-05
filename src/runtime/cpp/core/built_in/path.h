#ifndef PYTRA_BUILT_IN_PATH_H
#define PYTRA_BUILT_IN_PATH_H

#include "container_common.h"

class Path {
public:
    Path() = default;
    Path(const char* s) : p_(s) {}
    Path(const str& s) : p_(::std::string(s)) {}
    Path(const ::std::filesystem::path& p) : p_(p) {}

    Path operator/(const char* rhs) const { return Path(p_ / rhs); }
    Path operator/(const str& rhs) const { return Path(p_ / ::std::filesystem::path(::std::string(rhs))); }
    Path operator/(const Path& rhs) const { return Path(p_ / rhs.p_); }

    Path parent() const { return Path(p_.parent_path()); }
    str name() const { return p_.filename().string(); }
    str stem() const { return p_.stem().string(); }
    bool exists() const { return ::std::filesystem::exists(p_); }
    void write_text(const str& s) const {
        ::std::ofstream ofs(p_);
        ofs << s;
    }
    str read_text() const {
        ::std::ifstream ifs(p_);
        ::std::stringstream ss;
        ss << ifs.rdbuf();
        return ss.str();
    }

    void mkdir(bool parents = false, bool exist_ok = false) const {
        ::std::error_code ec;
        bool created = parents ? ::std::filesystem::create_directories(p_, ec) : ::std::filesystem::create_directory(p_, ec);
        if (!created && !exist_ok && !::std::filesystem::exists(p_)) {
            throw ::std::runtime_error("mkdir failed: " + p_.string());
        }
    }

    str string() const { return p_.string(); }
    const ::std::filesystem::path& native() const { return p_; }
    operator const ::std::filesystem::path&() const { return p_; }  // NOLINT(google-explicit-constructor)

private:
    ::std::filesystem::path p_;
};


#endif  // PYTRA_BUILT_IN_PATH_H
