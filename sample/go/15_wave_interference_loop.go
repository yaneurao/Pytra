package main

import (
    "math"
)


// 15: Sample that renders wave interference animation and writes a GIF.

func run_15_wave_interference_loop() {
    var w int64 = int64(320)
    var h int64 = int64(240)
    var frames_n int64 = int64(96)
    var out_path string = __pytra_str("sample/out/15_wave_interference_loop.gif")
    var start float64 = __pytra_perf_counter()
    var frames []any = __pytra_as_list([]any{})
    for t := int64(0); t < frames_n; t += 1 {
        var frame []any = __pytra_as_list(__pytra_bytearray((w * h)))
        var phase float64 = (float64(t) * float64(0.12))
        for y := int64(0); y < h; y += 1 {
            var row_base int64 = (y * w)
            for x := int64(0); x < w; x += 1 {
                var dx int64 = (x - int64(160))
                var dy int64 = (y - int64(120))
                var v float64 = (((math.Sin(((float64(x) + (float64(t) * float64(1.5))) * float64(0.045))) + math.Sin(((float64(y) - (float64(t) * float64(1.2))) * float64(0.04)))) + math.Sin(((float64((x + y)) * float64(0.02)) + phase))) + math.Sin(__pytra_float(((math.Sqrt(float64(((dx * dx) + (dy * dy)))) * float64(0.08)) - (phase * float64(1.3))))))
                var c int64 = __pytra_int(((v + float64(4.0)) * (float64(255.0) / float64(8.0))))
                if (c < int64(0)) {
                    c = int64(0)
                }
                if (c > int64(255)) {
                    c = int64(255)
                }
                __pytra_set_index(frame, (row_base + x), c)
            }
        }
        frames = append(frames, __pytra_bytes(frame))
    }
    __pytra_save_gif(out_path, w, h, frames, __pytra_grayscale_palette(), int64(4), int64(0))
    var elapsed float64 = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_15_wave_interference_loop()
}
