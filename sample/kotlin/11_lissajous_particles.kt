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

// 11: Sample that outputs Lissajous-motion particles as a GIF.

fun color_palette(): MutableList<Any?> {
    var p: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __step_0 = __pytra_int(1L)
    var i = __pytra_int(0L)
    while ((__step_0 >= 0L && i < __pytra_int(256L)) || (__step_0 < 0L && i > __pytra_int(256L))) {
        var r: Long = __pytra_int(i)
        var g: Long = __pytra_int((__pytra_int((__pytra_int(i) * __pytra_int(3L))) % __pytra_int(256L)))
        var b: Long = __pytra_int((__pytra_int(255L) - __pytra_int(i)))
        p = __pytra_as_list(p); p.add(r)
        p = __pytra_as_list(p); p.add(g)
        p = __pytra_as_list(p); p.add(b)
        i += __step_0
    }
    return __pytra_as_list(__pytra_bytes(p))
}

fun run_11_lissajous_particles() {
    var w: Long = __pytra_int(320L)
    var h: Long = __pytra_int(240L)
    var frames_n: Long = __pytra_int(360L)
    var particles: Long = __pytra_int(48L)
    var out_path: String = __pytra_str("sample/out/11_lissajous_particles.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __step_0 = __pytra_int(1L)
    var t = __pytra_int(0L)
    while ((__step_0 >= 0L && t < __pytra_int(frames_n)) || (__step_0 < 0L && t > __pytra_int(frames_n))) {
        var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
        var __hoisted_cast_1: Double = __pytra_float(__pytra_float(t))
        val __step_1 = __pytra_int(1L)
        var p = __pytra_int(0L)
        while ((__step_1 >= 0L && p < __pytra_int(particles)) || (__step_1 < 0L && p > __pytra_int(particles))) {
            var phase: Double = __pytra_float((__pytra_float(p) * __pytra_float(0.261799)))
            var x: Long = __pytra_int(__pytra_int(((__pytra_float(w) * __pytra_float(0.5)) + ((__pytra_float(w) * __pytra_float(0.38)) * kotlin.math.sin(__pytra_float((__pytra_float((__pytra_float(0.11) * __pytra_float(__hoisted_cast_1))) + __pytra_float((__pytra_float(phase) * __pytra_float(2.0))))))))))
            var y: Long = __pytra_int(__pytra_int(((__pytra_float(h) * __pytra_float(0.5)) + ((__pytra_float(h) * __pytra_float(0.38)) * kotlin.math.sin(__pytra_float((__pytra_float((__pytra_float(0.17) * __pytra_float(__hoisted_cast_1))) + __pytra_float((__pytra_float(phase) * __pytra_float(3.0))))))))))
            var color: Long = __pytra_int((__pytra_int(30L) + __pytra_int((__pytra_int((__pytra_int(p) * __pytra_int(9L))) % __pytra_int(220L)))))
            val __step_2 = __pytra_int(1L)
            var dy = __pytra_int((-2L))
            while ((__step_2 >= 0L && dy < __pytra_int(3L)) || (__step_2 < 0L && dy > __pytra_int(3L))) {
                val __step_3 = __pytra_int(1L)
                var dx = __pytra_int((-2L))
                while ((__step_3 >= 0L && dx < __pytra_int(3L)) || (__step_3 < 0L && dx > __pytra_int(3L))) {
                    var xx: Long = __pytra_int((__pytra_int(x) + __pytra_int(dx)))
                    var yy: Long = __pytra_int((__pytra_int(y) + __pytra_int(dy)))
                    if (((__pytra_int(xx) >= __pytra_int(0L)) && (__pytra_int(xx) < __pytra_int(w)) && (__pytra_int(yy) >= __pytra_int(0L)) && (__pytra_int(yy) < __pytra_int(h)))) {
                        var d2: Long = __pytra_int((__pytra_int((__pytra_int(dx) * __pytra_int(dx))) + __pytra_int((__pytra_int(dy) * __pytra_int(dy)))))
                        if ((__pytra_int(d2) <= __pytra_int(4L))) {
                            var idx: Long = __pytra_int((__pytra_int((__pytra_int(yy) * __pytra_int(w))) + __pytra_int(xx)))
                            var v: Long = __pytra_int((__pytra_int(color) - __pytra_int((__pytra_int(d2) * __pytra_int(20L)))))
                            v = __pytra_int(__pytra_max(0L, v))
                            if ((__pytra_int(v) > __pytra_int(__pytra_int(__pytra_get_index(frame, idx))))) {
                                __pytra_set_index(frame, idx, v)
                            }
                        }
                    }
                    dx += __step_3
                }
                dy += __step_2
            }
            p += __step_1
        }
        frames = __pytra_as_list(frames); frames.add(__pytra_bytes(frame))
        t += __step_0
    }
    __pytra_noop(out_path, w, h, frames, color_palette())
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_11_lissajous_particles()
}
