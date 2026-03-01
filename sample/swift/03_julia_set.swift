import Foundation


// 03: Sample that outputs a Julia set as a PNG image.
// Implemented with simple loop-centric logic for transpilation compatibility.

func render_julia(width: Int64, height: Int64, max_iter: Int64, cx: Double, cy: Double) -> [Any] {
    var pixels: [Any] = __pytra_as_list([])
    var __hoisted_cast_1: Double = __pytra_float(height - Int64(1))
    var __hoisted_cast_2: Double = __pytra_float(width - Int64(1))
    var __hoisted_cast_3: Double = __pytra_float(max_iter)
    var y = __pytra_int(Int64(0))
    while (y < __pytra_int(height)) {
        var zy0: Double = ((-Double(1.2)) + (Double(2.4) * (__pytra_float(y) / __hoisted_cast_1)))
        var x = __pytra_int(Int64(0))
        while (x < __pytra_int(width)) {
            var zx: Double = ((-Double(1.8)) + (Double(3.6) * (__pytra_float(x) / __hoisted_cast_2)))
            var zy: Double = zy0
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
            var r: Int64 = Int64(0)
            var g: Int64 = Int64(0)
            var b: Int64 = Int64(0)
            if (__pytra_int(i) >= __pytra_int(max_iter)) {
                r = Int64(0)
                g = Int64(0)
                b = Int64(0)
            } else {
                var t: Double = (__pytra_float(i) / __hoisted_cast_3)
                r = __pytra_int(Double(255.0) * (Double(0.2) + (Double(0.8) * t)))
                g = __pytra_int(Double(255.0) * (Double(0.1) + (Double(0.9) * (t * t))))
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

func run_julia() {
    var width: Int64 = Int64(3840)
    var height: Int64 = Int64(2160)
    var max_iter: Int64 = Int64(20000)
    var out_path: String = "sample/out/03_julia_set.png"
    var start: Double = __pytra_perf_counter()
    var pixels: [Any] = __pytra_as_list(render_julia(width, height, max_iter, (-Double(0.8)), Double(0.156)))
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
        run_julia()
    }
}
