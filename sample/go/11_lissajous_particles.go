package main

import (
    "math"
)


// 11: Sample that outputs Lissajous-motion particles as a GIF.

func color_palette() []any {
    var p []any = __pytra_as_list([]any{})
    __step_0 := __pytra_int(int64(1))
    for i := __pytra_int(int64(0)); (__step_0 >= 0 && i < __pytra_int(int64(256))) || (__step_0 < 0 && i > __pytra_int(int64(256))); i += __step_0 {
        var r int64 = __pytra_int(i)
        var g int64 = __pytra_int((__pytra_int((__pytra_int(i) * __pytra_int(int64(3)))) % __pytra_int(int64(256))))
        var b int64 = __pytra_int((__pytra_int(int64(255)) - __pytra_int(i)))
        p = append(__pytra_as_list(p), r)
        p = append(__pytra_as_list(p), g)
        p = append(__pytra_as_list(p), b)
    }
    return __pytra_as_list(__pytra_bytes(p))
}

func run_11_lissajous_particles() {
    var w int64 = __pytra_int(int64(320))
    var h int64 = __pytra_int(int64(240))
    var frames_n int64 = __pytra_int(int64(360))
    var particles int64 = __pytra_int(int64(48))
    var out_path string = __pytra_str("sample/out/11_lissajous_particles.gif")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var frames []any = __pytra_as_list([]any{})
    __step_0 := __pytra_int(int64(1))
    for t := __pytra_int(int64(0)); (__step_0 >= 0 && t < __pytra_int(frames_n)) || (__step_0 < 0 && t > __pytra_int(frames_n)); t += __step_0 {
        var frame []any = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
        var __hoisted_cast_1 float64 = __pytra_float(__pytra_float(t))
        __step_1 := __pytra_int(int64(1))
        for p := __pytra_int(int64(0)); (__step_1 >= 0 && p < __pytra_int(particles)) || (__step_1 < 0 && p > __pytra_int(particles)); p += __step_1 {
            var phase float64 = __pytra_float((__pytra_float(p) * __pytra_float(float64(0.261799))))
            var x int64 = __pytra_int(__pytra_int(((__pytra_float(w) * __pytra_float(float64(0.5))) + ((__pytra_float(w) * __pytra_float(float64(0.38))) * math.Sin(__pytra_float((__pytra_float((__pytra_float(float64(0.11)) * __pytra_float(__hoisted_cast_1))) + __pytra_float((__pytra_float(phase) * __pytra_float(float64(2.0)))))))))))
            var y int64 = __pytra_int(__pytra_int(((__pytra_float(h) * __pytra_float(float64(0.5))) + ((__pytra_float(h) * __pytra_float(float64(0.38))) * math.Sin(__pytra_float((__pytra_float((__pytra_float(float64(0.17)) * __pytra_float(__hoisted_cast_1))) + __pytra_float((__pytra_float(phase) * __pytra_float(float64(3.0)))))))))))
            var color int64 = __pytra_int((__pytra_int(int64(30)) + __pytra_int((__pytra_int((__pytra_int(p) * __pytra_int(int64(9)))) % __pytra_int(int64(220))))))
            __step_2 := __pytra_int(int64(1))
            for dy := __pytra_int((-int64(2))); (__step_2 >= 0 && dy < __pytra_int(int64(3))) || (__step_2 < 0 && dy > __pytra_int(int64(3))); dy += __step_2 {
                __step_3 := __pytra_int(int64(1))
                for dx := __pytra_int((-int64(2))); (__step_3 >= 0 && dx < __pytra_int(int64(3))) || (__step_3 < 0 && dx > __pytra_int(int64(3))); dx += __step_3 {
                    var xx int64 = __pytra_int((__pytra_int(x) + __pytra_int(dx)))
                    var yy int64 = __pytra_int((__pytra_int(y) + __pytra_int(dy)))
                    if ((__pytra_int(xx) >= __pytra_int(int64(0))) && (__pytra_int(xx) < __pytra_int(w)) && (__pytra_int(yy) >= __pytra_int(int64(0))) && (__pytra_int(yy) < __pytra_int(h))) {
                        var d2 int64 = __pytra_int((__pytra_int((__pytra_int(dx) * __pytra_int(dx))) + __pytra_int((__pytra_int(dy) * __pytra_int(dy)))))
                        if (__pytra_int(d2) <= __pytra_int(int64(4))) {
                            var idx int64 = __pytra_int((__pytra_int((__pytra_int(yy) * __pytra_int(w))) + __pytra_int(xx)))
                            var v int64 = __pytra_int((__pytra_int(color) - __pytra_int((__pytra_int(d2) * __pytra_int(int64(20))))))
                            v = __pytra_int(__pytra_max(int64(0), v))
                            if (__pytra_int(v) > __pytra_int(__pytra_int(__pytra_get_index(frame, idx)))) {
                                __pytra_set_index(frame, idx, v)
                            }
                        }
                    }
                }
            }
        }
        frames = append(__pytra_as_list(frames), __pytra_bytes(frame))
    }
    __pytra_noop(out_path, w, h, frames, color_palette())
    var elapsed float64 = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_11_lissajous_particles()
}
