import kotlin.math.*


// 07: Sample that outputs Game of Life evolution as a GIF.

fun next_state(grid: MutableList<Any?>, w: Long, h: Long): MutableList<Any?> {
    var nxt: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __step_0 = __pytra_int(1L)
    var y = __pytra_int(0L)
    while ((__step_0 >= 0L && y < __pytra_int(h)) || (__step_0 < 0L && y > __pytra_int(h))) {
        var row: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
        val __step_1 = __pytra_int(1L)
        var x = __pytra_int(0L)
        while ((__step_1 >= 0L && x < __pytra_int(w)) || (__step_1 < 0L && x > __pytra_int(w))) {
            var cnt: Long = __pytra_int(0L)
            val __step_2 = __pytra_int(1L)
            var dy = __pytra_int((-1L))
            while ((__step_2 >= 0L && dy < __pytra_int(2L)) || (__step_2 < 0L && dy > __pytra_int(2L))) {
                val __step_3 = __pytra_int(1L)
                var dx = __pytra_int((-1L))
                while ((__step_3 >= 0L && dx < __pytra_int(2L)) || (__step_3 < 0L && dx > __pytra_int(2L))) {
                    if (((__pytra_int(dx) != __pytra_int(0L)) || (__pytra_int(dy) != __pytra_int(0L)))) {
                        var nx: Long = __pytra_int((__pytra_int((__pytra_int((__pytra_int(x) + __pytra_int(dx))) + __pytra_int(w))) % __pytra_int(w)))
                        var ny: Long = __pytra_int((__pytra_int((__pytra_int((__pytra_int(y) + __pytra_int(dy))) + __pytra_int(h))) % __pytra_int(h)))
                        cnt += __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, ny)), nx))
                    }
                    dx += __step_3
                }
                dy += __step_2
            }
            var alive: Long = __pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)))
            if (((__pytra_int(alive) == __pytra_int(1L)) && ((__pytra_int(cnt) == __pytra_int(2L)) || (__pytra_int(cnt) == __pytra_int(3L))))) {
                row = __pytra_as_list(row); row.add(1L)
            } else {
                if (((__pytra_int(alive) == __pytra_int(0L)) && (__pytra_int(cnt) == __pytra_int(3L)))) {
                    row = __pytra_as_list(row); row.add(1L)
                } else {
                    row = __pytra_as_list(row); row.add(0L)
                }
            }
            x += __step_1
        }
        nxt = __pytra_as_list(nxt); nxt.add(row)
        y += __step_0
    }
    return __pytra_as_list(nxt)
}

fun render(grid: MutableList<Any?>, w: Long, h: Long, cell: Long): MutableList<Any?> {
    var width: Long = __pytra_int((__pytra_int(w) * __pytra_int(cell)))
    var height: Long = __pytra_int((__pytra_int(h) * __pytra_int(cell)))
    var frame: MutableList<Any?> = __pytra_as_list(__pytra_bytearray((__pytra_int(width) * __pytra_int(height))))
    val __step_0 = __pytra_int(1L)
    var y = __pytra_int(0L)
    while ((__step_0 >= 0L && y < __pytra_int(h)) || (__step_0 < 0L && y > __pytra_int(h))) {
        val __step_1 = __pytra_int(1L)
        var x = __pytra_int(0L)
        while ((__step_1 >= 0L && x < __pytra_int(w)) || (__step_1 < 0L && x > __pytra_int(w))) {
            var v: Long = __pytra_int(__pytra_ifexp((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)) != 0L), 255L, 0L))
            val __step_2 = __pytra_int(1L)
            var yy = __pytra_int(0L)
            while ((__step_2 >= 0L && yy < __pytra_int(cell)) || (__step_2 < 0L && yy > __pytra_int(cell))) {
                var base: Long = __pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int(y) * __pytra_int(cell))) + __pytra_int(yy))) * __pytra_int(width))) + __pytra_int((__pytra_int(x) * __pytra_int(cell)))))
                val __step_3 = __pytra_int(1L)
                var xx = __pytra_int(0L)
                while ((__step_3 >= 0L && xx < __pytra_int(cell)) || (__step_3 < 0L && xx > __pytra_int(cell))) {
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

fun run_07_game_of_life_loop() {
    var w: Long = __pytra_int(144L)
    var h: Long = __pytra_int(108L)
    var cell: Long = __pytra_int(4L)
    var steps: Long = __pytra_int(105L)
    var out_path: String = __pytra_str("sample/out/07_game_of_life_loop.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var grid: MutableList<Any?> = __pytra_as_list(run { val __out = mutableListOf<Any?>(); val __step = __pytra_int(1L); var __lc_i = __pytra_int(0L); while ((__step >= 0L && __lc_i < __pytra_int(h)) || (__step < 0L && __lc_i > __pytra_int(h))) { __out.add(__pytra_list_repeat(0L, w)); __lc_i += __step }; __out })
    val __step_0 = __pytra_int(1L)
    var y = __pytra_int(0L)
    while ((__step_0 >= 0L && y < __pytra_int(h)) || (__step_0 < 0L && y > __pytra_int(h))) {
        val __step_1 = __pytra_int(1L)
        var x = __pytra_int(0L)
        while ((__step_1 >= 0L && x < __pytra_int(w)) || (__step_1 < 0L && x > __pytra_int(w))) {
            var noise: Long = __pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int(x) * __pytra_int(37L))) + __pytra_int((__pytra_int(y) * __pytra_int(73L))))) + __pytra_int((__pytra_int((__pytra_int(x) * __pytra_int(y))) % __pytra_int(19L))))) + __pytra_int((__pytra_int((__pytra_int(x) + __pytra_int(y))) % __pytra_int(11L))))) % __pytra_int(97L)))
            if ((__pytra_int(noise) < __pytra_int(3L))) {
                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, y)), x, 1L)
            }
            x += __step_1
        }
        y += __step_0
    }
    var glider: MutableList<Any?> = __pytra_as_list(mutableListOf(mutableListOf(0L, 1L, 0L), mutableListOf(0L, 0L, 1L), mutableListOf(1L, 1L, 1L)))
    var r_pentomino: MutableList<Any?> = __pytra_as_list(mutableListOf(mutableListOf(0L, 1L, 1L), mutableListOf(1L, 1L, 0L), mutableListOf(0L, 1L, 0L)))
    var lwss: MutableList<Any?> = __pytra_as_list(mutableListOf(mutableListOf(0L, 1L, 1L, 1L, 1L), mutableListOf(1L, 0L, 0L, 0L, 1L), mutableListOf(0L, 0L, 0L, 0L, 1L), mutableListOf(1L, 0L, 0L, 1L, 0L)))
    val __step_2 = __pytra_int(18L)
    var gy = __pytra_int(8L)
    while ((__step_2 >= 0L && gy < __pytra_int((__pytra_int(h) - __pytra_int(8L)))) || (__step_2 < 0L && gy > __pytra_int((__pytra_int(h) - __pytra_int(8L))))) {
        val __step_3 = __pytra_int(22L)
        var gx = __pytra_int(8L)
        while ((__step_3 >= 0L && gx < __pytra_int((__pytra_int(w) - __pytra_int(8L)))) || (__step_3 < 0L && gx > __pytra_int((__pytra_int(w) - __pytra_int(8L))))) {
            var kind: Long = __pytra_int((__pytra_int((__pytra_int((__pytra_int(gx) * __pytra_int(7L))) + __pytra_int((__pytra_int(gy) * __pytra_int(11L))))) % __pytra_int(3L)))
            if ((__pytra_int(kind) == __pytra_int(0L))) {
                var ph: Long = __pytra_int(__pytra_len(glider))
                val __step_4 = __pytra_int(1L)
                var py = __pytra_int(0L)
                while ((__step_4 >= 0L && py < __pytra_int(ph)) || (__step_4 < 0L && py > __pytra_int(ph))) {
                    var pw: Long = __pytra_int(__pytra_len(__pytra_as_list(__pytra_get_index(glider, py))))
                    val __step_5 = __pytra_int(1L)
                    var px = __pytra_int(0L)
                    while ((__step_5 >= 0L && px < __pytra_int(pw)) || (__step_5 < 0L && px > __pytra_int(pw))) {
                        if ((__pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(glider, py)), px))) == __pytra_int(1L))) {
                            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, (__pytra_int((__pytra_int(gy) + __pytra_int(py))) % __pytra_int(h)))), (__pytra_int((__pytra_int(gx) + __pytra_int(px))) % __pytra_int(w)), 1L)
                        }
                        px += __step_5
                    }
                    py += __step_4
                }
            } else {
                if ((__pytra_int(kind) == __pytra_int(1L))) {
                    var ph: Long = __pytra_int(__pytra_len(r_pentomino))
                    val __step_6 = __pytra_int(1L)
                    var py = __pytra_int(0L)
                    while ((__step_6 >= 0L && py < __pytra_int(ph)) || (__step_6 < 0L && py > __pytra_int(ph))) {
                        var pw: Long = __pytra_int(__pytra_len(__pytra_as_list(__pytra_get_index(r_pentomino, py))))
                        val __step_7 = __pytra_int(1L)
                        var px = __pytra_int(0L)
                        while ((__step_7 >= 0L && px < __pytra_int(pw)) || (__step_7 < 0L && px > __pytra_int(pw))) {
                            if ((__pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(r_pentomino, py)), px))) == __pytra_int(1L))) {
                                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, (__pytra_int((__pytra_int(gy) + __pytra_int(py))) % __pytra_int(h)))), (__pytra_int((__pytra_int(gx) + __pytra_int(px))) % __pytra_int(w)), 1L)
                            }
                            px += __step_7
                        }
                        py += __step_6
                    }
                } else {
                    var ph: Long = __pytra_int(__pytra_len(lwss))
                    val __step_8 = __pytra_int(1L)
                    var py = __pytra_int(0L)
                    while ((__step_8 >= 0L && py < __pytra_int(ph)) || (__step_8 < 0L && py > __pytra_int(ph))) {
                        var pw: Long = __pytra_int(__pytra_len(__pytra_as_list(__pytra_get_index(lwss, py))))
                        val __step_9 = __pytra_int(1L)
                        var px = __pytra_int(0L)
                        while ((__step_9 >= 0L && px < __pytra_int(pw)) || (__step_9 < 0L && px > __pytra_int(pw))) {
                            if ((__pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(lwss, py)), px))) == __pytra_int(1L))) {
                                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, (__pytra_int((__pytra_int(gy) + __pytra_int(py))) % __pytra_int(h)))), (__pytra_int((__pytra_int(gx) + __pytra_int(px))) % __pytra_int(w)), 1L)
                            }
                            px += __step_9
                        }
                        py += __step_8
                    }
                }
            }
            gx += __step_3
        }
        gy += __step_2
    }
    var frames: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __step_11 = __pytra_int(1L)
    var __loop_10 = __pytra_int(0L)
    while ((__step_11 >= 0L && __loop_10 < __pytra_int(steps)) || (__step_11 < 0L && __loop_10 > __pytra_int(steps))) {
        frames = __pytra_as_list(frames); frames.add(render(grid, w, h, cell))
        grid = __pytra_as_list(next_state(grid, w, h))
        __loop_10 += __step_11
    }
    __pytra_noop(out_path, (__pytra_int(w) * __pytra_int(cell)), (__pytra_int(h) * __pytra_int(cell)), frames, mutableListOf<Any?>())
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_07_game_of_life_loop()
}
