import kotlin.math.*


// 13: Sample that outputs DFS maze-generation progress as a GIF.

fun capture(grid: MutableList<Any?>, w: Long, h: Long, scale: Long): MutableList<Any?> {
    var width: Long = (w * scale)
    var height: Long = (h * scale)
    var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((width * height)))
    var y = __pytra_int(0L)
    while (y < __pytra_int(h)) {
        var x = __pytra_int(0L)
        while (x < __pytra_int(w)) {
            var v: Long = __pytra_int(__pytra_ifexp((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)) == __pytra_int(0L)), 255L, 40L))
            var yy = __pytra_int(0L)
            while (yy < __pytra_int(scale)) {
                var base: Long = ((((y * scale) + yy) * width) + (x * scale))
                var xx = __pytra_int(0L)
                while (xx < __pytra_int(scale)) {
                    __pytra_set_index(frame, (base + xx), v)
                    xx += 1L
                }
                yy += 1L
            }
            x += 1L
        }
        y += 1L
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

fun run_13_maze_generation_steps() {
    var cell_w: Long = 89L
    var cell_h: Long = 67L
    var scale: Long = 5L
    var capture_every: Long = 20L
    var out_path: String = "sample/out/13_maze_generation_steps.gif"
    var start: Double = __pytra_perf_counter()
    var grid: MutableList<Any?> = __pytra_as_list(run { val __out = mutableListOf<Any?>(); val __step = __pytra_int(1L); var __lc_i = __pytra_int(0L); while ((__step >= 0L && __lc_i < __pytra_int(cell_h)) || (__step < 0L && __lc_i > __pytra_int(cell_h))) { __out.add(__pytra_list_repeat(1L, cell_w)); __lc_i += __step }; __out })
    var stack: MutableList<Any?> = __pytra_as_list(mutableListOf(mutableListOf(1L, 1L)))
    __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, 1L)), 1L, 0L)
    var dirs: MutableList<Any?> = __pytra_as_list(mutableListOf(mutableListOf(2L, 0L), mutableListOf((-2L), 0L), mutableListOf(0L, 2L), mutableListOf(0L, (-2L))))
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var step: Long = 0L
    while ((__pytra_len(stack) != 0L)) {
        val __tuple_0 = __pytra_as_list(__pytra_as_list(__pytra_get_index(stack, (-1L))))
        var x: Long = __pytra_int(__tuple_0[0])
        var y: Long = __pytra_int(__tuple_0[1])
        var candidates: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
        var k = __pytra_int(0L)
        while (k < __pytra_int(4L)) {
            val __tuple_2 = __pytra_as_list(__pytra_as_list(__pytra_get_index(dirs, k)))
            var dx: Long = __pytra_int(__tuple_2[0])
            var dy: Long = __pytra_int(__tuple_2[1])
            var nx: Long = __pytra_int(x + dx)
            var ny: Long = __pytra_int(y + dy)
            if (((__pytra_int(nx) >= __pytra_int(1L)) && (__pytra_int(nx) < __pytra_int(cell_w - 1L)) && (__pytra_int(ny) >= __pytra_int(1L)) && (__pytra_int(ny) < __pytra_int(cell_h - 1L)) && (__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, ny)), nx)) == __pytra_int(1L)))) {
                if ((__pytra_int(dx) == __pytra_int(2L))) {
                    candidates.add(mutableListOf(nx, ny, (x + 1L), y))
                } else {
                    if ((__pytra_int(dx) == __pytra_int(-2L))) {
                        candidates.add(mutableListOf(nx, ny, (x - 1L), y))
                    } else {
                        if ((__pytra_int(dy) == __pytra_int(2L))) {
                            candidates.add(mutableListOf(nx, ny, x, (y + 1L)))
                        } else {
                            candidates.add(mutableListOf(nx, ny, x, (y - 1L)))
                        }
                    }
                }
            }
            k += 1L
        }
        if ((__pytra_int(__pytra_len(candidates)) == __pytra_int(0L))) {
            stack = __pytra_pop_last(__pytra_as_list(stack))
        } else {
            var sel: MutableList<Any?> = __pytra_as_list(__pytra_get_index(candidates, (__pytra_int(((x * 17L) + (y * 29L)) + (__pytra_len(stack) * 13L)) % __pytra_len(candidates))))
            val __tuple_3 = __pytra_as_list(sel)
            var nx: Long = __pytra_int(__tuple_3[0])
            var ny: Long = __pytra_int(__tuple_3[1])
            var wx: Long = __pytra_int(__tuple_3[2])
            var wy: Long = __pytra_int(__tuple_3[3])
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, wy)), wx, 0L)
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ny)), nx, 0L)
            stack.add(mutableListOf(nx, ny))
        }
        if ((__pytra_int(step % capture_every) == __pytra_int(0L))) {
            frames.add(capture(grid, cell_w, cell_h, scale))
        }
        step += 1L
    }
    frames.add(capture(grid, cell_w, cell_h, scale))
    __pytra_noop(out_path, (cell_w * scale), (cell_h * scale), frames, mutableListOf<Any?>())
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_13_maze_generation_steps()
}
