// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// source: src/pytra/utils/gif.py
// generated-by: tools/gen_image_runtime_from_canonical.py

import kotlin.math.*
import java.io.File
import java.io.ByteArrayOutputStream
import java.io.FileOutputStream
import java.util.zip.CRC32
fun __pytra_write_rgb_png(path: Any?, width: Any?, height: Any?, pixels: Any?) {
    val outPath = __pytra_str(path)
    val w = __pytra_int(width).toInt()
    val h = __pytra_int(height).toInt()
    val raw = __pytra_to_byte_array(pixels)
    val expected = w * h * 3
    if (raw.size != expected) {
        throw RuntimeException("pixels length mismatch")
    }

    val scan = ByteArray(h * (1 + w * 3))
    val rowBytes = w * 3
    var pos = 0
    var y = 0
    while (y < h) {
        scan[pos] = 0
        pos += 1
        val start = y * rowBytes
        System.arraycopy(raw, start, scan, pos, rowBytes)
        pos += rowBytes
        y += 1
    }

    fun adler32(data: ByteArray): Int {
        val mod = 65521
        var s1 = 1
        var s2 = 0
        var i = 0
        while (i < data.size) {
            s1 += data[i].toInt() and 0xFF
            if (s1 >= mod) s1 -= mod
            s2 += s1
            s2 %= mod
            i += 1
        }
        return ((s2 shl 16) or s1)
    }

    fun zlibDeflateStore(data: ByteArray): ByteArray {
        val out = ByteArrayOutputStream()
        out.write(0x78)
        out.write(0x01)
        val n = data.size
        var pos = 0
        while (pos < n) {
            val remain = n - pos
            val chunkLen = if (remain > 65535) 65535 else remain
            val final = if ((pos + chunkLen) >= n) 1 else 0
            out.write(final)
            out.write(chunkLen and 0xFF)
            out.write((chunkLen ushr 8) and 0xFF)
            val nlen = 0xFFFF xor chunkLen
            out.write(nlen and 0xFF)
            out.write((nlen ushr 8) and 0xFF)
            out.write(data, pos, chunkLen)
            pos += chunkLen
        }
        val adler = adler32(data)
        out.write((adler ushr 24) and 0xFF)
        out.write((adler ushr 16) and 0xFF)
        out.write((adler ushr 8) and 0xFF)
        out.write(adler and 0xFF)
        return out.toByteArray()
    }

    val idat = zlibDeflateStore(scan)

    val ihdr = byteArrayOf(
        ((w ushr 24) and 0xFF).toByte(),
        ((w ushr 16) and 0xFF).toByte(),
        ((w ushr 8) and 0xFF).toByte(),
        (w and 0xFF).toByte(),
        ((h ushr 24) and 0xFF).toByte(),
        ((h ushr 16) and 0xFF).toByte(),
        ((h ushr 8) and 0xFF).toByte(),
        (h and 0xFF).toByte(),
        8,
        2,
        0,
        0,
        0
    )

    fun chunk(chunkType: String, data: ByteArray): ByteArray {
        val out = ByteArrayOutputStream()
        val n = data.size
        out.write((n ushr 24) and 0xFF)
        out.write((n ushr 16) and 0xFF)
        out.write((n ushr 8) and 0xFF)
        out.write(n and 0xFF)
        val typeBytes = chunkType.toByteArray(Charsets.US_ASCII)
        out.write(typeBytes)
        out.write(data)
        val crc = CRC32()
        crc.update(typeBytes)
        crc.update(data)
        val c = crc.value
        out.write(((c ushr 24) and 0xFF).toInt())
        out.write(((c ushr 16) and 0xFF).toInt())
        out.write(((c ushr 8) and 0xFF).toInt())
        out.write((c and 0xFF).toInt())
        return out.toByteArray()
    }

    val outPng = ByteArrayOutputStream()
    outPng.write(byteArrayOf(0x89.toByte(), 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A))
    outPng.write(chunk("IHDR", ihdr))
    outPng.write(chunk("IDAT", idat))
    outPng.write(chunk("IEND", ByteArray(0)))

    val outFile = File(outPath)
    val parent = outFile.parentFile
    if (parent != null && !parent.exists()) {
        parent.mkdirs()
    }
    FileOutputStream(outFile).use { fos ->
        fos.write(outPng.toByteArray())
    }
}

fun __pytra_lzw_encode(data: ByteArray, minCodeSize: Int): ByteArray {
    if (data.isEmpty()) return ByteArray(0)

    val clearCode = 1 shl minCodeSize
    val endCode = clearCode + 1
    val codeSize = minCodeSize + 1

    val out = ByteArrayOutputStream()
    var bitBuffer = 0
    var bitCount = 0

    fun emit(code: Int) {
        bitBuffer = bitBuffer or (code shl bitCount)
        bitCount += codeSize
        while (bitCount >= 8) {
            out.write(bitBuffer and 0xFF)
            bitBuffer = bitBuffer ushr 8
            bitCount -= 8
        }
    }

    emit(clearCode)
    var i = 0
    while (i < data.size) {
        emit(data[i].toInt() and 0xFF)
        emit(clearCode)
        i += 1
    }
    emit(endCode)
    if (bitCount > 0) {
        out.write(bitBuffer and 0xFF)
    }
    return out.toByteArray()
}

fun __pytra_to_byte_array(v: Any?): ByteArray {
    if (v is ByteArray) return v
    val list = __pytra_as_list(v)
    val out = ByteArray(list.size)
    var i = 0
    while (i < list.size) {
        out[i] = (__pytra_int(list[i]).toInt() and 0xFF).toByte()
        i += 1
    }
    return out
}

fun __pytra_grayscale_palette(): MutableList<Any?> {
    val p = mutableListOf<Any?>()
    var i = 0L
    while (i < 256L) {
        p.add(i)
        p.add(i)
        p.add(i)
        i += 1L
    }
    return p
}

fun __pytra_save_gif(path: Any?, width: Any?, height: Any?, frames: Any?, palette: Any?, delayCs: Any? = 4L, loop: Any? = 0L) {
    val outPath = __pytra_str(path)
    val w = __pytra_int(width).toInt()
    val h = __pytra_int(height).toInt()
    val frameBytes = w * h
    val pal = __pytra_to_byte_array(palette)
    if (pal.size != 256 * 3) {
        throw RuntimeException("palette must be 256*3 bytes")
    }
    val dcs = __pytra_int(delayCs).toInt()
    val lp = __pytra_int(loop).toInt()
    val frs = __pytra_as_list(frames)

    val out = ByteArrayOutputStream()

    fun writeU16LE(v: Int) {
        out.write(v and 0xFF)
        out.write((v ushr 8) and 0xFF)
    }

    out.write("GIF89a".toByteArray(Charsets.US_ASCII))
    writeU16LE(w)
    writeU16LE(h)
    out.write(0xF7)
    out.write(0)
    out.write(0)
    out.write(pal)
    out.write(byteArrayOf(0x21, 0xFF.toByte(), 0x0B))
    out.write("NETSCAPE2.0".toByteArray(Charsets.US_ASCII))
    out.write(byteArrayOf(0x03, 0x01, (lp and 0xFF).toByte(), ((lp ushr 8) and 0xFF).toByte(), 0x00))

    var i = 0
    while (i < frs.size) {
        val fr = __pytra_to_byte_array(frs[i])
        if (fr.size != frameBytes) {
            throw RuntimeException("frame size mismatch")
        }
        out.write(byteArrayOf(0x21, 0xF9.toByte(), 0x04, 0x00, (dcs and 0xFF).toByte(), ((dcs ushr 8) and 0xFF).toByte(), 0x00, 0x00))
        out.write(0x2C)
        writeU16LE(0)
        writeU16LE(0)
        writeU16LE(w)
        writeU16LE(h)
        out.write(0x00)
        out.write(0x08)

        val compressed = __pytra_lzw_encode(fr, 8)
        var pos = 0
        while (pos < compressed.size) {
            val len = minOf(255, compressed.size - pos)
            out.write(len)
            out.write(compressed, pos, len)
            pos += len
        }
        out.write(0x00)
        i += 1
    }
    out.write(0x3B)

    val outFile = File(outPath)
    val parent = outFile.parentFile
    if (parent != null && !parent.exists()) {
        parent.mkdirs()
    }
    FileOutputStream(outFile).use { fos ->
        fos.write(out.toByteArray())
    }
}

