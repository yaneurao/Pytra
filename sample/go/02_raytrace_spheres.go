// Auto-generated Pytra Go native source from EAST3.
package main

import (
    "math"
)

// Runtime helpers are provided by py_runtime.go in the same package.
var _ = math.Pi


func clamp01(v float64) float64 {
    if (__pytra_float(v) < __pytra_float(float64(0.0))) {
        return __pytra_float(float64(0.0))
    }
    if (__pytra_float(v) > __pytra_float(float64(1.0))) {
        return __pytra_float(float64(1.0))
    }
    return __pytra_float(v)
}

func hit_sphere(ox float64, oy float64, oz float64, dx float64, dy float64, dz float64, cx float64, cy float64, cz float64, r float64) float64 {
    var lx float64 = __pytra_float((__pytra_float(ox) - __pytra_float(cx)))
    var ly float64 = __pytra_float((__pytra_float(oy) - __pytra_float(cy)))
    var lz float64 = __pytra_float((__pytra_float(oz) - __pytra_float(cz)))
    var a float64 = __pytra_float((__pytra_float((__pytra_float((__pytra_float(dx) * __pytra_float(dx))) + __pytra_float((__pytra_float(dy) * __pytra_float(dy))))) + __pytra_float((__pytra_float(dz) * __pytra_float(dz)))))
    var b float64 = __pytra_float((__pytra_float(float64(2.0)) * __pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(dx))) + __pytra_float((__pytra_float(ly) * __pytra_float(dy))))) + __pytra_float((__pytra_float(lz) * __pytra_float(dz)))))))
    var c float64 = __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(lx))) + __pytra_float((__pytra_float(ly) * __pytra_float(ly))))) + __pytra_float((__pytra_float(lz) * __pytra_float(lz))))) - __pytra_float((__pytra_float(r) * __pytra_float(r)))))
    var d float64 = __pytra_float((__pytra_float((__pytra_float(b) * __pytra_float(b))) - __pytra_float((__pytra_float((__pytra_float(float64(4.0)) * __pytra_float(a))) * __pytra_float(c)))))
    if (__pytra_float(d) < __pytra_float(float64(0.0))) {
        return __pytra_float((-float64(1.0)))
    }
    var sd float64 = __pytra_float(math.Sqrt(__pytra_float(d)))
    var t0 float64 = __pytra_float((__pytra_float((__pytra_float((-b)) - __pytra_float(sd))) / __pytra_float((__pytra_float(float64(2.0)) * __pytra_float(a)))))
    var t1 float64 = __pytra_float((__pytra_float((__pytra_float((-b)) + __pytra_float(sd))) / __pytra_float((__pytra_float(float64(2.0)) * __pytra_float(a)))))
    if (__pytra_float(t0) > __pytra_float(float64(0.001))) {
        return __pytra_float(t0)
    }
    if (__pytra_float(t1) > __pytra_float(float64(0.001))) {
        return __pytra_float(t1)
    }
    return __pytra_float((-float64(1.0)))
}

func render(width int64, height int64, aa int64) []any {
    var pixels []any = __pytra_as_list([]any{})
    var ox float64 = __pytra_float(float64(0.0))
    var oy float64 = __pytra_float(float64(0.0))
    var oz float64 = __pytra_float((-float64(3.0)))
    var lx float64 = __pytra_float((-float64(0.4)))
    var ly float64 = __pytra_float(float64(0.8))
    var lz float64 = __pytra_float((-float64(0.45)))
    var __hoisted_cast_1 float64 = __pytra_float(__pytra_float(aa))
    var __hoisted_cast_2 float64 = __pytra_float(__pytra_float((__pytra_int(height) - __pytra_int(int64(1)))))
    var __hoisted_cast_3 float64 = __pytra_float(__pytra_float((__pytra_int(width) - __pytra_int(int64(1)))))
    var __hoisted_cast_4 float64 = __pytra_float(__pytra_float(height))
    __step_0 := __pytra_int(int64(1))
    for y := __pytra_int(int64(0)); (__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height)); y += __step_0 {
        __step_1 := __pytra_int(int64(1))
        for x := __pytra_int(int64(0)); (__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width)); x += __step_1 {
            var ar int64 = __pytra_int(int64(0))
            var ag int64 = __pytra_int(int64(0))
            var ab int64 = __pytra_int(int64(0))
            __step_2 := __pytra_int(int64(1))
            for ay := __pytra_int(int64(0)); (__step_2 >= 0 && ay < __pytra_int(aa)) || (__step_2 < 0 && ay > __pytra_int(aa)); ay += __step_2 {
                __step_3 := __pytra_int(int64(1))
                for ax := __pytra_int(int64(0)); (__step_3 >= 0 && ax < __pytra_int(aa)) || (__step_3 < 0 && ax > __pytra_int(aa)); ax += __step_3 {
                    var fy float64 = __pytra_float((__pytra_float((__pytra_float(y) + __pytra_float((__pytra_float((__pytra_float(ay) + __pytra_float(float64(0.5)))) / __pytra_float(__hoisted_cast_1))))) / __pytra_float(__hoisted_cast_2)))
                    var fx float64 = __pytra_float((__pytra_float((__pytra_float(x) + __pytra_float((__pytra_float((__pytra_float(ax) + __pytra_float(float64(0.5)))) / __pytra_float(__hoisted_cast_1))))) / __pytra_float(__hoisted_cast_3)))
                    var sy float64 = __pytra_float((__pytra_float(float64(1.0)) - __pytra_float((__pytra_float(float64(2.0)) * __pytra_float(fy)))))
                    var sx float64 = __pytra_float((__pytra_float((__pytra_float((__pytra_float(float64(2.0)) * __pytra_float(fx))) - __pytra_float(float64(1.0)))) * __pytra_float((__pytra_float(width) / __pytra_float(__hoisted_cast_4)))))
                    var dx float64 = __pytra_float(sx)
                    var dy float64 = __pytra_float(sy)
                    var dz float64 = __pytra_float(float64(1.0))
                    var inv_len float64 = __pytra_float((__pytra_float(float64(1.0)) / __pytra_float(math.Sqrt(__pytra_float((__pytra_float((__pytra_float((__pytra_float(dx) * __pytra_float(dx))) + __pytra_float((__pytra_float(dy) * __pytra_float(dy))))) + __pytra_float((__pytra_float(dz) * __pytra_float(dz)))))))))
                    dx *= inv_len
                    dy *= inv_len
                    dz *= inv_len
                    var t_min float64 = __pytra_float(float64(1e+30))
                    var hit_id int64 = __pytra_int((-int64(1)))
                    var t float64 = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, (-float64(0.8)), (-float64(0.2)), float64(2.2), float64(0.8)))
                    if ((__pytra_float(t) > __pytra_float(float64(0.0))) && (__pytra_float(t) < __pytra_float(t_min))) {
                        t_min = __pytra_float(t)
                        hit_id = __pytra_int(int64(0))
                    }
                    t = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, float64(0.9), float64(0.1), float64(2.9), float64(0.95)))
                    if ((__pytra_float(t) > __pytra_float(float64(0.0))) && (__pytra_float(t) < __pytra_float(t_min))) {
                        t_min = __pytra_float(t)
                        hit_id = __pytra_int(int64(1))
                    }
                    t = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, float64(0.0), (-float64(1001.0)), float64(3.0), float64(1000.0)))
                    if ((__pytra_float(t) > __pytra_float(float64(0.0))) && (__pytra_float(t) < __pytra_float(t_min))) {
                        t_min = __pytra_float(t)
                        hit_id = __pytra_int(int64(2))
                    }
                    var r int64 = __pytra_int(int64(0))
                    var g int64 = __pytra_int(int64(0))
                    var b int64 = __pytra_int(int64(0))
                    if (__pytra_int(hit_id) >= __pytra_int(int64(0))) {
                        var px float64 = __pytra_float((__pytra_float(ox) + __pytra_float((__pytra_float(dx) * __pytra_float(t_min)))))
                        var py float64 = __pytra_float((__pytra_float(oy) + __pytra_float((__pytra_float(dy) * __pytra_float(t_min)))))
                        var pz float64 = __pytra_float((__pytra_float(oz) + __pytra_float((__pytra_float(dz) * __pytra_float(t_min)))))
                        var nx float64 = __pytra_float(float64(0.0))
                        var ny float64 = __pytra_float(float64(0.0))
                        var nz float64 = __pytra_float(float64(0.0))
                        if (__pytra_int(hit_id) == __pytra_int(int64(0))) {
                            nx = __pytra_float((__pytra_float((__pytra_float(px) + __pytra_float(float64(0.8)))) / __pytra_float(float64(0.8))))
                            ny = __pytra_float((__pytra_float((__pytra_float(py) + __pytra_float(float64(0.2)))) / __pytra_float(float64(0.8))))
                            nz = __pytra_float((__pytra_float((__pytra_float(pz) - __pytra_float(float64(2.2)))) / __pytra_float(float64(0.8))))
                        } else {
                            if (__pytra_int(hit_id) == __pytra_int(int64(1))) {
                                nx = __pytra_float((__pytra_float((__pytra_float(px) - __pytra_float(float64(0.9)))) / __pytra_float(float64(0.95))))
                                ny = __pytra_float((__pytra_float((__pytra_float(py) - __pytra_float(float64(0.1)))) / __pytra_float(float64(0.95))))
                                nz = __pytra_float((__pytra_float((__pytra_float(pz) - __pytra_float(float64(2.9)))) / __pytra_float(float64(0.95))))
                            } else {
                                nx = __pytra_float(float64(0.0))
                                ny = __pytra_float(float64(1.0))
                                nz = __pytra_float(float64(0.0))
                            }
                        }
                        var diff float64 = __pytra_float((__pytra_float((__pytra_float((__pytra_float(nx) * __pytra_float((-lx)))) + __pytra_float((__pytra_float(ny) * __pytra_float((-ly)))))) + __pytra_float((__pytra_float(nz) * __pytra_float((-lz))))))
                        diff = __pytra_float(clamp01(diff))
                        var base_r float64 = __pytra_float(float64(0.0))
                        var base_g float64 = __pytra_float(float64(0.0))
                        var base_b float64 = __pytra_float(float64(0.0))
                        if (__pytra_int(hit_id) == __pytra_int(int64(0))) {
                            base_r = __pytra_float(float64(0.95))
                            base_g = __pytra_float(float64(0.35))
                            base_b = __pytra_float(float64(0.25))
                        } else {
                            if (__pytra_int(hit_id) == __pytra_int(int64(1))) {
                                base_r = __pytra_float(float64(0.25))
                                base_g = __pytra_float(float64(0.55))
                                base_b = __pytra_float(float64(0.95))
                            } else {
                                var checker int64 = __pytra_int((__pytra_int(__pytra_int((__pytra_float((__pytra_float(px) + __pytra_float(float64(50.0)))) * __pytra_float(float64(0.8))))) + __pytra_int(__pytra_int((__pytra_float((__pytra_float(pz) + __pytra_float(float64(50.0)))) * __pytra_float(float64(0.8)))))))
                                if (__pytra_int((__pytra_int(checker) % __pytra_int(int64(2)))) == __pytra_int(int64(0))) {
                                    base_r = __pytra_float(float64(0.85))
                                    base_g = __pytra_float(float64(0.85))
                                    base_b = __pytra_float(float64(0.85))
                                } else {
                                    base_r = __pytra_float(float64(0.2))
                                    base_g = __pytra_float(float64(0.2))
                                    base_b = __pytra_float(float64(0.2))
                                }
                            }
                        }
                        var shade float64 = __pytra_float((__pytra_float(float64(0.12)) + __pytra_float((__pytra_float(float64(0.88)) * __pytra_float(diff)))))
                        r = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float(clamp01((__pytra_float(base_r) * __pytra_float(shade)))))))
                        g = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float(clamp01((__pytra_float(base_g) * __pytra_float(shade)))))))
                        b = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float(clamp01((__pytra_float(base_b) * __pytra_float(shade)))))))
                    } else {
                        var tsky float64 = __pytra_float((__pytra_float(float64(0.5)) * __pytra_float((__pytra_float(dy) + __pytra_float(float64(1.0))))))
                        r = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float((__pytra_float(float64(0.65)) + __pytra_float((__pytra_float(float64(0.2)) * __pytra_float(tsky))))))))
                        g = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float((__pytra_float(float64(0.75)) + __pytra_float((__pytra_float(float64(0.18)) * __pytra_float(tsky))))))))
                        b = __pytra_int(__pytra_int((__pytra_float(float64(255.0)) * __pytra_float((__pytra_float(float64(0.9)) + __pytra_float((__pytra_float(float64(0.08)) * __pytra_float(tsky))))))))
                    }
                    ar += r
                    ag += g
                    ab += b
                }
            }
            var samples int64 = __pytra_int((__pytra_int(aa) * __pytra_int(aa)))
            pixels = append(__pytra_as_list(pixels), (__pytra_int(__pytra_int(ar) / __pytra_int(samples))))
            pixels = append(__pytra_as_list(pixels), (__pytra_int(__pytra_int(ag) / __pytra_int(samples))))
            pixels = append(__pytra_as_list(pixels), (__pytra_int(__pytra_int(ab) / __pytra_int(samples))))
        }
    }
    return __pytra_as_list(pixels)
}

func run_raytrace() {
    var width int64 = __pytra_int(int64(1600))
    var height int64 = __pytra_int(int64(900))
    var aa int64 = __pytra_int(int64(2))
    var out_path string = __pytra_str("sample/out/02_raytrace_spheres.png")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var pixels []any = __pytra_as_list(render(width, height, aa))
    __pytra_noop(out_path, width, height, pixels)
    var elapsed float64 = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_raytrace()
}
