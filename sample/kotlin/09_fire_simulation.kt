// Auto-generated Pytra Kotlin native source from EAST3.
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

fun fire_palette(): MutableList<Any?> {
    var p: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __step_0 = __pytra_int(1L)
    var i = __pytra_int(0L)
    while ((__step_0 >= 0L && i < __pytra_int(256L)) || (__step_0 < 0L && i > __pytra_int(256L))) {
        var r: Long = __pytra_int(0L)
        var g: Long = __pytra_int(0L)
        var b: Long = __pytra_int(0L)
        if ((__pytra_int(i) < __pytra_int(85L))) {
            r = __pytra_int((__pytra_int(i) * __pytra_int(3L)))
            g = __pytra_int(0L)
            b = __pytra_int(0L)
        } else {
            if ((__pytra_int(i) < __pytra_int(170L))) {
                r = __pytra_int(255L)
                g = __pytra_int((__pytra_int((__pytra_int(i) - __pytra_int(85L))) * __pytra_int(3L)))
                b = __pytra_int(0L)
            } else {
                r = __pytra_int(255L)
                g = __pytra_int(255L)
                b = __pytra_int((__pytra_int((__pytra_int(i) - __pytra_int(170L))) * __pytra_int(3L)))
            }
        }
        p = __pytra_as_list(p); p.add(r)
        p = __pytra_as_list(p); p.add(g)
        p = __pytra_as_list(p); p.add(b)
        i += __step_0
    }
    return __pytra_bytes(p)
}

fun run_09_fire_simulation() {
    var w: Long = __pytra_int(380L)
    var h: Long = __pytra_int(260L)
    var steps: Long = __pytra_int(420L)
    var out_path: String = __pytra_str("sample/out/09_fire_simulation.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var heat: MutableList<Any?> = __pytra_as_list(run { val __out = mutableListOf<Any?>(); val __step = __pytra_int(1L); var __lc_i = __pytra_int(0L); while ((__step >= 0L && __lc_i < __pytra_int(h)) || (__step < 0L && __lc_i > __pytra_int(h))) { __out.add(__pytra_list_repeat(0L, w)); __lc_i += __step }; __out })
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __step_0 = __pytra_int(1L)
    var t = __pytra_int(0L)
    while ((__step_0 >= 0L && t < __pytra_int(steps)) || (__step_0 < 0L && t > __pytra_int(steps))) {
        val __step_1 = __pytra_int(1L)
        var x = __pytra_int(0L)
        while ((__step_1 >= 0L && x < __pytra_int(w)) || (__step_1 < 0L && x > __pytra_int(w))) {
            var val_: Long = __pytra_int((__pytra_int(170L) + __pytra_int((__pytra_int((__pytra_int((__pytra_int(x) * __pytra_int(13L))) + __pytra_int((__pytra_int(t) * __pytra_int(17L))))) % __pytra_int(86L)))))
            __pytra_set_index(__pytra_as_list(__pytra_get_index(heat, (__pytra_int(h) - __pytra_int(1L)))), x, val_)
            x += __step_1
        }
        val __step_2 = __pytra_int(1L)
        var y = __pytra_int(1L)
        while ((__step_2 >= 0L && y < __pytra_int(h)) || (__step_2 < 0L && y > __pytra_int(h))) {
            val __step_3 = __pytra_int(1L)
            var x = __pytra_int(0L)
            while ((__step_3 >= 0L && x < __pytra_int(w)) || (__step_3 < 0L && x > __pytra_int(w))) {
                var a: Long = __pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)), x)))
                var b: Long = __pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)), (__pytra_int((__pytra_int((__pytra_int(x) - __pytra_int(1L))) + __pytra_int(w))) % __pytra_int(w)))))
                var c: Long = __pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)), (__pytra_int((__pytra_int(x) + __pytra_int(1L))) % __pytra_int(w)))))
                var d: Long = __pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, (__pytra_int((__pytra_int(y) + __pytra_int(1L))) % __pytra_int(h)))), x)))
                var v: Long = __pytra_int((__pytra_int(__pytra_int((__pytra_int((__pytra_int((__pytra_int(a) + __pytra_int(b))) + __pytra_int(c))) + __pytra_int(d))) / __pytra_int(4L))))
                var cool: Long = __pytra_int((__pytra_int(1L) + __pytra_int((__pytra_int((__pytra_int((__pytra_int(x) + __pytra_int(y))) + __pytra_int(t))) % __pytra_int(3L)))))
                var nv: Long = __pytra_int((__pytra_int(v) - __pytra_int(cool)))
                __pytra_set_index(__pytra_as_list(__pytra_get_index(heat, (__pytra_int(y) - __pytra_int(1L)))), x, __pytra_ifexp((__pytra_int(nv) > __pytra_int(0L)), nv, 0L))
                x += __step_3
            }
            y += __step_2
        }
        var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
        val __step_4 = __pytra_int(1L)
        var yy = __pytra_int(0L)
        while ((__step_4 >= 0L && yy < __pytra_int(h)) || (__step_4 < 0L && yy > __pytra_int(h))) {
            var row_base: Long = __pytra_int((__pytra_int(yy) * __pytra_int(w)))
            val __step_5 = __pytra_int(1L)
            var xx = __pytra_int(0L)
            while ((__step_5 >= 0L && xx < __pytra_int(w)) || (__step_5 < 0L && xx > __pytra_int(w))) {
                __pytra_set_index(frame, (__pytra_int(row_base) + __pytra_int(xx)), __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, yy)), xx)))
                xx += __step_5
            }
            yy += __step_4
        }
        frames = __pytra_as_list(frames); frames.add(__pytra_bytes(frame))
        t += __step_0
    }
    __pytra_noop(out_path, w, h, frames, fire_palette())
    var elapsed: Double = __pytra_float((__pytra_perf_counter() - start))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_09_fire_simulation()
}
