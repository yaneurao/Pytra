import kotlin.math.*


// 04: Sample that renders an orbit-trap Julia set and writes a PNG image.

fun render_orbit_trap_julia(width: Long, height: Long, max_iter: Long, cx: Double, cy: Double): MutableList<Any?> {
    var pixels: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var __hoisted_cast_1: Double = __pytra_float(height - 1L)
    var __hoisted_cast_2: Double = __pytra_float(width - 1L)
    var __hoisted_cast_3: Double = __pytra_float(max_iter)
    var y = __pytra_int(0L)
    while (y < __pytra_int(height)) {
        var zy0: Double = ((-1.3) + (2.6 * (__pytra_float(y) / __hoisted_cast_1)))
        var x = __pytra_int(0L)
        while (x < __pytra_int(width)) {
            var zx: Double = ((-1.9) + (3.8 * (__pytra_float(x) / __hoisted_cast_2)))
            var zy: Double = zy0
            var trap: Double = 1000000000.0
            var i: Long = 0L
            while ((__pytra_int(i) < __pytra_int(max_iter))) {
                var ax: Double = zx
                if ((__pytra_float(ax) < __pytra_float(0.0))) {
                    ax = __pytra_float(-ax)
                }
                var ay: Double = zy
                if ((__pytra_float(ay) < __pytra_float(0.0))) {
                    ay = __pytra_float(-ay)
                }
                var dxy: Double = (zx - zy)
                if ((__pytra_float(dxy) < __pytra_float(0.0))) {
                    dxy = __pytra_float(-dxy)
                }
                if ((__pytra_float(ax) < __pytra_float(trap))) {
                    trap = ax
                }
                if ((__pytra_float(ay) < __pytra_float(trap))) {
                    trap = ay
                }
                if ((__pytra_float(dxy) < __pytra_float(trap))) {
                    trap = dxy
                }
                var zx2: Double = (zx * zx)
                var zy2: Double = (zy * zy)
                if ((__pytra_float(zx2 + zy2) > __pytra_float(4.0))) {
                    break
                }
                zy = (((2.0 * zx) * zy) + cy)
                zx = ((zx2 - zy2) + cx)
                i += 1L
            }
            var r: Long = 0L
            var g: Long = 0L
            var b: Long = 0L
            if ((__pytra_int(i) >= __pytra_int(max_iter))) {
                r = 0L
                g = 0L
                b = 0L
            } else {
                var trap_scaled: Double = (trap * 3.2)
                if ((__pytra_float(trap_scaled) > __pytra_float(1.0))) {
                    trap_scaled = 1.0
                }
                if ((__pytra_float(trap_scaled) < __pytra_float(0.0))) {
                    trap_scaled = 0.0
                }
                var t: Double = (__pytra_float(i) / __hoisted_cast_3)
                var tone: Long = __pytra_int(255.0 * (1.0 - trap_scaled))
                r = __pytra_int(__pytra_float(tone) * (0.35 + (0.65 * t)))
                g = __pytra_int(__pytra_float(tone) * (0.15 + (0.85 * (1.0 - t))))
                b = __pytra_int(255.0 * (0.25 + (0.75 * t)))
                if ((__pytra_int(r) > __pytra_int(255L))) {
                    r = 255L
                }
                if ((__pytra_int(g) > __pytra_int(255L))) {
                    g = 255L
                }
                if ((__pytra_int(b) > __pytra_int(255L))) {
                    b = 255L
                }
            }
            pixels.add(r)
            pixels.add(g)
            pixels.add(b)
            x += 1L
        }
        y += 1L
    }
    return pixels
}

fun run_04_orbit_trap_julia() {
    var width: Long = 1920L
    var height: Long = 1080L
    var max_iter: Long = 1400L
    var out_path: String = "sample/out/04_orbit_trap_julia.png"
    var start: Double = __pytra_perf_counter()
    var pixels: MutableList<Any?> = __pytra_as_list(render_orbit_trap_julia(width, height, max_iter, (-0.7269), 0.1889))
    __pytra_write_rgb_png(out_path, width, height, pixels)
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_04_orbit_trap_julia()
}
