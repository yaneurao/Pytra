package main


// 08: Sample that outputs Langton's Ant trajectories as a GIF.

func capture(grid []any, w int64, h int64) []any {
    var frame []any = __pytra_as_list(__pytra_bytearray((w * h)))
    for y := int64(0); y < h; y += 1 {
        var row_base int64 = (y * w)
        for x := int64(0); x < w; x += 1 {
            __pytra_set_index(frame, (row_base + x), __pytra_ifexp((__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)) != 0), int64(255), int64(0)))
        }
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_08_langtons_ant() {
    var w int64 = int64(420)
    var h int64 = int64(420)
    var out_path string = __pytra_str("sample/out/08_langtons_ant.gif")
    var start float64 = __pytra_perf_counter()
    var grid []any = __pytra_as_list(func() []any { __out := []any{}; __step := __pytra_int(int64(1)); for __lc_i := __pytra_int(int64(0)); (__step >= 0 && __lc_i < __pytra_int(h)) || (__step < 0 && __lc_i > __pytra_int(h)); __lc_i += __step { __out = append(__out, __pytra_list_repeat(int64(0), w)) }; return __out }())
    var x int64 = __pytra_int((w / int64(2)))
    var y int64 = __pytra_int((h / int64(2)))
    var d int64 = int64(0)
    var steps_total int64 = int64(600000)
    var capture_every int64 = int64(3000)
    var frames []any = __pytra_as_list([]any{})
    for i := int64(0); i < steps_total; i += 1 {
        if (__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(grid, y)), x)) == int64(0)) {
            d = ((d + int64(1)) % int64(4))
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, y)), x, int64(1))
        } else {
            d = ((d + int64(3)) % int64(4))
            __pytra_set_index(__pytra_as_list(__pytra_get_index(grid, y)), x, int64(0))
        }
        if (d == int64(0)) {
            y = (((y - int64(1)) + h) % h)
        } else {
            if (d == int64(1)) {
                x = ((x + int64(1)) % w)
            } else {
                if (d == int64(2)) {
                    y = ((y + int64(1)) % h)
                } else {
                    x = (((x - int64(1)) + w) % w)
                }
            }
        }
        if ((i % capture_every) == int64(0)) {
            frames = append(frames, capture(grid, w, h))
        }
    }
    __pytra_save_gif(out_path, w, h, frames, __pytra_grayscale_palette(), int64(5), int64(0))
    var elapsed float64 = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_08_langtons_ant()
}
