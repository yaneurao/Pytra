// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// generated-by: src/py2cpp.py

#ifndef PYTRA_UTILS_PNG_H
#define PYTRA_UTILS_PNG_H

namespace pytra::utils::png {

int64 _crc32(const bytes& data);
int64 _adler32(const bytes& data);
bytes _u16le(int64 v);
bytes _u32be(int64 v);
bytes _zlib_deflate_store(const bytes& data);
bytes _chunk(const bytes& chunk_type, const bytes& data);
void write_rgb_png(const str& path, int64 width, int64 height, const bytes& pixels);

}  // namespace pytra::utils::png

#endif  // PYTRA_UTILS_PNG_H
