package main

import (
    "math"
)


// 16: Sample that ray-traces chaotic rotation of glass sculptures and outputs a GIF.

func clamp01(v float64) float64 {
    if (v < float64(0.0)) {
        return float64(0.0)
    }
    if (v > float64(1.0)) {
        return float64(1.0)
    }
    return v
}

func dot(ax float64, ay float64, az float64, bx float64, by float64, bz float64) float64 {
    return (((ax * bx) + (ay * by)) + (az * bz))
}

func length(x float64, y float64, z float64) float64 {
    return math.Sqrt((((x * x) + (y * y)) + (z * z)))
}

func normalize(x float64, y float64, z float64) []any {
    var l float64 = length(x, y, z)
    if (l < float64(1e-09)) {
        return __pytra_as_list([]any{float64(0.0), float64(0.0), float64(0.0)})
    }
    return __pytra_as_list([]any{(x / l), (y / l), (z / l)})
}

func reflect(ix float64, iy float64, iz float64, nx float64, ny float64, nz float64) []any {
    var d float64 = (dot(ix, iy, iz, nx, ny, nz) * float64(2.0))
    return __pytra_as_list([]any{(ix - (d * nx)), (iy - (d * ny)), (iz - (d * nz))})
}

func refract(ix float64, iy float64, iz float64, nx float64, ny float64, nz float64, eta float64) []any {
    var cosi float64 = (-dot(ix, iy, iz, nx, ny, nz))
    var sint2 float64 = ((eta * eta) * (float64(1.0) - (cosi * cosi)))
    if (sint2 > float64(1.0)) {
        return __pytra_as_list(reflect(ix, iy, iz, nx, ny, nz))
    }
    var cost float64 = math.Sqrt((float64(1.0) - sint2))
    var k float64 = ((eta * cosi) - cost)
    return __pytra_as_list([]any{((eta * ix) + (k * nx)), ((eta * iy) + (k * ny)), ((eta * iz) + (k * nz))})
}

func schlick(cos_theta float64, f0 float64) float64 {
    var m float64 = (float64(1.0) - cos_theta)
    return (f0 + ((float64(1.0) - f0) * ((((m * m) * m) * m) * m)))
}

func sky_color(dx float64, dy float64, dz float64, tphase float64) []any {
    var t float64 = (float64(0.5) * (dy + float64(1.0)))
    var r float64 = (float64(0.06) + (float64(0.2) * t))
    var g float64 = (float64(0.1) + (float64(0.25) * t))
    var b float64 = (float64(0.16) + (float64(0.45) * t))
    var band float64 = (float64(0.5) + (float64(0.5) * math.Sin((((float64(8.0) * dx) + (float64(6.0) * dz)) + tphase))))
    r += (float64(0.08) * band)
    g += (float64(0.05) * band)
    b += (float64(0.12) * band)
    return __pytra_as_list([]any{clamp01(r), clamp01(g), clamp01(b)})
}

func sphere_intersect(ox float64, oy float64, oz float64, dx float64, dy float64, dz float64, cx float64, cy float64, cz float64, radius float64) float64 {
    var lx float64 = (ox - cx)
    var ly float64 = (oy - cy)
    var lz float64 = (oz - cz)
    var b float64 = (((lx * dx) + (ly * dy)) + (lz * dz))
    var c float64 = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (radius * radius))
    var h float64 = ((b * b) - c)
    if (h < float64(0.0)) {
        return (-float64(1.0))
    }
    var s float64 = math.Sqrt(h)
    var t0 float64 = ((-b) - s)
    if (__pytra_float(t0) > float64(0.0001)) {
        return t0
    }
    var t1 float64 = ((-b) + s)
    if (__pytra_float(t1) > float64(0.0001)) {
        return t1
    }
    return (-float64(1.0))
}

func palette_332() []any {
    var p []any = __pytra_as_list(__pytra_bytearray((int64(256) * int64(3))))
    var __hoisted_cast_1 float64 = __pytra_float(int64(7))
    var __hoisted_cast_2 float64 = __pytra_float(int64(3))
    for i := int64(0); i < int64(256); i += 1 {
        var r int64 = ((i + int64(5)) + int64(7))
        var g int64 = ((i + int64(2)) + int64(7))
        var b int64 = (i + int64(3))
        __pytra_set_index(p, ((i * int64(3)) + int64(0)), __pytra_int((float64((int64(255) * r)) / __hoisted_cast_1)))
        __pytra_set_index(p, ((i * int64(3)) + int64(1)), __pytra_int((float64((int64(255) * g)) / __hoisted_cast_1)))
        __pytra_set_index(p, ((i * int64(3)) + int64(2)), __pytra_int((float64((int64(255) * b)) / __hoisted_cast_2)))
    }
    return __pytra_as_list(__pytra_bytes(p))
}

func quantize_332(r float64, g float64, b float64) int64 {
    var rr int64 = __pytra_int((clamp01(r) * float64(255.0)))
    var gg int64 = __pytra_int((clamp01(g) * float64(255.0)))
    var bb int64 = __pytra_int((clamp01(b) * float64(255.0)))
    return ((((rr + int64(5)) + int64(5)) + ((gg + int64(5)) + int64(2))) + (bb + int64(6)))
}

func render_frame(width int64, height int64, frame_id int64, frames_n int64) []any {
    var t float64 = (float64(frame_id) / float64(frames_n))
    var tphase float64 = ((float64(2.0) * math.Pi) * t)
    var cam_r float64 = float64(3.0)
    var cam_x float64 = (cam_r * math.Cos(__pytra_float((tphase * float64(0.9)))))
    var cam_y float64 = (float64(1.1) + (float64(0.25) * math.Sin(__pytra_float((tphase * float64(0.6))))))
    var cam_z float64 = (cam_r * math.Sin(__pytra_float((tphase * float64(0.9)))))
    var look_x float64 = float64(0.0)
    var look_y float64 = float64(0.35)
    var look_z float64 = float64(0.0)
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
    var s0x float64 = (float64(0.9) * math.Cos(__pytra_float((float64(1.3) * tphase))))
    var s0y float64 = (float64(0.15) + (float64(0.35) * math.Sin(__pytra_float((float64(1.7) * tphase)))))
    var s0z float64 = (float64(0.9) * math.Sin(__pytra_float((float64(1.3) * tphase))))
    var s1x float64 = (float64(1.2) * math.Cos(__pytra_float(((float64(1.3) * tphase) + float64(2.094)))))
    var s1y float64 = (float64(0.1) + (float64(0.4) * math.Sin(__pytra_float(((float64(1.1) * tphase) + float64(0.8))))))
    var s1z float64 = (float64(1.2) * math.Sin(__pytra_float(((float64(1.3) * tphase) + float64(2.094)))))
    var s2x float64 = (float64(1.0) * math.Cos(__pytra_float(((float64(1.3) * tphase) + float64(4.188)))))
    var s2y float64 = (float64(0.2) + (float64(0.3) * math.Sin(__pytra_float(((float64(1.5) * tphase) + float64(1.9))))))
    var s2z float64 = (float64(1.0) * math.Sin(__pytra_float(((float64(1.3) * tphase) + float64(4.188)))))
    _ = float64(0.35)
    var lx float64 = (float64(2.4) * math.Cos(__pytra_float((tphase * float64(1.8)))))
    var ly float64 = (float64(1.8) + (float64(0.8) * math.Sin(__pytra_float((tphase * float64(1.2))))))
    var lz float64 = (float64(2.4) * math.Sin(__pytra_float((tphase * float64(1.8)))))
    var frame []any = __pytra_as_list(__pytra_bytearray((width * height)))
    var aspect float64 = (float64(width) / float64(height))
    var fov float64 = float64(1.25)
    var __hoisted_cast_3 float64 = __pytra_float(height)
    var __hoisted_cast_4 float64 = __pytra_float(width)
    for py := int64(0); py < height; py += 1 {
        var row_base int64 = (py * width)
        var sy float64 = (float64(1.0) - ((float64(2.0) * (float64(py) + float64(0.5))) / __hoisted_cast_3))
        for px := int64(0); px < width; px += 1 {
            var sx float64 = ((((float64(2.0) * (float64(px) + float64(0.5))) / __hoisted_cast_4) - float64(1.0)) * aspect)
            var rx float64 = (fwd_x + (fov * ((sx * right_x) + (sy * up_x))))
            var ry float64 = (fwd_y + (fov * ((sx * right_y) + (sy * up_y))))
            var rz float64 = (fwd_z + (fov * ((sx * right_z) + (sy * up_z))))
            __tuple_3 := __pytra_as_list(normalize(rx, ry, rz))
            var dx float64 = __pytra_float(__tuple_3[0])
            _ = dx
            var dy float64 = __pytra_float(__tuple_3[1])
            _ = dy
            var dz float64 = __pytra_float(__tuple_3[2])
            _ = dz
            var best_t float64 = float64(1000000000.0)
            var hit_kind int64 = int64(0)
            var r float64 = float64(0.0)
            var g float64 = float64(0.0)
            var b float64 = float64(0.0)
            if (__pytra_float(dy) < (-float64(1e-06))) {
                var tf float64 = (__pytra_float(((-float64(1.2)) - cam_y)) / __pytra_float(dy))
                if ((__pytra_float(tf) > float64(0.0001)) && (__pytra_float(tf) < best_t)) {
                    best_t = tf
                    hit_kind = int64(1)
                }
            }
            var t0 float64 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, float64(0.65))
            if ((t0 > float64(0.0)) && (t0 < best_t)) {
                best_t = t0
                hit_kind = int64(2)
            }
            var t1 float64 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, float64(0.72))
            if ((t1 > float64(0.0)) && (t1 < best_t)) {
                best_t = t1
                hit_kind = int64(3)
            }
            var t2 float64 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, float64(0.58))
            if ((t2 > float64(0.0)) && (t2 < best_t)) {
                best_t = t2
                hit_kind = int64(4)
            }
            if (hit_kind == int64(0)) {
                __tuple_4 := __pytra_as_list(sky_color(dx, dy, dz, tphase))
                r = __pytra_float(__tuple_4[0])
                g = __pytra_float(__tuple_4[1])
                b = __pytra_float(__tuple_4[2])
            } else {
                if (hit_kind == int64(1)) {
                    var hx float64 = (cam_x + (best_t * dx))
                    var hz float64 = (cam_z + (best_t * dz))
                    var cx int64 = __pytra_int(math.Floor(__pytra_float((hx * float64(2.0)))))
                    var cz int64 = __pytra_int(math.Floor(__pytra_float((hz * float64(2.0)))))
                    var checker int64 = __pytra_ifexp((((cx + cz) % int64(2)) == int64(0)), int64(0), int64(1))
                    var base_r float64 = __pytra_ifexp((checker == int64(0)), float64(0.1), float64(0.04))
                    var base_g float64 = __pytra_ifexp((checker == int64(0)), float64(0.11), float64(0.05))
                    var base_b float64 = __pytra_ifexp((checker == int64(0)), float64(0.13), float64(0.08))
                    var lxv float64 = (lx - hx)
                    var lyv float64 = (ly - (-float64(1.2)))
                    var lzv float64 = (lz - hz)
                    __tuple_5 := __pytra_as_list(normalize(lxv, lyv, lzv))
                    var ldx float64 = __pytra_float(__tuple_5[0])
                    _ = ldx
                    var ldy float64 = __pytra_float(__tuple_5[1])
                    _ = ldy
                    var ldz float64 = __pytra_float(__tuple_5[2])
                    _ = ldz
                    var ndotl float64 = __pytra_max(ldy, float64(0.0))
                    var ldist2 float64 = (((lxv * lxv) + (lyv * lyv)) + (lzv * lzv))
                    var glow float64 = (float64(8.0) / __pytra_float((float64(1.0) + ldist2)))
                    r = ((base_r + (float64(0.8) * glow)) + (float64(0.2) * ndotl))
                    g = ((base_g + (float64(0.5) * glow)) + (float64(0.18) * ndotl))
                    b = ((base_b + (float64(1.0) * glow)) + (float64(0.24) * ndotl))
                } else {
                    var cx float64 = float64(0.0)
                    var cy float64 = float64(0.0)
                    var cz float64 = float64(0.0)
                    var rad float64 = float64(1.0)
                    if (hit_kind == int64(2)) {
                        cx = s0x
                        cy = s0y
                        cz = s0z
                        rad = float64(0.65)
                    } else {
                        if (hit_kind == int64(3)) {
                            cx = s1x
                            cy = s1y
                            cz = s1z
                            rad = float64(0.72)
                        } else {
                            cx = s2x
                            cy = s2y
                            cz = s2z
                            rad = float64(0.58)
                        }
                    }
                    var hx float64 = (cam_x + (best_t * dx))
                    var hy float64 = (cam_y + (best_t * dy))
                    var hz float64 = (cam_z + (best_t * dz))
                    __tuple_6 := __pytra_as_list(normalize((__pytra_float((hx - cx)) / rad), (__pytra_float((hy - cy)) / rad), (__pytra_float((hz - cz)) / rad)))
                    var nx float64 = __pytra_float(__tuple_6[0])
                    _ = nx
                    var ny float64 = __pytra_float(__tuple_6[1])
                    _ = ny
                    var nz float64 = __pytra_float(__tuple_6[2])
                    _ = nz
                    __tuple_7 := __pytra_as_list(reflect(dx, dy, dz, nx, ny, nz))
                    var rdx float64 = __pytra_float(__tuple_7[0])
                    _ = rdx
                    var rdy float64 = __pytra_float(__tuple_7[1])
                    _ = rdy
                    var rdz float64 = __pytra_float(__tuple_7[2])
                    _ = rdz
                    __tuple_8 := __pytra_as_list(refract(dx, dy, dz, nx, ny, nz, (float64(1.0) / float64(1.45))))
                    var tdx float64 = __pytra_float(__tuple_8[0])
                    _ = tdx
                    var tdy float64 = __pytra_float(__tuple_8[1])
                    _ = tdy
                    var tdz float64 = __pytra_float(__tuple_8[2])
                    _ = tdz
                    __tuple_9 := __pytra_as_list(sky_color(rdx, rdy, rdz, tphase))
                    var sr float64 = __pytra_float(__tuple_9[0])
                    _ = sr
                    var sg float64 = __pytra_float(__tuple_9[1])
                    _ = sg
                    var sb float64 = __pytra_float(__tuple_9[2])
                    _ = sb
                    __tuple_10 := __pytra_as_list(sky_color(tdx, tdy, tdz, (tphase + float64(0.8))))
                    var tr float64 = __pytra_float(__tuple_10[0])
                    _ = tr
                    var tg float64 = __pytra_float(__tuple_10[1])
                    _ = tg
                    var tb float64 = __pytra_float(__tuple_10[2])
                    _ = tb
                    var cosi float64 = __pytra_max((-(((dx * nx) + (dy * ny)) + (dz * nz))), float64(0.0))
                    var fr float64 = schlick(cosi, float64(0.04))
                    r = ((tr * (float64(1.0) - fr)) + (sr * fr))
                    g = ((tg * (float64(1.0) - fr)) + (sg * fr))
                    b = ((tb * (float64(1.0) - fr)) + (sb * fr))
                    var lxv float64 = (lx - hx)
                    var lyv float64 = (ly - hy)
                    var lzv float64 = (lz - hz)
                    __tuple_11 := __pytra_as_list(normalize(lxv, lyv, lzv))
                    var ldx float64 = __pytra_float(__tuple_11[0])
                    _ = ldx
                    var ldy float64 = __pytra_float(__tuple_11[1])
                    _ = ldy
                    var ldz float64 = __pytra_float(__tuple_11[2])
                    _ = ldz
                    var ndotl float64 = __pytra_max((((nx * ldx) + (ny * ldy)) + (nz * ldz)), float64(0.0))
                    __tuple_12 := __pytra_as_list(normalize((ldx - dx), (ldy - dy), (ldz - dz)))
                    var hvx float64 = __pytra_float(__tuple_12[0])
                    _ = hvx
                    var hvy float64 = __pytra_float(__tuple_12[1])
                    _ = hvy
                    var hvz float64 = __pytra_float(__tuple_12[2])
                    _ = hvz
                    var ndoth float64 = __pytra_max((((nx * hvx) + (ny * hvy)) + (nz * hvz)), float64(0.0))
                    var spec float64 = (ndoth * ndoth)
                    spec = (spec * spec)
                    spec = (spec * spec)
                    spec = (spec * spec)
                    var glow float64 = (float64(10.0) / __pytra_float((((float64(1.0) + (lxv * lxv)) + (lyv * lyv)) + (lzv * lzv))))
                    r += (((float64(0.2) * ndotl) + (float64(0.8) * spec)) + (float64(0.45) * glow))
                    g += (((float64(0.18) * ndotl) + (float64(0.6) * spec)) + (float64(0.35) * glow))
                    b += (((float64(0.26) * ndotl) + (float64(1.0) * spec)) + (float64(0.65) * glow))
                    if (hit_kind == int64(2)) {
                        r *= float64(0.95)
                        g *= float64(1.05)
                        b *= float64(1.1)
                    } else {
                        if (hit_kind == int64(3)) {
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
            r = math.Sqrt(clamp01(r))
            g = math.Sqrt(clamp01(g))
            b = math.Sqrt(clamp01(b))
            __pytra_set_index(frame, (row_base + px), quantize_332(r, g, b))
        }
    }
    return __pytra_as_list(__pytra_bytes(frame))
}

func run_16_glass_sculpture_chaos() {
    var width int64 = int64(320)
    var height int64 = int64(240)
    var frames_n int64 = int64(72)
    var out_path string = __pytra_str("sample/out/16_glass_sculpture_chaos.gif")
    var start float64 = __pytra_perf_counter()
    var frames []any = __pytra_as_list([]any{})
    for i := int64(0); i < frames_n; i += 1 {
        frames = append(__pytra_as_list(frames), render_frame(width, height, i, frames_n))
    }
    __pytra_save_gif(out_path, width, height, frames, palette_332(), int64(6), int64(0))
    var elapsed float64 = (__pytra_perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_16_glass_sculpture_chaos()
}
