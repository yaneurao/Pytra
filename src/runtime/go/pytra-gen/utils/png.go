// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// generated-by: tools/gen_runtime_from_manifest.py

package main


func _crc32(data []any) int64 {
    var crc int64 = int64(4294967295)
    var poly int64 = int64(3988292384)
    __iter_0 := __pytra_as_list(data)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        var b int64 = __pytra_int(__iter_0[__i_1])
        crc += b
        var i int64 = int64(0)
        for (i < int64(8)) {
            if ((crc & int64(1)) != int64(0)) {
                crc = ((crc >> int64(1)) ^ poly)
            } else {
                crc += int64(1)
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
        s2 %= mod
    }
    return (((s2 << int64(16)) | s1) & int64(4294967295))
}

func _u16le(v int64) []any {
    return __pytra_as_list(__pytra_bytes([]any{(v & int64(255)), ((v >> int64(8)) & int64(255))}))
}

func _u32be(v int64) []any {
    return __pytra_as_list(__pytra_bytes([]any{((v >> int64(24)) & int64(255)), ((v >> int64(16)) & int64(255)), ((v >> int64(8)) & int64(255)), (v & int64(255))}))
}

func _zlib_deflate_store(data []any) []any {
    var out []any = __pytra_as_list([]any{})
    out.extend(__pytra_bytes([]any{int64(120), int64(1)}))
    var n int64 = __pytra_len(data)
    var pos int64 = int64(0)
    for (pos < n) {
        var remain int64 = (n - pos)
        var chunk_len int64 = __pytra_int(__pytra_ifexp((remain > int64(65535)), int64(65535), remain))
        var final int64 = __pytra_int(__pytra_ifexp(((pos + chunk_len) >= n), int64(1), int64(0)))
        out = append(out, final)
        out.extend(_u16le(chunk_len))
        out.extend(_u16le((int64(65535) ^ chunk_len)))
        out.extend(__pytra_slice(data, pos, (pos + chunk_len)))
        pos += chunk_len
    }
    out.extend(_u32be(_adler32(data)))
    return __pytra_as_list(__pytra_bytes(out))
}

func _chunk(chunk_type []any, data []any) []any {
    var length []any = __pytra_as_list(_u32be(__pytra_len(data)))
    var crc int64 = (_crc32((chunk_type + data)) & int64(4294967295))
    return __pytra_as_list((((length + chunk_type) + data) + _u32be(crc)))
}

func write_rgb_png(path string, width int64, height int64, pixels any) {
    var raw []any = __pytra_as_list(__pytra_bytes(pixels))
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
        scanlines.extend(__pytra_slice(raw, start, end))
        y += int64(1)
    }
    var ihdr []any = __pytra_as_list(((_u32be(width) + _u32be(height)) + __pytra_bytes([]any{int64(8), int64(2), int64(0), int64(0), int64(0)})))
    var idat []any = __pytra_as_list(_zlib_deflate_store(__pytra_bytes(scanlines)))
    var png []any = __pytra_as_list([]any{})
    png.extend(__pytra_bytes([]any{int64(137), int64(80), int64(78), int64(71), int64(13), int64(10), int64(26), int64(10)}))
    png.extend(_chunk(__pytra_bytes([]any{int64(73), int64(72), int64(68), int64(82)}), ihdr))
    png.extend(_chunk(__pytra_bytes([]any{int64(73), int64(68), int64(65), int64(84)}), idat))
    png.extend(_chunk(__pytra_bytes([]any{int64(73), int64(69), int64(78), int64(68)}), ""))
    _ = open(path, "wb")
    f.write(png)
    f.close()
}

func main() {
}
