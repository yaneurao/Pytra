package main

import (
    "math"
)


// 11: Sample that outputs Lissajous-motion particles as a GIF.

func color_palette() []any {
    var p []any = __pytra_as_list([]any{})
    for i := int64(0); i < int64(256); i += 1 {
        var r int64 = i
        var g int64 = ((i * int64(3)) % int64(256))
        var b int64 = (int64(255) - i)
        p = append(__pytra_as_list(p), r)
        p = append(__pytra_as_list(p), g)
        p = append(__pytra_as_list(p), b)
    }
    return __pytra_as_list(__pytra_bytes(p))
}

func run_11_lissajous_particles() {
    var w int64 = int64(320)
    var h int64 = int64(240)
    var frames_n int64 = int64(360)
    var particles int64 = int64(48)
    var out_path string = __pytra_str("sample/out/11_lissajous_particles.gif")
    var start float64 = __pytra_perf_counter()
    var frames []any = __pytra_as_list([]any{})
    for t := int64(0); t < frames_n; t += 1 {
        var frame []any = __pytra_as_list(__pytra_bytearray((w * h)))
        var __hoisted_cast_1 float64 = __pytra_float(t)
        for p := int64(0); p < particles; p += 1 {
            var phase float64 = (float64(p) * float64(0.261799))
            var x int64 = __pytra_int(((float64(w) * float64(0.5)) + ((float64(w) * float64(0.38)) * math.Sin(((float64(0.11) * __hoisted_cast_1) + (phase * float64(2.0)))))))
            var y int64 = __pytra_int(((float64(h) * float64(0.5)) + ((float64(h) * float64(0.38)) * math.Sin(((float64(0.17) * __hoisted_cast_1) + (phase * float64(3.0)))))))
            var color int64 = (int64(30) + ((p * int64(9)) % int64(220)))
            for dy := (-int64(2)); dy < int64(3); dy += 1 {
                for dx := (-int64(2)); dx < int64(3); dx += 1 {
                    var xx int64 = (x + dx)
                    var yy int64 = (y + dy)
                    if ((xx >= int64(0)) && (xx < w) && (yy >= int64(0)) && (yy < h)) {
                        var d2 int64 = ((dx * dx) + (dy * dy))
                        if (d2 <= int64(4)) {
                            var idx int64 = ((yy * w) + xx)
                            var v int64 = (color - (d2 * int64(20)))
                            v = __pytra_max(int64(0), v)
                            if (__pytra_int(v) > __pytra_int(__pytra_get_index(frame, idx))) {
                                __pytra_set_index(frame, idx, v)
                            }
                        }
                    }
                }
            }
        }
        frames = append(__pytra_as_list(frames), __pytra_bytes(frame))
    }
    __pytra_save_gif(out_path, w, h, frames, color_palette(), int64(3), int64(0))
    var elapsed float64 = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_11_lissajous_particles()
}
