package main

import (
    "math"
)

var _ = math.Pi


// 15: Sample that renders wave interference animation and writes a GIF.

func run_15_wave_interference_loop() {
    var w int64 = __pytra_int(int64(320))
    var h int64 = __pytra_int(int64(240))
    var frames_n int64 = __pytra_int(int64(96))
    var out_path string = __pytra_str("sample/out/15_wave_interference_loop.gif")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var frames []any = __pytra_as_list([]any{})
    __step_0 := __pytra_int(int64(1))
    for t := __pytra_int(int64(0)); (__step_0 >= 0 && t < __pytra_int(frames_n)) || (__step_0 < 0 && t > __pytra_int(frames_n)); t += __step_0 {
        var frame []any = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
        var phase float64 = __pytra_float((__pytra_float(t) * __pytra_float(float64(0.12))))
        __step_1 := __pytra_int(int64(1))
        for y := __pytra_int(int64(0)); (__step_1 >= 0 && y < __pytra_int(h)) || (__step_1 < 0 && y > __pytra_int(h)); y += __step_1 {
            var row_base int64 = __pytra_int((__pytra_int(y) * __pytra_int(w)))
            __step_2 := __pytra_int(int64(1))
            for x := __pytra_int(int64(0)); (__step_2 >= 0 && x < __pytra_int(w)) || (__step_2 < 0 && x > __pytra_int(w)); x += __step_2 {
                var dx int64 = __pytra_int((__pytra_int(x) - __pytra_int(int64(160))))
                var dy int64 = __pytra_int((__pytra_int(y) - __pytra_int(int64(120))))
                var v float64 = __pytra_float((((math.Sin(__pytra_float((__pytra_float((__pytra_float(x) + __pytra_float((__pytra_float(t) * __pytra_float(float64(1.5)))))) * __pytra_float(float64(0.045))))) + math.Sin(__pytra_float((__pytra_float((__pytra_float(y) - __pytra_float((__pytra_float(t) * __pytra_float(float64(1.2)))))) * __pytra_float(float64(0.04)))))) + math.Sin(__pytra_float((__pytra_float((__pytra_float((__pytra_int(x) + __pytra_int(y))) * __pytra_float(float64(0.02)))) + __pytra_float(phase))))) + math.Sin(__pytra_float(((math.Sqrt(__pytra_float((__pytra_int((__pytra_int(dx) * __pytra_int(dx))) + __pytra_int((__pytra_int(dy) * __pytra_int(dy)))))) * float64(0.08)) - (__pytra_float(phase) * __pytra_float(float64(1.3))))))))
                var c int64 = __pytra_int(__pytra_int(((v + float64(4.0)) * (__pytra_float(float64(255.0)) / __pytra_float(float64(8.0))))))
                if (__pytra_int(c) < __pytra_int(int64(0))) {
                    c = __pytra_int(int64(0))
                }
                if (__pytra_int(c) > __pytra_int(int64(255))) {
                    c = __pytra_int(int64(255))
                }
                __pytra_set_index(frame, (__pytra_int(row_base) + __pytra_int(x)), c)
            }
        }
        frames = append(__pytra_as_list(frames), __pytra_bytes(frame))
    }
    __pytra_noop(out_path, w, h, frames, []any{})
    var elapsed float64 = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_15_wave_interference_loop()
}
