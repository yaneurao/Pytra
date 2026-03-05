// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class tmp {
    private tmp() {
    }


    public static long _crc32(java.util.ArrayList<Long> data) {
        long crc = 4294967295L;
        long poly = 3988292384L;
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(data));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            uint8 b = ((uint8)(__iter_0.get((int)(__iter_i_1))));
            crc += b;
            long i = 0L;
            while ((i < 8L)) {
                if ((crc & 1L != 0L)) {
                    crc = crc >> 1L ^ poly;
                } else {
                    crc += 1L;
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
            uint8 b = ((uint8)(__iter_0.get((int)(__iter_i_1))));
            s1 += b;
            if ((s1 >= mod)) {
                s1 -= mod;
            }
            s2 += s1;
            s2 %= mod;
        }
        return (s2 << 16L | s1) & 4294967295L;
    }

    public static java.util.ArrayList<Long> _u16le(long v) {
        return new java.util.ArrayList<Long>(new java.util.ArrayList<Long>(java.util.Arrays.asList(v & 255L, v >> 8L & 255L)));
    }

    public static java.util.ArrayList<Long> _u32be(long v) {
        return new java.util.ArrayList<Long>(new java.util.ArrayList<Long>(java.util.Arrays.asList(v >> 24L & 255L, v >> 16L & 255L, v >> 8L & 255L, v & 255L)));
    }

    public static java.util.ArrayList<Long> _zlib_deflate_store(java.util.ArrayList<Long> data) {
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        out.addAll(new java.util.ArrayList<Long>(java.util.Arrays.asList(120L, 1L)));
        long n = ((long)(data.size()));
        long pos = 0L;
        while ((pos < n)) {
            long remain = n - pos;
            long chunk_len = (((remain > 65535L)) ? (65535L) : (remain));
            long _final = (((pos + chunk_len >= n)) ? (1L) : (0L));
            out.add(_final);
            out.addAll(_u16le(chunk_len));
            out.addAll(_u16le(65535L ^ chunk_len));
            out.addAll(PyRuntime.__pytra_list_slice(data, (((pos) < 0L) ? (((long)(data.size())) + (pos)) : (pos)), (((pos + chunk_len) < 0L) ? (((long)(data.size())) + (pos + chunk_len)) : (pos + chunk_len))));
            pos += chunk_len;
        }
        out.addAll(_u32be(_adler32(data)));
        return new java.util.ArrayList<Long>(out);
    }

    public static java.util.ArrayList<Long> _chunk(java.util.ArrayList<Long> chunk_type, java.util.ArrayList<Long> data) {
        java.util.ArrayList<Long> length = _u32be(((long)(data.size())));
        long crc = _crc32(PyRuntime.__pytra_list_concat(chunk_type, data)) & 4294967295L;
        return PyRuntime.__pytra_list_concat(PyRuntime.__pytra_list_concat(PyRuntime.__pytra_list_concat(length, chunk_type), data), _u32be(crc));
    }

    public static void write_rgb_png(String path, long width, long height, Object pixels) {
        java.util.ArrayList<Long> raw = new java.util.ArrayList<Long>(pixels);
        long expected = width * height * 3L;
        if ((((long)(raw.size())) != expected)) {
            throw new RuntimeException(PyRuntime.pyToString(null));
        }
        java.util.ArrayList<Long> scanlines = new java.util.ArrayList<Long>();
        long row_bytes = width * 3L;
        long y = 0L;
        while ((y < height)) {
            scanlines.add(0L);
            long start = y * row_bytes;
            long end = start + row_bytes;
            scanlines.addAll(PyRuntime.__pytra_list_slice(raw, (((start) < 0L) ? (((long)(raw.size())) + (start)) : (start)), (((end) < 0L) ? (((long)(raw.size())) + (end)) : (end))));
            y += 1L;
        }
        java.util.ArrayList<Long> ihdr = PyRuntime.__pytra_list_concat(PyRuntime.__pytra_list_concat(_u32be(width), _u32be(height)), new java.util.ArrayList<Long>(new java.util.ArrayList<Long>(java.util.Arrays.asList(8L, 2L, 0L, 0L, 0L))));
        java.util.ArrayList<Long> idat = _zlib_deflate_store(new java.util.ArrayList<Long>(scanlines));
        java.util.ArrayList<Long> png = new java.util.ArrayList<Long>();
        png.addAll(new java.util.ArrayList<Long>(java.util.Arrays.asList(137L, 80L, 78L, 71L, 13L, 10L, 26L, 10L)));
        png.addAll(_chunk(new java.util.ArrayList<Long>(java.util.Arrays.asList(73L, 72L, 68L, 82L)), ihdr));
        png.addAll(_chunk(new java.util.ArrayList<Long>(java.util.Arrays.asList(73L, 68L, 65L, 84L)), idat));
        png.addAll(_chunk(new java.util.ArrayList<Long>(java.util.Arrays.asList(73L, 69L, 78L, 68L)), new java.util.ArrayList<Long>()));
        PyFile f = open(path, "wb");
        f.write(png);
        f.close();
    }

    public static void main(String[] args) {
    }
}
