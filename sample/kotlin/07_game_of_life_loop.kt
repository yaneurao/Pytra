import kotlin.math.*


// 07: Sample that outputs Game of Life evolution as a GIF.

fun next_state(grid: MutableList<Any?>, w: Long, h: Long): MutableList<Any?> {
    var nxt: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var y = __pytra_int(0L)
    while (y < __pytra_int(h)) {
        var row: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
        var x = __pytra_int(0L)
        while (x < __pytra_int(w)) {
            var cnt: Long = 0L
            var dy = __pytra_int(-1L)
            while (dy < __pytra_int(2L)) {
                var dx = __pytra_int(-1L)
                while (dx < __pytra_int(2L)) {
                    if (((__pytra_int(dx) != __pytra_int(0L)) || (__pytra_int(dy) != __pytra_int(0L)))) {
                        var nx: Long = (((x + dx) + w) % w)
                        var ny: Long = (((y + dy) + h) % h)
                        cnt += __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, ny)), nx))
                    }
                    dx += 1L
                }
                dy += 1L
            }
            var alive: Long = __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x))
            if (((__pytra_int(alive) == __pytra_int(1L)) && ((__pytra_int(cnt) == __pytra_int(2L)) || (__pytra_int(cnt) == __pytra_int(3L))))) {
                row.add(1L)
            } else {
                if (((__pytra_int(alive) == __pytra_int(0L)) && (__pytra_int(cnt) == __pytra_int(3L)))) {
                    row.add(1L)
                } else {
                    row.add(0L)
                }
            }
            x += 1L
        }
        nxt.add(row)
        y += 1L
    }
    return nxt
}

fun render(grid: MutableList<Any?>, w: Long, h: Long, cell: Long): MutableList<Any?> {
    var width: Long = (w * cell)
    var height: Long = (h * cell)
    var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((width * height)))
    var y = __pytra_int(0L)
    while (y < __pytra_int(h)) {
        var x = __pytra_int(0L)
        while (x < __pytra_int(w)) {
            var v: Long = __pytra_int(__pytra_ifexp((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)) != 0L), 255L, 0L))
            var yy = __pytra_int(0L)
            while (yy < __pytra_int(cell)) {
                var base: Long = ((((y * cell) + yy) * width) + (x * cell))
                var xx = __pytra_int(0L)
                while (xx < __pytra_int(cell)) {
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

fun run_07_game_of_life_loop() {
    var w: Long = 144L
    var h: Long = 108L
    var cell: Long = 4L
    var steps: Long = 105L
    var out_path: String = "sample/out/07_game_of_life_loop.gif"
    var start: Double = __pytra_perf_counter()
    var grid: MutableList<Any?> = __pytra_as_list(run { val __out = mutableListOf<Any?>(); val __step = __pytra_int(1L); var __lc_i = __pytra_int(0L); while ((__step >= 0L && __lc_i < __pytra_int(h)) || (__step < 0L && __lc_i > __pytra_int(h))) { __out.add(__pytra_list_repeat(0L, w)); __lc_i += __step }; __out })
    var y = __pytra_int(0L)
    while (y < __pytra_int(h)) {
        var x = __pytra_int(0L)
        while (x < __pytra_int(w)) {
            var noise: Long = (((((x * 37L) + (y * 73L)) + ((x * y) % 19L)) + ((x + y) % 11L)) % 97L)
            if ((__pytra_int(noise) < __pytra_int(3L))) {
                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, y)), x, 1L)
            }
            x += 1L
        }
        y += 1L
    }
    var glider: MutableList<Any?> = __pytra_as_list(mutableListOf(mutableListOf(0L, 1L, 0L), mutableListOf(0L, 0L, 1L), mutableListOf(1L, 1L, 1L)))
    var r_pentomino: MutableList<Any?> = __pytra_as_list(mutableListOf(mutableListOf(0L, 1L, 1L), mutableListOf(1L, 1L, 0L), mutableListOf(0L, 1L, 0L)))
    var lwss: MutableList<Any?> = __pytra_as_list(mutableListOf(mutableListOf(0L, 1L, 1L, 1L, 1L), mutableListOf(1L, 0L, 0L, 0L, 1L), mutableListOf(0L, 0L, 0L, 0L, 1L), mutableListOf(1L, 0L, 0L, 1L, 0L)))
    var gy = __pytra_int(8L)
    val __step_2 = __pytra_int(18L)
    while ((__step_2 >= 0L && gy < __pytra_int(h - 8L)) || (__step_2 < 0L && gy > __pytra_int(h - 8L))) {
        var gx = __pytra_int(8L)
        val __step_3 = __pytra_int(22L)
        while ((__step_3 >= 0L && gx < __pytra_int(w - 8L)) || (__step_3 < 0L && gx > __pytra_int(w - 8L))) {
            var kind: Long = (((gx * 7L) + (gy * 11L)) % 3L)
            if ((__pytra_int(kind) == __pytra_int(0L))) {
                var ph: Long = __pytra_len(glider)
                var py = __pytra_int(0L)
                while (py < __pytra_int(ph)) {
                    var pw: Long = __pytra_len(__pytra_as_list(__pytra_get_index(glider, py)))
                    var px = __pytra_int(0L)
                    while (px < __pytra_int(pw)) {
                        if ((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(glider, py)), px)) == __pytra_int(1L))) {
                            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ((gy + py) % h))), ((gx + px) % w), 1L)
                        }
                        px += 1L
                    }
                    py += 1L
                }
            } else {
                if ((__pytra_int(kind) == __pytra_int(1L))) {
                    var ph: Long = __pytra_len(r_pentomino)
                    var py = __pytra_int(0L)
                    while (py < __pytra_int(ph)) {
                        var pw: Long = __pytra_len(__pytra_as_list(__pytra_get_index(r_pentomino, py)))
                        var px = __pytra_int(0L)
                        while (px < __pytra_int(pw)) {
                            if ((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(r_pentomino, py)), px)) == __pytra_int(1L))) {
                                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ((gy + py) % h))), ((gx + px) % w), 1L)
                            }
                            px += 1L
                        }
                        py += 1L
                    }
                } else {
                    var ph: Long = __pytra_len(lwss)
                    var py = __pytra_int(0L)
                    while (py < __pytra_int(ph)) {
                        var pw: Long = __pytra_len(__pytra_as_list(__pytra_get_index(lwss, py)))
                        var px = __pytra_int(0L)
                        while (px < __pytra_int(pw)) {
                            if ((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(lwss, py)), px)) == __pytra_int(1L))) {
                                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ((gy + py) % h))), ((gx + px) % w), 1L)
                            }
                            px += 1L
                        }
                        py += 1L
                    }
                }
            }
            gx += __step_3
        }
        gy += __step_2
    }
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var __loop_10 = __pytra_int(0L)
    while (__loop_10 < __pytra_int(steps)) {
        frames.add(render(grid, w, h, cell))
        grid = __pytra_as_list(next_state(grid, w, h))
        __loop_10 += 1L
    }
    __pytra_noop(out_path, (w * cell), (h * cell), frames, mutableListOf<Any?>())
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_07_game_of_life_loop()
}
