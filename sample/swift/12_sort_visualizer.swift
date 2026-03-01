import Foundation


// 12: Sample that outputs intermediate states of bubble sort as a GIF.

func render(values: [Any], w: Int64, h: Int64) -> [Any] {
    var frame: [Any] = __pytra_as_list(__pytra_bytearray((w * h)))
    var n: Int64 = __pytra_len(values)
    var bar_w: Double = (__pytra_float(w) / __pytra_float(n))
    var __hoisted_cast_1: Double = __pytra_float(n)
    var __hoisted_cast_2: Double = __pytra_float(h)
    var i = __pytra_int(Int64(0))
    while (i < __pytra_int(n)) {
        var x0: Int64 = __pytra_int(__pytra_float(i) * bar_w)
        var x1: Int64 = __pytra_int(__pytra_float(i + Int64(1)) * bar_w)
        if (__pytra_int(x1) <= __pytra_int(x0)) {
            x1 = (x0 + Int64(1))
        }
        var bh: Int64 = __pytra_int((__pytra_float(__pytra_int(__pytra_getIndex(values, i))) / __hoisted_cast_1) * __hoisted_cast_2)
        var y: Int64 = (h - bh)
        var y = __pytra_int(y)
        while (y < __pytra_int(h)) {
            var x = __pytra_int(x0)
            while (x < __pytra_int(x1)) {
                __pytra_setIndex(frame, ((y * w) + x), Int64(255))
                x += 1
            }
            y += 1
        }
        i += 1
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_12_sort_visualizer() {
    var w: Int64 = Int64(320)
    var h: Int64 = Int64(180)
    var n: Int64 = Int64(124)
    var out_path: String = "sample/out/12_sort_visualizer.gif"
    var start: Double = __pytra_perf_counter()
    var values: [Any] = __pytra_as_list([])
    var i = __pytra_int(Int64(0))
    while (i < __pytra_int(n)) {
        values.append((((i * Int64(37)) + Int64(19)) % n))
        i += 1
    }
    var frames: [Any] = __pytra_as_list([render(values, w, h)])
    var frame_stride: Int64 = Int64(16)
    var op: Int64 = Int64(0)
    var i = __pytra_int(Int64(0))
    while (i < __pytra_int(n)) {
        var swapped: Bool = false
        var j = __pytra_int(Int64(0))
        while (j < __pytra_int((n - i) - Int64(1))) {
            if (__pytra_int(__pytra_getIndex(values, j)) > __pytra_int(__pytra_getIndex(values, (j + Int64(1))))) {
                let __tuple_3 = __pytra_as_list([__pytra_int(__pytra_getIndex(values, (j + Int64(1)))), __pytra_int(__pytra_getIndex(values, j))])
                __pytra_setIndex(values, j, __pytra_int(__tuple_3[0]))
                __pytra_setIndex(values, (j + Int64(1)), __pytra_int(__tuple_3[1]))
                swapped = true
            }
            if (__pytra_int(op % frame_stride) == __pytra_int(Int64(0))) {
                frames.append(render(values, w, h))
            }
            op += Int64(1)
            j += 1
        }
        if (!swapped) {
            break
        }
        i += 1
    }
    __pytra_noop(out_path, w, h, frames, [])
    var elapsed: Double = (__pytra_perf_counter() - start)
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
