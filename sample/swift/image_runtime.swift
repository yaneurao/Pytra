// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// source: src/pytra/utils/gif.py
// generated-by: tools/gen_image_runtime_from_canonical.py

import Foundation
func __pytra_to_u8(_ v: Any?) -> UInt8 {
    let n = __pytra_int(v)
    if n < 0 { return 0 }
    if n > 255 { return 255 }
    return UInt8(n)
}

func __pytra_append_u32be(_ out: inout [UInt8], _ value: UInt32) {
    out.append(UInt8((value >> 24) & 0xFF))
    out.append(UInt8((value >> 16) & 0xFF))
    out.append(UInt8((value >> 8) & 0xFF))
    out.append(UInt8(value & 0xFF))
}

func __pytra_crc32(_ data: [UInt8]) -> UInt32 {
    var crc: UInt32 = 0xFFFFFFFF
    for b in data {
        var x = crc ^ UInt32(b)
        var i = 0
        while i < 8 {
            if (x & 1) != 0 {
                x = (x >> 1) ^ 0xEDB88320
            } else {
                x >>= 1
            }
            i += 1
        }
        crc = x
    }
    return crc ^ 0xFFFFFFFF
}

func __pytra_adler32(_ data: [UInt8]) -> UInt32 {
    var s1: UInt32 = 1
    var s2: UInt32 = 0
    for b in data {
        s1 = (s1 + UInt32(b)) % 65521
        s2 = (s2 + s1) % 65521
    }
    return (s2 << 16) | s1
}

func __pytra_zlib_store(_ data: [UInt8]) -> [UInt8] {
    var out: [UInt8] = [0x78, 0x01]
    var pos = 0
    while pos < data.count {
        let remain = data.count - pos
        let chunkLen = min(65535, remain)
        let isFinal: UInt8 = (pos + chunkLen >= data.count) ? 1 : 0
        out.append(isFinal)

        let len = UInt16(chunkLen)
        out.append(UInt8(len & 0xFF))
        out.append(UInt8((len >> 8) & 0xFF))
        let nlen = ~len
        out.append(UInt8(nlen & 0xFF))
        out.append(UInt8((nlen >> 8) & 0xFF))

        out.append(contentsOf: data[pos..<(pos + chunkLen)])
        pos += chunkLen
    }
    __pytra_append_u32be(&out, __pytra_adler32(data))
    return out
}

func __pytra_png_chunk(_ kind: [UInt8], _ payload: [UInt8]) -> [UInt8] {
    var out: [UInt8] = []
    __pytra_append_u32be(&out, UInt32(payload.count))
    out.append(contentsOf: kind)
    out.append(contentsOf: payload)
    var crcInput = kind
    crcInput.append(contentsOf: payload)
    __pytra_append_u32be(&out, __pytra_crc32(crcInput))
    return out
}

func __pytra_write_rgb_png(_ path: Any?, _ width: Any?, _ height: Any?, _ pixels: Any?) {
    let outPath = __pytra_str(path)
    let w = Int(__pytra_int(width))
    let h = Int(__pytra_int(height))
    if w <= 0 || h <= 0 {
        return
    }

    let raw = __pytra_as_list(pixels)
    let expected = w * h * 3
    if raw.count < expected {
        return
    }

    var scanlines: [UInt8] = []
    scanlines.reserveCapacity(h * (1 + w * 3))
    var idx = 0
    var y = 0
    while y < h {
        scanlines.append(0)
        var x = 0
        while x < w {
            scanlines.append(__pytra_to_u8(raw[idx]))
            scanlines.append(__pytra_to_u8(raw[idx + 1]))
            scanlines.append(__pytra_to_u8(raw[idx + 2]))
            idx += 3
            x += 1
        }
        y += 1
    }

    var ihdr: [UInt8] = []
    __pytra_append_u32be(&ihdr, UInt32(w))
    __pytra_append_u32be(&ihdr, UInt32(h))
    ihdr.append(contentsOf: [8, 2, 0, 0, 0])
    let idat = __pytra_zlib_store(scanlines)

    var png: [UInt8] = [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]
    png.append(contentsOf: __pytra_png_chunk([0x49, 0x48, 0x44, 0x52], ihdr))
    png.append(contentsOf: __pytra_png_chunk([0x49, 0x44, 0x41, 0x54], idat))
    png.append(contentsOf: __pytra_png_chunk([0x49, 0x45, 0x4E, 0x44], []))

    let outURL = URL(fileURLWithPath: outPath)
    let parent = outURL.deletingLastPathComponent()
    if parent.path != "" && parent.path != "." {
        try? FileManager.default.createDirectory(at: parent, withIntermediateDirectories: true)
    }
    try? Data(png).write(to: outURL)
}

func __pytra_to_bytes(_ v: Any?) -> [UInt8] {
    if let arr = v as? [UInt8] {
        return arr
    }
    if let arr = v as? [Any] {
        var out: [UInt8] = []
        out.reserveCapacity(arr.count)
        for item in arr {
            out.append(__pytra_to_u8(item))
        }
        return out
    }
    if let data = v as? Data {
        return [UInt8](data)
    }
    if let s = v as? String {
        return [UInt8](s.utf8)
    }
    return []
}

func __pytra_lzw_encode(_ data: [UInt8], _ minCodeSize: Int = 8) -> [UInt8] {
    if data.isEmpty {
        return []
    }
    let clearCode = 1 << minCodeSize
    let endCode = clearCode + 1
    let codeSize = minCodeSize + 1

    var out: [UInt8] = []
    var bitBuffer = 0
    var bitCount = 0

    func emit(_ code: Int) {
        bitBuffer |= (code << bitCount)
        bitCount += codeSize
        while bitCount >= 8 {
            out.append(UInt8(bitBuffer & 0xFF))
            bitBuffer >>= 8
            bitCount -= 8
        }
    }

    emit(clearCode)
    for v in data {
        emit(Int(v))
        emit(clearCode)
    }
    emit(endCode)
    if bitCount > 0 {
        out.append(UInt8(bitBuffer & 0xFF))
    }
    return out
}

func __pytra_append_u16le(_ out: inout [UInt8], _ value: Int) {
    let v = UInt16(truncatingIfNeeded: value)
    out.append(UInt8(v & 0xFF))
    out.append(UInt8((v >> 8) & 0xFF))
}

func __pytra_grayscale_palette() -> [Any] {
    var p: [Any] = []
    p.reserveCapacity(256 * 3)
    var i: Int64 = 0
    while i < 256 {
        p.append(i)
        p.append(i)
        p.append(i)
        i += 1
    }
    return p
}

func __pytra_save_gif(
    _ path: Any?,
    _ width: Any?,
    _ height: Any?,
    _ frames: Any?,
    _ palette: Any?,
    _ delayCs: Any? = Int64(4),
    _ loop: Any? = Int64(0)
) {
    let outPath = __pytra_str(path)
    let w = Int(__pytra_int(width))
    let h = Int(__pytra_int(height))
    if w <= 0 || h <= 0 {
        return
    }

    let pal = __pytra_to_bytes(palette)
    if pal.count != 256 * 3 {
        return
    }

    let frameBytes = w * h
    let dcs = Int(__pytra_int(delayCs))
    let lp = Int(__pytra_int(loop))
    let frs = __pytra_as_list(frames)

    var out: [UInt8] = []
    out.append(contentsOf: [UInt8]("GIF89a".utf8))
    __pytra_append_u16le(&out, w)
    __pytra_append_u16le(&out, h)
    out.append(0xF7)
    out.append(0)
    out.append(0)
    out.append(contentsOf: pal)
    out.append(contentsOf: [0x21, 0xFF, 0x0B])
    out.append(contentsOf: [UInt8]("NETSCAPE2.0".utf8))
    out.append(0x03)
    out.append(0x01)
    __pytra_append_u16le(&out, lp)
    out.append(0x00)

    for frAny in frs {
        let fr = __pytra_to_bytes(frAny)
        if fr.count != frameBytes {
            return
        }
        out.append(contentsOf: [0x21, 0xF9, 0x04, 0x00])
        __pytra_append_u16le(&out, dcs)
        out.append(0x00)
        out.append(0x00)
        out.append(0x2C)
        __pytra_append_u16le(&out, 0)
        __pytra_append_u16le(&out, 0)
        __pytra_append_u16le(&out, w)
        __pytra_append_u16le(&out, h)
        out.append(0x00)
        out.append(0x08)

        let compressed = __pytra_lzw_encode(fr, 8)
        var pos = 0
        while pos < compressed.count {
            let len = min(255, compressed.count - pos)
            out.append(UInt8(len))
            out.append(contentsOf: compressed[pos..<(pos + len)])
            pos += len
        }
        out.append(0x00)
    }
    out.append(0x3B)

    let outURL = URL(fileURLWithPath: outPath)
    let parent = outURL.deletingLastPathComponent()
    if parent.path != "" && parent.path != "." {
        try? FileManager.default.createDirectory(at: parent, withIntermediateDirectories: true)
    }
    try? Data(out).write(to: outURL)
}

func __pytra_bytearray(_ initValue: Any?) -> [Any] {
    if let i = initValue as? Int64 {
        return Array(repeating: Int64(0), count: max(0, Int(i)))
    }
    if let i = initValue as? Int {
        return Array(repeating: Int64(0), count: max(0, i))
    }
    if let arr = initValue as? [Any] {
        return arr
    }
    return []
}

func __pytra_bytes(_ v: Any?) -> [Any] {
    if let arr = v as? [Any] {
        return arr
    }
    return []
}

func __pytra_list_repeat(_ value: Any, _ count: Any?) -> [Any] {
    var out: [Any] = []
    var i: Int64 = 0
    let n = __pytra_int(count)
    while i < n {
        out.append(value)
        i += 1
    }
    return out
}

func __pytra_as_list(_ v: Any?) -> [Any] {
    if let arr = v as? [Any] { return arr }
    return []
}

func __pytra_as_u8_list(_ v: Any?) -> [UInt8] {
    if let arr = v as? [UInt8] { return arr }
    return []
}

func __pytra_as_dict(_ v: Any?) -> [AnyHashable: Any] {
    if let dict = v as? [AnyHashable: Any] { return dict }
    return [:]
}

func __pytra_dict_get(_ dictAny: Any?, _ key: Any?, _ defaultValue: Any?) -> Any {
    if let dict = dictAny as? [AnyHashable: Any] {
        let k = AnyHashable(__pytra_str(key))
        if let v = dict[k] {
            return v
        }
    }
    return defaultValue as Any
}

func __pytra_enumerate(_ v: Any?) -> [Any] {
    let arr = __pytra_as_list(v)
    var out: [Any] = []
    out.reserveCapacity(arr.count)
    var i: Int64 = 0
    while i < Int64(arr.count) {
        out.append([i, arr[Int(i)]])
        i += 1
    }
    return out
}

