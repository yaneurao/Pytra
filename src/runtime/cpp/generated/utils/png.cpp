// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// generated-by: tools/gen_runtime_from_manifest.py

#include "runtime/cpp/core/py_runtime.h"
#include "runtime/cpp/core/process_runtime.h"
#include "runtime/cpp/core/scope_exit.h"

namespace pytra::utils::png {

/* PNG 書き出しユーティリティ（Python実行用）。

このモジュールは sample/py のスクリプトから利用し、
RGB 8bit バッファを PNG ファイルとして保存する。
 */

void _png_append_list(list<int64>& dst, const list<int64>& src) {
    int64 i = 0;
    int64 n = src.size();
    while (i < n) {
        dst.append(src[i]);
        i++;
    }
}

int64 _crc32(const list<int64>& data) {
    int64 crc = 0xFFFFFFFF;
    int64 poly = 0xEDB88320;
    for (int64 b : data) {
        crc = crc ^ b;
        int64 i = 0;
        while (i < 8) {
            int64 lowbit = crc & 1;
            if (lowbit != 0)
                crc = crc >> 1 ^ poly;
            else
                crc = crc >> 1;
            i++;
        }
    }
    return crc ^ 0xFFFFFFFF;
}

int64 _adler32(const list<int64>& data) {
    int64 mod = 65521;
    int64 s1 = 1;
    int64 s2 = 0;
    for (int64 b : data) {
        s1 += b;
        if (s1 >= mod)
            s1 -= mod;
        s2 += s1;
        s2 = s2 % mod;
    }
    return (s2 << 16 | s1) & 0xFFFFFFFF;
}

list<int64> _png_u16le(int64 v) {
    return list<int64>{v & 0xFF, v >> 8 & 0xFF};
}

list<int64> _png_u32be(int64 v) {
    return list<int64>{v >> 24 & 0xFF, v >> 16 & 0xFF, v >> 8 & 0xFF, v & 0xFF};
}

list<int64> _zlib_deflate_store(const list<int64>& data) {
    list<int64> out = {};
    _png_append_list(out, list<int64>{0x78, 0x01});
    int64 n = data.size();
    int64 pos = 0;
    while (pos < n) {
        int64 remain = n - pos;
        int64 chunk_len = (remain > 65535 ? 65535 : remain);
        int64 final = (pos + chunk_len >= n ? 1 : 0);
        out.append(final);
        _png_append_list(out, _png_u16le(chunk_len));
        _png_append_list(out, _png_u16le(0xFFFF ^ chunk_len));
        int64 i = pos;
        int64 end = pos + chunk_len;
        while (i < end) {
            out.append(data[i]);
            i++;
        }
        pos += chunk_len;
    }
    _png_append_list(out, _png_u32be(_adler32(data)));
    return out;
}

list<int64> _chunk(const list<int64>& chunk_type, const list<int64>& data) {
    list<int64> crc_input = {};
    _png_append_list(crc_input, chunk_type);
    _png_append_list(crc_input, data);
    int64 crc = _crc32(crc_input) & 0xFFFFFFFF;
    list<int64> out = {};
    _png_append_list(out, _png_u32be(data.size()));
    _png_append_list(out, chunk_type);
    _png_append_list(out, data);
    _png_append_list(out, _png_u32be(crc));
    return out;
}

void write_rgb_png(const str& path, int64 width, int64 height, const bytes& pixels) {
    list<int64> raw = {};
    for (uint8 b : pixels) {
        raw.append(b);
    }
    int64 expected = width * height * 3;
    if (raw.size() != expected)
        throw ValueError("pixels length mismatch: got=" + ::std::to_string(raw.size()) + " expected=" + ::std::to_string(expected));
    list<int64> scanlines = {};
    int64 row_bytes = width * 3;
    int64 y = 0;
    while (y < height) {
        scanlines.append(0);
        int64 start = y * row_bytes;
        int64 end = start + row_bytes;
        int64 i = start;
        while (i < end) {
            scanlines.append(raw[i]);
            i++;
        }
        y++;
    }
    list<int64> ihdr = {};
    _png_append_list(ihdr, _png_u32be(width));
    _png_append_list(ihdr, _png_u32be(height));
    _png_append_list(ihdr, list<int64>{8, 2, 0, 0, 0});
    list<int64> idat = _zlib_deflate_store(scanlines);
    
    list<int64> png = {};
    _png_append_list(png, list<int64>{137, 80, 78, 71, 13, 10, 26, 10});
    _png_append_list(png, _chunk(list<int64>{73, 72, 68, 82}, ihdr));
    _png_append_list(png, _chunk(list<int64>{73, 68, 65, 84}, idat));
    list<int64> iend_data = {};
    _png_append_list(png, _chunk(list<int64>{73, 69, 78, 68}, iend_data));
    
    pytra::runtime::cpp::base::PyFile f = open(path, "wb");
    {
        auto __finally_1 = py_make_scope_exit([&]() {
            f.close();
        });
        f.write(bytes(png));
    }
}

}  // namespace pytra::utils::png
