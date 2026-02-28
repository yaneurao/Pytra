// Auto-generated Pytra Swift native source from EAST3.
import Foundation

// Runtime helpers are provided by py_runtime.swift in the same module.


// 02: Sample that runs a mini sphere-only ray tracer and outputs a PNG image.
// Dependencies are kept minimal (time only) for transpilation compatibility.

func clamp01(v: Double) -> Double {
    if (__pytra_float(v) < __pytra_float(Double(0.0))) {
        return Double(0.0)
    }
    if (__pytra_float(v) > __pytra_float(Double(1.0))) {
        return Double(1.0)
    }
    return v
}

func hit_sphere(ox: Double, oy: Double, oz: Double, dx: Double, dy: Double, dz: Double, cx: Double, cy: Double, cz: Double, r: Double) -> Double {
    var lx: Double = __pytra_float((__pytra_float(ox) - __pytra_float(cx)))
    var ly: Double = __pytra_float((__pytra_float(oy) - __pytra_float(cy)))
    var lz: Double = __pytra_float((__pytra_float(oz) - __pytra_float(cz)))
    var a: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float(dx) * __pytra_float(dx))) + __pytra_float((__pytra_float(dy) * __pytra_float(dy))))) + __pytra_float((__pytra_float(dz) * __pytra_float(dz)))))
    var b: Double = __pytra_float((__pytra_float(Double(2.0)) * __pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(dx))) + __pytra_float((__pytra_float(ly) * __pytra_float(dy))))) + __pytra_float((__pytra_float(lz) * __pytra_float(dz)))))))
    var c: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(lx))) + __pytra_float((__pytra_float(ly) * __pytra_float(ly))))) + __pytra_float((__pytra_float(lz) * __pytra_float(lz))))) - __pytra_float((__pytra_float(r) * __pytra_float(r)))))
    var d: Double = __pytra_float((__pytra_float((__pytra_float(b) * __pytra_float(b))) - __pytra_float((__pytra_float((__pytra_float(Double(4.0)) * __pytra_float(a))) * __pytra_float(c)))))
    if (__pytra_float(d) < __pytra_float(Double(0.0))) {
        return (-Double(1.0))
    }
    var sd: Double = __pytra_float(sqrt(__pytra_float(d)))
    var t0: Double = __pytra_float((__pytra_float((__pytra_float((-b)) - __pytra_float(sd))) / __pytra_float((__pytra_float(Double(2.0)) * __pytra_float(a)))))
    var t1: Double = __pytra_float((__pytra_float((__pytra_float((-b)) + __pytra_float(sd))) / __pytra_float((__pytra_float(Double(2.0)) * __pytra_float(a)))))
    if (__pytra_float(t0) > __pytra_float(Double(0.001))) {
        return t0
    }
    if (__pytra_float(t1) > __pytra_float(Double(0.001))) {
        return t1
    }
    return (-Double(1.0))
}

func render(width: Int64, height: Int64, aa: Int64) -> [Any] {
    var pixels: [Any] = __pytra_as_list([])
    var ox: Double = __pytra_float(Double(0.0))
    var oy: Double = __pytra_float(Double(0.0))
    var oz: Double = __pytra_float((-Double(3.0)))
    var lx: Double = __pytra_float((-Double(0.4)))
    var ly: Double = __pytra_float(Double(0.8))
    var lz: Double = __pytra_float((-Double(0.45)))
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float(aa))
    var __hoisted_cast_2: Double = __pytra_float(__pytra_float((__pytra_int(height) - __pytra_int(Int64(1)))))
    var __hoisted_cast_3: Double = __pytra_float(__pytra_float((__pytra_int(width) - __pytra_int(Int64(1)))))
    var __hoisted_cast_4: Double = __pytra_float(__pytra_float(height))
    let __step_0 = __pytra_int(Int64(1))
    var y = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height))) {
        let __step_1 = __pytra_int(Int64(1))
        var x = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width))) {
            var ar: Int64 = __pytra_int(Int64(0))
            var ag: Int64 = __pytra_int(Int64(0))
            var ab: Int64 = __pytra_int(Int64(0))
            let __step_2 = __pytra_int(Int64(1))
            var ay = __pytra_int(Int64(0))
            while ((__step_2 >= 0 && ay < __pytra_int(aa)) || (__step_2 < 0 && ay > __pytra_int(aa))) {
                let __step_3 = __pytra_int(Int64(1))
                var ax = __pytra_int(Int64(0))
                while ((__step_3 >= 0 && ax < __pytra_int(aa)) || (__step_3 < 0 && ax > __pytra_int(aa))) {
                    var fy: Double = __pytra_float((__pytra_float((__pytra_float(y) + __pytra_float((__pytra_float((__pytra_float(ay) + __pytra_float(Double(0.5)))) / __pytra_float(__hoisted_cast_1))))) / __pytra_float(__hoisted_cast_2)))
                    var fx: Double = __pytra_float((__pytra_float((__pytra_float(x) + __pytra_float((__pytra_float((__pytra_float(ax) + __pytra_float(Double(0.5)))) / __pytra_float(__hoisted_cast_1))))) / __pytra_float(__hoisted_cast_3)))
                    var sy: Double = __pytra_float((__pytra_float(Double(1.0)) - __pytra_float((__pytra_float(Double(2.0)) * __pytra_float(fy)))))
                    var sx: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float(Double(2.0)) * __pytra_float(fx))) - __pytra_float(Double(1.0)))) * __pytra_float((__pytra_float(width) / __pytra_float(__hoisted_cast_4)))))
                    var dx: Double = __pytra_float(sx)
                    var dy: Double = __pytra_float(sy)
                    var dz: Double = __pytra_float(Double(1.0))
                    var inv_len: Double = __pytra_float((__pytra_float(Double(1.0)) / __pytra_float(sqrt(__pytra_float((__pytra_float((__pytra_float((__pytra_float(dx) * __pytra_float(dx))) + __pytra_float((__pytra_float(dy) * __pytra_float(dy))))) + __pytra_float((__pytra_float(dz) * __pytra_float(dz)))))))))
                    dx *= inv_len
                    dy *= inv_len
                    dz *= inv_len
                    var t_min: Double = __pytra_float(Double(1e+30))
                    var hit_id: Int64 = __pytra_int((-Int64(1)))
                    var t: Double = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, (-Double(0.8)), (-Double(0.2)), Double(2.2), Double(0.8)))
                    if ((__pytra_float(t) > __pytra_float(Double(0.0))) && (__pytra_float(t) < __pytra_float(t_min))) {
                        t_min = __pytra_float(t)
                        hit_id = __pytra_int(Int64(0))
                    }
                    t = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, Double(0.9), Double(0.1), Double(2.9), Double(0.95)))
                    if ((__pytra_float(t) > __pytra_float(Double(0.0))) && (__pytra_float(t) < __pytra_float(t_min))) {
                        t_min = __pytra_float(t)
                        hit_id = __pytra_int(Int64(1))
                    }
                    t = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, Double(0.0), (-Double(1001.0)), Double(3.0), Double(1000.0)))
                    if ((__pytra_float(t) > __pytra_float(Double(0.0))) && (__pytra_float(t) < __pytra_float(t_min))) {
                        t_min = __pytra_float(t)
                        hit_id = __pytra_int(Int64(2))
                    }
                    var r: Int64 = __pytra_int(Int64(0))
                    var g: Int64 = __pytra_int(Int64(0))
                    var b: Int64 = __pytra_int(Int64(0))
                    if (__pytra_int(hit_id) >= __pytra_int(Int64(0))) {
                        var px: Double = __pytra_float((__pytra_float(ox) + __pytra_float((__pytra_float(dx) * __pytra_float(t_min)))))
                        var py: Double = __pytra_float((__pytra_float(oy) + __pytra_float((__pytra_float(dy) * __pytra_float(t_min)))))
                        var pz: Double = __pytra_float((__pytra_float(oz) + __pytra_float((__pytra_float(dz) * __pytra_float(t_min)))))
                        var nx: Double = __pytra_float(Double(0.0))
                        var ny: Double = __pytra_float(Double(0.0))
                        var nz: Double = __pytra_float(Double(0.0))
                        if (__pytra_int(hit_id) == __pytra_int(Int64(0))) {
                            nx = __pytra_float((__pytra_float((__pytra_float(px) + __pytra_float(Double(0.8)))) / __pytra_float(Double(0.8))))
                            ny = __pytra_float((__pytra_float((__pytra_float(py) + __pytra_float(Double(0.2)))) / __pytra_float(Double(0.8))))
                            nz = __pytra_float((__pytra_float((__pytra_float(pz) - __pytra_float(Double(2.2)))) / __pytra_float(Double(0.8))))
                        } else {
                            if (__pytra_int(hit_id) == __pytra_int(Int64(1))) {
                                nx = __pytra_float((__pytra_float((__pytra_float(px) - __pytra_float(Double(0.9)))) / __pytra_float(Double(0.95))))
                                ny = __pytra_float((__pytra_float((__pytra_float(py) - __pytra_float(Double(0.1)))) / __pytra_float(Double(0.95))))
                                nz = __pytra_float((__pytra_float((__pytra_float(pz) - __pytra_float(Double(2.9)))) / __pytra_float(Double(0.95))))
                            } else {
                                nx = __pytra_float(Double(0.0))
                                ny = __pytra_float(Double(1.0))
                                nz = __pytra_float(Double(0.0))
                            }
                        }
                        var diff: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float(nx) * __pytra_float((-lx)))) + __pytra_float((__pytra_float(ny) * __pytra_float((-ly)))))) + __pytra_float((__pytra_float(nz) * __pytra_float((-lz))))))
                        diff = __pytra_float(clamp01(diff))
                        var base_r: Double = __pytra_float(Double(0.0))
                        var base_g: Double = __pytra_float(Double(0.0))
                        var base_b: Double = __pytra_float(Double(0.0))
                        if (__pytra_int(hit_id) == __pytra_int(Int64(0))) {
                            base_r = __pytra_float(Double(0.95))
                            base_g = __pytra_float(Double(0.35))
                            base_b = __pytra_float(Double(0.25))
                        } else {
                            if (__pytra_int(hit_id) == __pytra_int(Int64(1))) {
                                base_r = __pytra_float(Double(0.25))
                                base_g = __pytra_float(Double(0.55))
                                base_b = __pytra_float(Double(0.95))
                            } else {
                                var checker: Int64 = __pytra_int((__pytra_int(__pytra_int((__pytra_float((__pytra_float(px) + __pytra_float(Double(50.0)))) * __pytra_float(Double(0.8))))) + __pytra_int(__pytra_int((__pytra_float((__pytra_float(pz) + __pytra_float(Double(50.0)))) * __pytra_float(Double(0.8)))))))
                                if (__pytra_int((__pytra_int(checker) % __pytra_int(Int64(2)))) == __pytra_int(Int64(0))) {
                                    base_r = __pytra_float(Double(0.85))
                                    base_g = __pytra_float(Double(0.85))
                                    base_b = __pytra_float(Double(0.85))
                                } else {
                                    base_r = __pytra_float(Double(0.2))
                                    base_g = __pytra_float(Double(0.2))
                                    base_b = __pytra_float(Double(0.2))
                                }
                            }
                        }
                        var shade: Double = __pytra_float((__pytra_float(Double(0.12)) + __pytra_float((__pytra_float(Double(0.88)) * __pytra_float(diff)))))
                        r = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float(clamp01((__pytra_float(base_r) * __pytra_float(shade)))))))
                        g = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float(clamp01((__pytra_float(base_g) * __pytra_float(shade)))))))
                        b = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float(clamp01((__pytra_float(base_b) * __pytra_float(shade)))))))
                    } else {
                        var tsky: Double = __pytra_float((__pytra_float(Double(0.5)) * __pytra_float((__pytra_float(dy) + __pytra_float(Double(1.0))))))
                        r = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float((__pytra_float(Double(0.65)) + __pytra_float((__pytra_float(Double(0.2)) * __pytra_float(tsky))))))))
                        g = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float((__pytra_float(Double(0.75)) + __pytra_float((__pytra_float(Double(0.18)) * __pytra_float(tsky))))))))
                        b = __pytra_int(__pytra_int((__pytra_float(Double(255.0)) * __pytra_float((__pytra_float(Double(0.9)) + __pytra_float((__pytra_float(Double(0.08)) * __pytra_float(tsky))))))))
                    }
                    ar += r
                    ag += g
                    ab += b
                    ax += __step_3
                }
                ay += __step_2
            }
            var samples: Int64 = __pytra_int((__pytra_int(aa) * __pytra_int(aa)))
            pixels = __pytra_as_list(pixels); pixels.append((__pytra_int(__pytra_int(ar) / __pytra_int(samples))))
            pixels = __pytra_as_list(pixels); pixels.append((__pytra_int(__pytra_int(ag) / __pytra_int(samples))))
            pixels = __pytra_as_list(pixels); pixels.append((__pytra_int(__pytra_int(ab) / __pytra_int(samples))))
            x += __step_1
        }
        y += __step_0
    }
    return pixels
}

func run_raytrace() {
    var width: Int64 = __pytra_int(Int64(1600))
    var height: Int64 = __pytra_int(Int64(900))
    var aa: Int64 = __pytra_int(Int64(2))
    var out_path: String = __pytra_str("sample/out/02_raytrace_spheres.png")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var pixels: [Any] = __pytra_as_list(render(width, height, aa))
    __pytra_noop(out_path, width, height, pixels)
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("elapsed_sec:", elapsed)
}

@main
struct Main {
    static func main() {
        run_raytrace()
    }
}
