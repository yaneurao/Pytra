package main


// 09: Sample that outputs a simple fire effect as a GIF.

func fire_palette() []any {
    var p []any = __pytra_as_list([]any{})
    __step_0 := __pytra_int(int64(1))
    for i := __pytra_int(int64(0)); (__step_0 >= 0 && i < __pytra_int(int64(256))) || (__step_0 < 0 && i > __pytra_int(int64(256))); i += __step_0 {
        var r int64 = __pytra_int(int64(0))
        var g int64 = __pytra_int(int64(0))
        var b int64 = __pytra_int(int64(0))
        if (__pytra_int(i) < __pytra_int(int64(85))) {
            r = __pytra_int((__pytra_int(i) * __pytra_int(int64(3))))
            g = __pytra_int(int64(0))
            b = __pytra_int(int64(0))
        } else {
            if (__pytra_int(i) < __pytra_int(int64(170))) {
                r = __pytra_int(int64(255))
                g = __pytra_int((__pytra_int((__pytra_int(i) - __pytra_int(int64(85)))) * __pytra_int(int64(3))))
                b = __pytra_int(int64(0))
            } else {
                r = __pytra_int(int64(255))
                g = __pytra_int(int64(255))
                b = __pytra_int((__pytra_int((__pytra_int(i) - __pytra_int(int64(170)))) * __pytra_int(int64(3))))
            }
        }
        p = append(__pytra_as_list(p), r)
        p = append(__pytra_as_list(p), g)
        p = append(__pytra_as_list(p), b)
    }
    return __pytra_as_list(__pytra_bytes(p))
}

func run_09_fire_simulation() {
    var w int64 = __pytra_int(int64(380))
    var h int64 = __pytra_int(int64(260))
    var steps int64 = __pytra_int(int64(420))
    var out_path string = __pytra_str("sample/out/09_fire_simulation.gif")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var heat []any = __pytra_as_list(func() []any { __out := []any{}; __step := __pytra_int(int64(1)); for __lc_i := __pytra_int(int64(0)); (__step >= 0 && __lc_i < __pytra_int(h)) || (__step < 0 && __lc_i > __pytra_int(h)); __lc_i += __step { __out = append(__out, __pytra_list_repeat(int64(0), w)) }; return __out }())
    var frames []any = __pytra_as_list([]any{})
    __step_0 := __pytra_int(int64(1))
    for t := __pytra_int(int64(0)); (__step_0 >= 0 && t < __pytra_int(steps)) || (__step_0 < 0 && t > __pytra_int(steps)); t += __step_0 {
        __step_1 := __pytra_int(int64(1))
        for x := __pytra_int(int64(0)); (__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w)); x += __step_1 {
            var val int64 = __pytra_int((__pytra_int(int64(170)) + __pytra_int((__pytra_int((__pytra_int((__pytra_int(x) * __pytra_int(int64(13)))) + __pytra_int((__pytra_int(t) * __pytra_int(int64(17)))))) % __pytra_int(int64(86))))))
            __pytra_set_index(__pytra_as_list(__pytra_get_index(heat, (__pytra_int(h) - __pytra_int(int64(1))))), x, val)
        }
        __step_2 := __pytra_int(int64(1))
        for y := __pytra_int(int64(1)); (__step_2 >= 0 && y < __pytra_int(h)) || (__step_2 < 0 && y > __pytra_int(h)); y += __step_2 {
            __step_3 := __pytra_int(int64(1))
            for x := __pytra_int(int64(0)); (__step_3 >= 0 && x < __pytra_int(w)) || (__step_3 < 0 && x > __pytra_int(w)); x += __step_3 {
                var a int64 = __pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)), x)))
                var b int64 = __pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)), (__pytra_int((__pytra_int((__pytra_int(x) - __pytra_int(int64(1)))) + __pytra_int(w))) % __pytra_int(w)))))
                var c int64 = __pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, y)), (__pytra_int((__pytra_int(x) + __pytra_int(int64(1)))) % __pytra_int(w)))))
                var d int64 = __pytra_int(__pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, (__pytra_int((__pytra_int(y) + __pytra_int(int64(1)))) % __pytra_int(h)))), x)))
                var v int64 = __pytra_int((__pytra_int(__pytra_int((__pytra_int((__pytra_int((__pytra_int(a) + __pytra_int(b))) + __pytra_int(c))) + __pytra_int(d))) / __pytra_int(int64(4)))))
                var cool int64 = __pytra_int((__pytra_int(int64(1)) + __pytra_int((__pytra_int((__pytra_int((__pytra_int(x) + __pytra_int(y))) + __pytra_int(t))) % __pytra_int(int64(3))))))
                var nv int64 = __pytra_int((__pytra_int(v) - __pytra_int(cool)))
                __pytra_set_index(__pytra_as_list(__pytra_get_index(heat, (__pytra_int(y) - __pytra_int(int64(1))))), x, __pytra_ifexp((__pytra_int(nv) > __pytra_int(int64(0))), nv, int64(0)))
            }
        }
        var frame []any = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
        __step_4 := __pytra_int(int64(1))
        for yy := __pytra_int(int64(0)); (__step_4 >= 0 && yy < __pytra_int(h)) || (__step_4 < 0 && yy > __pytra_int(h)); yy += __step_4 {
            var row_base int64 = __pytra_int((__pytra_int(yy) * __pytra_int(w)))
            __step_5 := __pytra_int(int64(1))
            for xx := __pytra_int(int64(0)); (__step_5 >= 0 && xx < __pytra_int(w)) || (__step_5 < 0 && xx > __pytra_int(w)); xx += __step_5 {
                __pytra_set_index(frame, (__pytra_int(row_base) + __pytra_int(xx)), __pytra_int(__pytra_get_index(__pytra_as_list(__pytra_get_index(heat, yy)), xx)))
            }
        }
        frames = append(__pytra_as_list(frames), __pytra_bytes(frame))
    }
    __pytra_noop(out_path, w, h, frames, fire_palette())
    var elapsed float64 = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_09_fire_simulation()
}
