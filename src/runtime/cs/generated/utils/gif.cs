// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: tools/gen_runtime_from_manifest.py

using System;
using System.Collections.Generic;
using System.Linq;
using Any = System.Object;
using int64 = System.Int64;
using float64 = System.Double;
using str = System.String;

namespace Pytra.CsModule
{
    public static class gif_helper
    {
        public static void _gif_append_list(System.Collections.Generic.List<int64> dst, System.Collections.Generic.List<int64> src)
        {
            int64 i = 0;
            int64 n = (src).Count;
            while ((i) < (n)) {
                dst.Add(Pytra.CsModule.py_runtime.py_get(src, i));
                i += 1;
            }
        }

        public static System.Collections.Generic.List<int64> _gif_u16le(int64 v)
        {
            return new System.Collections.Generic.List<int64> { v & 0xFF, v >> System.Convert.ToInt32(8) & 0xFF };
        }

        public static bytes _lzw_encode(bytes data, int64 min_code_size = 8)
        {
            if (((data).Count) == (0)) {
                return Pytra.CsModule.py_runtime.py_bytes(new System.Collections.Generic.List<object>());
            }
            int64 clear_code = 1 << System.Convert.ToInt32(min_code_size);
            int64 end_code = clear_code + 1;
            int64 code_size = min_code_size + 1;

            System.Collections.Generic.List<int64> py_out = new System.Collections.Generic.List<int64>();
            int64 bit_buffer = 0;
            int64 bit_count = 0;

            bit_buffer |= clear_code << System.Convert.ToInt32(bit_count);
            bit_count += code_size;
            while ((bit_count) >= (8)) {
                py_out.Add(bit_buffer & 0xFF);
                bit_buffer = bit_buffer >> System.Convert.ToInt32(8);
                bit_count -= 8;
            }
            code_size = min_code_size + 1;

            foreach (var v in data) {
                bit_buffer |= System.Convert.ToInt64(v << System.Convert.ToInt32(bit_count));
                bit_count += code_size;
                while ((bit_count) >= (8)) {
                    py_out.Add(bit_buffer & 0xFF);
                    bit_buffer = bit_buffer >> System.Convert.ToInt32(8);
                    bit_count -= 8;
                }
                bit_buffer |= clear_code << System.Convert.ToInt32(bit_count);
                bit_count += code_size;
                while ((bit_count) >= (8)) {
                    py_out.Add(bit_buffer & 0xFF);
                    bit_buffer = bit_buffer >> System.Convert.ToInt32(8);
                    bit_count -= 8;
                }
                code_size = min_code_size + 1;
            }
            bit_buffer |= end_code << System.Convert.ToInt32(bit_count);
            bit_count += code_size;
            while ((bit_count) >= (8)) {
                py_out.Add(bit_buffer & 0xFF);
                bit_buffer = bit_buffer >> System.Convert.ToInt32(8);
                bit_count -= 8;
            }
            if ((bit_count) > (0)) {
                py_out.Add(bit_buffer & 0xFF);
            }
            return Pytra.CsModule.py_runtime.py_bytes(py_out);
        }

        public static bytes grayscale_palette()
        {
            System.Collections.Generic.List<int64> p = new System.Collections.Generic.List<int64>();
            int64 i = 0;
            while ((i) < (256)) {
                p.Add(i);
                p.Add(i);
                p.Add(i);
                i += 1;
            }
            return Pytra.CsModule.py_runtime.py_bytes(p);
        }

        public static void save_gif(str path, int64 width, int64 height, System.Collections.Generic.List<bytes> frames, bytes palette, int64 delay_cs = 4, int64 loop = 0)
        {
            if (((palette).Count) != (256 * 3)) {
                throw new System.Exception("palette must be 256*3 bytes");
            }
            System.Collections.Generic.List<System.Collections.Generic.List<int64>> frame_lists = new System.Collections.Generic.List<System.Collections.Generic.List<int64>>();
            foreach (var fr in frames) {
                System.Collections.Generic.List<int64> fr_list = new System.Collections.Generic.List<int64>();
                foreach (var v in fr) {
                    fr_list.Add(Pytra.CsModule.py_runtime.py_int(v));
                }
                if (((fr_list).Count) != (width * height)) {
                    throw new System.Exception("frame size mismatch");
                }
                frame_lists.Add(fr_list);
            }
            System.Collections.Generic.List<int64> palette_list = new System.Collections.Generic.List<int64>();
            foreach (var v in palette) {
                palette_list.Add(Pytra.CsModule.py_runtime.py_int(v));
            }
            System.Collections.Generic.List<int64> py_out = new System.Collections.Generic.List<int64>();
            _gif_append_list(py_out, new System.Collections.Generic.List<int64> { 71, 73, 70, 56, 57, 97 });
            _gif_append_list(py_out, _gif_u16le(width));
            _gif_append_list(py_out, _gif_u16le(height));
            py_out.Add(0xF7);
            py_out.Add(0);
            py_out.Add(0);
            _gif_append_list(py_out, palette_list);

            _gif_append_list(py_out, new System.Collections.Generic.List<int64> { 0x21, 0xFF, 0x0B, 78, 69, 84, 83, 67, 65, 80, 69, 50, 46, 48, 0x03, 0x01 });
            _gif_append_list(py_out, _gif_u16le(loop));
            py_out.Add(0);

            foreach (var fr_list in frame_lists) {
                _gif_append_list(py_out, new System.Collections.Generic.List<int64> { 0x21, 0xF9, 0x04, 0x00 });
                _gif_append_list(py_out, _gif_u16le(delay_cs));
                _gif_append_list(py_out, new System.Collections.Generic.List<int64> { 0x00, 0x00 });

                py_out.Add(0x2C);
                _gif_append_list(py_out, _gif_u16le(0));
                _gif_append_list(py_out, _gif_u16le(0));
                _gif_append_list(py_out, _gif_u16le(width));
                _gif_append_list(py_out, _gif_u16le(height));
                py_out.Add(0);
                py_out.Add(8);
                bytes compressed = _lzw_encode(Pytra.CsModule.py_runtime.py_bytes(fr_list), 8);
                int64 pos = 0;
                while ((pos) < ((compressed).Count)) {
                    int64 remain = (compressed).Count - pos;
                    int64 chunk_len = ((remain) > (255) ? 255 : remain);
                    py_out.Add(chunk_len);
                    int64 i = 0;
                    while ((i) < (chunk_len)) {
                        py_out.Add(Pytra.CsModule.py_runtime.py_get(compressed, pos + i));
                        i += 1;
                    }
                    pos += chunk_len;
                }
                py_out.Add(0);
            }
            py_out.Add(0x3B);

            PyFile f = Pytra.CsModule.py_runtime.open(path, "wb");
            try
            {
                f.write(Pytra.CsModule.py_runtime.py_bytes(py_out));
            } finally {
                f.close();
            }
        }

    }
}
