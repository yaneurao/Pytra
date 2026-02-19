// このファイルは Python の pathlib 互換機能を C++ で提供します。
// Path の最小機能（親参照、連結、テキスト読み書き）を実装しています。

#ifndef PYTRA_CPP_MODULE_PATHLIB_H
#define PYTRA_CPP_MODULE_PATHLIB_H

#include <filesystem>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>

namespace pytra::cpp_module {

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

    bool exists() const {
        return std::filesystem::exists(path_);
    }

    Path operator/(const std::string& rhs) const {
        return Path(path_ / rhs);
    }

    Path operator/(const char* rhs) const {
        return Path(path_ / rhs);
    }

    std::string string() const {
        return path_.string();
    }

    std::string read_text(const std::string& /*encoding*/ = "utf-8") const {
        std::ifstream ifs(path_);
        if (!ifs) {
            throw std::runtime_error("read_text failed: " + path_.string());
        }
        std::ostringstream oss;
        oss << ifs.rdbuf();
        return oss.str();
    }

    void write_text(const std::string& content, const std::string& /*encoding*/ = "utf-8") const {
        std::ofstream ofs(path_);
        if (!ofs) {
            throw std::runtime_error("write_text failed: " + path_.string());
        }
        ofs << content;
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

    std::string name() const {
        return path_.filename().string();
    }

    std::string stem() const {
        return path_.stem().string();
    }

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

}  // namespace pytra::cpp_module

#endif  // PYTRA_CPP_MODULE_PATHLIB_H
