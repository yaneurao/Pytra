// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
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
    public static class png_helper
    {
        public static void _png_append_list(System.Collections.Generic.List<long> dst, System.Collections.Generic.List<long> src)
        {
            long i = 0;
            long n = (src).Count;
            while ((i) < (n)) {
                dst.Add(Pytra.CsModule.py_runtime.py_get(src, i));
                i += 1;
            }
        }

        public static long _crc32(System.Collections.Generic.List<long> data)
        {
            long crc = 0xFFFFFFFF;
            long poly = 0xEDB88320;
            foreach (var b in data) {
                crc = crc ^ b;
                long i = 0;
                while ((i) < (8)) {
                    long lowbit = crc & 1;
                    if ((lowbit) != (0)) {
                        crc = crc >> System.Convert.ToInt32(1) ^ poly;
                    } else {
                        crc = crc >> System.Convert.ToInt32(1);
                    }
                    i += 1;
                }
            }
            return crc ^ 0xFFFFFFFF;
        }

        public static long _adler32(System.Collections.Generic.List<long> data)
        {
            long mod = 65521;
            long s1 = 1;
            long s2 = 0;
            foreach (var b in data) {
                s1 += b;
                if ((s1) >= (mod)) {
                    s1 -= mod;
                }
                s2 += s1;
                s2 = s2 % mod;
            }
            return (s2 << System.Convert.ToInt32(16) | s1) & 0xFFFFFFFF;
        }

        public static System.Collections.Generic.List<long> _png_u16le(long v)
        {
            return new System.Collections.Generic.List<long> { v & 0xFF, v >> System.Convert.ToInt32(8) & 0xFF };
        }

        public static System.Collections.Generic.List<long> _png_u32be(long v)
        {
            return new System.Collections.Generic.List<long> { v >> System.Convert.ToInt32(24) & 0xFF, v >> System.Convert.ToInt32(16) & 0xFF, v >> System.Convert.ToInt32(8) & 0xFF, v & 0xFF };
        }

        public static System.Collections.Generic.List<long> _zlib_deflate_store(System.Collections.Generic.List<long> data)
        {
            System.Collections.Generic.List<long> py_out = new System.Collections.Generic.List<long>();
            _png_append_list(py_out, new System.Collections.Generic.List<long> { 0x78, 0x01 });
            long n = (data).Count;
            long pos = 0;
            while ((pos) < (n)) {
                long remain = n - pos;
                long chunk_len = ((remain) > (65535) ? 65535 : remain);
                long final = ((pos + chunk_len) >= (n) ? 1 : 0);
                py_out.Add(final);
                _png_append_list(py_out, _png_u16le(chunk_len));
                _png_append_list(py_out, _png_u16le(0xFFFF ^ chunk_len));
                long i = pos;
                long end = pos + chunk_len;
                while ((i) < (end)) {
                    py_out.Add(Pytra.CsModule.py_runtime.py_get(data, i));
                    i += 1;
                }
                pos += chunk_len;
            }
            _png_append_list(py_out, _png_u32be(_adler32(data)));
            return py_out;
        }

        public static System.Collections.Generic.List<long> _chunk(System.Collections.Generic.List<long> chunk_type, System.Collections.Generic.List<long> data)
        {
            System.Collections.Generic.List<long> crc_input = new System.Collections.Generic.List<long>();
            _png_append_list(crc_input, chunk_type);
            _png_append_list(crc_input, data);
            long crc = _crc32(crc_input) & 0xFFFFFFFF;
            System.Collections.Generic.List<long> py_out = new System.Collections.Generic.List<long>();
            _png_append_list(py_out, _png_u32be((data).Count));
            _png_append_list(py_out, chunk_type);
            _png_append_list(py_out, data);
            _png_append_list(py_out, _png_u32be(crc));
            return py_out;
        }

        public static void write_rgb_png(string path, long width, long height, List<byte> pixels)
        {
            System.Collections.Generic.List<long> raw = new System.Collections.Generic.List<long>();
            foreach (var b in pixels) {
                raw.Add(Pytra.CsModule.py_runtime.py_int(b));
            }
            long expected = width * height * 3;
            if (((raw).Count) != (expected)) {
                throw new System.Exception("pixels length mismatch: got=" + System.Convert.ToString((raw).Count) + " expected=" + System.Convert.ToString(expected));
            }
            System.Collections.Generic.List<long> scanlines = new System.Collections.Generic.List<long>();
            long row_bytes = width * 3;
            long y = 0;
            while ((y) < (height)) {
                scanlines.Add(0);
                long start = y * row_bytes;
                long end = start + row_bytes;
                long i = start;
                while ((i) < (end)) {
                    scanlines.Add(Pytra.CsModule.py_runtime.py_get(raw, i));
                    i += 1;
                }
                y += 1;
            }
            System.Collections.Generic.List<long> ihdr = new System.Collections.Generic.List<long>();
            _png_append_list(ihdr, _png_u32be(width));
            _png_append_list(ihdr, _png_u32be(height));
            _png_append_list(ihdr, new System.Collections.Generic.List<long> { 8, 2, 0, 0, 0 });
            System.Collections.Generic.List<long> idat = _zlib_deflate_store(scanlines);

            System.Collections.Generic.List<long> png = new System.Collections.Generic.List<long>();
            _png_append_list(png, new System.Collections.Generic.List<long> { 137, 80, 78, 71, 13, 10, 26, 10 });
            _png_append_list(png, _chunk(new System.Collections.Generic.List<long> { 73, 72, 68, 82 }, ihdr));
            _png_append_list(png, _chunk(new System.Collections.Generic.List<long> { 73, 68, 65, 84 }, idat));
            System.Collections.Generic.List<long> iend_data = new System.Collections.Generic.List<long>();
            _png_append_list(png, _chunk(new System.Collections.Generic.List<long> { 73, 69, 78, 68 }, iend_data));

            PyFile f = Pytra.CsModule.py_runtime.open(path, "wb");
            try
            {
                f.write(Pytra.CsModule.py_runtime.py_bytes(png));
            } finally {
                f.close();
            }
        }

    }
}
