import kotlin.math.*


// 09: Sample that outputs a simple fire effect as a GIF.

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
    return __pytra_as_list(__pytra_bytes(p))
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
            x = __pytra_int(0L)
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
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_09_fire_simulation()
}
