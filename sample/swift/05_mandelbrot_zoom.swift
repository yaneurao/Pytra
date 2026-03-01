import Foundation


// 05: Sample that outputs a Mandelbrot zoom as an animated GIF.

func render_frame(width: Int64, height: Int64, center_x: Double, center_y: Double, scale: Double, max_iter: Int64) -> [Any] {
    var frame: [Any] = __pytra_as_list(__pytra_bytearray((width * height)))
    var __hoisted_cast_1: Double = __pytra_float(max_iter)
    var y = __pytra_int(Int64(0))
    while (y < __pytra_int(height)) {
        var row_base: Int64 = (y * width)
        var cy: Double = (center_y + ((__pytra_float(y) - (__pytra_float(height) * Double(0.5))) * scale))
        var x = __pytra_int(Int64(0))
        while (x < __pytra_int(width)) {
            var cx: Double = (center_x + ((__pytra_float(x) - (__pytra_float(width) * Double(0.5))) * scale))
            var zx: Double = Double(0.0)
            var zy: Double = Double(0.0)
            var i: Int64 = Int64(0)
            while (__pytra_int(i) < __pytra_int(max_iter)) {
                var zx2: Double = (zx * zx)
                var zy2: Double = (zy * zy)
                if (__pytra_float(zx2 + zy2) > __pytra_float(Double(4.0))) {
                    break
                }
                zy = (((Double(2.0) * zx) * zy) + cy)
                zx = ((zx2 - zy2) + cx)
                i += Int64(1)
            }
            __pytra_setIndex(frame, (row_base + x), __pytra_int((Double(255.0) * __pytra_float(i)) / __hoisted_cast_1))
            x += 1
        }
        y += 1
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_05_mandelbrot_zoom() {
    var width: Int64 = Int64(320)
    var height: Int64 = Int64(240)
    var frame_count: Int64 = Int64(48)
    var max_iter: Int64 = Int64(110)
    var center_x: Double = __pytra_float(-Double(0.743643887037151))
    var center_y: Double = Double(0.13182590420533)
    var base_scale: Double = (Double(3.2) / __pytra_float(width))
    var zoom_per_frame: Double = Double(0.93)
    var out_path: String = "sample/out/05_mandelbrot_zoom.gif"
    var start: Double = __pytra_perf_counter()
    var frames: [Any] = __pytra_as_list([])
    var scale: Double = base_scale
    var __loop_0 = __pytra_int(Int64(0))
    while (__loop_0 < __pytra_int(frame_count)) {
        frames.append(render_frame(width, height, center_x, center_y, scale, max_iter))
        scale *= zoom_per_frame
        __loop_0 += 1
    }
    __pytra_noop(out_path, width, height, frames, [])
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frame_count)
    __pytra_print("elapsed_sec:", elapsed)
}

@main
struct Main {
    static func main() {
        run_05_mandelbrot_zoom()
    }
}
