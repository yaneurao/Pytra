#include "core/io.h"

#include <stdexcept>
#include <utility>

#include "core/py_types.h"

namespace pytra::runtime::cpp::base {

PyFile::PyFile(const ::std::string& path, const ::std::string& mode) {
    if (mode == "wb") {
        ofs_.open(path, ::std::ios::binary | ::std::ios::out | ::std::ios::trunc);
        writable_ = true;
    } else if (mode == "ab") {
        ofs_.open(path, ::std::ios::binary | ::std::ios::out | ::std::ios::app);
        writable_ = true;
    } else if (mode == "w") {
        ofs_.open(path, ::std::ios::out | ::std::ios::trunc);
        writable_ = true;
    } else if (mode == "a") {
        ofs_.open(path, ::std::ios::out | ::std::ios::app);
        writable_ = true;
    } else if (mode == "r") {
        ifs_.open(path, ::std::ios::in);
        readable_ = true;
    } else if (mode == "rb") {
        ifs_.open(path, ::std::ios::in | ::std::ios::binary);
        readable_ = true;
    } else {
        throw ::std::runtime_error("open: unsupported mode: " + mode);
    }
    if ((writable_ && !ofs_.is_open()) || (readable_ && !ifs_.is_open())) {
        throw ::std::runtime_error("open: failed to open file: " + path);
    }
}

PyFile::~PyFile() {
    if (ifs_.is_open()) {
        ifs_.close();
    }
    if (ofs_.is_open()) {
        ofs_.close();
    }
}

PyFile::PyFile(PyFile&& other) noexcept
    : ofs_(::std::move(other.ofs_)),
      ifs_(::std::move(other.ifs_)),
      readable_(other.readable_),
      writable_(other.writable_),
      line_cache_ready_(other.line_cache_ready_),
      line_cache_(::std::move(other.line_cache_)) {}

PyFile& PyFile::operator=(PyFile&& other) noexcept {
    if (this != &other) {
        ofs_ = ::std::move(other.ofs_);
        ifs_ = ::std::move(other.ifs_);
        readable_ = other.readable_;
        writable_ = other.writable_;
        line_cache_ready_ = other.line_cache_ready_;
        line_cache_ = ::std::move(other.line_cache_);
    }
    return *this;
}

bool PyFile::is_open() const {
    return ifs_.is_open() || ofs_.is_open();
}

PyFile& PyFile::__enter__() {
    return *this;
}

void PyFile::__exit__(const object& exc_type, const object& exc_val, const object& exc_tb) {
    (void)exc_type;
    (void)exc_val;
    (void)exc_tb;
    close();
}

void PyFile::close() {
    if (ifs_.is_open()) {
        ifs_.close();
    }
    if (ofs_.is_open()) {
        ofs_.close();
    }
    line_cache_ready_ = false;
    line_cache_.clear();
}

void PyFile::ensure_open() const {
    if (!is_open()) {
        throw ::std::runtime_error("file is not open");
    }
}

void PyFile::ensure_writable() const {
    if (!writable_ || !ofs_.is_open()) {
        throw ::std::runtime_error("file is not writable");
    }
}

void PyFile::ensure_readable() const {
    if (!readable_ || !ifs_.is_open()) {
        throw ::std::runtime_error("file is not readable");
    }
}

int64 PyFile::write(const ::std::string& text) {
    ensure_writable();
    ofs_ << text;
    return static_cast<int64>(text.size());
}

str PyFile::read() {
    ensure_readable();
    ::std::stringstream ss;
    ss << ifs_.rdbuf();
    return str(ss.str());
}

PyFile::iterator PyFile::begin() {
    ensure_readable();
    if (!line_cache_ready_) {
        line_cache_.clear();
        ifs_.clear();
        ifs_.seekg(0, ::std::ios::beg);
        ::std::string line;
        while (::std::getline(ifs_, line)) {
            if (!line.empty() && line.back() == '\r') {
                line.pop_back();
            }
            line_cache_.push_back(line);
        }
        ifs_.clear();
        ifs_.seekg(0, ::std::ios::beg);
        line_cache_ready_ = true;
    }
    return line_cache_.begin();
}

PyFile::iterator PyFile::end() {
    if (!line_cache_ready_) {
        (void)begin();
    }
    return line_cache_.end();
}

PyFile::const_iterator PyFile::begin() const {
    if (!line_cache_ready_) {
        (void)const_cast<PyFile*>(this)->begin();
    }
    return line_cache_.cbegin();
}

PyFile::const_iterator PyFile::end() const {
    if (!line_cache_ready_) {
        (void)const_cast<PyFile*>(this)->begin();
    }
    return line_cache_.cend();
}

PyFile open(const ::std::string& path, const ::std::string& mode) {
    return PyFile(path, mode);
}

PyFile open(const ::std::string& path) {
    return open(path, "r");
}

}  // namespace pytra::runtime::cpp::base
