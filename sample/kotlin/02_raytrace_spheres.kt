import kotlin.math.*


// 02: Sample that runs a mini sphere-only ray tracer and outputs a PNG image.
// Dependencies are kept minimal (time only) for transpilation compatibility.

fun clamp01(v: Double): Double {
    if ((__pytra_float(v) < __pytra_float(0.0))) {
        return __pytra_float(0.0)
    }
    if ((__pytra_float(v) > __pytra_float(1.0))) {
        return __pytra_float(1.0)
    }
    return __pytra_float(v)
}

fun hit_sphere(ox: Double, oy: Double, oz: Double, dx: Double, dy: Double, dz: Double, cx: Double, cy: Double, cz: Double, r: Double): Double {
    var lx: Double = __pytra_float((__pytra_float(ox) - __pytra_float(cx)))
    var ly: Double = __pytra_float((__pytra_float(oy) - __pytra_float(cy)))
    var lz: Double = __pytra_float((__pytra_float(oz) - __pytra_float(cz)))
    var a: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float(dx) * __pytra_float(dx))) + __pytra_float((__pytra_float(dy) * __pytra_float(dy))))) + __pytra_float((__pytra_float(dz) * __pytra_float(dz)))))
    var b: Double = __pytra_float((__pytra_float(2.0) * __pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(dx))) + __pytra_float((__pytra_float(ly) * __pytra_float(dy))))) + __pytra_float((__pytra_float(lz) * __pytra_float(dz)))))))
    var c: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(lx))) + __pytra_float((__pytra_float(ly) * __pytra_float(ly))))) + __pytra_float((__pytra_float(lz) * __pytra_float(lz))))) - __pytra_float((__pytra_float(r) * __pytra_float(r)))))
    var d: Double = __pytra_float((__pytra_float((__pytra_float(b) * __pytra_float(b))) - __pytra_float((__pytra_float((__pytra_float(4.0) * __pytra_float(a))) * __pytra_float(c)))))
    if ((__pytra_float(d) < __pytra_float(0.0))) {
        return __pytra_float((-1.0))
    }
    var sd: Double = __pytra_float(kotlin.math.sqrt(__pytra_float(d)))
    var t0: Double = __pytra_float((__pytra_float((__pytra_float((-b)) - __pytra_float(sd))) / __pytra_float((__pytra_float(2.0) * __pytra_float(a)))))
    var t1: Double = __pytra_float((__pytra_float((__pytra_float((-b)) + __pytra_float(sd))) / __pytra_float((__pytra_float(2.0) * __pytra_float(a)))))
    if ((__pytra_float(t0) > __pytra_float(0.001))) {
        return __pytra_float(t0)
    }
    if ((__pytra_float(t1) > __pytra_float(0.001))) {
        return __pytra_float(t1)
    }
    return __pytra_float((-1.0))
}

fun render(width: Long, height: Long, aa: Long): MutableList<Any?> {
    var pixels: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var ox: Double = __pytra_float(0.0)
    var oy: Double = __pytra_float(0.0)
    var oz: Double = __pytra_float((-3.0))
    var lx: Double = __pytra_float((-0.4))
    var ly: Double = __pytra_float(0.8)
    var lz: Double = __pytra_float((-0.45))
    var __hoisted_cast_1: Double = __pytra_float(__pytra_float(aa))
    var __hoisted_cast_2: Double = __pytra_float(__pytra_float((__pytra_int(height) - __pytra_int(1L))))
    var __hoisted_cast_3: Double = __pytra_float(__pytra_float((__pytra_int(width) - __pytra_int(1L))))
    var __hoisted_cast_4: Double = __pytra_float(__pytra_float(height))
    val __step_0 = __pytra_int(1L)
    var y = __pytra_int(0L)
    while ((__step_0 >= 0L && y < __pytra_int(height)) || (__step_0 < 0L && y > __pytra_int(height))) {
        val __step_1 = __pytra_int(1L)
        var x = __pytra_int(0L)
        while ((__step_1 >= 0L && x < __pytra_int(width)) || (__step_1 < 0L && x > __pytra_int(width))) {
            var ar: Long = __pytra_int(0L)
            var ag: Long = __pytra_int(0L)
            var ab: Long = __pytra_int(0L)
            val __step_2 = __pytra_int(1L)
            var ay = __pytra_int(0L)
            while ((__step_2 >= 0L && ay < __pytra_int(aa)) || (__step_2 < 0L && ay > __pytra_int(aa))) {
                val __step_3 = __pytra_int(1L)
                var ax = __pytra_int(0L)
                while ((__step_3 >= 0L && ax < __pytra_int(aa)) || (__step_3 < 0L && ax > __pytra_int(aa))) {
                    var fy: Double = __pytra_float((__pytra_float((__pytra_float(y) + __pytra_float((__pytra_float((__pytra_float(ay) + __pytra_float(0.5))) / __pytra_float(__hoisted_cast_1))))) / __pytra_float(__hoisted_cast_2)))
                    var fx: Double = __pytra_float((__pytra_float((__pytra_float(x) + __pytra_float((__pytra_float((__pytra_float(ax) + __pytra_float(0.5))) / __pytra_float(__hoisted_cast_1))))) / __pytra_float(__hoisted_cast_3)))
                    var sy: Double = __pytra_float((__pytra_float(1.0) - __pytra_float((__pytra_float(2.0) * __pytra_float(fy)))))
                    var sx: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float(2.0) * __pytra_float(fx))) - __pytra_float(1.0))) * __pytra_float((__pytra_float(width) / __pytra_float(__hoisted_cast_4)))))
                    var dx: Double = __pytra_float(sx)
                    var dy: Double = __pytra_float(sy)
                    var dz: Double = __pytra_float(1.0)
                    var inv_len: Double = __pytra_float((__pytra_float(1.0) / __pytra_float(kotlin.math.sqrt(__pytra_float((__pytra_float((__pytra_float((__pytra_float(dx) * __pytra_float(dx))) + __pytra_float((__pytra_float(dy) * __pytra_float(dy))))) + __pytra_float((__pytra_float(dz) * __pytra_float(dz)))))))))
                    dx *= inv_len
                    dy *= inv_len
                    dz *= inv_len
                    var t_min: Double = __pytra_float(1e+30)
                    var hit_id: Long = __pytra_int((-1L))
                    var t: Double = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, (-0.8), (-0.2), 2.2, 0.8))
                    if (((__pytra_float(t) > __pytra_float(0.0)) && (__pytra_float(t) < __pytra_float(t_min)))) {
                        t_min = __pytra_float(t)
                        hit_id = __pytra_int(0L)
                    }
                    t = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95))
                    if (((__pytra_float(t) > __pytra_float(0.0)) && (__pytra_float(t) < __pytra_float(t_min)))) {
                        t_min = __pytra_float(t)
                        hit_id = __pytra_int(1L)
                    }
                    t = __pytra_float(hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, (-1001.0), 3.0, 1000.0))
                    if (((__pytra_float(t) > __pytra_float(0.0)) && (__pytra_float(t) < __pytra_float(t_min)))) {
                        t_min = __pytra_float(t)
                        hit_id = __pytra_int(2L)
                    }
                    var r: Long = __pytra_int(0L)
                    var g: Long = __pytra_int(0L)
                    var b: Long = __pytra_int(0L)
                    if ((__pytra_int(hit_id) >= __pytra_int(0L))) {
                        var px: Double = __pytra_float((__pytra_float(ox) + __pytra_float((__pytra_float(dx) * __pytra_float(t_min)))))
                        var py: Double = __pytra_float((__pytra_float(oy) + __pytra_float((__pytra_float(dy) * __pytra_float(t_min)))))
                        var pz: Double = __pytra_float((__pytra_float(oz) + __pytra_float((__pytra_float(dz) * __pytra_float(t_min)))))
                        var nx: Double = __pytra_float(0.0)
                        var ny: Double = __pytra_float(0.0)
                        var nz: Double = __pytra_float(0.0)
                        if ((__pytra_int(hit_id) == __pytra_int(0L))) {
                            nx = __pytra_float((__pytra_float((__pytra_float(px) + __pytra_float(0.8))) / __pytra_float(0.8)))
                            ny = __pytra_float((__pytra_float((__pytra_float(py) + __pytra_float(0.2))) / __pytra_float(0.8)))
                            nz = __pytra_float((__pytra_float((__pytra_float(pz) - __pytra_float(2.2))) / __pytra_float(0.8)))
                        } else {
                            if ((__pytra_int(hit_id) == __pytra_int(1L))) {
                                nx = __pytra_float((__pytra_float((__pytra_float(px) - __pytra_float(0.9))) / __pytra_float(0.95)))
                                ny = __pytra_float((__pytra_float((__pytra_float(py) - __pytra_float(0.1))) / __pytra_float(0.95)))
                                nz = __pytra_float((__pytra_float((__pytra_float(pz) - __pytra_float(2.9))) / __pytra_float(0.95)))
                            } else {
                                nx = __pytra_float(0.0)
                                ny = __pytra_float(1.0)
                                nz = __pytra_float(0.0)
                            }
                        }
                        var diff: Double = __pytra_float((__pytra_float((__pytra_float((__pytra_float(nx) * __pytra_float((-lx)))) + __pytra_float((__pytra_float(ny) * __pytra_float((-ly)))))) + __pytra_float((__pytra_float(nz) * __pytra_float((-lz))))))
                        diff = __pytra_float(clamp01(diff))
                        var base_r: Double = __pytra_float(0.0)
                        var base_g: Double = __pytra_float(0.0)
                        var base_b: Double = __pytra_float(0.0)
                        if ((__pytra_int(hit_id) == __pytra_int(0L))) {
                            base_r = __pytra_float(0.95)
                            base_g = __pytra_float(0.35)
                            base_b = __pytra_float(0.25)
                        } else {
                            if ((__pytra_int(hit_id) == __pytra_int(1L))) {
                                base_r = __pytra_float(0.25)
                                base_g = __pytra_float(0.55)
                                base_b = __pytra_float(0.95)
                            } else {
                                var checker: Long = __pytra_int((__pytra_int(__pytra_int((__pytra_float((__pytra_float(px) + __pytra_float(50.0))) * __pytra_float(0.8)))) + __pytra_int(__pytra_int((__pytra_float((__pytra_float(pz) + __pytra_float(50.0))) * __pytra_float(0.8))))))
                                if ((__pytra_int((__pytra_int(checker) % __pytra_int(2L))) == __pytra_int(0L))) {
                                    base_r = __pytra_float(0.85)
                                    base_g = __pytra_float(0.85)
                                    base_b = __pytra_float(0.85)
                                } else {
                                    base_r = __pytra_float(0.2)
                                    base_g = __pytra_float(0.2)
                                    base_b = __pytra_float(0.2)
                                }
                            }
                        }
                        var shade: Double = __pytra_float((__pytra_float(0.12) + __pytra_float((__pytra_float(0.88) * __pytra_float(diff)))))
                        r = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float(clamp01((__pytra_float(base_r) * __pytra_float(shade)))))))
                        g = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float(clamp01((__pytra_float(base_g) * __pytra_float(shade)))))))
                        b = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float(clamp01((__pytra_float(base_b) * __pytra_float(shade)))))))
                    } else {
                        var tsky: Double = __pytra_float((__pytra_float(0.5) * __pytra_float((__pytra_float(dy) + __pytra_float(1.0)))))
                        r = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float(0.65) + __pytra_float((__pytra_float(0.2) * __pytra_float(tsky))))))))
                        g = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float(0.75) + __pytra_float((__pytra_float(0.18) * __pytra_float(tsky))))))))
                        b = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float(0.9) + __pytra_float((__pytra_float(0.08) * __pytra_float(tsky))))))))
                    }
                    ar += r
                    ag += g
                    ab += b
                    ax += __step_3
                }
                ay += __step_2
            }
            var samples: Long = __pytra_int((__pytra_int(aa) * __pytra_int(aa)))
            pixels = __pytra_as_list(pixels); pixels.add((__pytra_int(__pytra_int(ar) / __pytra_int(samples))))
            pixels = __pytra_as_list(pixels); pixels.add((__pytra_int(__pytra_int(ag) / __pytra_int(samples))))
            pixels = __pytra_as_list(pixels); pixels.add((__pytra_int(__pytra_int(ab) / __pytra_int(samples))))
            x += __step_1
        }
        y += __step_0
    }
    return __pytra_as_list(pixels)
}

fun run_raytrace() {
    var width: Long = __pytra_int(1600L)
    var height: Long = __pytra_int(900L)
    var aa: Long = __pytra_int(2L)
    var out_path: String = __pytra_str("sample/out/02_raytrace_spheres.png")
    var start: Double = __pytra_float(__pytra_perf_counter())
    var pixels: MutableList<Any?> = __pytra_as_list(render(width, height, aa))
    __pytra_noop(out_path, width, height, pixels)
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_raytrace()
}
