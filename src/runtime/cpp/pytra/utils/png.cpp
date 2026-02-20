#include "runtime/cpp/pytra/built_in/py_runtime.h"


namespace pytra::utils::png {

    /* PNG 書き出しユーティリティ（Python実行用）。

このモジュールは sample/py のスクリプトから利用し、
RGB 8bit バッファを PNG ファイルとして保存する。
 */
    
    
    int64 _crc32(const bytes& data) {
        /* PNG chunk CRC32 を pure Python で計算する。 */
        int64 crc = 0xFFFFFFFF;
        int64 poly = 0xEDB88320;
        for (uint8 b : data) {
            crc ^= b;
            int64 i = 0;
            while (i < 8) {
                if (crc & 1 != 0)
                    crc = crc >> 1 ^ poly;
                else
                    crc >>= 1;
                i++;
            }
        }
        return crc ^ 0xFFFFFFFF;
    }
    
    int64 _adler32(const bytes& data) {
        /* zlib wrapper 用 Adler-32 を pure Python で計算する。 */
        int64 mod = 65521;
        int64 s1 = 1;
        int64 s2 = 0;
        for (uint8 b : data) {
            s1 += b;
            if (s1 >= mod)
                s1 -= mod;
            s2 += s1;
            s2 %= mod;
        }
        return (s2 << 16 | s1) & 0xFFFFFFFF;
    }
    
    bytes _u16le(int64 v) {
        return bytes(list<int64>{v & 0xFF, v >> 8 & 0xFF});
    }
    
    bytes _u32be(int64 v) {
        return bytes(list<int64>{v >> 24 & 0xFF, v >> 16 & 0xFF, v >> 8 & 0xFF, v & 0xFF});
    }
    
    bytes _zlib_deflate_store(const bytes& data) {
        /* 非圧縮 DEFLATE(stored block) を使って zlib ストリームを作る。 */
        bytearray out = bytearray{};
        // zlib header: CMF=0x78(Deflate, 32K window), FLG=0x01(check bits OK, fastest)
        out.extend(py_bytes_lit("\x78\x01"));
        int64 n = py_len(data);
        int64 pos = 0;
        while (pos < n) {
            int64 remain = n - pos;
            int64 chunk_len = (remain > 65535 ? 65535 : remain);
            int64 final = (pos + chunk_len >= n ? 1 : 0);
            // stored block: BTYPE=00, header bit field in LSB order (final in bit0)
            out.append(static_cast<uint8>(py_to_int64(final)));
            out.extend(_u16le(chunk_len));
            out.extend(_u16le(0xFFFF ^ chunk_len));
            out.extend(py_slice(data, pos, pos + chunk_len));
            pos += chunk_len;
        }
        out.extend(_u32be(_adler32(data)));
        return bytes(out);
    }
    
    bytes _chunk(const bytes& chunk_type, const bytes& data) {
        bytes length = _u32be(py_len(data));
        int64 crc = _crc32(chunk_type + data) & 0xFFFFFFFF;
        return length + chunk_type + data + _u32be(crc);
    }
    
    void write_rgb_png(const str& path, int64 width, int64 height, const bytes& pixels) {
        /* RGBバッファを PNG として保存する。

    Args:
        path: 出力PNGファイルパス。
        width: 画像幅（pixel）。
        height: 画像高さ（pixel）。
        pixels: 長さ width*height*3 の RGB バイト列。
     */
        bytes raw = bytes(pixels);
        int64 expected = width * height * 3;
        if (py_len(raw) != expected)
            throw ValueError("pixels length mismatch: got=" + ::std::to_string(py_len(raw)) + " expected=" + ::std::to_string(expected));
        
        bytearray scanlines = bytearray{};
        int64 row_bytes = width * 3;
        int64 y = 0;
        while (y < height) {
            scanlines.append(static_cast<uint8>(py_to_int64(0)));
            int64 start = y * row_bytes;
            int64 end = start + row_bytes;
            scanlines.extend(py_slice(raw, start, end));
            y++;
        }
        
        bytes ihdr = _u32be(width) + _u32be(height) + bytes(list<int64>{8, 2, 0, 0, 0});
        bytes idat = _zlib_deflate_store(bytes(scanlines));
        
        bytearray png = bytearray{};
        png.extend(py_bytes_lit("\x89PNG\r\n\x1a\n"));
        png.extend(_chunk(py_bytes_lit("IHDR"), ihdr));
        png.extend(_chunk(py_bytes_lit("IDAT"), idat));
        png.extend(_chunk(py_bytes_lit("IEND"), py_bytes_lit("")));
        
        pytra::runtime::cpp::base::PyFile f = open(path, "wb");
        {
            auto __finally_1 = py_make_scope_exit([&]() {
                f.close();
            });
            f.write(png);
        }
    }
    
}  // namespace pytra::utils::png
