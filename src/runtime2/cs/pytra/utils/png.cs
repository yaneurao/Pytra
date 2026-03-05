// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
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
    public static class png_helper
    {
        public static long _crc32(List<byte> data)
        {
            long crc = 0xFFFFFFFF;
            long poly = 0xEDB88320;
            foreach (var b in data) {
                crc ^= b;
                long i = 0;
                while ((i) < (8)) {
                    if ((crc & 1) != (0)) {
                        crc = crc >> System.Convert.ToInt32(1) ^ poly;
                    } else {
                        crc >>= 1;
                    }
                    i += 1;
                }
            }
            return crc ^ 0xFFFFFFFF;
        }

        public static long _adler32(List<byte> data)
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
                s2 %= mod;
            }
            return (s2 << System.Convert.ToInt32(16) | s1) & 0xFFFFFFFF;
        }

        public static List<byte> _u16le(long v)
        {
            return Pytra.CsModule.py_runtime.py_bytes(new System.Collections.Generic.List<long> { v & 0xFF, v >> System.Convert.ToInt32(8) & 0xFF });
        }

        public static List<byte> _u32be(long v)
        {
            return Pytra.CsModule.py_runtime.py_bytes(new System.Collections.Generic.List<long> { v >> System.Convert.ToInt32(24) & 0xFF, v >> System.Convert.ToInt32(16) & 0xFF, v >> System.Convert.ToInt32(8) & 0xFF, v & 0xFF });
        }

        public static List<byte> _zlib_deflate_store(List<byte> data)
        {
            List<byte> py_out = new System.Collections.Generic.List<byte>();
            // zlib header: CMF=0x78(Deflate, 32K window), FLG=0x01(check bits OK, fastest)
            py_out.AddRange(new System.Collections.Generic.List<byte> { (byte)120, (byte)1 });
            long n = (data).Count;
            long pos = 0;
            while ((pos) < (n)) {
                long remain = n - pos;
                long chunk_len = ((remain) > (65535) ? 65535 : remain);
                long final = ((pos + chunk_len) >= (n) ? 1 : 0);
                // stored block: BTYPE=00, header bit field in LSB order (final in bit0)
                Pytra.CsModule.py_runtime.py_append(py_out, final);
                py_out.AddRange(_u16le(chunk_len));
                py_out.AddRange(_u16le(0xFFFF ^ chunk_len));
                py_out.AddRange(Pytra.CsModule.py_runtime.py_slice(data, System.Convert.ToInt64(pos), System.Convert.ToInt64(pos + chunk_len)));
                pos += chunk_len;
            }
            py_out.AddRange(_u32be(_adler32(data)));
            return Pytra.CsModule.py_runtime.py_bytes(py_out);
        }

        public static List<byte> _chunk(List<byte> chunk_type, List<byte> data)
        {
            List<byte> length = _u32be((data).Count);
            long crc = _crc32(Pytra.CsModule.py_runtime.py_concat(chunk_type, data)) & 0xFFFFFFFF;
            return Pytra.CsModule.py_runtime.py_concat(Pytra.CsModule.py_runtime.py_concat(Pytra.CsModule.py_runtime.py_concat(length, chunk_type), data), _u32be(crc));
        }

        public static void write_rgb_png(string path, long width, long height, object pixels)
        {
            List<byte> raw = Pytra.CsModule.py_runtime.py_bytes(pixels);
            long expected = width * height * 3;
            if (((raw).Count) != (expected)) {
                throw new System.Exception($"pixels length mismatch: got={(raw).Count} expected={expected}");
            }
            List<byte> scanlines = new System.Collections.Generic.List<byte>();
            long row_bytes = width * 3;
            long y = 0;
            while ((y) < (height)) {
                Pytra.CsModule.py_runtime.py_append(scanlines, 0);
                long start = y * row_bytes;
                long end = start + row_bytes;
                scanlines.AddRange(Pytra.CsModule.py_runtime.py_slice(raw, System.Convert.ToInt64(start), System.Convert.ToInt64(end)));
                y += 1;
            }
            List<byte> ihdr = Pytra.CsModule.py_runtime.py_concat(Pytra.CsModule.py_runtime.py_concat(_u32be(width), _u32be(height)), Pytra.CsModule.py_runtime.py_bytes(new System.Collections.Generic.List<long> { 8, 2, 0, 0, 0 }));
            List<byte> idat = _zlib_deflate_store(Pytra.CsModule.py_runtime.py_bytes(scanlines));

            List<byte> png = new System.Collections.Generic.List<byte>();
            png.AddRange(new System.Collections.Generic.List<byte> { (byte)137, (byte)80, (byte)78, (byte)71, (byte)13, (byte)10, (byte)26, (byte)10 });
            png.AddRange(_chunk(new System.Collections.Generic.List<byte> { (byte)73, (byte)72, (byte)68, (byte)82 }, ihdr));
            png.AddRange(_chunk(new System.Collections.Generic.List<byte> { (byte)73, (byte)68, (byte)65, (byte)84 }, idat));
            png.AddRange(_chunk(new System.Collections.Generic.List<byte> { (byte)73, (byte)69, (byte)78, (byte)68 }, new System.Collections.Generic.List<byte> {  }));

            PyFile f = Pytra.CsModule.py_runtime.open(path, "wb");
            try
            {
                f.write(png);
            } finally {
                f.close();
            }
        }

    }
}
