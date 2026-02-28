// Auto-generated Pytra Swift native source from EAST3.
import Foundation

// Runtime helpers are provided by py_runtime.swift in the same module.

func capture(grid: [Any], w: Int64, h: Int64) -> [Any] {
    var frame: [Any] = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
    let __step_0 = __pytra_int(Int64(1))
    var y = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && y < __pytra_int(h)) || (__step_0 < 0 && y > __pytra_int(h))) {
        var row_base: Int64 = __pytra_int((__pytra_int(y) * __pytra_int(w)))
        let __step_1 = __pytra_int(Int64(1))
        var x = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w))) {
            __pytra_setIndex(frame, (__pytra_int(row_base) + __pytra_int(x)), __pytra_ifexp((__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(grid, y)), x)) != 0), Int64(255), Int64(0)))
            x += __step_1
        }
        y += __step_0
    }
    return __pytra_bytes(frame)
}

func run_08_langtons_ant() {
    var w: Int64 = __pytra_int(Int64(420))
    var h: Int64 = __pytra_int(Int64(420))
    var out_path: String = __pytra_str("sample/out/08_langtons_ant.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var grid: [Any] = __pytra_as_list(({ () -> [Any] in var __out: [Any] = []; let __step = __pytra_int(Int64(1)); var __lc_i = __pytra_int(Int64(0)); while ((__step >= 0 && __lc_i < __pytra_int(h)) || (__step < 0 && __lc_i > __pytra_int(h))) { __out.append(__pytra_list_repeat(Int64(0), w)); __lc_i += __step }; return __out })())
    var x: Int64 = __pytra_int((__pytra_int(__pytra_int(w) / __pytra_int(Int64(2)))))
    var y: Int64 = __pytra_int((__pytra_int(__pytra_int(h) / __pytra_int(Int64(2)))))
    var d: Int64 = __pytra_int(Int64(0))
    var steps_total: Int64 = __pytra_int(Int64(600000))
    var capture_every: Int64 = __pytra_int(Int64(3000))
    var frames: [Any] = __pytra_as_list([])
    let __step_0 = __pytra_int(Int64(1))
    var i = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && i < __pytra_int(steps_total)) || (__step_0 < 0 && i > __pytra_int(steps_total))) {
        if (__pytra_int(__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(grid, y)), x))) == __pytra_int(Int64(0))) {
            d = __pytra_int((__pytra_int((__pytra_int(d) + __pytra_int(Int64(1)))) % __pytra_int(Int64(4))))
            __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, y)), x, Int64(1))
        } else {
            d = __pytra_int((__pytra_int((__pytra_int(d) + __pytra_int(Int64(3)))) % __pytra_int(Int64(4))))
            __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, y)), x, Int64(0))
        }
        if (__pytra_int(d) == __pytra_int(Int64(0))) {
            y = __pytra_int((__pytra_int((__pytra_int((__pytra_int(y) - __pytra_int(Int64(1)))) + __pytra_int(h))) % __pytra_int(h)))
        } else {
            if (__pytra_int(d) == __pytra_int(Int64(1))) {
                x = __pytra_int((__pytra_int((__pytra_int(x) + __pytra_int(Int64(1)))) % __pytra_int(w)))
            } else {
                if (__pytra_int(d) == __pytra_int(Int64(2))) {
                    y = __pytra_int((__pytra_int((__pytra_int(y) + __pytra_int(Int64(1)))) % __pytra_int(h)))
                } else {
                    x = __pytra_int((__pytra_int((__pytra_int((__pytra_int(x) - __pytra_int(Int64(1)))) + __pytra_int(w))) % __pytra_int(w)))
                }
            }
        }
        if (__pytra_int((__pytra_int(i) % __pytra_int(capture_every))) == __pytra_int(Int64(0))) {
            frames = __pytra_as_list(frames); frames.append(capture(grid, w, h))
        }
        i += __step_0
    }
    __pytra_noop(out_path, w, h, frames, [])
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", __pytra_len(frames))
    __pytra_print("elapsed_sec:", elapsed)
}

@main
struct Main {
    static func main() {
        run_08_langtons_ant()
    }
}
