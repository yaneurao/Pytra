package main


// 03: Sample that outputs a Julia set as a PNG image.
// Implemented with simple loop-centric logic for transpilation compatibility.

func render_julia(width int64, height int64, max_iter int64, cx float64, cy float64) []any {
    var pixels []any = __pytra_as_list([]any{})
    var __hoisted_cast_1 float64 = __pytra_float((height - int64(1)))
    var __hoisted_cast_2 float64 = __pytra_float((width - int64(1)))
    var __hoisted_cast_3 float64 = __pytra_float(max_iter)
    for y := int64(0); y < height; y += 1 {
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
                zy = (((float64(2.0) * zx) * zy) + cy)
                zx = ((zx2 - zy2) + cx)
                i += int64(1)
            }
            var r int64 = int64(0)
            var g int64 = int64(0)
            var b int64 = int64(0)
            if (i >= max_iter) {
                r = int64(0)
                g = int64(0)
                b = int64(0)
            } else {
                var t float64 = (float64(i) / __hoisted_cast_3)
                r = __pytra_int((float64(255.0) * (float64(0.2) + (float64(0.8) * t))))
                g = __pytra_int((float64(255.0) * (float64(0.1) + (float64(0.9) * (t * t)))))
                b = __pytra_int((float64(255.0) * (float64(1.0) - t)))
            }
            pixels = append(__pytra_as_list(pixels), r)
            pixels = append(__pytra_as_list(pixels), g)
            pixels = append(__pytra_as_list(pixels), b)
        }
    }
    return __pytra_as_list(pixels)
}

func run_julia() {
    var width int64 = int64(3840)
    var height int64 = int64(2160)
    var max_iter int64 = int64(20000)
    var out_path string = __pytra_str("sample/out/03_julia_set.png")
    var start float64 = __pytra_perf_counter()
    var pixels []any = __pytra_as_list(render_julia(width, height, max_iter, (-float64(0.8)), float64(0.156)))
    __pytra_write_rgb_png(out_path, width, height, pixels)
    var elapsed float64 = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_julia()
}
