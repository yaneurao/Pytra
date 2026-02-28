// Auto-generated Pytra Swift native source from EAST3.
import Foundation

// Runtime helpers are provided by py_runtime.swift in the same module.

func render_julia(width: Int64, height: Int64, max_iter: Int64, cx: Double, cy: Double) -> [Any] {
    var pixels: [Any] = __pytra_as_list([])
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float((__pytra_int(height) - __pytra_int(Int64(1)))))
    var __hoisted_cast_2: Double = __pytra_float(__pytra_float((__pytra_int(width) - __pytra_int(Int64(1)))))
    var __hoisted_cast_3: Double = __pytra_float(__pytra_float(max_iter))
    let __step_0 = __pytra_int(Int64(1))
    var y = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height))) {
        var zy0: Double = __pytra_float((__pytra_float((-Double(1.2))) + __pytra_float((__pytra_float(Double(2.4)) * __pytra_float((__pytra_float(y) / __pytra_float(__hoisted_cast_1)))))))
        let __step_1 = __pytra_int(Int64(1))
        var x = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width))) {
            var zx: Double = __pytra_float((__pytra_float((-Double(1.8))) + __pytra_float((__pytra_float(Double(3.6)) * __pytra_float((__pytra_float(x) / __pytra_float(__hoisted_cast_2)))))))
            var zy: Double = __pytra_float(zy0)
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
            var r: Int64 = __pytra_int(Int64(0))
            var g: Int64 = __pytra_int(Int64(0))
            var b: Int64 = __pytra_int(Int64(0))
            if (__pytra_int(i) >= __pytra_int(max_iter)) {
                r = __pytra_int(Int64(0))
                g = __pytra_int(Int64(0))
                b = __pytra_int(Int64(0))
            } else {
                var t: Double = __pytra_float((__pytra_float(i) / __pytra_float(__hoisted_cast_3)))
                r = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float((__pytra_float(Double(0.2)) + __pytra_float((__pytra_float(Double(0.8)) * __pytra_float(t))))))))
                g = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float((__pytra_float(Double(0.1)) + __pytra_float((__pytra_float(Double(0.9)) * __pytra_float((__pytra_float(t) * __pytra_float(t))))))))))
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

func run_julia() {
    var width: Int64 = __pytra_int(Int64(3840))
    var height: Int64 = __pytra_int(Int64(2160))
    var max_iter: Int64 = __pytra_int(Int64(20000))
    var out_path: String = __pytra_str("sample/out/03_julia_set.png")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var pixels: [Any] = __pytra_as_list(render_julia(width, height, max_iter, (-Double(0.8)), Double(0.156)))
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
        run_julia()
    }
}
