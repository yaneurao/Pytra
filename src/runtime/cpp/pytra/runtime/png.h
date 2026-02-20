// AUTO-GENERATED FILE. DO NOT EDIT.
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_CPP_MODULE_PNG_H
#define PYTRA_CPP_MODULE_PNG_H

#include <cstdint>
#include <string>
#include <vector>

class str;
template <class T>
class list;

namespace pytra::runtime::png {

void write_rgb_png(const ::std::string& path, int width, int height, const ::std::vector<::std::uint8_t>& pixels);
void write_rgb_png_py(
    const str& path,
    ::std::int64_t width,
    ::std::int64_t height,
    const list<::std::uint8_t>& pixels
);

}  // namespace pytra::runtime::png

namespace pytra {
namespace png = runtime::png;
}

#endif  // PYTRA_CPP_MODULE_PNG_H
