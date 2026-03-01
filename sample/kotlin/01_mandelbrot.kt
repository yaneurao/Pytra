import kotlin.math.*


// 01: Sample that outputs the Mandelbrot set as a PNG image.
// Syntax is kept straightforward with future transpilation in mind.

fun escape_count(cx: Double, cy: Double, max_iter: Long): Long {
    var x: Double = 0.0
    var y: Double = 0.0
    var i = __pytra_int(0L)
    while (i < __pytra_int(max_iter)) {
        var x2: Double = (x * x)
        var y2: Double = (y * y)
        if ((__pytra_float(x2 + y2) > __pytra_float(4.0))) {
            return i
        }
        y = (((2.0 * x) * y) + cy)
        x = ((x2 - y2) + cx)
        i += 1L
    }
    return max_iter
}

fun color_map(iter_count: Long, max_iter: Long): MutableList<Any?> {
    if ((__pytra_int(iter_count) >= __pytra_int(max_iter))) {
        return __pytra_as_list(mutableListOf(0L, 0L, 0L))
    }
    var t: Double = (__pytra_float(iter_count) / __pytra_float(max_iter))
    var r: Long = __pytra_int(255.0 * (t * t))
    var g: Long = __pytra_int(255.0 * t)
    var b: Long = __pytra_int(255.0 * (1.0 - t))
    return __pytra_as_list(mutableListOf(r, g, b))
}

fun render_mandelbrot(width: Long, height: Long, max_iter: Long, x_min: Double, x_max: Double, y_min: Double, y_max: Double): MutableList<Any?> {
    var pixels: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var __hoisted_cast_1: Double = __pytra_float(height - 1L)
    var __hoisted_cast_2: Double = __pytra_float(width - 1L)
    var __hoisted_cast_3: Double = __pytra_float(max_iter)
    var y = __pytra_int(0L)
    while (y < __pytra_int(height)) {
        var py: Double = (y_min + ((y_max - y_min) * (__pytra_float(y) / __hoisted_cast_1)))
        var x = __pytra_int(0L)
        while (x < __pytra_int(width)) {
            var px: Double = (x_min + ((x_max - x_min) * (__pytra_float(x) / __hoisted_cast_2)))
            var it: Long = __pytra_int(escape_count(px, py, max_iter))
            var r: Long = 0L
            var g: Long = 0L
            var b: Long = 0L
            if ((__pytra_int(it) >= __pytra_int(max_iter))) {
                r = 0L
                g = 0L
                b = 0L
            } else {
                var t: Double = (__pytra_float(it) / __hoisted_cast_3)
                r = __pytra_int(255.0 * (t * t))
                g = __pytra_int(255.0 * t)
                b = __pytra_int(255.0 * (1.0 - t))
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

fun run_mandelbrot() {
    var width: Long = 1600L
    var height: Long = 1200L
    var max_iter: Long = 1000L
    var out_path: String = "sample/out/01_mandelbrot.png"
    var start: Double = __pytra_perf_counter()
    var pixels: MutableList<Any?> = __pytra_as_list(render_mandelbrot(width, height, max_iter, (-2.2), 1.0, (-1.2), 1.2))
    __pytra_write_rgb_png(out_path, width, height, pixels)
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_mandelbrot()
}
