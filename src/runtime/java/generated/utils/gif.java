// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class gif {
    private gif() {
    }


    public static void _gif_append_list(java.util.ArrayList<Long> dst, java.util.ArrayList<Long> src) {
        long i = 0L;
        long n = ((long)(src.size()));
        while (((i) < (n))) {
            dst.add(((Long)(src.get((int)((((i) < 0L) ? (((long)(src.size())) + (i)) : (i)))))));
            i += 1L;
        }
    }

    public static java.util.ArrayList<Long> _gif_u16le(long v) {
        return new java.util.ArrayList<Long>(java.util.Arrays.asList(v & 255L, v >> 8L & 255L));
    }

    public static java.util.ArrayList<Long> _lzw_encode(java.util.ArrayList<Long> data, long min_code_size) {
        if (((((long)(data.size()))) == (0L))) {
            java.util.ArrayList<Long> empty = new java.util.ArrayList<Long>();
            return PyRuntime.__pytra_bytearray(empty);
        }
        long clear_code = 1L << min_code_size;
        long end_code = clear_code + 1L;
        long code_size = min_code_size + 1L;
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        long bit_buffer = 0L;
        long bit_count = 0L;
        bit_buffer |= clear_code << bit_count;
        bit_count += code_size;
        while (((bit_count) >= (8L))) {
            out.add(bit_buffer & 255L);
            bit_buffer = bit_buffer >> 8L;
            bit_count -= 8L;
        }
        code_size = min_code_size + 1L;
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(data));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            long v = ((Long)(__iter_0.get((int)(__iter_i_1))));
            bit_buffer |= v << bit_count;
            bit_count += code_size;
            while (((bit_count) >= (8L))) {
                out.add(bit_buffer & 255L);
                bit_buffer = bit_buffer >> 8L;
                bit_count -= 8L;
            }
            bit_buffer |= clear_code << bit_count;
            bit_count += code_size;
            while (((bit_count) >= (8L))) {
                out.add(bit_buffer & 255L);
                bit_buffer = bit_buffer >> 8L;
                bit_count -= 8L;
            }
            code_size = min_code_size + 1L;
        }
        bit_buffer |= end_code << bit_count;
        bit_count += code_size;
        while (((bit_count) >= (8L))) {
            out.add(bit_buffer & 255L);
            bit_buffer = bit_buffer >> 8L;
            bit_count -= 8L;
        }
        if (((bit_count) > (0L))) {
            out.add(bit_buffer & 255L);
        }
        return PyRuntime.__pytra_bytearray(out);
    }

    public static java.util.ArrayList<Long> grayscale_palette() {
        java.util.ArrayList<Long> p = new java.util.ArrayList<Long>();
        long i = 0L;
        while (((i) < (256L))) {
            p.add(i);
            p.add(i);
            p.add(i);
            i += 1L;
        }
        return PyRuntime.__pytra_bytearray(p);
    }

    public static void save_gif(String path, long width, long height, java.util.ArrayList<java.util.ArrayList<Long>> frames, java.util.ArrayList<Long> palette, long delay_cs, long loop) {
        if (((((long)(palette.size()))) != (256L * 3L))) {
            throw new RuntimeException(PyRuntime.pyToString("palette must be 256*3 bytes"));
        }
        java.util.ArrayList<java.util.ArrayList<Long>> frame_lists = new java.util.ArrayList<java.util.ArrayList<Long>>();
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(frames));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            java.util.ArrayList<Long> fr = ((java.util.ArrayList<Long>)(__iter_0.get((int)(__iter_i_1))));
            java.util.ArrayList<Long> fr_list = new java.util.ArrayList<Long>();
            java.util.ArrayList<Object> __iter_2 = ((java.util.ArrayList<Object>)(Object)(fr));
            for (long __iter_i_3 = 0L; __iter_i_3 < ((long)(__iter_2.size())); __iter_i_3 += 1L) {
                long v = ((Long)(__iter_2.get((int)(__iter_i_3))));
                fr_list.add(PyRuntime.__pytra_int(v));
            }
            if (((((long)(fr_list.size()))) != (width * height))) {
                throw new RuntimeException(PyRuntime.pyToString("frame size mismatch"));
            }
            frame_lists.add(fr_list);
        }
        java.util.ArrayList<Long> palette_list = new java.util.ArrayList<Long>();
        java.util.ArrayList<Object> __iter_4 = ((java.util.ArrayList<Object>)(Object)(palette));
        for (long __iter_i_5 = 0L; __iter_i_5 < ((long)(__iter_4.size())); __iter_i_5 += 1L) {
            long v = ((Long)(__iter_4.get((int)(__iter_i_5))));
            palette_list.add(PyRuntime.__pytra_int(v));
        }
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        _gif_append_list(out, new java.util.ArrayList<Long>(java.util.Arrays.asList(71L, 73L, 70L, 56L, 57L, 97L)));
        _gif_append_list(out, _gif_u16le(width));
        _gif_append_list(out, _gif_u16le(height));
        out.add(247L);
        out.add(0L);
        out.add(0L);
        _gif_append_list(out, palette_list);
        _gif_append_list(out, new java.util.ArrayList<Long>(java.util.Arrays.asList(33L, 255L, 11L, 78L, 69L, 84L, 83L, 67L, 65L, 80L, 69L, 50L, 46L, 48L, 3L, 1L)));
        _gif_append_list(out, _gif_u16le(loop));
        out.add(0L);
        java.util.ArrayList<Object> __iter_6 = ((java.util.ArrayList<Object>)(Object)(frame_lists));
        for (long __iter_i_7 = 0L; __iter_i_7 < ((long)(__iter_6.size())); __iter_i_7 += 1L) {
            java.util.ArrayList<Long> fr_list = ((java.util.ArrayList<Long>)(__iter_6.get((int)(__iter_i_7))));
            _gif_append_list(out, new java.util.ArrayList<Long>(java.util.Arrays.asList(33L, 249L, 4L, 0L)));
            _gif_append_list(out, _gif_u16le(delay_cs));
            _gif_append_list(out, new java.util.ArrayList<Long>(java.util.Arrays.asList(0L, 0L)));
            out.add(44L);
            _gif_append_list(out, _gif_u16le(0L));
            _gif_append_list(out, _gif_u16le(0L));
            _gif_append_list(out, _gif_u16le(width));
            _gif_append_list(out, _gif_u16le(height));
            out.add(0L);
            out.add(8L);
            java.util.ArrayList<Long> compressed = _lzw_encode(PyRuntime.__pytra_bytearray(fr_list), 8L);
            long pos = 0L;
            while (((pos) < (((long)(compressed.size()))))) {
                long remain = ((long)(compressed.size())) - pos;
                long chunk_len = ((((remain) > (255L))) ? (255L) : (remain));
                out.add(chunk_len);
                long i = 0L;
                while (((i) < (chunk_len))) {
                    out.add(((Long)(compressed.get((int)((((pos + i) < 0L) ? (((long)(compressed.size())) + (pos + i)) : (pos + i)))))));
                    i += 1L;
                }
                pos += chunk_len;
            }
            out.add(0L);
        }
        out.add(59L);
        PyRuntime.PyFile f = PyRuntime.open(path, "wb");
        f.write(PyRuntime.__pytra_bytearray(out));
        f.close();
    }

    public static void main(String[] args) {
    }
}
