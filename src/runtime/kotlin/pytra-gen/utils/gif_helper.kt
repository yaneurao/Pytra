// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: tools/gen_runtime_from_manifest.py



fun _gif_append_list(dst: MutableList<Any?>, src: MutableList<Any?>) {
    var i: Long = 0L
    var n: Long = __pytra_len(src)
    while ((__pytra_int(i) < __pytra_int(n))) {
        dst.add(__pytra_int(__pytra_get_index(src, i)))
        i += 1L
    }
}

fun _gif_u16le(v: Long): MutableList<Any?> {
    return __pytra_as_list(mutableListOf((v and 255L), ((v shr (8L).toInt()) and 255L)))
}

fun _lzw_encode(data: MutableList<Any?>, min_code_size: Long): MutableList<Any?> {
    if ((__pytra_int(__pytra_len(data)) == __pytra_int(0L))) {
        return __pytra_bytes(mutableListOf<Any?>())
    }
    var clear_code: Long = (1L shl (min_code_size).toInt())
    var end_code: Long = (clear_code + 1L)
    var code_size: Long = (min_code_size + 1L)
    var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var bit_buffer: Long = 0L
    var bit_count: Long = 0L
    bit_buffer += (clear_code shl (bit_count).toInt())
    bit_count += code_size
    while ((__pytra_int(bit_count) >= __pytra_int(8L))) {
        out.add((bit_buffer and 255L))
        bit_buffer = (bit_buffer shr (8L).toInt())
        bit_count -= 8L
    }
    code_size = (min_code_size + 1L)
    val __iter_0 = __pytra_as_list(data)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val v: Long = __pytra_int(__iter_0[__i_1.toInt()])
        bit_buffer += (v shl (bit_count).toInt())
        bit_count += code_size
        while ((__pytra_int(bit_count) >= __pytra_int(8L))) {
            out.add((bit_buffer and 255L))
            bit_buffer = (bit_buffer shr (8L).toInt())
            bit_count -= 8L
        }
        bit_buffer += (clear_code shl (bit_count).toInt())
        bit_count += code_size
        while ((__pytra_int(bit_count) >= __pytra_int(8L))) {
            out.add((bit_buffer and 255L))
            bit_buffer = (bit_buffer shr (8L).toInt())
            bit_count -= 8L
        }
        code_size = (min_code_size + 1L)
        __i_1 += 1L
    }
    bit_buffer += (end_code shl (bit_count).toInt())
    bit_count += code_size
    while ((__pytra_int(bit_count) >= __pytra_int(8L))) {
        out.add((bit_buffer and 255L))
        bit_buffer = (bit_buffer shr (8L).toInt())
        bit_count -= 8L
    }
    if ((__pytra_int(bit_count) > __pytra_int(0L))) {
        out.add((bit_buffer and 255L))
    }
    return __pytra_bytes(out)
}

fun grayscale_palette(): MutableList<Any?> {
    var p: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var i: Long = 0L
    while ((__pytra_int(i) < __pytra_int(256L))) {
        p.add(i)
        p.add(i)
        p.add(i)
        i += 1L
    }
    return __pytra_bytes(p)
}

fun save_gif(path: String, width: Long, height: Long, frames: MutableList<Any?>, palette: MutableList<Any?>, delay_cs: Long, loop: Long) {
    if ((__pytra_int(__pytra_len(palette)) != __pytra_int(256L * 3L))) {
        throw RuntimeException(__pytra_str("palette must be 256*3 bytes"))
    }
    var frame_lists: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __iter_0 = __pytra_as_list(frames)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val fr: MutableList<Any?> = __pytra_as_list(__iter_0[__i_1.toInt()])
        var fr_list: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
        val __iter_2 = __pytra_as_list(fr)
        var __i_3: Long = 0L
        while (__i_3 < __iter_2.size.toLong()) {
            val v: Long = __pytra_int(__iter_2[__i_3.toInt()])
            fr_list.add(v)
            __i_3 += 1L
        }
        if ((__pytra_int(__pytra_len(fr_list)) != __pytra_int(width * height))) {
            throw RuntimeException(__pytra_str("frame size mismatch"))
        }
        frame_lists.add(fr_list)
        __i_1 += 1L
    }
    var palette_list: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __iter_4 = __pytra_as_list(palette)
    var __i_5: Long = 0L
    while (__i_5 < __iter_4.size.toLong()) {
        val v: Long = __pytra_int(__iter_4[__i_5.toInt()])
        palette_list.add(v)
        __i_5 += 1L
    }
    var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    _gif_append_list(out, mutableListOf(71L, 73L, 70L, 56L, 57L, 97L))
    _gif_append_list(out, _gif_u16le(width))
    _gif_append_list(out, _gif_u16le(height))
    out.add(247L)
    out.add(0L)
    out.add(0L)
    _gif_append_list(out, palette_list)
    _gif_append_list(out, mutableListOf(33L, 255L, 11L, 78L, 69L, 84L, 83L, 67L, 65L, 80L, 69L, 50L, 46L, 48L, 3L, 1L))
    _gif_append_list(out, _gif_u16le(loop))
    out.add(0L)
    val __iter_6 = __pytra_as_list(frame_lists)
    var __i_7: Long = 0L
    while (__i_7 < __iter_6.size.toLong()) {
        val fr_list: MutableList<Any?> = __pytra_as_list(__iter_6[__i_7.toInt()])
        _gif_append_list(out, mutableListOf(33L, 249L, 4L, 0L))
        _gif_append_list(out, _gif_u16le(delay_cs))
        _gif_append_list(out, mutableListOf(0L, 0L))
        out.add(44L)
        _gif_append_list(out, _gif_u16le(0L))
        _gif_append_list(out, _gif_u16le(0L))
        _gif_append_list(out, _gif_u16le(width))
        _gif_append_list(out, _gif_u16le(height))
        out.add(0L)
        out.add(8L)
        var compressed: MutableList<Any?> = _lzw_encode(__pytra_bytes(fr_list), 8L)
        var pos: Long = 0L
        while ((__pytra_int(pos) < __pytra_int(__pytra_len(compressed)))) {
            var remain: Long = (__pytra_len(compressed) - pos)
            var chunk_len: Long = __pytra_int(__pytra_ifexp((__pytra_int(remain) > __pytra_int(255L)), 255L, remain))
            out.add(chunk_len)
            var i: Long = 0L
            while ((__pytra_int(i) < __pytra_int(chunk_len))) {
                out.add(__pytra_int(__pytra_get_index(compressed, (pos + i))))
                i += 1L
            }
            pos += chunk_len
        }
        out.add(0L)
        __i_7 += 1L
    }
    out.add(59L)
    var f: PyFile = open(path, "wb")
    f.write(__pytra_bytes(out))
    f.close()
}

fun main(args: Array<String>) {
}
