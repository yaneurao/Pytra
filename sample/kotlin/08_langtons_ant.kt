import kotlin.math.*


// 08: Sample that outputs Langton's Ant trajectories as a GIF.

fun capture(grid: MutableList<Any?>, w: Long, h: Long): MutableList<Any?> {
    var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
    val __step_0 = __pytra_int(1L)
    var y = __pytra_int(0L)
    while ((__step_0 >= 0L && y < __pytra_int(h)) || (__step_0 < 0L && y > __pytra_int(h))) {
        var row_base: Long = __pytra_int((__pytra_int(y) * __pytra_int(w)))
        val __step_1 = __pytra_int(1L)
        var x = __pytra_int(0L)
        while ((__step_1 >= 0L && x < __pytra_int(w)) || (__step_1 < 0L && x > __pytra_int(w))) {
            __pytra_set_index(frame, (__pytra_int(row_base) + __pytra_int(x)), __pytra_ifexp((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)) != 0L), 255L, 0L))
            x += __step_1
        }
        y += __step_0
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

fun run_08_langtons_ant() {
    var w: Long = __pytra_int(420L)
    var h: Long = __pytra_int(420L)
    var out_path: String = __pytra_str("sample/out/08_langtons_ant.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var grid: MutableList<Any?> = __pytra_as_list(run { val __out = mutableListOf<Any?>(); val __step = __pytra_int(1L); var __lc_i = __pytra_int(0L); while ((__step >= 0L && __lc_i < __pytra_int(h)) || (__step < 0L && __lc_i > __pytra_int(h))) { __out.add(__pytra_list_repeat(0L, w)); __lc_i += __step }; __out })
    var x: Long = __pytra_int((__pytra_int(__pytra_int(w) / __pytra_int(2L))))
    var y: Long = __pytra_int((__pytra_int(__pytra_int(h) / __pytra_int(2L))))
    var d: Long = __pytra_int(0L)
    var steps_total: Long = __pytra_int(600000L)
    var capture_every: Long = __pytra_int(3000L)
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __step_0 = __pytra_int(1L)
    var i = __pytra_int(0L)
    while ((__step_0 >= 0L && i < __pytra_int(steps_total)) || (__step_0 < 0L && i > __pytra_int(steps_total))) {
        if ((__pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x))) == __pytra_int(0L))) {
            d = __pytra_int((__pytra_int((__pytra_int(d) + __pytra_int(1L))) % __pytra_int(4L)))
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, y)), x, 1L)
        } else {
            d = __pytra_int((__pytra_int((__pytra_int(d) + __pytra_int(3L))) % __pytra_int(4L)))
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, y)), x, 0L)
        }
        if ((__pytra_int(d) == __pytra_int(0L))) {
            y = __pytra_int((__pytra_int((__pytra_int((__pytra_int(y) - __pytra_int(1L))) + __pytra_int(h))) % __pytra_int(h)))
        } else {
            if ((__pytra_int(d) == __pytra_int(1L))) {
                x = __pytra_int((__pytra_int((__pytra_int(x) + __pytra_int(1L))) % __pytra_int(w)))
            } else {
                if ((__pytra_int(d) == __pytra_int(2L))) {
                    y = __pytra_int((__pytra_int((__pytra_int(y) + __pytra_int(1L))) % __pytra_int(h)))
                } else {
                    x = __pytra_int((__pytra_int((__pytra_int((__pytra_int(x) - __pytra_int(1L))) + __pytra_int(w))) % __pytra_int(w)))
                }
            }
        }
        if ((__pytra_int((__pytra_int(i) % __pytra_int(capture_every))) == __pytra_int(0L))) {
            frames = __pytra_as_list(frames); frames.add(capture(grid, w, h))
        }
        i += __step_0
    }
    __pytra_noop(out_path, w, h, frames, mutableListOf<Any?>())
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_08_langtons_ant()
}
