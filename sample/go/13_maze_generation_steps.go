package main


// 13: Sample that outputs DFS maze-generation progress as a GIF.

func capture(grid []any, w int64, h int64, scale int64) []any {
    var width int64 = (w * scale)
    var height int64 = (h * scale)
    var frame []any = __pytra_as_list(__pytra_bytearray((width * height)))
    for y := int64(0); y < h; y += 1 {
        for x := int64(0); x < w; x += 1 {
            var v int64 = __pytra_ifexp((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)) == int64(0)), int64(255), int64(40))
            for yy := int64(0); yy < scale; yy += 1 {
                var base int64 = ((((y * scale) + yy) * width) + (x * scale))
                for xx := int64(0); xx < scale; xx += 1 {
                    __pytra_set_index(frame, (base + xx), v)
                }
            }
        }
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_13_maze_generation_steps() {
    var cell_w int64 = int64(89)
    var cell_h int64 = int64(67)
    var scale int64 = int64(5)
    var capture_every int64 = int64(20)
    var out_path string = __pytra_str("sample/out/13_maze_generation_steps.gif")
    var start float64 = __pytra_perf_counter()
    var grid []any = __pytra_as_list(func() []any { __out := []any{}; __step := __pytra_int(int64(1)); for __lc_i := __pytra_int(int64(0)); (__step >= 0 && __lc_i < __pytra_int(cell_h)) || (__step < 0 && __lc_i > __pytra_int(cell_h)); __lc_i += __step { __out = append(__out, __pytra_list_repeat(int64(1), cell_w)) }; return __out }())
    var stack []any = __pytra_as_list([]any{[]any{int64(1), int64(1)}})
    __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, int64(1))), int64(1), int64(0))
    var dirs []any = __pytra_as_list([]any{[]any{int64(2), int64(0)}, []any{(-int64(2)), int64(0)}, []any{int64(0), int64(2)}, []any{int64(0), (-int64(2))}})
    var frames []any = __pytra_as_list([]any{})
    var step int64 = int64(0)
    for (__pytra_len(stack) != 0) {
        __tuple_0 := __pytra_as_list(__pytra_as_list(__pytra_get_index(stack, (-int64(1)))))
        var x int64 = __pytra_int(__tuple_0[0])
        _ = x
        var y int64 = __pytra_int(__tuple_0[1])
        _ = y
        var candidates []any = __pytra_as_list([]any{})
        for k := int64(0); k < int64(4); k += 1 {
            __tuple_1 := __pytra_as_list(__pytra_as_list(__pytra_get_index(dirs, k)))
            var dx int64 = __pytra_int(__tuple_1[0])
            _ = dx
            var dy int64 = __pytra_int(__tuple_1[1])
            _ = dy
            var nx int64 = (x + dx)
            var ny int64 = (y + dy)
            if ((__pytra_int(nx) >= int64(1)) && (__pytra_int(nx) < (cell_w - int64(1))) && (__pytra_int(ny) >= int64(1)) && (__pytra_int(ny) < (cell_h - int64(1))) && (__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, ny)), nx)) == int64(1))) {
                if (__pytra_int(dx) == int64(2)) {
                    candidates = append(candidates, []any{nx, ny, (x + int64(1)), y})
                } else {
                    if (__pytra_int(dx) == (-int64(2))) {
                        candidates = append(candidates, []any{nx, ny, (x - int64(1)), y})
                    } else {
                        if (__pytra_int(dy) == int64(2)) {
                            candidates = append(candidates, []any{nx, ny, x, (y + int64(1))})
                        } else {
                            candidates = append(candidates, []any{nx, ny, x, (y - int64(1))})
                        }
                    }
                }
            }
        }
        if (__pytra_len(candidates) == int64(0)) {
            stack = __pytra_pop_last(stack)
        } else {
            var sel []any = __pytra_as_list(__pytra_as_list(__pytra_get_index(candidates, (__pytra_int((((x * int64(17)) + (y * int64(29))) + (__pytra_len(stack) * int64(13)))) % __pytra_len(candidates)))))
            __tuple_2 := __pytra_as_list(sel)
            var nx int64 = __pytra_int(__tuple_2[0])
            _ = nx
            var ny int64 = __pytra_int(__tuple_2[1])
            _ = ny
            var wx int64 = __pytra_int(__tuple_2[2])
            _ = wx
            var wy int64 = __pytra_int(__tuple_2[3])
            _ = wy
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, wy)), wx, int64(0))
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ny)), nx, int64(0))
            stack = append(stack, []any{nx, ny})
        }
        if ((step % capture_every) == int64(0)) {
            frames = append(frames, capture(grid, cell_w, cell_h, scale))
        }
        step += int64(1)
    }
    frames = append(frames, capture(grid, cell_w, cell_h, scale))
    __pytra_save_gif(out_path, (cell_w * scale), (cell_h * scale), frames, __pytra_grayscale_palette(), int64(4), int64(0))
    var elapsed float64 = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_13_maze_generation_steps()
}
