import kotlin.math.*


// 12: Sample that outputs intermediate states of bubble sort as a GIF.

fun render(values: MutableList<Any?>, w: Long, h: Long): MutableList<Any?> {
    var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
    var n: Long = __pytra_int(__pytra_len(values))
    var bar_w: Double = __pytra_float((__pytra_float(w) / __pytra_float(n)))
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float(n))
    var __hoisted_cast_2: Double = __pytra_float(__pytra_float(h))
    val __step_0 = __pytra_int(1L)
    var i = __pytra_int(0L)
    while ((__step_0 >= 0L && i < __pytra_int(n)) || (__step_0 < 0L && i > __pytra_int(n))) {
        var x0: Long = __pytra_int(__pytra_int((__pytra_float(i) * __pytra_float(bar_w))))
        var x1: Long = __pytra_int(__pytra_int((__pytra_float((__pytra_int(i) + __pytra_int(1L))) * __pytra_float(bar_w))))
        if ((__pytra_int(x1) <= __pytra_int(x0))) {
            x1 = __pytra_int((__pytra_int(x0) + __pytra_int(1L)))
        }
        var bh: Long = __pytra_int(__pytra_int((__pytra_float((__pytra_float(__pytra_int(__pytra_get_index(values, i))) / __pytra_float(__hoisted_cast_1))) * __pytra_float(__hoisted_cast_2))))
        var y: Long = __pytra_int((__pytra_int(h) - __pytra_int(bh)))
        val __step_1 = __pytra_int(1L)
        y = __pytra_int(y)
        while ((__step_1 >= 0L && y < __pytra_int(h)) || (__step_1 < 0L && y > __pytra_int(h))) {
            val __step_2 = __pytra_int(1L)
            var x = __pytra_int(x0)
            while ((__step_2 >= 0L && x < __pytra_int(x1)) || (__step_2 < 0L && x > __pytra_int(x1))) {
                __pytra_set_index(frame, (__pytra_int((__pytra_int(y) * __pytra_int(w))) + __pytra_int(x)), 255L)
                x += __step_2
            }
            y += __step_1
        }
        i += __step_0
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

fun run_12_sort_visualizer() {
    var w: Long = __pytra_int(320L)
    var h: Long = __pytra_int(180L)
    var n: Long = __pytra_int(124L)
    var out_path: String = __pytra_str("sample/out/12_sort_visualizer.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var values: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __step_0 = __pytra_int(1L)
    var i = __pytra_int(0L)
    while ((__step_0 >= 0L && i < __pytra_int(n)) || (__step_0 < 0L && i > __pytra_int(n))) {
        values = __pytra_as_list(values); values.add((__pytra_int((__pytra_int((__pytra_int(i) * __pytra_int(37L))) + __pytra_int(19L))) % __pytra_int(n)))
        i += __step_0
    }
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf(render(values, w, h)))
    var frame_stride: Long = __pytra_int(16L)
    var op: Long = __pytra_int(0L)
    val __step_1 = __pytra_int(1L)
    i = __pytra_int(0L)
    while ((__step_1 >= 0L && i < __pytra_int(n)) || (__step_1 < 0L && i > __pytra_int(n))) {
        var swapped: Boolean = __pytra_truthy(false)
        val __step_2 = __pytra_int(1L)
        var j = __pytra_int(0L)
        while ((__step_2 >= 0L && j < __pytra_int((__pytra_int((__pytra_int(n) - __pytra_int(i))) - __pytra_int(1L)))) || (__step_2 < 0L && j > __pytra_int((__pytra_int((__pytra_int(n) - __pytra_int(i))) - __pytra_int(1L))))) {
            if ((__pytra_int(__pytra_int(__pytra_get_index(values, j))) > __pytra_int(__pytra_int(__pytra_get_index(values, (__pytra_int(j) + __pytra_int(1L))))))) {
                val __tuple_3 = __pytra_as_list(mutableListOf(__pytra_int(__pytra_get_index(values, (__pytra_int(j) + __pytra_int(1L)))), __pytra_int(__pytra_get_index(values, j))))
                __pytra_set_index(values, j, __pytra_int(__tuple_3[0]))
                __pytra_set_index(values, (__pytra_int(j) + __pytra_int(1L)), __pytra_int(__tuple_3[1]))
                swapped = __pytra_truthy(true)
            }
            if ((__pytra_int((__pytra_int(op) % __pytra_int(frame_stride))) == __pytra_int(0L))) {
                frames = __pytra_as_list(frames); frames.add(render(values, w, h))
            }
            op += 1L
            j += __step_2
        }
        if ((!swapped)) {
            break
        }
        i += __step_1
    }
    __pytra_noop(out_path, w, h, frames, mutableListOf<Any?>())
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_12_sort_visualizer()
}
