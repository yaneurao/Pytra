// Python の pylib.gif に対応する GIF 書き出し補助です。

#ifndef PYTRA_CPP_MODULE_GIF_H
#define PYTRA_CPP_MODULE_GIF_H

#include <cstdint>
#include <string>
#include <vector>

namespace pytra::cpp_module::gif {

// 0..255 のグレースケールパレット (256*3 bytes) を返します。
std::vector<std::uint8_t> grayscale_palette();

// インデックスカラーフレーム列を GIF89a アニメーションとして保存します。
void save_gif(
    const std::string& path,
    int width,
    int height,
    const std::vector<std::vector<std::uint8_t>>& frames,
    const std::vector<std::uint8_t>& palette,
    int delay_cs = 4,
    int loop = 0
);

}  // namespace pytra::cpp_module::gif

#endif  // PYTRA_CPP_MODULE_GIF_H
