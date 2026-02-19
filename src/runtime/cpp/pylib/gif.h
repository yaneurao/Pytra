// AUTO-GENERATED FILE. DO NOT EDIT.
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_CPP_MODULE_GIF_H
#define PYTRA_CPP_MODULE_GIF_H

#include <cstdint>
#include <string>
#include <vector>

namespace pytra::pylib::gif {

std::vector<std::uint8_t> grayscale_palette();

void save_gif(
    const std::string& path,
    int width,
    int height,
    const std::vector<std::vector<std::uint8_t>>& frames,
    const std::vector<std::uint8_t>& palette,
    int delay_cs = 4,
    int loop = 0
);

}  // namespace pytra::pylib::gif

namespace pytra {
namespace gif = pylib::gif;
}

#endif  // PYTRA_CPP_MODULE_GIF_H
