import kotlin.math.*


// 09: Sample that outputs a simple fire effect as a GIF.

fun fire_palette(): MutableList<Any?> {
    var p: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var i = __pytra_int(0L)
    while (i < __pytra_int(256L)) {
        var r: Long = 0L
        var g: Long = 0L
        var b: Long = 0L
        if ((__pytra_int(i) < __pytra_int(85L))) {
            r = (i * 3L)
            g = 0L
            b = 0L
        } else {
            if ((__pytra_int(i) < __pytra_int(170L))) {
                r = 255L
                g = ((i - 85L) * 3L)
                b = 0L
            } else {
                r = 255L
                g = 255L
                b = ((i - 170L) * 3L)
            }
        }
        p.add(r)
        p.add(g)
        p.add(b)
        i += 1L
    }
    return __pytra_as_list(__pytra_bytes(p))
}

fun run_09_fire_simulation() {
    var w: Long = 380L
    var h: Long = 260L
    var steps: Long = 420L
    var out_path: String = "sample/out/09_fire_simulation.gif"
    var start: Double = __pytra_perf_counter()
    var heat: MutableList<Any?> = __pytra_as_list(run { val __out = mutableListOf<Any?>(); val __step = __pytra_int(1L); var __lc_i = __pytra_int(0L); while ((__step >= 0L && __lc_i < __pytra_int(h)) || (__step < 0L && __lc_i > __pytra_int(h))) { __out.add(__pytra_list_repeat(0L, w)); __lc_i += __step }; __out })
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var t = __pytra_int(0L)
    while (t < __pytra_int(steps)) {
        var x = __pytra_int(0L)
        while (x < __pytra_int(w)) {
            var val_: Long = (170L + (((x * 13L) + (t * 17L)) % 86L))
            __pytra_set_index(__pytra_as_list(__pytra_get_index(heat, (h - 1L))), x, val_)
            x += 1L
        }
        var y = __pytra_int(1L)
        while (y < __pytra_int(h)) {
            x = __pytra_int(0L)
            while (x < __pytra_int(w)) {
                var a: Long = __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)), x))
                var b: Long = __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)), (((x - 1L) + w) % w)))
                var c: Long = __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)), ((x + 1L) % w)))
                var d: Long = __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, ((y + 1L) % h))), x))
                var v: Long = ((((a + b) + c) + d) / 4L)
                var cool: Long = (1L + (((x + y) + t) % 3L))
                var nv: Long = (v - cool)
                __pytra_set_index(__pytra_as_list(__pytra_get_index(heat, (y - 1L))), x, __pytra_ifexp((__pytra_int(nv) > __pytra_int(0L)), nv, 0L))
                x += 1L
            }
            y += 1L
        }
        var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((w * h)))
        var yy = __pytra_int(0L)
        while (yy < __pytra_int(h)) {
            var row_base: Long = (yy * w)
            var xx = __pytra_int(0L)
            while (xx < __pytra_int(w)) {
                __pytra_set_index(frame, (row_base + xx), __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, yy)), xx)))
                xx += 1L
            }
            yy += 1L
        }
        frames.add(__pytra_bytes(frame))
        t += 1L
    }
    __pytra_noop(out_path, w, h, frames, fire_palette())
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_09_fire_simulation()
}
