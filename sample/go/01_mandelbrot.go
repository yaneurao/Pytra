package main


// 01: Sample that outputs the Mandelbrot set as a PNG image.
// Syntax is kept straightforward with future transpilation in mind.

func escape_count(cx float64, cy float64, max_iter int64) int64 {
    var x float64 = float64(0.0)
    var y float64 = float64(0.0)
    for i := int64(0); i < max_iter; i += 1 {
        var x2 float64 = (x * x)
        var y2 float64 = (y * y)
        if ((x2 + y2) > float64(4.0)) {
            return i
        }
        y = (((float64(2.0) * x) * y) + cy)
        x = ((x2 - y2) + cx)
    }
    return max_iter
}

func color_map(iter_count int64, max_iter int64) []any {
    if (iter_count >= max_iter) {
        return __pytra_as_list([]any{int64(0), int64(0), int64(0)})
    }
    var t float64 = (float64(iter_count) / float64(max_iter))
    var r int64 = __pytra_int((float64(255.0) * (t * t)))
    var g int64 = __pytra_int((float64(255.0) * t))
    var b int64 = __pytra_int((float64(255.0) * (float64(1.0) - t)))
    return __pytra_as_list([]any{r, g, b})
}

func render_mandelbrot(width int64, height int64, max_iter int64, x_min float64, x_max float64, y_min float64, y_max float64) []any {
    var pixels []any = __pytra_as_list([]any{})
    var __hoisted_cast_1 float64 = __pytra_float((height - int64(1)))
    var __hoisted_cast_2 float64 = __pytra_float((width - int64(1)))
    var __hoisted_cast_3 float64 = __pytra_float(max_iter)
    for y := int64(0); y < height; y += 1 {
        var py float64 = (y_min + ((y_max - y_min) * (float64(y) / __hoisted_cast_1)))
        for x := int64(0); x < width; x += 1 {
            var px float64 = (x_min + ((x_max - x_min) * (float64(x) / __hoisted_cast_2)))
            var it int64 = escape_count(px, py, max_iter)
            var r int64 = 0
            var g int64 = 0
            var b int64 = 0
            if (it >= max_iter) {
                r = int64(0)
                g = int64(0)
                b = int64(0)
            } else {
                var t float64 = (float64(it) / __hoisted_cast_3)
                r = __pytra_int((float64(255.0) * (t * t)))
                g = __pytra_int((float64(255.0) * t))
                b = __pytra_int((float64(255.0) * (float64(1.0) - t)))
            }
            pixels = append(pixels, r)
            pixels = append(pixels, g)
            pixels = append(pixels, b)
        }
    }
    return __pytra_as_list(pixels)
}

func run_mandelbrot() {
    var width int64 = int64(1600)
    var height int64 = int64(1200)
    var max_iter int64 = int64(1000)
    var out_path string = __pytra_str("sample/out/01_mandelbrot.png")
    var start float64 = __pytra_perf_counter()
    var pixels []any = __pytra_as_list(render_mandelbrot(width, height, max_iter, (-float64(2.2)), float64(1.0), (-float64(1.2)), float64(1.2)))
    __pytra_write_rgb_png(out_path, width, height, pixels)
    var elapsed float64 = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_mandelbrot()
}
