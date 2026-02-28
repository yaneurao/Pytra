// Auto-generated Pytra Swift native source from EAST3.
import Foundation

// Runtime helpers are provided by py_runtime.swift in the same module.


// 06: Sample that sweeps Julia-set parameters and outputs a GIF.

func julia_palette() -> [Any] {
    var palette: [Any] = __pytra_as_list(__pytra_bytearray((__pytra_int(Int64(256)) * __pytra_int(Int64(3)))))
    __pytra_setIndex(palette, Int64(0), Int64(0))
    __pytra_setIndex(palette, Int64(1), Int64(0))
    __pytra_setIndex(palette, Int64(2), Int64(0))
    let __step_0 = __pytra_int(Int64(1))
    var i = __pytra_int(Int64(1))
    while ((__step_0 >= 0 && i < __pytra_int(Int64(256))) || (__step_0 < 0 && i > __pytra_int(Int64(256)))) {
        var t: Double = __pytra_float((__pytra_float((__pytra_int(i) - __pytra_int(Int64(1)))) / __pytra_float(Double(254.0))))
        var r: Int64 = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(Double(9.0)) * __pytra_float((__pytra_float(Double(1.0)) - __pytra_float(t))))) * __pytra_float(t))) * __pytra_float(t))) * __pytra_float(t))))))
        var g: Int64 = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(Double(15.0)) * __pytra_float((__pytra_float(Double(1.0)) - __pytra_float(t))))) * __pytra_float((__pytra_float(Double(1.0)) - __pytra_float(t))))) * __pytra_float(t))) * __pytra_float(t))))))
        var b: Int64 = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(Double(8.5)) * __pytra_float((__pytra_float(Double(1.0)) - __pytra_float(t))))) * __pytra_float((__pytra_float(Double(1.0)) - __pytra_float(t))))) * __pytra_float((__pytra_float(Double(1.0)) - __pytra_float(t))))) * __pytra_float(t))))))
        __pytra_setIndex(palette, (__pytra_int((__pytra_int(i) * __pytra_int(Int64(3)))) + __pytra_int(Int64(0))), r)
        __pytra_setIndex(palette, (__pytra_int((__pytra_int(i) * __pytra_int(Int64(3)))) + __pytra_int(Int64(1))), g)
        __pytra_setIndex(palette, (__pytra_int((__pytra_int(i) * __pytra_int(Int64(3)))) + __pytra_int(Int64(2))), b)
        i += __step_0
    }
    return __pytra_bytes(palette)
}

func render_frame(width: Int64, height: Int64, cr: Double, ci: Double, max_iter: Int64, phase: Int64) -> [Any] {
    var frame: [Any] = __pytra_as_list(__pytra_bytearray((__pytra_int(width) * __pytra_int(height))))
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float((__pytra_int(height) - __pytra_int(Int64(1)))))
    var __hoisted_cast_2: Double = __pytra_float(__pytra_float((__pytra_int(width) - __pytra_int(Int64(1)))))
    let __step_0 = __pytra_int(Int64(1))
    var y = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height))) {
        var row_base: Int64 = __pytra_int((__pytra_int(y) * __pytra_int(width)))
        var zy0: Double = __pytra_float((__pytra_float((-Double(1.2))) + __pytra_float((__pytra_float(Double(2.4)) * __pytra_float((__pytra_float(y) / __pytra_float(__hoisted_cast_1)))))))
        let __step_1 = __pytra_int(Int64(1))
        var x = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width))) {
            var zx: Double = __pytra_float((__pytra_float((-Double(1.8))) + __pytra_float((__pytra_float(Double(3.6)) * __pytra_float((__pytra_float(x) / __pytra_float(__hoisted_cast_2)))))))
            var zy: Double = __pytra_float(zy0)
            var i: Int64 = __pytra_int(Int64(0))
            while (__pytra_int(i) < __pytra_int(max_iter)) {
                var zx2: Double = __pytra_float((__pytra_float(zx) * __pytra_float(zx)))
                var zy2: Double = __pytra_float((__pytra_float(zy) * __pytra_float(zy)))
                if (__pytra_float((__pytra_float(zx2) + __pytra_float(zy2))) > __pytra_float(Double(4.0))) {
                    break
                }
                zy = __pytra_float((__pytra_float((__pytra_float((__pytra_float(Double(2.0)) * __pytra_float(zx))) * __pytra_float(zy))) + __pytra_float(ci)))
                zx = __pytra_float((__pytra_float((__pytra_float(zx2) - __pytra_float(zy2))) + __pytra_float(cr)))
                i += Int64(1)
            }
            if (__pytra_int(i) >= __pytra_int(max_iter)) {
                __pytra_setIndex(frame, (__pytra_int(row_base) + __pytra_int(x)), Int64(0))
            } else {
                var color_index: Int64 = __pytra_int((__pytra_int(Int64(1)) + __pytra_int((__pytra_int((__pytra_int((__pytra_int(__pytra_int((__pytra_int(i) * __pytra_int(Int64(224)))) / __pytra_int(max_iter)))) + __pytra_int(phase))) % __pytra_int(Int64(255))))))
                __pytra_setIndex(frame, (__pytra_int(row_base) + __pytra_int(x)), color_index)
            }
            x += __step_1
        }
        y += __step_0
    }
    return __pytra_bytes(frame)
}

func run_06_julia_parameter_sweep() {
    var width: Int64 = __pytra_int(Int64(320))
    var height: Int64 = __pytra_int(Int64(240))
    var frames_n: Int64 = __pytra_int(Int64(72))
    var max_iter: Int64 = __pytra_int(Int64(180))
    var out_path: String = __pytra_str("sample/out/06_julia_parameter_sweep.gif")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var frames: [Any] = __pytra_as_list([])
    var center_cr: Double = __pytra_float((-Double(0.745)))
    var center_ci: Double = __pytra_float(Double(0.186))
    var radius_cr: Double = __pytra_float(Double(0.12))
    var radius_ci: Double = __pytra_float(Double(0.1))
    var start_offset: Int64 = __pytra_int(Int64(20))
    var phase_offset: Int64 = __pytra_int(Int64(180))
    var __hoisted_cast_3: Double = __pytra_float(__pytra_float(frames_n))
    let __step_0 = __pytra_int(Int64(1))
    var i = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && i < __pytra_int(frames_n)) || (__step_0 < 0 && i > __pytra_int(frames_n))) {
        var t: Double = __pytra_float((__pytra_float((__pytra_int((__pytra_int(i) + __pytra_int(start_offset))) % __pytra_int(frames_n))) / __pytra_float(__hoisted_cast_3)))
        var angle: Double = __pytra_float(((Double(2.0) * Double.pi) * t))
        var cr: Double = __pytra_float((center_cr + (radius_cr * cos(__pytra_float(angle)))))
        var ci: Double = __pytra_float((center_ci + (radius_ci * sin(__pytra_float(angle)))))
        var phase: Int64 = __pytra_int((__pytra_int((__pytra_int(phase_offset) + __pytra_int((__pytra_int(i) * __pytra_int(Int64(5)))))) % __pytra_int(Int64(255))))
        frames = __pytra_as_list(frames); frames.append(render_frame(width, height, cr, ci, max_iter, phase))
        i += __step_0
    }
    __pytra_noop(out_path, width, height, frames, julia_palette())
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
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
