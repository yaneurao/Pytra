import kotlin.math.*


// 11: Sample that outputs Lissajous-motion particles as a GIF.

fun color_palette(): MutableList<Any?> {
    var p: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var i = __pytra_int(0L)
    while (i < __pytra_int(256L)) {
        var r: Long = i
        var g: Long = ((i * 3L) % 256L)
        var b: Long = (255L - i)
        p.add(r)
        p.add(g)
        p.add(b)
        i += 1L
    }
    return __pytra_as_list(__pytra_bytes(p))
}

fun run_11_lissajous_particles() {
    var w: Long = 320L
    var h: Long = 240L
    var frames_n: Long = 360L
    var particles: Long = 48L
    var out_path: String = "sample/out/11_lissajous_particles.gif"
    var start: Double = __pytra_perf_counter()
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var t = __pytra_int(0L)
    while (t < __pytra_int(frames_n)) {
        var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((w * h)))
        var __hoisted_cast_1: Double = __pytra_float(t)
        var p = __pytra_int(0L)
        while (p < __pytra_int(particles)) {
            var phase: Double = (__pytra_float(p) * 0.261799)
            var x: Long = __pytra_int((__pytra_float(w) * 0.5) + ((__pytra_float(w) * 0.38) * kotlin.math.sin(__pytra_float((0.11 * __hoisted_cast_1) + (phase * 2.0)))))
            var y: Long = __pytra_int((__pytra_float(h) * 0.5) + ((__pytra_float(h) * 0.38) * kotlin.math.sin(__pytra_float((0.17 * __hoisted_cast_1) + (phase * 3.0)))))
            var color: Long = (30L + ((p * 9L) % 220L))
            var dy = __pytra_int(-2L)
            while (dy < __pytra_int(3L)) {
                var dx = __pytra_int(-2L)
                while (dx < __pytra_int(3L)) {
                    var xx: Long = (x + dx)
                    var yy: Long = (y + dy)
                    if (((__pytra_int(xx) >= __pytra_int(0L)) && (__pytra_int(xx) < __pytra_int(w)) && (__pytra_int(yy) >= __pytra_int(0L)) && (__pytra_int(yy) < __pytra_int(h)))) {
                        var d2: Long = ((dx * dx) + (dy * dy))
                        if ((__pytra_int(d2) <= __pytra_int(4L))) {
                            var idx: Long = ((yy * w) + xx)
                            var v: Long = (color - (d2 * 20L))
                            v = __pytra_int(__pytra_max(0L, v))
                            if ((__pytra_int(v) > __pytra_int(__pytra_get_index(frame, idx)))) {
                                __pytra_set_index(frame, idx, v)
                            }
                        }
                    }
                    dx += 1L
                }
                dy += 1L
            }
            p += 1L
        }
        frames.add(__pytra_bytes(frame))
        t += 1L
    }
    __pytra_noop(out_path, w, h, frames, color_palette())
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_11_lissajous_particles()
}
