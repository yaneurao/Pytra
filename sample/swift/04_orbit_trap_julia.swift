import Foundation


// 04: Sample that renders an orbit-trap Julia set and writes a PNG image.

func render_orbit_trap_julia(width: Int64, height: Int64, max_iter: Int64, cx: Double, cy: Double) -> [Any] {
    var pixels: [Any] = __pytra_as_list([])
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float((__pytra_int(height) - __pytra_int(Int64(1)))))
    var __hoisted_cast_2: Double = __pytra_float(__pytra_float((__pytra_int(width) - __pytra_int(Int64(1)))))
    var __hoisted_cast_3: Double = __pytra_float(__pytra_float(max_iter))
    let __step_0 = __pytra_int(Int64(1))
    var y = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height))) {
        var zy0: Double = __pytra_float((__pytra_float((-Double(1.3))) + __pytra_float((__pytra_float(Double(2.6)) * __pytra_float((__pytra_float(y) / __pytra_float(__hoisted_cast_1)))))))
        let __step_1 = __pytra_int(Int64(1))
        var x = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width))) {
            var zx: Double = __pytra_float((__pytra_float((-Double(1.9))) + __pytra_float((__pytra_float(Double(3.8)) * __pytra_float((__pytra_float(x) / __pytra_float(__hoisted_cast_2)))))))
            var zy: Double = __pytra_float(zy0)
            var trap: Double = __pytra_float(Double(1000000000.0))
            var i: Int64 = __pytra_int(Int64(0))
            while (__pytra_int(i) < __pytra_int(max_iter)) {
                var ax: Double = __pytra_float(zx)
                if (__pytra_float(ax) < __pytra_float(Double(0.0))) {
                    ax = __pytra_float((-ax))
                }
                var ay: Double = __pytra_float(zy)
                if (__pytra_float(ay) < __pytra_float(Double(0.0))) {
                    ay = __pytra_float((-ay))
                }
                var dxy: Double = __pytra_float((__pytra_float(zx) - __pytra_float(zy)))
                if (__pytra_float(dxy) < __pytra_float(Double(0.0))) {
                    dxy = __pytra_float((-dxy))
                }
                if (__pytra_float(ax) < __pytra_float(trap)) {
                    trap = __pytra_float(ax)
                }
                if (__pytra_float(ay) < __pytra_float(trap)) {
                    trap = __pytra_float(ay)
                }
                if (__pytra_float(dxy) < __pytra_float(trap)) {
                    trap = __pytra_float(dxy)
                }
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
                var trap_scaled: Double = __pytra_float((__pytra_float(trap) * __pytra_float(Double(3.2))))
                if (__pytra_float(trap_scaled) > __pytra_float(Double(1.0))) {
                    trap_scaled = __pytra_float(Double(1.0))
                }
                if (__pytra_float(trap_scaled) < __pytra_float(Double(0.0))) {
                    trap_scaled = __pytra_float(Double(0.0))
                }
                var t: Double = __pytra_float((__pytra_float(i) / __pytra_float(__hoisted_cast_3)))
                var tone: Int64 = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float((__pytra_float(Double(1.0)) - __pytra_float(trap_scaled))))))
                r = __pytra_int(__pytra_int((__pytra_float(tone) * __pytra_float((__pytra_float(Double(0.35)) + __pytra_float((__pytra_float(Double(0.65)) * __pytra_float(t))))))))
                g = __pytra_int(__pytra_int((__pytra_float(tone) * __pytra_float((__pytra_float(Double(0.15)) + __pytra_float((__pytra_float(Double(0.85)) * __pytra_float((__pytra_float(Double(1.0)) - __pytra_float(t))))))))))
                b = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float((__pytra_float(Double(0.25)) + __pytra_float((__pytra_float(Double(0.75)) * __pytra_float(t))))))))
                if (__pytra_int(r) > __pytra_int(Int64(255))) {
                    r = __pytra_int(Int64(255))
                }
                if (__pytra_int(g) > __pytra_int(Int64(255))) {
                    g = __pytra_int(Int64(255))
                }
                if (__pytra_int(b) > __pytra_int(Int64(255))) {
                    b = __pytra_int(Int64(255))
                }
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

func run_04_orbit_trap_julia() {
    var width: Int64 = __pytra_int(Int64(1920))
    var height: Int64 = __pytra_int(Int64(1080))
    var max_iter: Int64 = __pytra_int(Int64(1400))
    var out_path: String = __pytra_str("sample/out/04_orbit_trap_julia.png")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var pixels: [Any] = __pytra_as_list(render_orbit_trap_julia(width, height, max_iter, (-Double(0.7269)), Double(0.1889)))
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
        run_04_orbit_trap_julia()
    }
}
