// Auto-generated Pytra Swift native source from EAST3.
import Foundation

// Runtime helpers are provided by py_runtime.swift in the same module.

func fire_palette() -> [Any] {
    var p: [Any] = __pytra_as_list([])
    let __step_0 = __pytra_int(Int64(1))
    var i = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && i < __pytra_int(Int64(256))) || (__step_0 < 0 && i > __pytra_int(Int64(256)))) {
        var r: Int64 = __pytra_int(Int64(0))
        var g: Int64 = __pytra_int(Int64(0))
        var b: Int64 = __pytra_int(Int64(0))
        if (__pytra_int(i) < __pytra_int(Int64(85))) {
            r = __pytra_int((__pytra_int(i) * __pytra_int(Int64(3))))
            g = __pytra_int(Int64(0))
            b = __pytra_int(Int64(0))
        } else {
            if (__pytra_int(i) < __pytra_int(Int64(170))) {
                r = __pytra_int(Int64(255))
                g = __pytra_int((__pytra_int((__pytra_int(i) - __pytra_int(Int64(85)))) * __pytra_int(Int64(3))))
                b = __pytra_int(Int64(0))
            } else {
                r = __pytra_int(Int64(255))
                g = __pytra_int(Int64(255))
                b = __pytra_int((__pytra_int((__pytra_int(i) - __pytra_int(Int64(170)))) * __pytra_int(Int64(3))))
            }
        }
        p = __pytra_as_list(p); p.append(r)
        p = __pytra_as_list(p); p.append(g)
        p = __pytra_as_list(p); p.append(b)
        i += __step_0
    }
    return __pytra_bytes(p)
}

func run_09_fire_simulation() {
    var w: Int64 = __pytra_int(Int64(380))
    var h: Int64 = __pytra_int(Int64(260))
    var steps: Int64 = __pytra_int(Int64(420))
    var out_path: String = __pytra_str("sample/out/09_fire_simulation.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var heat: [Any] = __pytra_as_list(({ () -> [Any] in var __out: [Any] = []; let __step = __pytra_int(Int64(1)); var __lc_i = __pytra_int(Int64(0)); while ((__step >= 0 && __lc_i < __pytra_int(h)) || (__step < 0 && __lc_i > __pytra_int(h))) { __out.append(__pytra_list_repeat(Int64(0), w)); __lc_i += __step }; return __out })())
    var frames: [Any] = __pytra_as_list([])
    let __step_0 = __pytra_int(Int64(1))
    var t = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && t < __pytra_int(steps)) || (__step_0 < 0 && t > __pytra_int(steps))) {
        let __step_1 = __pytra_int(Int64(1))
        var x = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w))) {
            var val: Int64 = __pytra_int((__pytra_int(Int64(170)) + __pytra_int((__pytra_int((__pytra_int((__pytra_int(x) * __pytra_int(Int64(13)))) + __pytra_int((__pytra_int(t) * __pytra_int(Int64(17)))))) % __pytra_int(Int64(86))))))
            __pytra_setIndex(__pytra_as_list(__pytra_getIndex(heat, (__pytra_int(h) - __pytra_int(Int64(1))))), x, val)
            x += __step_1
        }
        let __step_2 = __pytra_int(Int64(1))
        var y = __pytra_int(Int64(1))
        while ((__step_2 >= 0 && y < __pytra_int(h)) || (__step_2 < 0 && y > __pytra_int(h))) {
            let __step_3 = __pytra_int(Int64(1))
            var x = __pytra_int(Int64(0))
            while ((__step_3 >= 0 && x < __pytra_int(w)) || (__step_3 < 0 && x > __pytra_int(w))) {
                var a: Int64 = __pytra_int(__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(heat, y)), x)))
                var b: Int64 = __pytra_int(__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(heat, y)), (__pytra_int((__pytra_int((__pytra_int(x) - __pytra_int(Int64(1)))) + __pytra_int(w))) % __pytra_int(w)))))
                var c: Int64 = __pytra_int(__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(heat, y)), (__pytra_int((__pytra_int(x) + __pytra_int(Int64(1)))) % __pytra_int(w)))))
                var d: Int64 = __pytra_int(__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(heat, (__pytra_int((__pytra_int(y) + __pytra_int(Int64(1)))) % __pytra_int(h)))), x)))
                var v: Int64 = __pytra_int((__pytra_int(__pytra_int((__pytra_int((__pytra_int((__pytra_int(a) + __pytra_int(b))) + __pytra_int(c))) + __pytra_int(d))) / __pytra_int(Int64(4)))))
                var cool: Int64 = __pytra_int((__pytra_int(Int64(1)) + __pytra_int((__pytra_int((__pytra_int((__pytra_int(x) + __pytra_int(y))) + __pytra_int(t))) % __pytra_int(Int64(3))))))
                var nv: Int64 = __pytra_int((__pytra_int(v) - __pytra_int(cool)))
                __pytra_setIndex(__pytra_as_list(__pytra_getIndex(heat, (__pytra_int(y) - __pytra_int(Int64(1))))), x, __pytra_ifexp((__pytra_int(nv) > __pytra_int(Int64(0))), nv, Int64(0)))
                x += __step_3
            }
            y += __step_2
        }
        var frame: [Any] = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
        let __step_4 = __pytra_int(Int64(1))
        var yy = __pytra_int(Int64(0))
        while ((__step_4 >= 0 && yy < __pytra_int(h)) || (__step_4 < 0 && yy > __pytra_int(h))) {
            var row_base: Int64 = __pytra_int((__pytra_int(yy) * __pytra_int(w)))
            let __step_5 = __pytra_int(Int64(1))
            var xx = __pytra_int(Int64(0))
            while ((__step_5 >= 0 && xx < __pytra_int(w)) || (__step_5 < 0 && xx > __pytra_int(w))) {
                __pytra_setIndex(frame, (__pytra_int(row_base) + __pytra_int(xx)), __pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(heat, yy)), xx)))
                xx += __step_5
            }
            yy += __step_4
        }
        frames = __pytra_as_list(frames); frames.append(__pytra_bytes(frame))
        t += __step_0
    }
    __pytra_noop(out_path, w, h, frames, fire_palette())
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
}

@main
struct Main {
    static func main() {
        run_09_fire_simulation()
    }
}
