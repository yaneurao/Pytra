package main


// 12: Sample that outputs intermediate states of bubble sort as a GIF.

func render(values []any, w int64, h int64) []any {
    var frame []any = __pytra_as_list(__pytra_bytearray((w * h)))
    var n int64 = __pytra_len(values)
    var bar_w float64 = (float64(w) / float64(n))
    var __hoisted_cast_1 float64 = __pytra_float(n)
    var __hoisted_cast_2 float64 = __pytra_float(h)
    for i := int64(0); i < n; i += 1 {
        var x0 int64 = __pytra_int((float64(i) * bar_w))
        var x1 int64 = __pytra_int((float64((i + int64(1))) * bar_w))
        if (x1 <= x0) {
            x1 = (x0 + int64(1))
        }
        var bh int64 = __pytra_int(((float64(__pytra_int(__pytra_get_index(values, i))) / __hoisted_cast_1) * __hoisted_cast_2))
        var y int64 = (h - bh)
        for y := y; y < h; y += 1 {
            for x := x0; x < x1; x += 1 {
                __pytra_set_index(frame, ((y * w) + x), int64(255))
            }
        }
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_12_sort_visualizer() {
    var w int64 = int64(320)
    var h int64 = int64(180)
    var n int64 = int64(124)
    var out_path string = __pytra_str("sample/out/12_sort_visualizer.gif")
    var start float64 = __pytra_perf_counter()
    var values []any = __pytra_as_list([]any{})
    for i := int64(0); i < n; i += 1 {
        values = append(values, (((i * int64(37)) + int64(19)) % n))
    }
    var frames []any = __pytra_as_list([]any{render(values, w, h)})
    var frame_stride int64 = int64(16)
    var op int64 = int64(0)
    for i := int64(0); i < n; i += 1 {
        var swapped bool = __pytra_truthy(false)
        for j := int64(0); j < ((n - i) - int64(1)); j += 1 {
            if (__pytra_int(__pytra_get_index(values, j)) > __pytra_int(__pytra_get_index(values, (j + int64(1))))) {
                __tuple_0 := __pytra_as_list([]any{__pytra_int(__pytra_get_index(values, (j + int64(1)))), __pytra_int(__pytra_get_index(values, j))})
                __pytra_set_index(values, j, __pytra_int(__tuple_0[0]))
                __pytra_set_index(values, (j + int64(1)), __pytra_int(__tuple_0[1]))
                swapped = __pytra_truthy(true)
            }
            if ((op % frame_stride) == int64(0)) {
                frames = append(frames, render(values, w, h))
            }
            op += int64(1)
        }
        if (!swapped) {
            break
        }
    }
    __pytra_save_gif(out_path, w, h, frames, __pytra_grayscale_palette(), int64(3), int64(0))
    var elapsed float64 = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_12_sort_visualizer()
}
