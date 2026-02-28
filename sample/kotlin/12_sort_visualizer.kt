import kotlin.math.*

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

// 12: Sample that outputs intermediate states of bubble sort as a GIF.

fun render(values: MutableList<Any?>, w: Long, h: Long): MutableList<Any?> {
    var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
    var n: Long = __pytra_int(__pytra_len(values))
    var bar_w: Double = __pytra_float((__pytra_float(w) / __pytra_float(n)))
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float(n))
    var __hoisted_cast_2: Double = __pytra_float(__pytra_float(h))
    val __step_0 = __pytra_int(1L)
    var i = __pytra_int(0L)
    while ((__step_0 >= 0L && i < __pytra_int(n)) || (__step_0 < 0L && i > __pytra_int(n))) {
        var x0: Long = __pytra_int(__pytra_int((__pytra_float(i) * __pytra_float(bar_w))))
        var x1: Long = __pytra_int(__pytra_int((__pytra_float((__pytra_int(i) + __pytra_int(1L))) * __pytra_float(bar_w))))
        if ((__pytra_int(x1) <= __pytra_int(x0))) {
            x1 = __pytra_int((__pytra_int(x0) + __pytra_int(1L)))
        }
        var bh: Long = __pytra_int(__pytra_int((__pytra_float((__pytra_float(__pytra_int(__pytra_get_index(values, i))) / __pytra_float(__hoisted_cast_1))) * __pytra_float(__hoisted_cast_2))))
        var y: Long = __pytra_int((__pytra_int(h) - __pytra_int(bh)))
        val __step_1 = __pytra_int(1L)
        y = __pytra_int(y)
        while ((__step_1 >= 0L && y < __pytra_int(h)) || (__step_1 < 0L && y > __pytra_int(h))) {
            val __step_2 = __pytra_int(1L)
            var x = __pytra_int(x0)
            while ((__step_2 >= 0L && x < __pytra_int(x1)) || (__step_2 < 0L && x > __pytra_int(x1))) {
                __pytra_set_index(frame, (__pytra_int((__pytra_int(y) * __pytra_int(w))) + __pytra_int(x)), 255L)
                x += __step_2
            }
            y += __step_1
        }
        i += __step_0
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

fun run_12_sort_visualizer() {
    var w: Long = __pytra_int(320L)
    var h: Long = __pytra_int(180L)
    var n: Long = __pytra_int(124L)
    var out_path: String = __pytra_str("sample/out/12_sort_visualizer.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var values: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __step_0 = __pytra_int(1L)
    var i = __pytra_int(0L)
    while ((__step_0 >= 0L && i < __pytra_int(n)) || (__step_0 < 0L && i > __pytra_int(n))) {
        values = __pytra_as_list(values); values.add((__pytra_int((__pytra_int((__pytra_int(i) * __pytra_int(37L))) + __pytra_int(19L))) % __pytra_int(n)))
        i += __step_0
    }
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf(render(values, w, h)))
    var frame_stride: Long = __pytra_int(16L)
    var op: Long = __pytra_int(0L)
    val __step_1 = __pytra_int(1L)
    i = __pytra_int(0L)
    while ((__step_1 >= 0L && i < __pytra_int(n)) || (__step_1 < 0L && i > __pytra_int(n))) {
        var swapped: Boolean = __pytra_truthy(false)
        val __step_2 = __pytra_int(1L)
        var j = __pytra_int(0L)
        while ((__step_2 >= 0L && j < __pytra_int((__pytra_int((__pytra_int(n) - __pytra_int(i))) - __pytra_int(1L)))) || (__step_2 < 0L && j > __pytra_int((__pytra_int((__pytra_int(n) - __pytra_int(i))) - __pytra_int(1L))))) {
            if ((__pytra_int(__pytra_int(__pytra_get_index(values, j))) > __pytra_int(__pytra_int(__pytra_get_index(values, (__pytra_int(j) + __pytra_int(1L))))))) {
                val __tuple_3 = __pytra_as_list(mutableListOf(__pytra_int(__pytra_get_index(values, (__pytra_int(j) + __pytra_int(1L)))), __pytra_int(__pytra_get_index(values, j))))
                __pytra_set_index(values, j, __pytra_int(__tuple_3[0]))
                __pytra_set_index(values, (__pytra_int(j) + __pytra_int(1L)), __pytra_int(__tuple_3[1]))
                swapped = __pytra_truthy(true)
            }
            if ((__pytra_int((__pytra_int(op) % __pytra_int(frame_stride))) == __pytra_int(0L))) {
                frames = __pytra_as_list(frames); frames.add(render(values, w, h))
            }
            op += 1L
            j += __step_2
        }
        if ((!swapped)) {
            break
        }
        i += __step_1
    }
    __pytra_noop(out_path, w, h, frames, mutableListOf<Any?>())
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_12_sort_visualizer()
}
