package main

import (
    "math"
)

var _ = math.Pi


// 06: Sample that sweeps Julia-set parameters and outputs a GIF.

func julia_palette() []any {
    var palette []any = __pytra_as_list(__pytra_bytearray((__pytra_int(int64(256)) * __pytra_int(int64(3)))))
    __pytra_set_index(palette, int64(0), int64(0))
    __pytra_set_index(palette, int64(1), int64(0))
    __pytra_set_index(palette, int64(2), int64(0))
    __step_0 := __pytra_int(int64(1))
    for i := __pytra_int(int64(1)); (__step_0 >= 0 && i < __pytra_int(int64(256))) || (__step_0 < 0 && i > __pytra_int(int64(256))); i += __step_0 {
        var t float64 = __pytra_float((__pytra_float((__pytra_int(i) - __pytra_int(int64(1)))) / __pytra_float(float64(254.0))))
        var r int64 = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(float64(9.0)) * __pytra_float((__pytra_float(float64(1.0)) - __pytra_float(t))))) * __pytra_float(t))) * __pytra_float(t))) * __pytra_float(t))))))
        var g int64 = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(float64(15.0)) * __pytra_float((__pytra_float(float64(1.0)) - __pytra_float(t))))) * __pytra_float((__pytra_float(float64(1.0)) - __pytra_float(t))))) * __pytra_float(t))) * __pytra_float(t))))))
        var b int64 = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(float64(8.5)) * __pytra_float((__pytra_float(float64(1.0)) - __pytra_float(t))))) * __pytra_float((__pytra_float(float64(1.0)) - __pytra_float(t))))) * __pytra_float((__pytra_float(float64(1.0)) - __pytra_float(t))))) * __pytra_float(t))))))
        __pytra_set_index(palette, (__pytra_int((__pytra_int(i) * __pytra_int(int64(3)))) + __pytra_int(int64(0))), r)
        __pytra_set_index(palette, (__pytra_int((__pytra_int(i) * __pytra_int(int64(3)))) + __pytra_int(int64(1))), g)
        __pytra_set_index(palette, (__pytra_int((__pytra_int(i) * __pytra_int(int64(3)))) + __pytra_int(int64(2))), b)
    }
    return __pytra_as_list(__pytra_bytes(palette))
}

func render_frame(width int64, height int64, cr float64, ci float64, max_iter int64, phase int64) []any {
    var frame []any = __pytra_as_list(__pytra_bytearray((__pytra_int(width) * __pytra_int(height))))
    var __hoisted_cast_1 float64 = __pytra_float(__pytra_float((__pytra_int(height) - __pytra_int(int64(1)))))
    var __hoisted_cast_2 float64 = __pytra_float(__pytra_float((__pytra_int(width) - __pytra_int(int64(1)))))
    __step_0 := __pytra_int(int64(1))
    for y := __pytra_int(int64(0)); (__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height)); y += __step_0 {
        var row_base int64 = __pytra_int((__pytra_int(y) * __pytra_int(width)))
        var zy0 float64 = __pytra_float((__pytra_float((-float64(1.2))) + __pytra_float((__pytra_float(float64(2.4)) * __pytra_float((__pytra_float(y) / __pytra_float(__hoisted_cast_1)))))))
        __step_1 := __pytra_int(int64(1))
        for x := __pytra_int(int64(0)); (__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width)); x += __step_1 {
            var zx float64 = __pytra_float((__pytra_float((-float64(1.8))) + __pytra_float((__pytra_float(float64(3.6)) * __pytra_float((__pytra_float(x) / __pytra_float(__hoisted_cast_2)))))))
            var zy float64 = __pytra_float(zy0)
            var i int64 = __pytra_int(int64(0))
            for (__pytra_int(i) < __pytra_int(max_iter)) {
                var zx2 float64 = __pytra_float((__pytra_float(zx) * __pytra_float(zx)))
                var zy2 float64 = __pytra_float((__pytra_float(zy) * __pytra_float(zy)))
                if (__pytra_float((__pytra_float(zx2) + __pytra_float(zy2))) > __pytra_float(float64(4.0))) {
                    break
                }
                zy = __pytra_float((__pytra_float((__pytra_float((__pytra_float(float64(2.0)) * __pytra_float(zx))) * __pytra_float(zy))) + __pytra_float(ci)))
                zx = __pytra_float((__pytra_float((__pytra_float(zx2) - __pytra_float(zy2))) + __pytra_float(cr)))
                i += int64(1)
            }
            if (__pytra_int(i) >= __pytra_int(max_iter)) {
                __pytra_set_index(frame, (__pytra_int(row_base) + __pytra_int(x)), int64(0))
            } else {
                var color_index int64 = __pytra_int((__pytra_int(int64(1)) + __pytra_int((__pytra_int((__pytra_int((__pytra_int(__pytra_int((__pytra_int(i) * __pytra_int(int64(224)))) / __pytra_int(max_iter)))) + __pytra_int(phase))) % __pytra_int(int64(255))))))
                __pytra_set_index(frame, (__pytra_int(row_base) + __pytra_int(x)), color_index)
            }
        }
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_06_julia_parameter_sweep() {
    var width int64 = __pytra_int(int64(320))
    var height int64 = __pytra_int(int64(240))
    var frames_n int64 = __pytra_int(int64(72))
    var max_iter int64 = __pytra_int(int64(180))
    var out_path string = __pytra_str("sample/out/06_julia_parameter_sweep.gif")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var frames []any = __pytra_as_list([]any{})
    var center_cr float64 = __pytra_float((-float64(0.745)))
    var center_ci float64 = __pytra_float(float64(0.186))
    var radius_cr float64 = __pytra_float(float64(0.12))
    var radius_ci float64 = __pytra_float(float64(0.1))
    var start_offset int64 = __pytra_int(int64(20))
    var phase_offset int64 = __pytra_int(int64(180))
    var __hoisted_cast_3 float64 = __pytra_float(__pytra_float(frames_n))
    __step_0 := __pytra_int(int64(1))
    for i := __pytra_int(int64(0)); (__step_0 >= 0 && i < __pytra_int(frames_n)) || (__step_0 < 0 && i > __pytra_int(frames_n)); i += __step_0 {
        var t float64 = __pytra_float((__pytra_float((__pytra_int((__pytra_int(i) + __pytra_int(start_offset))) % __pytra_int(frames_n))) / __pytra_float(__hoisted_cast_3)))
        var angle float64 = __pytra_float(((float64(2.0) * math.Pi) * t))
        var cr float64 = __pytra_float((center_cr + (radius_cr * math.Cos(__pytra_float(angle)))))
        var ci float64 = __pytra_float((center_ci + (radius_ci * math.Sin(__pytra_float(angle)))))
        var phase int64 = __pytra_int((__pytra_int((__pytra_int(phase_offset) + __pytra_int((__pytra_int(i) * __pytra_int(int64(5)))))) % __pytra_int(int64(255))))
        frames = append(__pytra_as_list(frames), render_frame(width, height, cr, ci, max_iter, phase))
    }
    __pytra_noop(out_path, width, height, frames, julia_palette())
    var elapsed float64 = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_06_julia_parameter_sweep()
}
