// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func _png_append_list(dst []any, src []any) {
    var i int64 = int64(0)
    var n int64 = __pytra_len(src)
    for (i < n) {
        dst = append(dst, __pytra_int(__pytra_get_index(src, i)))
        i += int64(1)
    }
}

func _crc32(data []any) int64 {
    var crc int64 = int64(4294967295)
    var poly int64 = int64(3988292384)
    __iter_0 := __pytra_as_list(data)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        var b int64 = __pytra_int(__iter_0[__i_1])
        crc = (crc ^ b)
        var i int64 = int64(0)
        for (i < int64(8)) {
            var lowbit int64 = (crc & int64(1))
            if (lowbit != int64(0)) {
                crc = ((crc >> int64(1)) ^ poly)
            } else {
                crc = (crc >> int64(1))
            }
            i += int64(1)
        }
    }
    return (crc ^ int64(4294967295))
}

func _adler32(data []any) int64 {
    var mod int64 = int64(65521)
    var s1 int64 = int64(1)
    var s2 int64 = int64(0)
    __iter_0 := __pytra_as_list(data)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        var b int64 = __pytra_int(__iter_0[__i_1])
        s1 += b
        if (s1 >= mod) {
            s1 -= mod
        }
        s2 += s1
        s2 = (s2 % mod)
    }
    return (((s2 << int64(16)) | s1) & int64(4294967295))
}

func _png_u16le(v int64) []any {
    return __pytra_as_list([]any{(v & int64(255)), ((v >> int64(8)) & int64(255))})
}

func _png_u32be(v int64) []any {
    return __pytra_as_list([]any{((v >> int64(24)) & int64(255)), ((v >> int64(16)) & int64(255)), ((v >> int64(8)) & int64(255)), (v & int64(255))})
}

func _zlib_deflate_store(data []any) []any {
    var out []any = __pytra_as_list([]any{})
    out = append(out, []any{int64(120), int64(1)}...)
    var n int64 = __pytra_len(data)
    var pos int64 = int64(0)
    for (pos < n) {
        var remain int64 = (n - pos)
        var chunk_len int64 = __pytra_int(__pytra_ifexp((remain > int64(65535)), int64(65535), remain))
        var final int64 = __pytra_int(__pytra_ifexp(((pos + chunk_len) >= n), int64(1), int64(0)))
        out = append(out, final)
        out = append(out, _png_u16le(chunk_len)...)
        out = append(out, _png_u16le((int64(65535) ^ chunk_len))...)
        var i int64 = pos
        var end int64 = (pos + chunk_len)
        for (i < end) {
            out = append(out, __pytra_int(__pytra_get_index(data, i)))
            i += int64(1)
        }
        pos += chunk_len
    }
    out = append(out, _png_u32be(_adler32(data))...)
    return __pytra_as_list(out)
}

func _chunk(chunk_type []any, data []any) []any {
    var crc_input []any = __pytra_as_list([]any{})
    crc_input = append(crc_input, chunk_type...)
    crc_input = append(crc_input, data...)
    var crc int64 = (_crc32(crc_input) & int64(4294967295))
    var out []any = __pytra_as_list([]any{})
    out = append(out, _png_u32be(__pytra_len(data))...)
    out = append(out, chunk_type...)
    out = append(out, data...)
    out = append(out, _png_u32be(crc)...)
    return __pytra_as_list(out)
}

func write_rgb_png(path string, width int64, height int64, pixels []any) {
    var raw []any = __pytra_as_list([]any{})
    __iter_0 := __pytra_as_list(pixels)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        var b int64 = __pytra_int(__iter_0[__i_1])
        raw = append(raw, __pytra_int(b))
    }
    var expected int64 = ((width * height) * int64(3))
    if (__pytra_len(raw) != expected) {
        panic(__pytra_str((__pytra_str((__pytra_str((__pytra_str("pixels length mismatch: got=") + __pytra_str(__pytra_str(__pytra_len(raw))))) + __pytra_str(" expected="))) + __pytra_str(__pytra_str(expected)))))
    }
    var scanlines []any = __pytra_as_list([]any{})
    var row_bytes int64 = (width * int64(3))
    var y int64 = int64(0)
    for (y < height) {
        scanlines = append(scanlines, int64(0))
        var start int64 = (y * row_bytes)
        var end int64 = (start + row_bytes)
        var i int64 = start
        for (i < end) {
            scanlines = append(scanlines, __pytra_int(__pytra_get_index(raw, i)))
            i += int64(1)
        }
        y += int64(1)
    }
    var ihdr []any = __pytra_as_list([]any{})
    ihdr = append(ihdr, _png_u32be(width)...)
    ihdr = append(ihdr, _png_u32be(height)...)
    ihdr = append(ihdr, []any{int64(8), int64(2), int64(0), int64(0), int64(0)}...)
    var idat []any = __pytra_as_list(_zlib_deflate_store(scanlines))
    var png []any = __pytra_as_list([]any{})
    png = append(png, []any{int64(137), int64(80), int64(78), int64(71), int64(13), int64(10), int64(26), int64(10)}...)
    png = append(png, _chunk([]any{int64(73), int64(72), int64(68), int64(82)}, ihdr)...)
    png = append(png, _chunk([]any{int64(73), int64(68), int64(65), int64(84)}, idat)...)
    var iend_data []any = __pytra_as_list([]any{})
    png = append(png, _chunk([]any{int64(73), int64(69), int64(78), int64(68)}, iend_data)...)
    f := open(path, "wb")
    f.write(__pytra_bytes(png))
    f.close()
}
