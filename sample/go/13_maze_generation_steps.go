package main

import (
    "math"
)

var _ = math.Pi


// 13: Sample that outputs DFS maze-generation progress as a GIF.

func capture(grid []any, w int64, h int64, scale int64) []any {
    var width int64 = __pytra_int((__pytra_int(w) * __pytra_int(scale)))
    var height int64 = __pytra_int((__pytra_int(h) * __pytra_int(scale)))
    var frame []any = __pytra_as_list(__pytra_bytearray((__pytra_int(width) * __pytra_int(height))))
    __step_0 := __pytra_int(int64(1))
    for y := __pytra_int(int64(0)); (__step_0 >= 0 && y < __pytra_int(h)) || (__step_0 < 0 && y > __pytra_int(h)); y += __step_0 {
        __step_1 := __pytra_int(int64(1))
        for x := __pytra_int(int64(0)); (__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w)); x += __step_1 {
            var v int64 = __pytra_int(__pytra_ifexp((__pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x))) == __pytra_int(int64(0))), int64(255), int64(40)))
            __step_2 := __pytra_int(int64(1))
            for yy := __pytra_int(int64(0)); (__step_2 >= 0 && yy < __pytra_int(scale)) || (__step_2 < 0 && yy > __pytra_int(scale)); yy += __step_2 {
                var base int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int(y) * __pytra_int(scale))) + __pytra_int(yy))) * __pytra_int(width))) + __pytra_int((__pytra_int(x) * __pytra_int(scale)))))
                __step_3 := __pytra_int(int64(1))
                for xx := __pytra_int(int64(0)); (__step_3 >= 0 && xx < __pytra_int(scale)) || (__step_3 < 0 && xx > __pytra_int(scale)); xx += __step_3 {
                    __pytra_set_index(frame, (__pytra_int(base) + __pytra_int(xx)), v)
                }
            }
        }
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_13_maze_generation_steps() {
    var cell_w int64 = __pytra_int(int64(89))
    var cell_h int64 = __pytra_int(int64(67))
    var scale int64 = __pytra_int(int64(5))
    var capture_every int64 = __pytra_int(int64(20))
    var out_path string = __pytra_str("sample/out/13_maze_generation_steps.gif")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var grid []any = __pytra_as_list(func() []any { __out := []any{}; __step := __pytra_int(int64(1)); for __lc_i := __pytra_int(int64(0)); (__step >= 0 && __lc_i < __pytra_int(cell_h)) || (__step < 0 && __lc_i > __pytra_int(cell_h)); __lc_i += __step { __out = append(__out, __pytra_list_repeat(int64(1), cell_w)) }; return __out }())
    var stack []any = __pytra_as_list([]any{[]any{int64(1), int64(1)}})
    __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, int64(1))), int64(1), int64(0))
    var dirs []any = __pytra_as_list([]any{[]any{int64(2), int64(0)}, []any{(-int64(2)), int64(0)}, []any{int64(0), int64(2)}, []any{int64(0), (-int64(2))}})
    var frames []any = __pytra_as_list([]any{})
    var step int64 = __pytra_int(int64(0))
    for (__pytra_len(stack) != 0) {
        __tuple_0 := __pytra_as_list(__pytra_as_list(__pytra_get_index(stack, (-int64(1)))))
        var x int64 = __pytra_int(__tuple_0[0])
        _ = x
        var y int64 = __pytra_int(__tuple_0[1])
        _ = y
        var candidates []any = __pytra_as_list([]any{})
        __step_1 := __pytra_int(int64(1))
        for k := __pytra_int(int64(0)); (__step_1 >= 0 && k < __pytra_int(int64(4))) || (__step_1 < 0 && k > __pytra_int(int64(4))); k += __step_1 {
            __tuple_2 := __pytra_as_list(__pytra_as_list(__pytra_get_index(dirs, k)))
            var dx int64 = __pytra_int(__tuple_2[0])
            _ = dx
            var dy int64 = __pytra_int(__tuple_2[1])
            _ = dy
            var nx int64 = __pytra_int((x + dx))
            var ny int64 = __pytra_int((y + dy))
            if ((__pytra_int(nx) >= __pytra_int(int64(1))) && (__pytra_int(nx) < __pytra_int((__pytra_int(cell_w) - __pytra_int(int64(1))))) && (__pytra_int(ny) >= __pytra_int(int64(1))) && (__pytra_int(ny) < __pytra_int((__pytra_int(cell_h) - __pytra_int(int64(1))))) && (__pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, ny)), nx))) == __pytra_int(int64(1)))) {
                if (__pytra_int(dx) == __pytra_int(int64(2))) {
                    candidates = append(__pytra_as_list(candidates), []any{nx, ny, (x + int64(1)), y})
                } else {
                    if (__pytra_int(dx) == __pytra_int((-int64(2)))) {
                        candidates = append(__pytra_as_list(candidates), []any{nx, ny, (x - int64(1)), y})
                    } else {
                        if (__pytra_int(dy) == __pytra_int(int64(2))) {
                            candidates = append(__pytra_as_list(candidates), []any{nx, ny, x, (y + int64(1))})
                        } else {
                            candidates = append(__pytra_as_list(candidates), []any{nx, ny, x, (y - int64(1))})
                        }
                    }
                }
            }
        }
        if (__pytra_int(__pytra_len(candidates)) == __pytra_int(int64(0))) {
            stack = __pytra_pop_last(__pytra_as_list(stack))
        } else {
            var sel []any = __pytra_as_list(__pytra_as_list(__pytra_get_index(candidates, (__pytra_int((((x * int64(17)) + (y * int64(29))) + (__pytra_int(__pytra_len(stack)) * __pytra_int(int64(13))))) % __pytra_int(__pytra_len(candidates))))))
            __tuple_3 := __pytra_as_list(sel)
            var nx int64 = __pytra_int(__tuple_3[0])
            _ = nx
            var ny int64 = __pytra_int(__tuple_3[1])
            _ = ny
            var wx int64 = __pytra_int(__tuple_3[2])
            _ = wx
            var wy int64 = __pytra_int(__tuple_3[3])
            _ = wy
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, wy)), wx, int64(0))
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, ny)), nx, int64(0))
            stack = append(__pytra_as_list(stack), []any{nx, ny})
        }
        if (__pytra_int((__pytra_int(step) % __pytra_int(capture_every))) == __pytra_int(int64(0))) {
            frames = append(__pytra_as_list(frames), capture(grid, cell_w, cell_h, scale))
        }
        step += int64(1)
    }
    frames = append(__pytra_as_list(frames), capture(grid, cell_w, cell_h, scale))
    __pytra_noop(out_path, (__pytra_int(cell_w) * __pytra_int(scale)), (__pytra_int(cell_h) * __pytra_int(scale)), frames, []any{})
    var elapsed float64 = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_13_maze_generation_steps()
}
