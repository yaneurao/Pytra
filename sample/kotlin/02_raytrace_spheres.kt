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

// 02: Sample that runs a mini sphere-only ray tracer and outputs a PNG image.
// Dependencies are kept minimal (time only) for transpilation compatibility.

fun clamp01(v: Double): Double {
    if ((__pytra_float(v) < __pytra_float(0.0))) {
        return __pytra_float(0.0)
    }
    if ((__pytra_float(v) > __pytra_float(1.0))) {
        return __pytra_float(1.0)
    }
    return __pytra_float(v)
}

fun hit_sphere(ox: Double, oy: Double, oz: Double, dx: Double, dy: Double, dz: Double, cx: Double, cy: Double, cz: Double, r: Double): Double {
    var lx: Double = __pytra_float((__pytra_float(ox) - __pytra_float(cx)))
    var ly: Double = __pytra_float((__pytra_float(oy) - __pytra_float(cy)))
    var lz: Double = __pytra_float((__pytra_float(oz) - __pytra_float(cz)))
    var a: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float(dx) * __pytra_float(dx))) + __pytra_float((__pytra_float(dy) * __pytra_float(dy))))) + __pytra_float((__pytra_float(dz) * __pytra_float(dz)))))
    var b: Double = __pytra_float((__pytra_float(2.0) * __pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(dx))) + __pytra_float((__pytra_float(ly) * __pytra_float(dy))))) + __pytra_float((__pytra_float(lz) * __pytra_float(dz)))))))
    var c: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(lx))) + __pytra_float((__pytra_float(ly) * __pytra_float(ly))))) + __pytra_float((__pytra_float(lz) * __pytra_float(lz))))) - __pytra_float((__pytra_float(r) * __pytra_float(r)))))
    var d: Double = __pytra_float((__pytra_float((__pytra_float(b) * __pytra_float(b))) - __pytra_float((__pytra_float((__pytra_float(4.0) * __pytra_float(a))) * __pytra_float(c)))))
    if ((__pytra_float(d) < __pytra_float(0.0))) {
        return __pytra_float((-1.0))
    }
    var sd: Double = __pytra_float(kotlin.math.sqrt(__pytra_float(d)))
    var t0: Double = __pytra_float((__pytra_float((__pytra_float((-b)) - __pytra_float(sd))) / __pytra_float((__pytra_float(2.0) * __pytra_float(a)))))
    var t1: Double = __pytra_float((__pytra_float((__pytra_float((-b)) + __pytra_float(sd))) / __pytra_float((__pytra_float(2.0) * __pytra_float(a)))))
    if ((__pytra_float(t0) > __pytra_float(0.001))) {
        return __pytra_float(t0)
    }
    if ((__pytra_float(t1) > __pytra_float(0.001))) {
        return __pytra_float(t1)
    }
    return __pytra_float((-1.0))
}

fun render(width: Long, height: Long, aa: Long): MutableList<Any?> {
    var pixels: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var ox: Double = __pytra_float(0.0)
    var oy: Double = __pytra_float(0.0)
    var oz: Double = __pytra_float((-3.0))
    var lx: Double = __pytra_float((-0.4))
    var ly: Double = __pytra_float(0.8)
    var lz: Double = __pytra_float((-0.45))
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float(aa))
    var __hoisted_cast_2: Double = __pytra_float(__pytra_float((__pytra_int(height) - __pytra_int(1L))))
    var __hoisted_cast_3: Double = __pytra_float(__pytra_float((__pytra_int(width) - __pytra_int(1L))))
    var __hoisted_cast_4: Double = __pytra_float(__pytra_float(height))
    val __step_0 = __pytra_int(1L)
    var y = __pytra_int(0L)
    while ((__step_0 >= 0L && y < __pytra_int(height)) || (__step_0 < 0L && y > __pytra_int(height))) {
        val __step_1 = __pytra_int(1L)
        var x = __pytra_int(0L)
        while ((__step_1 >= 0L && x < __pytra_int(width)) || (__step_1 < 0L && x > __pytra_int(width))) {
            var ar: Long = __pytra_int(0L)
            var ag: Long = __pytra_int(0L)
            var ab: Long = __pytra_int(0L)
            val __step_2 = __pytra_int(1L)
            var ay = __pytra_int(0L)
            while ((__step_2 >= 0L && ay < __pytra_int(aa)) || (__step_2 < 0L && ay > __pytra_int(aa))) {
                val __step_3 = __pytra_int(1L)
                var ax = __pytra_int(0L)
                while ((__step_3 >= 0L && ax < __pytra_int(aa)) || (__step_3 < 0L && ax > __pytra_int(aa))) {
                    var fy: Double = __pytra_float((__pytra_float((__pytra_float(y) + __pytra_float((__pytra_float((__pytra_float(ay) + __pytra_float(0.5))) / __pytra_float(__hoisted_cast_1))))) / __pytra_float(__hoisted_cast_2)))
                    var fx: Double = __pytra_float((__pytra_float((__pytra_float(x) + __pytra_float((__pytra_float((__pytra_float(ax) + __pytra_float(0.5))) / __pytra_float(__hoisted_cast_1))))) / __pytra_float(__hoisted_cast_3)))
                    var sy: Double = __pytra_float((__pytra_float(1.0) - __pytra_float((__pytra_float(2.0) * __pytra_float(fy)))))
                    var sx: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float(2.0) * __pytra_float(fx))) - __pytra_float(1.0))) * __pytra_float((__pytra_float(width) / __pytra_float(__hoisted_cast_4)))))
                    var dx: Double = __pytra_float(sx)
                    var dy: Double = __pytra_float(sy)
                    var dz: Double = __pytra_float(1.0)
                    var inv_len: Double = __pytra_float((__pytra_float(1.0) / __pytra_float(kotlin.math.sqrt(__pytra_float((__pytra_float((__pytra_float((__pytra_float(dx) * __pytra_float(dx))) + __pytra_float((__pytra_float(dy) * __pytra_float(dy))))) + __pytra_float((__pytra_float(dz) * __pytra_float(dz)))))))))
                    dx *= inv_len
                    dy *= inv_len
                    dz *= inv_len
                    var t_min: Double = __pytra_float(1e+30)
                    var hit_id: Long = __pytra_int((-1L))
                    var t: Double = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, (-0.8), (-0.2), 2.2, 0.8))
                    if (((__pytra_float(t) > __pytra_float(0.0)) && (__pytra_float(t) < __pytra_float(t_min)))) {
                        t_min = __pytra_float(t)
                        hit_id = __pytra_int(0L)
                    }
                    t = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95))
                    if (((__pytra_float(t) > __pytra_float(0.0)) && (__pytra_float(t) < __pytra_float(t_min)))) {
                        t_min = __pytra_float(t)
                        hit_id = __pytra_int(1L)
                    }
                    t = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, (-1001.0), 3.0, 1000.0))
                    if (((__pytra_float(t) > __pytra_float(0.0)) && (__pytra_float(t) < __pytra_float(t_min)))) {
                        t_min = __pytra_float(t)
                        hit_id = __pytra_int(2L)
                    }
                    var r: Long = __pytra_int(0L)
                    var g: Long = __pytra_int(0L)
                    var b: Long = __pytra_int(0L)
                    if ((__pytra_int(hit_id) >= __pytra_int(0L))) {
                        var px: Double = __pytra_float((__pytra_float(ox) + __pytra_float((__pytra_float(dx) * __pytra_float(t_min)))))
                        var py: Double = __pytra_float((__pytra_float(oy) + __pytra_float((__pytra_float(dy) * __pytra_float(t_min)))))
                        var pz: Double = __pytra_float((__pytra_float(oz) + __pytra_float((__pytra_float(dz) * __pytra_float(t_min)))))
                        var nx: Double = __pytra_float(0.0)
                        var ny: Double = __pytra_float(0.0)
                        var nz: Double = __pytra_float(0.0)
                        if ((__pytra_int(hit_id) == __pytra_int(0L))) {
                            nx = __pytra_float((__pytra_float((__pytra_float(px) + __pytra_float(0.8))) / __pytra_float(0.8)))
                            ny = __pytra_float((__pytra_float((__pytra_float(py) + __pytra_float(0.2))) / __pytra_float(0.8)))
                            nz = __pytra_float((__pytra_float((__pytra_float(pz) - __pytra_float(2.2))) / __pytra_float(0.8)))
                        } else {
                            if ((__pytra_int(hit_id) == __pytra_int(1L))) {
                                nx = __pytra_float((__pytra_float((__pytra_float(px) - __pytra_float(0.9))) / __pytra_float(0.95)))
                                ny = __pytra_float((__pytra_float((__pytra_float(py) - __pytra_float(0.1))) / __pytra_float(0.95)))
                                nz = __pytra_float((__pytra_float((__pytra_float(pz) - __pytra_float(2.9))) / __pytra_float(0.95)))
                            } else {
                                nx = __pytra_float(0.0)
                                ny = __pytra_float(1.0)
                                nz = __pytra_float(0.0)
                            }
                        }
                        var diff: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float(nx) * __pytra_float((-lx)))) + __pytra_float((__pytra_float(ny) * __pytra_float((-ly)))))) + __pytra_float((__pytra_float(nz) * __pytra_float((-lz))))))
                        diff = __pytra_float(clamp01(diff))
                        var base_r: Double = __pytra_float(0.0)
                        var base_g: Double = __pytra_float(0.0)
                        var base_b: Double = __pytra_float(0.0)
                        if ((__pytra_int(hit_id) == __pytra_int(0L))) {
                            base_r = __pytra_float(0.95)
                            base_g = __pytra_float(0.35)
                            base_b = __pytra_float(0.25)
                        } else {
                            if ((__pytra_int(hit_id) == __pytra_int(1L))) {
                                base_r = __pytra_float(0.25)
                                base_g = __pytra_float(0.55)
                                base_b = __pytra_float(0.95)
                            } else {
                                var checker: Long = __pytra_int((__pytra_int(__pytra_int((__pytra_float((__pytra_float(px) + __pytra_float(50.0))) * __pytra_float(0.8)))) + __pytra_int(__pytra_int((__pytra_float((__pytra_float(pz) + __pytra_float(50.0))) * __pytra_float(0.8))))))
                                if ((__pytra_int((__pytra_int(checker) % __pytra_int(2L))) == __pytra_int(0L))) {
                                    base_r = __pytra_float(0.85)
                                    base_g = __pytra_float(0.85)
                                    base_b = __pytra_float(0.85)
                                } else {
                                    base_r = __pytra_float(0.2)
                                    base_g = __pytra_float(0.2)
                                    base_b = __pytra_float(0.2)
                                }
                            }
                        }
                        var shade: Double = __pytra_float((__pytra_float(0.12) + __pytra_float((__pytra_float(0.88) * __pytra_float(diff)))))
                        r = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float(clamp01((__pytra_float(base_r) * __pytra_float(shade)))))))
                        g = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float(clamp01((__pytra_float(base_g) * __pytra_float(shade)))))))
                        b = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float(clamp01((__pytra_float(base_b) * __pytra_float(shade)))))))
                    } else {
                        var tsky: Double = __pytra_float((__pytra_float(0.5) * __pytra_float((__pytra_float(dy) + __pytra_float(1.0)))))
                        r = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float(0.65) + __pytra_float((__pytra_float(0.2) * __pytra_float(tsky))))))))
                        g = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float(0.75) + __pytra_float((__pytra_float(0.18) * __pytra_float(tsky))))))))
                        b = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float(0.9) + __pytra_float((__pytra_float(0.08) * __pytra_float(tsky))))))))
                    }
                    ar += r
                    ag += g
                    ab += b
                    ax += __step_3
                }
                ay += __step_2
            }
            var samples: Long = __pytra_int((__pytra_int(aa) * __pytra_int(aa)))
            pixels = __pytra_as_list(pixels); pixels.add((__pytra_int(__pytra_int(ar) / __pytra_int(samples))))
            pixels = __pytra_as_list(pixels); pixels.add((__pytra_int(__pytra_int(ag) / __pytra_int(samples))))
            pixels = __pytra_as_list(pixels); pixels.add((__pytra_int(__pytra_int(ab) / __pytra_int(samples))))
            x += __step_1
        }
        y += __step_0
    }
    return __pytra_as_list(pixels)
}

fun run_raytrace() {
    var width: Long = __pytra_int(1600L)
    var height: Long = __pytra_int(900L)
    var aa: Long = __pytra_int(2L)
    var out_path: String = __pytra_str("sample/out/02_raytrace_spheres.png")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var pixels: MutableList<Any?> = __pytra_as_list(render(width, height, aa))
    __pytra_noop(out_path, width, height, pixels)
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_raytrace()
}
