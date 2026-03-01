package main


// 12: Sample that outputs intermediate states of bubble sort as a GIF.

func render(values []any, w int64, h int64) []any {
    var frame []any = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
    var n int64 = __pytra_int(__pytra_len(values))
    var bar_w float64 = __pytra_float((__pytra_float(w) / __pytra_float(n)))
    var __hoisted_cast_1 float64 = __pytra_float(__pytra_float(n))
    var __hoisted_cast_2 float64 = __pytra_float(__pytra_float(h))
    __step_0 := __pytra_int(int64(1))
    for i := __pytra_int(int64(0)); (__step_0 >= 0 && i < __pytra_int(n)) || (__step_0 < 0 && i > __pytra_int(n)); i += __step_0 {
        var x0 int64 = __pytra_int(__pytra_int((__pytra_float(i) * __pytra_float(bar_w))))
        var x1 int64 = __pytra_int(__pytra_int((__pytra_float((__pytra_int(i) + __pytra_int(int64(1)))) * __pytra_float(bar_w))))
        if (__pytra_int(x1) <= __pytra_int(x0)) {
            x1 = __pytra_int((__pytra_int(x0) + __pytra_int(int64(1))))
        }
        var bh int64 = __pytra_int(__pytra_int((__pytra_float((__pytra_float(__pytra_int(__pytra_get_index(values, i))) / __pytra_float(__hoisted_cast_1))) * __pytra_float(__hoisted_cast_2))))
        var y int64 = __pytra_int((__pytra_int(h) - __pytra_int(bh)))
        __step_1 := __pytra_int(int64(1))
        for y := __pytra_int(y); (__step_1 >= 0 && y < __pytra_int(h)) || (__step_1 < 0 && y > __pytra_int(h)); y += __step_1 {
            __step_2 := __pytra_int(int64(1))
            for x := __pytra_int(x0); (__step_2 >= 0 && x < __pytra_int(x1)) || (__step_2 < 0 && x > __pytra_int(x1)); x += __step_2 {
                __pytra_set_index(frame, (__pytra_int((__pytra_int(y) * __pytra_int(w))) + __pytra_int(x)), int64(255))
            }
        }
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_12_sort_visualizer() {
    var w int64 = __pytra_int(int64(320))
    var h int64 = __pytra_int(int64(180))
    var n int64 = __pytra_int(int64(124))
    var out_path string = __pytra_str("sample/out/12_sort_visualizer.gif")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var values []any = __pytra_as_list([]any{})
    __step_0 := __pytra_int(int64(1))
    for i := __pytra_int(int64(0)); (__step_0 >= 0 && i < __pytra_int(n)) || (__step_0 < 0 && i > __pytra_int(n)); i += __step_0 {
        values = append(__pytra_as_list(values), (__pytra_int((__pytra_int((__pytra_int(i) * __pytra_int(int64(37)))) + __pytra_int(int64(19)))) % __pytra_int(n)))
    }
    var frames []any = __pytra_as_list([]any{render(values, w, h)})
    var frame_stride int64 = __pytra_int(int64(16))
    var op int64 = __pytra_int(int64(0))
    __step_1 := __pytra_int(int64(1))
    for i := __pytra_int(int64(0)); (__step_1 >= 0 && i < __pytra_int(n)) || (__step_1 < 0 && i > __pytra_int(n)); i += __step_1 {
        var swapped bool = __pytra_truthy(false)
        __step_2 := __pytra_int(int64(1))
        for j := __pytra_int(int64(0)); (__step_2 >= 0 && j < __pytra_int((__pytra_int((__pytra_int(n) - __pytra_int(i))) - __pytra_int(int64(1))))) || (__step_2 < 0 && j > __pytra_int((__pytra_int((__pytra_int(n) - __pytra_int(i))) - __pytra_int(int64(1))))); j += __step_2 {
            if (__pytra_int(__pytra_int(__pytra_get_index(values, j))) > __pytra_int(__pytra_int(__pytra_get_index(values, (__pytra_int(j) + __pytra_int(int64(1))))))) {
                __tuple_3 := __pytra_as_list([]any{__pytra_int(__pytra_get_index(values, (__pytra_int(j) + __pytra_int(int64(1))))), __pytra_int(__pytra_get_index(values, j))})
                __pytra_set_index(values, j, __pytra_int(__tuple_3[0]))
                __pytra_set_index(values, (__pytra_int(j) + __pytra_int(int64(1))), __pytra_int(__tuple_3[1]))
                swapped = __pytra_truthy(true)
            }
            if (__pytra_int((__pytra_int(op) % __pytra_int(frame_stride))) == __pytra_int(int64(0))) {
                frames = append(__pytra_as_list(frames), render(values, w, h))
            }
            op += int64(1)
        }
        if (!swapped) {
            break
        }
    }
    __pytra_noop(out_path, w, h, frames, []any{})
    var elapsed float64 = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_12_sort_visualizer()
}
