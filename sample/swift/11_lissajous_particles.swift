import Foundation


// 11: Sample that outputs Lissajous-motion particles as a GIF.

func color_palette() -> [Any] {
    var p: [Any] = __pytra_as_list([])
    var i = __pytra_int(Int64(0))
    while (i < __pytra_int(Int64(256))) {
        var r: Int64 = i
        var g: Int64 = ((i * Int64(3)) % Int64(256))
        var b: Int64 = (Int64(255) - i)
        p.append(r)
        p.append(g)
        p.append(b)
        i += 1
    }
    return __pytra_as_list(__pytra_bytes(p))
}

func run_11_lissajous_particles() {
    var w: Int64 = Int64(320)
    var h: Int64 = Int64(240)
    var frames_n: Int64 = Int64(360)
    var particles: Int64 = Int64(48)
    var out_path: String = "sample/out/11_lissajous_particles.gif"
    var start: Double = __pytra_perf_counter()
    var frames: [Any] = __pytra_as_list([])
    var t = __pytra_int(Int64(0))
    while (t < __pytra_int(frames_n)) {
        var frame: [Any] = __pytra_as_list(__pytra_bytearray((w * h)))
        var __hoisted_cast_1: Double = __pytra_float(t)
        var p = __pytra_int(Int64(0))
        while (p < __pytra_int(particles)) {
            var phase: Double = (__pytra_float(p) * Double(0.261799))
            var x: Int64 = __pytra_int((__pytra_float(w) * Double(0.5)) + ((__pytra_float(w) * Double(0.38)) * sin(__pytra_float((Double(0.11) * __hoisted_cast_1) + (phase * Double(2.0))))))
            var y: Int64 = __pytra_int((__pytra_float(h) * Double(0.5)) + ((__pytra_float(h) * Double(0.38)) * sin(__pytra_float((Double(0.17) * __hoisted_cast_1) + (phase * Double(3.0))))))
            var color: Int64 = (Int64(30) + ((p * Int64(9)) % Int64(220)))
            var dy = __pytra_int(-Int64(2))
            while (dy < __pytra_int(Int64(3))) {
                var dx = __pytra_int(-Int64(2))
                while (dx < __pytra_int(Int64(3))) {
                    var xx: Int64 = (x + dx)
                    var yy: Int64 = (y + dy)
                    if ((__pytra_int(xx) >= __pytra_int(Int64(0))) && (__pytra_int(xx) < __pytra_int(w)) && (__pytra_int(yy) >= __pytra_int(Int64(0))) && (__pytra_int(yy) < __pytra_int(h))) {
                        var d2: Int64 = ((dx * dx) + (dy * dy))
                        if (__pytra_int(d2) <= __pytra_int(Int64(4))) {
                            var idx: Int64 = ((yy * w) + xx)
                            var v: Int64 = (color - (d2 * Int64(20)))
                            v = __pytra_int(__pytra_max(Int64(0), v))
                            if (__pytra_int(v) > __pytra_int(__pytra_getIndex(frame, idx))) {
                                __pytra_setIndex(frame, idx, v)
                            }
                        }
                    }
                    dx += 1
                }
                dy += 1
            }
            p += 1
        }
        frames.append(__pytra_bytes(frame))
        t += 1
    }
    __pytra_noop(out_path, w, h, frames, color_palette())
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

@main
struct Main {
    static func main() {
        run_11_lissajous_particles()
    }
}
