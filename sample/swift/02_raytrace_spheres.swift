import Foundation


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
    var lx: Double = (ox - cx)
    var ly: Double = (oy - cy)
    var lz: Double = (oz - cz)
    var a: Double = (((dx * dx) + (dy * dy)) + (dz * dz))
    var b: Double = (Double(2.0) * (((lx * dx) + (ly * dy)) + (lz * dz)))
    var c: Double = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (r * r))
    var d: Double = ((b * b) - ((Double(4.0) * a) * c))
    if (__pytra_float(d) < __pytra_float(Double(0.0))) {
        return __pytra_float(-Double(1.0))
    }
    var sd: Double = __pytra_float(sqrt(__pytra_float(d)))
    var t0: Double = (((-b) - sd) / (Double(2.0) * a))
    var t1: Double = (((-b) + sd) / (Double(2.0) * a))
    if (__pytra_float(t0) > __pytra_float(Double(0.001))) {
        return t0
    }
    if (__pytra_float(t1) > __pytra_float(Double(0.001))) {
        return t1
    }
    return __pytra_float(-Double(1.0))
}

func render(width: Int64, height: Int64, aa: Int64) -> [Any] {
    var pixels: [Any] = __pytra_as_list([])
    var ox: Double = Double(0.0)
    var oy: Double = Double(0.0)
    var oz: Double = __pytra_float(-Double(3.0))
    var lx: Double = __pytra_float(-Double(0.4))
    var ly: Double = Double(0.8)
    var lz: Double = __pytra_float(-Double(0.45))
    var __hoisted_cast_1: Double = __pytra_float(aa)
    var __hoisted_cast_2: Double = __pytra_float(height - Int64(1))
    var __hoisted_cast_3: Double = __pytra_float(width - Int64(1))
    var __hoisted_cast_4: Double = __pytra_float(height)
    var y = __pytra_int(Int64(0))
    while (y < __pytra_int(height)) {
        var x = __pytra_int(Int64(0))
        while (x < __pytra_int(width)) {
            var ar: Int64 = Int64(0)
            var ag: Int64 = Int64(0)
            var ab: Int64 = Int64(0)
            var ay = __pytra_int(Int64(0))
            while (ay < __pytra_int(aa)) {
                var ax = __pytra_int(Int64(0))
                while (ax < __pytra_int(aa)) {
                    var fy: Double = ((__pytra_float(y) + ((__pytra_float(ay) + Double(0.5)) / __hoisted_cast_1)) / __hoisted_cast_2)
                    var fx: Double = ((__pytra_float(x) + ((__pytra_float(ax) + Double(0.5)) / __hoisted_cast_1)) / __hoisted_cast_3)
                    var sy: Double = (Double(1.0) - (Double(2.0) * fy))
                    var sx: Double = (((Double(2.0) * fx) - Double(1.0)) * (__pytra_float(width) / __hoisted_cast_4))
                    var dx: Double = sx
                    var dy: Double = sy
                    var dz: Double = Double(1.0)
                    var inv_len: Double = __pytra_float(Double(1.0) / __pytra_float(sqrt(__pytra_float(((dx * dx) + (dy * dy)) + (dz * dz)))))
                    dx *= inv_len
                    dy *= inv_len
                    dz *= inv_len
                    var t_min: Double = Double(1e+30)
                    var hit_id: Int64 = __pytra_int(-Int64(1))
                    var t: Double = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, (-Double(0.8)), (-Double(0.2)), Double(2.2), Double(0.8)))
                    if ((__pytra_float(t) > __pytra_float(Double(0.0))) && (__pytra_float(t) < __pytra_float(t_min))) {
                        t_min = t
                        hit_id = Int64(0)
                    }
                    t = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, Double(0.9), Double(0.1), Double(2.9), Double(0.95)))
                    if ((__pytra_float(t) > __pytra_float(Double(0.0))) && (__pytra_float(t) < __pytra_float(t_min))) {
                        t_min = t
                        hit_id = Int64(1)
                    }
                    t = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, Double(0.0), (-Double(1001.0)), Double(3.0), Double(1000.0)))
                    if ((__pytra_float(t) > __pytra_float(Double(0.0))) && (__pytra_float(t) < __pytra_float(t_min))) {
                        t_min = t
                        hit_id = Int64(2)
                    }
                    var r: Int64 = Int64(0)
                    var g: Int64 = Int64(0)
                    var b: Int64 = Int64(0)
                    if (__pytra_int(hit_id) >= __pytra_int(Int64(0))) {
                        var px: Double = (ox + (dx * t_min))
                        var py: Double = (oy + (dy * t_min))
                        var pz: Double = (oz + (dz * t_min))
                        var nx: Double = Double(0.0)
                        var ny: Double = Double(0.0)
                        var nz: Double = Double(0.0)
                        if (__pytra_int(hit_id) == __pytra_int(Int64(0))) {
                            nx = ((px + Double(0.8)) / Double(0.8))
                            ny = ((py + Double(0.2)) / Double(0.8))
                            nz = ((pz - Double(2.2)) / Double(0.8))
                        } else {
                            if (__pytra_int(hit_id) == __pytra_int(Int64(1))) {
                                nx = ((px - Double(0.9)) / Double(0.95))
                                ny = ((py - Double(0.1)) / Double(0.95))
                                nz = ((pz - Double(2.9)) / Double(0.95))
                            } else {
                                nx = Double(0.0)
                                ny = Double(1.0)
                                nz = Double(0.0)
                            }
                        }
                        var diff: Double = (((nx * (-lx)) + (ny * (-ly))) + (nz * (-lz)))
                        diff = __pytra_float(clamp01(diff))
                        var base_r: Double = Double(0.0)
                        var base_g: Double = Double(0.0)
                        var base_b: Double = Double(0.0)
                        if (__pytra_int(hit_id) == __pytra_int(Int64(0))) {
                            base_r = Double(0.95)
                            base_g = Double(0.35)
                            base_b = Double(0.25)
                        } else {
                            if (__pytra_int(hit_id) == __pytra_int(Int64(1))) {
                                base_r = Double(0.25)
                                base_g = Double(0.55)
                                base_b = Double(0.95)
                            } else {
                                var checker: Int64 = (__pytra_int((px + Double(50.0)) * Double(0.8)) + __pytra_int((pz + Double(50.0)) * Double(0.8)))
                                if (__pytra_int(checker % Int64(2)) == __pytra_int(Int64(0))) {
                                    base_r = Double(0.85)
                                    base_g = Double(0.85)
                                    base_b = Double(0.85)
                                } else {
                                    base_r = Double(0.2)
                                    base_g = Double(0.2)
                                    base_b = Double(0.2)
                                }
                            }
                        }
                        var shade: Double = (Double(0.12) + (Double(0.88) * diff))
                        r = __pytra_int(Double(255.0) * clamp01((base_r * shade)))
                        g = __pytra_int(Double(255.0) * clamp01((base_g * shade)))
                        b = __pytra_int(Double(255.0) * clamp01((base_b * shade)))
                    } else {
                        var tsky: Double = (Double(0.5) * (dy + Double(1.0)))
                        r = __pytra_int(Double(255.0) * (Double(0.65) + (Double(0.2) * tsky)))
                        g = __pytra_int(Double(255.0) * (Double(0.75) + (Double(0.18) * tsky)))
                        b = __pytra_int(Double(255.0) * (Double(0.9) + (Double(0.08) * tsky)))
                    }
                    ar += r
                    ag += g
                    ab += b
                    ax += 1
                }
                ay += 1
            }
            var samples: Int64 = (aa * aa)
            pixels.append((ar / samples))
            pixels.append((ag / samples))
            pixels.append((ab / samples))
            x += 1
        }
        y += 1
    }
    return pixels
}

func run_raytrace() {
    var width: Int64 = Int64(1600)
    var height: Int64 = Int64(900)
    var aa: Int64 = Int64(2)
    var out_path: String = "sample/out/02_raytrace_spheres.png"
    var start: Double = __pytra_perf_counter()
    var pixels: [Any] = __pytra_as_list(render(width, height, aa))
    __pytra_write_rgb_png(out_path, width, height, pixels)
    var elapsed: Double = (__pytra_perf_counter() - start)
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
