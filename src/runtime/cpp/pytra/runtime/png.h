// AUTO-GENERATED FILE. DO NOT EDIT.
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_CPP_MODULE_PNG_H
#define PYTRA_CPP_MODULE_PNG_H

#include <cstdint>
#include <string>
#include <vector>

namespace pytra::runtime::png {

void write_rgb_png(const std::string& path, int width, int height, const std::vector<std::uint8_t>& pixels);

}  // namespace pytra::runtime::png

namespace pytra {
namespace png = runtime::png;
}

#endif  // PYTRA_CPP_MODULE_PNG_H
