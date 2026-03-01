import Foundation


// 14: Sample that outputs a moving-light scene in a simple raymarching style as a GIF.

func palette() -> [Any] {
    var p: [Any] = __pytra_as_list([])
    var i = __pytra_int(Int64(0))
    while (i < __pytra_int(Int64(256))) {
        var r: Int64 = __pytra_int(__pytra_min(Int64(255), __pytra_int(__pytra_float(Int64(20)) + (__pytra_float(i) * Double(0.9)))))
        var g: Int64 = __pytra_int(__pytra_min(Int64(255), __pytra_int(__pytra_float(Int64(10)) + (__pytra_float(i) * Double(0.7)))))
        var b: Int64 = __pytra_int(__pytra_min(Int64(255), (Int64(30) + i)))
        p.append(r)
        p.append(g)
        p.append(b)
        i += 1
    }
    return __pytra_as_list(__pytra_bytes(p))
}

func scene(x: Double, y: Double, light_x: Double, light_y: Double) -> Int64 {
    var x1: Double = (x + Double(0.45))
    var y1: Double = (y + Double(0.2))
    var x2: Double = (x - Double(0.35))
    var y2: Double = (y - Double(0.15))
    var r1: Any = sqrt(__pytra_float((x1 * x1) + (y1 * y1)))
    var r2: Any = sqrt(__pytra_float((x2 * x2) + (y2 * y2)))
    var blob: Any = (exp(__pytra_float(((-Double(7.0)) * r1) * r1)) + exp(__pytra_float(((-Double(8.0)) * r2) * r2)))
    var lx: Double = (x - light_x)
    var ly: Double = (y - light_y)
    var l: Any = sqrt(__pytra_float((lx * lx) + (ly * ly)))
    var lit: Double = __pytra_float(Double(1.0) / __pytra_float(Double(1.0) + ((Double(3.5) * l) * l)))
    var v: Int64 = __pytra_int(((Double(255.0) * blob) * lit) * Double(5.0))
    return __pytra_int(__pytra_min(Int64(255), __pytra_max(Int64(0), v)))
}

func run_14_raymarching_light_cycle() {
    var w: Int64 = Int64(320)
    var h: Int64 = Int64(240)
    var frames_n: Int64 = Int64(84)
    var out_path: String = "sample/out/14_raymarching_light_cycle.gif"
    var start: Double = __pytra_perf_counter()
    var frames: [Any] = __pytra_as_list([])
    var __hoisted_cast_1: Double = __pytra_float(frames_n)
    var __hoisted_cast_2: Double = __pytra_float(h - Int64(1))
    var __hoisted_cast_3: Double = __pytra_float(w - Int64(1))
    var t = __pytra_int(Int64(0))
    while (t < __pytra_int(frames_n)) {
        var frame: [Any] = __pytra_as_list(__pytra_bytearray((w * h)))
        var a: Double = __pytra_float(((__pytra_float(t) / __hoisted_cast_1) * Double.pi) * Double(2.0))
        var light_x: Double = __pytra_float(Double(0.75) * cos(__pytra_float(a)))
        var light_y: Double = __pytra_float(Double(0.55) * sin(__pytra_float(a * Double(1.2))))
        var y = __pytra_int(Int64(0))
        while (y < __pytra_int(h)) {
            var row_base: Int64 = (y * w)
            var py: Double = (((__pytra_float(y) / __hoisted_cast_2) * Double(2.0)) - Double(1.0))
            var x = __pytra_int(Int64(0))
            while (x < __pytra_int(w)) {
                var px: Double = (((__pytra_float(x) / __hoisted_cast_3) * Double(2.0)) - Double(1.0))
                __pytra_setIndex(frame, (row_base + x), scene(px, py, light_x, light_y))
                x += 1
            }
            y += 1
        }
        frames.append(__pytra_bytes(frame))
        t += 1
    }
    __pytra_noop(out_path, w, h, frames, palette())
    var elapsed: Double = (__pytra_perf_counter() - start)
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
