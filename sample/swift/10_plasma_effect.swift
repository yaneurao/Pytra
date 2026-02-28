// Auto-generated Pytra Swift native source from EAST3.
import Foundation

// Runtime helpers are provided by py_runtime.swift in the same module.

func run_10_plasma_effect() {
    var w: Int64 = __pytra_int(Int64(320))
    var h: Int64 = __pytra_int(Int64(240))
    var frames_n: Int64 = __pytra_int(Int64(216))
    var out_path: String = __pytra_str("sample/out/10_plasma_effect.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var frames: [Any] = __pytra_as_list([])
    let __step_0 = __pytra_int(Int64(1))
    var t = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && t < __pytra_int(frames_n)) || (__step_0 < 0 && t > __pytra_int(frames_n))) {
        var frame: [Any] = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
        let __step_1 = __pytra_int(Int64(1))
        var y = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && y < __pytra_int(h)) || (__step_1 < 0 && y > __pytra_int(h))) {
            var row_base: Int64 = __pytra_int((__pytra_int(y) * __pytra_int(w)))
            let __step_2 = __pytra_int(Int64(1))
            var x = __pytra_int(Int64(0))
            while ((__step_2 >= 0 && x < __pytra_int(w)) || (__step_2 < 0 && x > __pytra_int(w))) {
                var dx: Int64 = __pytra_int((__pytra_int(x) - __pytra_int(Int64(160))))
                var dy: Int64 = __pytra_int((__pytra_int(y) - __pytra_int(Int64(120))))
                var v: Any = (((sin(__pytra_float((__pytra_float((__pytra_float(x) + __pytra_float((__pytra_float(t) * __pytra_float(Double(2.0)))))) * __pytra_float(Double(0.045))))) + sin(__pytra_float((__pytra_float((__pytra_float(y) - __pytra_float((__pytra_float(t) * __pytra_float(Double(1.2)))))) * __pytra_float(Double(0.05)))))) + sin(__pytra_float((__pytra_float((__pytra_float((__pytra_int(x) + __pytra_int(y))) + __pytra_float((__pytra_float(t) * __pytra_float(Double(1.7)))))) * __pytra_float(Double(0.03)))))) + sin(__pytra_float(((sqrt(__pytra_float((__pytra_int((__pytra_int(dx) * __pytra_int(dx))) + __pytra_int((__pytra_int(dy) * __pytra_int(dy)))))) * Double(0.07)) - (__pytra_float(t) * __pytra_float(Double(0.18)))))))
                var c: Int64 = __pytra_int(__pytra_int(((v + Double(4.0)) * (__pytra_float(Double(255.0)) / __pytra_float(Double(8.0))))))
                if (__pytra_int(c) < __pytra_int(Int64(0))) {
                    c = __pytra_int(Int64(0))
                }
                if (__pytra_int(c) > __pytra_int(Int64(255))) {
                    c = __pytra_int(Int64(255))
                }
                __pytra_setIndex(frame, (__pytra_int(row_base) + __pytra_int(x)), c)
                x += __step_2
            }
            y += __step_1
        }
        frames = __pytra_as_list(frames); frames.append(__pytra_bytes(frame))
        t += __step_0
    }
    __pytra_noop(out_path, w, h, frames, [])
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

@main
struct Main {
    static func main() {
        run_10_plasma_effect()
    }
}
