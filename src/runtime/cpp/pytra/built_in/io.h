#ifndef PYTRA_BUILT_IN_IO_H
#define PYTRA_BUILT_IN_IO_H

#include <fstream>
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

    template <class BytesLike>
    void write(const BytesLike& bytes_like) {
        ensure_open();
        for (const auto& v : bytes_like) {
            ofs_.put(static_cast<char>(v));
        }
    }

private:
    void ensure_open() const;

    ::std::ofstream ofs_;
};

PyFile open(const ::std::string& path, const ::std::string& mode);

}  // namespace pytra::runtime::cpp::base

#endif  // PYTRA_BUILT_IN_IO_H
