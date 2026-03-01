import kotlin.math.*


// 03: Sample that outputs a Julia set as a PNG image.
// Implemented with simple loop-centric logic for transpilation compatibility.

fun render_julia(width: Long, height: Long, max_iter: Long, cx: Double, cy: Double): MutableList<Any?> {
    var pixels: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float((__pytra_int(height) - __pytra_int(1L))))
    var __hoisted_cast_2: Double = __pytra_float(__pytra_float((__pytra_int(width) - __pytra_int(1L))))
    var __hoisted_cast_3: Double = __pytra_float(__pytra_float(max_iter))
    val __step_0 = __pytra_int(1L)
    var y = __pytra_int(0L)
    while ((__step_0 >= 0L && y < __pytra_int(height)) || (__step_0 < 0L && y > __pytra_int(height))) {
        var zy0: Double = __pytra_float((__pytra_float((-1.2)) + __pytra_float((__pytra_float(2.4) * __pytra_float((__pytra_float(y) / __pytra_float(__hoisted_cast_1)))))))
        val __step_1 = __pytra_int(1L)
        var x = __pytra_int(0L)
        while ((__step_1 >= 0L && x < __pytra_int(width)) || (__step_1 < 0L && x > __pytra_int(width))) {
            var zx: Double = __pytra_float((__pytra_float((-1.8)) + __pytra_float((__pytra_float(3.6) * __pytra_float((__pytra_float(x) / __pytra_float(__hoisted_cast_2)))))))
            var zy: Double = __pytra_float(zy0)
            var i: Long = __pytra_int(0L)
            while ((__pytra_int(i) < __pytra_int(max_iter))) {
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
                var t: Double = __pytra_float((__pytra_float(i) / __pytra_float(__hoisted_cast_3)))
                r = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float(0.2) + __pytra_float((__pytra_float(0.8) * __pytra_float(t))))))))
                g = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float(0.1) + __pytra_float((__pytra_float(0.9) * __pytra_float((__pytra_float(t) * __pytra_float(t))))))))))
                b = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float(1.0) - __pytra_float(t))))))
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

fun run_julia() {
    var width: Long = __pytra_int(3840L)
    var height: Long = __pytra_int(2160L)
    var max_iter: Long = __pytra_int(20000L)
    var out_path: String = __pytra_str("sample/out/03_julia_set.png")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var pixels: MutableList<Any?> = __pytra_as_list(render_julia(width, height, max_iter, (-0.8), 0.156))
    __pytra_noop(out_path, width, height, pixels)
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_julia()
}
