import kotlin.math.*


// 12: Sample that outputs intermediate states of bubble sort as a GIF.

fun render(values: MutableList<Any?>, w: Long, h: Long): MutableList<Any?> {
    var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((w * h)))
    var n: Long = __pytra_len(values)
    var bar_w: Double = (__pytra_float(w) / __pytra_float(n))
    var __hoisted_cast_1: Double = __pytra_float(n)
    var __hoisted_cast_2: Double = __pytra_float(h)
    var i = __pytra_int(0L)
    while (i < __pytra_int(n)) {
        var x0: Long = __pytra_int(__pytra_float(i) * bar_w)
        var x1: Long = __pytra_int(__pytra_float(i + 1L) * bar_w)
        if ((__pytra_int(x1) <= __pytra_int(x0))) {
            x1 = (x0 + 1L)
        }
        var bh: Long = __pytra_int((__pytra_float(__pytra_int(__pytra_get_index(values, i))) / __hoisted_cast_1) * __hoisted_cast_2)
        var y: Long = (h - bh)
        y = __pytra_int(y)
        while (y < __pytra_int(h)) {
            var x = __pytra_int(x0)
            while (x < __pytra_int(x1)) {
                __pytra_set_index(frame, ((y * w) + x), 255L)
                x += 1L
            }
            y += 1L
        }
        i += 1L
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

fun run_12_sort_visualizer() {
    var w: Long = 320L
    var h: Long = 180L
    var n: Long = 124L
    var out_path: String = "sample/out/12_sort_visualizer.gif"
    var start: Double = __pytra_perf_counter()
    var values: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var i = __pytra_int(0L)
    while (i < __pytra_int(n)) {
        values.add((((i * 37L) + 19L) % n))
        i += 1L
    }
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf(render(values, w, h)))
    var frame_stride: Long = 16L
    var op: Long = 0L
    i = __pytra_int(0L)
    while (i < __pytra_int(n)) {
        var swapped: Boolean = false
        var j = __pytra_int(0L)
        while (j < __pytra_int((n - i) - 1L)) {
            if ((__pytra_int(__pytra_get_index(values, j)) > __pytra_int(__pytra_get_index(values, (j + 1L))))) {
                val __tuple_3 = __pytra_as_list(mutableListOf(__pytra_int(__pytra_get_index(values, (j + 1L))), __pytra_int(__pytra_get_index(values, j))))
                __pytra_set_index(values, j, __pytra_int(__tuple_3[0]))
                __pytra_set_index(values, (j + 1L), __pytra_int(__tuple_3[1]))
                swapped = true
            }
            if ((__pytra_int(op % frame_stride) == __pytra_int(0L))) {
                frames.add(render(values, w, h))
            }
            op += 1L
            j += 1L
        }
        if ((!swapped)) {
            break
        }
        i += 1L
    }
    __pytra_noop(out_path, w, h, frames, mutableListOf<Any?>())
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_12_sort_visualizer()
}
