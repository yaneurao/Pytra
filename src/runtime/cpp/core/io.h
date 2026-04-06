#ifndef PYTRA_BUILT_IN_IO_H
#define PYTRA_BUILT_IN_IO_H

#include <fstream>
#include <sstream>
#include <string>
#include <type_traits>
#include <vector>

#include "core/py_scalar_types.h"

class str;

template <typename T>
struct Object;
using object = Object<void>;

namespace pytra::runtime::cpp::base {

class PyFile {
public:
    using iterator = ::std::vector<::std::string>::iterator;
    using const_iterator = ::std::vector<::std::string>::const_iterator;

    PyFile() = default;
    PyFile(const ::std::string& path, const ::std::string& mode);
    ~PyFile();

    PyFile(const PyFile&) = delete;
    PyFile& operator=(const PyFile&) = delete;
    PyFile(PyFile&& other) noexcept;
    PyFile& operator=(PyFile&& other) noexcept;

    bool is_open() const;
    PyFile& __enter__();
    void __exit__(const object& exc_type, const object& exc_val, const object& exc_tb);
    void close();

    int64 write(const ::std::string& text);
    str read();
    iterator begin();
    iterator end();
    const_iterator begin() const;
    const_iterator end() const;

    template <class BytesLike, class = ::std::enable_if_t<!::std::is_convertible_v<BytesLike, ::std::string>>>
    void write(const BytesLike& bytes_like) {
        ensure_writable();
        if constexpr (requires { bytes_like.data(); bytes_like.size(); }) {
            using Elem = ::std::remove_cv_t<::std::remove_pointer_t<decltype(bytes_like.data())>>;
            if constexpr (sizeof(Elem) == 1) {
                const auto* ptr = bytes_like.data();
                const auto n = static_cast<::std::streamsize>(bytes_like.size());
                if (ptr != nullptr && n > 0) {
                    ofs_.write(reinterpret_cast<const char*>(ptr), n);
                }
                return;
            }
        }
        for (const auto& v : bytes_like) {
            ofs_.put(static_cast<char>(v));
        }
    }

private:
    void ensure_open() const;
    void ensure_writable() const;
    void ensure_readable() const;

    ::std::ofstream ofs_;
    ::std::ifstream ifs_;
    bool readable_ = false;
    bool writable_ = false;
    mutable bool line_cache_ready_ = false;
    mutable ::std::vector<::std::string> line_cache_;
};

PyFile open(const ::std::string& path, const ::std::string& mode);
PyFile open(const ::std::string& path);

}  // namespace pytra::runtime::cpp::base

#endif  // PYTRA_BUILT_IN_IO_H
