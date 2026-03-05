// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class tmp {
    private tmp() {
    }


    public static java.util.ArrayList<Long> _lzw_encode(java.util.ArrayList<Long> data, long min_code_size) {
        if ((((long)(data.size())) == 0L)) {
            return new java.util.ArrayList<Long>();
        }
        long clear_code = 1L << min_code_size;
        long end_code = clear_code + 1L;
        long code_size = min_code_size + 1L;
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        long bit_buffer = 0L;
        long bit_count = 0L;
        bit_buffer += clear_code << bit_count;
        bit_count += code_size;
        while ((bit_count >= 8L)) {
            out.add(bit_buffer & 255L);
            bit_buffer += 8L;
            bit_count -= 8L;
        }
        code_size = min_code_size + 1L;
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(data));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            uint8 v = ((uint8)(__iter_0.get((int)(__iter_i_1))));
            bit_buffer += v << bit_count;
            bit_count += code_size;
            while ((bit_count >= 8L)) {
                out.add(bit_buffer & 255L);
                bit_buffer += 8L;
                bit_count -= 8L;
            }
            bit_buffer += clear_code << bit_count;
            bit_count += code_size;
            while ((bit_count >= 8L)) {
                out.add(bit_buffer & 255L);
                bit_buffer += 8L;
                bit_count -= 8L;
            }
            code_size = min_code_size + 1L;
        }
        bit_buffer += end_code << bit_count;
        bit_count += code_size;
        while ((bit_count >= 8L)) {
            out.add(bit_buffer & 255L);
            bit_buffer += 8L;
            bit_count -= 8L;
        }
        if ((bit_count > 0L)) {
            out.add(bit_buffer & 255L);
        }
        return new java.util.ArrayList<Long>(out);
    }

    public static java.util.ArrayList<Long> grayscale_palette() {
        java.util.ArrayList<Long> p = new java.util.ArrayList<Long>();
        long i = 0L;
        while ((i < 256L)) {
            p.add(i);
            p.add(i);
            p.add(i);
            i += 1L;
        }
        return new java.util.ArrayList<Long>(p);
    }

    public static void save_gif(String path, long width, long height, java.util.ArrayList<java.util.ArrayList<Long>> frames, java.util.ArrayList<Long> palette, long delay_cs, long loop) {
        if ((((long)(palette.size())) != 256L * 3L)) {
            throw new RuntimeException(PyRuntime.pyToString("palette must be 256*3 bytes"));
        }
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(frames));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            java.util.ArrayList<Long> fr = ((java.util.ArrayList<Long>)(__iter_0.get((int)(__iter_i_1))));
            if ((((long)(fr.size())) != width * height)) {
                throw new RuntimeException(PyRuntime.pyToString("frame size mismatch"));
            }
        }
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        out.addAll(new java.util.ArrayList<Long>(java.util.Arrays.asList(71L, 73L, 70L, 56L, 57L, 97L)));
        out.addAll(width.to_bytes(2L, "little"));
        out.addAll(height.to_bytes(2L, "little"));
        out.add(247L);
        out.add(0L);
        out.add(0L);
        out.addAll(palette);
        out.addAll(new java.util.ArrayList<Long>(java.util.Arrays.asList(33L, 255L, 11L, 78L, 69L, 84L, 83L, 67L, 65L, 80L, 69L, 50L, 46L, 48L, 3L, 1L)));
        out.addAll(loop.to_bytes(2L, "little"));
        out.add(0L);
        java.util.ArrayList<Object> __iter_2 = ((java.util.ArrayList<Object>)(Object)(frames));
        for (long __iter_i_3 = 0L; __iter_i_3 < ((long)(__iter_2.size())); __iter_i_3 += 1L) {
            java.util.ArrayList<Long> fr = ((java.util.ArrayList<Long>)(__iter_2.get((int)(__iter_i_3))));
            out.addAll(new java.util.ArrayList<Long>(java.util.Arrays.asList(33L, 249L, 4L, 0L)));
            out.addAll(delay_cs.to_bytes(2L, "little"));
            out.addAll(new java.util.ArrayList<Long>(java.util.Arrays.asList(0L, 0L)));
            out.add(44L);
            out.addAll(0L.to_bytes(2L, "little"));
            out.addAll(0L.to_bytes(2L, "little"));
            out.addAll(width.to_bytes(2L, "little"));
            out.addAll(height.to_bytes(2L, "little"));
            out.add(0L);
            out.add(8L);
            java.util.ArrayList<Long> compressed = _lzw_encode(fr, 8L);
            long pos = 0L;
            while ((pos < ((long)(compressed.size())))) {
                java.util.ArrayList<Long> chunk = PyRuntime.__pytra_list_slice(compressed, (((pos) < 0L) ? (((long)(compressed.size())) + (pos)) : (pos)), (((pos + 255L) < 0L) ? (((long)(compressed.size())) + (pos + 255L)) : (pos + 255L)));
                out.add(((long)(chunk.size())));
                out.addAll(chunk);
                pos += ((long)(chunk.size()));
            }
            out.add(0L);
        }
        out.add(59L);
        PyFile f = open(path, "wb");
        f.write(out);
        f.close();
    }

    public static void main(String[] args) {
    }
}
