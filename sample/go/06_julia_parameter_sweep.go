package main

import (
    "math"
)


// 06: Sample that sweeps Julia-set parameters and outputs a GIF.

func julia_palette() []any {
    var palette []any = __pytra_as_list(__pytra_bytearray((int64(256) * int64(3))))
    __pytra_set_index(palette, int64(0), int64(0))
    __pytra_set_index(palette, int64(1), int64(0))
    __pytra_set_index(palette, int64(2), int64(0))
    for i := int64(1); i < int64(256); i += 1 {
        var t float64 = (float64((i - int64(1))) / float64(254.0))
        var r int64 = __pytra_int((float64(255.0) * ((((float64(9.0) * (float64(1.0) - t)) * t) * t) * t)))
        var g int64 = __pytra_int((float64(255.0) * ((((float64(15.0) * (float64(1.0) - t)) * (float64(1.0) - t)) * t) * t)))
        var b int64 = __pytra_int((float64(255.0) * ((((float64(8.5) * (float64(1.0) - t)) * (float64(1.0) - t)) * (float64(1.0) - t)) * t)))
        __pytra_set_index(palette, ((i * int64(3)) + int64(0)), r)
        __pytra_set_index(palette, ((i * int64(3)) + int64(1)), g)
        __pytra_set_index(palette, ((i * int64(3)) + int64(2)), b)
    }
    return __pytra_as_list(__pytra_bytes(palette))
}

func render_frame(width int64, height int64, cr float64, ci float64, max_iter int64, phase int64) []any {
    var frame []any = __pytra_as_list(__pytra_bytearray((width * height)))
    var __hoisted_cast_1 float64 = __pytra_float((height - int64(1)))
    var __hoisted_cast_2 float64 = __pytra_float((width - int64(1)))
    for y := int64(0); y < height; y += 1 {
        var row_base int64 = (y * width)
        var zy0 float64 = ((-float64(1.2)) + (float64(2.4) * (float64(y) / __hoisted_cast_1)))
        for x := int64(0); x < width; x += 1 {
            var zx float64 = ((-float64(1.8)) + (float64(3.6) * (float64(x) / __hoisted_cast_2)))
            var zy float64 = zy0
            var i int64 = int64(0)
            for (i < max_iter) {
                var zx2 float64 = (zx * zx)
                var zy2 float64 = (zy * zy)
                if ((zx2 + zy2) > float64(4.0)) {
                    break
                }
                zy = (((float64(2.0) * zx) * zy) + ci)
                zx = ((zx2 - zy2) + cr)
                i += int64(1)
            }
            if (i >= max_iter) {
                __pytra_set_index(frame, (row_base + x), int64(0))
            } else {
                var color_index int64 = (int64(1) + ((__pytra_int(((i * int64(224)) / max_iter)) + phase) % int64(255)))
                __pytra_set_index(frame, (row_base + x), color_index)
            }
        }
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_06_julia_parameter_sweep() {
    var width int64 = int64(320)
    var height int64 = int64(240)
    var frames_n int64 = int64(72)
    var max_iter int64 = int64(180)
    var out_path string = __pytra_str("sample/out/06_julia_parameter_sweep.gif")
    var start float64 = __pytra_perf_counter()
    var frames []any = __pytra_as_list([]any{})
    var center_cr float64 = (-float64(0.745))
    var center_ci float64 = float64(0.186)
    var radius_cr float64 = float64(0.12)
    var radius_ci float64 = float64(0.1)
    var start_offset int64 = int64(20)
    var phase_offset int64 = int64(180)
    var __hoisted_cast_3 float64 = __pytra_float(frames_n)
    for i := int64(0); i < frames_n; i += 1 {
        var t float64 = (float64(((i + start_offset) % frames_n)) / __hoisted_cast_3)
        var angle float64 = ((float64(2.0) * math.Pi) * t)
        var cr float64 = (center_cr + (radius_cr * math.Cos(__pytra_float(angle))))
        var ci float64 = (center_ci + (radius_ci * math.Sin(__pytra_float(angle))))
        var phase int64 = ((phase_offset + (i * int64(5))) % int64(255))
        frames = append(frames, render_frame(width, height, cr, ci, max_iter, phase))
    }
    __pytra_save_gif(out_path, width, height, frames, julia_palette(), int64(8), int64(0))
    var elapsed float64 = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_06_julia_parameter_sweep()
}
