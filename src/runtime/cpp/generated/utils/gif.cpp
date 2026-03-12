// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/native/core/py_runtime.h"

#include "runtime/cpp/generated/utils/gif.h"
#include "runtime/cpp/native/core/process_runtime.h"
#include "runtime/cpp/native/core/scope_exit.h"


namespace pytra::utils::gif {

    /* アニメーションGIFを書き出すための最小ヘルパー。 */
    
    void _gif_append_list(rc<list<int64>>& dst, const rc<list<int64>>& src) {
        int64 i = 0;
        int64 n = py_len(src);
        while (i < n) {
            py_list_append_mut(rc_list_ref(dst), py_at(src, py_to<int64>(i)));
            i++;
        }
    }
    
    rc<list<int64>> _gif_u16le(int64 v) {
        return rc_list_from_value(list<int64>{v & 0xFF, v >> 8 & 0xFF});
    }
    
    bytes _lzw_encode(const bytes& data, int64 min_code_size) {
        if (py_len(data) == 0)
            return bytes(make_object(list<object>{}));
        int64 clear_code = 1 << min_code_size;
        int64 end_code = clear_code + 1;
        int64 code_size = min_code_size + 1;
        
        rc<list<int64>> out = rc_list_from_value(list<int64>{});
        int64 bit_buffer = 0;
        int64 bit_count = 0;
        
        bit_buffer |= clear_code << bit_count;
        bit_count += code_size;
        while (bit_count >= 8) {
            py_list_append_mut(rc_list_ref(out), bit_buffer & 0xFF);
            bit_buffer = bit_buffer >> 8;
            bit_count -= 8;
        }
        code_size = min_code_size + 1;
        
        for (uint8 v : data) {
            bit_buffer |= v << bit_count;
            bit_count += code_size;
            while (bit_count >= 8) {
                py_list_append_mut(rc_list_ref(out), bit_buffer & 0xFF);
                bit_buffer = bit_buffer >> 8;
                bit_count -= 8;
            }
            bit_buffer |= clear_code << bit_count;
            bit_count += code_size;
            while (bit_count >= 8) {
                py_list_append_mut(rc_list_ref(out), bit_buffer & 0xFF);
                bit_buffer = bit_buffer >> 8;
                bit_count -= 8;
            }
            code_size = min_code_size + 1;
        }
        bit_buffer |= end_code << bit_count;
        bit_count += code_size;
        while (bit_count >= 8) {
            py_list_append_mut(rc_list_ref(out), bit_buffer & 0xFF);
            bit_buffer = bit_buffer >> 8;
            bit_count -= 8;
        }
        if (bit_count > 0)
            py_list_append_mut(rc_list_ref(out), bit_buffer & 0xFF);
        return bytes(rc_list_copy_value(out));
    }
    
    bytes grayscale_palette() {
        rc<list<int64>> p = rc_list_from_value(list<int64>{});
        int64 i = 0;
        while (i < 256) {
            py_list_append_mut(rc_list_ref(p), i);
            py_list_append_mut(rc_list_ref(p), i);
            py_list_append_mut(rc_list_ref(p), i);
            i++;
        }
        return bytes(rc_list_copy_value(p));
    }
    
    void save_gif(const str& path, int64 width, int64 height, const list<bytes>& frames, const bytes& palette, int64 delay_cs, int64 loop) {
        if (py_len(palette) != 256 * 3)
            throw ValueError("palette must be 256*3 bytes");
        rc<list<list<int64>>> frame_lists = rc_list_from_value(list<list<int64>>{});
        for (bytes fr : frames) {
            rc<list<int64>> fr_list = rc_list_from_value(list<int64>{});
            for (uint8 v : fr) {
                py_list_append_mut(rc_list_ref(fr_list), int64(v));
            }
            if (py_len(fr_list) != width * height)
                throw ValueError("frame size mismatch");
            py_list_append_mut(rc_list_ref(frame_lists), rc_list_copy_value(fr_list));
        }
        rc<list<int64>> palette_list = rc_list_from_value(list<int64>{});
        for (uint8 v : palette) {
            py_list_append_mut(rc_list_ref(palette_list), int64(v));
        }
        rc<list<int64>> out = rc_list_from_value(list<int64>{});
        _gif_append_list(out, rc_list_from_value(list<int64>{71, 73, 70, 56, 57, 97}));
        _gif_append_list(out, _gif_u16le(width));
        _gif_append_list(out, _gif_u16le(height));
        py_list_append_mut(rc_list_ref(out), 0xF7);
        py_list_append_mut(rc_list_ref(out), 0);
        py_list_append_mut(rc_list_ref(out), 0);
        _gif_append_list(out, palette_list);
        
        _gif_append_list(out, rc_list_from_value(list<int64>{0x21, 0xFF, 0x0B, 78, 69, 84, 83, 67, 65, 80, 69, 50, 46, 48, 0x03, 0x01}));
        _gif_append_list(out, _gif_u16le(loop));
        py_list_append_mut(rc_list_ref(out), 0);
        
        for (list<int64> fr_list : rc_list_ref(frame_lists)) {
            _gif_append_list(out, rc_list_from_value(list<int64>{0x21, 0xF9, 0x04, 0x00}));
            _gif_append_list(out, _gif_u16le(delay_cs));
            _gif_append_list(out, rc_list_from_value(list<int64>{0x00, 0x00}));
            
            py_list_append_mut(rc_list_ref(out), 0x2C);
            _gif_append_list(out, _gif_u16le(0));
            _gif_append_list(out, _gif_u16le(0));
            _gif_append_list(out, _gif_u16le(width));
            _gif_append_list(out, _gif_u16le(height));
            py_list_append_mut(rc_list_ref(out), 0);
            py_list_append_mut(rc_list_ref(out), 8);
            bytes compressed = _lzw_encode(bytes(fr_list), 8);
            int64 pos = 0;
            while (pos < py_len(compressed)) {
                int64 remain = py_len(compressed) - pos;
                int64 chunk_len = (remain > 255 ? 255 : remain);
                py_list_append_mut(rc_list_ref(out), chunk_len);
                int64 i = 0;
                while (i < chunk_len) {
                    py_list_append_mut(rc_list_ref(out), compressed[pos + i]);
                    i++;
                }
                pos += chunk_len;
            }
            py_list_append_mut(rc_list_ref(out), 0);
        }
        py_list_append_mut(rc_list_ref(out), 0x3B);
        
        pytra::runtime::cpp::base::PyFile f = open(path, "wb");
        {
            auto __finally_1 = py_make_scope_exit([&]() {
                f.close();
            });
            f.write(bytes(rc_list_copy_value(out)));
        }
    }
    
}  // namespace pytra::utils::gif
