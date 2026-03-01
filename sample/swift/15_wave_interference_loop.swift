import Foundation


// 15: Sample that renders wave interference animation and writes a GIF.

func run_15_wave_interference_loop() {
    var w: Int64 = Int64(320)
    var h: Int64 = Int64(240)
    var frames_n: Int64 = Int64(96)
    var out_path: String = "sample/out/15_wave_interference_loop.gif"
    var start: Double = __pytra_perf_counter()
    var frames: [Any] = __pytra_as_list([])
    var t = __pytra_int(Int64(0))
    while (t < __pytra_int(frames_n)) {
        var frame: [Any] = __pytra_as_list(__pytra_bytearray((w * h)))
        var phase: Double = (__pytra_float(t) * Double(0.12))
        var y = __pytra_int(Int64(0))
        while (y < __pytra_int(h)) {
            var row_base: Int64 = (y * w)
            var x = __pytra_int(Int64(0))
            while (x < __pytra_int(w)) {
                var dx: Int64 = (x - Int64(160))
                var dy: Int64 = (y - Int64(120))
                var v: Any = (((sin(__pytra_float((__pytra_float(x) + (__pytra_float(t) * Double(1.5))) * Double(0.045))) + sin(__pytra_float((__pytra_float(y) - (__pytra_float(t) * Double(1.2))) * Double(0.04)))) + sin(__pytra_float((__pytra_float(x + y) * Double(0.02)) + phase))) + sin(__pytra_float((sqrt(__pytra_float((dx * dx) + (dy * dy))) * Double(0.08)) - (phase * Double(1.3)))))
                var c: Int64 = __pytra_int((v + Double(4.0)) * (Double(255.0) / Double(8.0)))
                if (__pytra_int(c) < __pytra_int(Int64(0))) {
                    c = Int64(0)
                }
                if (__pytra_int(c) > __pytra_int(Int64(255))) {
                    c = Int64(255)
                }
                __pytra_setIndex(frame, (row_base + x), c)
                x += 1
            }
            y += 1
        }
        frames.append(__pytra_bytes(frame))
        t += 1
    }
    __pytra_noop(out_path, w, h, frames, [])
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

@main
struct Main {
    static func main() {
        run_15_wave_interference_loop()
    }
}
