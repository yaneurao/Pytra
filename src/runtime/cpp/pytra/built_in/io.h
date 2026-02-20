#ifndef PYTRA_BUILT_IN_IO_H
#define PYTRA_BUILT_IN_IO_H

#include <fstream>
#include <sstream>
#include <string>
#include <type_traits>

namespace pytra::runtime::cpp::base {

class PyFile {
public:
    PyFile() = default;
    PyFile(const ::std::string& path, const ::std::string& mode);
    ~PyFile();

    PyFile(const PyFile&) = delete;
    PyFile& operator=(const PyFile&) = delete;
    PyFile(PyFile&& other) noexcept;
    PyFile& operator=(PyFile&& other) noexcept;

    bool is_open() const;
    void close();

    ::std::size_t write(const ::std::string& text);
    ::std::string read();

    template <class BytesLike, class = ::std::enable_if_t<!::std::is_convertible_v<BytesLike, ::std::string>>>
    void write(const BytesLike& bytes_like) {
        ensure_writable();
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
};

PyFile open(const ::std::string& path, const ::std::string& mode);

}  // namespace pytra::runtime::cpp::base

#endif  // PYTRA_BUILT_IN_IO_H
