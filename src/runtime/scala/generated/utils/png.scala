// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def _png_append_list(dst: mutable.ArrayBuffer[Long], src: mutable.ArrayBuffer[Long]): Unit = {
    var i: Long = 0L
    var n: Long = __pytra_len(src)
    while (i < n) {
        dst.append(__pytra_int(__pytra_get_index(src, i)))
        i += 1L
    }
}

def _crc32(data: mutable.ArrayBuffer[Long]): Long = {
    var crc: Long = 4294967295L
    var poly: Long = 3988292384L
    val __iter_0 = __pytra_as_list(data)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong) {
        val b: Long = __pytra_int(__iter_0(__i_1.toInt))
        crc = crc ^ b
        var i: Long = 0L
        while (i < 8L) {
            var lowbit: Long = crc & 1L
            if (lowbit != 0L) {
                crc = (crc >> 1L ^ poly)
            } else {
                crc = crc >> 1L
            }
            i += 1L
        }
        __i_1 += 1L
    }
    return crc ^ 4294967295L
}

def _adler32(data: mutable.ArrayBuffer[Long]): Long = {
    var mod: Long = 65521L
    var s1: Long = 1L
    var s2: Long = 0L
    val __iter_0 = __pytra_as_list(data)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong) {
        val b: Long = __pytra_int(__iter_0(__i_1.toInt))
        s1 += b
        if (s1 >= mod) {
            s1 -= mod
        }
        s2 += s1
        s2 = s2 % mod
        __i_1 += 1L
    }
    return (((s2 << 16L | s1)) & 4294967295L)
}

def _png_u16le(v: Long): mutable.ArrayBuffer[Long] = {
    return __pytra_as_list(mutable.ArrayBuffer[Long](v & 255L, (v >> 8L & 255L))).asInstanceOf[mutable.ArrayBuffer[Long]]
}

def _png_u32be(v: Long): mutable.ArrayBuffer[Long] = {
    return __pytra_as_list(mutable.ArrayBuffer[Long]((v >> 24L & 255L), (v >> 16L & 255L), (v >> 8L & 255L), v & 255L)).asInstanceOf[mutable.ArrayBuffer[Long]]
}

def _zlib_deflate_store(data: mutable.ArrayBuffer[Long]): mutable.ArrayBuffer[Long] = {
    var out: mutable.ArrayBuffer[Long] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Long]]
    _png_append_list(out, mutable.ArrayBuffer[Long](120L, 1L))
    var n: Long = __pytra_len(data)
    var pos: Long = 0L
    while (pos < n) {
        var remain: Long = n - pos
        var chunk_len: Long = __pytra_int(__pytra_ifexp((remain > 65535L), 65535L, remain))
        var py_final: Long = __pytra_int(__pytra_ifexp((pos + chunk_len >= n), 1L, 0L))
        out.append(py_final)
        _png_append_list(out, _png_u16le(chunk_len))
        _png_append_list(out, _png_u16le(65535L ^ chunk_len))
        var i: Long = pos
        var end: Long = pos + chunk_len
        while (i < end) {
            out.append(__pytra_int(__pytra_get_index(data, i)))
            i += 1L
        }
        pos += chunk_len
    }
    _png_append_list(out, _png_u32be(_adler32(data)))
    return out
}

def _chunk(chunk_type: mutable.ArrayBuffer[Long], data: mutable.ArrayBuffer[Long]): mutable.ArrayBuffer[Long] = {
    var crc_input: mutable.ArrayBuffer[Long] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Long]]
    _png_append_list(crc_input, chunk_type)
    _png_append_list(crc_input, data)
    var crc: Long = _crc32(crc_input) & 4294967295L
    var out: mutable.ArrayBuffer[Long] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Long]]
    _png_append_list(out, _png_u32be(__pytra_len(data)))
    _png_append_list(out, chunk_type)
    _png_append_list(out, data)
    _png_append_list(out, _png_u32be(crc))
    return out
}

def write_rgb_png(path: String, width: Long, height: Long, pixels: mutable.ArrayBuffer[Long]): Unit = {
    var raw: mutable.ArrayBuffer[Long] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Long]]
    val __iter_0 = __pytra_as_list(pixels)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong) {
        val b: Long = __pytra_int(__iter_0(__i_1.toInt))
        raw.append(b)
        __i_1 += 1L
    }
    var expected: Long = (width * height * 3L)
    if (__pytra_len(raw) != expected) {
        throw new RuntimeException(__pytra_str((__pytra_str(__pytra_str(__pytra_str("pixels length mismatch: got=") + __pytra_str(__pytra_len(raw))) + __pytra_str(" expected=")) + __pytra_str(expected))))
    }
    var scanlines: mutable.ArrayBuffer[Long] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Long]]
    var row_bytes: Long = width * 3L
    var y: Long = 0L
    while (y < height) {
        scanlines.append(0L)
        var start: Long = y * row_bytes
        var end: Long = start + row_bytes
        var i: Long = start
        while (i < end) {
            scanlines.append(__pytra_int(__pytra_get_index(raw, i)))
            i += 1L
        }
        y += 1L
    }
    var ihdr: mutable.ArrayBuffer[Long] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Long]]
    _png_append_list(ihdr, _png_u32be(width))
    _png_append_list(ihdr, _png_u32be(height))
    _png_append_list(ihdr, mutable.ArrayBuffer[Long](8L, 2L, 0L, 0L, 0L))
    var idat: mutable.ArrayBuffer[Long] = _zlib_deflate_store(scanlines)
    var png: mutable.ArrayBuffer[Long] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Long]]
    _png_append_list(png, mutable.ArrayBuffer[Long](137L, 80L, 78L, 71L, 13L, 10L, 26L, 10L))
    _png_append_list(png, _chunk(mutable.ArrayBuffer[Long](73L, 72L, 68L, 82L), ihdr))
    _png_append_list(png, _chunk(mutable.ArrayBuffer[Long](73L, 68L, 65L, 84L), idat))
    var iend_data: mutable.ArrayBuffer[Long] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Long]]
    _png_append_list(png, _chunk(mutable.ArrayBuffer[Long](73L, 69L, 78L, 68L), iend_data))
    var f: PyFile = open(path, "wb")
    try {
        f.write(__pytra_bytes(png))
    } finally {
        f.close()
    }
}

def main(args: Array[String]): Unit = {
}