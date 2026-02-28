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

func dot(ax float64, ay float64, az float64, bx float64, by float64, bz float64) float64 {
    return __pytra_float((__pytra_float((__pytra_float((__pytra_float(ax) * __pytra_float(bx))) + __pytra_float((__pytra_float(ay) * __pytra_float(by))))) + __pytra_float((__pytra_float(az) * __pytra_float(bz)))))
}

func length(x float64, y float64, z float64) float64 {
    return __pytra_float(math.Sqrt(__pytra_float((__pytra_float((__pytra_float((__pytra_float(x) * __pytra_float(x))) + __pytra_float((__pytra_float(y) * __pytra_float(y))))) + __pytra_float((__pytra_float(z) * __pytra_float(z)))))))
}

func normalize(x float64, y float64, z float64) []any {
    var l float64 = __pytra_float(length(x, y, z))
    if (__pytra_float(l) < __pytra_float(float64(1e-09))) {
        return __pytra_as_list([]any{float64(0.0), float64(0.0), float64(0.0)})
    }
    return __pytra_as_list([]any{(__pytra_float(x) / __pytra_float(l)), (__pytra_float(y) / __pytra_float(l)), (__pytra_float(z) / __pytra_float(l))})
}

func reflect(ix float64, iy float64, iz float64, nx float64, ny float64, nz float64) []any {
    var d float64 = __pytra_float((__pytra_float(dot(ix, iy, iz, nx, ny, nz)) * __pytra_float(float64(2.0))))
    return __pytra_as_list([]any{(__pytra_float(ix) - __pytra_float((__pytra_float(d) * __pytra_float(nx)))), (__pytra_float(iy) - __pytra_float((__pytra_float(d) * __pytra_float(ny)))), (__pytra_float(iz) - __pytra_float((__pytra_float(d) * __pytra_float(nz))))})
}

func refract(ix float64, iy float64, iz float64, nx float64, ny float64, nz float64, eta float64) []any {
    var cosi float64 = __pytra_float((-dot(ix, iy, iz, nx, ny, nz)))
    var sint2 float64 = __pytra_float((__pytra_float((__pytra_float(eta) * __pytra_float(eta))) * __pytra_float((__pytra_float(float64(1.0)) - __pytra_float((__pytra_float(cosi) * __pytra_float(cosi)))))))
    if (__pytra_float(sint2) > __pytra_float(float64(1.0))) {
        return __pytra_as_list(reflect(ix, iy, iz, nx, ny, nz))
    }
    var cost float64 = __pytra_float(math.Sqrt(__pytra_float((__pytra_float(float64(1.0)) - __pytra_float(sint2)))))
    var k float64 = __pytra_float(((__pytra_float(eta) * __pytra_float(cosi)) - cost))
    return __pytra_as_list([]any{((__pytra_float(eta) * __pytra_float(ix)) + (k * nx)), ((__pytra_float(eta) * __pytra_float(iy)) + (k * ny)), ((__pytra_float(eta) * __pytra_float(iz)) + (k * nz))})
}

func schlick(cos_theta float64, f0 float64) float64 {
    var m float64 = __pytra_float((__pytra_float(float64(1.0)) - __pytra_float(cos_theta)))
    return __pytra_float((__pytra_float(f0) + __pytra_float((__pytra_float((__pytra_float(float64(1.0)) - __pytra_float(f0))) * __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(m) * __pytra_float(m))) * __pytra_float(m))) * __pytra_float(m))) * __pytra_float(m)))))))
}

func sky_color(dx float64, dy float64, dz float64, tphase float64) []any {
    var t float64 = __pytra_float((__pytra_float(float64(0.5)) * __pytra_float((__pytra_float(dy) + __pytra_float(float64(1.0))))))
    var r float64 = __pytra_float((__pytra_float(float64(0.06)) + __pytra_float((__pytra_float(float64(0.2)) * __pytra_float(t)))))
    var g float64 = __pytra_float((__pytra_float(float64(0.1)) + __pytra_float((__pytra_float(float64(0.25)) * __pytra_float(t)))))
    var b float64 = __pytra_float((__pytra_float(float64(0.16)) + __pytra_float((__pytra_float(float64(0.45)) * __pytra_float(t)))))
    var band float64 = __pytra_float((float64(0.5) + (float64(0.5) * math.Sin(__pytra_float((__pytra_float((__pytra_float((__pytra_float(float64(8.0)) * __pytra_float(dx))) + __pytra_float((__pytra_float(float64(6.0)) * __pytra_float(dz))))) + __pytra_float(tphase)))))))
    r += (float64(0.08) * band)
    g += (float64(0.05) * band)
    b += (float64(0.12) * band)
    return __pytra_as_list([]any{clamp01(r), clamp01(g), clamp01(b)})
}

func sphere_intersect(ox float64, oy float64, oz float64, dx float64, dy float64, dz float64, cx float64, cy float64, cz float64, radius float64) float64 {
    var lx float64 = __pytra_float((__pytra_float(ox) - __pytra_float(cx)))
    var ly float64 = __pytra_float((__pytra_float(oy) - __pytra_float(cy)))
    var lz float64 = __pytra_float((__pytra_float(oz) - __pytra_float(cz)))
    var b float64 = __pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(dx))) + __pytra_float((__pytra_float(ly) * __pytra_float(dy))))) + __pytra_float((__pytra_float(lz) * __pytra_float(dz)))))
    var c float64 = __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(lx) * __pytra_float(lx))) + __pytra_float((__pytra_float(ly) * __pytra_float(ly))))) + __pytra_float((__pytra_float(lz) * __pytra_float(lz))))) - __pytra_float((__pytra_float(radius) * __pytra_float(radius)))))
    var h float64 = __pytra_float((__pytra_float((__pytra_float(b) * __pytra_float(b))) - __pytra_float(c)))
    if (__pytra_float(h) < __pytra_float(float64(0.0))) {
        return __pytra_float((-float64(1.0)))
    }
    var s float64 = __pytra_float(math.Sqrt(__pytra_float(h)))
    var t0 float64 = __pytra_float(((-b) - s))
    if (__pytra_float(t0) > __pytra_float(float64(0.0001))) {
        return __pytra_float(t0)
    }
    var t1 float64 = __pytra_float(((-b) + s))
    if (__pytra_float(t1) > __pytra_float(float64(0.0001))) {
        return __pytra_float(t1)
    }
    return __pytra_float((-float64(1.0)))
}

func palette_332() []any {
    var p []any = __pytra_as_list(__pytra_bytearray((__pytra_int(int64(256)) * __pytra_int(int64(3)))))
    var __hoisted_cast_1 float64 = __pytra_float(__pytra_float(int64(7)))
    var __hoisted_cast_2 float64 = __pytra_float(__pytra_float(int64(3)))
    __step_0 := __pytra_int(int64(1))
    for i := __pytra_int(int64(0)); (__step_0 >= 0 && i < __pytra_int(int64(256))) || (__step_0 < 0 && i > __pytra_int(int64(256))); i += __step_0 {
        var r int64 = __pytra_int((__pytra_int((__pytra_int(i) + __pytra_int(int64(5)))) + __pytra_int(int64(7))))
        var g int64 = __pytra_int((__pytra_int((__pytra_int(i) + __pytra_int(int64(2)))) + __pytra_int(int64(7))))
        var b int64 = __pytra_int((__pytra_int(i) + __pytra_int(int64(3))))
        __pytra_set_index(p, (__pytra_int((__pytra_int(i) * __pytra_int(int64(3)))) + __pytra_int(int64(0))), __pytra_int((__pytra_float((__pytra_int(int64(255)) * __pytra_int(r))) / __pytra_float(__hoisted_cast_1))))
        __pytra_set_index(p, (__pytra_int((__pytra_int(i) * __pytra_int(int64(3)))) + __pytra_int(int64(1))), __pytra_int((__pytra_float((__pytra_int(int64(255)) * __pytra_int(g))) / __pytra_float(__hoisted_cast_1))))
        __pytra_set_index(p, (__pytra_int((__pytra_int(i) * __pytra_int(int64(3)))) + __pytra_int(int64(2))), __pytra_int((__pytra_float((__pytra_int(int64(255)) * __pytra_int(b))) / __pytra_float(__hoisted_cast_2))))
    }
    return __pytra_as_list(__pytra_bytes(p))
}

func quantize_332(r float64, g float64, b float64) int64 {
    var rr int64 = __pytra_int(__pytra_int((__pytra_float(clamp01(r)) * __pytra_float(float64(255.0)))))
    var gg int64 = __pytra_int(__pytra_int((__pytra_float(clamp01(g)) * __pytra_float(float64(255.0)))))
    var bb int64 = __pytra_int(__pytra_int((__pytra_float(clamp01(b)) * __pytra_float(float64(255.0)))))
    return __pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int(rr) + __pytra_int(int64(5)))) + __pytra_int(int64(5)))) + __pytra_int((__pytra_int((__pytra_int(gg) + __pytra_int(int64(5)))) + __pytra_int(int64(2)))))) + __pytra_int((__pytra_int(bb) + __pytra_int(int64(6))))))
}

func render_frame(width int64, height int64, frame_id int64, frames_n int64) []any {
    var t float64 = __pytra_float((__pytra_float(frame_id) / __pytra_float(frames_n)))
    var tphase float64 = __pytra_float(((float64(2.0) * math.Pi) * t))
    var cam_r float64 = __pytra_float(float64(3.0))
    var cam_x float64 = __pytra_float((cam_r * math.Cos(__pytra_float((tphase * float64(0.9))))))
    var cam_y float64 = __pytra_float((float64(1.1) + (float64(0.25) * math.Sin(__pytra_float((tphase * float64(0.6)))))))
    var cam_z float64 = __pytra_float((cam_r * math.Sin(__pytra_float((tphase * float64(0.9))))))
    var look_x float64 = __pytra_float(float64(0.0))
    var look_y float64 = __pytra_float(float64(0.35))
    var look_z float64 = __pytra_float(float64(0.0))
    __tuple_0 := __pytra_as_list(normalize((look_x - cam_x), (look_y - cam_y), (look_z - cam_z)))
    var fwd_x float64 = __pytra_float(__tuple_0[0])
    _ = fwd_x
    var fwd_y float64 = __pytra_float(__tuple_0[1])
    _ = fwd_y
    var fwd_z float64 = __pytra_float(__tuple_0[2])
    _ = fwd_z
    __tuple_1 := __pytra_as_list(normalize(fwd_z, float64(0.0), (-fwd_x)))
    var right_x float64 = __pytra_float(__tuple_1[0])
    _ = right_x
    var right_y float64 = __pytra_float(__tuple_1[1])
    _ = right_y
    var right_z float64 = __pytra_float(__tuple_1[2])
    _ = right_z
    __tuple_2 := __pytra_as_list(normalize(((right_y * fwd_z) - (right_z * fwd_y)), ((right_z * fwd_x) - (right_x * fwd_z)), ((right_x * fwd_y) - (right_y * fwd_x))))
    var up_x float64 = __pytra_float(__tuple_2[0])
    _ = up_x
    var up_y float64 = __pytra_float(__tuple_2[1])
    _ = up_y
    var up_z float64 = __pytra_float(__tuple_2[2])
    _ = up_z
    var s0x float64 = __pytra_float((float64(0.9) * math.Cos(__pytra_float((float64(1.3) * tphase)))))
    var s0y float64 = __pytra_float((float64(0.15) + (float64(0.35) * math.Sin(__pytra_float((float64(1.7) * tphase))))))
    var s0z float64 = __pytra_float((float64(0.9) * math.Sin(__pytra_float((float64(1.3) * tphase)))))
    var s1x float64 = __pytra_float((float64(1.2) * math.Cos(__pytra_float(((float64(1.3) * tphase) + float64(2.094))))))
    var s1y float64 = __pytra_float((float64(0.1) + (float64(0.4) * math.Sin(__pytra_float(((float64(1.1) * tphase) + float64(0.8)))))))
    var s1z float64 = __pytra_float((float64(1.2) * math.Sin(__pytra_float(((float64(1.3) * tphase) + float64(2.094))))))
    var s2x float64 = __pytra_float((float64(1.0) * math.Cos(__pytra_float(((float64(1.3) * tphase) + float64(4.188))))))
    var s2y float64 = __pytra_float((float64(0.2) + (float64(0.3) * math.Sin(__pytra_float(((float64(1.5) * tphase) + float64(1.9)))))))
    var s2z float64 = __pytra_float((float64(1.0) * math.Sin(__pytra_float(((float64(1.3) * tphase) + float64(4.188))))))
    _ = float64(0.35)
    var lx float64 = __pytra_float((float64(2.4) * math.Cos(__pytra_float((tphase * float64(1.8))))))
    var ly float64 = __pytra_float((float64(1.8) + (float64(0.8) * math.Sin(__pytra_float((tphase * float64(1.2)))))))
    var lz float64 = __pytra_float((float64(2.4) * math.Sin(__pytra_float((tphase * float64(1.8))))))
    var frame []any = __pytra_as_list(__pytra_bytearray((__pytra_int(width) * __pytra_int(height))))
    var aspect float64 = __pytra_float((__pytra_float(width) / __pytra_float(height)))
    var fov float64 = __pytra_float(float64(1.25))
    var __hoisted_cast_3 float64 = __pytra_float(__pytra_float(height))
    var __hoisted_cast_4 float64 = __pytra_float(__pytra_float(width))
    __step_3 := __pytra_int(int64(1))
    for py := __pytra_int(int64(0)); (__step_3 >= 0 && py < __pytra_int(height)) || (__step_3 < 0 && py > __pytra_int(height)); py += __step_3 {
        var row_base int64 = __pytra_int((__pytra_int(py) * __pytra_int(width)))
        var sy float64 = __pytra_float((__pytra_float(float64(1.0)) - __pytra_float((__pytra_float((__pytra_float(float64(2.0)) * __pytra_float((__pytra_float(py) + __pytra_float(float64(0.5)))))) / __pytra_float(__hoisted_cast_3)))))
        __step_4 := __pytra_int(int64(1))
        for px := __pytra_int(int64(0)); (__step_4 >= 0 && px < __pytra_int(width)) || (__step_4 < 0 && px > __pytra_int(width)); px += __step_4 {
            var sx float64 = __pytra_float((__pytra_float((__pytra_float((__pytra_float((__pytra_float(float64(2.0)) * __pytra_float((__pytra_float(px) + __pytra_float(float64(0.5)))))) / __pytra_float(__hoisted_cast_4))) - __pytra_float(float64(1.0)))) * __pytra_float(aspect)))
            var rx float64 = __pytra_float((fwd_x + (fov * ((sx * right_x) + (sy * up_x)))))
            var ry float64 = __pytra_float((fwd_y + (fov * ((sx * right_y) + (sy * up_y)))))
            var rz float64 = __pytra_float((fwd_z + (fov * ((sx * right_z) + (sy * up_z)))))
            __tuple_5 := __pytra_as_list(normalize(rx, ry, rz))
            var dx float64 = __pytra_float(__tuple_5[0])
            _ = dx
            var dy float64 = __pytra_float(__tuple_5[1])
            _ = dy
            var dz float64 = __pytra_float(__tuple_5[2])
            _ = dz
            var best_t float64 = __pytra_float(float64(1000000000.0))
            var hit_kind int64 = __pytra_int(int64(0))
            var r float64 = __pytra_float(float64(0.0))
            var g float64 = __pytra_float(float64(0.0))
            var b float64 = __pytra_float(float64(0.0))
            if (__pytra_float(dy) < __pytra_float((-float64(1e-06)))) {
                var tf float64 = __pytra_float((__pytra_float(((-float64(1.2)) - cam_y)) / __pytra_float(dy)))
                if ((__pytra_float(tf) > __pytra_float(float64(0.0001))) && (__pytra_float(tf) < __pytra_float(best_t))) {
                    best_t = __pytra_float(tf)
                    hit_kind = __pytra_int(int64(1))
                }
            }
            var t0 float64 = __pytra_float(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, float64(0.65)))
            if ((__pytra_float(t0) > __pytra_float(float64(0.0))) && (__pytra_float(t0) < __pytra_float(best_t))) {
                best_t = __pytra_float(t0)
                hit_kind = __pytra_int(int64(2))
            }
            var t1 float64 = __pytra_float(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, float64(0.72)))
            if ((__pytra_float(t1) > __pytra_float(float64(0.0))) && (__pytra_float(t1) < __pytra_float(best_t))) {
                best_t = __pytra_float(t1)
                hit_kind = __pytra_int(int64(3))
            }
            var t2 float64 = __pytra_float(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, float64(0.58)))
            if ((__pytra_float(t2) > __pytra_float(float64(0.0))) && (__pytra_float(t2) < __pytra_float(best_t))) {
                best_t = __pytra_float(t2)
                hit_kind = __pytra_int(int64(4))
            }
            if (__pytra_int(hit_kind) == __pytra_int(int64(0))) {
                __tuple_6 := __pytra_as_list(sky_color(dx, dy, dz, tphase))
                r = __pytra_float(__tuple_6[0])
                g = __pytra_float(__tuple_6[1])
                b = __pytra_float(__tuple_6[2])
            } else {
                if (__pytra_int(hit_kind) == __pytra_int(int64(1))) {
                    var hx float64 = __pytra_float((cam_x + (best_t * dx)))
                    var hz float64 = __pytra_float((cam_z + (best_t * dz)))
                    var cx int64 = __pytra_int(__pytra_int(math.Floor(__pytra_float((hx * float64(2.0))))))
                    var cz int64 = __pytra_int(__pytra_int(math.Floor(__pytra_float((hz * float64(2.0))))))
                    var checker int64 = __pytra_int(__pytra_ifexp((__pytra_int((__pytra_int((__pytra_int(cx) + __pytra_int(cz))) % __pytra_int(int64(2)))) == __pytra_int(int64(0))), int64(0), int64(1)))
                    var base_r float64 = __pytra_float(__pytra_ifexp((__pytra_int(checker) == __pytra_int(int64(0))), float64(0.1), float64(0.04)))
                    var base_g float64 = __pytra_float(__pytra_ifexp((__pytra_int(checker) == __pytra_int(int64(0))), float64(0.11), float64(0.05)))
                    var base_b float64 = __pytra_float(__pytra_ifexp((__pytra_int(checker) == __pytra_int(int64(0))), float64(0.13), float64(0.08)))
                    var lxv float64 = __pytra_float((lx - hx))
                    var lyv float64 = __pytra_float((ly - (-float64(1.2))))
                    var lzv float64 = __pytra_float((lz - hz))
                    __tuple_7 := __pytra_as_list(normalize(lxv, lyv, lzv))
                    var ldx float64 = __pytra_float(__tuple_7[0])
                    _ = ldx
                    var ldy float64 = __pytra_float(__tuple_7[1])
                    _ = ldy
                    var ldz float64 = __pytra_float(__tuple_7[2])
                    _ = ldz
                    var ndotl float64 = __pytra_float(__pytra_max(ldy, float64(0.0)))
                    var ldist2 float64 = __pytra_float((((lxv * lxv) + (lyv * lyv)) + (lzv * lzv)))
                    var glow float64 = __pytra_float((__pytra_float(float64(8.0)) / __pytra_float((float64(1.0) + ldist2))))
                    r = __pytra_float(((base_r + (float64(0.8) * glow)) + (float64(0.2) * ndotl)))
                    g = __pytra_float(((base_g + (float64(0.5) * glow)) + (float64(0.18) * ndotl)))
                    b = __pytra_float(((base_b + (float64(1.0) * glow)) + (float64(0.24) * ndotl)))
                } else {
                    var cx float64 = __pytra_float(float64(0.0))
                    var cy float64 = __pytra_float(float64(0.0))
                    var cz float64 = __pytra_float(float64(0.0))
                    var rad float64 = __pytra_float(float64(1.0))
                    if (__pytra_int(hit_kind) == __pytra_int(int64(2))) {
                        cx = __pytra_float(s0x)
                        cy = __pytra_float(s0y)
                        cz = __pytra_float(s0z)
                        rad = __pytra_float(float64(0.65))
                    } else {
                        if (__pytra_int(hit_kind) == __pytra_int(int64(3))) {
                            cx = __pytra_float(s1x)
                            cy = __pytra_float(s1y)
                            cz = __pytra_float(s1z)
                            rad = __pytra_float(float64(0.72))
                        } else {
                            cx = __pytra_float(s2x)
                            cy = __pytra_float(s2y)
                            cz = __pytra_float(s2z)
                            rad = __pytra_float(float64(0.58))
                        }
                    }
                    var hx float64 = __pytra_float((cam_x + (best_t * dx)))
                    var hy float64 = __pytra_float((cam_y + (best_t * dy)))
                    var hz float64 = __pytra_float((cam_z + (best_t * dz)))
                    __tuple_8 := __pytra_as_list(normalize((__pytra_float((hx - cx)) / __pytra_float(rad)), (__pytra_float((hy - cy)) / __pytra_float(rad)), (__pytra_float((hz - cz)) / __pytra_float(rad))))
                    var nx float64 = __pytra_float(__tuple_8[0])
                    _ = nx
                    var ny float64 = __pytra_float(__tuple_8[1])
                    _ = ny
                    var nz float64 = __pytra_float(__tuple_8[2])
                    _ = nz
                    __tuple_9 := __pytra_as_list(reflect(dx, dy, dz, nx, ny, nz))
                    var rdx float64 = __pytra_float(__tuple_9[0])
                    _ = rdx
                    var rdy float64 = __pytra_float(__tuple_9[1])
                    _ = rdy
                    var rdz float64 = __pytra_float(__tuple_9[2])
                    _ = rdz
                    __tuple_10 := __pytra_as_list(refract(dx, dy, dz, nx, ny, nz, (__pytra_float(float64(1.0)) / __pytra_float(float64(1.45)))))
                    var tdx float64 = __pytra_float(__tuple_10[0])
                    _ = tdx
                    var tdy float64 = __pytra_float(__tuple_10[1])
                    _ = tdy
                    var tdz float64 = __pytra_float(__tuple_10[2])
                    _ = tdz
                    __tuple_11 := __pytra_as_list(sky_color(rdx, rdy, rdz, tphase))
                    var sr float64 = __pytra_float(__tuple_11[0])
                    _ = sr
                    var sg float64 = __pytra_float(__tuple_11[1])
                    _ = sg
                    var sb float64 = __pytra_float(__tuple_11[2])
                    _ = sb
                    __tuple_12 := __pytra_as_list(sky_color(tdx, tdy, tdz, (tphase + float64(0.8))))
                    var tr float64 = __pytra_float(__tuple_12[0])
                    _ = tr
                    var tg float64 = __pytra_float(__tuple_12[1])
                    _ = tg
                    var tb float64 = __pytra_float(__tuple_12[2])
                    _ = tb
                    var cosi float64 = __pytra_float(__pytra_max((-(((dx * nx) + (dy * ny)) + (dz * nz))), float64(0.0)))
                    var fr float64 = __pytra_float(schlick(cosi, float64(0.04)))
                    r = __pytra_float(((tr * (__pytra_float(float64(1.0)) - __pytra_float(fr))) + (sr * fr)))
                    g = __pytra_float(((tg * (__pytra_float(float64(1.0)) - __pytra_float(fr))) + (sg * fr)))
                    b = __pytra_float(((tb * (__pytra_float(float64(1.0)) - __pytra_float(fr))) + (sb * fr)))
                    var lxv float64 = __pytra_float((lx - hx))
                    var lyv float64 = __pytra_float((ly - hy))
                    var lzv float64 = __pytra_float((lz - hz))
                    __tuple_13 := __pytra_as_list(normalize(lxv, lyv, lzv))
                    var ldx float64 = __pytra_float(__tuple_13[0])
                    _ = ldx
                    var ldy float64 = __pytra_float(__tuple_13[1])
                    _ = ldy
                    var ldz float64 = __pytra_float(__tuple_13[2])
                    _ = ldz
                    var ndotl float64 = __pytra_float(__pytra_max((((nx * ldx) + (ny * ldy)) + (nz * ldz)), float64(0.0)))
                    __tuple_14 := __pytra_as_list(normalize((ldx - dx), (ldy - dy), (ldz - dz)))
                    var hvx float64 = __pytra_float(__tuple_14[0])
                    _ = hvx
                    var hvy float64 = __pytra_float(__tuple_14[1])
                    _ = hvy
                    var hvz float64 = __pytra_float(__tuple_14[2])
                    _ = hvz
                    var ndoth float64 = __pytra_float(__pytra_max((((nx * hvx) + (ny * hvy)) + (nz * hvz)), float64(0.0)))
                    var spec float64 = __pytra_float((ndoth * ndoth))
                    spec = __pytra_float((spec * spec))
                    spec = __pytra_float((spec * spec))
                    spec = __pytra_float((spec * spec))
                    var glow float64 = __pytra_float((__pytra_float(float64(10.0)) / __pytra_float((((float64(1.0) + (lxv * lxv)) + (lyv * lyv)) + (lzv * lzv)))))
                    r += (((float64(0.2) * ndotl) + (float64(0.8) * spec)) + (float64(0.45) * glow))
                    g += (((float64(0.18) * ndotl) + (float64(0.6) * spec)) + (float64(0.35) * glow))
                    b += (((float64(0.26) * ndotl) + (float64(1.0) * spec)) + (float64(0.65) * glow))
                    if (__pytra_int(hit_kind) == __pytra_int(int64(2))) {
                        r *= float64(0.95)
                        g *= float64(1.05)
                        b *= float64(1.1)
                    } else {
                        if (__pytra_int(hit_kind) == __pytra_int(int64(3))) {
                            r *= float64(1.08)
                            g *= float64(0.98)
                            b *= float64(1.04)
                        } else {
                            r *= float64(1.02)
                            g *= float64(1.1)
                            b *= float64(0.95)
                        }
                    }
                }
            }
            r = __pytra_float(math.Sqrt(__pytra_float(clamp01(r))))
            g = __pytra_float(math.Sqrt(__pytra_float(clamp01(g))))
            b = __pytra_float(math.Sqrt(__pytra_float(clamp01(b))))
            __pytra_set_index(frame, (__pytra_int(row_base) + __pytra_int(px)), quantize_332(r, g, b))
        }
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_16_glass_sculpture_chaos() {
    var width int64 = __pytra_int(int64(320))
    var height int64 = __pytra_int(int64(240))
    var frames_n int64 = __pytra_int(int64(72))
    var out_path string = __pytra_str("sample/out/16_glass_sculpture_chaos.gif")
    var start float64 = __pytra_float(__pytra_perf_counter())
    var frames []any = __pytra_as_list([]any{})
    __step_0 := __pytra_int(int64(1))
    for i := __pytra_int(int64(0)); (__step_0 >= 0 && i < __pytra_int(frames_n)) || (__step_0 < 0 && i > __pytra_int(frames_n)); i += __step_0 {
        frames = append(__pytra_as_list(frames), render_frame(width, height, i, frames_n))
    }
    __pytra_noop(out_path, width, height, frames, palette_332())
    var elapsed float64 = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_16_glass_sculpture_chaos()
}
