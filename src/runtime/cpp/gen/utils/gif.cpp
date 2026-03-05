// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/gen/utils/gif.h"


namespace pytra::utils::gif {

    void _gif_append_list(list<int64>& dst, const list<int64>& src) {
        int64 i = 0;
        int64 n = py_len(src);
        while (i < n) {
            dst.append(int64(src[i]));
            i++;
        }
    }
    
    list<int64> _gif_u16le(int64 v) {
        return list<int64>{v & 0xFF, v >> 8 & 0xFF};
    }
    
    bytes _lzw_encode(const bytes& data, int64 min_code_size = 8) {
        if (py_len(data) == 0)
            return bytes(make_object(list<object>{}));
        int64 clear_code = 1 << min_code_size;
        int64 end_code = clear_code + 1;
        int64 code_size = min_code_size + 1;
        
        list<int64> out = {};
        int64 bit_buffer = 0;
        int64 bit_count = 0;
        
        bit_buffer |= clear_code << bit_count;
        bit_count += code_size;
        while (bit_count >= 8) {
            out.append(int64(bit_buffer & 0xFF));
            bit_buffer = bit_buffer >> 8;
            bit_count -= 8;
        }
        code_size = min_code_size + 1;
        
        for (uint8 v : data) {
            bit_buffer |= v << bit_count;
            bit_count += code_size;
            while (bit_count >= 8) {
                out.append(int64(bit_buffer & 0xFF));
                bit_buffer = bit_buffer >> 8;
                bit_count -= 8;
            }
            bit_buffer |= clear_code << bit_count;
            bit_count += code_size;
            while (bit_count >= 8) {
                out.append(int64(bit_buffer & 0xFF));
                bit_buffer = bit_buffer >> 8;
                bit_count -= 8;
            }
            code_size = min_code_size + 1;
        }
        bit_buffer |= end_code << bit_count;
        bit_count += code_size;
        while (bit_count >= 8) {
            out.append(int64(bit_buffer & 0xFF));
            bit_buffer = bit_buffer >> 8;
            bit_count -= 8;
        }
        if (bit_count > 0)
            out.append(int64(bit_buffer & 0xFF));
        return bytes(out);
    }
    
    bytes grayscale_palette() {
        list<int64> p = {};
        int64 i = 0;
        while (i < 256) {
            p.append(i);
            p.append(i);
            p.append(i);
            i++;
        }
        return bytes(p);
    }
    
    void save_gif(const str& path, int64 width, int64 height, const list<bytes>& frames, const bytes& palette, int64 delay_cs = 4, int64 loop = 0) {
        if (py_len(palette) != 256 * 3)
            throw ValueError("palette must be 256*3 bytes");
        list<list<int64>> frame_lists = {};
        for (object __itobj_1 : py_dyn_range(frames)) {
            bytes fr = __itobj_1;
            list<int64> fr_list = {};
            for (uint8 v : fr) {
                fr_list.append(int64(int64(v)));
            }
            if (py_len(fr_list) != width * height)
                throw ValueError("frame size mismatch");
            frame_lists.append(list<int64>(fr_list));
        }
        list<int64> palette_list = {};
        for (uint8 v : palette) {
            palette_list.append(int64(int64(v)));
        }
        list<int64> out = {};
        _gif_append_list(out, list<int64>{71, 73, 70, 56, 57, 97});
        _gif_append_list(out, _gif_u16le(width));
        _gif_append_list(out, _gif_u16le(height));
        out.append(int64(0xF7));
        out.append(int64(0));
        out.append(int64(0));
        _gif_append_list(out, palette_list);
        
        _gif_append_list(out, list<int64>{0x21, 0xFF, 0x0B, 78, 69, 84, 83, 67, 65, 80, 69, 50, 46, 48, 0x03, 0x01});
        _gif_append_list(out, _gif_u16le(loop));
        out.append(int64(0));
        
        for (list<int64> fr_list : frame_lists) {
            _gif_append_list(out, list<int64>{0x21, 0xF9, 0x04, 0x00});
            _gif_append_list(out, _gif_u16le(delay_cs));
            _gif_append_list(out, list<int64>{0x00, 0x00});
            
            out.append(int64(0x2C));
            _gif_append_list(out, _gif_u16le(0));
            _gif_append_list(out, _gif_u16le(0));
            _gif_append_list(out, _gif_u16le(width));
            _gif_append_list(out, _gif_u16le(height));
            out.append(int64(0));
            out.append(int64(8));
            bytes compressed = _lzw_encode(bytes(fr_list), 8);
            int64 pos = 0;
            while (pos < py_len(compressed)) {
                int64 remain = py_len(compressed) - pos;
                int64 chunk_len = (remain > 255 ? 255 : remain);
                out.append(chunk_len);
                int64 i = 0;
                while (i < chunk_len) {
                    out.append(int64(compressed[pos + i]));
                    i++;
                }
                pos += chunk_len;
            }
            out.append(int64(0));
        }
        out.append(int64(0x3B));
        
        pytra::runtime::cpp::base::PyFile f = open(path, "wb");
        {
            auto __finally_2 = py_make_scope_exit([&]() {
                f.close();
            });
            f.write(bytes(out));
        }
    }
    
    static void __pytra_module_init() {
        static bool __initialized = false;
        if (__initialized) return;
        __initialized = true;
        /* アニメーションGIFを書き出すための最小ヘルパー。 */
    }
    
}  // namespace pytra::utils::gif
