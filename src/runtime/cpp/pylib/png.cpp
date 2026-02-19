// AUTO-GENERATED WRAPPER. DO NOT EDIT MANUALLY.
// source implementation: src/runtime/cpp/pylib/generated/png_impl.cpp

#include "runtime/cpp/pylib/png.h"

#include "runtime/cpp/py_runtime.h"

namespace pytra::pylib::png {
namespace generated {
#include "runtime/cpp/pylib/generated/png_impl.cpp"
}  // namespace generated

void write_rgb_png(const std::string& path, int width, int height, const std::vector<std::uint8_t>& pixels) {
    const bytes raw(pixels.begin(), pixels.end());
    generated::write_rgb_png(str(path), int64(width), int64(height), raw);
}

}  // namespace pytra::pylib::png

