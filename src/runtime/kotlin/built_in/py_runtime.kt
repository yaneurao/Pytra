// Kotlin native runtime helpers for Pytra-generated code.
import kotlin.math.*
import java.io.File
import java.io.FileOutputStream
import java.nio.file.Paths

class PyTuple(items: Collection<Any?> = emptyList()) : ArrayList<Any?>(items)

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

class PyFile(private val path: String, private val mode: String) {
    private val stream = FileOutputStream(path)

    fun write(data: Any?) {
        when (data) {
            is MutableList<*> -> {
                val bytes = ByteArray(data.size)
                var i = 0
                while (i < data.size) {
                    bytes[i] = (__pytra_int(data[i]) and 0xFF).toByte()
                    i += 1
                }
                stream.write(bytes)
            }
            is String -> stream.write(data.toByteArray(Charsets.UTF_8))
            else -> stream.write(__pytra_str(data).toByteArray(Charsets.UTF_8))
        }
    }

    fun close() {
        stream.close()
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

private fun __pytra_repr(v: Any?): String {
    if (v == null) return "None"
    if (v is Boolean) return if (v) "True" else "False"
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
fun __pytra_upper(v: Any?): String = __pytra_str(v).uppercase()
fun __pytra_lower(v: Any?): String = __pytra_str(v).lowercase()
fun __pytra_find(v: Any?, sub: Any?): Long = __pytra_str(v).indexOf(__pytra_str(sub)).toLong()
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
        if (container.isEmpty()) return __pytra_any_default()
        val i = __pytra_index(__pytra_int(index), container.size.toLong())
        if (i < 0L || i >= container.size.toLong()) return __pytra_any_default()
        return container[i.toInt()]
    }
    if (container is Map<*, *>) {
        return container[index] ?: __pytra_any_default()
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

private fun __pytra_json_stringify(v: Any?): String {
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
    if (v is String) return __pytra_json_escape_string(v)
    if (v is List<*>) {
        return v.joinToString(prefix = "[", postfix = "]", separator = ",") { __pytra_json_stringify(it) }
    }
    if (v is Map<*, *>) {
        return v.entries.joinToString(prefix = "{", postfix = "}", separator = ",") {
            __pytra_json_escape_string(__pytra_str(it.key)) + ":" + __pytra_json_stringify(it.value)
        }
    }
    return __pytra_json_escape_string(__pytra_str(v))
}

private fun __pytra_json_escape_string(s: String): String {
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
                if (ch.toInt() < 0x20) {
                    out.append("\\u")
                    out.append(ch.toInt().toString(16).padStart(4, '0'))
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

    fun resolve(): Path {
        return Path(Paths.get(value).toAbsolutePath().normalize().toString())
    }

    override fun toString(): String {
        return value
    }
}
