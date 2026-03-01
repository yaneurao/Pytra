package main


// 05: Sample that outputs a Mandelbrot zoom as an animated GIF.

func render_frame(width int64, height int64, center_x float64, center_y float64, scale float64, max_iter int64) []any {
    var frame []any = __pytra_as_list(__pytra_bytearray((width * height)))
    var __hoisted_cast_1 float64 = __pytra_float(max_iter)
    for y := int64(0); y < height; y += 1 {
        var row_base int64 = (y * width)
        var cy float64 = (center_y + ((float64(y) - (float64(height) * float64(0.5))) * scale))
        for x := int64(0); x < width; x += 1 {
            var cx float64 = (center_x + ((float64(x) - (float64(width) * float64(0.5))) * scale))
            var zx float64 = float64(0.0)
            var zy float64 = float64(0.0)
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
            __pytra_set_index(frame, (row_base + x), __pytra_int(((float64(255.0) * float64(i)) / __hoisted_cast_1)))
        }
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_05_mandelbrot_zoom() {
    var width int64 = int64(320)
    var height int64 = int64(240)
    var frame_count int64 = int64(48)
    var max_iter int64 = int64(110)
    var center_x float64 = (-float64(0.743643887037151))
    var center_y float64 = float64(0.13182590420533)
    var base_scale float64 = (float64(3.2) / float64(width))
    var zoom_per_frame float64 = float64(0.93)
    var out_path string = __pytra_str("sample/out/05_mandelbrot_zoom.gif")
    var start float64 = __pytra_perf_counter()
    var frames []any = __pytra_as_list([]any{})
    var scale float64 = base_scale
    for __loop_0 := int64(0); __loop_0 < frame_count; __loop_0 += 1 {
        frames = append(frames, render_frame(width, height, center_x, center_y, scale, max_iter))
        scale *= zoom_per_frame
    }
    __pytra_save_gif(out_path, width, height, frames, __pytra_grayscale_palette(), int64(5), int64(0))
    var elapsed float64 = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frame_count)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_05_mandelbrot_zoom()
}
