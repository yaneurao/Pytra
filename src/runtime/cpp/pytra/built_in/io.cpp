#include "runtime/cpp/pytra/built_in/io.h"

#include <stdexcept>
#include <utility>

namespace pytra::runtime::cpp::base {

PyFile::PyFile(const ::std::string& path, const ::std::string& mode) {
    if (mode == "wb") {
        ofs_.open(path, ::std::ios::binary | ::std::ios::out | ::std::ios::trunc);
    } else if (mode == "ab") {
        ofs_.open(path, ::std::ios::binary | ::std::ios::out | ::std::ios::app);
    } else {
        throw ::std::runtime_error("open: unsupported mode: " + mode);
    }
    if (!ofs_.is_open()) {
        throw ::std::runtime_error("open: failed to open file: " + path);
    }
}

PyFile::~PyFile() {
    if (ofs_.is_open()) {
        ofs_.close();
    }
}

PyFile::PyFile(PyFile&& other) noexcept : ofs_(::std::move(other.ofs_)) {}

PyFile& PyFile::operator=(PyFile&& other) noexcept {
    if (this != &other) {
        ofs_ = ::std::move(other.ofs_);
    }
    return *this;
}

bool PyFile::is_open() const {
    return ofs_.is_open();
}

void PyFile::close() {
    if (ofs_.is_open()) {
        ofs_.close();
    }
}

void PyFile::ensure_open() const {
    if (!ofs_.is_open()) {
        throw ::std::runtime_error("file is not open");
    }
}

PyFile open(const ::std::string& path, const ::std::string& mode) {
    return PyFile(path, mode);
}

}  // namespace pytra::runtime::cpp::base
