// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// source: src/pytra/utils/gif.py
// generated-by: tools/gen_image_runtime_from_canonical.py

import scala.collection.mutable
import java.nio.file.{Files, Paths}

def __pytra_to_byte(v: Any): Int = {
    (__pytra_int(v) & 0xFFL).toInt
}

def __pytra_to_byte_buffer(v: Any): mutable.ArrayBuffer[Byte] = {
    val src = __pytra_as_list(v)
    val out = mutable.ArrayBuffer[Byte]()
    var i = 0
    while (i < src.size) {
        out.append(__pytra_to_byte(src(i)).toByte)
        i += 1
    }
    out
}

def __pytra_append_u16le(out: mutable.ArrayBuffer[Byte], value: Int): Unit = {
    out.append((value & 0xFF).toByte)
    out.append(((value >>> 8) & 0xFF).toByte)
}

def __pytra_append_u32be(out: mutable.ArrayBuffer[Byte], value: Int): Unit = {
    out.append(((value >>> 24) & 0xFF).toByte)
    out.append(((value >>> 16) & 0xFF).toByte)
    out.append(((value >>> 8) & 0xFF).toByte)
    out.append((value & 0xFF).toByte)
}

def __pytra_crc32(data: mutable.ArrayBuffer[Byte]): Int = {
    var crc = 0xFFFFFFFFL
    val poly = 0xEDB88320L
    var i = 0
    while (i < data.size) {
        crc ^= (data(i) & 0xFF).toLong
        var j = 0
        while (j < 8) {
            if ((crc & 1L) != 0L) crc = (crc >>> 1) ^ poly
            else crc = crc >>> 1
            j += 1
        }
        i += 1
    }
    (crc ^ 0xFFFFFFFFL).toInt
}

def __pytra_adler32(data: mutable.ArrayBuffer[Byte]): Int = {
    val mod = 65521
    var s1 = 1
    var s2 = 0
    var i = 0
    while (i < data.size) {
        s1 += (data(i) & 0xFF)
        if (s1 >= mod) s1 -= mod
        s2 += s1
        s2 %= mod
        i += 1
    }
    ((s2 << 16) | s1) & 0xFFFFFFFF
}

def __pytra_zlib_deflate_store(data: mutable.ArrayBuffer[Byte]): mutable.ArrayBuffer[Byte] = {
    val out = mutable.ArrayBuffer[Byte](0x78.toByte, 0x01.toByte)
    val n = data.size
    var pos = 0
    while (pos < n) {
        val remain = n - pos
        val chunkLen = if (remain > 65535) 65535 else remain
        val finalFlag = if ((pos + chunkLen) >= n) 1 else 0
        out.append(finalFlag.toByte)
        __pytra_append_u16le(out, chunkLen)
        __pytra_append_u16le(out, 0xFFFF ^ chunkLen)
        var i = 0
        while (i < chunkLen) {
            out.append(data(pos + i))
            i += 1
        }
        pos += chunkLen
    }
    __pytra_append_u32be(out, __pytra_adler32(data))
    out
}

def __pytra_png_chunk(chunkType: String, data: mutable.ArrayBuffer[Byte]): mutable.ArrayBuffer[Byte] = {
    val out = mutable.ArrayBuffer[Byte]()
    __pytra_append_u32be(out, data.size)
    val ct = chunkType.getBytes("US-ASCII")
    val crcData = mutable.ArrayBuffer[Byte]()
    var i = 0
    while (i < ct.length) {
        out.append(ct(i))
        crcData.append(ct(i))
        i += 1
    }
    i = 0
    while (i < data.size) {
        out.append(data(i))
        crcData.append(data(i))
        i += 1
    }
    __pytra_append_u32be(out, __pytra_crc32(crcData))
    out
}

def __pytra_write_file_bytes(path: Any, data: mutable.ArrayBuffer[Byte]): Unit = {
    val p = Paths.get(__pytra_str(path))
    val parent = p.getParent
    if (parent != null) Files.createDirectories(parent)
    Files.write(p, data.toArray)
}

def __pytra_grayscale_palette(): mutable.ArrayBuffer[Any] = {
    val p = mutable.ArrayBuffer[Any]()
    var i = 0L
    while (i < 256L) {
        p.append(i)
        p.append(i)
        p.append(i)
        i += 1L
    }
    p
}

def __pytra_write_rgb_png(path: Any, width: Any, height: Any, pixels: Any): Unit = {
    val w = __pytra_int(width).toInt
    val h = __pytra_int(height).toInt
    val raw = __pytra_to_byte_buffer(pixels)
    val expected = w * h * 3
    if (raw.size != expected) {
        throw new RuntimeException("pixels length mismatch")
    }
    val scanlines = mutable.ArrayBuffer[Byte]()
    val rowBytes = w * 3
    var y = 0
    while (y < h) {
        scanlines.append(0.toByte)
        val start = y * rowBytes
        var x = 0
        while (x < rowBytes) {
            scanlines.append(raw(start + x))
            x += 1
        }
        y += 1
    }
    val ihdr = mutable.ArrayBuffer[Byte]()
    __pytra_append_u32be(ihdr, w)
    __pytra_append_u32be(ihdr, h)
    ihdr.append(8.toByte)
    ihdr.append(2.toByte)
    ihdr.append(0.toByte)
    ihdr.append(0.toByte)
    ihdr.append(0.toByte)
    val idat = __pytra_zlib_deflate_store(scanlines)
    val png = mutable.ArrayBuffer[Byte](0x89.toByte, 'P'.toByte, 'N'.toByte, 'G'.toByte, 0x0D.toByte, 0x0A.toByte, 0x1A.toByte, 0x0A.toByte)
    png ++= __pytra_png_chunk("IHDR", ihdr)
    png ++= __pytra_png_chunk("IDAT", idat)
    png ++= __pytra_png_chunk("IEND", mutable.ArrayBuffer[Byte]())
    __pytra_write_file_bytes(path, png)
}

def __pytra_gif_lzw_encode(data: mutable.ArrayBuffer[Byte], minCodeSize: Int = 8): mutable.ArrayBuffer[Byte] = {
    if (data.isEmpty) return mutable.ArrayBuffer[Byte]()
    val clearCode = 1 << minCodeSize
    val endCode = clearCode + 1
    var codeSize = minCodeSize + 1
    val out = mutable.ArrayBuffer[Byte]()
    var bitBuffer = 0
    var bitCount = 0
    def writeCode(code: Int): Unit = {
        bitBuffer |= (code << bitCount)
        bitCount += codeSize
        while (bitCount >= 8) {
            out.append((bitBuffer & 0xFF).toByte)
            bitBuffer = bitBuffer >>> 8
            bitCount -= 8
        }
    }
    writeCode(clearCode)
    codeSize = minCodeSize + 1
    var i = 0
    while (i < data.size) {
        val v = data(i) & 0xFF
        writeCode(v)
        writeCode(clearCode)
        codeSize = minCodeSize + 1
        i += 1
    }
    writeCode(endCode)
    if (bitCount > 0) out.append((bitBuffer & 0xFF).toByte)
    out
}

def __pytra_save_gif(path: Any, width: Any, height: Any, frames: Any, palette: Any, delayCsArg: Any = 4L, loopArg: Any = 0L): Unit = {
    val w = __pytra_int(width).toInt
    val h = __pytra_int(height).toInt
    val delayCs = __pytra_int(delayCsArg).toInt
    val loop = __pytra_int(loopArg).toInt
    val paletteBytes = __pytra_to_byte_buffer(palette)
    if (paletteBytes.size != 256 * 3) {
        throw new RuntimeException("palette must be 256*3 bytes")
    }
    val frameItems = __pytra_as_list(frames)
    val out = mutable.ArrayBuffer[Byte]('G'.toByte, 'I'.toByte, 'F'.toByte, '8'.toByte, '9'.toByte, 'a'.toByte)
    __pytra_append_u16le(out, w)
    __pytra_append_u16le(out, h)
    out.append(0xF7.toByte)
    out.append(0.toByte)
    out.append(0.toByte)
    out ++= paletteBytes
    out.append(0x21.toByte)
    out.append(0xFF.toByte)
    out.append(0x0B.toByte)
    out ++= mutable.ArrayBuffer[Byte]('N'.toByte, 'E'.toByte, 'T'.toByte, 'S'.toByte, 'C'.toByte, 'A'.toByte, 'P'.toByte, 'E'.toByte, '2'.toByte, '.'.toByte, '0'.toByte)
    out.append(0x03.toByte)
    out.append(0x01.toByte)
    __pytra_append_u16le(out, loop)
    out.append(0.toByte)
    var i = 0
    while (i < frameItems.size) {
        val fr = __pytra_to_byte_buffer(frameItems(i))
        if (fr.size != w * h) {
            throw new RuntimeException("frame size mismatch")
        }
        out.append(0x21.toByte)
        out.append(0xF9.toByte)
        out.append(0x04.toByte)
        out.append(0x00.toByte)
        __pytra_append_u16le(out, delayCs)
        out.append(0x00.toByte)
        out.append(0x00.toByte)
        out.append(0x2C.toByte)
        __pytra_append_u16le(out, 0)
        __pytra_append_u16le(out, 0)
        __pytra_append_u16le(out, w)
        __pytra_append_u16le(out, h)
        out.append(0x00.toByte)
        out.append(8.toByte)
        val compressed = __pytra_gif_lzw_encode(fr, 8)
        var pos = 0
        while (pos < compressed.size) {
            val remain = compressed.size - pos
            val chunkLen = if (remain > 255) 255 else remain
            out.append(chunkLen.toByte)
            var j = 0
            while (j < chunkLen) {
                out.append(compressed(pos + j))
                j += 1
            }
            pos += chunkLen
        }
        out.append(0.toByte)
        i += 1
    }
    out.append(0x3B.toByte)
    __pytra_write_file_bytes(path, out)
}
