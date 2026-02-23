// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: src/py2cpp.py

#ifndef PYTRA_UTILS_GIF_H
#define PYTRA_UTILS_GIF_H

namespace pytra::utils::gif {

bytes _lzw_encode(const bytes& data, int64 min_code_size);
bytes grayscale_palette();
void save_gif(const str& path, int64 width, int64 height, const list<bytes>& frames, const bytes& palette, int64 delay_cs, int64 loop);

}  // namespace pytra::utils::gif

#endif  // PYTRA_UTILS_GIF_H
