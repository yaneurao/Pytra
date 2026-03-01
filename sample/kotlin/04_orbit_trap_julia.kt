import kotlin.math.*


// 04: Sample that renders an orbit-trap Julia set and writes a PNG image.

fun render_orbit_trap_julia(width: Long, height: Long, max_iter: Long, cx: Double, cy: Double): MutableList<Any?> {
    var pixels: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float((__pytra_int(height) - __pytra_int(1L))))
    var __hoisted_cast_2: Double = __pytra_float(__pytra_float((__pytra_int(width) - __pytra_int(1L))))
    var __hoisted_cast_3: Double = __pytra_float(__pytra_float(max_iter))
    val __step_0 = __pytra_int(1L)
    var y = __pytra_int(0L)
    while ((__step_0 >= 0L && y < __pytra_int(height)) || (__step_0 < 0L && y > __pytra_int(height))) {
        var zy0: Double = __pytra_float((__pytra_float((-1.3)) + __pytra_float((__pytra_float(2.6) * __pytra_float((__pytra_float(y) / __pytra_float(__hoisted_cast_1)))))))
        val __step_1 = __pytra_int(1L)
        var x = __pytra_int(0L)
        while ((__step_1 >= 0L && x < __pytra_int(width)) || (__step_1 < 0L && x > __pytra_int(width))) {
            var zx: Double = __pytra_float((__pytra_float((-1.9)) + __pytra_float((__pytra_float(3.8) * __pytra_float((__pytra_float(x) / __pytra_float(__hoisted_cast_2)))))))
            var zy: Double = __pytra_float(zy0)
            var trap: Double = __pytra_float(1000000000.0)
            var i: Long = __pytra_int(0L)
            while ((__pytra_int(i) < __pytra_int(max_iter))) {
                var ax: Double = __pytra_float(zx)
                if ((__pytra_float(ax) < __pytra_float(0.0))) {
                    ax = __pytra_float((-ax))
                }
                var ay: Double = __pytra_float(zy)
                if ((__pytra_float(ay) < __pytra_float(0.0))) {
                    ay = __pytra_float((-ay))
                }
                var dxy: Double = __pytra_float((__pytra_float(zx) - __pytra_float(zy)))
                if ((__pytra_float(dxy) < __pytra_float(0.0))) {
                    dxy = __pytra_float((-dxy))
                }
                if ((__pytra_float(ax) < __pytra_float(trap))) {
                    trap = __pytra_float(ax)
                }
                if ((__pytra_float(ay) < __pytra_float(trap))) {
                    trap = __pytra_float(ay)
                }
                if ((__pytra_float(dxy) < __pytra_float(trap))) {
                    trap = __pytra_float(dxy)
                }
                var zx2: Double = __pytra_float((__pytra_float(zx) * __pytra_float(zx)))
                var zy2: Double = __pytra_float((__pytra_float(zy) * __pytra_float(zy)))
                if ((__pytra_float((__pytra_float(zx2) + __pytra_float(zy2))) > __pytra_float(4.0))) {
                    break
                }
                zy = __pytra_float((__pytra_float((__pytra_float((__pytra_float(2.0) * __pytra_float(zx))) * __pytra_float(zy))) + __pytra_float(cy)))
                zx = __pytra_float((__pytra_float((__pytra_float(zx2) - __pytra_float(zy2))) + __pytra_float(cx)))
                i += 1L
            }
            var r: Long = __pytra_int(0L)
            var g: Long = __pytra_int(0L)
            var b: Long = __pytra_int(0L)
            if ((__pytra_int(i) >= __pytra_int(max_iter))) {
                r = __pytra_int(0L)
                g = __pytra_int(0L)
                b = __pytra_int(0L)
            } else {
                var trap_scaled: Double = __pytra_float((__pytra_float(trap) * __pytra_float(3.2)))
                if ((__pytra_float(trap_scaled) > __pytra_float(1.0))) {
                    trap_scaled = __pytra_float(1.0)
                }
                if ((__pytra_float(trap_scaled) < __pytra_float(0.0))) {
                    trap_scaled = __pytra_float(0.0)
                }
                var t: Double = __pytra_float((__pytra_float(i) / __pytra_float(__hoisted_cast_3)))
                var tone: Long = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float(1.0) - __pytra_float(trap_scaled))))))
                r = __pytra_int(__pytra_int((__pytra_float(tone) * __pytra_float((__pytra_float(0.35) + __pytra_float((__pytra_float(0.65) * __pytra_float(t))))))))
                g = __pytra_int(__pytra_int((__pytra_float(tone) * __pytra_float((__pytra_float(0.15) + __pytra_float((__pytra_float(0.85) * __pytra_float((__pytra_float(1.0) - __pytra_float(t))))))))))
                b = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float(0.25) + __pytra_float((__pytra_float(0.75) * __pytra_float(t))))))))
                if ((__pytra_int(r) > __pytra_int(255L))) {
                    r = __pytra_int(255L)
                }
                if ((__pytra_int(g) > __pytra_int(255L))) {
                    g = __pytra_int(255L)
                }
                if ((__pytra_int(b) > __pytra_int(255L))) {
                    b = __pytra_int(255L)
                }
            }
            pixels = __pytra_as_list(pixels); pixels.add(r)
            pixels = __pytra_as_list(pixels); pixels.add(g)
            pixels = __pytra_as_list(pixels); pixels.add(b)
            x += __step_1
        }
        y += __step_0
    }
    return __pytra_as_list(pixels)
}

fun run_04_orbit_trap_julia() {
    var width: Long = __pytra_int(1920L)
    var height: Long = __pytra_int(1080L)
    var max_iter: Long = __pytra_int(1400L)
    var out_path: String = __pytra_str("sample/out/04_orbit_trap_julia.png")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var pixels: MutableList<Any?> = __pytra_as_list(render_orbit_trap_julia(width, height, max_iter, (-0.7269), 0.1889))
    __pytra_noop(out_path, width, height, pixels)
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_04_orbit_trap_julia()
}
