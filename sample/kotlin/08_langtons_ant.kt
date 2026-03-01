import kotlin.math.*


// 08: Sample that outputs Langton's Ant trajectories as a GIF.

fun capture(grid: MutableList<Any?>, w: Long, h: Long): MutableList<Any?> {
    var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((w * h)))
    var y = __pytra_int(0L)
    while (y < __pytra_int(h)) {
        var row_base: Long = (y * w)
        var x = __pytra_int(0L)
        while (x < __pytra_int(w)) {
            __pytra_set_index(frame, (row_base + x), __pytra_ifexp((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)) != 0L), 255L, 0L))
            x += 1L
        }
        y += 1L
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

fun run_08_langtons_ant() {
    var w: Long = 420L
    var h: Long = 420L
    var out_path: String = "sample/out/08_langtons_ant.gif"
    var start: Double = __pytra_perf_counter()
    var grid: MutableList<Any?> = __pytra_as_list(run { val __out = mutableListOf<Any?>(); val __step = __pytra_int(1L); var __lc_i = __pytra_int(0L); while ((__step >= 0L && __lc_i < __pytra_int(h)) || (__step < 0L && __lc_i > __pytra_int(h))) { __out.add(__pytra_list_repeat(0L, w)); __lc_i += __step }; __out })
    var x: Long = (w / 2L)
    var y: Long = (h / 2L)
    var d: Long = 0L
    var steps_total: Long = 600000L
    var capture_every: Long = 3000L
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var i = __pytra_int(0L)
    while (i < __pytra_int(steps_total)) {
        if ((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)) == __pytra_int(0L))) {
            d = ((d + 1L) % 4L)
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, y)), x, 1L)
        } else {
            d = ((d + 3L) % 4L)
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, y)), x, 0L)
        }
        if ((__pytra_int(d) == __pytra_int(0L))) {
            y = (((y - 1L) + h) % h)
        } else {
            if ((__pytra_int(d) == __pytra_int(1L))) {
                x = ((x + 1L) % w)
            } else {
                if ((__pytra_int(d) == __pytra_int(2L))) {
                    y = ((y + 1L) % h)
                } else {
                    x = (((x - 1L) + w) % w)
                }
            }
        }
        if ((__pytra_int(i % capture_every) == __pytra_int(0L))) {
            frames.add(capture(grid, w, h))
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
    run_08_langtons_ant()
}
