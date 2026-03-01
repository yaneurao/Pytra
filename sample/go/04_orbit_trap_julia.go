package main


// 04: Sample that renders an orbit-trap Julia set and writes a PNG image.

func render_orbit_trap_julia(width int64, height int64, max_iter int64, cx float64, cy float64) []any {
    var pixels []any = __pytra_as_list([]any{})
    var __hoisted_cast_1 float64 = __pytra_float((height - int64(1)))
    var __hoisted_cast_2 float64 = __pytra_float((width - int64(1)))
    var __hoisted_cast_3 float64 = __pytra_float(max_iter)
    for y := int64(0); y < height; y += 1 {
        var zy0 float64 = ((-float64(1.3)) + (float64(2.6) * (float64(y) / __hoisted_cast_1)))
        for x := int64(0); x < width; x += 1 {
            var zx float64 = ((-float64(1.9)) + (float64(3.8) * (float64(x) / __hoisted_cast_2)))
            var zy float64 = zy0
            var trap float64 = float64(1000000000.0)
            var i int64 = int64(0)
            for (i < max_iter) {
                var ax float64 = zx
                if (ax < float64(0.0)) {
                    ax = (-ax)
                }
                var ay float64 = zy
                if (ay < float64(0.0)) {
                    ay = (-ay)
                }
                var dxy float64 = (zx - zy)
                if (dxy < float64(0.0)) {
                    dxy = (-dxy)
                }
                if (ax < trap) {
                    trap = ax
                }
                if (ay < trap) {
                    trap = ay
                }
                if (dxy < trap) {
                    trap = dxy
                }
                var zx2 float64 = (zx * zx)
                var zy2 float64 = (zy * zy)
                if ((zx2 + zy2) > float64(4.0)) {
                    break
                }
                zy = (((float64(2.0) * zx) * zy) + cy)
                zx = ((zx2 - zy2) + cx)
                i += int64(1)
            }
            var r int64 = int64(0)
            var g int64 = int64(0)
            var b int64 = int64(0)
            if (i >= max_iter) {
                r = int64(0)
                g = int64(0)
                b = int64(0)
            } else {
                var trap_scaled float64 = (trap * float64(3.2))
                if (trap_scaled > float64(1.0)) {
                    trap_scaled = float64(1.0)
                }
                if (trap_scaled < float64(0.0)) {
                    trap_scaled = float64(0.0)
                }
                var t float64 = (float64(i) / __hoisted_cast_3)
                var tone int64 = __pytra_int((float64(255.0) * (float64(1.0) - trap_scaled)))
                r = __pytra_int((float64(tone) * (float64(0.35) + (float64(0.65) * t))))
                g = __pytra_int((float64(tone) * (float64(0.15) + (float64(0.85) * (float64(1.0) - t)))))
                b = __pytra_int((float64(255.0) * (float64(0.25) + (float64(0.75) * t))))
                if (r > int64(255)) {
                    r = int64(255)
                }
                if (g > int64(255)) {
                    g = int64(255)
                }
                if (b > int64(255)) {
                    b = int64(255)
                }
            }
            pixels = append(pixels, r)
            pixels = append(pixels, g)
            pixels = append(pixels, b)
        }
    }
    return __pytra_as_list(pixels)
}

func run_04_orbit_trap_julia() {
    var width int64 = int64(1920)
    var height int64 = int64(1080)
    var max_iter int64 = int64(1400)
    var out_path string = __pytra_str("sample/out/04_orbit_trap_julia.png")
    var start float64 = __pytra_perf_counter()
    var pixels []any = __pytra_as_list(render_orbit_trap_julia(width, height, max_iter, (-float64(0.7269)), float64(0.1889)))
    __pytra_write_rgb_png(out_path, width, height, pixels)
    var elapsed float64 = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_04_orbit_trap_julia()
}
