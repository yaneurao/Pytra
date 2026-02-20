// AUTO-GENERATED FILE. DO NOT EDIT.
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_CPP_MODULE_GIF_H
#define PYTRA_CPP_MODULE_GIF_H

#include <cstdint>
#include <string>
#include <vector>

class str;
template <class T>
class list;

namespace pytra::runtime::gif {

::std::vector<::std::uint8_t> grayscale_palette();
list<::std::uint8_t> grayscale_palette_py();

void save_gif(
    const ::std::string& path,
    int width,
    int height,
    const ::std::vector<::std::vector<::std::uint8_t>>& frames,
    const ::std::vector<::std::uint8_t>& palette,
    int delay_cs = 4,
    int loop = 0
);
void save_gif_py(
    const str& path,
    ::std::int64_t width,
    ::std::int64_t height,
    const list<list<::std::uint8_t>>& frames,
    const list<::std::uint8_t>& palette,
    ::std::int64_t delay_cs = 4,
    ::std::int64_t loop = 0
);

}  // namespace pytra::runtime::gif

namespace pytra {
namespace gif = runtime::gif;
}

#endif  // PYTRA_CPP_MODULE_GIF_H
