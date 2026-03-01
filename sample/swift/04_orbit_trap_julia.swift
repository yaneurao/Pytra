import Foundation


// 04: Sample that renders an orbit-trap Julia set and writes a PNG image.

func render_orbit_trap_julia(width: Int64, height: Int64, max_iter: Int64, cx: Double, cy: Double) -> [Any] {
    var pixels: [Any] = __pytra_as_list([])
    var __hoisted_cast_1: Double = __pytra_float(height - Int64(1))
    var __hoisted_cast_2: Double = __pytra_float(width - Int64(1))
    var __hoisted_cast_3: Double = __pytra_float(max_iter)
    var y = __pytra_int(Int64(0))
    while (y < __pytra_int(height)) {
        var zy0: Double = ((-Double(1.3)) + (Double(2.6) * (__pytra_float(y) / __hoisted_cast_1)))
        var x = __pytra_int(Int64(0))
        while (x < __pytra_int(width)) {
            var zx: Double = ((-Double(1.9)) + (Double(3.8) * (__pytra_float(x) / __hoisted_cast_2)))
            var zy: Double = zy0
            var trap: Double = Double(1000000000.0)
            var i: Int64 = Int64(0)
            while (__pytra_int(i) < __pytra_int(max_iter)) {
                var ax: Double = zx
                if (__pytra_float(ax) < __pytra_float(Double(0.0))) {
                    ax = __pytra_float(-ax)
                }
                var ay: Double = zy
                if (__pytra_float(ay) < __pytra_float(Double(0.0))) {
                    ay = __pytra_float(-ay)
                }
                var dxy: Double = (zx - zy)
                if (__pytra_float(dxy) < __pytra_float(Double(0.0))) {
                    dxy = __pytra_float(-dxy)
                }
                if (__pytra_float(ax) < __pytra_float(trap)) {
                    trap = ax
                }
                if (__pytra_float(ay) < __pytra_float(trap)) {
                    trap = ay
                }
                if (__pytra_float(dxy) < __pytra_float(trap)) {
                    trap = dxy
                }
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
                var trap_scaled: Double = (trap * Double(3.2))
                if (__pytra_float(trap_scaled) > __pytra_float(Double(1.0))) {
                    trap_scaled = Double(1.0)
                }
                if (__pytra_float(trap_scaled) < __pytra_float(Double(0.0))) {
                    trap_scaled = Double(0.0)
                }
                var t: Double = (__pytra_float(i) / __hoisted_cast_3)
                var tone: Int64 = __pytra_int(Double(255.0) * (Double(1.0) - trap_scaled))
                r = __pytra_int(__pytra_float(tone) * (Double(0.35) + (Double(0.65) * t)))
                g = __pytra_int(__pytra_float(tone) * (Double(0.15) + (Double(0.85) * (Double(1.0) - t))))
                b = __pytra_int(Double(255.0) * (Double(0.25) + (Double(0.75) * t)))
                if (__pytra_int(r) > __pytra_int(Int64(255))) {
                    r = Int64(255)
                }
                if (__pytra_int(g) > __pytra_int(Int64(255))) {
                    g = Int64(255)
                }
                if (__pytra_int(b) > __pytra_int(Int64(255))) {
                    b = Int64(255)
                }
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

func run_04_orbit_trap_julia() {
    var width: Int64 = Int64(1920)
    var height: Int64 = Int64(1080)
    var max_iter: Int64 = Int64(1400)
    var out_path: String = "sample/out/04_orbit_trap_julia.png"
    var start: Double = __pytra_perf_counter()
    var pixels: [Any] = __pytra_as_list(render_orbit_trap_julia(width, height, max_iter, (-Double(0.7269)), Double(0.1889)))
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
        run_04_orbit_trap_julia()
    }
}
