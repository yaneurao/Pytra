import kotlin.math.*


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
