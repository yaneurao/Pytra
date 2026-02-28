// Auto-generated Pytra Go native source from EAST3.
package main

import (
    "math"
)

// Runtime helpers are provided by py_runtime.go in the same package.
var _ = math.Pi


func palette() []any {
    var p []any = __pytra_as_list([]any{})
    __step_0 := __pytra_int(int64(1))
    for i := __pytra_int(int64(0)); (__step_0 >= 0 && i < __pytra_int(int64(256))) || (__step_0 < 0 && i > __pytra_int(int64(256))); i += __step_0 {
        var r int64 = __pytra_int(__pytra_min(int64(255), __pytra_int((__pytra_float(int64(20)) + __pytra_float((__pytra_float(i) * __pytra_float(float64(0.9))))))))
        var g int64 = __pytra_int(__pytra_min(int64(255), __pytra_int((__pytra_float(int64(10)) + __pytra_float((__pytra_float(i) * __pytra_float(float64(0.7))))))))
        var b int64 = __pytra_int(__pytra_min(int64(255), (__pytra_int(int64(30)) + __pytra_int(i))))
        p = append(__pytra_as_list(p), r)
        p = append(__pytra_as_list(p), g)
        p = append(__pytra_as_list(p), b)
    }
    return __pytra_as_list(__pytra_bytes(p))
}

func scene(x float64, y float64, light_x float64, light_y float64) int64 {
    var x1 float64 = __pytra_float((__pytra_float(x) + __pytra_float(float64(0.45))))
    var y1 float64 = __pytra_float((__pytra_float(y) + __pytra_float(float64(0.2))))
    var x2 float64 = __pytra_float((__pytra_float(x) - __pytra_float(float64(0.35))))
    var y2 float64 = __pytra_float((__pytra_float(y) - __pytra_float(float64(0.15))))
    var r1 float64 = __pytra_float(math.Sqrt(__pytra_float((__pytra_float((__pytra_float(x1) * __pytra_float(x1))) + __pytra_float((__pytra_float(y1) * __pytra_float(y1)))))))
    var r2 float64 = __pytra_float(math.Sqrt(__pytra_float((__pytra_float((__pytra_float(x2) * __pytra_float(x2))) + __pytra_float((__pytra_float(y2) * __pytra_float(y2)))))))
    var blob float64 = __pytra_float((math.Exp(__pytra_float((((-float64(7.0)) * r1) * r1))) + math.Exp(__pytra_float((((-float64(8.0)) * r2) * r2)))))
    var lx float64 = __pytra_float((__pytra_float(x) - __pytra_float(light_x)))
    var ly float64 = __pytra_float((__pytra_float(y) - __pytra_float(light_y)))
    var l float64 = __pytra_float(math.Sqrt(__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(lx))) + __pytra_float((__pytra_float(ly) * __pytra_float(ly)))))))
    var lit float64 = __pytra_float((__pytra_float(float64(1.0)) / __pytra_float((float64(1.0) + ((float64(3.5) * l) * l)))))
    var v int64 = __pytra_int(__pytra_int((((float64(255.0) * blob) * lit) * float64(5.0))))
    return __pytra_int(__pytra_min(int64(255), __pytra_max(int64(0), v)))
}

func run_14_raymarching_light_cycle() {
    var w int64 = __pytra_int(int64(320))
    var h int64 = __pytra_int(int64(240))
    var frames_n int64 = __pytra_int(int64(84))
    var out_path string = __pytra_str("sample/out/14_raymarching_light_cycle.gif")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var frames []any = __pytra_as_list([]any{})
    var __hoisted_cast_1 float64 = __pytra_float(__pytra_float(frames_n))
    var __hoisted_cast_2 float64 = __pytra_float(__pytra_float((__pytra_int(h) - __pytra_int(int64(1)))))
    var __hoisted_cast_3 float64 = __pytra_float(__pytra_float((__pytra_int(w) - __pytra_int(int64(1)))))
    __step_0 := __pytra_int(int64(1))
    for t := __pytra_int(int64(0)); (__step_0 >= 0 && t < __pytra_int(frames_n)) || (__step_0 < 0 && t > __pytra_int(frames_n)); t += __step_0 {
        var frame []any = __pytra_as_list(__pytra_bytearray((__pytra_int(w) * __pytra_int(h))))
        var a float64 = __pytra_float((((__pytra_float(t) / __pytra_float(__hoisted_cast_1)) * math.Pi) * float64(2.0)))
        var light_x float64 = __pytra_float((float64(0.75) * math.Cos(__pytra_float(a))))
        var light_y float64 = __pytra_float((float64(0.55) * math.Sin(__pytra_float((a * float64(1.2))))))
        __step_1 := __pytra_int(int64(1))
        for y := __pytra_int(int64(0)); (__step_1 >= 0 && y < __pytra_int(h)) || (__step_1 < 0 && y > __pytra_int(h)); y += __step_1 {
            var row_base int64 = __pytra_int((__pytra_int(y) * __pytra_int(w)))
            var py float64 = __pytra_float((__pytra_float((__pytra_float((__pytra_float(y) / __pytra_float(__hoisted_cast_2))) * __pytra_float(float64(2.0)))) - __pytra_float(float64(1.0))))
            __step_2 := __pytra_int(int64(1))
            for x := __pytra_int(int64(0)); (__step_2 >= 0 && x < __pytra_int(w)) || (__step_2 < 0 && x > __pytra_int(w)); x += __step_2 {
                var px float64 = __pytra_float((__pytra_float((__pytra_float((__pytra_float(x) / __pytra_float(__hoisted_cast_3))) * __pytra_float(float64(2.0)))) - __pytra_float(float64(1.0))))
                __pytra_set_index(frame, (__pytra_int(row_base) + __pytra_int(x)), scene(px, py, light_x, light_y))
            }
        }
        frames = append(__pytra_as_list(frames), __pytra_bytes(frame))
    }
    __pytra_noop(out_path, w, h, frames, palette())
    var elapsed float64 = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_14_raymarching_light_cycle()
}
