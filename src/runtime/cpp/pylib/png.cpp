// このファイルは src/pylib/png.py を正本として C++ 実装化したものです。

#include "runtime/cpp/pylib/png.h"

#include "runtime/cpp/py_runtime.h"

namespace pytra::pylib::png {
namespace {

int64 _crc32(const bytes& data) {
    int64 crc = 4294967295;
    int64 poly = 3988292384;
    for (uint8 b : data) {
        crc ^= b;
        int64 i = 0;
        while (i < 8) {
            if ((crc & 1) != 0) {
                crc = (crc >> 1) ^ poly;
            } else {
                crc >>= 1;
            }
            i++;
        }
    }
    return crc ^ 4294967295;
}

int64 _adler32(const bytes& data) {
    int64 mod = 65521;
    int64 s1 = 1;
    int64 s2 = 0;
    for (uint8 b : data) {
        s1 += b;
        if (s1 >= mod) {
            s1 -= mod;
        }
        s2 += s1;
        s2 %= mod;
    }
    return ((s2 << 16) | s1) & 4294967295;
}

bytes _u16le(int64 v) {
    return bytes(list<int64>{v & 255, (v >> 8) & 255});
}

bytes _u32be(int64 v) {
    return bytes(list<int64>{(v >> 24) & 255, (v >> 16) & 255, (v >> 8) & 255, v & 255});
}

bytes _zlib_deflate_store(const bytes& data) {
    bytearray out = bytearray{};
    out.extend(py_bytes_lit("\x78\x01"));
    int64 n = py_len(data);
    int64 pos = 0;
    while (pos < n) {
        int64 remain = n - pos;
        int64 chunk_len = (remain > 65535 ? 65535 : remain);
        int64 final = ((pos + chunk_len) >= n ? 1 : 0);
        out.append(final);
        out.extend(_u16le(chunk_len));
        out.extend(_u16le(65535 ^ chunk_len));
        out.extend(py_slice(data, pos, pos + chunk_len));
        pos += chunk_len;
    }
    out.extend(_u32be(_adler32(data)));
    return bytes(out);
}

bytes _chunk(const bytes& chunk_type, const bytes& data) {
    bytes length = _u32be(py_len(data));
    int64 crc = _crc32(chunk_type + data) & 4294967295;
    return length + chunk_type + data + _u32be(crc);
}

void write_rgb_png_impl(const str& path, int64 width, int64 height, const bytes& pixels) {
    bytes raw = bytes(pixels);
    int64 expected = width * height * 3;
    if (py_len(raw) != expected) {
        throw ValueError(
            "pixels length mismatch: got=" + std::to_string(py_len(raw)) + " expected=" + std::to_string(expected)
        );
    }

    bytearray scanlines = bytearray{};
    int64 row_bytes = width * 3;
    int64 y = 0;
    while (y < height) {
        scanlines.append(0);
        int64 start = y * row_bytes;
        int64 end = start + row_bytes;
        scanlines.extend(py_slice(raw, start, end));
        y++;
    }

    bytes ihdr = _u32be(width) + _u32be(height) + bytes(list<int64>{8, 2, 0, 0, 0});
    bytes idat = _zlib_deflate_store(bytes(scanlines));

    bytearray png_data = bytearray{};
    png_data.extend(py_bytes_lit("\x89PNG\r\n\x1a\n"));
    png_data.extend(_chunk(py_bytes_lit("IHDR"), ihdr));
    png_data.extend(_chunk(py_bytes_lit("IDAT"), idat));
    png_data.extend(_chunk(py_bytes_lit("IEND"), py_bytes_lit("")));

    pytra::runtime::cpp::base::PyFile f = open(path, "wb");
    {
        auto __finally_1 = py_make_scope_exit([&]() { f.close(); });
        f.write(png_data);
    }
}

}  // namespace

void write_rgb_png(const std::string& path, int width, int height, const std::vector<std::uint8_t>& pixels) {
    bytes buf(pixels.begin(), pixels.end());
    write_rgb_png_impl(str(path), int64(width), int64(height), buf);
}

}  // namespace pytra::pylib::png
