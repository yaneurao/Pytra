package main


// 09: Sample that outputs a simple fire effect as a GIF.

func fire_palette() []any {
    var p []any = __pytra_as_list([]any{})
    for i := int64(0); i < int64(256); i += 1 {
        var r int64 = int64(0)
        var g int64 = int64(0)
        var b int64 = int64(0)
        if (i < int64(85)) {
            r = (i * int64(3))
            g = int64(0)
            b = int64(0)
        } else {
            if (i < int64(170)) {
                r = int64(255)
                g = ((i - int64(85)) * int64(3))
                b = int64(0)
            } else {
                r = int64(255)
                g = int64(255)
                b = ((i - int64(170)) * int64(3))
            }
        }
        p = append(p, r)
        p = append(p, g)
        p = append(p, b)
    }
    return __pytra_as_list(__pytra_bytes(p))
}

func run_09_fire_simulation() {
    var w int64 = int64(380)
    var h int64 = int64(260)
    var steps int64 = int64(420)
    var out_path string = __pytra_str("sample/out/09_fire_simulation.gif")
    var start float64 = __pytra_perf_counter()
    var heat []any = __pytra_as_list(func() []any { __out := []any{}; __step := __pytra_int(int64(1)); for __lc_i := __pytra_int(int64(0)); (__step >= 0 && __lc_i < __pytra_int(h)) || (__step < 0 && __lc_i > __pytra_int(h)); __lc_i += __step { __out = append(__out, __pytra_list_repeat(int64(0), w)) }; return __out }())
    var frames []any = __pytra_as_list([]any{})
    for t := int64(0); t < steps; t += 1 {
        for x := int64(0); x < w; x += 1 {
            var val int64 = (int64(170) + (((x * int64(13)) + (t * int64(17))) % int64(86)))
            __pytra_set_index(__pytra_as_list(__pytra_get_index(heat, (h - int64(1)))), x, val)
        }
        for y := int64(1); y < h; y += 1 {
            for x := int64(0); x < w; x += 1 {
                var a int64 = __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)), x))
                var b int64 = __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)), (((x - int64(1)) + w) % w)))
                var c int64 = __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)), ((x + int64(1)) % w)))
                var d int64 = __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, ((y + int64(1)) % h))), x))
                var v int64 = __pytra_int(((((a + b) + c) + d) / int64(4)))
                var cool int64 = (int64(1) + (((x + y) + t) % int64(3)))
                var nv int64 = (v - cool)
                __pytra_set_index(__pytra_as_list(__pytra_get_index(heat, (y - int64(1)))), x, __pytra_ifexp((nv > int64(0)), nv, int64(0)))
            }
        }
        var frame []any = __pytra_as_list(__pytra_bytearray((w * h)))
        for yy := int64(0); yy < h; yy += 1 {
            var row_base int64 = (yy * w)
            for xx := int64(0); xx < w; xx += 1 {
                __pytra_set_index(frame, (row_base + xx), __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, yy)), xx)))
            }
        }
        frames = append(frames, __pytra_bytes(frame))
    }
    __pytra_save_gif(out_path, w, h, frames, fire_palette(), int64(4), int64(0))
    var elapsed float64 = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_09_fire_simulation()
}
