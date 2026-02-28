import Foundation


// 05: Sample that outputs a Mandelbrot zoom as an animated GIF.

func render_frame(width: Int64, height: Int64, center_x: Double, center_y: Double, scale: Double, max_iter: Int64) -> [Any] {
    var frame: [Any] = __pytra_as_list(__pytra_bytearray((__pytra_int(width) * __pytra_int(height))))
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float(max_iter))
    let __step_0 = __pytra_int(Int64(1))
    var y = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height))) {
        var row_base: Int64 = __pytra_int((__pytra_int(y) * __pytra_int(width)))
        var cy: Double = __pytra_float((__pytra_float(center_y) + __pytra_float((__pytra_float((__pytra_float(y) - __pytra_float((__pytra_float(height) * __pytra_float(Double(0.5)))))) * __pytra_float(scale)))))
        let __step_1 = __pytra_int(Int64(1))
        var x = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width))) {
            var cx: Double = __pytra_float((__pytra_float(center_x) + __pytra_float((__pytra_float((__pytra_float(x) - __pytra_float((__pytra_float(width) * __pytra_float(Double(0.5)))))) * __pytra_float(scale)))))
            var zx: Double = __pytra_float(Double(0.0))
            var zy: Double = __pytra_float(Double(0.0))
            var i: Int64 = __pytra_int(Int64(0))
            while (__pytra_int(i) < __pytra_int(max_iter)) {
                var zx2: Double = __pytra_float((__pytra_float(zx) * __pytra_float(zx)))
                var zy2: Double = __pytra_float((__pytra_float(zy) * __pytra_float(zy)))
                if (__pytra_float((__pytra_float(zx2) + __pytra_float(zy2))) > __pytra_float(Double(4.0))) {
                    break
                }
                zy = __pytra_float((__pytra_float((__pytra_float((__pytra_float(Double(2.0)) * __pytra_float(zx))) * __pytra_float(zy))) + __pytra_float(cy)))
                zx = __pytra_float((__pytra_float((__pytra_float(zx2) - __pytra_float(zy2))) + __pytra_float(cx)))
                i += Int64(1)
            }
            __pytra_setIndex(frame, (__pytra_int(row_base) + __pytra_int(x)), __pytra_int((__pytra_float((__pytra_float(Double(255.0)) * __pytra_float(i))) / __pytra_float(__hoisted_cast_1))))
            x += __step_1
        }
        y += __step_0
    }
    return __pytra_bytes(frame)
}

func run_05_mandelbrot_zoom() {
    var width: Int64 = __pytra_int(Int64(320))
    var height: Int64 = __pytra_int(Int64(240))
    var frame_count: Int64 = __pytra_int(Int64(48))
    var max_iter: Int64 = __pytra_int(Int64(110))
    var center_x: Double = __pytra_float((-Double(0.743643887037151)))
    var center_y: Double = __pytra_float(Double(0.13182590420533))
    var base_scale: Double = __pytra_float((__pytra_float(Double(3.2)) / __pytra_float(width)))
    var zoom_per_frame: Double = __pytra_float(Double(0.93))
    var out_path: String = __pytra_str("sample/out/05_mandelbrot_zoom.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var frames: [Any] = __pytra_as_list([])
    var scale: Double = __pytra_float(base_scale)
    let __step_1 = __pytra_int(Int64(1))
    var __loop_0 = __pytra_int(Int64(0))
    while ((__step_1 >= 0 && __loop_0 < __pytra_int(frame_count)) || (__step_1 < 0 && __loop_0 > __pytra_int(frame_count))) {
        frames = __pytra_as_list(frames); frames.append(render_frame(width, height, center_x, center_y, scale, max_iter))
        scale *= zoom_per_frame
        __loop_0 += __step_1
    }
    __pytra_noop(out_path, width, height, frames, [])
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
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
