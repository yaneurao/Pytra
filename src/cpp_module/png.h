// このファイルは PNG 出力の最小実装を提供します。
// Python 側の `png_helper.write_rgb_png` に対応します。

#ifndef PYCS_CPP_MODULE_PNG_H
#define PYCS_CPP_MODULE_PNG_H

#include <string>

namespace pycs::cpp_module::png {

/**
 * @brief RGB 8bit バッファを PNG ファイルとして保存します。
 * @param path 出力PNGファイルパス。
 * @param width 画像幅（pixel）。
 * @param height 画像高さ（pixel）。
 * @param pixels 長さ width*height*3 の RGB バイト列。
 */
void write_rgb_png(const std::string& path, int width, int height, const std::string& pixels);

}  // namespace pycs::cpp_module::png

#endif  // PYCS_CPP_MODULE_PNG_H
