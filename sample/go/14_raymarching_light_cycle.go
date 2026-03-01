package main

import (
    "math"
)


// 14: Sample that outputs a moving-light scene in a simple raymarching style as a GIF.

func palette() []any {
    var p []any = __pytra_as_list([]any{})
    for i := int64(0); i < int64(256); i += 1 {
        var r int64 = __pytra_min(int64(255), __pytra_int((float64(int64(20)) + (float64(i) * float64(0.9)))))
        var g int64 = __pytra_min(int64(255), __pytra_int((float64(int64(10)) + (float64(i) * float64(0.7)))))
        var b int64 = __pytra_min(int64(255), (int64(30) + i))
        p = append(__pytra_as_list(p), r)
        p = append(__pytra_as_list(p), g)
        p = append(__pytra_as_list(p), b)
    }
    return __pytra_as_list(__pytra_bytes(p))
}

func scene(x float64, y float64, light_x float64, light_y float64) int64 {
    var x1 float64 = (x + float64(0.45))
    var y1 float64 = (y + float64(0.2))
    var x2 float64 = (x - float64(0.35))
    var y2 float64 = (y - float64(0.15))
    var r1 float64 = math.Sqrt(((x1 * x1) + (y1 * y1)))
    var r2 float64 = math.Sqrt(((x2 * x2) + (y2 * y2)))
    var blob float64 = (math.Exp(__pytra_float((((-float64(7.0)) * r1) * r1))) + math.Exp(__pytra_float((((-float64(8.0)) * r2) * r2))))
    var lx float64 = (x - light_x)
    var ly float64 = (y - light_y)
    var l float64 = math.Sqrt(((lx * lx) + (ly * ly)))
    var lit float64 = (float64(1.0) / __pytra_float((float64(1.0) + ((float64(3.5) * l) * l))))
    var v int64 = __pytra_int((((float64(255.0) * blob) * lit) * float64(5.0)))
    return __pytra_min(int64(255), __pytra_max(int64(0), v))
}

func run_14_raymarching_light_cycle() {
    var w int64 = int64(320)
    var h int64 = int64(240)
    var frames_n int64 = int64(84)
    var out_path string = __pytra_str("sample/out/14_raymarching_light_cycle.gif")
    var start float64 = __pytra_perf_counter()
    var frames []any = __pytra_as_list([]any{})
    var __hoisted_cast_1 float64 = __pytra_float(frames_n)
    var __hoisted_cast_2 float64 = __pytra_float((h - int64(1)))
    var __hoisted_cast_3 float64 = __pytra_float((w - int64(1)))
    for t := int64(0); t < frames_n; t += 1 {
        var frame []any = __pytra_as_list(__pytra_bytearray((w * h)))
        var a float64 = (((float64(t) / __hoisted_cast_1) * math.Pi) * float64(2.0))
        var light_x float64 = (float64(0.75) * math.Cos(__pytra_float(a)))
        var light_y float64 = (float64(0.55) * math.Sin(__pytra_float((a * float64(1.2)))))
        for y := int64(0); y < h; y += 1 {
            var row_base int64 = (y * w)
            var py float64 = (((float64(y) / __hoisted_cast_2) * float64(2.0)) - float64(1.0))
            for x := int64(0); x < w; x += 1 {
                var px float64 = (((float64(x) / __hoisted_cast_3) * float64(2.0)) - float64(1.0))
                __pytra_set_index(frame, (row_base + x), scene(px, py, light_x, light_y))
            }
        }
        frames = append(__pytra_as_list(frames), __pytra_bytes(frame))
    }
    __pytra_save_gif(out_path, w, h, frames, palette(), int64(3), int64(0))
    var elapsed float64 = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_14_raymarching_light_cycle()
}
