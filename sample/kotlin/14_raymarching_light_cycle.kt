import kotlin.math.*


// 14: Sample that outputs a moving-light scene in a simple raymarching style as a GIF.

fun palette(): MutableList<Any?> {
    var p: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var i = __pytra_int(0L)
    while (i < __pytra_int(256L)) {
        var r: Long = __pytra_int(__pytra_min(255L, __pytra_int(__pytra_float(20L) + (__pytra_float(i) * 0.9))))
        var g: Long = __pytra_int(__pytra_min(255L, __pytra_int(__pytra_float(10L) + (__pytra_float(i) * 0.7))))
        var b: Long = __pytra_int(__pytra_min(255L, (30L + i)))
        p.add(r)
        p.add(g)
        p.add(b)
        i += 1L
    }
    return __pytra_as_list(__pytra_bytes(p))
}

fun scene(x: Double, y: Double, light_x: Double, light_y: Double): Long {
    var x1: Double = (x + 0.45)
    var y1: Double = (y + 0.2)
    var x2: Double = (x - 0.35)
    var y2: Double = (y - 0.15)
    var r1: Double = __pytra_float(kotlin.math.sqrt(__pytra_float((x1 * x1) + (y1 * y1))))
    var r2: Double = __pytra_float(kotlin.math.sqrt(__pytra_float((x2 * x2) + (y2 * y2))))
    var blob: Double = __pytra_float(kotlin.math.exp(__pytra_float(((-7.0) * r1) * r1)) + kotlin.math.exp(__pytra_float(((-8.0) * r2) * r2)))
    var lx: Double = (x - light_x)
    var ly: Double = (y - light_y)
    var l: Double = __pytra_float(kotlin.math.sqrt(__pytra_float((lx * lx) + (ly * ly))))
    var lit: Double = __pytra_float(1.0 / __pytra_float(1.0 + ((3.5 * l) * l)))
    var v: Long = __pytra_int(((255.0 * blob) * lit) * 5.0)
    return __pytra_int(__pytra_min(255L, __pytra_max(0L, v)))
}

fun run_14_raymarching_light_cycle() {
    var w: Long = 320L
    var h: Long = 240L
    var frames_n: Long = 84L
    var out_path: String = "sample/out/14_raymarching_light_cycle.gif"
    var start: Double = __pytra_perf_counter()
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var __hoisted_cast_1: Double = __pytra_float(frames_n)
    var __hoisted_cast_2: Double = __pytra_float(h - 1L)
    var __hoisted_cast_3: Double = __pytra_float(w - 1L)
    var t = __pytra_int(0L)
    while (t < __pytra_int(frames_n)) {
        var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((w * h)))
        var a: Double = __pytra_float(((__pytra_float(t) / __hoisted_cast_1) * Math.PI) * 2.0)
        var light_x: Double = __pytra_float(0.75 * kotlin.math.cos(__pytra_float(a)))
        var light_y: Double = __pytra_float(0.55 * kotlin.math.sin(__pytra_float(a * 1.2)))
        var y = __pytra_int(0L)
        while (y < __pytra_int(h)) {
            var row_base: Long = (y * w)
            var py: Double = (((__pytra_float(y) / __hoisted_cast_2) * 2.0) - 1.0)
            var x = __pytra_int(0L)
            while (x < __pytra_int(w)) {
                var px: Double = (((__pytra_float(x) / __hoisted_cast_3) * 2.0) - 1.0)
                __pytra_set_index(frame, (row_base + x), scene(px, py, light_x, light_y))
                x += 1L
            }
            y += 1L
        }
        frames.add(__pytra_bytes(frame))
        t += 1L
    }
    __pytra_noop(out_path, w, h, frames, palette())
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_14_raymarching_light_cycle()
}
