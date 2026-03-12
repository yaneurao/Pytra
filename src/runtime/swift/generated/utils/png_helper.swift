// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func _png_append_list(_ dst: [Any], _ src: [Any]) {
    var i: Int64 = Int64(0)
    var n: Int64 = __pytra_len(src)
    while (__pytra_int(i) < __pytra_int(n)) {
        dst.append(__pytra_int(__pytra_getIndex(src, i)))
        i += Int64(1)
    }
}

func _crc32(_ data: [Any]) -> Int64 {
    var crc: Int64 = Int64(4294967295)
    var poly: Int64 = Int64(3988292384)
    do {
        let __iter_0 = __pytra_as_list(data)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let b: Int64 = __pytra_int(__iter_0[Int(__i_1)])
            crc = (crc ^ b)
            var i: Int64 = Int64(0)
            while (__pytra_int(i) < __pytra_int(Int64(8))) {
                var lowbit: Int64 = (crc & Int64(1))
                if (__pytra_int(lowbit) != __pytra_int(Int64(0))) {
                    crc = ((crc >> Int64(1)) ^ poly)
                } else {
                    crc = (crc >> Int64(1))
                }
                i += Int64(1)
            }
            __i_1 += 1
        }
    }
    return (crc ^ Int64(4294967295))
}

func _adler32(_ data: [Any]) -> Int64 {
    var mod: Int64 = Int64(65521)
    var s1: Int64 = Int64(1)
    var s2: Int64 = Int64(0)
    do {
        let __iter_0 = __pytra_as_list(data)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let b: Int64 = __pytra_int(__iter_0[Int(__i_1)])
            s1 += b
            if (__pytra_int(s1) >= __pytra_int(mod)) {
                s1 -= mod
            }
            s2 += s1
            s2 = (s2 % mod)
            __i_1 += 1
        }
    }
    return (((s2 << Int64(16)) | s1) & Int64(4294967295))
}

func _png_u16le(_ v: Int64) -> [Any] {
    return __pytra_as_list([(v & Int64(255)), ((v >> Int64(8)) & Int64(255))])
}

func _png_u32be(_ v: Int64) -> [Any] {
    return __pytra_as_list([((v >> Int64(24)) & Int64(255)), ((v >> Int64(16)) & Int64(255)), ((v >> Int64(8)) & Int64(255)), (v & Int64(255))])
}

func _zlib_deflate_store(_ data: [Any]) -> [Any] {
    var out: [Any] = __pytra_as_list([])
    _png_append_list(out, [Int64(120), Int64(1)])
    var n: Int64 = __pytra_len(data)
    var pos: Int64 = Int64(0)
    while (__pytra_int(pos) < __pytra_int(n)) {
        var remain: Int64 = (n - pos)
        var chunk_len: Int64 = __pytra_int(__pytra_ifexp((__pytra_int(remain) > __pytra_int(Int64(65535))), Int64(65535), remain))
        var final: Int64 = __pytra_int(__pytra_ifexp((__pytra_int(pos + chunk_len) >= __pytra_int(n)), Int64(1), Int64(0)))
        out.append(final)
        _png_append_list(out, _png_u16le(chunk_len))
        _png_append_list(out, _png_u16le((Int64(65535) ^ chunk_len)))
        var i: Int64 = pos
        var end: Int64 = (pos + chunk_len)
        while (__pytra_int(i) < __pytra_int(end)) {
            out.append(__pytra_int(__pytra_getIndex(data, i)))
            i += Int64(1)
        }
        pos += chunk_len
    }
    _png_append_list(out, _png_u32be(_adler32(data)))
    return out
}

func _chunk(_ chunk_type: [Any], _ data: [Any]) -> [Any] {
    var crc_input: [Any] = __pytra_as_list([])
    _png_append_list(crc_input, chunk_type)
    _png_append_list(crc_input, data)
    var crc: Int64 = (_crc32(crc_input) & Int64(4294967295))
    var out: [Any] = __pytra_as_list([])
    _png_append_list(out, _png_u32be(__pytra_len(data)))
    _png_append_list(out, chunk_type)
    _png_append_list(out, data)
    _png_append_list(out, _png_u32be(crc))
    return out
}

func write_rgb_png(_ path: String, _ width: Int64, _ height: Int64, _ pixels: [Any]) {
    var raw: [Any] = __pytra_as_list([])
    do {
        let __iter_0 = __pytra_as_list(pixels)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let b: Int64 = __pytra_int(__iter_0[Int(__i_1)])
            raw.append(b)
            __i_1 += 1
        }
    }
    var expected: Int64 = ((width * height) * Int64(3))
    if (__pytra_int(__pytra_len(raw)) != __pytra_int(expected)) {
        fatalError("pytra raise")
    }
    var scanlines: [Any] = __pytra_as_list([])
    var row_bytes: Int64 = (width * Int64(3))
    var y: Int64 = Int64(0)
    while (__pytra_int(y) < __pytra_int(height)) {
        scanlines.append(Int64(0))
        var start: Int64 = (y * row_bytes)
        var end: Int64 = (start + row_bytes)
        var i: Int64 = start
        while (__pytra_int(i) < __pytra_int(end)) {
            scanlines.append(__pytra_int(__pytra_getIndex(raw, i)))
            i += Int64(1)
        }
        y += Int64(1)
    }
    var ihdr: [Any] = __pytra_as_list([])
    _png_append_list(ihdr, _png_u32be(width))
    _png_append_list(ihdr, _png_u32be(height))
    _png_append_list(ihdr, [Int64(8), Int64(2), Int64(0), Int64(0), Int64(0)])
    var idat: [Any] = _zlib_deflate_store(scanlines)
    var png: [Any] = __pytra_as_list([])
    _png_append_list(png, [Int64(137), Int64(80), Int64(78), Int64(71), Int64(13), Int64(10), Int64(26), Int64(10)])
    _png_append_list(png, _chunk([Int64(73), Int64(72), Int64(68), Int64(82)], ihdr))
    _png_append_list(png, _chunk([Int64(73), Int64(68), Int64(65), Int64(84)], idat))
    var iend_data: [Any] = __pytra_as_list([])
    _png_append_list(png, _chunk([Int64(73), Int64(69), Int64(78), Int64(68)], iend_data))
    var f: PyFile = open(path, "wb")
    f.write(__pytra_bytes(png))
    f.close()
}

@main
struct Main {
    static func main() {
    }
}
