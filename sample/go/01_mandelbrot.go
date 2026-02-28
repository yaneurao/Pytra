package main

import (
    "math"
)

var _ = math.Pi


// 01: Sample that outputs the Mandelbrot set as a PNG image.
// Syntax is kept straightforward with future transpilation in mind.

func escape_count(cx float64, cy float64, max_iter int64) int64 {
    var x float64 = __pytra_float(float64(0.0))
    var y float64 = __pytra_float(float64(0.0))
    __step_0 := __pytra_int(int64(1))
    for i := __pytra_int(int64(0)); (__step_0 >= 0 && i < __pytra_int(max_iter)) || (__step_0 < 0 && i > __pytra_int(max_iter)); i += __step_0 {
        var x2 float64 = __pytra_float((__pytra_float(x) * __pytra_float(x)))
        var y2 float64 = __pytra_float((__pytra_float(y) * __pytra_float(y)))
        if (__pytra_float((__pytra_float(x2) + __pytra_float(y2))) > __pytra_float(float64(4.0))) {
            return __pytra_int(i)
        }
        y = __pytra_float((__pytra_float((__pytra_float((__pytra_float(float64(2.0)) * __pytra_float(x))) * __pytra_float(y))) + __pytra_float(cy)))
        x = __pytra_float((__pytra_float((__pytra_float(x2) - __pytra_float(y2))) + __pytra_float(cx)))
    }
    return __pytra_int(max_iter)
}

func color_map(iter_count int64, max_iter int64) []any {
    if (__pytra_int(iter_count) >= __pytra_int(max_iter)) {
        return __pytra_as_list([]any{int64(0), int64(0), int64(0)})
    }
    var t float64 = __pytra_float((__pytra_float(iter_count) / __pytra_float(max_iter)))
    var r int64 = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float((__pytra_float(t) * __pytra_float(t))))))
    var g int64 = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float(t))))
    var b int64 = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float((__pytra_float(float64(1.0)) - __pytra_float(t))))))
    return __pytra_as_list([]any{r, g, b})
}

func render_mandelbrot(width int64, height int64, max_iter int64, x_min float64, x_max float64, y_min float64, y_max float64) []any {
    var pixels []any = __pytra_as_list([]any{})
    var __hoisted_cast_1 float64 = __pytra_float(__pytra_float((__pytra_int(height) - __pytra_int(int64(1)))))
    var __hoisted_cast_2 float64 = __pytra_float(__pytra_float((__pytra_int(width) - __pytra_int(int64(1)))))
    var __hoisted_cast_3 float64 = __pytra_float(__pytra_float(max_iter))
    __step_0 := __pytra_int(int64(1))
    for y := __pytra_int(int64(0)); (__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height)); y += __step_0 {
        var py float64 = __pytra_float((__pytra_float(y_min) + __pytra_float((__pytra_float((__pytra_float(y_max) - __pytra_float(y_min))) * __pytra_float((__pytra_float(y) / __pytra_float(__hoisted_cast_1)))))))
        __step_1 := __pytra_int(int64(1))
        for x := __pytra_int(int64(0)); (__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width)); x += __step_1 {
            var px float64 = __pytra_float((__pytra_float(x_min) + __pytra_float((__pytra_float((__pytra_float(x_max) - __pytra_float(x_min))) * __pytra_float((__pytra_float(x) / __pytra_float(__hoisted_cast_2)))))))
            var it int64 = __pytra_int(escape_count(px, py, max_iter))
            var r int64 = 0
            var g int64 = 0
            var b int64 = 0
            if (__pytra_int(it) >= __pytra_int(max_iter)) {
                r = __pytra_int(int64(0))
                g = __pytra_int(int64(0))
                b = __pytra_int(int64(0))
            } else {
                var t float64 = __pytra_float((__pytra_float(it) / __pytra_float(__hoisted_cast_3)))
                r = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float((__pytra_float(t) * __pytra_float(t))))))
                g = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float(t))))
                b = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float((__pytra_float(float64(1.0)) - __pytra_float(t))))))
            }
            pixels = append(__pytra_as_list(pixels), r)
            pixels = append(__pytra_as_list(pixels), g)
            pixels = append(__pytra_as_list(pixels), b)
        }
    }
    return __pytra_as_list(pixels)
}

func run_mandelbrot() {
    var width int64 = __pytra_int(int64(1600))
    var height int64 = __pytra_int(int64(1200))
    var max_iter int64 = __pytra_int(int64(1000))
    var out_path string = __pytra_str("sample/out/01_mandelbrot.png")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var pixels []any = __pytra_as_list(render_mandelbrot(width, height, max_iter, (-float64(2.2)), float64(1.0), (-float64(1.2)), float64(1.2)))
    __pytra_noop(out_path, width, height, pixels)
    var elapsed float64 = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_mandelbrot()
}
