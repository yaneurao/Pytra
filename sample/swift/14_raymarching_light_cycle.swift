// Auto-generated Pytra Swift native source from EAST3.
import Foundation

// Runtime helpers are provided by py_runtime.swift in the same module.

func palette() -> [Any] {
    var p: [Any] = __pytra_as_list([])
    let __step_0 = __pytra_int(Int64(1))
    var i = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && i < __pytra_int(Int64(256))) || (__step_0 < 0 && i > __pytra_int(Int64(256)))) {
        var r: Int64 = __pytra_int(__pytra_min(Int64(255), __pytra_int((__pytra_float(Int64(20)) + __pytra_float((__pytra_float(i) * __pytra_float(Double(0.9))))))))
        var g: Int64 = __pytra_int(__pytra_min(Int64(255), __pytra_int((__pytra_float(Int64(10)) + __pytra_float((__pytra_float(i) * __pytra_float(Double(0.7))))))))
        var b: Int64 = __pytra_int(__pytra_min(Int64(255), (__pytra_int(Int64(30)) + __pytra_int(i))))
        p = __pytra_as_list(p); p.append(r)
        p = __pytra_as_list(p); p.append(g)
        p = __pytra_as_list(p); p.append(b)
        i += __step_0
    }
    return __pytra_bytes(p)
}

func scene(x: Double, y: Double, light_x: Double, light_y: Double) -> Int64 {
    var x1: Double = __pytra_float((__pytra_float(x) + __pytra_float(Double(0.45))))
    var y1: Double = __pytra_float((__pytra_float(y) + __pytra_float(Double(0.2))))
    var x2: Double = __pytra_float((__pytra_float(x) - __pytra_float(Double(0.35))))
    var y2: Double = __pytra_float((__pytra_float(y) - __pytra_float(Double(0.15))))
    var r1: Any = sqrt(__pytra_float((__pytra_float((__pytra_float(x1) * __pytra_float(x1))) + __pytra_float((__pytra_float(y1) * __pytra_float(y1))))))
    var r2: Any = sqrt(__pytra_float((__pytra_float((__pytra_float(x2) * __pytra_float(x2))) + __pytra_float((__pytra_float(y2) * __pytra_float(y2))))))
    var blob: Any = (exp(__pytra_float((((-Double(7.0)) * r1) * r1))) + exp(__pytra_float((((-Double(8.0)) * r2) * r2))))
    var lx: Double = __pytra_float((__pytra_float(x) - __pytra_float(light_x)))
    var ly: Double = __pytra_float((__pytra_float(y) - __pytra_float(light_y)))
    var l: Any = sqrt(__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(lx))) + __pytra_float((__pytra_float(ly) * __pytra_float(ly))))))
    var lit: Double = __pytra_float((__pytra_float(Double(1.0)) / __pytra_float((Double(1.0) + ((Double(3.5) * l) * l)))))
    var v: Int64 = __pytra_int(__pytra_int((((Double(255.0) * blob) * lit) * Double(5.0))))
    return __pytra_min(Int64(255), __pytra_max(Int64(0), v))
}

func run_14_raymarching_light_cycle() {
    var w: Int64 = __pytra_int(Int64(320))
    var h: Int64 = __pytra_int(Int64(240))
    var frames_n: Int64 = __pytra_int(Int64(84))
    var out_path: String = __pytra_str("sample/out/14_raymarching_light_cycle.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var frames: [Any] = __pytra_as_list([])
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float(frames_n))
    var __hoisted_cast_2: Double = __pytra_float(__pytra_float((__pytra_int(h) - __pytra_int(Int64(1)))))
    var __hoisted_cast_3: Double = __pytra_float(__pytra_float((__pytra_int(w) - __pytra_int(Int64(1)))))
    let __step_0 = __pytra_int(Int64(1))
    var t = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && t < __pytra_int(frames_n)) || (__step_0 < 0 && t > __pytra_int(frames_n))) {
        var frame: [Any] = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
        var a: Double = __pytra_float((((__pytra_float(t) / __pytra_float(__hoisted_cast_1)) * Double.pi) * Double(2.0)))
        var light_x: Double = __pytra_float((Double(0.75) * cos(__pytra_float(a))))
        var light_y: Double = __pytra_float((Double(0.55) * sin(__pytra_float((a * Double(1.2))))))
        let __step_1 = __pytra_int(Int64(1))
        var y = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && y < __pytra_int(h)) || (__step_1 < 0 && y > __pytra_int(h))) {
            var row_base: Int64 = __pytra_int((__pytra_int(y) * __pytra_int(w)))
            var py: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float(y) / __pytra_float(__hoisted_cast_2))) * __pytra_float(Double(2.0)))) - __pytra_float(Double(1.0))))
            let __step_2 = __pytra_int(Int64(1))
            var x = __pytra_int(Int64(0))
            while ((__step_2 >= 0 && x < __pytra_int(w)) || (__step_2 < 0 && x > __pytra_int(w))) {
                var px: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float(x) / __pytra_float(__hoisted_cast_3))) * __pytra_float(Double(2.0)))) - __pytra_float(Double(1.0))))
                __pytra_setIndex(frame, (__pytra_int(row_base) + __pytra_int(x)), scene(px, py, light_x, light_y))
                x += __step_2
            }
            y += __step_1
        }
        frames = __pytra_as_list(frames); frames.append(__pytra_bytes(frame))
        t += __step_0
    }
    __pytra_noop(out_path, w, h, frames, palette())
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

@main
struct Main {
    static func main() {
        run_14_raymarching_light_cycle()
    }
}
