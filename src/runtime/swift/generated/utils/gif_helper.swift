// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func _gif_append_list(_ dst: [Any], _ src: [Any]) {
    var i: Int64 = Int64(0)
    var n: Int64 = __pytra_len(src)
    while (__pytra_int(i) < __pytra_int(n)) {
        dst.append(__pytra_int(__pytra_getIndex(src, i)))
        i += Int64(1)
    }
}

func _gif_u16le(_ v: Int64) -> [Any] {
    return __pytra_as_list([(v & Int64(255)), ((v >> Int64(8)) & Int64(255))])
}

func _lzw_encode(_ data: [Any], _ min_code_size: Int64) -> [Any] {
    if (__pytra_int(__pytra_len(data)) == __pytra_int(Int64(0))) {
        return __pytra_bytes([])
    }
    var clear_code: Int64 = (Int64(1) << min_code_size)
    var end_code: Int64 = (clear_code + Int64(1))
    var code_size: Int64 = (min_code_size + Int64(1))
    var out: [Any] = __pytra_as_list([])
    var bit_buffer: Int64 = Int64(0)
    var bit_count: Int64 = Int64(0)
    bit_buffer += (clear_code << bit_count)
    bit_count += code_size
    while (__pytra_int(bit_count) >= __pytra_int(Int64(8))) {
        out.append((bit_buffer & Int64(255)))
        bit_buffer = (bit_buffer >> Int64(8))
        bit_count -= Int64(8)
    }
    code_size = (min_code_size + Int64(1))
    do {
        let __iter_0 = __pytra_as_list(data)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let v: Int64 = __pytra_int(__iter_0[Int(__i_1)])
            bit_buffer += (v << bit_count)
            bit_count += code_size
            while (__pytra_int(bit_count) >= __pytra_int(Int64(8))) {
                out.append((bit_buffer & Int64(255)))
                bit_buffer = (bit_buffer >> Int64(8))
                bit_count -= Int64(8)
            }
            bit_buffer += (clear_code << bit_count)
            bit_count += code_size
            while (__pytra_int(bit_count) >= __pytra_int(Int64(8))) {
                out.append((bit_buffer & Int64(255)))
                bit_buffer = (bit_buffer >> Int64(8))
                bit_count -= Int64(8)
            }
            code_size = (min_code_size + Int64(1))
            __i_1 += 1
        }
    }
    bit_buffer += (end_code << bit_count)
    bit_count += code_size
    while (__pytra_int(bit_count) >= __pytra_int(Int64(8))) {
        out.append((bit_buffer & Int64(255)))
        bit_buffer = (bit_buffer >> Int64(8))
        bit_count -= Int64(8)
    }
    if (__pytra_int(bit_count) > __pytra_int(Int64(0))) {
        out.append((bit_buffer & Int64(255)))
    }
    return __pytra_bytes(out)
}

func grayscale_palette() -> [Any] {
    var p: [Any] = __pytra_as_list([])
    var i: Int64 = Int64(0)
    while (__pytra_int(i) < __pytra_int(Int64(256))) {
        p.append(i)
        p.append(i)
        p.append(i)
        i += Int64(1)
    }
    return __pytra_bytes(p)
}

func save_gif(_ path: String, _ width: Int64, _ height: Int64, _ frames: [Any], _ palette: [Any], _ delay_cs: Int64, _ loop: Int64) {
    if (__pytra_int(__pytra_len(palette)) != __pytra_int(Int64(256) * Int64(3))) {
        fatalError("pytra raise")
    }
    var frame_lists: [Any] = __pytra_as_list([])
    do {
        let __iter_0 = __pytra_as_list(frames)
        var __i_1: Int64 = 0
        while __i_1 < Int64(__iter_0.count) {
            let fr: [Any] = __pytra_as_list(__iter_0[Int(__i_1)])
            var fr_list: [Any] = __pytra_as_list([])
            do {
                let __iter_2 = __pytra_as_list(fr)
                var __i_3: Int64 = 0
                while __i_3 < Int64(__iter_2.count) {
                    let v: Int64 = __pytra_int(__iter_2[Int(__i_3)])
                    fr_list.append(v)
                    __i_3 += 1
                }
            }
            if (__pytra_int(__pytra_len(fr_list)) != __pytra_int(width * height)) {
                fatalError("pytra raise")
            }
            frame_lists.append(fr_list)
            __i_1 += 1
        }
    }
    var palette_list: [Any] = __pytra_as_list([])
    do {
        let __iter_4 = __pytra_as_list(palette)
        var __i_5: Int64 = 0
        while __i_5 < Int64(__iter_4.count) {
            let v: Int64 = __pytra_int(__iter_4[Int(__i_5)])
            palette_list.append(v)
            __i_5 += 1
        }
    }
    var out: [Any] = __pytra_as_list([])
    _gif_append_list(out, [Int64(71), Int64(73), Int64(70), Int64(56), Int64(57), Int64(97)])
    _gif_append_list(out, _gif_u16le(width))
    _gif_append_list(out, _gif_u16le(height))
    out.append(Int64(247))
    out.append(Int64(0))
    out.append(Int64(0))
    _gif_append_list(out, palette_list)
    _gif_append_list(out, [Int64(33), Int64(255), Int64(11), Int64(78), Int64(69), Int64(84), Int64(83), Int64(67), Int64(65), Int64(80), Int64(69), Int64(50), Int64(46), Int64(48), Int64(3), Int64(1)])
    _gif_append_list(out, _gif_u16le(loop))
    out.append(Int64(0))
    do {
        let __iter_6 = __pytra_as_list(frame_lists)
        var __i_7: Int64 = 0
        while __i_7 < Int64(__iter_6.count) {
            let fr_list: [Any] = __pytra_as_list(__iter_6[Int(__i_7)])
            _gif_append_list(out, [Int64(33), Int64(249), Int64(4), Int64(0)])
            _gif_append_list(out, _gif_u16le(delay_cs))
            _gif_append_list(out, [Int64(0), Int64(0)])
            out.append(Int64(44))
            _gif_append_list(out, _gif_u16le(Int64(0)))
            _gif_append_list(out, _gif_u16le(Int64(0)))
            _gif_append_list(out, _gif_u16le(width))
            _gif_append_list(out, _gif_u16le(height))
            out.append(Int64(0))
            out.append(Int64(8))
            var compressed: [Any] = _lzw_encode(__pytra_bytes(fr_list), Int64(8))
            var pos: Int64 = Int64(0)
            while (__pytra_int(pos) < __pytra_int(__pytra_len(compressed))) {
                var remain: Int64 = (__pytra_len(compressed) - pos)
                var chunk_len: Int64 = __pytra_int(__pytra_ifexp((__pytra_int(remain) > __pytra_int(Int64(255))), Int64(255), remain))
                out.append(chunk_len)
                var i: Int64 = Int64(0)
                while (__pytra_int(i) < __pytra_int(chunk_len)) {
                    out.append(__pytra_int(__pytra_getIndex(compressed, (pos + i))))
                    i += Int64(1)
                }
                pos += chunk_len
            }
            out.append(Int64(0))
            __i_7 += 1
        }
    }
    out.append(Int64(59))
    var f: PyFile = open(path, "wb")
    f.write(__pytra_bytes(out))
    f.close()
}

@main
struct Main {
    static func main() {
    }
}
