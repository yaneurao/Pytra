// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_UTILS_GIF_H
#define PYTRA_GENERATED_UTILS_GIF_H

#include "runtime/cpp/native/core/py_types.h"

namespace pytra::utils::gif {

void _gif_append_list(rc<list<int64>>& dst, const rc<list<int64>>& src);
rc<list<int64>> _gif_u16le(int64 v);
bytes _lzw_encode(const bytes& data, int64 min_code_size = 8);
bytes grayscale_palette();
void save_gif(const str& path, int64 width, int64 height, const list<bytes>& frames, const bytes& palette, int64 delay_cs = 4, int64 loop = 0);

}  // namespace pytra::utils::gif

#endif  // PYTRA_GENERATED_UTILS_GIF_H
