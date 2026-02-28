package main

import (
    "math"
)

var _ = math.Pi


// 07: Sample that outputs Game of Life evolution as a GIF.

func next_state(grid []any, w int64, h int64) []any {
    var nxt []any = __pytra_as_list([]any{})
    __step_0 := __pytra_int(int64(1))
    for y := __pytra_int(int64(0)); (__step_0 >= 0 && y < __pytra_int(h)) || (__step_0 < 0 && y > __pytra_int(h)); y += __step_0 {
        var row []any = __pytra_as_list([]any{})
        __step_1 := __pytra_int(int64(1))
        for x := __pytra_int(int64(0)); (__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w)); x += __step_1 {
            var cnt int64 = __pytra_int(int64(0))
            __step_2 := __pytra_int(int64(1))
            for dy := __pytra_int((-int64(1))); (__step_2 >= 0 && dy < __pytra_int(int64(2))) || (__step_2 < 0 && dy > __pytra_int(int64(2))); dy += __step_2 {
                __step_3 := __pytra_int(int64(1))
                for dx := __pytra_int((-int64(1))); (__step_3 >= 0 && dx < __pytra_int(int64(2))) || (__step_3 < 0 && dx > __pytra_int(int64(2))); dx += __step_3 {
                    if ((__pytra_int(dx) != __pytra_int(int64(0))) || (__pytra_int(dy) != __pytra_int(int64(0)))) {
                        var nx int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int(x) + __pytra_int(dx))) + __pytra_int(w))) % __pytra_int(w)))
                        var ny int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int(y) + __pytra_int(dy))) + __pytra_int(h))) % __pytra_int(h)))
                        cnt += __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, ny)), nx))
                    }
                }
            }
            var alive int64 = __pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)))
            if ((__pytra_int(alive) == __pytra_int(int64(1))) && ((__pytra_int(cnt) == __pytra_int(int64(2))) || (__pytra_int(cnt) == __pytra_int(int64(3))))) {
                row = append(__pytra_as_list(row), int64(1))
            } else {
                if ((__pytra_int(alive) == __pytra_int(int64(0))) && (__pytra_int(cnt) == __pytra_int(int64(3)))) {
                    row = append(__pytra_as_list(row), int64(1))
                } else {
                    row = append(__pytra_as_list(row), int64(0))
                }
            }
        }
        nxt = append(__pytra_as_list(nxt), row)
    }
    return __pytra_as_list(nxt)
}

func render(grid []any, w int64, h int64, cell int64) []any {
    var width int64 = __pytra_int((__pytra_int(w) * __pytra_int(cell)))
    var height int64 = __pytra_int((__pytra_int(h) * __pytra_int(cell)))
    var frame []any = __pytra_as_list(__pytra_bytearray((__pytra_int(width) * __pytra_int(height))))
    __step_0 := __pytra_int(int64(1))
    for y := __pytra_int(int64(0)); (__step_0 >= 0 && y < __pytra_int(h)) || (__step_0 < 0 && y > __pytra_int(h)); y += __step_0 {
        __step_1 := __pytra_int(int64(1))
        for x := __pytra_int(int64(0)); (__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w)); x += __step_1 {
            var v int64 = __pytra_int(__pytra_ifexp((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)) != 0), int64(255), int64(0)))
            __step_2 := __pytra_int(int64(1))
            for yy := __pytra_int(int64(0)); (__step_2 >= 0 && yy < __pytra_int(cell)) || (__step_2 < 0 && yy > __pytra_int(cell)); yy += __step_2 {
                var base int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int(y) * __pytra_int(cell))) + __pytra_int(yy))) * __pytra_int(width))) + __pytra_int((__pytra_int(x) * __pytra_int(cell)))))
                __step_3 := __pytra_int(int64(1))
                for xx := __pytra_int(int64(0)); (__step_3 >= 0 && xx < __pytra_int(cell)) || (__step_3 < 0 && xx > __pytra_int(cell)); xx += __step_3 {
                    __pytra_set_index(frame, (__pytra_int(base) + __pytra_int(xx)), v)
                }
            }
        }
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_07_game_of_life_loop() {
    var w int64 = __pytra_int(int64(144))
    var h int64 = __pytra_int(int64(108))
    var cell int64 = __pytra_int(int64(4))
    var steps int64 = __pytra_int(int64(105))
    var out_path string = __pytra_str("sample/out/07_game_of_life_loop.gif")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var grid []any = __pytra_as_list(func() []any { __out := []any{}; __step := __pytra_int(int64(1)); for __lc_i := __pytra_int(int64(0)); (__step >= 0 && __lc_i < __pytra_int(h)) || (__step < 0 && __lc_i > __pytra_int(h)); __lc_i += __step { __out = append(__out, __pytra_list_repeat(int64(0), w)) }; return __out }())
    __step_0 := __pytra_int(int64(1))
    for y := __pytra_int(int64(0)); (__step_0 >= 0 && y < __pytra_int(h)) || (__step_0 < 0 && y > __pytra_int(h)); y += __step_0 {
        __step_1 := __pytra_int(int64(1))
        for x := __pytra_int(int64(0)); (__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w)); x += __step_1 {
            var noise int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int(x) * __pytra_int(int64(37)))) + __pytra_int((__pytra_int(y) * __pytra_int(int64(73)))))) + __pytra_int((__pytra_int((__pytra_int(x) * __pytra_int(y))) % __pytra_int(int64(19)))))) + __pytra_int((__pytra_int((__pytra_int(x) + __pytra_int(y))) % __pytra_int(int64(11)))))) % __pytra_int(int64(97))))
            if (__pytra_int(noise) < __pytra_int(int64(3))) {
                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, y)), x, int64(1))
            }
        }
    }
    var glider []any = __pytra_as_list([]any{[]any{int64(0), int64(1), int64(0)}, []any{int64(0), int64(0), int64(1)}, []any{int64(1), int64(1), int64(1)}})
    var r_pentomino []any = __pytra_as_list([]any{[]any{int64(0), int64(1), int64(1)}, []any{int64(1), int64(1), int64(0)}, []any{int64(0), int64(1), int64(0)}})
    var lwss []any = __pytra_as_list([]any{[]any{int64(0), int64(1), int64(1), int64(1), int64(1)}, []any{int64(1), int64(0), int64(0), int64(0), int64(1)}, []any{int64(0), int64(0), int64(0), int64(0), int64(1)}, []any{int64(1), int64(0), int64(0), int64(1), int64(0)}})
    __step_2 := __pytra_int(int64(18))
    for gy := __pytra_int(int64(8)); (__step_2 >= 0 && gy < __pytra_int((__pytra_int(h) - __pytra_int(int64(8))))) || (__step_2 < 0 && gy > __pytra_int((__pytra_int(h) - __pytra_int(int64(8))))); gy += __step_2 {
        __step_3 := __pytra_int(int64(22))
        for gx := __pytra_int(int64(8)); (__step_3 >= 0 && gx < __pytra_int((__pytra_int(w) - __pytra_int(int64(8))))) || (__step_3 < 0 && gx > __pytra_int((__pytra_int(w) - __pytra_int(int64(8))))); gx += __step_3 {
            var kind int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int(gx) * __pytra_int(int64(7)))) + __pytra_int((__pytra_int(gy) * __pytra_int(int64(11)))))) % __pytra_int(int64(3))))
            if (__pytra_int(kind) == __pytra_int(int64(0))) {
                var ph int64 = __pytra_int(__pytra_len(glider))
                __step_4 := __pytra_int(int64(1))
                for py := __pytra_int(int64(0)); (__step_4 >= 0 && py < __pytra_int(ph)) || (__step_4 < 0 && py > __pytra_int(ph)); py += __step_4 {
                    var pw int64 = __pytra_int(__pytra_len(__pytra_as_list(__pytra_get_index(glider, py))))
                    __step_5 := __pytra_int(int64(1))
                    for px := __pytra_int(int64(0)); (__step_5 >= 0 && px < __pytra_int(pw)) || (__step_5 < 0 && px > __pytra_int(pw)); px += __step_5 {
                        if (__pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(glider, py)), px))) == __pytra_int(int64(1))) {
                            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, (__pytra_int((__pytra_int(gy) + __pytra_int(py))) % __pytra_int(h)))), (__pytra_int((__pytra_int(gx) + __pytra_int(px))) % __pytra_int(w)), int64(1))
                        }
                    }
                }
            } else {
                if (__pytra_int(kind) == __pytra_int(int64(1))) {
                    var ph int64 = __pytra_int(__pytra_len(r_pentomino))
                    __step_6 := __pytra_int(int64(1))
                    for py := __pytra_int(int64(0)); (__step_6 >= 0 && py < __pytra_int(ph)) || (__step_6 < 0 && py > __pytra_int(ph)); py += __step_6 {
                        var pw int64 = __pytra_int(__pytra_len(__pytra_as_list(__pytra_get_index(r_pentomino, py))))
                        __step_7 := __pytra_int(int64(1))
                        for px := __pytra_int(int64(0)); (__step_7 >= 0 && px < __pytra_int(pw)) || (__step_7 < 0 && px > __pytra_int(pw)); px += __step_7 {
                            if (__pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(r_pentomino, py)), px))) == __pytra_int(int64(1))) {
                                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, (__pytra_int((__pytra_int(gy) + __pytra_int(py))) % __pytra_int(h)))), (__pytra_int((__pytra_int(gx) + __pytra_int(px))) % __pytra_int(w)), int64(1))
                            }
                        }
                    }
                } else {
                    var ph int64 = __pytra_int(__pytra_len(lwss))
                    __step_8 := __pytra_int(int64(1))
                    for py := __pytra_int(int64(0)); (__step_8 >= 0 && py < __pytra_int(ph)) || (__step_8 < 0 && py > __pytra_int(ph)); py += __step_8 {
                        var pw int64 = __pytra_int(__pytra_len(__pytra_as_list(__pytra_get_index(lwss, py))))
                        __step_9 := __pytra_int(int64(1))
                        for px := __pytra_int(int64(0)); (__step_9 >= 0 && px < __pytra_int(pw)) || (__step_9 < 0 && px > __pytra_int(pw)); px += __step_9 {
                            if (__pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(lwss, py)), px))) == __pytra_int(int64(1))) {
                                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, (__pytra_int((__pytra_int(gy) + __pytra_int(py))) % __pytra_int(h)))), (__pytra_int((__pytra_int(gx) + __pytra_int(px))) % __pytra_int(w)), int64(1))
                            }
                        }
                    }
                }
            }
        }
    }
    var frames []any = __pytra_as_list([]any{})
    __step_11 := __pytra_int(int64(1))
    for __loop_10 := __pytra_int(int64(0)); (__step_11 >= 0 && __loop_10 < __pytra_int(steps)) || (__step_11 < 0 && __loop_10 > __pytra_int(steps)); __loop_10 += __step_11 {
        frames = append(__pytra_as_list(frames), render(grid, w, h, cell))
        grid = __pytra_as_list(next_state(grid, w, h))
    }
    __pytra_noop(out_path, (__pytra_int(w) * __pytra_int(cell)), (__pytra_int(h) * __pytra_int(cell)), frames, []any{})
    var elapsed float64 = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_07_game_of_life_loop()
}
