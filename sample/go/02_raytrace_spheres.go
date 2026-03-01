package main

import (
    "math"
)


// 02: Sample that runs a mini sphere-only ray tracer and outputs a PNG image.
// Dependencies are kept minimal (time only) for transpilation compatibility.

func clamp01(v float64) float64 {
    if (v < float64(0.0)) {
        return float64(0.0)
    }
    if (v > float64(1.0)) {
        return float64(1.0)
    }
    return v
}

func hit_sphere(ox float64, oy float64, oz float64, dx float64, dy float64, dz float64, cx float64, cy float64, cz float64, r float64) float64 {
    var lx float64 = (ox - cx)
    var ly float64 = (oy - cy)
    var lz float64 = (oz - cz)
    var a float64 = (((dx * dx) + (dy * dy)) + (dz * dz))
    var b float64 = (float64(2.0) * (((lx * dx) + (ly * dy)) + (lz * dz)))
    var c float64 = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (r * r))
    var d float64 = ((b * b) - ((float64(4.0) * a) * c))
    if (d < float64(0.0)) {
        return (-float64(1.0))
    }
    var sd float64 = math.Sqrt(d)
    var t0 float64 = (((-b) - sd) / (float64(2.0) * a))
    var t1 float64 = (((-b) + sd) / (float64(2.0) * a))
    if (t0 > float64(0.001)) {
        return t0
    }
    if (t1 > float64(0.001)) {
        return t1
    }
    return (-float64(1.0))
}

func render(width int64, height int64, aa int64) []any {
    var pixels []any = __pytra_as_list([]any{})
    var ox float64 = float64(0.0)
    var oy float64 = float64(0.0)
    var oz float64 = (-float64(3.0))
    var lx float64 = (-float64(0.4))
    var ly float64 = float64(0.8)
    var lz float64 = (-float64(0.45))
    var __hoisted_cast_1 float64 = __pytra_float(aa)
    var __hoisted_cast_2 float64 = __pytra_float((height - int64(1)))
    var __hoisted_cast_3 float64 = __pytra_float((width - int64(1)))
    var __hoisted_cast_4 float64 = __pytra_float(height)
    for y := int64(0); y < height; y += 1 {
        for x := int64(0); x < width; x += 1 {
            var ar int64 = int64(0)
            var ag int64 = int64(0)
            var ab int64 = int64(0)
            for ay := int64(0); ay < aa; ay += 1 {
                for ax := int64(0); ax < aa; ax += 1 {
                    var fy float64 = ((float64(y) + ((float64(ay) + float64(0.5)) / __hoisted_cast_1)) / __hoisted_cast_2)
                    var fx float64 = ((float64(x) + ((float64(ax) + float64(0.5)) / __hoisted_cast_1)) / __hoisted_cast_3)
                    var sy float64 = (float64(1.0) - (float64(2.0) * fy))
                    var sx float64 = (((float64(2.0) * fx) - float64(1.0)) * (float64(width) / __hoisted_cast_4))
                    var dx float64 = sx
                    var dy float64 = sy
                    var dz float64 = float64(1.0)
                    var inv_len float64 = (float64(1.0) / __pytra_float(math.Sqrt((((dx * dx) + (dy * dy)) + (dz * dz)))))
                    dx *= inv_len
                    dy *= inv_len
                    dz *= inv_len
                    var t_min float64 = float64(1e+30)
                    var hit_id int64 = (-int64(1))
                    var t float64 = hit_sphere(ox, oy, oz, dx, dy, dz, (-float64(0.8)), (-float64(0.2)), float64(2.2), float64(0.8))
                    if ((t > float64(0.0)) && (t < t_min)) {
                        t_min = t
                        hit_id = int64(0)
                    }
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, float64(0.9), float64(0.1), float64(2.9), float64(0.95))
                    if ((t > float64(0.0)) && (t < t_min)) {
                        t_min = t
                        hit_id = int64(1)
                    }
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, float64(0.0), (-float64(1001.0)), float64(3.0), float64(1000.0))
                    if ((t > float64(0.0)) && (t < t_min)) {
                        t_min = t
                        hit_id = int64(2)
                    }
                    var r int64 = int64(0)
                    var g int64 = int64(0)
                    var b int64 = int64(0)
                    if (hit_id >= int64(0)) {
                        var px float64 = (ox + (dx * t_min))
                        var py float64 = (oy + (dy * t_min))
                        var pz float64 = (oz + (dz * t_min))
                        var nx float64 = float64(0.0)
                        var ny float64 = float64(0.0)
                        var nz float64 = float64(0.0)
                        if (hit_id == int64(0)) {
                            nx = ((px + float64(0.8)) / float64(0.8))
                            ny = ((py + float64(0.2)) / float64(0.8))
                            nz = ((pz - float64(2.2)) / float64(0.8))
                        } else {
                            if (hit_id == int64(1)) {
                                nx = ((px - float64(0.9)) / float64(0.95))
                                ny = ((py - float64(0.1)) / float64(0.95))
                                nz = ((pz - float64(2.9)) / float64(0.95))
                            } else {
                                nx = float64(0.0)
                                ny = float64(1.0)
                                nz = float64(0.0)
                            }
                        }
                        var diff float64 = (((nx * (-lx)) + (ny * (-ly))) + (nz * (-lz)))
                        diff = clamp01(diff)
                        var base_r float64 = float64(0.0)
                        var base_g float64 = float64(0.0)
                        var base_b float64 = float64(0.0)
                        if (hit_id == int64(0)) {
                            base_r = float64(0.95)
                            base_g = float64(0.35)
                            base_b = float64(0.25)
                        } else {
                            if (hit_id == int64(1)) {
                                base_r = float64(0.25)
                                base_g = float64(0.55)
                                base_b = float64(0.95)
                            } else {
                                var checker int64 = (__pytra_int(((px + float64(50.0)) * float64(0.8))) + __pytra_int(((pz + float64(50.0)) * float64(0.8))))
                                if ((checker % int64(2)) == int64(0)) {
                                    base_r = float64(0.85)
                                    base_g = float64(0.85)
                                    base_b = float64(0.85)
                                } else {
                                    base_r = float64(0.2)
                                    base_g = float64(0.2)
                                    base_b = float64(0.2)
                                }
                            }
                        }
                        var shade float64 = (float64(0.12) + (float64(0.88) * diff))
                        r = __pytra_int((float64(255.0) * clamp01((base_r * shade))))
                        g = __pytra_int((float64(255.0) * clamp01((base_g * shade))))
                        b = __pytra_int((float64(255.0) * clamp01((base_b * shade))))
                    } else {
                        var tsky float64 = (float64(0.5) * (dy + float64(1.0)))
                        r = __pytra_int((float64(255.0) * (float64(0.65) + (float64(0.2) * tsky))))
                        g = __pytra_int((float64(255.0) * (float64(0.75) + (float64(0.18) * tsky))))
                        b = __pytra_int((float64(255.0) * (float64(0.9) + (float64(0.08) * tsky))))
                    }
                    ar += r
                    ag += g
                    ab += b
                }
            }
            var samples int64 = (aa * aa)
            pixels = append(__pytra_as_list(pixels), __pytra_int((ar / samples)))
            pixels = append(__pytra_as_list(pixels), __pytra_int((ag / samples)))
            pixels = append(__pytra_as_list(pixels), __pytra_int((ab / samples)))
        }
    }
    return __pytra_as_list(pixels)
}

func run_raytrace() {
    var width int64 = int64(1600)
    var height int64 = int64(900)
    var aa int64 = int64(2)
    var out_path string = __pytra_str("sample/out/02_raytrace_spheres.png")
    var start float64 = __pytra_perf_counter()
    var pixels []any = __pytra_as_list(render(width, height, aa))
    __pytra_write_rgb_png(out_path, width, height, pixels)
    var elapsed float64 = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_raytrace()
}
