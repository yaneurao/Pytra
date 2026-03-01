import Foundation


// 01: Sample that outputs the Mandelbrot set as a PNG image.
// Syntax is kept straightforward with future transpilation in mind.

func escape_count(cx: Double, cy: Double, max_iter: Int64) -> Int64 {
    var x: Double = Double(0.0)
    var y: Double = Double(0.0)
    var i = __pytra_int(Int64(0))
    while (i < __pytra_int(max_iter)) {
        var x2: Double = (x * x)
        var y2: Double = (y * y)
        if (__pytra_float(x2 + y2) > __pytra_float(Double(4.0))) {
            return i
        }
        y = (((Double(2.0) * x) * y) + cy)
        x = ((x2 - y2) + cx)
        i += 1
    }
    return max_iter
}

func color_map(iter_count: Int64, max_iter: Int64) -> [Any] {
    if (__pytra_int(iter_count) >= __pytra_int(max_iter)) {
        return __pytra_as_list([Int64(0), Int64(0), Int64(0)])
    }
    var t: Double = (__pytra_float(iter_count) / __pytra_float(max_iter))
    var r: Int64 = __pytra_int(Double(255.0) * (t * t))
    var g: Int64 = __pytra_int(Double(255.0) * t)
    var b: Int64 = __pytra_int(Double(255.0) * (Double(1.0) - t))
    return __pytra_as_list([r, g, b])
}

func render_mandelbrot(width: Int64, height: Int64, max_iter: Int64, x_min: Double, x_max: Double, y_min: Double, y_max: Double) -> [Any] {
    var pixels: [Any] = __pytra_as_list([])
    var __hoisted_cast_1: Double = __pytra_float(height - Int64(1))
    var __hoisted_cast_2: Double = __pytra_float(width - Int64(1))
    var __hoisted_cast_3: Double = __pytra_float(max_iter)
    var y = __pytra_int(Int64(0))
    while (y < __pytra_int(height)) {
        var py: Double = (y_min + ((y_max - y_min) * (__pytra_float(y) / __hoisted_cast_1)))
        var x = __pytra_int(Int64(0))
        while (x < __pytra_int(width)) {
            var px: Double = (x_min + ((x_max - x_min) * (__pytra_float(x) / __hoisted_cast_2)))
            var it: Int64 = __pytra_int(escape_count(px, py, max_iter))
            var r: Int64 = 0
            var g: Int64 = 0
            var b: Int64 = 0
            if (__pytra_int(it) >= __pytra_int(max_iter)) {
                r = Int64(0)
                g = Int64(0)
                b = Int64(0)
            } else {
                var t: Double = (__pytra_float(it) / __hoisted_cast_3)
                r = __pytra_int(Double(255.0) * (t * t))
                g = __pytra_int(Double(255.0) * t)
                b = __pytra_int(Double(255.0) * (Double(1.0) - t))
            }
            pixels.append(r)
            pixels.append(g)
            pixels.append(b)
            x += 1
        }
        y += 1
    }
    return pixels
}

func run_mandelbrot() {
    var width: Int64 = Int64(1600)
    var height: Int64 = Int64(1200)
    var max_iter: Int64 = Int64(1000)
    var out_path: String = "sample/out/01_mandelbrot.png"
    var start: Double = __pytra_perf_counter()
    var pixels: [Any] = __pytra_as_list(render_mandelbrot(width, height, max_iter, (-Double(2.2)), Double(1.0), (-Double(1.2)), Double(1.2)))
    __pytra_write_rgb_png(out_path, width, height, pixels)
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
}

@main
struct Main {
    static func main() {
        run_mandelbrot()
    }
}
