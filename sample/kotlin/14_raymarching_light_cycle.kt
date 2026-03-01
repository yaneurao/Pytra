import kotlin.math.*


// 14: Sample that outputs a moving-light scene in a simple raymarching style as a GIF.

fun palette(): MutableList<Any?> {
    var p: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __step_0 = __pytra_int(1L)
    var i = __pytra_int(0L)
    while ((__step_0 >= 0L && i < __pytra_int(256L)) || (__step_0 < 0L && i > __pytra_int(256L))) {
        var r: Long = __pytra_int(__pytra_min(255L, __pytra_int((__pytra_float(20L) + __pytra_float((__pytra_float(i) * __pytra_float(0.9)))))))
        var g: Long = __pytra_int(__pytra_min(255L, __pytra_int((__pytra_float(10L) + __pytra_float((__pytra_float(i) * __pytra_float(0.7)))))))
        var b: Long = __pytra_int(__pytra_min(255L, (__pytra_int(30L) + __pytra_int(i))))
        p = __pytra_as_list(p); p.add(r)
        p = __pytra_as_list(p); p.add(g)
        p = __pytra_as_list(p); p.add(b)
        i += __step_0
    }
    return __pytra_as_list(__pytra_bytes(p))
}

fun scene(x: Double, y: Double, light_x: Double, light_y: Double): Long {
    var x1: Double = __pytra_float((__pytra_float(x) + __pytra_float(0.45)))
    var y1: Double = __pytra_float((__pytra_float(y) + __pytra_float(0.2)))
    var x2: Double = __pytra_float((__pytra_float(x) - __pytra_float(0.35)))
    var y2: Double = __pytra_float((__pytra_float(y) - __pytra_float(0.15)))
    var r1: Double = __pytra_float(kotlin.math.sqrt(__pytra_float((__pytra_float((__pytra_float(x1) * __pytra_float(x1))) + __pytra_float((__pytra_float(y1) * __pytra_float(y1)))))))
    var r2: Double = __pytra_float(kotlin.math.sqrt(__pytra_float((__pytra_float((__pytra_float(x2) * __pytra_float(x2))) + __pytra_float((__pytra_float(y2) * __pytra_float(y2)))))))
    var blob: Double = __pytra_float((kotlin.math.exp(__pytra_float((((-7.0) * r1) * r1))) + kotlin.math.exp(__pytra_float((((-8.0) * r2) * r2)))))
    var lx: Double = __pytra_float((__pytra_float(x) - __pytra_float(light_x)))
    var ly: Double = __pytra_float((__pytra_float(y) - __pytra_float(light_y)))
    var l: Double = __pytra_float(kotlin.math.sqrt(__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(lx))) + __pytra_float((__pytra_float(ly) * __pytra_float(ly)))))))
    var lit: Double = __pytra_float((__pytra_float(1.0) / __pytra_float((1.0 + ((3.5 * l) * l)))))
    var v: Long = __pytra_int(__pytra_int((((255.0 * blob) * lit) * 5.0)))
    return __pytra_int(__pytra_min(255L, __pytra_max(0L, v)))
}

fun run_14_raymarching_light_cycle() {
    var w: Long = __pytra_int(320L)
    var h: Long = __pytra_int(240L)
    var frames_n: Long = __pytra_int(84L)
    var out_path: String = __pytra_str("sample/out/14_raymarching_light_cycle.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float(frames_n))
    var __hoisted_cast_2: Double = __pytra_float(__pytra_float((__pytra_int(h) - __pytra_int(1L))))
    var __hoisted_cast_3: Double = __pytra_float(__pytra_float((__pytra_int(w) - __pytra_int(1L))))
    val __step_0 = __pytra_int(1L)
    var t = __pytra_int(0L)
    while ((__step_0 >= 0L && t < __pytra_int(frames_n)) || (__step_0 < 0L && t > __pytra_int(frames_n))) {
        var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
        var a: Double = __pytra_float((((__pytra_float(t) / __pytra_float(__hoisted_cast_1)) * Math.PI) * 2.0))
        var light_x: Double = __pytra_float((0.75 * kotlin.math.cos(__pytra_float(a))))
        var light_y: Double = __pytra_float((0.55 * kotlin.math.sin(__pytra_float((a * 1.2)))))
        val __step_1 = __pytra_int(1L)
        var y = __pytra_int(0L)
        while ((__step_1 >= 0L && y < __pytra_int(h)) || (__step_1 < 0L && y > __pytra_int(h))) {
            var row_base: Long = __pytra_int((__pytra_int(y) * __pytra_int(w)))
            var py: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float(y) / __pytra_float(__hoisted_cast_2))) * __pytra_float(2.0))) - __pytra_float(1.0)))
            val __step_2 = __pytra_int(1L)
            var x = __pytra_int(0L)
            while ((__step_2 >= 0L && x < __pytra_int(w)) || (__step_2 < 0L && x > __pytra_int(w))) {
                var px: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float(x) / __pytra_float(__hoisted_cast_3))) * __pytra_float(2.0))) - __pytra_float(1.0)))
                __pytra_set_index(frame, (__pytra_int(row_base) + __pytra_int(x)), scene(px, py, light_x, light_y))
                x += __step_2
            }
            y += __step_1
        }
        frames = __pytra_as_list(frames); frames.add(__pytra_bytes(frame))
        t += __step_0
    }
    __pytra_noop(out_path, w, h, frames, palette())
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_14_raymarching_light_cycle()
}
