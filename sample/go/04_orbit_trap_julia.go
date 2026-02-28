package main

import (
    "math"
)

var _ = math.Pi


// 04: Sample that renders an orbit-trap Julia set and writes a PNG image.

func render_orbit_trap_julia(width int64, height int64, max_iter int64, cx float64, cy float64) []any {
    var pixels []any = __pytra_as_list([]any{})
    var __hoisted_cast_1 float64 = __pytra_float(__pytra_float((__pytra_int(height) - __pytra_int(int64(1)))))
    var __hoisted_cast_2 float64 = __pytra_float(__pytra_float((__pytra_int(width) - __pytra_int(int64(1)))))
    var __hoisted_cast_3 float64 = __pytra_float(__pytra_float(max_iter))
    __step_0 := __pytra_int(int64(1))
    for y := __pytra_int(int64(0)); (__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height)); y += __step_0 {
        var zy0 float64 = __pytra_float((__pytra_float((-float64(1.3))) + __pytra_float((__pytra_float(float64(2.6)) * __pytra_float((__pytra_float(y) / __pytra_float(__hoisted_cast_1)))))))
        __step_1 := __pytra_int(int64(1))
        for x := __pytra_int(int64(0)); (__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width)); x += __step_1 {
            var zx float64 = __pytra_float((__pytra_float((-float64(1.9))) + __pytra_float((__pytra_float(float64(3.8)) * __pytra_float((__pytra_float(x) / __pytra_float(__hoisted_cast_2)))))))
            var zy float64 = __pytra_float(zy0)
            var trap float64 = __pytra_float(float64(1000000000.0))
            var i int64 = __pytra_int(int64(0))
            for (__pytra_int(i) < __pytra_int(max_iter)) {
                var ax float64 = __pytra_float(zx)
                if (__pytra_float(ax) < __pytra_float(float64(0.0))) {
                    ax = __pytra_float((-ax))
                }
                var ay float64 = __pytra_float(zy)
                if (__pytra_float(ay) < __pytra_float(float64(0.0))) {
                    ay = __pytra_float((-ay))
                }
                var dxy float64 = __pytra_float((__pytra_float(zx) - __pytra_float(zy)))
                if (__pytra_float(dxy) < __pytra_float(float64(0.0))) {
                    dxy = __pytra_float((-dxy))
                }
                if (__pytra_float(ax) < __pytra_float(trap)) {
                    trap = __pytra_float(ax)
                }
                if (__pytra_float(ay) < __pytra_float(trap)) {
                    trap = __pytra_float(ay)
                }
                if (__pytra_float(dxy) < __pytra_float(trap)) {
                    trap = __pytra_float(dxy)
                }
                var zx2 float64 = __pytra_float((__pytra_float(zx) * __pytra_float(zx)))
                var zy2 float64 = __pytra_float((__pytra_float(zy) * __pytra_float(zy)))
                if (__pytra_float((__pytra_float(zx2) + __pytra_float(zy2))) > __pytra_float(float64(4.0))) {
                    break
                }
                zy = __pytra_float((__pytra_float((__pytra_float((__pytra_float(float64(2.0)) * __pytra_float(zx))) * __pytra_float(zy))) + __pytra_float(cy)))
                zx = __pytra_float((__pytra_float((__pytra_float(zx2) - __pytra_float(zy2))) + __pytra_float(cx)))
                i += int64(1)
            }
            var r int64 = __pytra_int(int64(0))
            var g int64 = __pytra_int(int64(0))
            var b int64 = __pytra_int(int64(0))
            if (__pytra_int(i) >= __pytra_int(max_iter)) {
                r = __pytra_int(int64(0))
                g = __pytra_int(int64(0))
                b = __pytra_int(int64(0))
            } else {
                var trap_scaled float64 = __pytra_float((__pytra_float(trap) * __pytra_float(float64(3.2))))
                if (__pytra_float(trap_scaled) > __pytra_float(float64(1.0))) {
                    trap_scaled = __pytra_float(float64(1.0))
                }
                if (__pytra_float(trap_scaled) < __pytra_float(float64(0.0))) {
                    trap_scaled = __pytra_float(float64(0.0))
                }
                var t float64 = __pytra_float((__pytra_float(i) / __pytra_float(__hoisted_cast_3)))
                var tone int64 = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float((__pytra_float(float64(1.0)) - __pytra_float(trap_scaled))))))
                r = __pytra_int(__pytra_int((__pytra_float(tone) * __pytra_float((__pytra_float(float64(0.35)) + __pytra_float((__pytra_float(float64(0.65)) * __pytra_float(t))))))))
                g = __pytra_int(__pytra_int((__pytra_float(tone) * __pytra_float((__pytra_float(float64(0.15)) + __pytra_float((__pytra_float(float64(0.85)) * __pytra_float((__pytra_float(float64(1.0)) - __pytra_float(t))))))))))
                b = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float((__pytra_float(float64(0.25)) + __pytra_float((__pytra_float(float64(0.75)) * __pytra_float(t))))))))
                if (__pytra_int(r) > __pytra_int(int64(255))) {
                    r = __pytra_int(int64(255))
                }
                if (__pytra_int(g) > __pytra_int(int64(255))) {
                    g = __pytra_int(int64(255))
                }
                if (__pytra_int(b) > __pytra_int(int64(255))) {
                    b = __pytra_int(int64(255))
                }
            }
            pixels = append(__pytra_as_list(pixels), r)
            pixels = append(__pytra_as_list(pixels), g)
            pixels = append(__pytra_as_list(pixels), b)
        }
    }
    return __pytra_as_list(pixels)
}

func run_04_orbit_trap_julia() {
    var width int64 = __pytra_int(int64(1920))
    var height int64 = __pytra_int(int64(1080))
    var max_iter int64 = __pytra_int(int64(1400))
    var out_path string = __pytra_str("sample/out/04_orbit_trap_julia.png")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var pixels []any = __pytra_as_list(render_orbit_trap_julia(width, height, max_iter, (-float64(0.7269)), float64(0.1889)))
    __pytra_noop(out_path, width, height, pixels)
    var elapsed float64 = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_04_orbit_trap_julia()
}
