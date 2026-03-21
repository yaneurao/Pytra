#include "core/py_runtime.h"
#include "core/process_runtime.h"
#include "core/scope_exit.h"

/* PNG 書き出しユーティリティ（Python実行用）。

このモジュールは sample/py のスクリプトから利用し、
RGB 8bit バッファを PNG ファイルとして保存する。
 */

void _png_append_list(rc<list<int64>>& dst, const rc<list<int64>>& src) {
    int64 i = 0;
    int64 n = (rc_list_ref(src)).size();
    while (i < n) {
        rc_list_ref(dst).append(py_list_at_ref(rc_list_ref(src), i));
        i++;
    }
}

int64 _crc32(const rc<list<int64>>& data) {
    int64 crc = 0xFFFFFFFF;
    int64 poly = 0xEDB88320;
    for (int64 b : rc_list_ref(data)) {
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

int64 _adler32(const rc<list<int64>>& data) {
    int64 mod = 65521;
    int64 s1 = 1;
    int64 s2 = 0;
    for (int64 b : rc_list_ref(data)) {
        s1 += b;
        if (s1 >= mod)
            s1 -= mod;
        s2 += s1;
        s2 = s2 % mod;
    }
    return (s2 << 16 | s1) & 0xFFFFFFFF;
}

rc<list<int64>> _png_u16le(int64 v) {
    return rc_list_from_value(list<int64>{v & 0xFF, v >> 8 & 0xFF});
}

rc<list<int64>> _png_u32be(int64 v) {
    return rc_list_from_value(list<int64>{v >> 24 & 0xFF, v >> 16 & 0xFF, v >> 8 & 0xFF, v & 0xFF});
}

rc<list<int64>> _zlib_deflate_store(const rc<list<int64>>& data) {
    rc<list<int64>> out = rc_list_from_value(list<int64>{});
    _png_append_list(out, rc_list_from_value(list<int64>{0x78, 0x01}));
    int64 n = (rc_list_ref(data)).size();
    int64 pos = 0;
    while (pos < n) {
        int64 remain = n - pos;
        int64 chunk_len = (remain > 65535 ? 65535 : remain);
        int64 final = (pos + chunk_len >= n ? 1 : 0);
        rc_list_ref(out).append(final);
        _png_append_list(out, _png_u16le(chunk_len));
        _png_append_list(out, _png_u16le(0xFFFF ^ chunk_len));
        int64 i = pos;
        int64 end = pos + chunk_len;
        while (i < end) {
            rc_list_ref(out).append(py_list_at_ref(rc_list_ref(data), i));
            i++;
        }
        pos += chunk_len;
    }
    _png_append_list(out, _png_u32be(_adler32(data)));
    return out;
}

rc<list<int64>> _chunk(const rc<list<int64>>& chunk_type, const rc<list<int64>>& data) {
    rc<list<int64>> crc_input = rc_list_from_value(list<int64>{});
    _png_append_list(crc_input, chunk_type);
    _png_append_list(crc_input, data);
    int64 crc = _crc32(crc_input) & 0xFFFFFFFF;
    rc<list<int64>> out = rc_list_from_value(list<int64>{});
    _png_append_list(out, _png_u32be((rc_list_ref(data)).size()));
    _png_append_list(out, chunk_type);
    _png_append_list(out, data);
    _png_append_list(out, _png_u32be(crc));
    return out;
}

void write_rgb_png(const str& path, int64 width, int64 height, const bytes& pixels) {
    rc<list<int64>> raw = rc_list_from_value(list<int64>{});
    for (uint8 b : pixels) {
        rc_list_ref(raw).append(b);
    }
    int64 expected = width * height * 3;
    if ((rc_list_ref(raw)).size() != expected)
        throw ValueError("pixels length mismatch: got=" + ::std::to_string((rc_list_ref(raw)).size()) + " expected=" + ::std::to_string(expected));
    rc<list<int64>> scanlines = rc_list_from_value(list<int64>{});
    int64 row_bytes = width * 3;
    int64 y = 0;
    while (y < height) {
        rc_list_ref(scanlines).append(0);
        int64 start = y * row_bytes;
        int64 end = start + row_bytes;
        int64 i = start;
        while (i < end) {
            rc_list_ref(scanlines).append(py_list_at_ref(rc_list_ref(raw), i));
            i++;
        }
        y++;
    }
    rc<list<int64>> ihdr = rc_list_from_value(list<int64>{});
    _png_append_list(ihdr, _png_u32be(width));
    _png_append_list(ihdr, _png_u32be(height));
    _png_append_list(ihdr, rc_list_from_value(list<int64>{8, 2, 0, 0, 0}));
    rc<list<int64>> idat = _zlib_deflate_store(scanlines);
    
    rc<list<int64>> png = rc_list_from_value(list<int64>{});
    _png_append_list(png, rc_list_from_value(list<int64>{137, 80, 78, 71, 13, 10, 26, 10}));
    _png_append_list(png, _chunk(rc_list_from_value(list<int64>{73, 72, 68, 82}), ihdr));
    _png_append_list(png, _chunk(rc_list_from_value(list<int64>{73, 68, 65, 84}), idat));
    rc<list<int64>> iend_data = rc_list_from_value(list<int64>{});
    _png_append_list(png, _chunk(rc_list_from_value(list<int64>{73, 69, 78, 68}), iend_data));
    
    pytra::runtime::cpp::base::PyFile f = open(path, "wb");
    {
        auto __finally_1 = py_make_scope_exit([&]() {{
            f.close();
        });
        f.write(bytes(rc_list_copy_value(png)));
    }
}
