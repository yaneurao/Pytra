// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: tools/gen_cs_image_runtime_from_canonical.py

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
        public static List<byte> _lzw_encode(List<byte> data, long min_code_size = 8)
        {
            if (((data).Count) == (0)) {
                return new System.Collections.Generic.List<byte> {  };
            }
            long clear_code = 1 << System.Convert.ToInt32(min_code_size);
            long end_code = clear_code + 1;

            long code_size = min_code_size + 1;

            List<byte> py_out = new System.Collections.Generic.List<byte>();
            long bit_buffer = 0;
            long bit_count = 0;

            bit_buffer |= clear_code << System.Convert.ToInt32(bit_count);
            bit_count += code_size;
            while ((bit_count) >= (8)) {
                Pytra.CsModule.py_runtime.py_append(py_out, bit_buffer & 0xFF);
                bit_buffer >>= 8;
                bit_count -= 8;
            }
            code_size = min_code_size + 1;

            foreach (var v in data) {
                bit_buffer |= System.Convert.ToInt64(v << System.Convert.ToInt32(bit_count));
                bit_count += code_size;
                while ((bit_count) >= (8)) {
                    Pytra.CsModule.py_runtime.py_append(py_out, bit_buffer & 0xFF);
                    bit_buffer >>= 8;
                    bit_count -= 8;
                }
                bit_buffer |= clear_code << System.Convert.ToInt32(bit_count);
                bit_count += code_size;
                while ((bit_count) >= (8)) {
                    Pytra.CsModule.py_runtime.py_append(py_out, bit_buffer & 0xFF);
                    bit_buffer >>= 8;
                    bit_count -= 8;
                }
                code_size = min_code_size + 1;
            }
            bit_buffer |= end_code << System.Convert.ToInt32(bit_count);
            bit_count += code_size;
            while ((bit_count) >= (8)) {
                Pytra.CsModule.py_runtime.py_append(py_out, bit_buffer & 0xFF);
                bit_buffer >>= 8;
                bit_count -= 8;
            }
            if ((bit_count) > (0)) {
                Pytra.CsModule.py_runtime.py_append(py_out, bit_buffer & 0xFF);
            }
            return Pytra.CsModule.py_runtime.py_bytes(py_out);
        }

        public static List<byte> grayscale_palette()
        {
            List<byte> p = new System.Collections.Generic.List<byte>();
            long i = 0;
            while ((i) < (256)) {
                Pytra.CsModule.py_runtime.py_append(p, i);
                Pytra.CsModule.py_runtime.py_append(p, i);
                Pytra.CsModule.py_runtime.py_append(p, i);
                i += 1;
            }
            return Pytra.CsModule.py_runtime.py_bytes(p);
        }

        public static void save_gif(string path, long width, long height, System.Collections.Generic.List<List<byte>> frames, List<byte> palette, long delay_cs = 4, long loop = 0)
        {
            if (((palette).Count) != (256 * 3)) {
                throw new System.Exception("palette must be 256*3 bytes");
            }
            foreach (var fr in frames) {
                if (((fr).Count) != (width * height)) {
                    throw new System.Exception("frame size mismatch");
                }
            }
            List<byte> py_out = new System.Collections.Generic.List<byte>();
            py_out.AddRange(new System.Collections.Generic.List<byte> { (byte)71, (byte)73, (byte)70, (byte)56, (byte)57, (byte)97 });
            py_out.AddRange(Pytra.CsModule.py_runtime.py_int_to_bytes(width, System.Convert.ToInt32(2), "little"));
            py_out.AddRange(Pytra.CsModule.py_runtime.py_int_to_bytes(height, System.Convert.ToInt32(2), "little"));
            Pytra.CsModule.py_runtime.py_append(py_out, 0xF7);
            Pytra.CsModule.py_runtime.py_append(py_out, 0);
            Pytra.CsModule.py_runtime.py_append(py_out, 0);
            py_out.AddRange(palette);

            // Netscape loop extension
            py_out.AddRange(new System.Collections.Generic.List<byte> { (byte)33, (byte)255, (byte)11, (byte)78, (byte)69, (byte)84, (byte)83, (byte)67, (byte)65, (byte)80, (byte)69, (byte)50, (byte)46, (byte)48, (byte)3, (byte)1 });
            py_out.AddRange(Pytra.CsModule.py_runtime.py_int_to_bytes(loop, System.Convert.ToInt32(2), "little"));
            Pytra.CsModule.py_runtime.py_append(py_out, 0);

            foreach (var fr in frames) {
                py_out.AddRange(new System.Collections.Generic.List<byte> { (byte)33, (byte)249, (byte)4, (byte)0 });
                py_out.AddRange(Pytra.CsModule.py_runtime.py_int_to_bytes(delay_cs, System.Convert.ToInt32(2), "little"));
                py_out.AddRange(new System.Collections.Generic.List<byte> { (byte)0, (byte)0 });

                Pytra.CsModule.py_runtime.py_append(py_out, 0x2C);
                py_out.AddRange(Pytra.CsModule.py_runtime.py_int_to_bytes((0), System.Convert.ToInt32(2), "little"));
                py_out.AddRange(Pytra.CsModule.py_runtime.py_int_to_bytes((0), System.Convert.ToInt32(2), "little"));
                py_out.AddRange(Pytra.CsModule.py_runtime.py_int_to_bytes(width, System.Convert.ToInt32(2), "little"));
                py_out.AddRange(Pytra.CsModule.py_runtime.py_int_to_bytes(height, System.Convert.ToInt32(2), "little"));
                Pytra.CsModule.py_runtime.py_append(py_out, 0);

                Pytra.CsModule.py_runtime.py_append(py_out, 8);
                List<byte> compressed = _lzw_encode(fr, 8);
                long pos = 0;
                while ((pos) < ((compressed).Count)) {
                    List<byte> chunk = Pytra.CsModule.py_runtime.py_slice(compressed, System.Convert.ToInt64(pos), System.Convert.ToInt64(pos + 255));
                    Pytra.CsModule.py_runtime.py_append(py_out, (chunk).Count);
                    py_out.AddRange(chunk);
                    pos += (chunk).Count;
                }
                Pytra.CsModule.py_runtime.py_append(py_out, 0);
            }
            Pytra.CsModule.py_runtime.py_append(py_out, 0x3B);

            PyFile f = Pytra.CsModule.py_runtime.open(path, "wb");
            try
            {
                f.write(py_out);
            } finally {
                f.close();
            }
        }

    }
}
