// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: src/py2cpp.py

#include "runtime/cpp/pytra/built_in/py_runtime.h"


namespace pytra::utils::gif {

    /* アニメーションGIFを書き出すための最小ヘルパー。 */
    
    
    bytes _lzw_encode(const bytes& data, int64 min_code_size) {
        /* GIF用LZW圧縮を実行する（互換性重視: Clear+Literal方式）。 */
        if (data.empty())
            return py_bytes_lit("");
        
        int64 clear_code = 1 << min_code_size;
        int64 end_code = clear_code + 1;
        
        int64 code_size = min_code_size + 1;
        
        bytearray out = bytearray{};
        int64 bit_buffer = 0;
        int64 bit_count = 0;
        
        bit_buffer |= clear_code << bit_count;
        bit_count += code_size;
        while (bit_count >= 8) {
            out.append(static_cast<uint8>(bit_buffer & 0xFF));
            bit_buffer >>= 8;
            bit_count -= 8;
        }
        code_size = min_code_size + 1;
        
        for (uint8 v : data) {
            bit_buffer |= static_cast<int64>(v) << bit_count;
            bit_count += code_size;
            while (bit_count >= 8) {
                out.append(static_cast<uint8>(bit_buffer & 0xFF));
                bit_buffer >>= 8;
                bit_count -= 8;
            }
            
            bit_buffer |= clear_code << bit_count;
            bit_count += code_size;
            while (bit_count >= 8) {
                out.append(static_cast<uint8>(bit_buffer & 0xFF));
                bit_buffer >>= 8;
                bit_count -= 8;
            }
            
            code_size = min_code_size + 1;
        }
        
        bit_buffer |= end_code << bit_count;
        bit_count += code_size;
        while (bit_count >= 8) {
            out.append(static_cast<uint8>(bit_buffer & 0xFF));
            bit_buffer >>= 8;
            bit_count -= 8;
        }
        
        if (bit_count > 0)
            out.append(static_cast<uint8>(bit_buffer & 0xFF));
        
        return bytes(out);
    }
    
    bytes grayscale_palette() {
        /* 0..255のグレースケールパレットを返す。 */
        bytearray p = bytearray{};
        p.reserve(256 * 3);
        int64 i = 0;
        while (i < 256) {
            p.append(static_cast<uint8>(i));
            p.append(static_cast<uint8>(i));
            p.append(static_cast<uint8>(i));
            i++;
        }
        return bytes(p);
    }
    
    void save_gif(const str& path, int64 width, int64 height, const list<bytes>& frames, const bytes& palette, int64 delay_cs, int64 loop) {
        /* インデックスカラーのフレーム列をアニメーションGIFとして保存する。 */
        if (palette.size() != static_cast<::std::size_t>(256 * 3))
            throw ValueError("palette must be 256*3 bytes");
        
        const int64 expected_frame_size = width * height;
        for (const bytes& fr : frames) {
            if (fr.size() != static_cast<::std::size_t>(expected_frame_size))
                throw ValueError("frame size mismatch");
        }
        
        bytearray out = bytearray{};
        out.extend(py_bytes_lit("GIF89a"));
        out.extend(py_int_to_bytes(width, 2, "little"));
        out.extend(py_int_to_bytes(height, 2, "little"));
        out.append(static_cast<uint8>(0xF7));
        out.append(static_cast<uint8>(0));
        out.append(static_cast<uint8>(0));
        out.extend(palette);
        
        // Netscape loop extension
        out.extend(py_bytes_lit("\x21\xFF\x0BNETSCAPE2.0\x03\x01"));
        out.extend(py_int_to_bytes(loop, 2, "little"));
        out.append(static_cast<uint8>(0));
        
        for (const bytes& fr : frames) {
            out.extend(py_bytes_lit("\x21\xF9\x04\x00"));
            out.extend(py_int_to_bytes(delay_cs, 2, "little"));
            out.extend(py_bytes_lit("\x00\x00"));
            
            out.append(static_cast<uint8>(0x2C));
            out.extend(py_int_to_bytes((0), 2, "little"));
            out.extend(py_int_to_bytes((0), 2, "little"));
            out.extend(py_int_to_bytes(width, 2, "little"));
            out.extend(py_int_to_bytes(height, 2, "little"));
            out.append(static_cast<uint8>(0));
            
            out.append(static_cast<uint8>(8));
            bytes compressed = _lzw_encode(fr, 8);
            int64 pos = 0;
            const int64 compressed_n = static_cast<int64>(compressed.size());
            while (pos < compressed_n) {
                int64 remain = compressed_n - pos;
                int64 chunk_len = (remain > 255 ? 255 : remain);
                out.append(static_cast<uint8>(chunk_len));
                auto chunk_begin = compressed.begin() + static_cast<::std::size_t>(pos);
                auto chunk_end = chunk_begin + static_cast<::std::size_t>(chunk_len);
                out.insert(out.end(), chunk_begin, chunk_end);
                pos += chunk_len;
            }
            out.append(static_cast<uint8>(0));
        }
        
        out.append(static_cast<uint8>(0x3B));
        
        pytra::runtime::cpp::base::PyFile f = open(path, "wb");
        {
            auto __finally_1 = py_make_scope_exit([&]() {
                f.close();
            });
            f.write(out);
        }
    }
    
}  // namespace pytra::utils::gif
