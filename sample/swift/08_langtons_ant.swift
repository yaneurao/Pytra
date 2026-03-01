import Foundation


// 08: Sample that outputs Langton's Ant trajectories as a GIF.

func capture(grid: [Any], w: Int64, h: Int64) -> [Any] {
    var frame: [Any] = __pytra_as_list(__pytra_bytearray((w * h)))
    var y = __pytra_int(Int64(0))
    while (y < __pytra_int(h)) {
        var row_base: Int64 = (y * w)
        var x = __pytra_int(Int64(0))
        while (x < __pytra_int(w)) {
            __pytra_setIndex(frame, (row_base + x), __pytra_ifexp((__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(grid, y)), x)) != 0), Int64(255), Int64(0)))
            x += 1
        }
        y += 1
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_08_langtons_ant() {
    var w: Int64 = Int64(420)
    var h: Int64 = Int64(420)
    var out_path: String = "sample/out/08_langtons_ant.gif"
    var start: Double = __pytra_perf_counter()
    var grid: [Any] = __pytra_as_list(({ () -> [Any] in var __out: [Any] = []; let __step = __pytra_int(Int64(1)); var __lc_i = __pytra_int(Int64(0)); while ((__step >= 0 && __lc_i < __pytra_int(h)) || (__step < 0 && __lc_i > __pytra_int(h))) { __out.append(__pytra_list_repeat(Int64(0), w)); __lc_i += __step }; return __out })())
    var x: Int64 = (w / Int64(2))
    var y: Int64 = (h / Int64(2))
    var d: Int64 = Int64(0)
    var steps_total: Int64 = Int64(600000)
    var capture_every: Int64 = Int64(3000)
    var frames: [Any] = __pytra_as_list([])
    var i = __pytra_int(Int64(0))
    while (i < __pytra_int(steps_total)) {
        if (__pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(grid, y)), x)) == __pytra_int(Int64(0))) {
            d = ((d + Int64(1)) % Int64(4))
            __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, y)), x, Int64(1))
        } else {
            d = ((d + Int64(3)) % Int64(4))
            __pytra_setIndex(__pytra_as_list(__pytra_getIndex(grid, y)), x, Int64(0))
        }
        if (__pytra_int(d) == __pytra_int(Int64(0))) {
            y = (((y - Int64(1)) + h) % h)
        } else {
            if (__pytra_int(d) == __pytra_int(Int64(1))) {
                x = ((x + Int64(1)) % w)
            } else {
                if (__pytra_int(d) == __pytra_int(Int64(2))) {
                    y = ((y + Int64(1)) % h)
                } else {
                    x = (((x - Int64(1)) + w) % w)
                }
            }
        }
        if (__pytra_int(i % capture_every) == __pytra_int(Int64(0))) {
            frames.append(capture(grid, w, h))
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
        run_08_langtons_ant()
    }
}
