import kotlin.math.*


// 05: Sample that outputs a Mandelbrot zoom as an animated GIF.

fun render_frame(width: Long, height: Long, center_x: Double, center_y: Double, scale: Double, max_iter: Long): MutableList<Any?> {
    var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((width * height)))
    var __hoisted_cast_1: Double = __pytra_float(max_iter)
    var y = __pytra_int(0L)
    while (y < __pytra_int(height)) {
        var row_base: Long = (y * width)
        var cy: Double = (center_y + ((__pytra_float(y) - (__pytra_float(height) * 0.5)) * scale))
        var x = __pytra_int(0L)
        while (x < __pytra_int(width)) {
            var cx: Double = (center_x + ((__pytra_float(x) - (__pytra_float(width) * 0.5)) * scale))
            var zx: Double = 0.0
            var zy: Double = 0.0
            var i: Long = 0L
            while ((__pytra_int(i) < __pytra_int(max_iter))) {
                var zx2: Double = (zx * zx)
                var zy2: Double = (zy * zy)
                if ((__pytra_float(zx2 + zy2) > __pytra_float(4.0))) {
                    break
                }
                zy = (((2.0 * zx) * zy) + cy)
                zx = ((zx2 - zy2) + cx)
                i += 1L
            }
            __pytra_set_index(frame, (row_base + x), __pytra_int((255.0 * __pytra_float(i)) / __hoisted_cast_1))
            x += 1L
        }
        y += 1L
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

fun run_05_mandelbrot_zoom() {
    var width: Long = 320L
    var height: Long = 240L
    var frame_count: Long = 48L
    var max_iter: Long = 110L
    var center_x: Double = __pytra_float(-0.743643887037151)
    var center_y: Double = 0.13182590420533
    var base_scale: Double = (3.2 / __pytra_float(width))
    var zoom_per_frame: Double = 0.93
    var out_path: String = "sample/out/05_mandelbrot_zoom.gif"
    var start: Double = __pytra_perf_counter()
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var scale: Double = base_scale
    var __loop_0 = __pytra_int(0L)
    while (__loop_0 < __pytra_int(frame_count)) {
        frames.add(render_frame(width, height, center_x, center_y, scale, max_iter))
        scale *= zoom_per_frame
        __loop_0 += 1L
    }
    __pytra_noop(out_path, width, height, frames, mutableListOf<Any?>())
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frame_count)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_05_mandelbrot_zoom()
}
