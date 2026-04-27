// Kotlin native runtime helpers for Pytra-generated code.
import kotlin.math.*
import java.io.File
import java.io.FileOutputStream
import java.nio.file.Files
import java.nio.file.Paths

class PyTuple(items: Collection<Any?> = emptyList()) : ArrayList<Any?>(items)

typealias ArgValue = Any?

open class Exception : RuntimeException() {
    var __pytra_message: String = ""
    open fun __init__(msg: Any?) {
        __pytra_message = __pytra_str(msg)
    }
    override val message: String
        get() = __pytra_message
    override fun toString(): String = __pytra_message
}

open class ValueError : Exception()
open class TypeError : Exception()
open class RuntimeError : Exception()
open class IndexError : Exception()
open class KeyError : Exception()

fun __pytra_Exception(msg: Any?): Exception = run { val __pytraObj = Exception(); __pytraObj.__init__(msg); __pytraObj }
fun __pytra_ValueError(msg: Any?): ValueError = run { val __pytraObj = ValueError(); __pytraObj.__init__(msg); __pytraObj }
fun __pytra_TypeError(msg: Any?): TypeError = run { val __pytraObj = TypeError(); __pytraObj.__init__(msg); __pytraObj }
fun __pytra_RuntimeError(msg: Any?): RuntimeError = run { val __pytraObj = RuntimeError(); __pytraObj.__init__(msg); __pytraObj }
fun __pytra_IndexError(msg: Any?): IndexError = run { val __pytraObj = IndexError(); __pytraObj.__init__(msg); __pytraObj }
fun __pytra_KeyError(msg: Any?): KeyError = run { val __pytraObj = KeyError(); __pytraObj.__init__(msg); __pytraObj }

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

object env {
    val target: String = "kotlin"
}

object os_path {
    fun join(a: Any?, b: Any?): String = Paths.get(__pytra_str(a)).resolve(__pytra_str(b)).toString()
    fun dirname(p: Any?): String = File(__pytra_str(p)).parent ?: ""
    fun basename(p: Any?): String = File(__pytra_str(p)).name
    fun splitext(p: Any?): MutableList<Any?> {
        val path = __pytra_str(p)
        val idx = path.lastIndexOf('.')
        return if (idx <= 0) mutableListOf(path, "") else mutableListOf(path.substring(0, idx), path.substring(idx))
    }
    fun abspath(p: Any?): String = Paths.get(__pytra_str(p)).toAbsolutePath().normalize().toString()
    fun exists(p: Any?): Boolean = File(__pytra_str(p)).exists()
}

object os {
    val path = os_path

    fun getcwd(): String = Paths.get("").toAbsolutePath().normalize().toString()

    fun mkdir(p: Any?, exist_ok: Boolean = false) {
        val dir = File(__pytra_str(p))
        val ok = dir.mkdir()
        if (!ok && !(exist_ok && dir.exists())) {
            throw RuntimeException("File exists: ${dir.path}")
        }
    }

    fun makedirs(p: Any?, exist_ok: Boolean = false) {
        val dir = File(__pytra_str(p))
        if (dir.exists()) {
            if (!exist_ok) {
                throw RuntimeException("File exists: ${dir.path}")
            }
            return
        }
        if (!dir.mkdirs() && !dir.exists()) {
            throw RuntimeException("mkdirs failed: ${dir.path}")
        }
    }
}

object glob {
    fun glob(pattern: Any?): MutableList<String> {
        val matcher = java.nio.file.FileSystems.getDefault().getPathMatcher("glob:" + __pytra_str(pattern))
        val cwd = Paths.get("").toAbsolutePath().normalize()
        val out = mutableListOf<String>()
        java.nio.file.Files.newDirectoryStream(cwd).use { stream ->
            for (entry in stream) {
                val name = entry.fileName.toString()
                if (matcher.matches(java.nio.file.Paths.get(name))) out.add(name)
            }
        }
        return out
    }
}

class PyStdWriter(private val useErr: Boolean) {
    fun write(text: Any?) {
        if (useErr) System.err.print(__pytra_str(text))
        else kotlin.io.print(__pytra_str(text))
    }
}

var sys_argv: MutableList<String> = mutableListOf()
var sys_path: MutableList<String> = mutableListOf()
val sys_stderr = PyStdWriter(true)
val sys_stdout = PyStdWriter(false)

fun sys_exit(code: Any? = 0L) {
    throw RuntimeException("SystemExit(" + __pytra_int(code).toString() + ")")
}

fun sys_set_argv(values: Any?) {
    sys_argv.clear()
    for (v in __pytra_as_list(values)) sys_argv.add(__pytra_str(v))
}

fun sys_set_path(values: Any?) {
    sys_path.clear()
    for (v in __pytra_as_list(values)) sys_path.add(__pytra_str(v))
}

fun pytra_std_sys_write_stderr(text: Any?) { sys_stderr.write(text) }
fun pytra_std_sys_write_stdout(text: Any?) { sys_stdout.write(text) }
fun __pytra_makedirs(path: Any?, exist_ok: Any? = false) { os.makedirs(path, __pytra_truthy(exist_ok)) }
fun __pytra_floor(v: Any?): Double = floor(__pytra_float(v))
fun __pytra_Path(raw: Any?): Path = Path(raw)

fun <T> __pytra_sorted(values: MutableList<T>): MutableList<T> {
    val out = values.toMutableList()
    out.sortWith(Comparator { left: T, right: T ->
        val leftValue = left as Any?
        val rightValue = right as Any?
        if (leftValue is String || rightValue is String) {
            __pytra_str(leftValue).compareTo(__pytra_str(rightValue))
        } else {
            __pytra_float(leftValue).compareTo(__pytra_float(rightValue))
        }
    })
    return out
}

fun <T> __pytra_sorted(values: MutableSet<T>): MutableList<T> = __pytra_sorted(values.toMutableList())

fun <T> __pytra_set_update(target: MutableSet<T>, values: Iterable<*>) {
    for (value in values) {
        @Suppress("UNCHECKED_CAST")
        target.add(value as T)
    }
}
fun __pytra_glob(pattern: Any?): MutableList<String> = glob.glob(pattern)

fun __pytra_cast(target: Any?, value: Any?): Any? = value

class Namespace(var values: MutableMap<String, Any?> = linkedMapOf())

class _ArgSpec(
    var names: MutableList<String>,
    var action: String = "",
    var choices: MutableList<String> = mutableListOf(),
    var default: Any? = null,
    var help_text: String = ""
) {
    var is_optional: Boolean = names.isNotEmpty() && names[0].startsWith("-")
    var dest: String = if (is_optional) names.last().trimStart('-').replace("-", "_") else if (names.isNotEmpty()) names[0] else ""
}

class ArgumentParser(var description: String = "") {
    var _specs: MutableList<_ArgSpec> = mutableListOf()

    fun add_argument(
        name1: Any?,
        name2: Any? = null,
        name3: Any? = null,
        name4: Any? = null,
        action: String = "",
        choices: Any? = null,
        default: Any? = null,
        help_text: String = ""
    ) {
        val raw = mutableListOf<Any?>(name1)
        if (name2 != null) raw.add(name2)
        if (name3 != null) raw.add(name3)
        if (name4 != null) raw.add(name4)
        if (choices != null) raw.add(choices)
        if (action != "") raw.add(action)
        if (default != null) raw.add(default)
        if (help_text != "") raw.add(help_text)
        val names = mutableListOf<String>()
        var idx = 0
        while (idx < raw.size && names.size < 4) {
            val value = raw[idx]
            if (value is String && value != "" && (names.isEmpty() || value.startsWith("-"))) {
                names.add(value)
                idx += 1
            } else {
                idx = raw.size
            }
        }
        if (names.isEmpty()) throw ValueError()
        var action = ""
        var choices: MutableList<String> = mutableListOf()
        var default: Any? = null
        var help = ""
        var tailIndex = names.size
        while (tailIndex < raw.size) {
            when (val value = raw[tailIndex]) {
                is MutableList<*> -> if (choices.isEmpty()) choices = value.map { __pytra_str(it) }.toMutableList()
                is List<*> -> if (choices.isEmpty()) choices = value.map { __pytra_str(it) }.toMutableList()
                is String -> when {
                    action == "" && (value == "store_true" || value == "store_false") -> action = value
                    default == null && !value.startsWith("-") -> default = value
                    help == "" -> help = value
                }
                else -> if (default == null) default = value
            }
            tailIndex += 1
        }
        _specs.add(_ArgSpec(names, action, choices, default, help))
    }

    private fun _fail(msg: String) {
        if (msg != "") pytra_std_sys_write_stderr("error: $msg\n")
        sys_exit(2L)
    }

    fun parse_args(argv: Any? = null): MutableMap<String, Any?> {
        val args: MutableList<String> =
            if (argv == null) sys_argv.drop(1).toMutableList()
            else __pytra_as_list(argv).map { __pytra_str(it) }.toMutableList()
        val specsPos = mutableListOf<_ArgSpec>()
        val specsOpt = mutableListOf<_ArgSpec>()
        for (s in _specs) {
            if (s.is_optional) specsOpt.add(s) else specsPos.add(s)
        }
        val byName = linkedMapOf<String, Long>()
        var specI = 0L
        for (s in specsOpt) {
            for (n in s.names) byName[n] = specI
            specI += 1L
        }
        val values = linkedMapOf<String, Any?>()
        for (s in _specs) {
            values[s.dest] = if (s.action == "store_true") {
                if (s.default is Boolean) s.default else false
            } else if (s.default != null) s.default else null
        }
        var posI = 0
        var i = 0
        while (i < args.size) {
            val tok = args[i]
            if (tok.startsWith("-")) {
                if (!byName.containsKey(tok)) _fail("unknown option: $tok")
                val spec = specsOpt[byName[tok]!!.toInt()]
                if (spec.action == "store_true") {
                    values[spec.dest] = true
                    i += 1
                } else {
                    if (i + 1 >= args.size) _fail("missing value for option: $tok")
                    val value = args[i + 1]
                    if (spec.choices.isNotEmpty() && !spec.choices.contains(value)) _fail("invalid choice for $tok: $value")
                    values[spec.dest] = value
                    i += 2
                }
            } else {
                if (posI >= specsPos.size) _fail("unexpected extra argument: $tok")
                val spec = specsPos[posI]
                values[spec.dest] = tok
                posI += 1
                i += 1
            }
        }
        if (posI < specsPos.size) _fail("missing required argument: ${specsPos[posI].dest}")
        return values
    }
}

fun __pytra_assert_true(cond: Boolean, label: String = ""): Boolean {
    if (cond) return true
    if (label != "") __pytra_print("[assert_true] $label: False")
    else __pytra_print("[assert_true] False")
    return false
}

fun __pytra_assert_eq(actual: Any?, expected: Any?, label: String = ""): Boolean {
    val ok = __pytra_str(actual) == __pytra_str(expected)
    if (ok) return true
    if (label != "") __pytra_print("[assert_eq] $label: actual=${__pytra_str(actual)}, expected=${__pytra_str(expected)}")
    else __pytra_print("[assert_eq] actual=${__pytra_str(actual)}, expected=${__pytra_str(expected)}")
    return false
}

fun __pytra_assert_all(results: Any?, label: String = ""): Boolean {
    for (v in __pytra_as_list(results)) {
        if (!__pytra_truthy(v)) {
            if (label != "") __pytra_print("[assert_all] $label: False")
            else __pytra_print("[assert_all] False")
            return false
        }
    }
    return true
}

fun __pytra_assert_stdout(expected_lines: Any?, fn: Any?): Boolean = true

private fun _pngAppend(dst: MutableList<Long>, src: List<Long>) { dst.addAll(src) }
private fun _pngU16le(v: Long): MutableList<Long> = mutableListOf(v and 0xffL, (v shr 8) and 0xffL)
private fun _pngU32be(v: Long): MutableList<Long> = mutableListOf((v shr 24) and 0xffL, (v shr 16) and 0xffL, (v shr 8) and 0xffL, v and 0xffL)
private fun _crc32(data: List<Long>): Long {
    var crc = 0xffffffffL
    val poly = 0xedb88320L
    for (b in data) {
        crc = crc xor (b and 0xffL)
        repeat(8) {
            crc = if ((crc and 1L) != 0L) (crc shr 1) xor poly else (crc shr 1)
        }
    }
    return crc xor 0xffffffffL
}
private fun _adler32(data: List<Long>): Long {
    val mod = 65521L
    var s1 = 1L
    var s2 = 0L
    for (b in data) {
        s1 += (b and 0xffL)
        if (s1 >= mod) s1 -= mod
        s2 = (s2 + s1) % mod
    }
    return ((s2 shl 16) or s1) and 0xffffffffL
}
private fun _zlibDeflateStore(data: List<Long>): MutableList<Long> {
    val out = mutableListOf<Long>(0x78L, 0x01L)
    var pos = 0
    while (pos < data.size) {
        val remain = data.size - pos
        val chunkLen = if (remain > 65535) 65535 else remain
        val finalFlag = if (pos + chunkLen >= data.size) 1L else 0L
        out.add(finalFlag)
        _pngAppend(out, _pngU16le(chunkLen.toLong()))
        _pngAppend(out, _pngU16le((0xffff xor chunkLen).toLong()))
        repeat(chunkLen) { i -> out.add(data[pos + i]) }
        pos += chunkLen
    }
    _pngAppend(out, _pngU32be(_adler32(data)))
    return out
}
private fun _pngChunk(chunkType: List<Long>, data: MutableList<Long>): MutableList<Long> {
    val crcInput = mutableListOf<Long>()
    _pngAppend(crcInput, chunkType)
    _pngAppend(crcInput, data)
    val out = mutableListOf<Long>()
    _pngAppend(out, _pngU32be(data.size.toLong()))
    _pngAppend(out, chunkType)
    _pngAppend(out, data)
    _pngAppend(out, _pngU32be(_crc32(crcInput)))
    return out
}
fun __pytra_write_rgb_png(path: String, width: Long, height: Long, pixels: Any?) {
    val raw = __pytra_bytes(pixels)
    val expected = width * height * 3L
    if (raw.size.toLong() != expected) throw RuntimeException("pixels length mismatch: got=${raw.size} expected=$expected")
    val scanlines = mutableListOf<Long>()
    val rowBytes = width * 3L
    var y = 0L
    while (y < height) {
        scanlines.add(0L)
        var i = y * rowBytes
        while (i < y * rowBytes + rowBytes) {
            scanlines.add(raw[i.toInt()])
            i += 1L
        }
        y += 1L
    }
    val ihdr = mutableListOf<Long>()
    _pngAppend(ihdr, _pngU32be(width))
    _pngAppend(ihdr, _pngU32be(height))
    _pngAppend(ihdr, listOf(8L, 2L, 0L, 0L, 0L))
    val idat = _zlibDeflateStore(scanlines)
    val png = mutableListOf<Long>()
    _pngAppend(png, listOf(137L, 80L, 78L, 71L, 13L, 10L, 26L, 10L))
    _pngAppend(png, _pngChunk(listOf(73L, 72L, 68L, 82L), ihdr))
    _pngAppend(png, _pngChunk(listOf(73L, 68L, 65L, 84L), idat))
    _pngAppend(png, _pngChunk(listOf(73L, 69L, 78L, 68L), mutableListOf()))
    val file = open(path, "wb")
    try {
        file.write(png)
    } finally {
        file.close()
    }
}

private fun __pytra_gif_append(dst: MutableList<Long>, src: List<*>) {
    for (value in src) dst.add(__pytra_int(value) and 0xffL)
}

private fun __pytra_gif_u16le(value: Long): MutableList<Long> = mutableListOf(value and 0xffL, (value shr 8) and 0xffL)

private fun __pytra_lzw_encode(data: List<*>, minCodeSize: Long): MutableList<Long> {
    if (data.isEmpty()) return mutableListOf()
    val clearCode = 1L shl minCodeSize.toInt()
    val endCode = clearCode + 1L
    var codeSize = minCodeSize + 1L
    val out = mutableListOf<Long>()
    var bitBuffer = clearCode
    var bitCount = codeSize
    while (bitCount >= 8L) {
        out.add(bitBuffer and 0xffL)
        bitBuffer = bitBuffer shr 8
        bitCount -= 8L
    }
    codeSize = minCodeSize + 1L
    var index = 0
    while (index < data.size) {
        val value = __pytra_int(data[index])
        bitBuffer = bitBuffer or (value shl bitCount.toInt())
        bitCount += codeSize
        while (bitCount >= 8L) {
            out.add(bitBuffer and 0xffL)
            bitBuffer = bitBuffer shr 8
            bitCount -= 8L
        }
        bitBuffer = bitBuffer or (clearCode shl bitCount.toInt())
        bitCount += codeSize
        while (bitCount >= 8L) {
            out.add(bitBuffer and 0xffL)
            bitBuffer = bitBuffer shr 8
            bitCount -= 8L
        }
        codeSize = minCodeSize + 1L
        index += 1
    }
    bitBuffer = bitBuffer or (endCode shl bitCount.toInt())
    bitCount += codeSize
    while (bitCount >= 8L) {
        out.add(bitBuffer and 0xffL)
        bitBuffer = bitBuffer shr 8
        bitCount -= 8L
    }
    if (bitCount > 0L) out.add(bitBuffer and 0xffL)
    return out
}

fun __pytra_grayscale_palette(): MutableList<Long> {
    val out = mutableListOf<Long>()
    var i = 0L
    while (i < 256L) {
        out.add(i)
        out.add(i)
        out.add(i)
        i += 1L
    }
    return out
}

fun __pytra_save_gif(path: String, width: Long, height: Long, frames: Any?, palette: Any?, delayCs: Long = 4L, loop: Long = 0L) {
    val paletteList = __pytra_as_list(palette)
    if (paletteList.size != 256 * 3) throw RuntimeException("palette must be 256*3 bytes")
    val frameSize = width * height
    val out = mutableListOf<Long>()
    __pytra_gif_append(out, listOf(71L, 73L, 70L, 56L, 57L, 97L))
    __pytra_gif_append(out, __pytra_gif_u16le(width))
    __pytra_gif_append(out, __pytra_gif_u16le(height))
    __pytra_gif_append(out, listOf(0xF7L, 0L, 0L))
    __pytra_gif_append(out, paletteList)
    __pytra_gif_append(out, listOf(0x21L, 0xFFL, 0x0BL, 78L, 69L, 84L, 83L, 67L, 65L, 80L, 69L, 50L, 46L, 48L, 0x03L, 0x01L))
    __pytra_gif_append(out, __pytra_gif_u16le(loop))
    out.add(0L)
    val frameList = __pytra_as_list(frames)
    var frameIndex = 0
    while (frameIndex < frameList.size) {
        val frame = __pytra_as_list(frameList[frameIndex])
        if (frame.size.toLong() != frameSize) throw RuntimeException("frame size mismatch")
        __pytra_gif_append(out, listOf(0x21L, 0xF9L, 0x04L, 0x00L))
        __pytra_gif_append(out, __pytra_gif_u16le(delayCs))
        __pytra_gif_append(out, listOf(0x00L, 0x00L))
        out.add(0x2CL)
        __pytra_gif_append(out, __pytra_gif_u16le(0L))
        __pytra_gif_append(out, __pytra_gif_u16le(0L))
        __pytra_gif_append(out, __pytra_gif_u16le(width))
        __pytra_gif_append(out, __pytra_gif_u16le(height))
        out.add(0L)
        out.add(8L)
        val compressed = __pytra_lzw_encode(frame, 8L)
        var pos = 0
        while (pos < compressed.size) {
            val remain = compressed.size - pos
            val chunkLen = if (remain > 255) 255 else remain
            out.add(chunkLen.toLong())
            var i = 0
            while (i < chunkLen) {
                out.add(compressed[pos + i])
                i += 1
            }
            pos += chunkLen
        }
        out.add(0L)
        frameIndex += 1
    }
    out.add(0x3BL)
    val outPath = Paths.get(path)
    val parent = outPath.parent
    if (parent != null) Files.createDirectories(parent)
    Files.write(outPath, out.map { (it and 0xffL).toByte() }.toByteArray())
}

class PyFile(private val path: String, private val mode: String) {
    private val stream = if (mode.contains("r")) null else FileOutputStream(path)

    fun read(): String {
        return Files.readString(Paths.get(path))
    }

    fun write(data: Any?) {
        val out = stream ?: throw RuntimeException("file not opened for writing")
        when (data) {
            is MutableList<*> -> {
                val bytes = ByteArray(data.size)
                var i = 0
                while (i < data.size) {
                    bytes[i] = (__pytra_int(data[i]) and 0xFF).toByte()
                    i += 1
                }
                out.write(bytes)
            }
            is String -> out.write(data.toByteArray(Charsets.UTF_8))
            else -> out.write(__pytra_str(data).toByteArray(Charsets.UTF_8))
        }
    }

    fun __enter__(): PyFile = this

    fun __exit__(excType: Any?, excVal: Any?, excTb: Any?) {
        close()
    }

    fun close() {
        stream?.close()
    }
}

fun open(path: Any?, mode: String = "r"): PyFile {
    return PyFile(__pytra_str(path), mode)
}

fun __pytra_truthy(v: Any?): Boolean {
    if (v == null) return false
    if (v is Boolean) return v
    if (v is Long) return v != 0L
    if (v is Int) return v != 0
    if (v is Double) return v != 0.0
    if (v is String) return v.isNotEmpty()
    if (v is List<*>) return v.isNotEmpty()
    if (v is Set<*>) return v.isNotEmpty()
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

private fun __pytra_float_str(v: Double): String = java.lang.Double.toString(v).replace("E", "e")

private fun __pytra_repr(v: Any?): String {
    if (v == null) return "None"
    if (v is Boolean) return if (v) "True" else "False"
    if (v is Double) return __pytra_float_str(v)
    if (v is Float) return __pytra_float_str(v.toDouble())
    if (v is String) return "'" + v.replace("\\", "\\\\").replace("'", "\\'") + "'"
    if (v is PyTuple) {
        val inner = v.joinToString(", ") { __pytra_repr(it) }
        return if (v.size == 1) "(" + inner + ",)" else "(" + inner + ")"
    }
    if (v is List<*>) {
        return "[" + v.joinToString(", ") { __pytra_repr(it) } + "]"
    }
    if (v is Map<*, *>) {
        return "{" + v.entries.joinToString(", ") { __pytra_repr(it.key) + ": " + __pytra_repr(it.value) } + "}"
    }
    if (v is Set<*>) {
        return "{" + v.joinToString(", ") { __pytra_repr(it) } + "}"
    }
    return v.toString()
}

fun __pytra_str(v: Any?): String {
    if (v is String) return v
    return __pytra_repr(v)
}

fun __pytra_tuple(vararg items: Any?): PyTuple {
    return PyTuple(items.toList())
}

fun __pytra_format(value: Any?, spec: String): String {
    if (spec.isEmpty()) return __pytra_str(value)
    if (spec.endsWith("%")) {
        return __pytra_format(__pytra_float(value) * 100.0, spec.dropLast(1) + "f") + "%"
    }
    val kind = spec.last()
    val flags = spec.dropLast(1).replace("<", "-")
    val fmt = "%" + flags + kind
    return when (kind) {
        'd', 'x', 'X' -> String.format(java.util.Locale.US, fmt, __pytra_int(value))
        'f' -> String.format(java.util.Locale.US, fmt, __pytra_float(value))
        's' -> String.format(java.util.Locale.US, fmt, __pytra_str(value))
        else -> __pytra_str(value)
    }
}

fun __pytra_join(sep: Any?, items: Any?): String {
    return __pytra_as_list(items).joinToString(__pytra_str(sep)) { __pytra_str(it) }
}

fun __pytra_strip(v: Any?): String = __pytra_str(v).trim()
fun __pytra_lstrip(v: Any?): String = __pytra_str(v).trimStart()
fun __pytra_rstrip(v: Any?): String = __pytra_str(v).trimEnd()
fun __pytra_split(v: Any?, sep: Any?): MutableList<String> {
    val s = __pytra_str(v)
    val parts = if (sep == null || __pytra_str(sep).isEmpty()) {
        s.trim().split(Regex("\\s+")).filter { it.isNotEmpty() }
    } else {
        s.split(__pytra_str(sep))
    }
    return parts.toMutableList()
}
fun __pytra_startswith(v: Any?, prefix: Any?): Boolean = __pytra_str(v).startsWith(__pytra_str(prefix))
fun __pytra_endswith(v: Any?, suffix: Any?): Boolean = __pytra_str(v).endsWith(__pytra_str(suffix))
fun __pytra_replace(v: Any?, old: Any?, newValue: Any?): String = __pytra_str(v).replace(__pytra_str(old), __pytra_str(newValue))
fun __pytra_upper(v: Any?): String = __pytra_str(v).toUpperCase()
fun __pytra_lower(v: Any?): String = __pytra_str(v).toLowerCase()
fun __pytra_find(v: Any?, sub: Any?): Long = __pytra_str(v).indexOf(__pytra_str(sub)).toLong()
fun __pytra_rfind(v: Any?, sub: Any?): Long = __pytra_str(v).lastIndexOf(__pytra_str(sub)).toLong()
fun __pytra_str_index(v: Any?, sub: Any?): Long {
    val found = __pytra_find(v, sub)
    if (found < 0L) {
        val err = ValueError()
        err.__init__("substring not found")
        throw err
    }
    return found
}
fun __pytra_count_substr(v: Any?, sub: Any?): Long {
    val s = __pytra_str(v)
    val t = __pytra_str(sub)
    if (t.isEmpty()) return (s.length + 1).toLong()
    var count = 0L
    var idx = 0
    while (true) {
        val found = s.indexOf(t, idx)
        if (found < 0) break
        count += 1L
        idx = found + t.length
    }
    return count
}
fun __pytra_isalnum(v: Any?): Boolean {
    val s = __pytra_str(v)
    if (s.isEmpty()) return false
    return s.all { it.isLetterOrDigit() }
}

fun __pytra_eq(a: Any?, b: Any?): Boolean {
    if (a == null || b == null) return a == b
    if (a is String || b is String) return __pytra_str(a) == __pytra_str(b)
    if ((a is Long || a is Int || a is Double || a is Boolean) && (b is Long || b is Int || b is Double || b is Boolean)) {
        return __pytra_float(a) == __pytra_float(b)
    }
    return a == b
}

fun __pytra_len(v: Any?): Long {
    if (v == null) return 0L
    if (v is String) return v.length.toLong()
    if (v is List<*>) return v.size.toLong()
    if (v is Set<*>) return v.size.toLong()
    if (v is Map<*, *>) return v.size.toLong()
    return try {
        __pytra_int(v.javaClass.getMethod("__len__").invoke(v))
    } catch (_: Throwable) {
        0L
    }
}

fun __pytra_index(i: Long, n: Long): Long {
    if (i < 0L) return i + n
    return i
}

fun __pytra_get_index(container: Any?, index: Any?): Any? {
    if (container is List<*>) {
        if (container.isEmpty()) {
            throw run { val __pytraObj = IndexError(); __pytraObj.__init__("list index out of range"); __pytraObj }
        }
        val i = __pytra_index(__pytra_int(index), container.size.toLong())
        if (i < 0L || i >= container.size.toLong()) {
            throw run { val __pytraObj = IndexError(); __pytraObj.__init__("list index out of range"); __pytraObj }
        }
        return container[i.toInt()]
    }
    if (container is Map<*, *>) {
        return container[index] ?: __pytra_any_default()
    }
    if (container is String) {
        if (container.isEmpty()) {
            throw run { val __pytraObj = IndexError(); __pytraObj.__init__("string index out of range"); __pytraObj }
        }
        val chars = container.toCharArray()
        val i = __pytra_index(__pytra_int(index), chars.size.toLong())
        if (i < 0L || i >= chars.size.toLong()) {
            throw run { val __pytraObj = IndexError(); __pytraObj.__init__("string index out of range"); __pytraObj }
        }
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
        val map = container as MutableMap<Any?, Any?>
        map[index] = value
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
        for (item in container) {
            if (item == value) return true
        }
        return false
    }
    if (container is Set<*>) {
        return container.contains(value)
    }
    if (container is Map<*, *>) {
        return container.containsKey(value)
    }
    if (container is String) {
        return container.contains(__pytra_str(value))
    }
    return false
}

fun __pytra_ifexp(cond: Boolean, a: Any?, b: Any?): Any? {
    return if (cond) a else b
}

fun __pytra_bytearray(initValue: Any? = null): MutableList<Long> {
    if (initValue is Long) {
        val out = mutableListOf<Long>()
        var i = 0L
        while (i < initValue) {
            out.add(0L)
            i += 1L
        }
        return out
    }
    if (initValue is Int) {
        val out = mutableListOf<Long>()
        var i = 0
        while (i < initValue) {
            out.add(0L)
            i += 1
        }
        return out
    }
    if (initValue is MutableList<*>) {
        val out = mutableListOf<Long>()
        for (item in initValue) out.add(__pytra_int(item))
        return out
    }
    if (initValue is List<*>) {
        val out = mutableListOf<Long>()
        for (item in initValue) out.add(__pytra_int(item))
        return out
    }
    return mutableListOf()
}

fun __pytra_bytes(v: Any? = null): MutableList<Long> {
    if (v is MutableList<*>) {
        val out = mutableListOf<Long>()
        for (item in v) out.add(__pytra_int(item))
        return out
    }
    if (v is List<*>) {
        val out = mutableListOf<Long>()
        for (item in v) out.add(__pytra_int(item))
        return out
    }
    return mutableListOf()
}

fun __pytra_list_repeat(value: Any?, count: Any?): MutableList<Any?> {
    val out = mutableListOf<Any?>()
    val n = __pytra_int(count)
    val items = __pytra_as_list(value)
    var i = 0L
    while (i < n) {
        out.addAll(items)
        i += 1L
    }
    return out
}

fun __pytra_list_concat(a: Any?, b: Any?): MutableList<Any?> {
    val out = mutableListOf<Any?>()
    out.addAll(__pytra_as_list(a))
    out.addAll(__pytra_as_list(b))
    return out
}

fun __pytra_reversed(v: Any?): MutableList<Any?> {
    val items = __pytra_as_list(v)
    val out = mutableListOf<Any?>()
    var i = items.size - 1
    while (i >= 0) {
        out.add(items[i])
        i -= 1
    }
    return out
}

@Suppress("UNCHECKED_CAST")
fun <T> __pytra_list(v: Any?): MutableList<T> {
    val out = mutableListOf<T>()
    for (item in __pytra_as_list(v)) out.add(item as T)
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

fun __pytra_range(vararg args: Any?): MutableList<Any?> {
    var start = 0L
    var stop = 0L
    var step = 1L
    if (args.size == 1) {
        stop = __pytra_int(args[0])
    } else if (args.size >= 2) {
        start = __pytra_int(args[0])
        stop = __pytra_int(args[1])
        if (args.size >= 3) {
            step = __pytra_int(args[2])
        }
    }
    val out = mutableListOf<Any?>()
    if (step == 0L) return out
    var i = start
    if (step > 0L) {
        while (i < stop) {
            out.add(i)
            i += step
        }
    } else {
        while (i > stop) {
            out.add(i)
            i += step
        }
    }
    return out
}

fun __pytra_sum(xs: Any?): Any? {
    val lst = __pytra_as_list(xs)
    var hasFloat = false
    for (v in lst) {
        if (v is Double || v is Float) {
            hasFloat = true
            break
        }
    }
    if (hasFloat) {
        var acc = 0.0
        for (v in lst) acc += __pytra_float(v)
        return acc
    }
    var acc = 0L
    for (v in lst) acc += __pytra_int(v)
    return acc
}

fun __pytra_zip(a: Any?, b: Any?): MutableList<Any?> {
    val la = __pytra_as_list(a)
    val lb = __pytra_as_list(b)
    val n = minOf(la.size, lb.size)
    val out = mutableListOf<Any?>()
    var i = 0
    while (i < n) {
        out.add(mutableListOf(la[i], lb[i]))
        i += 1
    }
    return out
}

fun __pytra_set_new(v: Any? = null): MutableSet<Any?> {
    if (v == null) {
        return linkedSetOf()
    }
    if (v is Set<*>) {
        @Suppress("UNCHECKED_CAST")
        return (v as Set<Any?>).toMutableSet()
    }
    if (v is List<*>) {
        @Suppress("UNCHECKED_CAST")
        return (v as List<Any?>).toMutableSet()
    }
    return linkedSetOf()
}

fun __pytra_dict_items(v: Any?): MutableList<Any?> {
    val out = mutableListOf<Any?>()
    if (v is Map<*, *>) {
        for ((k, value) in v) {
            out.add(mutableListOf(k, value))
        }
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
    if (v is Set<*>) {
        @Suppress("UNCHECKED_CAST")
        return (v as Set<Any?>).toMutableList()
    }
    if (v is String) {
        return v.map { it.toString() as Any? }.toMutableList()
    }
    return mutableListOf()
}

fun __pytra_as_dict(v: Any?): MutableMap<Any?, Any?> {
    if (v is MutableMap<*, *>) {
        @Suppress("UNCHECKED_CAST")
        return v as MutableMap<Any?, Any?>
    }
    if (v is Map<*, *>) {
        val out = mutableMapOf<Any?, Any?>()
        for ((k, valAny) in v) {
            out[k] = valAny
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

fun __pytra_min(a: Long, b: Long): Long {
    return if (a < b) a else b
}

fun __pytra_min(a: Double, b: Double): Double {
    return if (a < b) a else b
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

fun __pytra_max(a: Long, b: Long): Long {
    return if (a > b) a else b
}

fun __pytra_max(a: Double, b: Double): Double {
    return if (a > b) a else b
}

fun pyMathSqrt(v: Any?): Double { return kotlin.math.sqrt(__pytra_float(v)) }
fun pyMathSin(v: Any?): Double { return kotlin.math.sin(__pytra_float(v)) }
fun pyMathCos(v: Any?): Double { return kotlin.math.cos(__pytra_float(v)) }
fun pyMathTan(v: Any?): Double { return kotlin.math.tan(__pytra_float(v)) }
fun pyMathExp(v: Any?): Double { return kotlin.math.exp(__pytra_float(v)) }
fun pyMathLog(v: Any?): Double { return kotlin.math.ln(__pytra_float(v)) }
fun pyMathFabs(v: Any?): Double { return kotlin.math.abs(__pytra_float(v)) }
fun pyMathFloor(v: Any?): Double { return kotlin.math.floor(__pytra_float(v)) }
fun pyMathCeil(v: Any?): Double { return kotlin.math.ceil(__pytra_float(v)) }
fun pyMathPow(a: Any?, b: Any?): Double { return __pytra_float(a).pow(__pytra_float(b)) }
fun pyMathPi(): Double { return Math.PI }
fun pyMathE(): Double { return Math.E }
fun __pytra_sqrt(v: Any?): Double { return pyMathSqrt(v) }
fun __pytra_sin(v: Any?): Double { return pyMathSin(v) }
fun __pytra_cos(v: Any?): Double { return pyMathCos(v) }
fun __pytra_tan(v: Any?): Double { return pyMathTan(v) }
fun __pytra_exp(v: Any?): Double { return pyMathExp(v) }
fun __pytra_log(v: Any?): Double { return pyMathLog(v) }
fun __pytra_fabs(v: Any?): Double { return pyMathFabs(v) }
fun __pytra_ceil(v: Any?): Double { return pyMathCeil(v) }
fun __pytra_pow(a: Any?, b: Any?): Double { return pyMathPow(a, b) }

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

fun __pytra_type_name(v: Any?): String {
    if (v == null) return "None"
    if (v is Boolean) return "bool"
    if (v is Long || v is Int) return "int"
    if (v is Double || v is Float) return "float"
    if (v is String) return "str"
    if (v is PyTuple) return "tuple"
    if (v is MutableMap<*, *> || v is Map<*, *>) return "dict"
    if (v is MutableSet<*> || v is Set<*>) return "set"
    if (v is MutableList<*> || v is List<*>) return "list"
    return v.javaClass.simpleName
}

fun __pytra_is_instance(v: Any?, expected: String): Boolean {
    fun hasTypeName(cls: Class<*>?, name: String): Boolean {
        var cur = cls
        while (cur != null) {
            if (cur.simpleName == name) return true
            for (iface in cur.interfaces) {
                if (hasTypeName(iface, name)) return true
            }
            cur = cur.superclass
        }
        return false
    }
    return when (expected) {
        "None", "none" -> v == null
        "bool" -> v is Boolean
        "int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64" -> (v is Long) || (v is Int)
        "float", "float32", "float64" -> (v is Double) || (v is Float)
        "str" -> v is String
        "list", "tuple", "bytes", "bytearray" -> v is List<*>
        "set" -> v is Set<*>
        "dict" -> v is Map<*, *>
        "Path" -> v is java.nio.file.Path
        else -> v != null && hasTypeName(v.javaClass, expected)
    }
}

fun __pytra_is_subtype(actual: Any?, expected: Any?): Boolean {
    return __pytra_str(actual) == __pytra_str(expected)
}

// --- json ---

fun pyJsonDumps(v: Any?): String {
    return __pytra_json_stringify(v)
}

fun pyJsonLoads(v: Any?): Any? {
    return __PytraJsonParser(__pytra_str(v)).parse()
}

class JsonValue(var raw: Any?) {
    fun as_str(): String? = raw as? String
    fun as_int(): Long? = when (val v = raw) {
        is Long -> v
        is Int -> v.toLong()
        else -> null
    }
    fun as_float(): Double? = when (val v = raw) {
        is Double -> v
        is Float -> v.toDouble()
        is Long -> v.toDouble()
        is Int -> v.toDouble()
        else -> null
    }
    fun as_bool(): Boolean? = raw as? Boolean
    fun as_arr(): JsonArr? = when (val v = raw) {
        is MutableList<*> -> JsonArr(v as MutableList<Any?>)
        else -> null
    }
    fun as_obj(): JsonObj? = when (val v = raw) {
        is MutableMap<*, *> -> {
            val out = linkedMapOf<String, Any?>()
            for ((k, value) in v) out[__pytra_str(k)] = value
            JsonObj(out)
        }
        else -> null
    }
}

class JsonArr(var raw: MutableList<Any?>) {
    fun get(index: Long): JsonValue? {
        val i = index.toInt()
        return if (i < 0 || i >= raw.size) null else JsonValue(raw[i])
    }
    fun get_str(index: Long): String? = get(index)?.as_str()
    fun get_int(index: Long): Long? = get(index)?.as_int()
    fun get_float(index: Long): Double? = get(index)?.as_float()
    fun get_bool(index: Long): Boolean? = get(index)?.as_bool()
    fun get_arr(index: Long): JsonArr? = get(index)?.as_arr()
    fun get_obj(index: Long): JsonObj? = get(index)?.as_obj()
}

class JsonObj(var raw: MutableMap<String, Any?>) {
    fun get(key: String): JsonValue? = if (raw.containsKey(key)) JsonValue(raw[key]) else null
    fun get_str(key: String): String? = get(key)?.as_str()
    fun get_int(key: String): Long? = get(key)?.as_int()
    fun get_float(key: String): Double? = get(key)?.as_float()
    fun get_bool(key: String): Boolean? = get(key)?.as_bool()
    fun get_arr(key: String): JsonArr? = get(key)?.as_arr()
    fun get_obj(key: String): JsonObj? = get(key)?.as_obj()
}

private fun __pytra_json_unwrap(value: Any?): Any? = when (value) {
    is JsonValue -> value.raw
    is JsonArr -> value.raw
    is JsonObj -> value.raw
    else -> value
}

fun __pytra_loads(v: Any?): JsonValue = JsonValue(pyJsonLoads(v))
fun __pytra_loads_arr(v: Any?): JsonArr = JsonArr(__pytra_as_list(pyJsonLoads(v)))
fun __pytra_loads_obj(v: Any?): JsonObj {
    val out = linkedMapOf<String, Any?>()
    for ((k, value) in __pytra_as_dict(pyJsonLoads(v))) out[__pytra_str(k)] = value
    return JsonObj(out)
}
fun __pytra_dumps(value: Any?, ensure_ascii: Any? = true, indent: Any? = null, separators: Any? = null): String {
    val indentValue = when (indent) {
        is Long -> indent.toInt()
        is Int -> indent
        else -> null
    }
    return __pytra_json_stringify(__pytra_json_unwrap(value), __pytra_truthy(ensure_ascii), indentValue, 0)
}
fun __pytra_sub(pattern: Any?, repl: Any?, text: Any?, count: Any? = 0L): String {
    val regex = Regex(__pytra_str(pattern))
    val limit = __pytra_int(count)
    return if (limit <= 0L) regex.replace(__pytra_str(text), __pytra_str(repl)) else regex.replaceFirst(__pytra_str(text), __pytra_str(repl))
}

private fun __pytra_json_stringify(v: Any?, ensureAscii: Boolean = true, indent: Int? = null, depth: Int = 0): String {
    if (v == null) return "null"
    if (v is Boolean) return if (v) "true" else "false"
    if (v is Int) return v.toString()
    if (v is Long) return v.toString()
    if (v is Double) {
        if (!v.isFinite()) {
            throw RuntimeException("json.dumps: non-finite float")
        }
        return v.toString()
    }
    if (v is Float) {
        if (!v.isFinite()) {
            throw RuntimeException("json.dumps: non-finite float")
        }
        return v.toString()
    }
    if (v is String) return __pytra_json_escape_string(v, ensureAscii)
    if (v is List<*>) {
        val parts = v.map { __pytra_json_stringify(__pytra_json_unwrap(it), ensureAscii, indent, depth + 1) }
        return if (indent != null && indent > 0) {
            val pad = " ".repeat(indent * (depth + 1))
            val closePad = " ".repeat(indent * depth)
            "[\n" + parts.joinToString(",\n") { pad + it } + "\n" + closePad + "]"
        } else {
            parts.joinToString(prefix = "[", postfix = "]", separator = ", ")
        }
    }
    if (v is Map<*, *>) {
        val parts = v.entries.map {
            __pytra_json_escape_string(__pytra_str(it.key), ensureAscii) + ": " + __pytra_json_stringify(__pytra_json_unwrap(it.value), ensureAscii, indent, depth + 1)
        }
        return if (indent != null && indent > 0) {
            val pad = " ".repeat(indent * (depth + 1))
            val closePad = " ".repeat(indent * depth)
            "{\n" + parts.joinToString(",\n") { pad + it } + "\n" + closePad + "}"
        } else {
            parts.joinToString(prefix = "{", postfix = "}", separator = ", ")
        }
    }
    return __pytra_json_escape_string(__pytra_str(v), ensureAscii)
}

private fun __pytra_json_escape_string(s: String, ensureAscii: Boolean = true): String {
    val out = StringBuilder()
    out.append('"')
    for (ch in s) {
        when (ch) {
            '"' -> out.append("\\\"")
            '\\' -> out.append("\\\\")
            '\b' -> out.append("\\b")
            '\u000c' -> out.append("\\f")
            '\n' -> out.append("\\n")
            '\r' -> out.append("\\r")
            '\t' -> out.append("\\t")
            else -> {
                val chCode = ch.toInt()
                if (chCode < 0x20 || (ensureAscii && chCode > 0x7f)) {
                    out.append("\\u")
                    out.append(chCode.toString(16).padStart(4, '0'))
                } else {
                    out.append(ch)
                }
            }
        }
    }
    out.append('"')
    return out.toString()
}

private class __PytraJsonParser(private val text: String) {
    private var i: Int = 0
    private val n: Int = text.length

    fun parse(): Any? {
        skipWs()
        val out = parseValue()
        skipWs()
        if (i != n) {
            throw RuntimeException("invalid json: trailing characters")
        }
        return out
    }

    private fun skipWs() {
        while (i < n) {
            val ch = text[i]
            if (ch == ' ' || ch == '\t' || ch == '\r' || ch == '\n') {
                i += 1
                continue
            }
            return
        }
    }

    private fun parseValue(): Any? {
        if (i >= n) {
            throw RuntimeException("invalid json: unexpected end")
        }
        return when (text[i]) {
            '{' -> parseObject()
            '[' -> parseArray()
            '"' -> parseString()
            else -> {
                if (matchLiteral("true")) {
                    i += 4
                    true
                } else if (matchLiteral("false")) {
                    i += 5
                    false
                } else if (matchLiteral("null")) {
                    i += 4
                    null
                } else {
                    parseNumber()
                }
            }
        }
    }

    private fun matchLiteral(lit: String): Boolean {
        return text.startsWith(lit, i)
    }

    private fun parseObject(): MutableMap<Any, Any?> {
        val out = mutableMapOf<Any, Any?>()
        i += 1 // {
        skipWs()
        if (i < n && text[i] == '}') {
            i += 1
            return out
        }
        while (true) {
            skipWs()
            if (i >= n || text[i] != '"') {
                throw RuntimeException("invalid json object key")
            }
            val key = parseString()
            skipWs()
            if (i >= n || text[i] != ':') {
                throw RuntimeException("invalid json object: missing ':'")
            }
            i += 1
            skipWs()
            out[key] = parseValue()
            skipWs()
            if (i >= n) {
                throw RuntimeException("invalid json object: unexpected end")
            }
            val delim = text[i]
            i += 1
            if (delim == '}') return out
            if (delim != ',') {
                throw RuntimeException("invalid json object separator")
            }
        }
    }

    private fun parseArray(): MutableList<Any?> {
        val out = mutableListOf<Any?>()
        i += 1 // [
        skipWs()
        if (i < n && text[i] == ']') {
            i += 1
            return out
        }
        while (true) {
            skipWs()
            out.add(parseValue())
            skipWs()
            if (i >= n) {
                throw RuntimeException("invalid json array: unexpected end")
            }
            val delim = text[i]
            i += 1
            if (delim == ']') return out
            if (delim != ',') {
                throw RuntimeException("invalid json array separator")
            }
        }
    }

    private fun parseString(): String {
        if (i >= n || text[i] != '"') {
            throw RuntimeException("invalid json string")
        }
        i += 1 // opening quote
        val out = StringBuilder()
        while (i < n) {
            val ch = text[i]
            i += 1
            if (ch == '"') return out.toString()
            if (ch == '\\') {
                if (i >= n) {
                    throw RuntimeException("invalid json string escape")
                }
                val esc = text[i]
                i += 1
                when (esc) {
                    '"', '\\', '/' -> out.append(esc)
                    'b' -> out.append('\b')
                    'f' -> out.append('\u000c')
                    'n' -> out.append('\n')
                    'r' -> out.append('\r')
                    't' -> out.append('\t')
                    'u' -> out.append(parseUnicodeEscape())
                    else -> throw RuntimeException("invalid json escape")
                }
                continue
            }
            out.append(ch)
        }
        throw RuntimeException("unterminated json string")
    }

    private fun parseUnicodeEscape(): Char {
        if (i + 4 > n) {
            throw RuntimeException("invalid json unicode escape")
        }
        var value = 0
        var j = 0
        while (j < 4) {
            val digit = Character.digit(text[i + j], 16)
            if (digit < 0) {
                throw RuntimeException("invalid json unicode escape")
            }
            value = (value shl 4) or digit
            j += 1
        }
        i += 4
        return value.toChar()
    }

    private fun parseNumber(): Any {
        val start = i
        if (text[i] == '-') {
            i += 1
        }
        if (i >= n) {
            throw RuntimeException("invalid json number")
        }
        if (text[i] == '0') {
            i += 1
        } else {
            if (!isDigit(text[i])) {
                throw RuntimeException("invalid json number")
            }
            while (i < n && isDigit(text[i])) {
                i += 1
            }
        }
        var isFloat = false
        if (i < n && text[i] == '.') {
            isFloat = true
            i += 1
            if (i >= n || !isDigit(text[i])) {
                throw RuntimeException("invalid json number")
            }
            while (i < n && isDigit(text[i])) {
                i += 1
            }
        }
        if (i < n && (text[i] == 'e' || text[i] == 'E')) {
            isFloat = true
            i += 1
            if (i < n && (text[i] == '+' || text[i] == '-')) {
                i += 1
            }
            if (i >= n || !isDigit(text[i])) {
                throw RuntimeException("invalid json exponent")
            }
            while (i < n && isDigit(text[i])) {
                i += 1
            }
        }
        val token = text.substring(start, i)
        return try {
            if (isFloat) token.toDouble() else token.toLong()
        } catch (_: NumberFormatException) {
            throw RuntimeException("invalid json number")
        }
    }

    private fun isDigit(ch: Char): Boolean {
        return ch >= '0' && ch <= '9'
    }
}

// --- pathlib ---

class Path(raw: Any?) {
    val value: String = __pytra_str(raw)

    val parent: Path
        get() {
            val parentText = File(value).parent ?: ""
            return Path(parentText)
        }

    val name: String
        get() {
            return File(value).name
        }

    val stem: String
        get() {
            val n = name
            val idx = n.lastIndexOf('.')
            if (idx <= 0) return n
            return n.substring(0, idx)
        }

    fun exists(): Boolean {
        return File(value).exists()
    }

    fun read_text(): String {
        return File(value).readText(Charsets.UTF_8)
    }

    fun write_text(content: Any?): Any? {
        val outFile = File(value)
        val parentDir = outFile.parentFile
        if (parentDir != null && !parentDir.exists()) {
            parentDir.mkdirs()
        }
        outFile.writeText(__pytra_str(content), Charsets.UTF_8)
        return null
    }

    fun mkdir(parents: Any? = false, exist_ok: Any? = false): Any? {
        val dir = File(value)
        val ok = if (__pytra_truthy(parents)) dir.mkdirs() else dir.mkdir()
        if (!ok && dir.exists() && __pytra_truthy(exist_ok)) {
            return null
        }
        if (!dir.exists()) {
            throw RuntimeException("Path.mkdir failed: " + value)
        }
        return null
    }

    fun joinpath(child: Any?): Path {
        return Path(Paths.get(value).resolve(__pytra_str(child)).toString())
    }

    fun joinpath(child1: Any?, child2: Any?): Path {
        return Path(Paths.get(value).resolve(__pytra_str(child1)).resolve(__pytra_str(child2)).toString())
    }

    operator fun div(child: Any?): Path = joinpath(child)

    fun resolve(): Path {
        return Path(Paths.get(value).toAbsolutePath().normalize().toString())
    }

    override fun toString(): String {
        return value
    }
}
