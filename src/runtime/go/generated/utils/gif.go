// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func _gif_append_list(dst []any, src []any) {
    var i int64 = int64(0)
    var n int64 = __pytra_len(src)
    for (i < n) {
        dst = append(dst, __pytra_int(__pytra_get_index(src, i)))
        i += int64(1)
    }
}

func _gif_u16le(v int64) []any {
    return __pytra_as_list([]any{(v & int64(255)), ((v >> int64(8)) & int64(255))})
}

func _lzw_encode(data []any, min_code_size int64) []any {
    if (__pytra_len(data) == int64(0)) {
        return __pytra_as_list(__pytra_bytes([]any{}))
    }
    var clear_code int64 = (int64(1) << min_code_size)
    var end_code int64 = (clear_code + int64(1))
    var code_size int64 = (min_code_size + int64(1))
    var out []any = __pytra_as_list([]any{})
    var bit_buffer int64 = int64(0)
    var bit_count int64 = int64(0)
    bit_buffer += (clear_code << bit_count)
    bit_count += code_size
    for (bit_count >= int64(8)) {
        out = append(out, (bit_buffer & int64(255)))
        bit_buffer = (bit_buffer >> int64(8))
        bit_count -= int64(8)
    }
    code_size = (min_code_size + int64(1))
    __iter_0 := __pytra_as_list(data)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        var v int64 = __pytra_int(__iter_0[__i_1])
        bit_buffer += (v << bit_count)
        bit_count += code_size
        for (bit_count >= int64(8)) {
            out = append(out, (bit_buffer & int64(255)))
            bit_buffer = (bit_buffer >> int64(8))
            bit_count -= int64(8)
        }
        bit_buffer += (clear_code << bit_count)
        bit_count += code_size
        for (bit_count >= int64(8)) {
            out = append(out, (bit_buffer & int64(255)))
            bit_buffer = (bit_buffer >> int64(8))
            bit_count -= int64(8)
        }
        code_size = (min_code_size + int64(1))
    }
    bit_buffer += (end_code << bit_count)
    bit_count += code_size
    for (bit_count >= int64(8)) {
        out = append(out, (bit_buffer & int64(255)))
        bit_buffer = (bit_buffer >> int64(8))
        bit_count -= int64(8)
    }
    if (bit_count > int64(0)) {
        out = append(out, (bit_buffer & int64(255)))
    }
    return __pytra_as_list(__pytra_bytes(out))
}

func grayscale_palette() []any {
    var p []any = __pytra_as_list([]any{})
    var i int64 = int64(0)
    for (i < int64(256)) {
        p = append(p, i)
        p = append(p, i)
        p = append(p, i)
        i += int64(1)
    }
    return __pytra_as_list(__pytra_bytes(p))
}

func save_gif(path string, width int64, height int64, frames []any, palette []any, delay_cs int64, loop int64) {
    if (__pytra_len(palette) != (int64(256) * int64(3))) {
        panic(__pytra_str("palette must be 256*3 bytes"))
    }
    var frame_lists []any = __pytra_as_list([]any{})
    __iter_0 := __pytra_as_list(frames)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        var fr []any = __pytra_as_list(__iter_0[__i_1])
        var fr_list []any = __pytra_as_list([]any{})
        __iter_2 := __pytra_as_list(fr)
        for __i_3 := int64(0); __i_3 < int64(len(__iter_2)); __i_3 += 1 {
            var v int64 = __pytra_int(__iter_2[__i_3])
            fr_list = append(fr_list, __pytra_int(v))
        }
        if (__pytra_len(fr_list) != (width * height)) {
            panic(__pytra_str("frame size mismatch"))
        }
        frame_lists = append(frame_lists, fr_list)
    }
    var palette_list []any = __pytra_as_list([]any{})
    __iter_4 := __pytra_as_list(palette)
    for __i_5 := int64(0); __i_5 < int64(len(__iter_4)); __i_5 += 1 {
        var v int64 = __pytra_int(__iter_4[__i_5])
        palette_list = append(palette_list, __pytra_int(v))
    }
    var out []any = __pytra_as_list([]any{})
    out = append(out, []any{int64(71), int64(73), int64(70), int64(56), int64(57), int64(97)}...)
    out = append(out, _gif_u16le(width)...)
    out = append(out, _gif_u16le(height)...)
    out = append(out, int64(247))
    out = append(out, int64(0))
    out = append(out, int64(0))
    out = append(out, palette_list...)
    out = append(out, []any{int64(33), int64(255), int64(11), int64(78), int64(69), int64(84), int64(83), int64(67), int64(65), int64(80), int64(69), int64(50), int64(46), int64(48), int64(3), int64(1)}...)
    out = append(out, _gif_u16le(loop)...)
    out = append(out, int64(0))
    __iter_6 := __pytra_as_list(frame_lists)
    for __i_7 := int64(0); __i_7 < int64(len(__iter_6)); __i_7 += 1 {
        var fr_list []any = __pytra_as_list(__iter_6[__i_7])
        out = append(out, []any{int64(33), int64(249), int64(4), int64(0)}...)
        out = append(out, _gif_u16le(delay_cs)...)
        out = append(out, []any{int64(0), int64(0)}...)
        out = append(out, int64(44))
        out = append(out, _gif_u16le(int64(0))...)
        out = append(out, _gif_u16le(int64(0))...)
        out = append(out, _gif_u16le(width)...)
        out = append(out, _gif_u16le(height)...)
        out = append(out, int64(0))
        out = append(out, int64(8))
        var compressed []any = __pytra_as_list(_lzw_encode(__pytra_bytes(fr_list), int64(8)))
        var pos int64 = int64(0)
        for (pos < __pytra_len(compressed)) {
            var remain int64 = (__pytra_len(compressed) - pos)
            var chunk_len int64 = __pytra_int(__pytra_ifexp((remain > int64(255)), int64(255), remain))
            out = append(out, chunk_len)
            var i int64 = int64(0)
            for (i < chunk_len) {
                out = append(out, __pytra_int(__pytra_get_index(compressed, (pos + i))))
                i += int64(1)
            }
            pos += chunk_len
        }
        out = append(out, int64(0))
    }
    out = append(out, int64(59))
    f := open(path, "wb")
    f.write(__pytra_bytes(out))
    f.close()
}
