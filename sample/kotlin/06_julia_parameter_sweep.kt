import kotlin.math.*


// 06: Sample that sweeps Julia-set parameters and outputs a GIF.

fun julia_palette(): MutableList<Any?> {
    var palette: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((256L * 3L)))
    __pytra_set_index(palette, 0L, 0L)
    __pytra_set_index(palette, 1L, 0L)
    __pytra_set_index(palette, 2L, 0L)
    var i = __pytra_int(1L)
    while (i < __pytra_int(256L)) {
        var t: Double = (__pytra_float(i - 1L) / 254.0)
        var r: Long = __pytra_int(255.0 * ((((9.0 * (1.0 - t)) * t) * t) * t))
        var g: Long = __pytra_int(255.0 * ((((15.0 * (1.0 - t)) * (1.0 - t)) * t) * t))
        var b: Long = __pytra_int(255.0 * ((((8.5 * (1.0 - t)) * (1.0 - t)) * (1.0 - t)) * t))
        __pytra_set_index(palette, ((i * 3L) + 0L), r)
        __pytra_set_index(palette, ((i * 3L) + 1L), g)
        __pytra_set_index(palette, ((i * 3L) + 2L), b)
        i += 1L
    }
    return __pytra_as_list(__pytra_bytes(palette))
}

fun render_frame(width: Long, height: Long, cr: Double, ci: Double, max_iter: Long, phase: Long): MutableList<Any?> {
    var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((width * height)))
    var __hoisted_cast_1: Double = __pytra_float(height - 1L)
    var __hoisted_cast_2: Double = __pytra_float(width - 1L)
    var y = __pytra_int(0L)
    while (y < __pytra_int(height)) {
        var row_base: Long = (y * width)
        var zy0: Double = ((-1.2) + (2.4 * (__pytra_float(y) / __hoisted_cast_1)))
        var x = __pytra_int(0L)
        while (x < __pytra_int(width)) {
            var zx: Double = ((-1.8) + (3.6 * (__pytra_float(x) / __hoisted_cast_2)))
            var zy: Double = zy0
            var i: Long = 0L
            while ((__pytra_int(i) < __pytra_int(max_iter))) {
                var zx2: Double = (zx * zx)
                var zy2: Double = (zy * zy)
                if ((__pytra_float(zx2 + zy2) > __pytra_float(4.0))) {
                    break
                }
                zy = (((2.0 * zx) * zy) + ci)
                zx = ((zx2 - zy2) + cr)
                i += 1L
            }
            if ((__pytra_int(i) >= __pytra_int(max_iter))) {
                __pytra_set_index(frame, (row_base + x), 0L)
            } else {
                var color_index: Long = (1L + ((((i * 224L) / max_iter) + phase) % 255L))
                __pytra_set_index(frame, (row_base + x), color_index)
            }
            x += 1L
        }
        y += 1L
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

fun run_06_julia_parameter_sweep() {
    var width: Long = 320L
    var height: Long = 240L
    var frames_n: Long = 72L
    var max_iter: Long = 180L
    var out_path: String = "sample/out/06_julia_parameter_sweep.gif"
    var start: Double = __pytra_perf_counter()
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var center_cr: Double = __pytra_float(-0.745)
    var center_ci: Double = 0.186
    var radius_cr: Double = 0.12
    var radius_ci: Double = 0.1
    var start_offset: Long = 20L
    var phase_offset: Long = 180L
    var __hoisted_cast_3: Double = __pytra_float(frames_n)
    var i = __pytra_int(0L)
    while (i < __pytra_int(frames_n)) {
        var t: Double = (__pytra_float((i + start_offset) % frames_n) / __hoisted_cast_3)
        var angle: Double = __pytra_float((2.0 * Math.PI) * t)
        var cr: Double = __pytra_float(center_cr + (radius_cr * kotlin.math.cos(__pytra_float(angle))))
        var ci: Double = __pytra_float(center_ci + (radius_ci * kotlin.math.sin(__pytra_float(angle))))
        var phase: Long = ((phase_offset + (i * 5L)) % 255L)
        frames.add(render_frame(width, height, cr, ci, max_iter, phase))
        i += 1L
    }
    __pytra_noop(out_path, width, height, frames, julia_palette())
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_06_julia_parameter_sweep()
}
