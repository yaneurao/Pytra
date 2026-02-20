#include "runtime/cpp/pytra/built_in/io.h"

#include <stdexcept>
#include <utility>

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
      writable_(other.writable_) {}

PyFile& PyFile::operator=(PyFile&& other) noexcept {
    if (this != &other) {
        ofs_ = ::std::move(other.ofs_);
        ifs_ = ::std::move(other.ifs_);
        readable_ = other.readable_;
        writable_ = other.writable_;
    }
    return *this;
}

bool PyFile::is_open() const {
    return ifs_.is_open() || ofs_.is_open();
}

void PyFile::close() {
    if (ifs_.is_open()) {
        ifs_.close();
    }
    if (ofs_.is_open()) {
        ofs_.close();
    }
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

::std::size_t PyFile::write(const ::std::string& text) {
    ensure_writable();
    ofs_ << text;
    return text.size();
}

::std::string PyFile::read() {
    ensure_readable();
    ::std::stringstream ss;
    ss << ifs_.rdbuf();
    return ss.str();
}

PyFile open(const ::std::string& path, const ::std::string& mode) {
    return PyFile(path, mode);
}

}  // namespace pytra::runtime::cpp::base
