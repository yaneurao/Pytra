// Auto-generated Pytra Go native source from EAST3.
package main

import (
    "math"
)

// Runtime helpers are provided by py_runtime.go in the same package.
var _ = math.Pi


// 08: Sample that outputs Langton's Ant trajectories as a GIF.

func capture(grid []any, w int64, h int64) []any {
    var frame []any = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
    __step_0 := __pytra_int(int64(1))
    for y := __pytra_int(int64(0)); (__step_0 >= 0 && y < __pytra_int(h)) || (__step_0 < 0 && y > __pytra_int(h)); y += __step_0 {
        var row_base int64 = __pytra_int((__pytra_int(y) * __pytra_int(w)))
        __step_1 := __pytra_int(int64(1))
        for x := __pytra_int(int64(0)); (__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w)); x += __step_1 {
            __pytra_set_index(frame, (__pytra_int(row_base) + __pytra_int(x)), __pytra_ifexp((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)) != 0), int64(255), int64(0)))
        }
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_08_langtons_ant() {
    var w int64 = __pytra_int(int64(420))
    var h int64 = __pytra_int(int64(420))
    var out_path string = __pytra_str("sample/out/08_langtons_ant.gif")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var grid []any = __pytra_as_list(func() []any { __out := []any{}; __step := __pytra_int(int64(1)); for __lc_i := __pytra_int(int64(0)); (__step >= 0 && __lc_i < __pytra_int(h)) || (__step < 0 && __lc_i > __pytra_int(h)); __lc_i += __step { __out = append(__out, __pytra_list_repeat(int64(0), w)) }; return __out }())
    var x int64 = __pytra_int((__pytra_int(__pytra_int(w) / __pytra_int(int64(2)))))
    var y int64 = __pytra_int((__pytra_int(__pytra_int(h) / __pytra_int(int64(2)))))
    var d int64 = __pytra_int(int64(0))
    var steps_total int64 = __pytra_int(int64(600000))
    var capture_every int64 = __pytra_int(int64(3000))
    var frames []any = __pytra_as_list([]any{})
    __step_0 := __pytra_int(int64(1))
    for i := __pytra_int(int64(0)); (__step_0 >= 0 && i < __pytra_int(steps_total)) || (__step_0 < 0 && i > __pytra_int(steps_total)); i += __step_0 {
        if (__pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x))) == __pytra_int(int64(0))) {
            d = __pytra_int((__pytra_int((__pytra_int(d) + __pytra_int(int64(1)))) % __pytra_int(int64(4))))
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, y)), x, int64(1))
        } else {
            d = __pytra_int((__pytra_int((__pytra_int(d) + __pytra_int(int64(3)))) % __pytra_int(int64(4))))
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, y)), x, int64(0))
        }
        if (__pytra_int(d) == __pytra_int(int64(0))) {
            y = __pytra_int((__pytra_int((__pytra_int((__pytra_int(y) - __pytra_int(int64(1)))) + __pytra_int(h))) % __pytra_int(h)))
        } else {
            if (__pytra_int(d) == __pytra_int(int64(1))) {
                x = __pytra_int((__pytra_int((__pytra_int(x) + __pytra_int(int64(1)))) % __pytra_int(w)))
            } else {
                if (__pytra_int(d) == __pytra_int(int64(2))) {
                    y = __pytra_int((__pytra_int((__pytra_int(y) + __pytra_int(int64(1)))) % __pytra_int(h)))
                } else {
                    x = __pytra_int((__pytra_int((__pytra_int((__pytra_int(x) - __pytra_int(int64(1)))) + __pytra_int(w))) % __pytra_int(w)))
                }
            }
        }
        if (__pytra_int((__pytra_int(i) % __pytra_int(capture_every))) == __pytra_int(int64(0))) {
            frames = append(__pytra_as_list(frames), capture(grid, w, h))
        }
    }
    __pytra_noop(out_path, w, h, frames, []any{})
    var elapsed float64 = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_08_langtons_ant()
}
