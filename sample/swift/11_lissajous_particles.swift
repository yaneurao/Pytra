import Foundation


// 11: Sample that outputs Lissajous-motion particles as a GIF.

func color_palette() -> [Any] {
    var p: [Any] = __pytra_as_list([])
    let __step_0 = __pytra_int(Int64(1))
    var i = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && i < __pytra_int(Int64(256))) || (__step_0 < 0 && i > __pytra_int(Int64(256)))) {
        var r: Int64 = __pytra_int(i)
        var g: Int64 = __pytra_int((__pytra_int((__pytra_int(i) * __pytra_int(Int64(3)))) % __pytra_int(Int64(256))))
        var b: Int64 = __pytra_int((__pytra_int(Int64(255)) - __pytra_int(i)))
        p = __pytra_as_list(p); p.append(r)
        p = __pytra_as_list(p); p.append(g)
        p = __pytra_as_list(p); p.append(b)
        i += __step_0
    }
    return __pytra_bytes(p)
}

func run_11_lissajous_particles() {
    var w: Int64 = __pytra_int(Int64(320))
    var h: Int64 = __pytra_int(Int64(240))
    var frames_n: Int64 = __pytra_int(Int64(360))
    var particles: Int64 = __pytra_int(Int64(48))
    var out_path: String = __pytra_str("sample/out/11_lissajous_particles.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var frames: [Any] = __pytra_as_list([])
    let __step_0 = __pytra_int(Int64(1))
    var t = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && t < __pytra_int(frames_n)) || (__step_0 < 0 && t > __pytra_int(frames_n))) {
        var frame: [Any] = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
        var __hoisted_cast_1: Double = __pytra_float(__pytra_float(t))
        let __step_1 = __pytra_int(Int64(1))
        var p = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && p < __pytra_int(particles)) || (__step_1 < 0 && p > __pytra_int(particles))) {
            var phase: Double = __pytra_float((__pytra_float(p) * __pytra_float(Double(0.261799))))
            var x: Int64 = __pytra_int(__pytra_int(((__pytra_float(w) * __pytra_float(Double(0.5))) + ((__pytra_float(w) * __pytra_float(Double(0.38))) * sin(__pytra_float((__pytra_float((__pytra_float(Double(0.11)) * __pytra_float(__hoisted_cast_1))) + __pytra_float((__pytra_float(phase) * __pytra_float(Double(2.0)))))))))))
            var y: Int64 = __pytra_int(__pytra_int(((__pytra_float(h) * __pytra_float(Double(0.5))) + ((__pytra_float(h) * __pytra_float(Double(0.38))) * sin(__pytra_float((__pytra_float((__pytra_float(Double(0.17)) * __pytra_float(__hoisted_cast_1))) + __pytra_float((__pytra_float(phase) * __pytra_float(Double(3.0)))))))))))
            var color: Int64 = __pytra_int((__pytra_int(Int64(30)) + __pytra_int((__pytra_int((__pytra_int(p) * __pytra_int(Int64(9)))) % __pytra_int(Int64(220))))))
            let __step_2 = __pytra_int(Int64(1))
            var dy = __pytra_int((-Int64(2)))
            while ((__step_2 >= 0 && dy < __pytra_int(Int64(3))) || (__step_2 < 0 && dy > __pytra_int(Int64(3)))) {
                let __step_3 = __pytra_int(Int64(1))
                var dx = __pytra_int((-Int64(2)))
                while ((__step_3 >= 0 && dx < __pytra_int(Int64(3))) || (__step_3 < 0 && dx > __pytra_int(Int64(3)))) {
                    var xx: Int64 = __pytra_int((__pytra_int(x) + __pytra_int(dx)))
                    var yy: Int64 = __pytra_int((__pytra_int(y) + __pytra_int(dy)))
                    if ((__pytra_int(xx) >= __pytra_int(Int64(0))) && (__pytra_int(xx) < __pytra_int(w)) && (__pytra_int(yy) >= __pytra_int(Int64(0))) && (__pytra_int(yy) < __pytra_int(h))) {
                        var d2: Int64 = __pytra_int((__pytra_int((__pytra_int(dx) * __pytra_int(dx))) + __pytra_int((__pytra_int(dy) * __pytra_int(dy)))))
                        if (__pytra_int(d2) <= __pytra_int(Int64(4))) {
                            var idx: Int64 = __pytra_int((__pytra_int((__pytra_int(yy) * __pytra_int(w))) + __pytra_int(xx)))
                            var v: Int64 = __pytra_int((__pytra_int(color) - __pytra_int((__pytra_int(d2) * __pytra_int(Int64(20))))))
                            v = __pytra_int(__pytra_max(Int64(0), v))
                            if (__pytra_int(v) > __pytra_int(__pytra_int(__pytra_getIndex(frame, idx)))) {
                                __pytra_setIndex(frame, idx, v)
                            }
                        }
                    }
                    dx += __step_3
                }
                dy += __step_2
            }
            p += __step_1
        }
        frames = __pytra_as_list(frames); frames.append(__pytra_bytes(frame))
        t += __step_0
    }
    __pytra_noop(out_path, w, h, frames, color_palette())
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
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
