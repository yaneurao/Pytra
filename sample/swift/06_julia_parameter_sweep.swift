import Foundation


// 06: Sample that sweeps Julia-set parameters and outputs a GIF.

func julia_palette() -> [Any] {
    var palette: [Any] = __pytra_as_list(__pytra_bytearray((Int64(256) * Int64(3))))
    __pytra_setIndex(palette, Int64(0), Int64(0))
    __pytra_setIndex(palette, Int64(1), Int64(0))
    __pytra_setIndex(palette, Int64(2), Int64(0))
    var i = __pytra_int(Int64(1))
    while (i < __pytra_int(Int64(256))) {
        var t: Double = (__pytra_float(i - Int64(1)) / Double(254.0))
        var r: Int64 = __pytra_int(Double(255.0) * ((((Double(9.0) * (Double(1.0) - t)) * t) * t) * t))
        var g: Int64 = __pytra_int(Double(255.0) * ((((Double(15.0) * (Double(1.0) - t)) * (Double(1.0) - t)) * t) * t))
        var b: Int64 = __pytra_int(Double(255.0) * ((((Double(8.5) * (Double(1.0) - t)) * (Double(1.0) - t)) * (Double(1.0) - t)) * t))
        __pytra_setIndex(palette, ((i * Int64(3)) + Int64(0)), r)
        __pytra_setIndex(palette, ((i * Int64(3)) + Int64(1)), g)
        __pytra_setIndex(palette, ((i * Int64(3)) + Int64(2)), b)
        i += 1
    }
    return __pytra_as_list(__pytra_bytes(palette))
}

func render_frame(width: Int64, height: Int64, cr: Double, ci: Double, max_iter: Int64, phase: Int64) -> [Any] {
    var frame: [Any] = __pytra_as_list(__pytra_bytearray((width * height)))
    var __hoisted_cast_1: Double = __pytra_float(height - Int64(1))
    var __hoisted_cast_2: Double = __pytra_float(width - Int64(1))
    var y = __pytra_int(Int64(0))
    while (y < __pytra_int(height)) {
        var row_base: Int64 = (y * width)
        var zy0: Double = ((-Double(1.2)) + (Double(2.4) * (__pytra_float(y) / __hoisted_cast_1)))
        var x = __pytra_int(Int64(0))
        while (x < __pytra_int(width)) {
            var zx: Double = ((-Double(1.8)) + (Double(3.6) * (__pytra_float(x) / __hoisted_cast_2)))
            var zy: Double = zy0
            var i: Int64 = Int64(0)
            while (__pytra_int(i) < __pytra_int(max_iter)) {
                var zx2: Double = (zx * zx)
                var zy2: Double = (zy * zy)
                if (__pytra_float(zx2 + zy2) > __pytra_float(Double(4.0))) {
                    break
                }
                zy = (((Double(2.0) * zx) * zy) + ci)
                zx = ((zx2 - zy2) + cr)
                i += Int64(1)
            }
            if (__pytra_int(i) >= __pytra_int(max_iter)) {
                __pytra_setIndex(frame, (row_base + x), Int64(0))
            } else {
                var color_index: Int64 = (Int64(1) + ((((i * Int64(224)) / max_iter) + phase) % Int64(255)))
                __pytra_setIndex(frame, (row_base + x), color_index)
            }
            x += 1
        }
        y += 1
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_06_julia_parameter_sweep() {
    var width: Int64 = Int64(320)
    var height: Int64 = Int64(240)
    var frames_n: Int64 = Int64(72)
    var max_iter: Int64 = Int64(180)
    var out_path: String = "sample/out/06_julia_parameter_sweep.gif"
    var start: Double = __pytra_perf_counter()
    var frames: [Any] = __pytra_as_list([])
    var center_cr: Double = __pytra_float(-Double(0.745))
    var center_ci: Double = Double(0.186)
    var radius_cr: Double = Double(0.12)
    var radius_ci: Double = Double(0.1)
    var start_offset: Int64 = Int64(20)
    var phase_offset: Int64 = Int64(180)
    var __hoisted_cast_3: Double = __pytra_float(frames_n)
    var i = __pytra_int(Int64(0))
    while (i < __pytra_int(frames_n)) {
        var t: Double = (__pytra_float((i + start_offset) % frames_n) / __hoisted_cast_3)
        var angle: Double = __pytra_float((Double(2.0) * Double.pi) * t)
        var cr: Double = __pytra_float(center_cr + (radius_cr * cos(__pytra_float(angle))))
        var ci: Double = __pytra_float(center_ci + (radius_ci * sin(__pytra_float(angle))))
        var phase: Int64 = ((phase_offset + (i * Int64(5))) % Int64(255))
        frames.append(render_frame(width, height, cr, ci, max_iter, phase))
        i += 1
    }
    __pytra_noop(out_path, width, height, frames, julia_palette())
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

@main
struct Main {
    static func main() {
        run_06_julia_parameter_sweep()
    }
}
