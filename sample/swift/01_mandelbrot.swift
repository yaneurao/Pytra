// Auto-generated Pytra Swift native source from EAST3.
import Foundation

// Runtime helpers are provided by py_runtime.swift in the same module.

func escape_count(cx: Double, cy: Double, max_iter: Int64) -> Int64 {
    var x: Double = __pytra_float(Double(0.0))
    var y: Double = __pytra_float(Double(0.0))
    let __step_0 = __pytra_int(Int64(1))
    var i = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && i < __pytra_int(max_iter)) || (__step_0 < 0 && i > __pytra_int(max_iter))) {
        var x2: Double = __pytra_float((__pytra_float(x) * __pytra_float(x)))
        var y2: Double = __pytra_float((__pytra_float(y) * __pytra_float(y)))
        if (__pytra_float((__pytra_float(x2) + __pytra_float(y2))) > __pytra_float(Double(4.0))) {
            return i
        }
        y = __pytra_float((__pytra_float((__pytra_float((__pytra_float(Double(2.0)) * __pytra_float(x))) * __pytra_float(y))) + __pytra_float(cy)))
        x = __pytra_float((__pytra_float((__pytra_float(x2) - __pytra_float(y2))) + __pytra_float(cx)))
        i += __step_0
    }
    return max_iter
}

func color_map(iter_count: Int64, max_iter: Int64) -> [Any] {
    if (__pytra_int(iter_count) >= __pytra_int(max_iter)) {
        return [Int64(0), Int64(0), Int64(0)]
    }
    var t: Double = __pytra_float((__pytra_float(iter_count) / __pytra_float(max_iter)))
    var r: Int64 = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float((__pytra_float(t) * __pytra_float(t))))))
    var g: Int64 = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float(t))))
    var b: Int64 = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float((__pytra_float(Double(1.0)) - __pytra_float(t))))))
    return [r, g, b]
}

func render_mandelbrot(width: Int64, height: Int64, max_iter: Int64, x_min: Double, x_max: Double, y_min: Double, y_max: Double) -> [Any] {
    var pixels: [Any] = __pytra_as_list([])
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float((__pytra_int(height) - __pytra_int(Int64(1)))))
    var __hoisted_cast_2: Double = __pytra_float(__pytra_float((__pytra_int(width) - __pytra_int(Int64(1)))))
    var __hoisted_cast_3: Double = __pytra_float(__pytra_float(max_iter))
    let __step_0 = __pytra_int(Int64(1))
    var y = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height))) {
        var py: Double = __pytra_float((__pytra_float(y_min) + __pytra_float((__pytra_float((__pytra_float(y_max) - __pytra_float(y_min))) * __pytra_float((__pytra_float(y) / __pytra_float(__hoisted_cast_1)))))))
        let __step_1 = __pytra_int(Int64(1))
        var x = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width))) {
            var px: Double = __pytra_float((__pytra_float(x_min) + __pytra_float((__pytra_float((__pytra_float(x_max) - __pytra_float(x_min))) * __pytra_float((__pytra_float(x) / __pytra_float(__hoisted_cast_2)))))))
            var it: Int64 = __pytra_int(escape_count(px, py, max_iter))
            var r: Int64 = 0
            var g: Int64 = 0
            var b: Int64 = 0
            if (__pytra_int(it) >= __pytra_int(max_iter)) {
                r = __pytra_int(Int64(0))
                g = __pytra_int(Int64(0))
                b = __pytra_int(Int64(0))
            } else {
                var t: Double = __pytra_float((__pytra_float(it) / __pytra_float(__hoisted_cast_3)))
                r = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float((__pytra_float(t) * __pytra_float(t))))))
                g = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float(t))))
                b = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float((__pytra_float(Double(1.0)) - __pytra_float(t))))))
            }
            pixels = __pytra_as_list(pixels); pixels.append(r)
            pixels = __pytra_as_list(pixels); pixels.append(g)
            pixels = __pytra_as_list(pixels); pixels.append(b)
            x += __step_1
        }
        y += __step_0
    }
    return pixels
}

func run_mandelbrot() {
    var width: Int64 = __pytra_int(Int64(1600))
    var height: Int64 = __pytra_int(Int64(1200))
    var max_iter: Int64 = __pytra_int(Int64(1000))
    var out_path: String = __pytra_str("sample/out/01_mandelbrot.png")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var pixels: [Any] = __pytra_as_list(render_mandelbrot(width, height, max_iter, (-Double(2.2)), Double(1.0), (-Double(1.2)), Double(1.2)))
    __pytra_noop(out_path, width, height, pixels)
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
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
