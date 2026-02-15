// このファイルは Python 由来の補助モジュール（Path, sys, str など）を
// C++ 側で扱うための最小ランタイム実装です。

#ifndef PYCS_CPP_MODULE_PY_RUNTIME_MODULES_H
#define PYCS_CPP_MODULE_PY_RUNTIME_MODULES_H

#include <cstdlib>
#include <filesystem>
#include <stdexcept>
#include <string>
#include <vector>

namespace pycs::cpp_module {

class Path;

class PathParentProxy {
public:
    explicit PathParentProxy(const Path* owner) : owner_(owner) {}
    Path* operator->() const;
    Path operator()() const;

private:
    const Path* owner_;
};

class PathParentsProxy {
public:
    explicit PathParentsProxy(const Path* owner) : owner_(owner) {}
    Path operator[](std::size_t index) const;

private:
    const Path* owner_;
};

class Path {
public:
    Path() : parent(this), parents(this) {}
    explicit Path(const std::string& value) : path_(value), parent(this), parents(this) {}
    explicit Path(const char* value) : path_(value), parent(this), parents(this) {}
    explicit Path(std::filesystem::path value)
        : path_(std::move(value)), parent(this), parents(this) {}
    Path(const Path& other) : path_(other.path_), parent(this), parents(this) {}
    Path(Path&& other) noexcept : path_(std::move(other.path_)), parent(this), parents(this) {}

    Path& operator=(const Path& other) {
        if (this != &other) {
            path_ = other.path_;
        }
        return *this;
    }

    Path& operator=(Path&& other) noexcept {
        if (this != &other) {
            path_ = std::move(other.path_);
        }
        return *this;
    }

    Path resolve() const {
        return Path(std::filesystem::absolute(path_));
    }

    Path operator/(const std::string& rhs) const {
        return Path(path_ / rhs);
    }

    std::string string() const {
        return path_.string();
    }

    void mkdir(bool parents_flag = false, bool exist_ok = false) const {
        std::error_code ec;
        if (parents_flag) {
            std::filesystem::create_directories(path_, ec);
        } else {
            std::filesystem::create_directory(path_, ec);
        }
        if (!exist_ok && ec) {
            throw std::runtime_error("mkdir failed: " + ec.message());
        }
    }

    Path* operator->() { return this; }
    const Path* operator->() const { return this; }

    const std::filesystem::path& raw_path() const { return path_; }

    PathParentProxy parent;
    PathParentsProxy parents;

private:
    std::filesystem::path path_;
};

inline Path* PathParentProxy::operator->() const {
    static thread_local Path cached;
    cached = Path(owner_->raw_path().parent_path());
    return &cached;
}

inline Path PathParentProxy::operator()() const {
    return Path(owner_->raw_path().parent_path());
}

inline Path PathParentsProxy::operator[](std::size_t index) const {
    std::filesystem::path cur = owner_->raw_path();
    for (std::size_t i = 0; i <= index; ++i) {
        cur = cur.parent_path();
    }
    return Path(cur);
}

inline std::string str(const Path& p) {
    return p.string();
}

class SysPath {
public:
    void insert(int index, const std::string& value) {
        if (index < 0 || static_cast<std::size_t>(index) >= entries_.size()) {
            entries_.push_back(value);
            return;
        }
        entries_.insert(entries_.begin() + index, value);
    }

private:
    std::vector<std::string> entries_;
};

class SysModule {
public:
    SysModule() : path(new SysPath()) {}
    ~SysModule() { delete path; }

    SysPath* path;
};

inline SysModule* sys = new SysModule();

}  // namespace pycs::cpp_module

using pycs::cpp_module::Path;
using pycs::cpp_module::str;
using pycs::cpp_module::sys;

#ifndef __file__
#define __file__ __FILE__
#endif

// Python側の transpile 呼び出しをC++から委譲するためのブリッジ。
inline void transpile(const std::string& input_path, const std::string& output_path) {
    std::string cmd =
        "python -c \"import sys;sys.path.insert(0,'.');from src.pycpp_transpiler import transpile;"
        "transpile(r'" +
        input_path + "', r'" + output_path + "')\"";
    std::system(cmd.c_str());
}

#endif  // PYCS_CPP_MODULE_PY_RUNTIME_MODULES_H
