import kotlin.math.*


// 01: Sample that outputs the Mandelbrot set as a PNG image.
// Syntax is kept straightforward with future transpilation in mind.

fun escape_count(cx: Double, cy: Double, max_iter: Long): Long {
    var x: Double = __pytra_float(0.0)
    var y: Double = __pytra_float(0.0)
    val __step_0 = __pytra_int(1L)
    var i = __pytra_int(0L)
    while ((__step_0 >= 0L && i < __pytra_int(max_iter)) || (__step_0 < 0L && i > __pytra_int(max_iter))) {
        var x2: Double = __pytra_float((__pytra_float(x) * __pytra_float(x)))
        var y2: Double = __pytra_float((__pytra_float(y) * __pytra_float(y)))
        if ((__pytra_float((__pytra_float(x2) + __pytra_float(y2))) > __pytra_float(4.0))) {
            return __pytra_int(i)
        }
        y = __pytra_float((__pytra_float((__pytra_float((__pytra_float(2.0) * __pytra_float(x))) * __pytra_float(y))) + __pytra_float(cy)))
        x = __pytra_float((__pytra_float((__pytra_float(x2) - __pytra_float(y2))) + __pytra_float(cx)))
        i += __step_0
    }
    return __pytra_int(max_iter)
}

fun color_map(iter_count: Long, max_iter: Long): MutableList<Any?> {
    if ((__pytra_int(iter_count) >= __pytra_int(max_iter))) {
        return __pytra_as_list(mutableListOf(0L, 0L, 0L))
    }
    var t: Double = __pytra_float((__pytra_float(iter_count) / __pytra_float(max_iter)))
    var r: Long = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float(t) * __pytra_float(t))))))
    var g: Long = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float(t))))
    var b: Long = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float(1.0) - __pytra_float(t))))))
    return __pytra_as_list(mutableListOf(r, g, b))
}

fun render_mandelbrot(width: Long, height: Long, max_iter: Long, x_min: Double, x_max: Double, y_min: Double, y_max: Double): MutableList<Any?> {
    var pixels: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float((__pytra_int(height) - __pytra_int(1L))))
    var __hoisted_cast_2: Double = __pytra_float(__pytra_float((__pytra_int(width) - __pytra_int(1L))))
    var __hoisted_cast_3: Double = __pytra_float(__pytra_float(max_iter))
    val __step_0 = __pytra_int(1L)
    var y = __pytra_int(0L)
    while ((__step_0 >= 0L && y < __pytra_int(height)) || (__step_0 < 0L && y > __pytra_int(height))) {
        var py: Double = __pytra_float((__pytra_float(y_min) + __pytra_float((__pytra_float((__pytra_float(y_max) - __pytra_float(y_min))) * __pytra_float((__pytra_float(y) / __pytra_float(__hoisted_cast_1)))))))
        val __step_1 = __pytra_int(1L)
        var x = __pytra_int(0L)
        while ((__step_1 >= 0L && x < __pytra_int(width)) || (__step_1 < 0L && x > __pytra_int(width))) {
            var px: Double = __pytra_float((__pytra_float(x_min) + __pytra_float((__pytra_float((__pytra_float(x_max) - __pytra_float(x_min))) * __pytra_float((__pytra_float(x) / __pytra_float(__hoisted_cast_2)))))))
            var it: Long = __pytra_int(escape_count(px, py, max_iter))
            var r: Long = 0L
            var g: Long = 0L
            var b: Long = 0L
            if ((__pytra_int(it) >= __pytra_int(max_iter))) {
                r = __pytra_int(0L)
                g = __pytra_int(0L)
                b = __pytra_int(0L)
            } else {
                var t: Double = __pytra_float((__pytra_float(it) / __pytra_float(__hoisted_cast_3)))
                r = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float(t) * __pytra_float(t))))))
                g = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float(t))))
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

fun run_mandelbrot() {
    var width: Long = __pytra_int(1600L)
    var height: Long = __pytra_int(1200L)
    var max_iter: Long = __pytra_int(1000L)
    var out_path: String = __pytra_str("sample/out/01_mandelbrot.png")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var pixels: MutableList<Any?> = __pytra_as_list(render_mandelbrot(width, height, max_iter, (-2.2), 1.0, (-1.2), 1.2))
    __pytra_noop(out_path, width, height, pixels)
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_mandelbrot()
}
