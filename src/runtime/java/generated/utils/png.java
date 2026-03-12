// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class png {
    private png() {
    }


    public static void _png_append_list(java.util.ArrayList<Long> dst, java.util.ArrayList<Long> src) {
        long i = 0L;
        long n = ((long)(src.size()));
        while (((i) < (n))) {
            dst.add(((Long)(src.get((int)((((i) < 0L) ? (((long)(src.size())) + (i)) : (i)))))));
            i += 1L;
        }
    }

    public static long _crc32(java.util.ArrayList<Long> data) {
        long crc = 4294967295L;
        long poly = 3988292384L;
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(data));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            long b = ((Long)(__iter_0.get((int)(__iter_i_1))));
            crc = crc ^ b;
            long i = 0L;
            while (((i) < (8L))) {
                long lowbit = crc & 1L;
                if (((lowbit) != (0L))) {
                    crc = crc >> 1L ^ poly;
                } else {
                    crc = crc >> 1L;
                }
                i += 1L;
            }
        }
        return crc ^ 4294967295L;
    }

    public static long _adler32(java.util.ArrayList<Long> data) {
        long mod = 65521L;
        long s1 = 1L;
        long s2 = 0L;
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(data));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            long b = ((Long)(__iter_0.get((int)(__iter_i_1))));
            s1 += b;
            if (((s1) >= (mod))) {
                s1 -= mod;
            }
            s2 += s1;
            s2 = s2 % mod;
        }
        return (s2 << 16L | s1) & 4294967295L;
    }

    public static java.util.ArrayList<Long> _png_u16le(long v) {
        return new java.util.ArrayList<Long>(java.util.Arrays.asList(v & 255L, v >> 8L & 255L));
    }

    public static java.util.ArrayList<Long> _png_u32be(long v) {
        return new java.util.ArrayList<Long>(java.util.Arrays.asList(v >> 24L & 255L, v >> 16L & 255L, v >> 8L & 255L, v & 255L));
    }

    public static java.util.ArrayList<Long> _zlib_deflate_store(java.util.ArrayList<Long> data) {
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        _png_append_list(out, new java.util.ArrayList<Long>(java.util.Arrays.asList(120L, 1L)));
        long n = ((long)(data.size()));
        long pos = 0L;
        while (((pos) < (n))) {
            long remain = n - pos;
            long chunk_len = ((((remain) > (65535L))) ? (65535L) : (remain));
            long _final = ((((pos + chunk_len) >= (n))) ? (1L) : (0L));
            out.add(_final);
            _png_append_list(out, _png_u16le(chunk_len));
            _png_append_list(out, _png_u16le(65535L ^ chunk_len));
            long i = pos;
            long end = pos + chunk_len;
            while (((i) < (end))) {
                out.add(((Long)(data.get((int)((((i) < 0L) ? (((long)(data.size())) + (i)) : (i)))))));
                i += 1L;
            }
            pos += chunk_len;
        }
        _png_append_list(out, _png_u32be(_adler32(data)));
        return out;
    }

    public static java.util.ArrayList<Long> _chunk(java.util.ArrayList<Long> chunk_type, java.util.ArrayList<Long> data) {
        java.util.ArrayList<Long> crc_input = new java.util.ArrayList<Long>();
        _png_append_list(crc_input, chunk_type);
        _png_append_list(crc_input, data);
        long crc = _crc32(crc_input) & 4294967295L;
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        _png_append_list(out, _png_u32be(((long)(data.size()))));
        _png_append_list(out, chunk_type);
        _png_append_list(out, data);
        _png_append_list(out, _png_u32be(crc));
        return out;
    }

    public static void write_rgb_png(String path, long width, long height, java.util.ArrayList<Long> pixels) {
        java.util.ArrayList<Long> raw = new java.util.ArrayList<Long>();
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(pixels));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            long b = ((Long)(__iter_0.get((int)(__iter_i_1))));
            raw.add(PyRuntime.__pytra_int(b));
        }
        long expected = width * height * 3L;
        if (((((long)(raw.size()))) != (expected))) {
            throw new RuntimeException(PyRuntime.pyToString("pixels length mismatch: got=" + String.valueOf(((long)(raw.size()))) + " expected=" + String.valueOf(expected)));
        }
        java.util.ArrayList<Long> scanlines = new java.util.ArrayList<Long>();
        long row_bytes = width * 3L;
        long y = 0L;
        while (((y) < (height))) {
            scanlines.add(0L);
            long start = y * row_bytes;
            long end = start + row_bytes;
            long i = start;
            while (((i) < (end))) {
                scanlines.add(((Long)(raw.get((int)((((i) < 0L) ? (((long)(raw.size())) + (i)) : (i)))))));
                i += 1L;
            }
            y += 1L;
        }
        java.util.ArrayList<Long> ihdr = new java.util.ArrayList<Long>();
        _png_append_list(ihdr, _png_u32be(width));
        _png_append_list(ihdr, _png_u32be(height));
        _png_append_list(ihdr, new java.util.ArrayList<Long>(java.util.Arrays.asList(8L, 2L, 0L, 0L, 0L)));
        java.util.ArrayList<Long> idat = _zlib_deflate_store(scanlines);
        java.util.ArrayList<Long> png = new java.util.ArrayList<Long>();
        _png_append_list(png, new java.util.ArrayList<Long>(java.util.Arrays.asList(137L, 80L, 78L, 71L, 13L, 10L, 26L, 10L)));
        _png_append_list(png, _chunk(new java.util.ArrayList<Long>(java.util.Arrays.asList(73L, 72L, 68L, 82L)), ihdr));
        _png_append_list(png, _chunk(new java.util.ArrayList<Long>(java.util.Arrays.asList(73L, 68L, 65L, 84L)), idat));
        java.util.ArrayList<Long> iend_data = new java.util.ArrayList<Long>();
        _png_append_list(png, _chunk(new java.util.ArrayList<Long>(java.util.Arrays.asList(73L, 69L, 78L, 68L)), iend_data));
        PyRuntime.PyFile f = PyRuntime.open(path, "wb");
        f.write(PyRuntime.__pytra_bytearray(png));
        f.close();
    }

    public static void main(String[] args) {
    }
}
