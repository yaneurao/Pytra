// Kotlin native runtime helpers for Pytra-generated code.
// source: src/pytra/utils/png.py
// source: src/pytra/utils/gif.py

import kotlin.math.*
import java.io.File
import java.io.ByteArrayOutputStream
import java.io.FileOutputStream
import java.util.zip.CRC32

fun __pytra_noop(vararg args: Any?) { }

fun __pytra_any_default(): Any? {
    return 0L
}

fun __pytra_assert(vararg args: Any?): String {
    return "True"
}

fun __pytra_perf_counter(): Double {
    return System.nanoTime().toDouble() / 1_000_000_000.0
}

fun __pytra_truthy(v: Any?): Boolean {
    if (v == null) return false
    if (v is Boolean) return v
    if (v is Long) return v != 0L
    if (v is Int) return v != 0
    if (v is Double) return v != 0.0
    if (v is String) return v.isNotEmpty()
    if (v is List<*>) return v.isNotEmpty()
    if (v is Map<*, *>) return v.isNotEmpty()
    return true
}

fun __pytra_int(v: Any?): Long {
    if (v == null) return 0L
    if (v is Long) return v
    if (v is Int) return v.toLong()
    if (v is Double) return v.toLong()
    if (v is Boolean) return if (v) 1L else 0L
    if (v is String) return v.toLongOrNull() ?: 0L
    return 0L
}

fun __pytra_float(v: Any?): Double {
    if (v == null) return 0.0
    if (v is Double) return v
    if (v is Float) return v.toDouble()
    if (v is Long) return v.toDouble()
    if (v is Int) return v.toDouble()
    if (v is Boolean) return if (v) 1.0 else 0.0
    if (v is String) return v.toDoubleOrNull() ?: 0.0
    return 0.0
}

fun __pytra_str(v: Any?): String {
    if (v == null) return ""
    return v.toString()
}

fun __pytra_len(v: Any?): Long {
    if (v == null) return 0L
    if (v is String) return v.length.toLong()
    if (v is List<*>) return v.size.toLong()
    if (v is Map<*, *>) return v.size.toLong()
    return 0L
}

fun __pytra_index(i: Long, n: Long): Long {
    if (i < 0L) return i + n
    return i
}

fun __pytra_get_index(container: Any?, index: Any?): Any? {
    if (container is List<*>) {
        if (container.isEmpty()) return __pytra_any_default()
        val i = __pytra_index(__pytra_int(index), container.size.toLong())
        if (i < 0L || i >= container.size.toLong()) return __pytra_any_default()
        return container[i.toInt()]
    }
    if (container is Map<*, *>) {
        return container[__pytra_str(index)] ?: __pytra_any_default()
    }
    if (container is String) {
        if (container.isEmpty()) return ""
        val chars = container.toCharArray()
        val i = __pytra_index(__pytra_int(index), chars.size.toLong())
        if (i < 0L || i >= chars.size.toLong()) return ""
        return chars[i.toInt()].toString()
    }
    return __pytra_any_default()
}

fun __pytra_set_index(container: Any?, index: Any?, value: Any?) {
    if (container is MutableList<*>) {
        @Suppress("UNCHECKED_CAST")
        val list = container as MutableList<Any?>
        if (list.isEmpty()) return
        val i = __pytra_index(__pytra_int(index), list.size.toLong())
        if (i < 0L || i >= list.size.toLong()) return
        list[i.toInt()] = value
        return
    }
    if (container is MutableMap<*, *>) {
        @Suppress("UNCHECKED_CAST")
        val map = container as MutableMap<Any, Any?>
        map[__pytra_str(index)] = value
    }
}

fun __pytra_slice(container: Any?, lower: Any?, upper: Any?): Any? {
    if (container is String) {
        val n = container.length.toLong()
        var lo = __pytra_index(__pytra_int(lower), n)
        var hi = __pytra_index(__pytra_int(upper), n)
        if (lo < 0L) lo = 0L
        if (hi < 0L) hi = 0L
        if (lo > n) lo = n
        if (hi > n) hi = n
        if (hi < lo) hi = lo
        return container.substring(lo.toInt(), hi.toInt())
    }
    if (container is List<*>) {
        val n = container.size.toLong()
        var lo = __pytra_index(__pytra_int(lower), n)
        var hi = __pytra_index(__pytra_int(upper), n)
        if (lo < 0L) lo = 0L
        if (hi < 0L) hi = 0L
        if (lo > n) lo = n
        if (hi > n) hi = n
        if (hi < lo) hi = lo
        @Suppress("UNCHECKED_CAST")
        return container.subList(lo.toInt(), hi.toInt()).toMutableList() as MutableList<Any?>
    }
    return __pytra_any_default()
}

fun __pytra_isdigit(v: Any?): Boolean {
    val s = __pytra_str(v)
    if (s.isEmpty()) return false
    return s.all { it.isDigit() }
}

fun __pytra_isalpha(v: Any?): Boolean {
    val s = __pytra_str(v)
    if (s.isEmpty()) return false
    return s.all { it.isLetter() }
}

fun __pytra_contains(container: Any?, value: Any?): Boolean {
    if (container is List<*>) {
        val needle = __pytra_str(value)
        for (item in container) {
            if (__pytra_str(item) == needle) return true
        }
        return false
    }
    if (container is Map<*, *>) {
        return container.containsKey(__pytra_str(value))
    }
    if (container is String) {
        return container.contains(__pytra_str(value))
    }
    return false
}

fun __pytra_ifexp(cond: Boolean, a: Any?, b: Any?): Any? {
    return if (cond) a else b
}

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

fun __pytra_bytearray(initValue: Any?): MutableList<Any?> {
    if (initValue is Long) {
        val out = mutableListOf<Any?>()
        var i = 0L
        while (i < initValue) {
            out.add(0L)
            i += 1L
        }
        return out
    }
    if (initValue is Int) {
        val out = mutableListOf<Any?>()
        var i = 0
        while (i < initValue) {
            out.add(0L)
            i += 1
        }
        return out
    }
    if (initValue is MutableList<*>) {
        @Suppress("UNCHECKED_CAST")
        return (initValue as MutableList<Any?>).toMutableList()
    }
    if (initValue is List<*>) {
        @Suppress("UNCHECKED_CAST")
        return (initValue as List<Any?>).toMutableList()
    }
    return mutableListOf()
}

fun __pytra_bytes(v: Any?): MutableList<Any?> {
    if (v is MutableList<*>) {
        @Suppress("UNCHECKED_CAST")
        return (v as MutableList<Any?>).toMutableList()
    }
    if (v is List<*>) {
        @Suppress("UNCHECKED_CAST")
        return (v as List<Any?>).toMutableList()
    }
    return mutableListOf()
}

fun __pytra_list_repeat(value: Any?, count: Any?): MutableList<Any?> {
    val out = mutableListOf<Any?>()
    val n = __pytra_int(count)
    var i = 0L
    while (i < n) {
        out.add(value)
        i += 1L
    }
    return out
}

fun __pytra_enumerate(v: Any?): MutableList<Any?> {
    val items = __pytra_as_list(v)
    val out = mutableListOf<Any?>()
    var i = 0L
    while (i < items.size.toLong()) {
        out.add(mutableListOf(i, items[i.toInt()]))
        i += 1L
    }
    return out
}

fun __pytra_as_list(v: Any?): MutableList<Any?> {
    if (v is MutableList<*>) {
        @Suppress("UNCHECKED_CAST")
        return v as MutableList<Any?>
    }
    if (v is List<*>) {
        @Suppress("UNCHECKED_CAST")
        return (v as List<Any?>).toMutableList()
    }
    return mutableListOf()
}

fun __pytra_as_dict(v: Any?): MutableMap<Any, Any?> {
    if (v is MutableMap<*, *>) {
        @Suppress("UNCHECKED_CAST")
        return v as MutableMap<Any, Any?>
    }
    if (v is Map<*, *>) {
        val out = mutableMapOf<Any, Any?>()
        for ((k, valAny) in v) {
            if (k != null) out[k] = valAny
        }
        return out
    }
    return mutableMapOf()
}

fun __pytra_pop_last(v: MutableList<Any?>): MutableList<Any?> {
    if (v.isEmpty()) return v
    v.removeAt(v.size - 1)
    return v
}

fun __pytra_print(vararg args: Any?) {
    if (args.isEmpty()) {
        println()
        return
    }
    println(args.joinToString(" ") { __pytra_str(it) })
}

fun __pytra_min(a: Any?, b: Any?): Any? {
    val af = __pytra_float(a)
    val bf = __pytra_float(b)
    if (af < bf) {
        if (__pytra_is_float(a) || __pytra_is_float(b)) return af
        return __pytra_int(a)
    }
    if (__pytra_is_float(a) || __pytra_is_float(b)) return bf
    return __pytra_int(b)
}

fun __pytra_max(a: Any?, b: Any?): Any? {
    val af = __pytra_float(a)
    val bf = __pytra_float(b)
    if (af > bf) {
        if (__pytra_is_float(a) || __pytra_is_float(b)) return af
        return __pytra_int(a)
    }
    if (__pytra_is_float(a) || __pytra_is_float(b)) return bf
    return __pytra_int(b)
}

fun __pytra_is_int(v: Any?): Boolean {
    return (v is Long) || (v is Int)
}

fun __pytra_is_float(v: Any?): Boolean {
    return v is Double
}

fun __pytra_is_bool(v: Any?): Boolean {
    return v is Boolean
}

fun __pytra_is_str(v: Any?): Boolean {
    return v is String
}

fun __pytra_is_list(v: Any?): Boolean {
    return v is List<*>
}
