// AUTO-GENERATED WRAPPER. DO NOT EDIT MANUALLY.
// source implementation: src/runtime/cpp/pylib/generated/gif_impl.cpp

#include "runtime/cpp/pylib/gif.h"

#include "runtime/cpp/py_runtime.h"

namespace pytra::pylib::gif {
namespace generated {
#include "runtime/cpp/pylib/generated/gif_impl.cpp"
}  // namespace generated

std::vector<std::uint8_t> grayscale_palette() {
    const bytes raw = generated::grayscale_palette();
    return std::vector<std::uint8_t>(raw.begin(), raw.end());
}

void save_gif(
    const std::string& path,
    int width,
    int height,
    const std::vector<std::vector<std::uint8_t>>& frames,
    const std::vector<std::uint8_t>& palette,
    int delay_cs,
    int loop
) {
    list<bytes> frame_list{};
    frame_list.reserve(frames.size());
    for (const auto& fr : frames) {
        frame_list.append(bytes(fr.begin(), fr.end()));
    }
    const bytes pal_bytes(palette.begin(), palette.end());
    generated::save_gif(
        str(path),
        int64(width),
        int64(height),
        frame_list,
        pal_bytes,
        int64(delay_cs),
        int64(loop)
    );
}

}  // namespace pytra::pylib::gif

