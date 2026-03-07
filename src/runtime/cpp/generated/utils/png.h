// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_UTILS_PNG_H
#define PYTRA_GENERATED_UTILS_PNG_H

#include "runtime/cpp/core/py_types.h"

namespace pytra::utils::png {

void _png_append_list(list<int64>& dst, const list<int64>& src);
int64 _crc32(const list<int64>& data);
int64 _adler32(const list<int64>& data);
list<int64> _png_u16le(int64 v);
list<int64> _png_u32be(int64 v);
list<int64> _zlib_deflate_store(const list<int64>& data);
list<int64> _chunk(const list<int64>& chunk_type, const list<int64>& data);
void write_rgb_png(const str& path, int64 width, int64 height, const bytes& pixels);

}  // namespace pytra::utils::png

#endif  // PYTRA_GENERATED_UTILS_PNG_H
