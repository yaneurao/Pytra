import kotlin.math.*


// 13: Sample that outputs DFS maze-generation progress as a GIF.

fun capture(grid: MutableList<Any?>, w: Long, h: Long, scale: Long): MutableList<Any?> {
    var width: Long = __pytra_int((__pytra_int(w) * __pytra_int(scale)))
    var height: Long = __pytra_int((__pytra_int(h) * __pytra_int(scale)))
    var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((__pytra_int(width) * __pytra_int(height))))
    val __step_0 = __pytra_int(1L)
    var y = __pytra_int(0L)
    while ((__step_0 >= 0L && y < __pytra_int(h)) || (__step_0 < 0L && y > __pytra_int(h))) {
        val __step_1 = __pytra_int(1L)
        var x = __pytra_int(0L)
        while ((__step_1 >= 0L && x < __pytra_int(w)) || (__step_1 < 0L && x > __pytra_int(w))) {
            var v: Long = __pytra_int(__pytra_ifexp((__pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x))) == __pytra_int(0L)), 255L, 40L))
            val __step_2 = __pytra_int(1L)
            var yy = __pytra_int(0L)
            while ((__step_2 >= 0L && yy < __pytra_int(scale)) || (__step_2 < 0L && yy > __pytra_int(scale))) {
                var base: Long = __pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int(y) * __pytra_int(scale))) + __pytra_int(yy))) * __pytra_int(width))) + __pytra_int((__pytra_int(x) * __pytra_int(scale)))))
                val __step_3 = __pytra_int(1L)
                var xx = __pytra_int(0L)
                while ((__step_3 >= 0L && xx < __pytra_int(scale)) || (__step_3 < 0L && xx > __pytra_int(scale))) {
                    __pytra_set_index(frame, (__pytra_int(base) + __pytra_int(xx)), v)
                    xx += __step_3
                }
                yy += __step_2
            }
            x += __step_1
        }
        y += __step_0
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

fun run_13_maze_generation_steps() {
    var cell_w: Long = __pytra_int(89L)
    var cell_h: Long = __pytra_int(67L)
    var scale: Long = __pytra_int(5L)
    var capture_every: Long = __pytra_int(20L)
    var out_path: String = __pytra_str("sample/out/13_maze_generation_steps.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var grid: MutableList<Any?> = __pytra_as_list(run { val __out = mutableListOf<Any?>(); val __step = __pytra_int(1L); var __lc_i = __pytra_int(0L); while ((__step >= 0L && __lc_i < __pytra_int(cell_h)) || (__step < 0L && __lc_i > __pytra_int(cell_h))) { __out.add(__pytra_list_repeat(1L, cell_w)); __lc_i += __step }; __out })
    var stack: MutableList<Any?> = __pytra_as_list(mutableListOf(mutableListOf(1L, 1L)))
    __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, 1L)), 1L, 0L)
    var dirs: MutableList<Any?> = __pytra_as_list(mutableListOf(mutableListOf(2L, 0L), mutableListOf((-2L), 0L), mutableListOf(0L, 2L), mutableListOf(0L, (-2L))))
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var step: Long = __pytra_int(0L)
    while ((__pytra_len(stack) != 0L)) {
        val __tuple_0 = __pytra_as_list(__pytra_as_list(__pytra_get_index(stack, (-1L))))
        var x: Long = __pytra_int(__tuple_0[0])
        var y: Long = __pytra_int(__tuple_0[1])
        var candidates: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
        val __step_1 = __pytra_int(1L)
        var k = __pytra_int(0L)
        while ((__step_1 >= 0L && k < __pytra_int(4L)) || (__step_1 < 0L && k > __pytra_int(4L))) {
            val __tuple_2 = __pytra_as_list(__pytra_as_list(__pytra_get_index(dirs, k)))
            var dx: Long = __pytra_int(__tuple_2[0])
            var dy: Long = __pytra_int(__tuple_2[1])
            var nx: Long = __pytra_int((x + dx))
            var ny: Long = __pytra_int((y + dy))
            if (((__pytra_int(nx) >= __pytra_int(1L)) && (__pytra_int(nx) < __pytra_int((__pytra_int(cell_w) - __pytra_int(1L)))) && (__pytra_int(ny) >= __pytra_int(1L)) && (__pytra_int(ny) < __pytra_int((__pytra_int(cell_h) - __pytra_int(1L)))) && (__pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, ny)), nx))) == __pytra_int(1L)))) {
                if ((__pytra_int(dx) == __pytra_int(2L))) {
                    candidates = __pytra_as_list(candidates); candidates.add(mutableListOf(nx, ny, (x + 1L), y))
                } else {
                    if ((__pytra_int(dx) == __pytra_int((-2L)))) {
                        candidates = __pytra_as_list(candidates); candidates.add(mutableListOf(nx, ny, (x - 1L), y))
                    } else {
                        if ((__pytra_int(dy) == __pytra_int(2L))) {
                            candidates = __pytra_as_list(candidates); candidates.add(mutableListOf(nx, ny, x, (y + 1L)))
                        } else {
                            candidates = __pytra_as_list(candidates); candidates.add(mutableListOf(nx, ny, x, (y - 1L)))
                        }
                    }
                }
            }
            k += __step_1
        }
        if ((__pytra_int(__pytra_len(candidates)) == __pytra_int(0L))) {
            stack = __pytra_pop_last(__pytra_as_list(stack))
        } else {
            var sel: MutableList<Any?> = __pytra_as_list(__pytra_as_list(__pytra_get_index(candidates, (__pytra_int((((x * 17L) + (y * 29L)) + (__pytra_int(__pytra_len(stack)) * __pytra_int(13L)))) % __pytra_int(__pytra_len(candidates))))))
            val __tuple_3 = __pytra_as_list(sel)
            var nx: Long = __pytra_int(__tuple_3[0])
            var ny: Long = __pytra_int(__tuple_3[1])
            var wx: Long = __pytra_int(__tuple_3[2])
            var wy: Long = __pytra_int(__tuple_3[3])
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, wy)), wx, 0L)
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ny)), nx, 0L)
            stack = __pytra_as_list(stack); stack.add(mutableListOf(nx, ny))
        }
        if ((__pytra_int((__pytra_int(step) % __pytra_int(capture_every))) == __pytra_int(0L))) {
            frames = __pytra_as_list(frames); frames.add(capture(grid, cell_w, cell_h, scale))
        }
        step += 1L
    }
    frames = __pytra_as_list(frames); frames.add(capture(grid, cell_w, cell_h, scale))
    __pytra_noop(out_path, (__pytra_int(cell_w) * __pytra_int(scale)), (__pytra_int(cell_h) * __pytra_int(scale)), frames, mutableListOf<Any?>())
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_13_maze_generation_steps()
}
