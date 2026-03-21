#include "core/py_runtime.h"
#include "core/process_runtime.h"
#include "core/scope_exit.h"

/* アニメーションGIFを書き出すための最小ヘルパー。 */

void _gif_append_list(rc<list<int64>>& dst, const rc<list<int64>>& src) {
    int64 i = 0;
    int64 n = (rc_list_ref(src)).size();
    while (i < n) {
        rc_list_ref(dst).append(py_list_at_ref(rc_list_ref(src), i));
        i++;
    }
}

rc<list<int64>> _gif_u16le(int64 v) {
    return rc_list_from_value(list<int64>{v & 0xFF, v >> 8 & 0xFF});
}

bytes _lzw_encode(const bytes& data, int64 min_code_size = 8) {
    if (data.size() == 0) {
        rc<list<int64>> empty = rc_list_from_value(list<int64>{});
        return bytes(rc_list_copy_value(empty));
    }
    int64 clear_code = 1 << min_code_size;
    int64 end_code = clear_code + 1;
    int64 code_size = min_code_size + 1;
    
    rc<list<int64>> out = rc_list_from_value(list<int64>{});
    int64 bit_buffer = 0;
    int64 bit_count = 0;
    
    bit_buffer |= clear_code << bit_count;
    bit_count += code_size;
    while (bit_count >= 8) {
        rc_list_ref(out).append(bit_buffer & 0xFF);
        bit_buffer = bit_buffer >> 8;
        bit_count -= 8;
    }
    code_size = min_code_size + 1;
    
    for (uint8 v : data) {
        bit_buffer |= v << bit_count;
        bit_count += code_size;
        while (bit_count >= 8) {
            rc_list_ref(out).append(bit_buffer & 0xFF);
            bit_buffer = bit_buffer >> 8;
            bit_count -= 8;
        }
        bit_buffer |= clear_code << bit_count;
        bit_count += code_size;
        while (bit_count >= 8) {
            rc_list_ref(out).append(bit_buffer & 0xFF);
            bit_buffer = bit_buffer >> 8;
            bit_count -= 8;
        }
        code_size = min_code_size + 1;
    }
    bit_buffer |= end_code << bit_count;
    bit_count += code_size;
    while (bit_count >= 8) {
        rc_list_ref(out).append(bit_buffer & 0xFF);
        bit_buffer = bit_buffer >> 8;
        bit_count -= 8;
    }
    if (bit_count > 0)
        rc_list_ref(out).append(bit_buffer & 0xFF);
    return bytes(rc_list_copy_value(out));
}

bytes grayscale_palette() {
    rc<list<int64>> p = rc_list_from_value(list<int64>{});
    int64 i = 0;
    while (i < 256) {
        rc_list_ref(p).append(i);
        rc_list_ref(p).append(i);
        rc_list_ref(p).append(i);
        i++;
    }
    return bytes(rc_list_copy_value(p));
}

void save_gif(const str& path, int64 width, int64 height, const list<bytes>& frames, const bytes& palette, int64 delay_cs = 4, int64 loop = 0) {
    if (palette.size() != 256 * 3)
        throw ValueError("palette must be 256*3 bytes");
    rc<list<list<int64>>> frame_lists = rc_list_from_value(list<list<int64>>{});
    for (bytes fr : frames) {
        rc<list<int64>> fr_list = rc_list_from_value(list<int64>{});
        for (uint8 v : fr) {
            rc_list_ref(fr_list).append(v);
        }
        if ((rc_list_ref(fr_list)).size() != width * height)
            throw ValueError("frame size mismatch");
        rc_list_ref(frame_lists).append(rc_list_copy_value(fr_list));
    }
    rc<list<int64>> palette_list = rc_list_from_value(list<int64>{});
    for (uint8 v : palette) {
        rc_list_ref(palette_list).append(v);
    }
    rc<list<int64>> out = rc_list_from_value(list<int64>{});
    _gif_append_list(out, rc_list_from_value(list<int64>{71, 73, 70, 56, 57, 97}));
    _gif_append_list(out, _gif_u16le(width));
    _gif_append_list(out, _gif_u16le(height));
    rc_list_ref(out).append(0xF7);
    rc_list_ref(out).append(0);
    rc_list_ref(out).append(0);
    _gif_append_list(out, palette_list);
    
    _gif_append_list(out, rc_list_from_value(list<int64>{0x21, 0xFF, 0x0B, 78, 69, 84, 83, 67, 65, 80, 69, 50, 46, 48, 0x03, 0x01}));
    _gif_append_list(out, _gif_u16le(loop));
    rc_list_ref(out).append(0);
    
    for (list<int64> fr_list : rc_list_ref(frame_lists)) {
        _gif_append_list(out, rc_list_from_value(list<int64>{0x21, 0xF9, 0x04, 0x00}));
        _gif_append_list(out, _gif_u16le(delay_cs));
        _gif_append_list(out, rc_list_from_value(list<int64>{0x00, 0x00}));
        
        rc_list_ref(out).append(0x2C);
        _gif_append_list(out, _gif_u16le(0));
        _gif_append_list(out, _gif_u16le(0));
        _gif_append_list(out, _gif_u16le(width));
        _gif_append_list(out, _gif_u16le(height));
        rc_list_ref(out).append(0);
        rc_list_ref(out).append(8);
        bytes compressed = _lzw_encode(bytes(fr_list), 8);
        int64 pos = 0;
        while (pos < compressed.size()) {
            int64 remain = compressed.size() - pos;
            int64 chunk_len = (remain > 255 ? 255 : remain);
            rc_list_ref(out).append(chunk_len);
            int64 i = 0;
            while (i < chunk_len) {
                rc_list_ref(out).append(compressed[pos + i]);
                i++;
            }
            pos += chunk_len;
        }
        rc_list_ref(out).append(0);
    }
    rc_list_ref(out).append(0x3B);
    
    pytra::runtime::cpp::base::PyFile f = open(path, "wb");
    {
        auto __finally_1 = py_make_scope_exit([&]() {{
            f.close();
        });
        f.write(bytes(rc_list_copy_value(out)));
    }
}
