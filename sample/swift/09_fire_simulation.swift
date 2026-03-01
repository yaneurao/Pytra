import Foundation


// 09: Sample that outputs a simple fire effect as a GIF.

func fire_palette() -> [Any] {
    var p: [Any] = __pytra_as_list([])
    var i = __pytra_int(Int64(0))
    while (i < __pytra_int(Int64(256))) {
        var r: Int64 = Int64(0)
        var g: Int64 = Int64(0)
        var b: Int64 = Int64(0)
        if (__pytra_int(i) < __pytra_int(Int64(85))) {
            r = (i * Int64(3))
            g = Int64(0)
            b = Int64(0)
        } else {
            if (__pytra_int(i) < __pytra_int(Int64(170))) {
                r = Int64(255)
                g = ((i - Int64(85)) * Int64(3))
                b = Int64(0)
            } else {
                r = Int64(255)
                g = Int64(255)
                b = ((i - Int64(170)) * Int64(3))
            }
        }
        p.append(r)
        p.append(g)
        p.append(b)
        i += 1
    }
    return __pytra_as_list(__pytra_bytes(p))
}

func run_09_fire_simulation() {
    var w: Int64 = Int64(380)
    var h: Int64 = Int64(260)
    var steps: Int64 = Int64(420)
    var out_path: String = "sample/out/09_fire_simulation.gif"
    var start: Double = __pytra_perf_counter()
    var heat: [Any] = __pytra_as_list(({ () -> [Any] in var __out: [Any] = []; let __step = __pytra_int(Int64(1)); var __lc_i = __pytra_int(Int64(0)); while ((__step >= 0 && __lc_i < __pytra_int(h)) || (__step < 0 && __lc_i > __pytra_int(h))) { __out.append(__pytra_list_repeat(Int64(0), w)); __lc_i += __step }; return __out })())
    var frames: [Any] = __pytra_as_list([])
    var t = __pytra_int(Int64(0))
    while (t < __pytra_int(steps)) {
        var x = __pytra_int(Int64(0))
        while (x < __pytra_int(w)) {
            var val: Int64 = (Int64(170) + (((x * Int64(13)) + (t * Int64(17))) % Int64(86)))
            __pytra_setIndex(__pytra_as_list(__pytra_getIndex(heat, (h - Int64(1)))), x, val)
            x += 1
        }
        var y = __pytra_int(Int64(1))
        while (y < __pytra_int(h)) {
            var x = __pytra_int(Int64(0))
            while (x < __pytra_int(w)) {
                var a: Int64 = __pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(heat, y)), x))
                var b: Int64 = __pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(heat, y)), (((x - Int64(1)) + w) % w)))
                var c: Int64 = __pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(heat, y)), ((x + Int64(1)) % w)))
                var d: Int64 = __pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(heat, ((y + Int64(1)) % h))), x))
                var v: Int64 = ((((a + b) + c) + d) / Int64(4))
                var cool: Int64 = (Int64(1) + (((x + y) + t) % Int64(3)))
                var nv: Int64 = (v - cool)
                __pytra_setIndex(__pytra_as_list(__pytra_getIndex(heat, (y - Int64(1)))), x, __pytra_ifexp((__pytra_int(nv) > __pytra_int(Int64(0))), nv, Int64(0)))
                x += 1
            }
            y += 1
        }
        var frame: [Any] = __pytra_as_list(__pytra_bytearray((w * h)))
        var yy = __pytra_int(Int64(0))
        while (yy < __pytra_int(h)) {
            var row_base: Int64 = (yy * w)
            var xx = __pytra_int(Int64(0))
            while (xx < __pytra_int(w)) {
                __pytra_setIndex(frame, (row_base + xx), __pytra_int(__pytra_getIndex(__pytra_as_list(__pytra_getIndex(heat, yy)), xx)))
                xx += 1
            }
            yy += 1
        }
        frames.append(__pytra_bytes(frame))
        t += 1
    }
    __pytra_noop(out_path, w, h, frames, fire_palette())
    var elapsed: Double = (__pytra_perf_counter() - start)
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
