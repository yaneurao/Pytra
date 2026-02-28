// Auto-generated Pytra Swift native source from EAST3.
import Foundation

// Runtime helpers are provided by py_runtime.swift in the same module.


// 12: Sample that outputs intermediate states of bubble sort as a GIF.

func render(values: [Any], w: Int64, h: Int64) -> [Any] {
    var frame: [Any] = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
    var n: Int64 = __pytra_int(__pytra_len(values))
    var bar_w: Double = __pytra_float((__pytra_float(w) / __pytra_float(n)))
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float(n))
    var __hoisted_cast_2: Double = __pytra_float(__pytra_float(h))
    let __step_0 = __pytra_int(Int64(1))
    var i = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && i < __pytra_int(n)) || (__step_0 < 0 && i > __pytra_int(n))) {
        var x0: Int64 = __pytra_int(__pytra_int((__pytra_float(i) * __pytra_float(bar_w))))
        var x1: Int64 = __pytra_int(__pytra_int((__pytra_float((__pytra_int(i) + __pytra_int(Int64(1)))) * __pytra_float(bar_w))))
        if (__pytra_int(x1) <= __pytra_int(x0)) {
            x1 = __pytra_int((__pytra_int(x0) + __pytra_int(Int64(1))))
        }
        var bh: Int64 = __pytra_int(__pytra_int((__pytra_float((__pytra_float(__pytra_int(__pytra_getIndex(values, i))) / __pytra_float(__hoisted_cast_1))) * __pytra_float(__hoisted_cast_2))))
        var y: Int64 = __pytra_int((__pytra_int(h) - __pytra_int(bh)))
        let __step_1 = __pytra_int(Int64(1))
        var y = __pytra_int(y)
        while ((__step_1 >= 0 && y < __pytra_int(h)) || (__step_1 < 0 && y > __pytra_int(h))) {
            let __step_2 = __pytra_int(Int64(1))
            var x = __pytra_int(x0)
            while ((__step_2 >= 0 && x < __pytra_int(x1)) || (__step_2 < 0 && x > __pytra_int(x1))) {
                __pytra_setIndex(frame, (__pytra_int((__pytra_int(y) * __pytra_int(w))) + __pytra_int(x)), Int64(255))
                x += __step_2
            }
            y += __step_1
        }
        i += __step_0
    }
    return __pytra_bytes(frame)
}

func run_12_sort_visualizer() {
    var w: Int64 = __pytra_int(Int64(320))
    var h: Int64 = __pytra_int(Int64(180))
    var n: Int64 = __pytra_int(Int64(124))
    var out_path: String = __pytra_str("sample/out/12_sort_visualizer.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var values: [Any] = __pytra_as_list([])
    let __step_0 = __pytra_int(Int64(1))
    var i = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && i < __pytra_int(n)) || (__step_0 < 0 && i > __pytra_int(n))) {
        values = __pytra_as_list(values); values.append((__pytra_int((__pytra_int((__pytra_int(i) * __pytra_int(Int64(37)))) + __pytra_int(Int64(19)))) % __pytra_int(n)))
        i += __step_0
    }
    var frames: [Any] = __pytra_as_list([render(values, w, h)])
    var frame_stride: Int64 = __pytra_int(Int64(16))
    var op: Int64 = __pytra_int(Int64(0))
    let __step_1 = __pytra_int(Int64(1))
    var i = __pytra_int(Int64(0))
    while ((__step_1 >= 0 && i < __pytra_int(n)) || (__step_1 < 0 && i > __pytra_int(n))) {
        var swapped: Bool = __pytra_truthy(false)
        let __step_2 = __pytra_int(Int64(1))
        var j = __pytra_int(Int64(0))
        while ((__step_2 >= 0 && j < __pytra_int((__pytra_int((__pytra_int(n) - __pytra_int(i))) - __pytra_int(Int64(1))))) || (__step_2 < 0 && j > __pytra_int((__pytra_int((__pytra_int(n) - __pytra_int(i))) - __pytra_int(Int64(1)))))) {
            if (__pytra_int(__pytra_int(__pytra_getIndex(values, j))) > __pytra_int(__pytra_int(__pytra_getIndex(values, (__pytra_int(j) + __pytra_int(Int64(1))))))) {
                let __tuple_3 = __pytra_as_list([__pytra_int(__pytra_getIndex(values, (__pytra_int(j) + __pytra_int(Int64(1))))), __pytra_int(__pytra_getIndex(values, j))])
                __pytra_setIndex(values, j, __pytra_int(__tuple_3[0]))
                __pytra_setIndex(values, (__pytra_int(j) + __pytra_int(Int64(1))), __pytra_int(__tuple_3[1]))
                swapped = __pytra_truthy(true)
            }
            if (__pytra_int((__pytra_int(op) % __pytra_int(frame_stride))) == __pytra_int(Int64(0))) {
                frames = __pytra_as_list(frames); frames.append(render(values, w, h))
            }
            op += Int64(1)
            j += __step_2
        }
        if (!swapped) {
            break
        }
        i += __step_1
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
        run_12_sort_visualizer()
    }
}
