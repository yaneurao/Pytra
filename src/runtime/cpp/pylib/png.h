// このファイルは PNG 出力の最小実装を提供します。
// Python 側の `png.write_rgb_png` に対応します。

#ifndef PYTRA_CPP_MODULE_PNG_H
#define PYTRA_CPP_MODULE_PNG_H

#include <cstdint>
#include <string>
#include <vector>

namespace pytra::cpp_module::png {

/**
 * @brief RGB 8bit バッファを PNG ファイルとして保存します。
 * @param path 出力PNGファイルパス。
 * @param width 画像幅（pixel）。
 * @param height 画像高さ（pixel）。
 * @param pixels 長さ width*height*3 の RGB バイト列。
 */
void write_rgb_png(const std::string& path, int width, int height, const std::vector<std::uint8_t>& pixels);

/**
 * @brief RGB 8bit バッファを PPM(P6) ファイルとして保存します。
 * @param path 出力PPMファイルパス。
 * @param width 画像幅（pixel）。
 * @param height 画像高さ（pixel）。
 * @param pixels 長さ width*height*3 の RGB バイト列。
 */
void write_rgb_ppm(const std::string& path, int width, int height, const std::vector<std::uint8_t>& pixels);

}  // namespace pytra::cpp_module::png

#endif  // PYTRA_CPP_MODULE_PNG_H
