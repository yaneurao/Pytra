package main

import (
    "math"
)

var _ = math.Pi


// 05: Sample that outputs a Mandelbrot zoom as an animated GIF.

func render_frame(width int64, height int64, center_x float64, center_y float64, scale float64, max_iter int64) []any {
    var frame []any = __pytra_as_list(__pytra_bytearray((__pytra_int(width) * __pytra_int(height))))
    var __hoisted_cast_1 float64 = __pytra_float(__pytra_float(max_iter))
    __step_0 := __pytra_int(int64(1))
    for y := __pytra_int(int64(0)); (__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height)); y += __step_0 {
        var row_base int64 = __pytra_int((__pytra_int(y) * __pytra_int(width)))
        var cy float64 = __pytra_float((__pytra_float(center_y) + __pytra_float((__pytra_float((__pytra_float(y) - __pytra_float((__pytra_float(height) * __pytra_float(float64(0.5)))))) * __pytra_float(scale)))))
        __step_1 := __pytra_int(int64(1))
        for x := __pytra_int(int64(0)); (__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width)); x += __step_1 {
            var cx float64 = __pytra_float((__pytra_float(center_x) + __pytra_float((__pytra_float((__pytra_float(x) - __pytra_float((__pytra_float(width) * __pytra_float(float64(0.5)))))) * __pytra_float(scale)))))
            var zx float64 = __pytra_float(float64(0.0))
            var zy float64 = __pytra_float(float64(0.0))
            var i int64 = __pytra_int(int64(0))
            for (__pytra_int(i) < __pytra_int(max_iter)) {
                var zx2 float64 = __pytra_float((__pytra_float(zx) * __pytra_float(zx)))
                var zy2 float64 = __pytra_float((__pytra_float(zy) * __pytra_float(zy)))
                if (__pytra_float((__pytra_float(zx2) + __pytra_float(zy2))) > __pytra_float(float64(4.0))) {
                    break
                }
                zy = __pytra_float((__pytra_float((__pytra_float((__pytra_float(float64(2.0)) * __pytra_float(zx))) * __pytra_float(zy))) + __pytra_float(cy)))
                zx = __pytra_float((__pytra_float((__pytra_float(zx2) - __pytra_float(zy2))) + __pytra_float(cx)))
                i += int64(1)
            }
            __pytra_set_index(frame, (__pytra_int(row_base) + __pytra_int(x)), __pytra_int((__pytra_float((__pytra_float(float64(255.0)) * __pytra_float(i))) / __pytra_float(__hoisted_cast_1))))
        }
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_05_mandelbrot_zoom() {
    var width int64 = __pytra_int(int64(320))
    var height int64 = __pytra_int(int64(240))
    var frame_count int64 = __pytra_int(int64(48))
    var max_iter int64 = __pytra_int(int64(110))
    var center_x float64 = __pytra_float((-float64(0.743643887037151)))
    var center_y float64 = __pytra_float(float64(0.13182590420533))
    var base_scale float64 = __pytra_float((__pytra_float(float64(3.2)) / __pytra_float(width)))
    var zoom_per_frame float64 = __pytra_float(float64(0.93))
    var out_path string = __pytra_str("sample/out/05_mandelbrot_zoom.gif")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var frames []any = __pytra_as_list([]any{})
    var scale float64 = __pytra_float(base_scale)
    __step_1 := __pytra_int(int64(1))
    for __loop_0 := __pytra_int(int64(0)); (__step_1 >= 0 && __loop_0 < __pytra_int(frame_count)) || (__step_1 < 0 && __loop_0 > __pytra_int(frame_count)); __loop_0 += __step_1 {
        frames = append(__pytra_as_list(frames), render_frame(width, height, center_x, center_y, scale, max_iter))
        scale *= zoom_per_frame
    }
    __pytra_noop(out_path, width, height, frames, []any{})
    var elapsed float64 = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frame_count)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_05_mandelbrot_zoom()
}
