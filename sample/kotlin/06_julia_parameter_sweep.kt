import kotlin.math.*


// 06: Sample that sweeps Julia-set parameters and outputs a GIF.

fun julia_palette(): MutableList<Any?> {
    var palette: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((__pytra_int(256L) * __pytra_int(3L))))
    __pytra_set_index(palette, 0L, 0L)
    __pytra_set_index(palette, 1L, 0L)
    __pytra_set_index(palette, 2L, 0L)
    val __step_0 = __pytra_int(1L)
    var i = __pytra_int(1L)
    while ((__step_0 >= 0L && i < __pytra_int(256L)) || (__step_0 < 0L && i > __pytra_int(256L))) {
        var t: Double = __pytra_float((__pytra_float((__pytra_int(i) - __pytra_int(1L))) / __pytra_float(254.0)))
        var r: Long = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(9.0) * __pytra_float((__pytra_float(1.0) - __pytra_float(t))))) * __pytra_float(t))) * __pytra_float(t))) * __pytra_float(t))))))
        var g: Long = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(15.0) * __pytra_float((__pytra_float(1.0) - __pytra_float(t))))) * __pytra_float((__pytra_float(1.0) - __pytra_float(t))))) * __pytra_float(t))) * __pytra_float(t))))))
        var b: Long = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(8.5) * __pytra_float((__pytra_float(1.0) - __pytra_float(t))))) * __pytra_float((__pytra_float(1.0) - __pytra_float(t))))) * __pytra_float((__pytra_float(1.0) - __pytra_float(t))))) * __pytra_float(t))))))
        __pytra_set_index(palette, (__pytra_int((__pytra_int(i) * __pytra_int(3L))) + __pytra_int(0L)), r)
        __pytra_set_index(palette, (__pytra_int((__pytra_int(i) * __pytra_int(3L))) + __pytra_int(1L)), g)
        __pytra_set_index(palette, (__pytra_int((__pytra_int(i) * __pytra_int(3L))) + __pytra_int(2L)), b)
        i += __step_0
    }
    return __pytra_as_list(__pytra_bytes(palette))
}

fun render_frame(width: Long, height: Long, cr: Double, ci: Double, max_iter: Long, phase: Long): MutableList<Any?> {
    var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((__pytra_int(width) * __pytra_int(height))))
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float((__pytra_int(height) - __pytra_int(1L))))
    var __hoisted_cast_2: Double = __pytra_float(__pytra_float((__pytra_int(width) - __pytra_int(1L))))
    val __step_0 = __pytra_int(1L)
    var y = __pytra_int(0L)
    while ((__step_0 >= 0L && y < __pytra_int(height)) || (__step_0 < 0L && y > __pytra_int(height))) {
        var row_base: Long = __pytra_int((__pytra_int(y) * __pytra_int(width)))
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
                zy = __pytra_float((__pytra_float((__pytra_float((__pytra_float(2.0) * __pytra_float(zx))) * __pytra_float(zy))) + __pytra_float(ci)))
                zx = __pytra_float((__pytra_float((__pytra_float(zx2) - __pytra_float(zy2))) + __pytra_float(cr)))
                i += 1L
            }
            if ((__pytra_int(i) >= __pytra_int(max_iter))) {
                __pytra_set_index(frame, (__pytra_int(row_base) + __pytra_int(x)), 0L)
            } else {
                var color_index: Long = __pytra_int((__pytra_int(1L) + __pytra_int((__pytra_int((__pytra_int((__pytra_int(__pytra_int((__pytra_int(i) * __pytra_int(224L))) / __pytra_int(max_iter)))) + __pytra_int(phase))) % __pytra_int(255L)))))
                __pytra_set_index(frame, (__pytra_int(row_base) + __pytra_int(x)), color_index)
            }
            x += __step_1
        }
        y += __step_0
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

fun run_06_julia_parameter_sweep() {
    var width: Long = __pytra_int(320L)
    var height: Long = __pytra_int(240L)
    var frames_n: Long = __pytra_int(72L)
    var max_iter: Long = __pytra_int(180L)
    var out_path: String = __pytra_str("sample/out/06_julia_parameter_sweep.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var center_cr: Double = __pytra_float((-0.745))
    var center_ci: Double = __pytra_float(0.186)
    var radius_cr: Double = __pytra_float(0.12)
    var radius_ci: Double = __pytra_float(0.1)
    var start_offset: Long = __pytra_int(20L)
    var phase_offset: Long = __pytra_int(180L)
    var __hoisted_cast_3: Double = __pytra_float(__pytra_float(frames_n))
    val __step_0 = __pytra_int(1L)
    var i = __pytra_int(0L)
    while ((__step_0 >= 0L && i < __pytra_int(frames_n)) || (__step_0 < 0L && i > __pytra_int(frames_n))) {
        var t: Double = __pytra_float((__pytra_float((__pytra_int((__pytra_int(i) + __pytra_int(start_offset))) % __pytra_int(frames_n))) / __pytra_float(__hoisted_cast_3)))
        var angle: Double = __pytra_float(((2.0 * Math.PI) * t))
        var cr: Double = __pytra_float((center_cr + (radius_cr * kotlin.math.cos(__pytra_float(angle)))))
        var ci: Double = __pytra_float((center_ci + (radius_ci * kotlin.math.sin(__pytra_float(angle)))))
        var phase: Long = __pytra_int((__pytra_int((__pytra_int(phase_offset) + __pytra_int((__pytra_int(i) * __pytra_int(5L))))) % __pytra_int(255L)))
        frames = __pytra_as_list(frames); frames.add(render_frame(width, height, cr, ci, max_iter, phase))
        i += __step_0
    }
    __pytra_noop(out_path, width, height, frames, julia_palette())
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_06_julia_parameter_sweep()
}
