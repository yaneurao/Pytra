// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// generated-by: tools/gen_runtime_from_manifest.py



fun _png_append_list(dst: MutableList<Any?>, src: MutableList<Any?>) {
    var i: Long = 0L
    var n: Long = __pytra_len(src)
    while ((__pytra_int(i) < __pytra_int(n))) {
        dst.add(__pytra_int(__pytra_get_index(src, i)))
        i += 1L
    }
}

fun _crc32(data: MutableList<Any?>): Long {
    var crc: Long = 4294967295L
    var poly: Long = 3988292384L
    val __iter_0 = __pytra_as_list(data)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val b: Long = __pytra_int(__iter_0[__i_1.toInt()])
        crc = (crc xor b)
        var i: Long = 0L
        while ((__pytra_int(i) < __pytra_int(8L))) {
            var lowbit: Long = (crc and 1L)
            if ((__pytra_int(lowbit) != __pytra_int(0L))) {
                crc = ((crc shr (1L).toInt()) xor poly)
            } else {
                crc = (crc shr (1L).toInt())
            }
            i += 1L
        }
        __i_1 += 1L
    }
    return (crc xor 4294967295L)
}

fun _adler32(data: MutableList<Any?>): Long {
    var mod: Long = 65521L
    var s1: Long = 1L
    var s2: Long = 0L
    val __iter_0 = __pytra_as_list(data)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val b: Long = __pytra_int(__iter_0[__i_1.toInt()])
        s1 += b
        if ((__pytra_int(s1) >= __pytra_int(mod))) {
            s1 -= mod
        }
        s2 += s1
        s2 = (s2 % mod)
        __i_1 += 1L
    }
    return (((s2 shl (16L).toInt()) or s1) and 4294967295L)
}

fun _png_u16le(v: Long): MutableList<Any?> {
    return __pytra_as_list(mutableListOf((v and 255L), ((v shr (8L).toInt()) and 255L)))
}

fun _png_u32be(v: Long): MutableList<Any?> {
    return __pytra_as_list(mutableListOf(((v shr (24L).toInt()) and 255L), ((v shr (16L).toInt()) and 255L), ((v shr (8L).toInt()) and 255L), (v and 255L)))
}

fun _zlib_deflate_store(data: MutableList<Any?>): MutableList<Any?> {
    var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    _png_append_list(out, mutableListOf(120L, 1L))
    var n: Long = __pytra_len(data)
    var pos: Long = 0L
    while ((__pytra_int(pos) < __pytra_int(n))) {
        var remain: Long = (n - pos)
        var chunk_len: Long = __pytra_int(__pytra_ifexp((__pytra_int(remain) > __pytra_int(65535L)), 65535L, remain))
        var final: Long = __pytra_int(__pytra_ifexp((__pytra_int(pos + chunk_len) >= __pytra_int(n)), 1L, 0L))
        out.add(final)
        _png_append_list(out, _png_u16le(chunk_len))
        _png_append_list(out, _png_u16le((65535L xor chunk_len)))
        var i: Long = pos
        var end: Long = (pos + chunk_len)
        while ((__pytra_int(i) < __pytra_int(end))) {
            out.add(__pytra_int(__pytra_get_index(data, i)))
            i += 1L
        }
        pos += chunk_len
    }
    _png_append_list(out, _png_u32be(_adler32(data)))
    return out
}

fun _chunk(chunk_type: MutableList<Any?>, data: MutableList<Any?>): MutableList<Any?> {
    var crc_input: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    _png_append_list(crc_input, chunk_type)
    _png_append_list(crc_input, data)
    var crc: Long = (_crc32(crc_input) and 4294967295L)
    var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    _png_append_list(out, _png_u32be(__pytra_len(data)))
    _png_append_list(out, chunk_type)
    _png_append_list(out, data)
    _png_append_list(out, _png_u32be(crc))
    return out
}

fun write_rgb_png(path: String, width: Long, height: Long, pixels: MutableList<Any?>) {
    var raw: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __iter_0 = __pytra_as_list(pixels)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val b: Long = __pytra_int(__iter_0[__i_1.toInt()])
        raw.add(b)
        __i_1 += 1L
    }
    var expected: Long = ((width * height) * 3L)
    if ((__pytra_int(__pytra_len(raw)) != __pytra_int(expected))) {
        throw RuntimeException(__pytra_str((__pytra_str(__pytra_str(__pytra_str("pixels length mismatch: got=") + __pytra_str(__pytra_len(raw))) + __pytra_str(" expected=")) + __pytra_str(expected))))
    }
    var scanlines: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var row_bytes: Long = (width * 3L)
    var y: Long = 0L
    while ((__pytra_int(y) < __pytra_int(height))) {
        scanlines.add(0L)
        var start: Long = (y * row_bytes)
        var end: Long = (start + row_bytes)
        var i: Long = start
        while ((__pytra_int(i) < __pytra_int(end))) {
            scanlines.add(__pytra_int(__pytra_get_index(raw, i)))
            i += 1L
        }
        y += 1L
    }
    var ihdr: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    _png_append_list(ihdr, _png_u32be(width))
    _png_append_list(ihdr, _png_u32be(height))
    _png_append_list(ihdr, mutableListOf(8L, 2L, 0L, 0L, 0L))
    var idat: MutableList<Any?> = _zlib_deflate_store(scanlines)
    var png: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    _png_append_list(png, mutableListOf(137L, 80L, 78L, 71L, 13L, 10L, 26L, 10L))
    _png_append_list(png, _chunk(mutableListOf(73L, 72L, 68L, 82L), ihdr))
    _png_append_list(png, _chunk(mutableListOf(73L, 68L, 65L, 84L), idat))
    var iend_data: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    _png_append_list(png, _chunk(mutableListOf(73L, 69L, 78L, 68L), iend_data))
    var f: PyFile = open(path, "wb")
    f.write(__pytra_bytes(png))
    f.close()
}

fun main(args: Array<String>) {
}
