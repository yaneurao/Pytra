package main


// 07: Sample that outputs Game of Life evolution as a GIF.

func next_state(grid []any, w int64, h int64) []any {
    var nxt []any = __pytra_as_list([]any{})
    for y := int64(0); y < h; y += 1 {
        var row []any = __pytra_as_list([]any{})
        for x := int64(0); x < w; x += 1 {
            var cnt int64 = int64(0)
            for dy := (-int64(1)); dy < int64(2); dy += 1 {
                for dx := (-int64(1)); dx < int64(2); dx += 1 {
                    if ((dx != int64(0)) || (dy != int64(0))) {
                        var nx int64 = (((x + dx) + w) % w)
                        var ny int64 = (((y + dy) + h) % h)
                        cnt += __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, ny)), nx))
                    }
                }
            }
            var alive int64 = __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x))
            if ((alive == int64(1)) && ((cnt == int64(2)) || (cnt == int64(3)))) {
                row = append(row, int64(1))
            } else {
                if ((alive == int64(0)) && (cnt == int64(3))) {
                    row = append(row, int64(1))
                } else {
                    row = append(row, int64(0))
                }
            }
        }
        nxt = append(nxt, row)
    }
    return __pytra_as_list(nxt)
}

func render(grid []any, w int64, h int64, cell int64) []any {
    var width int64 = (w * cell)
    var height int64 = (h * cell)
    var frame []any = __pytra_as_list(__pytra_bytearray((width * height)))
    for y := int64(0); y < h; y += 1 {
        for x := int64(0); x < w; x += 1 {
            var v int64 = __pytra_ifexp((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)) != 0), int64(255), int64(0))
            for yy := int64(0); yy < cell; yy += 1 {
                var base int64 = ((((y * cell) + yy) * width) + (x * cell))
                for xx := int64(0); xx < cell; xx += 1 {
                    __pytra_set_index(frame, (base + xx), v)
                }
            }
        }
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_07_game_of_life_loop() {
    var w int64 = int64(144)
    var h int64 = int64(108)
    var cell int64 = int64(4)
    var steps int64 = int64(105)
    var out_path string = __pytra_str("sample/out/07_game_of_life_loop.gif")
    var start float64 = __pytra_perf_counter()
    var grid []any = __pytra_as_list(func() []any { __out := []any{}; __step := __pytra_int(int64(1)); for __lc_i := __pytra_int(int64(0)); (__step >= 0 && __lc_i < __pytra_int(h)) || (__step < 0 && __lc_i > __pytra_int(h)); __lc_i += __step { __out = append(__out, __pytra_list_repeat(int64(0), w)) }; return __out }())
    for y := int64(0); y < h; y += 1 {
        for x := int64(0); x < w; x += 1 {
            var noise int64 = (((((x * int64(37)) + (y * int64(73))) + ((x * y) % int64(19))) + ((x + y) % int64(11))) % int64(97))
            if (noise < int64(3)) {
                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, y)), x, int64(1))
            }
        }
    }
    var glider []any = __pytra_as_list([]any{[]any{int64(0), int64(1), int64(0)}, []any{int64(0), int64(0), int64(1)}, []any{int64(1), int64(1), int64(1)}})
    var r_pentomino []any = __pytra_as_list([]any{[]any{int64(0), int64(1), int64(1)}, []any{int64(1), int64(1), int64(0)}, []any{int64(0), int64(1), int64(0)}})
    var lwss []any = __pytra_as_list([]any{[]any{int64(0), int64(1), int64(1), int64(1), int64(1)}, []any{int64(1), int64(0), int64(0), int64(0), int64(1)}, []any{int64(0), int64(0), int64(0), int64(0), int64(1)}, []any{int64(1), int64(0), int64(0), int64(1), int64(0)}})
    __step_0 := int64(18)
    for gy := int64(8); (__step_0 >= 0 && gy < (h - int64(8))) || (__step_0 < 0 && gy > (h - int64(8))); gy += __step_0 {
        __step_1 := int64(22)
        for gx := int64(8); (__step_1 >= 0 && gx < (w - int64(8))) || (__step_1 < 0 && gx > (w - int64(8))); gx += __step_1 {
            var kind int64 = (((gx * int64(7)) + (gy * int64(11))) % int64(3))
            if (kind == int64(0)) {
                var ph int64 = __pytra_len(glider)
                for py := int64(0); py < ph; py += 1 {
                    var pw int64 = __pytra_len(__pytra_as_list(__pytra_get_index(glider, py)))
                    for px := int64(0); px < pw; px += 1 {
                        if (__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(glider, py)), px)) == int64(1)) {
                            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ((gy + py) % h))), ((gx + px) % w), int64(1))
                        }
                    }
                }
            } else {
                if (kind == int64(1)) {
                    var ph int64 = __pytra_len(r_pentomino)
                    for py := int64(0); py < ph; py += 1 {
                        var pw int64 = __pytra_len(__pytra_as_list(__pytra_get_index(r_pentomino, py)))
                        for px := int64(0); px < pw; px += 1 {
                            if (__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(r_pentomino, py)), px)) == int64(1)) {
                                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ((gy + py) % h))), ((gx + px) % w), int64(1))
                            }
                        }
                    }
                } else {
                    var ph int64 = __pytra_len(lwss)
                    for py := int64(0); py < ph; py += 1 {
                        var pw int64 = __pytra_len(__pytra_as_list(__pytra_get_index(lwss, py)))
                        for px := int64(0); px < pw; px += 1 {
                            if (__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(lwss, py)), px)) == int64(1)) {
                                __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ((gy + py) % h))), ((gx + px) % w), int64(1))
                            }
                        }
                    }
                }
            }
        }
    }
    var frames []any = __pytra_as_list([]any{})
    for __loop_2 := int64(0); __loop_2 < steps; __loop_2 += 1 {
        frames = append(frames, render(grid, w, h, cell))
        grid = __pytra_as_list(next_state(grid, w, h))
    }
    __pytra_save_gif(out_path, (w * cell), (h * cell), frames, __pytra_grayscale_palette(), int64(4), int64(0))
    var elapsed float64 = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_07_game_of_life_loop()
}
